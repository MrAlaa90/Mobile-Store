import React, { useEffect, useState } from 'react';
import api from '../api';

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
  const [sales, setSales] = useState<Sale[]>([]);
  const [availableItems, setAvailableItems] = useState<InventoryItem[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  // New Sale Form
  const [selectedItem, setSelectedItem] = useState<number | ''>('');
  const [selectedCustomer, setSelectedCustomer] = useState<number | ''>('');
  const [salePrice, setSalePrice] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

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
      setError('Failed to load sales data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onItemChange = (itemId: number) => {
    setSelectedItem(itemId);
    const item = availableItems.find(i => i.id === itemId);
    if (item) {
      setSalePrice(item.sale_price);
    }
  };

  const handleCreateSale = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem || !selectedCustomer || !salePrice) {
      setError('Please select an item, customer, and confirm sale price.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const cust = customers.find(c => c.id === selectedCustomer);
      const itm = availableItems.find(i => i.id === selectedItem);
      const res = await api.post('/sales/', {
        item: selectedItem,
        customer: selectedCustomer,
        customer_name: cust ? cust.name : 'Customer',
        item_description: itm ? `${itm.brand} ${itm.model} - ${itm.name}` : '',
        cost_price: itm ? (itm.purchase_price || '0.00') : '0.00',
        sale_price: salePrice,
        quantity: 1,
      });
      setSales([res.data, ...sales]);
      setSelectedItem('');
      setSelectedCustomer('');
      setSalePrice('');
      // Refresh available inventory list
      const itemsRes = await api.get('/inventory/?status=available');
      setAvailableItems(itemsRes.data);
    } catch (err) {
      console.error(err);
      setError('Failed to record sale.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 960, margin: '20px auto', fontFamily: 'sans-serif' }}>
      <h2>Sales & POS Invoicing (سجل المبيعات والفواتير)</h2>
      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      <div style={{ background: '#f9f9f9', padding: 15, borderRadius: 6, marginBottom: 20 }}>
        <h3>Record New Sale</h3>
        <form onSubmit={handleCreateSale} style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <select
            value={selectedItem}
            onChange={e => onItemChange(Number(e.target.value))}
            required
            style={{ padding: 8 }}
          >
            <option value="">-- Select Available Item --</option>
            {availableItems.map(item => (
              <option key={item.id} value={item.id}>
                {item.brand} {item.model} - {item.name} ({item.sale_price} EGP)
              </option>
            ))}
          </select>

          <select
            value={selectedCustomer}
            onChange={e => setSelectedCustomer(Number(e.target.value))}
            required
            style={{ padding: 8 }}
          >
            <option value="">-- Select Customer --</option>
            {customers.map(c => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.phone})
              </option>
            ))}
          </select>

          <input
            type="number"
            step="0.01"
            placeholder="Sale Price (EGP)"
            value={salePrice}
            onChange={e => setSalePrice(e.target.value)}
            required
            style={{ padding: 8, width: 140 }}
          />

          <button type="submit" disabled={submitting || availableItems.length === 0} style={{ padding: '8px 16px', backgroundColor: '#0078d4', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
            {submitting ? 'Recording...' : 'Complete Sale'}
          </button>
        </form>
        {availableItems.length === 0 && (
          <p style={{ color: '#888', fontSize: 13, marginTop: 5 }}>No available inventory items to sell. Add items to inventory first.</p>
        )}
      </div>

      {loading ? (
        <p>Loading sales history...</p>
      ) : sales.length === 0 ? (
        <p>No sales recorded yet.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ccc', backgroundColor: '#f1f5f9' }}>
              <th style={{ padding: 10 }}>ID / Invoice</th>
              <th style={{ padding: 10 }}>Item Description</th>
              <th style={{ padding: 10 }}>Customer</th>
              <th style={{ padding: 10 }}>Qty</th>
              <th style={{ padding: 10 }}>Cost</th>
              <th style={{ padding: 10 }}>Sale Price</th>
              <th style={{ padding: 10 }}>Net Profit</th>
              <th style={{ padding: 10 }}>Date</th>
            </tr>
          </thead>
          <tbody>
            {sales.map(sale => {
              const itemTitle = sale.item_description || (sale.item_detail ? `${sale.item_detail.brand} ${sale.item_detail.model} - ${sale.item_detail.name}` : `Item #${sale.item || '-'}`);
              const invoiceTag = sale.invoice_id ? `#${sale.invoice_id.toUpperCase()}` : `#SALE-${sale.id}`;
              const profitNum = Number(sale.profit || 0);

              return (
                <tr key={sale.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: 10, fontWeight: 'bold', color: '#0078d4' }}>{invoiceTag}</td>
                  <td style={{ padding: 10 }}>
                    <strong>{itemTitle}</strong>
                  </td>
                  <td style={{ padding: 10 }}>{sale.customer_name || `Customer #${sale.customer || 'Walk-in'}`}</td>
                  <td style={{ padding: 10 }}>{sale.quantity || 1}</td>
                  <td style={{ padding: 10, color: '#64748b' }}>{sale.cost_price ? `${Number(sale.cost_price).toFixed(2)} EGP` : '-'}</td>
                  <td style={{ padding: 10, fontWeight: 'bold' }}>{Number(sale.sale_price).toFixed(2)} EGP</td>
                  <td style={{ padding: 10, color: profitNum >= 0 ? '#16a34a' : '#dc2626', fontWeight: 'bold' }}>
                    {profitNum >= 0 ? `+${profitNum.toFixed(2)}` : profitNum.toFixed(2)} EGP
                  </td>
                  <td style={{ padding: 10, color: '#64748b', fontSize: 13 }}>{new Date(sale.date).toLocaleDateString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default SalesList;
