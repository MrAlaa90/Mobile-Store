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
    { path: '/', label: 'Dashboard', arLabel: 'لوحة التحكم', shortLabel: 'الرئيسية', icon: '📊' },
    { path: '/inventory', label: 'Inventory', arLabel: 'المخزون', shortLabel: 'المخزون', icon: '📦' },
    { path: '/sales', label: 'Sales & POS', arLabel: 'المبيعات والفواتير', shortLabel: 'المبيعات', icon: '💰' },
    { path: '/repairs', label: 'Repairs', arLabel: 'قسم الصيانة', shortLabel: 'الصيانة', icon: '🛠️' },
    { path: '/customers', label: 'Customers', arLabel: 'العملاء', shortLabel: 'العملاء', icon: '👥' },
  ];

  return (
    <>
      <header className="navbar-header">
      <div className="navbar-container">
        {/* Main Row: Brand (Left), Desktop Nav (Center), Desktop Actions (Right) */}
        <div className="navbar-main-row">
          {/* Brand & Logo */}
          <div
            onClick={() => navigate('/')}
            className="navbar-brand"
          >
            <div className="navbar-logo-icon">📱</div>
            <div>
              <div className="navbar-brand-name">
                Mobile-Store <span className="navbar-brand-badge">POS</span>
              </div>
              <div className="navbar-brand-status">
                <span className="navbar-status-indicator"></span>
                System Connected
              </div>
            </div>
          </div>

          {/* Navigation Tabs (Desktop Only) */}
          <nav className="desktop-nav">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`desktop-nav-link ${isActive ? 'active' : ''}`}
                >
                  <span>{link.icon}</span>
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Tools (Desktop Only) */}
          <div className="desktop-actions">
            {/* Downloads Center Button */}
            <button
              onClick={() => setShowDownloads(true)}
              className="nav-action-btn btn-downloads"
              title="تحميل تطبيق الموبايل وبرنامج الديسكتوب"
            >
              <span style={{ fontSize: '1rem' }}>📥</span>
              <span>تنزيل التطبيقات</span>
            </button>

            {/* Theme Switcher Button */}
            <button
              onClick={toggleTheme}
              aria-label="Toggle Theme"
              className="nav-action-btn btn-theme"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>

            {/* User Profile */}
            <div className="nav-user-pill">
              <div className="nav-user-avatar">
                {(username || 'U')[0].toUpperCase()}
              </div>
              <div className="nav-user-details">
                <span className="nav-user-name">
                  {username || 'Store Admin'}
                </span>
                <span className="nav-user-role">Online Terminal</span>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="nav-action-btn btn-logout"
              title="تسجيل الخروج من النظام"
            >
              <span>🚪</span>
              <span>خروج</span>
            </button>
          </div>
        </div>

        {/* Dedicated Mobile Controls Strip (Mobile Devices <= 768px ONLY) */}
        <div className="mobile-header-subbar">
          <div className="mobile-user-tag">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="mobile-user-avatar">
                {(username || 'U')[0].toUpperCase()}
              </div>
              <div className="mobile-user-text" dir="rtl">
                <span className="mobile-user-label">المستخدم: </span>
                <bdi className="mobile-user-name">{username || 'admin'}</bdi>
              </div>
            </div>
            <span className="mobile-user-status" dir="rtl">
              <span className="status-dot"></span>
              متصل
            </span>
          </div>

          <div className="mobile-actions-grid">
            <button
              onClick={() => setShowDownloads(true)}
              className="mobile-btn-download"
              title="تحميل تطبيق الموبايل وبرنامج الديسكتوب"
            >
              <span>📥</span>
              <span>تنزيل التطبيقات</span>
            </button>
            <button
              onClick={toggleTheme}
              className="mobile-btn-theme"
              title="تبديل الوضع الليلي / الفاتح"
            >
              <span>{theme === 'dark' ? '☀️ فاتح' : '🌙 داكن'}</span>
            </button>
            <button
              onClick={onLogout}
              className="mobile-btn-logout"
              title="تسجيل الخروج من النظام"
            >
              <span>🚪</span>
              <span>خروج</span>
            </button>
          </div>
        </div>
      </div>
    </header>

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
            <span>{link.shortLabel || link.arLabel}</span>
          </Link>
        );
      })}
    </nav>

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
