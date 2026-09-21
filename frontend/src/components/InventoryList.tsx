import React, { useEffect, useState } from 'react';
import api from '../api';

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
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'available' | 'sold'>('all');

  // New item form
  const [name, setName] = useState('');
  const [brand, setBrand] = useState('');
  const [model, setModel] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [salePrice, setSalePrice] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const fetchItems = async () => {
    setLoading(true);
    try {
      const url = filter === 'all' ? '/inventory/' : `/inventory/?status=${filter}`;
      const res = await api.get(url);
      setItems(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch inventory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [filter]);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !brand || !model || !purchasePrice || !salePrice) {
      setError('Please fill all item fields.');
      return;
    }
    setError('');
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
    } catch (err) {
      console.error(err);
      setError('Failed to add inventory item.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '20px auto', fontFamily: 'sans-serif' }}>
      <h2>Inventory Management</h2>
      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      <form onSubmit={handleAddItem} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10, marginBottom: 20 }}>
        <input placeholder="Item Name (e.g. iPhone 15)" value={name} onChange={e => setName(e.target.value)} required style={{ padding: 8 }} />
        <input placeholder="Brand" value={brand} onChange={e => setBrand(e.target.value)} required style={{ padding: 8 }} />
        <input placeholder="Model" value={model} onChange={e => setModel(e.target.value)} required style={{ padding: 8 }} />
        <input placeholder="Purchase Price" type="number" step="0.01" value={purchasePrice} onChange={e => setPurchasePrice(e.target.value)} required style={{ padding: 8 }} />
        <input placeholder="Sale Price" type="number" step="0.01" value={salePrice} onChange={e => setSalePrice(e.target.value)} required style={{ padding: 8 }} />
        <button type="submit" disabled={submitting} style={{ padding: 8 }}>{submitting ? 'Adding...' : 'Add Item'}</button>
      </form>

      <div style={{ marginBottom: 15 }}>
        <label>Filter: </label>
        <button onClick={() => setFilter('all')} style={{ fontWeight: filter === 'all' ? 'bold' : 'normal', marginRight: 5 }}>All</button>
        <button onClick={() => setFilter('available')} style={{ fontWeight: filter === 'available' ? 'bold' : 'normal', marginRight: 5 }}>Available</button>
        <button onClick={() => setFilter('sold')} style={{ fontWeight: filter === 'sold' ? 'bold' : 'normal' }}>Sold</button>
      </div>

      {loading ? (
        <p>Loading inventory...</p>
      ) : items.length === 0 ? (
        <p>No inventory items found.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ccc' }}>
              <th style={{ padding: 8 }}>ID</th>
              <th style={{ padding: 8 }}>Name</th>
              <th style={{ padding: 8 }}>Brand/Model</th>
              <th style={{ padding: 8 }}>Purchase Price</th>
              <th style={{ padding: 8 }}>Sale Price</th>
              <th style={{ padding: 8 }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 8 }}>{item.id}</td>
                <td style={{ padding: 8 }}><strong>{item.name}</strong></td>
                <td style={{ padding: 8 }}>{item.brand} ({item.model})</td>
                <td style={{ padding: 8 }}>${item.purchase_price}</td>
                <td style={{ padding: 8 }}>${item.sale_price}</td>
                <td style={{ padding: 8, color: item.status === 'available' ? 'green' : 'gray' }}>
                  {item.status.toUpperCase()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default InventoryList;
