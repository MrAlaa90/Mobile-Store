import React, { useEffect, useState, useMemo } from 'react';
import api from '../api';
import { useToast } from './Toast';

interface InventoryItem {
  id: number;
  name: string;
  brand: string;
  model: string;
  purchase_price: string;
  sale_price: string;
  status: 'available' | 'sold';
  created_at: string;
}

const InventoryList: React.FC = () => {
  const toast = useToast();
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'all' | 'available' | 'sold'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('all');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [brand, setBrand] = useState('');
  const [model, setModel] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [salePrice, setSalePrice] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const url = statusFilter === 'all' ? '/inventory/' : `/inventory/?status=${statusFilter}`;
      const res = await api.get(url);
      setItems(res.data);
    } catch (err) {
      console.error(err);
      toast.error('فشل في تحميل بيانات المخزون');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [statusFilter]);

  // Extract unique brands for filtering
  const availableBrands = useMemo(() => {
    const brands = new Set<string>();
    items.forEach((i) => {
      if (i.brand) brands.add(i.brand.trim());
    });
    return Array.from(brands);
  }, [items]);

  // Filter items by search query and selected brand
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesSearch =
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.brand.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id.toString().includes(searchQuery);

      const matchesBrand = selectedBrand === 'all' || item.brand.toLowerCase() === selectedBrand.toLowerCase();

      return matchesSearch && matchesBrand;
    });
  }, [items, searchQuery, selectedBrand]);

  // Summary calculations
  const totalValuation = useMemo(() => {
    return filteredItems
      .filter((i) => i.status === 'available')
      .reduce((sum, item) => sum + Number(item.purchase_price || 0), 0);
  }, [filteredItems]);

  const totalExpectedRevenue = useMemo(() => {
    return filteredItems
      .filter((i) => i.status === 'available')
      .reduce((sum, item) => sum + Number(item.sale_price || 0), 0);
  }, [filteredItems]);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !brand || !model || !purchasePrice || !salePrice) {
      toast.warning('يرجى ملء جميع حقول الجهاز');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post('/inventory/', {
        name,
        brand,
        model,
        purchase_price: purchasePrice,
        sale_price: salePrice,
        status: 'available',
      });
      setItems([res.data, ...items]);
      setName('');
      setBrand('');
      setModel('');
      setPurchasePrice('');
      setSalePrice('');
      setIsAddModalOpen(false);
      toast.success(`تم إضافة الجهاز (${res.data.name}) إلى المخزون بنجاح!`);
    } catch (err) {
      console.error(err);
      toast.error('حدث خطأ أثناء حفظ الجهاز');
    } finally {
      setSubmitting(false);
    }
  };

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
            <span>📦 إدارة المخزون والأجهزة</span>
          </h1>
          <p className="page-subtitle">
            متابعة الهواتف الذكية والإكسسوارات المتاحة والمباعة بالمحل
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="btn btn-primary"
        >
          <span>➕</span>
          <span>إضافة جهاز جديد (Add Item)</span>
        </button>
      </div>

      {/* Overview Stat Badges */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 14,
        marginBottom: 22
      }}>
        <div className="glass-card" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>إجمالي الأجهزة المعروضة</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800 }}>{filteredItems.length}</div>
          </div>
          <span style={{ fontSize: '1.6rem' }}>📱</span>
        </div>

        <div className="glass-card" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>قيمة رأس المال المتوفر</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--primary-light)' }}>
              {totalValuation.toLocaleString()} EGP
            </div>
          </div>
          <span style={{ fontSize: '1.6rem' }}>💵</span>
        </div>

        <div className="glass-card" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>القيمة البيعية المتوقعة</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#10b981' }}>
              {totalExpectedRevenue.toLocaleString()} EGP
            </div>
          </div>
          <span style={{ fontSize: '1.6rem' }}>📈</span>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="glass-card" style={{ padding: 18, marginBottom: 20 }}>
        <div style={{
          display: 'flex',
          gap: 12,
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          {/* Search Input */}
          <div style={{ flex: '1 1 300px', position: 'relative' }}>
            <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
              🔍
            </span>
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: 40 }}
              placeholder="ابحث بالاسم، الماركة، الموديل أو رقم المعرف..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                style={{
                  position: 'absolute',
                  right: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer'
                }}
              >
                ✕
              </button>
            )}
          </div>

          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: 6, background: 'var(--bg-surface-elevated)', padding: 4, borderRadius: 8 }}>
            {(['all', 'available', 'sold'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 6,
                  border: 'none',
                  background: statusFilter === st ? 'var(--primary)' : 'transparent',
                  color: statusFilter === st ? '#ffffff' : 'var(--text-secondary)',
                  fontWeight: statusFilter === st ? 700 : 500,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
              >
                {st === 'all' ? 'الكل (All)' : st === 'available' ? 'متوفر (Available)' : 'مباع (Sold)'}
              </button>
            ))}
          </div>
        </div>

        {/* Brand Quick Chips */}
        {availableBrands.length > 0 && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14, alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>الماركات:</span>
            <button
              onClick={() => setSelectedBrand('all')}
              style={{
                padding: '3px 10px',
                borderRadius: 20,
                fontSize: '0.75rem',
                border: '1px solid var(--border-color)',
                background: selectedBrand === 'all' ? 'var(--bg-card-hover)' : 'transparent',
                color: selectedBrand === 'all' ? 'var(--primary-light)' : 'var(--text-secondary)',
                cursor: 'pointer'
              }}
            >
              الكل
            </button>
            {availableBrands.map((b) => (
              <button
                key={b}
                onClick={() => setSelectedBrand(selectedBrand === b ? 'all' : b)}
                style={{
                  padding: '3px 10px',
                  borderRadius: 20,
                  fontSize: '0.75rem',
                  border: '1px solid var(--border-color)',
                  background: selectedBrand === b ? 'var(--primary)' : 'transparent',
                  color: selectedBrand === b ? '#fff' : 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                {b}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Table of Items */}
      {loading ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          جاري تحميل بيانات المخزون...
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🔍</div>
          <h4>لم يتم العثور على أي أجهزة مطابقة للبحث</h4>
          <p style={{ fontSize: '0.85rem', marginTop: 6 }}>جرب تغيير كلمات البحث أو الفلاتر المختارة</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: 70 }}>#ID</th>
                <th>اسم الجهاز والوصف</th>
                <th>الماركة والموديل</th>
                <th>سعر التكلفة</th>
                <th>سعر البيع</th>
                <th>الربح المتوقع</th>
                <th>الحالة</th>
                <th>تاريخ الإضافة</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => {
                const cost = Number(item.purchase_price || 0);
                const price = Number(item.sale_price || 0);
                const expectedProfit = price - cost;

                return (
                  <tr key={item.id}>
                    <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>#{item.id}</td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{item.name}</div>
                    </td>
                    <td>
                      <span className="badge badge-info" style={{ fontSize: '0.75rem' }}>
                        {item.brand}
                      </span>{' '}
                      <span style={{ color: 'var(--text-secondary)' }}>{item.model}</span>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>
                      {cost.toLocaleString()} EGP
                    </td>
                    <td style={{ fontWeight: 700 }}>
                      {price.toLocaleString()} EGP
                    </td>
                    <td style={{ color: expectedProfit >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      +{expectedProfit.toLocaleString()} EGP
                    </td>
                    <td>
                      <span className={`badge ${item.status === 'available' ? 'badge-success' : 'badge-danger'}`}>
                        {item.status === 'available' ? '● متوفر' : '✖ مباع'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Item Modal */}
      {isAddModalOpen && (
        <div className="modal-overlay" onClick={() => setIsAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1.2rem' }}>إضافة جهاز جديد إلى المخزون</h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.3rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddItem}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">اسم الجهاز (Device Name)</label>
                  <input
                    className="form-input"
                    placeholder="مثال: iPhone 15 Pro Max 256GB"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div className="form-group">
                    <label className="form-label">الماركة (Brand)</label>
                    <input
                      className="form-input"
                      placeholder="Apple, Samsung, Xiaomi..."
                      value={brand}
                      onChange={(e) => setBrand(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">الموديل (Model)</label>
                    <input
                      className="form-input"
                      placeholder="15 Pro, S24 Ultra..."
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div className="form-group">
                    <label className="form-label">سعر التكلفة والشراء (EGP)</label>
                    <input
                      className="form-input"
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={purchasePrice}
                      onChange={(e) => setPurchasePrice(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">سعر البيع المقترح (EGP)</label>
                    <input
                      className="form-input"
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={salePrice}
                      onChange={(e) => setSalePrice(e.target.value)}
                      required
                    />
                  </div>
                </div>

                {purchasePrice && salePrice && (
                  <div style={{
                    padding: '10px 14px',
                    borderRadius: 8,
                    background: 'var(--bg-surface-elevated)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.88rem'
                  }}>
                    <span>هامش الربح المتوقع:</span>
                    <strong style={{ color: Number(salePrice) - Number(purchasePrice) >= 0 ? '#10b981' : '#ef4444' }}>
                      +{(Number(salePrice) - Number(purchasePrice)).toLocaleString()} EGP
                    </strong>
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="btn btn-secondary"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn btn-primary"
                >
                  {submitting ? 'جاري الحفظ...' : 'حفظ الجهاز في المخزون'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryList;
