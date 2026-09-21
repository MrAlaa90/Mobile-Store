import React, { useEffect, useState } from 'react';
import { Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import api from './api';
import Navbar from './components/Navbar';
import CustomerManagement from './components/CustomerManagement';
import InventoryList from './components/InventoryList';
import SalesList from './components/SalesList';
import RepairManagement from './components/RepairManagement';
import { useToast } from './components/Toast';
import { useTheme } from './context/ThemeContext';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('accessToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function Login() {
  const navigate = useNavigate();
  const toast = useToast();
  const { theme, toggleTheme } = useTheme();

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
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
      toast.success(`مرحباً بك ${username}! تم تسجيل الدخول بنجاح`);
      navigate('/');
    } catch {
      setError('اسم المستخدم أو كلمة المرور غير صحيحة');
      toast.error('فشل تسجيل الدخول - تحقق من البيانات');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      position: 'relative',
      background: 'radial-gradient(circle at 50% 20%, rgba(2, 132, 199, 0.15) 0%, transparent 60%)'
    }}>
      {/* Top right theme toggle */}
      <div style={{ position: 'absolute', top: 24, right: 24 }}>
        <button
          onClick={toggleTheme}
          style={{
            width: 42,
            height: 42,
            borderRadius: '12px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-surface-elevated)',
            color: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '1.2rem',
            boxShadow: 'var(--shadow-sm)'
          }}
          title={theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>

      <div className="glass-card animate-fade-in" style={{
        width: '100%',
        maxWidth: 440,
        padding: '36px 32px',
        position: 'relative'
      }}>
        {/* Header Branding */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 56,
            height: 56,
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.8rem',
            boxShadow: '0 8px 20px rgba(2, 132, 199, 0.4)',
            marginBottom: 16
          }}>
            📱
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: 6 }}>
            Mobile-Store POS
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            نظام إدارة محلات الهواتف والمبيعات والصيانة
          </p>
        </div>

        {error && (
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            color: 'var(--danger)',
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">اسم المستخدم (Username)</label>
            <input
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">كلمة المرور (Password)</label>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', marginTop: 10, fontSize: '0.95rem' }}
          >
            {loading ? 'جاري التحقق...' : 'تسجيل الدخول (Sign In)'}
          </button>
        </form>

        <div style={{
          marginTop: 24,
          padding: '12px',
          borderRadius: '8px',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-color)',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
          textAlign: 'center'
        }}>
          💡 <strong>حساب تجريبي سريع:</strong> <code>admin</code> / <code>admin123</code> أو <code>store_a</code> / <code>password123</code>
        </div>
      </div>
    </div>
  );
}

interface DashboardMetrics {
  inventoryTotal: number;
  inventoryAvailable: number;
  inventorySold: number;
  inventoryValue: number;
  totalSalesCount: number;
  totalRevenue: number;
  totalProfit: number;
  activeRepairsCount: number;
  repairsByStatus: Record<string, number>;
  totalCustomersCount: number;
}

function Dashboard() {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    inventoryTotal: 0,
    inventoryAvailable: 0,
    inventorySold: 0,
    inventoryValue: 0,
    totalSalesCount: 0,
    totalRevenue: 0,
    totalProfit: 0,
    activeRepairsCount: 0,
    repairsByStatus: {},
    totalCustomersCount: 0,
  });
  const [recentSales, setRecentSales] = useState<any[]>([]);
  const [recentRepairs, setRecentRepairs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/inventory/'),
      api.get('/sales/'),
      api.get('/repairs/'),
      api.get('/customers/'),
    ])
      .then(([invRes, salesRes, repRes, custRes]) => {
        const inventory = invRes.data || [];
        const sales = salesRes.data || [];
        const repairs = repRes.data || [];
        const customers = custRes.data || [];

        // Calculate Inventory
        const available = inventory.filter((i: any) => i.status === 'available');
        const sold = inventory.filter((i: any) => i.status === 'sold');
        const invValue = available.reduce((acc: number, curr: any) => acc + Number(curr.purchase_price || 0), 0);

        // Calculate Sales & Profits
        const revenue = sales.reduce((acc: number, curr: any) => acc + Number(curr.sale_price || 0), 0);
        const profit = sales.reduce((acc: number, curr: any) => acc + Number(curr.profit || 0), 0);

        // Calculate Repairs
        const repairStatusMap: Record<string, number> = {};
        let activeRepairs = 0;
        repairs.forEach((r: any) => {
          const st = r.status || 'diagnosing';
          repairStatusMap[st] = (repairStatusMap[st] || 0) + 1;
          if (st !== 'delivered' && st !== 'cancelled') {
            activeRepairs++;
          }
        });

        setMetrics({
          inventoryTotal: inventory.length,
          inventoryAvailable: available.length,
          inventorySold: sold.length,
          inventoryValue: invValue,
          totalSalesCount: sales.length,
          totalRevenue: revenue,
          totalProfit: profit,
          activeRepairsCount: activeRepairs,
          repairsByStatus: repairStatusMap,
          totalCustomersCount: customers.length,
        });

        setRecentSales(sales.slice(0, 5));
        setRecentRepairs(repairs.slice(0, 5));
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const repairStatusLabels: Record<string, { label: string; color: string }> = {
    diagnosing: { label: 'قيد الفحص والتشخيص', color: '#38bdf8' },
    waiting_parts: { label: 'انتظار قطع الغيار', color: '#fb923c' },
    in_progress: { label: 'قيد الصيانة والإصلاح', color: '#facc15' },
    ready: { label: 'جاهز للاستلام', color: '#34d399' },
    delivered: { label: 'تم التسليم ومكتمل', color: '#10b981' },
    cancelled: { label: 'ملغي / تعذر الإصلاح', color: '#ef4444' },
  };

  return (
    <div className="main-content animate-fade-in">
      {/* Top Header & Quick Actions */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16,
        marginBottom: 24
      }}>
        <div>
          <h1 className="page-title">
            <span>لوحة التحكم والعمليات</span>
            <span style={{ fontSize: '0.9rem', padding: '4px 10px', background: 'var(--primary-glow)', color: 'var(--primary-light)', borderRadius: '20px' }}>
              Real-Time Sync
            </span>
          </h1>
          <p className="page-subtitle">
            نظرة شاملة ومباشرة على الإيرادات والأرباح وتذاكر الصيانة والمخزون
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button onClick={() => navigate('/sales')} className="btn btn-primary">
            <span>➕</span>
            <span>تسجيل عملية بيع (POS)</span>
          </button>
          <button onClick={() => navigate('/repairs')} className="btn btn-secondary">
            <span>🔧</span>
            <span>استلام جهاز صيانة</span>
          </button>
          <button onClick={() => navigate('/inventory')} className="btn btn-secondary">
            <span>📦</span>
            <span>إضافة للمخزون</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        {/* Total Revenue */}
        <div className="glass-card kpi-card">
          <div className="kpi-icon-wrap" style={{ background: 'rgba(2, 132, 199, 0.15)', color: '#0284c7' }}>
            💰
          </div>
          <div className="kpi-details">
            <h3>{metrics.totalRevenue.toLocaleString()} <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>EGP</span></h3>
            <p>إجمالي المبيعات (Total Revenue)</p>
          </div>
        </div>

        {/* Net Profit */}
        <div className="glass-card kpi-card">
          <div className="kpi-icon-wrap" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
            📈
          </div>
          <div className="kpi-details">
            <h3 style={{ color: '#10b981' }}>+{metrics.totalProfit.toLocaleString()} <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>EGP</span></h3>
            <p>صافي الأرباح المحققة (Net Profit)</p>
          </div>
        </div>

        {/* Active Repairs */}
        <div className="glass-card kpi-card">
          <div className="kpi-icon-wrap" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
            🛠️
          </div>
          <div className="kpi-details">
            <h3>{metrics.activeRepairsCount} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>أجهزة</span></h3>
            <p>تذاكر صيانة قيد العمل بالورشة</p>
          </div>
        </div>

        {/* Available Inventory */}
        <div className="glass-card kpi-card">
          <div className="kpi-icon-wrap" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}>
            📱
          </div>
          <div className="kpi-details">
            <h3>{metrics.inventoryAvailable} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>/ {metrics.inventoryTotal}</span></h3>
            <p>الأجهزة المتوفرة بالمخزون</p>
          </div>
        </div>
      </div>

      {/* Visual Analytics & Charts Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
        gap: 24,
        marginBottom: 28
      }}>
        {/* Sales & Profit Breakdown Visual Card */}
        <div className="glass-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>المؤشرات المالية (Financial Overview)</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>مقارنة الإيرادات والتكاليف وقيمة المخزون</p>
            </div>
            <span className="badge badge-info">{metrics.totalSalesCount} عملية بيع</span>
          </div>

          {/* Pure SVG Bar Visualizer */}
          <div style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                <span>إجمالي الإيرادات (Revenue)</span>
                <strong>{metrics.totalRevenue.toLocaleString()} EGP</strong>
              </div>
              <div style={{ height: 10, background: 'var(--bg-surface-elevated)', borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ width: '100%', height: '100%', background: 'linear-gradient(90deg, #0284c7, #38bdf8)' }}></div>
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                <span>صافي الأرباح (Net Profit)</span>
                <strong style={{ color: '#10b981' }}>+{metrics.totalProfit.toLocaleString()} EGP</strong>
              </div>
              <div style={{ height: 10, background: 'var(--bg-surface-elevated)', borderRadius: 6, overflow: 'hidden' }}>
                <div style={{
                  width: `${metrics.totalRevenue > 0 ? Math.min(100, Math.round((metrics.totalProfit / metrics.totalRevenue) * 100)) : 0}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #059669, #10b981)'
                }}></div>
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                <span>قيمة المخزون الحالي (Purchased Cost)</span>
                <strong>{metrics.inventoryValue.toLocaleString()} EGP</strong>
              </div>
              <div style={{ height: 10, background: 'var(--bg-surface-elevated)', borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ width: '75%', height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #c084fc)' }}></div>
              </div>
            </div>

            <div style={{
              marginTop: 20,
              padding: '14px',
              borderRadius: '8px',
              background: 'var(--bg-surface-elevated)',
              display: 'flex',
              justifyContent: 'space-around',
              textAlign: 'center'
            }}>
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>هامش الربح التقريبي</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#10b981' }}>
                  {metrics.totalRevenue > 0 ? ((metrics.totalProfit / metrics.totalRevenue) * 100).toFixed(1) : '0'}%
                </div>
              </div>
              <div style={{ width: 1, background: 'var(--border-color)' }}></div>
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>إجمالي العملاء المسجلين</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>
                  {metrics.totalCustomersCount}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Repair Workshop Status Breakdown */}
        <div className="glass-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <div>
              <h3 style={{ fontSize: '1.15rem' }}>حالات تذاكر الصيانة (Repairs Status)</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>توزيع الأجهزة داخل ورشة الصيانة</p>
            </div>
            <button onClick={() => navigate('/repairs')} className="btn btn-secondary btn-sm">
              عرض الكل
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
            {Object.entries(repairStatusLabels).map(([key, info]) => {
              const count = metrics.repairsByStatus[key] || 0;
              const totalRepairs = Object.values(metrics.repairsByStatus).reduce((a, b) => a + b, 0);
              const percentage = totalRepairs > 0 ? Math.round((count / totalRepairs) * 100) : 0;

              return (
                <div key={key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem', marginBottom: 4 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: info.color }}></span>
                      {info.label}
                    </span>
                    <span style={{ fontWeight: 600 }}>{count} ({percentage}%)</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--bg-surface-elevated)', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ width: `${percentage}%`, height: '100%', background: info.color }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Activity Feeds */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: 24
      }}>
        {/* Latest Sales */}
        <div className="glass-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.1rem' }}>أحدث عمليات البيع (Recent Sales)</h3>
            <button onClick={() => navigate('/sales')} className="btn btn-ghost btn-sm">سجل الفواتير ←</button>
          </div>

          {recentSales.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>لا توجد مبيعات مسجلة حتى الآن.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {recentSales.map((sale) => (
                <div
                  key={sale.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      {sale.item_description || `عملية بيع #${sale.id}`}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      العميل: {sale.customer_name || 'نقدي'} • {new Date(sale.date).toLocaleDateString()}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                      {Number(sale.sale_price).toLocaleString()} EGP
                    </div>
                    <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                      +{Number(sale.profit || 0).toFixed(0)} EGP ربح
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Latest Repairs */}
        <div className="glass-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.1rem' }}>أحدث تذاكر الصيانة (Recent Repairs)</h3>
            <button onClick={() => navigate('/repairs')} className="btn btn-ghost btn-sm">إدارة الصيانة ←</button>
          </div>

          {recentRepairs.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>لا توجد أجهزة قيد الصيانة حالياً.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {recentRepairs.map((rep) => {
                const info = repairStatusLabels[rep.status] || { label: rep.status, color: '#38bdf8' };
                return (
                  <div
                    key={rep.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                        {rep.device_info}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        العطل: {rep.issue_description} • العميل: {rep.customer_name || 'نقدي'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          background: `${info.color}20`,
                          color: info.color,
                          border: `1px solid ${info.color}40`
                        }}
                      >
                        {info.label}
                      </span>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, marginTop: 4 }}>
                        {Number(rep.customer_payment).toLocaleString()} EGP
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
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
    <div className="app-container">
      {token && <Navbar username={username || undefined} onLogout={logout} />}

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
