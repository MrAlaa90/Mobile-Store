import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import api from '../api';
import { useToast } from './Toast';

export interface DeviceItem {
  id: number;
  name: string;
  hardware_id: string;
  device_type: 'desktop' | 'mobile' | 'tablet';
  is_active: boolean;
  license: number | null;
  license_key?: string;
  username?: string;
  store_name?: string;
  created_at: string;
  last_seen: string;
}

interface DeviceManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const DeviceManagementModal: React.FC<DeviceManagementModalProps> = ({ isOpen, onClose }) => {
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const toast = useToast();

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/devices/');
      setDevices(response.data);
    } catch {
      toast.error('تعذر جلب قائمة الأجهزة المتصلة من السيرفر');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (isOpen) {
      fetchDevices();
    }
  }, [isOpen, fetchDevices]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleDelete = async (device: DeviceItem) => {
    const confirmMessage = `هل أنت متأكد من رغبتك في حذف وإلغاء ربط هذا الجهاز (${device.name || device.hardware_id.slice(0, 10)})؟\nسيتم تحرير مقعد الترخيص فوراً ولن يتمكن هذا الجهاز من الاتصال مجدداً إلا بعد إعادة تسجيله.`;
    if (!window.confirm(confirmMessage)) return;

    setDeletingId(device.id);
    try {
      await api.delete(`/devices/${device.id}/`);
      toast.success(`تم حذف الجهاز (${device.name || device.hardware_id.slice(0, 8)}) وإلغاء ربطه بنجاح`);
      setDevices((prev) => prev.filter((d) => d.id !== device.id));
    } catch {
      toast.error('حدث خطأ أثناء محاولة حذف الجهاز');
    } finally {
      setDeletingId(null);
    }
  };

  const handleToggleActive = async (device: DeviceItem) => {
    setTogglingId(device.id);
    try {
      const newStatus = !device.is_active;
      await api.patch(`/devices/${device.id}/`, { is_active: newStatus });
      setDevices((prev) =>
        prev.map((d) => (d.id === device.id ? { ...d, is_active: newStatus } : d))
      );
      toast.success(newStatus ? 'تم تنشيط الجهاز والسماح له بالاتصال' : 'تم تجميد وتعطيل الجهاز بنجاح');
    } catch {
      toast.error('تعذر تعديل حالة الجهاز');
    } finally {
      setTogglingId(null);
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'desktop':
        return '💻';
      case 'mobile':
        return '📱';
      case 'tablet':
        return '📟';
      default:
        return '🖥️';
    }
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'غير متوفر';
    try {
      const date = new Date(isoString);
      return date.toLocaleString('ar-EG', {
        dateStyle: 'short',
        timeStyle: 'short',
      });
    } catch {
      return isoString;
    }
  };

  if (!isOpen) return null;

  const filteredDevices = devices.filter((d) => {
    const q = searchQuery.toLowerCase();
    return (
      (d.name && d.name.toLowerCase().includes(q)) ||
      (d.hardware_id && d.hardware_id.toLowerCase().includes(q)) ||
      (d.username && d.username.toLowerCase().includes(q)) ||
      (d.store_name && d.store_name.toLowerCase().includes(q))
    );
  });

  return createPortal(
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="modal-content"
        style={{ maxWidth: 760, maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>💻</span>
              <span>إدارة الأجهزة المتصلة والتراخيص</span>
            </h3>
            <p style={{ margin: '4px 0 0 0', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              مراقبة وإلغاء ربط أجهزة الكاشير وتطبيقات الهواتف المرتبطة بحسابك
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.4rem',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '4px 8px',
              lineHeight: 1,
            }}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Toolbar: Search & Refresh */}
        <div style={{
          padding: '12px 20px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
          background: 'var(--bg-surface)'
        }}>
          <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
            <input
              type="text"
              placeholder="🔍 ابحث بالاسم أو بصمة الجهاز (HWID)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field"
              style={{
                width: '100%',
                padding: '8px 12px',
                fontSize: '0.85rem',
                borderRadius: 8,
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-elevated)',
                color: 'var(--text-primary)'
              }}
            />
          </div>
          <button
            onClick={fetchDevices}
            disabled={loading}
            className="btn"
            style={{
              padding: '8px 14px',
              fontSize: '0.85rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              borderRadius: 8
            }}
          >
            <span style={{ display: 'inline-block', transform: loading ? 'rotate(180deg)' : 'none', transition: 'transform 0.5s' }}>🔄</span>
            <span>تحديث القائمة</span>
          </button>
        </div>

        {/* Body: Devices List */}
        <div className="modal-body" style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {loading && devices.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '1.8rem', marginBottom: 8 }}>⏳</div>
              <div>جارٍ تحميل الأجهزة المتصلة بالسيرفر...</div>
            </div>
          ) : filteredDevices.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '36px 16px',
              borderRadius: 12,
              background: 'var(--bg-surface-elevated)',
              border: '1px dashed var(--border-color)',
              color: 'var(--text-muted)'
            }}>
              <div style={{ fontSize: '2.2rem', marginBottom: 8 }}>🖥️</div>
              <h4 style={{ margin: '0 0 6px 0', color: 'var(--text-primary)', fontSize: '1rem' }}>
                {searchQuery ? 'لا توجد أجهزة مطابقة للبحث' : 'لا توجد أجهزة متصلة مسجلة حالياً'}
              </h4>
              <p style={{ margin: 0, fontSize: '0.82rem' }}>
                عند تشغيل تطبيق الديسكتوب أو تسجيل الدخول من هاتف جديد، سيظهر الجهاز هنا تلقائياً.
              </p>
            </div>
          ) : (
            filteredDevices.map((device) => (
              <div
                key={device.id}
                style={{
                  padding: '14px 16px',
                  borderRadius: 12,
                  background: 'var(--bg-surface-elevated)',
                  border: `1px solid ${device.is_active ? 'var(--border-color)' : 'rgba(239, 68, 68, 0.3)'}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 16,
                  flexWrap: 'wrap',
                  transition: 'all 0.2s ease',
                  opacity: device.is_active ? 1 : 0.75
                }}
              >
                {/* Left: Device Info */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 240, flex: 1 }}>
                  <div style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: device.is_active
                      ? 'linear-gradient(135deg, rgba(2, 132, 199, 0.2), rgba(56, 189, 248, 0.2))'
                      : 'rgba(239, 68, 68, 0.15)',
                    border: `1px solid ${device.is_active ? 'rgba(2, 132, 199, 0.4)' : 'rgba(239, 68, 68, 0.3)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.4rem',
                    flexShrink: 0
                  }}>
                    {getDeviceIcon(device.device_type)}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                        {device.name || `جهاز #${device.id}`}
                      </strong>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 6,
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: device.is_active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: device.is_active ? '#10b981' : '#ef4444',
                        border: `1px solid ${device.is_active ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                      }}>
                        {device.is_active ? '● نشط ومصرح له' : '⛔ معطل ومجمد'}
                      </span>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: 6,
                        fontSize: '0.7rem',
                        background: 'var(--bg-surface)',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border-color)'
                      }}>
                        {device.device_type === 'desktop' ? 'كمبيوتر كاشير' : 'هاتف محمول'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4, flexWrap: 'wrap', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                      <span>بصمة العتاد (HWID): <code style={{ color: 'var(--primary-light)', fontSize: '0.75rem' }}>{device.hardware_id.slice(0, 18)}...</code></span>
                      {device.username && <span>المتجر: <strong style={{ color: 'var(--text-secondary)' }}>{device.store_name || device.username}</strong></span>}
                      <span>آخر اتصال: {formatDate(device.last_seen)}</span>
                    </div>
                  </div>
                </div>

                {/* Right: Actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <button
                    onClick={() => handleToggleActive(device)}
                    disabled={togglingId === device.id}
                    title={device.is_active ? 'تعطيل الجهاز وتجميد عمله' : 'تنشيط الجهاز والسماح بالاتصال'}
                    style={{
                      padding: '7px 12px',
                      borderRadius: 8,
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-surface)',
                      color: device.is_active ? 'var(--warning, #f59e0b)' : '#10b981',
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <span>{device.is_active ? '⏸️ إيقاف' : '▶️ تفعيل'}</span>
                  </button>

                  <button
                    onClick={() => handleDelete(device)}
                    disabled={deletingId === device.id}
                    title="حذف الجهاز وإلغاء ربطه من الترخيص فوراً"
                    style={{
                      padding: '7px 12px',
                      borderRadius: 8,
                      border: '1px solid rgba(239, 68, 68, 0.4)',
                      background: 'rgba(239, 68, 68, 0.12)',
                      color: '#ef4444',
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <span>{deletingId === device.id ? '⏳' : '🗑️'}</span>
                    <span>{deletingId === device.id ? 'جارٍ الحذف...' : 'حذف وإلغاء الربط'}</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer / Tip */}
        <div style={{
          padding: '12px 20px',
          borderTop: '1px solid var(--border-color)',
          background: 'var(--bg-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.8rem',
          flexWrap: 'wrap',
          gap: 10
        }}>
          <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>💡</span>
            <span>حذف أي جهاز يحرر مقعد الترخيص فوراً لسيرفر المتجر.</span>
          </div>

          <a
            href="/admin/api/device/"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: 'var(--primary-light)',
              textDecoration: 'none',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}
          >
            <span>⚙️ لوحة تحكم Django Admin المتقدمة</span>
            <span>↗</span>
          </a>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default DeviceManagementModal;
