import React, { useEffect, useState, useMemo } from 'react';
import api from '../api';
import { useToast } from './Toast';

interface Sale {
  id: number;
  invoice_id?: string;
  item?: number;
  item_detail?: {
    name: string;
    brand: string;
    model: string;
  };
  item_description?: string;
  customer?: number;
  customer_name?: string;
  quantity?: number;
  cost_price?: string;
  sale_price: string;
  profit: string;
  date: string;
}

interface InventoryItem {
  id: number;
  name: string;
  brand: string;
  model: string;
  purchase_price?: string;
  sale_price: string;
  status: string;
}

interface Customer {
  id: number;
  name: string;
  phone: string;
}

const SalesList: React.FC = () => {
  const toast = useToast();
  const [sales, setSales] = useState<Sale[]>([]);
  const [availableItems, setAvailableItems] = useState<InventoryItem[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isNewSaleOpen, setIsNewSaleOpen] = useState(false);
  const [activeReceipt, setActiveReceipt] = useState<Sale | null>(null);

  // New Sale Form State
  const [selectedItem, setSelectedItem] = useState<number | ''>('');
  const [selectedCustomer, setSelectedCustomer] = useState<number | ''>('');
  const [customCustomerName, setCustomCustomerName] = useState('');
  const [salePrice, setSalePrice] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [salesRes, itemsRes, custRes] = await Promise.all([
        api.get('/sales/'),
        api.get('/inventory/?status=available'),
        api.get('/customers/'),
      ]);
      setSales(salesRes.data);
      setAvailableItems(itemsRes.data);
      setCustomers(custRes.data);
    } catch (err) {
      console.error(err);
      toast.error('فشل في تحميل بيانات المبيعات');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onItemChange = (itemId: number) => {
    setSelectedItem(itemId);
    const item = availableItems.find((i) => i.id === itemId);
    if (item) {
      setSalePrice(item.sale_price);
    }
  };

  const handleCreateSale = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem || !salePrice) {
      toast.warning('يرجى اختيار الجهاز وتأكيد سعر البيع');
      return;
    }

    setSubmitting(true);
    try {
      const cust = customers.find((c) => c.id === selectedCustomer);
      const itm = availableItems.find((i) => i.id === selectedItem);
      const finalCustomerName = cust ? cust.name : (customCustomerName.trim() || 'عميل نقدي (Walk-in)');

      const res = await api.post('/sales/', {
        item: selectedItem,
        customer: selectedCustomer || null,
        customer_name: finalCustomerName,
        item_description: itm ? `${itm.brand} ${itm.model} - ${itm.name}` : '',
        cost_price: itm ? (itm.purchase_price || '0.00') : '0.00',
        sale_price: salePrice,
        quantity: 1,
      });

      setSales([res.data, ...sales]);
      setSelectedItem('');
      setSelectedCustomer('');
      setCustomCustomerName('');
      setSalePrice('');
      setIsNewSaleOpen(false);

      // Refresh available inventory list
      const itemsRes = await api.get('/inventory/?status=available');
      setAvailableItems(itemsRes.data);

      toast.success(`تم تسجيل عملية البيع بنجاح! فاتورة #${res.data.invoice_id || res.data.id}`);
      setActiveReceipt(res.data);
    } catch (err) {
      console.error(err);
      toast.error('حدث خطأ أثناء حفظ الفاتورة');
    } finally {
      setSubmitting(false);
    }
  };

  // Filter sales
  const filteredSales = useMemo(() => {
    return sales.filter((s) => {
      const query = searchQuery.toLowerCase();
      const invoice = (s.invoice_id || s.id.toString()).toLowerCase();
      const customer = (s.customer_name || '').toLowerCase();
      const desc = (s.item_description || '').toLowerCase();

      return invoice.includes(query) || customer.includes(query) || desc.includes(query);
    });
  }, [sales, searchQuery]);

  // Totals for filtered sales
  const totals = useMemo(() => {
    const rev = filteredSales.reduce((acc, curr) => acc + Number(curr.sale_price || 0), 0);
    const prof = filteredSales.reduce((acc, curr) => acc + Number(curr.profit || 0), 0);
    return { revenue: rev, profit: prof, count: filteredSales.length };
  }, [filteredSales]);

  // Selected item object for live profit preview in form
  const selectedItemObj = availableItems.find((i) => i.id === selectedItem);
  const liveProfit = selectedItemObj && salePrice
    ? Number(salePrice) - Number(selectedItemObj.purchase_price || 0)
    : 0;

  return (
    <div className="main-content animate-fade-in">
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16,
        marginBottom: 20
      }}>
        <div>
          <h1 className="page-title">
            <span>💰 سجل المبيعات ونقاط البيع (Sales & POS)</span>
          </h1>
          <p className="page-subtitle">
            تسجيل عمليات البيع، احتساب الأرباح اللحظية، وإصدار الفواتير
          </p>
        </div>

        <button
          onClick={() => setIsNewSaleOpen(true)}
          className="btn btn-primary"
        >
          <span>➕</span>
          <span>تسجيل بيع جديد (New Sale)</span>
        </button>
      </div>

      {/* Summary KPI Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: 16,
        marginBottom: 22
      }}>
        <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>عدد العمليات المعروضة</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{totals.count} عملية</div>
          </div>
          <span style={{ fontSize: '1.8rem' }}>🧾</span>
        </div>

        <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>إجمالي الإيرادات للفترة</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--primary-light)' }}>
              {totals.revenue.toLocaleString()} EGP
            </div>
          </div>
          <span style={{ fontSize: '1.8rem' }}>💵</span>
        </div>

        <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>صافي الأرباح المحققة</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981' }}>
              +{totals.profit.toLocaleString()} EGP
            </div>
          </div>
          <span style={{ fontSize: '1.8rem' }}>📈</span>
        </div>
      </div>

      {/* Search Toolbar */}
      <div className="glass-card" style={{ padding: 18, marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 260, position: 'relative' }}>
            <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
              🔍
            </span>
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: 40 }}
              placeholder="ابحث برقم الفاتورة، اسم العميل، أو اسم الجهاز..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            الأجهزة المتاحة للبيع الآن: <strong>{availableItems.length}</strong>
          </div>
        </div>
      </div>

      {/* Sales Table */}
      {loading ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          جاري تحميل سجل المبيعات...
        </div>
      ) : filteredSales.length === 0 ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🧾</div>
          <h4>لا توجد فواتير مطابقة للبحث</h4>
          <p style={{ fontSize: '0.85rem', marginTop: 6 }}>سجل أول عملية بيع من زر "تسجيل بيع جديد" بالأعلى</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>رقم الفاتورة</th>
                <th>بيان الجهاز المباع</th>
                <th>اسم العميل</th>
                <th>الكمية</th>
                <th>سعر التكلفة</th>
                <th>سعر البيع</th>
                <th>صافي الربح</th>
                <th>تاريخ الفاتورة</th>
                <th style={{ textAlign: 'center' }}>الإجراء</th>
              </tr>
            </thead>
            <tbody>
              {filteredSales.map((sale) => {
                const itemTitle =
                  sale.item_description ||
                  (sale.item_detail ? `${sale.item_detail.brand} ${sale.item_detail.model} - ${sale.item_detail.name}` : `جهاز #${sale.item || '-'}`);
                const invoiceTag = sale.invoice_id ? `#${sale.invoice_id.toUpperCase()}` : `#SALE-${sale.id}`;
                const profitNum = Number(sale.profit || 0);

                return (
                  <tr key={sale.id}>
                    <td>
                      <span style={{ fontWeight: 800, color: 'var(--primary-light)' }}>
                        {invoiceTag}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{itemTitle}</div>
                    </td>
                    <td>
                      <span style={{ fontWeight: 500 }}>{sale.customer_name || 'عميل نقدي'}</span>
                    </td>
                    <td>{sale.quantity || 1}</td>
                    <td style={{ color: 'var(--text-muted)' }}>
                      {sale.cost_price ? `${Number(sale.cost_price).toLocaleString()} EGP` : '-'}
                    </td>
                    <td style={{ fontWeight: 700 }}>
                      {Number(sale.sale_price).toLocaleString()} EGP
                    </td>
                    <td>
                      <span className={`badge ${profitNum >= 0 ? 'badge-success' : 'badge-danger'}`}>
                        {profitNum >= 0 ? `+${profitNum.toLocaleString()}` : profitNum.toLocaleString()} EGP
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(sale.date).toLocaleDateString()}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => setActiveReceipt(sale)}
                        className="btn btn-secondary btn-sm"
                        title="عرض وطباعة الفاتورة"
                      >
                        🖨️ إيصال
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* POS New Sale Modal */}
      {isNewSaleOpen && (
        <div className="modal-overlay" onClick={() => setIsNewSaleOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1.2rem' }}>تسجيل عملية بيع جديدة (POS Checkout)</h3>
              <button
                onClick={() => setIsNewSaleOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.3rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSale}>
              <div className="modal-body">
                {availableItems.length === 0 ? (
                  <div style={{ padding: 20, textAlign: 'center', background: 'var(--warning-bg)', borderRadius: 8, color: 'var(--warning)' }}>
                    ⚠️ لا توجد أجهزة متاحة في المخزون حالياً للبيع. يرجى إضافة أجهزة للمخزون أولاً.
                  </div>
                ) : (
                  <>
                    <div className="form-group">
                      <label className="form-label">اختر الجهاز من المخزون المتوفر</label>
                      <select
                        className="form-select"
                        value={selectedItem}
                        onChange={(e) => onItemChange(Number(e.target.value))}
                        required
                      >
                        <option value="">-- اضغط للاختيار --</option>
                        {availableItems.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.brand} {item.model} - {item.name} (تكلفة: {item.purchase_price} | بيع: {item.sale_price} EGP)
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">العميل المسجل (اختياري)</label>
                      <select
                        className="form-select"
                        value={selectedCustomer}
                        onChange={(e) => setSelectedCustomer(Number(e.target.value))}
                      >
                        <option value="">-- عميل نقدي أو أدخل اسم يدوي أدناه --</option>
                        {customers.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name} ({c.phone})
                          </option>
                        ))}
                      </select>
                    </div>

                    {!selectedCustomer && (
                      <div className="form-group">
                        <label className="form-label">أو أدخل اسم العميل يدوياً</label>
                        <input
                          className="form-input"
                          placeholder="مثال: محمد محمود (نقدي)"
                          value={customCustomerName}
                          onChange={(e) => setCustomCustomerName(e.target.value)}
                        />
                      </div>
                    )}

                    <div className="form-group">
                      <label className="form-label">سعر البيع الفعلي (EGP)</label>
                      <input
                        type="number"
                        step="0.01"
                        className="form-input"
                        placeholder="0.00"
                        value={salePrice}
                        onChange={(e) => setSalePrice(e.target.value)}
                        required
                      />
                    </div>

                    {selectedItemObj && (
                      <div style={{
                        padding: '14px',
                        borderRadius: 8,
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-color)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 6,
                        fontSize: '0.86rem'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-muted)' }}>سعر تكلفة الجهاز:</span>
                          <span>{Number(selectedItemObj.purchase_price || 0).toLocaleString()} EGP</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-muted)' }}>سعر البيع المحدد:</span>
                          <strong>{Number(salePrice || 0).toLocaleString()} EGP</strong>
                        </div>
                        <div style={{ height: 1, background: 'var(--border-color)', margin: '4px 0' }}></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem' }}>
                          <span>صافي الربح المتوقع:</span>
                          <strong style={{ color: liveProfit >= 0 ? '#10b981' : '#ef4444' }}>
                            +{liveProfit.toLocaleString()} EGP
                          </strong>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setIsNewSaleOpen(false)}
                  className="btn btn-secondary"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  disabled={submitting || availableItems.length === 0}
                  className="btn btn-primary"
                >
                  {submitting ? 'جاري التسجيل...' : 'إتمام البيع وطباعة الفاتورة'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Printable Receipt Preview Modal */}
      {activeReceipt && (
        <div className="modal-overlay" onClick={() => setActiveReceipt(null)}>
          <div className="modal-content" style={{ maxWidth: 440 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1.1rem' }}>إيصال فاتورة مبيعات</h3>
              <button
                onClick={() => setActiveReceipt(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.3rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div className="modal-body" style={{
              fontFamily: 'var(--font-mono)',
              background: 'var(--bg-surface-elevated)',
              padding: 24,
              borderRadius: 8,
              border: '1px dashed var(--border-color)',
              lineHeight: 1.6
            }}>
              <div style={{ textAlign: 'center', marginBottom: 14 }}>
                <h4 style={{ margin: 0, fontSize: '1.1rem' }}>📱 MOBILE-STORE POS</h4>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>فاتورة بيع رسمية معتمدة</div>
                <div style={{ fontSize: '0.75rem', marginTop: 4 }}>
                  {new Date(activeReceipt.date).toLocaleString()}
                </div>
              </div>

              <div style={{ borderTop: '1px dashed var(--border-color)', borderBottom: '1px dashed var(--border-color)', padding: '10px 0', margin: '10px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>رقم الفاتورة:</span>
                  <strong>{activeReceipt.invoice_id ? `#${activeReceipt.invoice_id.toUpperCase()}` : `#SALE-${activeReceipt.id}`}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>العميل:</span>
                  <span>{activeReceipt.customer_name || 'عميل نقدي'}</span>
                </div>
              </div>

              <div style={{ padding: '8px 0' }}>
                <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                  {activeReceipt.item_description || 'جهاز موبايل'}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  <span>الكمية: {activeReceipt.quantity || 1}</span>
                  <span style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>
                    {Number(activeReceipt.sale_price).toLocaleString()} EGP
                  </span>
                </div>
              </div>

              <div style={{ borderTop: '2px solid var(--border-color)', paddingTop: 10, marginTop: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.1rem', fontWeight: 'bold' }}>
                  <span>الإجمالي المدفوع:</span>
                  <span style={{ color: 'var(--primary-light)' }}>
                    {Number(activeReceipt.sale_price).toLocaleString()} EGP
                  </span>
                </div>
              </div>

              <div style={{ textAlign: 'center', marginTop: 18, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                شكراً لتعاملكم معنا! نتمنى لكم يوماً سعيداً
              </div>
            </div>

            <div className="modal-footer">
              <button
                onClick={() => window.print()}
                className="btn btn-primary"
              >
                🖨️ طباعة الفاتورة
              </button>
              <button
                onClick={() => setActiveReceipt(null)}
                className="btn btn-secondary"
              >
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesList;
