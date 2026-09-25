import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

interface NavbarProps {
  username?: string;
  onLogout: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ username, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [showDownloads, setShowDownloads] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showDownloads) {
        setShowDownloads(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showDownloads]);

  const navLinks = [
    { path: '/', label: 'Dashboard', arLabel: 'لوحة التحكم', icon: '📊' },
    { path: '/inventory', label: 'Inventory', arLabel: 'المخزون', icon: '📦' },
    { path: '/sales', label: 'Sales & POS', arLabel: 'المبيعات والفواتير', icon: '💰' },
    { path: '/repairs', label: 'Repairs', arLabel: 'قسم الصيانة', icon: '🛠️' },
    { path: '/customers', label: 'Customers', arLabel: 'العملاء', icon: '👥' },
  ];

  return (
    <>
      <header style={{
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-color)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      transition: 'all var(--transition-normal)'
    }}>
      <div style={{
        maxWidth: 1360,
        margin: '0 auto',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16
      }}>
        {/* Brand & Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div
            onClick={() => navigate('/')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              cursor: 'pointer',
              textDecoration: 'none'
            }}
          >
            <div style={{
              width: 38,
              height: 38,
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.25rem',
              boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)'
            }}>
              📱
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.15rem', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Mobile-Store <span style={{ color: 'var(--primary-light)', fontSize: '0.85rem', fontWeight: 600 }}>POS</span>
              </div>
              <div className="nav-hide-mobile" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }}></span>
                System Connected
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs (Desktop) */}
        <nav className="desktop-nav" style={{
          alignItems: 'center',
          gap: 6,
          background: 'var(--bg-surface-elevated)',
          padding: '4px',
          borderRadius: '12px',
          border: '1px solid var(--border-color)'
        }}>
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '7px 14px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 700 : 500,
                  textDecoration: 'none',
                  color: isActive ? '#ffffff' : 'var(--text-secondary)',
                  background: isActive ? 'linear-gradient(135deg, #0284c7, #2563eb)' : 'transparent',
                  boxShadow: isActive ? '0 2px 8px rgba(37, 99, 235, 0.35)' : 'none',
                  transition: 'all var(--transition-fast)'
                }}
              >
                <span>{link.icon}</span>
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Tools (Theme Toggle, User Info, Logout) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Downloads Center Button */}
          <button
            onClick={() => setShowDownloads(true)}
            style={{
              padding: '7px 11px',
              borderRadius: '10px',
              border: '1px solid var(--primary-border, rgba(2, 132, 199, 0.4))',
              background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.15), rgba(56, 189, 248, 0.15))',
              color: 'var(--primary-light, #0284c7)',
              cursor: 'pointer',
              fontSize: '0.82rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              transition: 'all var(--transition-fast)'
            }}
            title="تحميل تطبيق الموبايل وبرنامج الديسكتوب"
          >
            <span style={{ fontSize: '1rem' }}>📥</span>
            <span className="nav-hide-mobile">تنزيل التطبيقات</span>
          </button>

          {/* Theme Switcher Button */}
          <button
            onClick={toggleTheme}
            aria-label="Toggle Theme"
            style={{
              width: 36,
              height: 36,
              borderRadius: '10px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-elevated)',
              color: 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '1rem',
              transition: 'all var(--transition-fast)'
            }}
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>

          {/* User Profile */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '4px 8px',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px'
          }}>
            <div style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.75rem',
              fontWeight: 800,
              color: '#fff'
            }}>
              {(username || 'U')[0].toUpperCase()}
            </div>
            <div className="nav-hide-mobile" style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {username || 'Store Admin'}
              </span>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Online Terminal</span>
            </div>
          </div>

          {/* Logout Button */}
          <button
            onClick={onLogout}
            style={{
              padding: '7px 11px',
              borderRadius: '10px',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              background: 'rgba(239, 68, 68, 0.12)',
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: '0.82rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              transition: 'all var(--transition-fast)'
            }}
            title="تسجيل الخروج من النظام"
          >
            <span>🚪</span>
            <span className="nav-hide-mobile">خروج</span>
          </button>
        </div>
      </div>

      {/* Mobile Bottom App Navigation Bar */}
      <nav className="mobile-bottom-nav">
        {navLinks.map((link) => {
          const isActive = location.pathname === link.path;
          return (
            <Link
              key={link.path}
              to={link.path}
              className={`mobile-bottom-link ${isActive ? 'active' : ''}`}
            >
              <span className="mobile-bottom-icon">{link.icon}</span>
              <span>{link.arLabel}</span>
            </Link>
          );
        })}
      </nav>
    </header>

    {/* Downloads Modal Dialog (Portaled to document.body outside header containing block) */}
    {showDownloads && createPortal(
      <div
        className="modal-overlay"
        onClick={() => setShowDownloads(false)}
        role="dialog"
        aria-modal="true"
      >
        <div
          className="modal-content"
          style={{ maxWidth: 560 }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>📥</span>
                <span>مركز تنزيل تطبيقات النظام</span>
              </h3>
              <p style={{ margin: '4px 0 0 0', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                حزم التثبيت الرسمية الجاهزة للعمل والربط السحابي التلقائي
              </p>
            </div>
            <button
              onClick={() => setShowDownloads(false)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '1.4rem',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                padding: '4px 8px',
                lineHeight: 1
              }}
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Windows Desktop Setup */}
            <div className="download-card-responsive" style={{
              padding: '16px',
              borderRadius: '12px',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  background: 'rgba(2, 132, 199, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.6rem',
                  flexShrink: 0
                }}>
                  💻
                </div>
                <div>
                  <h4 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700 }}>
                    برنامج الكاشير والديسكتوب (Windows)
                  </h4>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    ملف تثبيت كامل <code>MobileStore-Setup.exe</code> مع دعم الأوفلاين وحماية العتاد
                  </p>
                </div>
              </div>
              <a
                href="/downloads/MobileStore-Setup.exe"
                download="MobileStore-Setup.exe"
                className="btn btn-primary"
                style={{ textDecoration: 'none', whiteSpace: 'nowrap', padding: '9px 16px', fontSize: '0.85rem' }}
              >
                تحميل (.EXE)
              </a>
            </div>

            {/* Android Release APK */}
            <div className="download-card-responsive" style={{
              padding: '16px',
              borderRadius: '12px',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.6rem',
                  flexShrink: 0
                }}>
                  📱
                </div>
                <div>
                  <h4 style={{ margin: 0, fontSize: '0.96rem', fontWeight: 700 }}>
                    تطبيق الهاتف للمتابعة (Android APK)
                  </h4>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    نسخة الإنتاج الرسمية <code>MobileStore.apk</code> تثبيت مباشر وسريع
                  </p>
                </div>
              </div>
              <a
                href="/downloads/MobileStore.apk"
                download="MobileStore.apk"
                className="btn btn-success"
                style={{ textDecoration: 'none', whiteSpace: 'nowrap', padding: '9px 16px', fontSize: '0.85rem' }}
              >
                تحميل (.APK)
              </a>
            </div>

            <div style={{
              marginTop: 4,
              padding: '12px',
              borderRadius: '8px',
              background: 'rgba(2, 132, 199, 0.08)',
              border: '1px solid rgba(2, 132, 199, 0.2)',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              textAlign: 'center'
            }}>
              💡 التطبيقات مربوطة مسبقاً بالسيرفر السحابي <code>http://34.175.186.221/api</code> تلقائياً وتمنحك فترة تجريبية 20 يوماً عند أول تشغيل.
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              onClick={() => setShowDownloads(false)}
              className="btn btn-secondary"
            >
              إغلاق النافذة
            </button>
          </div>
        </div>
      </div>,
      document.body
    )}
  </>
  );
};

export default Navbar;
