import React, { useEffect, useState, useMemo } from 'react';
import api from '../api';
import { useToast } from './Toast';

interface Customer {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  created_at: string;
}

const CustomerManagement: React.FC = () => {
  const toast = useToast();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const res = await api.get('/customers/');
      setCustomers(res.data);
    } catch (err) {
      console.error(err);
      toast.error('فشل في تحميل قائمة العملاء');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  const handleAddCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !phone.trim()) {
      toast.warning('يرجى إدخال اسم العميل ورقم الهاتف');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post('/customers/', {
        name: name.trim(),
        phone: phone.trim(),
        email: email.trim() || null,
      });
      setCustomers([res.data, ...customers]);
      setName('');
      setPhone('');
      setEmail('');
      setIsAddModalOpen(false);
      toast.success(`تمت إضافة العميل (${res.data.name}) بنجاح!`);
    } catch (err) {
      console.error(err);
      toast.error('حدث خطأ أثناء حفظ بيانات العميل');
    } finally {
      setSubmitting(false);
    }
  };

  // Filter customers by search
  const filteredCustomers = useMemo(() => {
    const query = searchQuery.toLowerCase();
    return customers.filter((c) => {
      return (
        c.name.toLowerCase().includes(query) ||
        c.phone.includes(query) ||
        (c.email || '').toLowerCase().includes(query) ||
        c.id.toString().includes(query)
      );
    });
  }, [customers, searchQuery]);

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
            <span>👥 إدارة العملاء والاتصال (Customer Directory)</span>
          </h1>
          <p className="page-subtitle">
            سجل عملاء المتجر ومتابعة أرقام الهواتف والتواصل السريع
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="btn btn-primary"
        >
          <span>➕</span>
          <span>إضافة عميل جديد (Add Customer)</span>
        </button>
      </div>

      {/* Stats and Search Bar */}
      <div className="glass-card" style={{ padding: 18, marginBottom: 20 }}>
        <div style={{
          display: 'flex',
          gap: 14,
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap'
        }}>
          {/* Search Input */}
          <div style={{ flex: '1 1 320px', position: 'relative' }}>
            <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
              🔍
            </span>
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: 40 }}
              placeholder="ابحث بالاسم، رقم التليفون أو البريد الإلكتروني..."
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

          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            إجمالي العملاء: <strong>{filteredCustomers.length}</strong> عميل
          </div>
        </div>
      </div>

      {/* Table of Customers */}
      {loading ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          جاري تحميل بيانات العملاء...
        </div>
      ) : filteredCustomers.length === 0 ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>👥</div>
          <h4>لا يوجد عملاء مطابقين للبحث</h4>
          <p style={{ fontSize: '0.85rem', marginTop: 6 }}>سجل عميلاً جديداً بالضغط على "إضافة عميل جديد"</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: 70 }}>#ID</th>
                <th>اسم العميل</th>
                <th>رقم الهاتف والتواصل</th>
                <th>البريد الإلكتروني</th>
                <th>تاريخ التسجيل</th>
                <th style={{ textAlign: 'center' }}>إجراءات سريعة</th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((c) => {
                // Clean phone for whatsapp
                const cleanPhone = c.phone.replace(/[^0-9]/g, '');
                const waPhone = cleanPhone.startsWith('0') ? `2${cleanPhone}` : cleanPhone;

                return (
                  <tr key={c.id}>
                    <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>#{c.id}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 34,
                          height: 34,
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
                          color: '#fff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          fontSize: '0.85rem'
                        }}>
                          {c.name ? c.name[0].toUpperCase() : 'C'}
                        </div>
                        <strong style={{ fontSize: '0.95rem' }}>{c.name}</strong>
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {c.phone}
                      </div>
                    </td>
                    <td>
                      <span style={{ color: c.email ? 'var(--text-secondary)' : 'var(--text-muted)', fontSize: '0.85rem' }}>
                        {c.email || '-'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <div style={{ display: 'inline-flex', gap: 8 }}>
                        <a
                          href={`tel:${c.phone}`}
                          className="btn btn-secondary btn-sm"
                          style={{ textDecoration: 'none' }}
                          title="اتصال هاتفي"
                        >
                          📞 اتصال
                        </a>
                        <a
                          href={`https://wa.me/${waPhone}`}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-success btn-sm"
                          style={{ textDecoration: 'none', background: '#25d366' }}
                          title="محادثة واتساب"
                        >
                          💬 واتساب
                        </a>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Customer Modal */}
      {isAddModalOpen && (
        <div className="modal-overlay" onClick={() => setIsAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1.2rem' }}>إضافة عميل جديد</h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.3rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddCustomer}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">اسم العميل بالكامل</label>
                  <input
                    className="form-input"
                    placeholder="مثال: أحمد محمود إبراهيم"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">رقم الهاتف المحمول</label>
                  <input
                    className="form-input"
                    placeholder="مثال: 01012345678"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">البريد الإلكتروني (اختياري)</label>
                  <input
                    className="form-input"
                    type="email"
                    placeholder="customer@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
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
                  {submitting ? 'جاري الحفظ...' : 'حفظ العميل'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerManagement;
