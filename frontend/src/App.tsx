import React, { useEffect, useState } from 'react';
import { Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import api from './api';
import CustomerManagement from './components/CustomerManagement';
import InventoryList from './components/InventoryList';
import SalesList from './components/SalesList';
import RepairManagement from './components/RepairManagement';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('accessToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('root');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await api.post('/auth/login/', { username, password });
      localStorage.setItem('accessToken', response.data.access);
      localStorage.setItem('refreshToken', response.data.refresh);
      localStorage.setItem('username', username);
      navigate('/');
    } catch {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 360, margin: '60px auto', padding: 25, border: '1px solid #ddd', borderRadius: 8 }}>
      <h2 style={{ textAlign: 'center', marginBottom: 20 }}>Store Login</h2>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        <div>
          <label style={{ display: 'block', marginBottom: 5 }}>Username</label>
          <input
            style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 5 }}>Password</label>
          <input
            style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p role="alert" style={{ color: 'red', margin: 0 }}>{error}</p>}
        <button
          type="submit"
          disabled={loading}
          style={{ padding: 10, background: '#0066cc', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({ inventory: 0, sales: 0, repairs: 0, customers: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/inventory/'),
      api.get('/sales/'),
      api.get('/repairs/'),
      api.get('/customers/'),
    ])
      .then(([inv, sales, rep, cust]) => {
        setStats({
          inventory: inv.data.length,
          sales: sales.data.length,
          repairs: rep.data.length,
          customers: cust.data.length,
        });
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 800, margin: '30px auto', fontFamily: 'sans-serif' }}>
      <h2>Store Overview Dashboard</h2>
      {loading ? (
        <p>Loading metrics...</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 20, marginTop: 20 }}>
          <div style={{ background: '#eef2ff', padding: 20, borderRadius: 8, textAlign: 'center' }}>
            <h3 style={{ margin: 0, color: '#3730a3' }}>{stats.inventory}</h3>
            <p style={{ margin: '8px 0 0', color: '#4f46e5' }}>Total Inventory Items</p>
          </div>
          <div style={{ background: '#ecfdf5', padding: 20, borderRadius: 8, textAlign: 'center' }}>
            <h3 style={{ margin: 0, color: '#065f46' }}>{stats.sales}</h3>
            <p style={{ margin: '8px 0 0', color: '#059669' }}>Total Sales Recorded</p>
          </div>
          <div style={{ background: '#fffbeb', padding: 20, borderRadius: 8, textAlign: 'center' }}>
            <h3 style={{ margin: 0, color: '#92400e' }}>{stats.repairs}</h3>
            <p style={{ margin: '8px 0 0', color: '#d97706' }}>Repair Tickets</p>
          </div>
          <div style={{ background: '#fdf2f8', padding: 20, borderRadius: 8, textAlign: 'center' }}>
            <h3 style={{ margin: 0, color: '#9d174d' }}>{stats.customers}</h3>
            <p style={{ margin: '8px 0 0', color: '#db2777' }}>Registered Customers</p>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  const navigate = useNavigate();
  const token = localStorage.getItem('accessToken');
  const username = localStorage.getItem('username');

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('username');
    navigate('/login');
  };

  return (
    <div>
      <nav style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '12px 24px',
        background: '#1e293b',
        color: '#fff',
        fontFamily: 'sans-serif'
      }}>
        <div style={{ display: 'flex', gap: 15, alignItems: 'center' }}>
          <strong>Mobile-Store POS</strong>
          {token && (
            <>
              <Link to="/" style={{ color: '#94a3b8', textDecoration: 'none' }}>Dashboard</Link>
              <Link to="/inventory" style={{ color: '#94a3b8', textDecoration: 'none' }}>Inventory</Link>
              <Link to="/customers" style={{ color: '#94a3b8', textDecoration: 'none' }}>Customers</Link>
              <Link to="/sales" style={{ color: '#94a3b8', textDecoration: 'none' }}>Sales</Link>
              <Link to="/repairs" style={{ color: '#94a3b8', textDecoration: 'none' }}>Repairs</Link>
            </>
          )}
        </div>
        <div>
          {token ? (
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <span style={{ fontSize: 14 }}>User: {username}</span>
              <button
                onClick={logout}
                style={{ padding: '6px 12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
              >
                Logout
              </button>
            </div>
          ) : (
            <Link to="/login" style={{ color: '#38bdf8', textDecoration: 'none' }}>Login</Link>
          )}
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/login" element={<Login />} />
        <Route path="/inventory" element={<ProtectedRoute><InventoryList /></ProtectedRoute>} />
        <Route path="/customers" element={<ProtectedRoute><CustomerManagement /></ProtectedRoute>} />
        <Route path="/sales" element={<ProtectedRoute><SalesList /></ProtectedRoute>} />
        <Route path="/repairs" element={<ProtectedRoute><RepairManagement /></ProtectedRoute>} />
      </Routes>
    </div>
  );
}

export default App;
