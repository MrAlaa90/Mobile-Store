import React, { useEffect, useState } from 'react';
import api from '../api';

interface Customer {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  created_at: string;
}

const CustomerManagement: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const res = await api.get('/customers/');
      setCustomers(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch customers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  const handleAddCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !phone) {
      setError('Name and Phone are required.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const res = await api.post('/customers/', { name, phone, email: email || null });
      setCustomers([res.data, ...customers]);
      setName('');
      setPhone('');
      setEmail('');
    } catch (err) {
      console.error(err);
      setError('Failed to create customer');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '20px auto', fontFamily: 'sans-serif' }}>
      <h2>Customer Management</h2>
      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      <form onSubmit={handleAddCustomer} style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <input
          placeholder="Customer Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ padding: 8 }}
        />
        <input
          placeholder="Phone Number"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required
          style={{ padding: 8 }}
        />
        <input
          placeholder="Email (optional)"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ padding: 8 }}
        />
        <button type="submit" disabled={submitting} style={{ padding: '8px 16px' }}>
          {submitting ? 'Adding...' : 'Add Customer'}
        </button>
      </form>

      {loading ? (
        <p>Loading customers...</p>
      ) : customers.length === 0 ? (
        <p>No customers found.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ccc' }}>
              <th style={{ padding: 8 }}>ID</th>
              <th style={{ padding: 8 }}>Name</th>
              <th style={{ padding: 8 }}>Phone</th>
              <th style={{ padding: 8 }}>Email</th>
              <th style={{ padding: 8 }}>Date Added</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 8 }}>{c.id}</td>
                <td style={{ padding: 8 }}><strong>{c.name}</strong></td>
                <td style={{ padding: 8 }}>{c.phone}</td>
                <td style={{ padding: 8 }}>{c.email || '-'}</td>
                <td style={{ padding: 8 }}>{new Date(c.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default CustomerManagement;
