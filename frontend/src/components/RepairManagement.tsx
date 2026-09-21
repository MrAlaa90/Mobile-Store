import React, { useEffect, useState, useMemo } from 'react';
import api from '../api';
import { useToast } from './Toast';

const STATUS_CHOICES = [
  { value: 'diagnosing', label: 'قيد الفحص والتشخيص', color: '#38bdf8' },
  { value: 'waiting_parts', label: 'في انتظار قطع الغيار', color: '#fb923c' },
  { value: 'in_progress', label: 'قيد الصيانة والإصلاح', color: '#facc15' },
  { value: 'ready', label: 'جاهز للاستلام', color: '#34d399' },
  { value: 'delivered', label: 'تم التسليم ومكتمل', color: '#10b981' },
  { value: 'cancelled', label: 'مرفوض / تعذر الإصلاح', color: '#ef4444' },
];

interface Repair {
  id: number;
  customer?: number;
  customer_name?: string;
  device_info: string;
  issue_description: string;
  repair_cost: string; // تكلفة على المحل
  customer_payment: string; // سعر الإصلاح للعميل
  deposit: string; // المدفوع تحت الحساب
  remaining_balance?: string; // المتبقي
  profit: string;
  status: string;
  created_at: string;
}

interface Customer {
  id: number;
  name: string;
  phone: string;
}

const RepairManagement: React.FC = () => {
  const toast = useToast();
  const [repairs, setRepairs] = useState<Repair[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // New repair form state
  const [selectedCustomer, setSelectedCustomer] = useState<number | ''>('');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [deviceInfo, setDeviceInfo] = useState('');
  const [issueDescription, setIssueDescription] = useState('');
  const [repairCost, setRepairCost] = useState('');
  const [customerPayment, setCustomerPayment] = useState('');
  const [deposit, setDeposit] = useState('0.00');
  const [repairStatus, setRepairStatus] = useState('diagnosing');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [repairsRes, custRes] = await Promise.all([
        api.get('/repairs/'),
        api.get('/customers/'),
      ]);
      setRepairs(repairsRes.data);
      setCustomers(custRes.data);
    } catch (err) {
      console.error(err);
      toast.error('فشل في تحميل تذاكر الصيانة');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Quick inline status change handler
  const handleUpdateStatus = async (repairId: number, newStatus: string) => {
    try {
      const res = await api.patch(`/repairs/${repairId}/`, { status: newStatus });
      setRepairs((prev) =>
        prev.map((r) => (r.id === repairId ? { ...r, status: res.data.status } : r))
      );
      const statusObj = STATUS_CHOICES.find((s) => s.value === newStatus);
      toast.success(`تم تحديث حالة التذكرة #${repairId} إلى (${statusObj?.label || newStatus})`);
    } catch (err) {
      console.error(err);
      toast.error('فشل تحديث حالة التذكرة');
    }
  };

  const handleCreateRepair = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deviceInfo || !issueDescription || !repairCost || !customerPayment) {
      toast.warning('يرجى استكمال بيانات العطل والتكلفة');
      return;
    }

    setSubmitting(true);
    try {
      let finalCustId = selectedCustomer || null;
      let finalCustName = customerName.trim();

      // If user provided a new customer with phone, create customer first
      if (!selectedCustomer && customerName.trim() && customerPhone.trim()) {
        try {
          const custRes = await api.post('/customers/', {
            name: customerName.trim(),
            phone: customerPhone.trim(),
          });
          finalCustId = custRes.data.id;
          finalCustName = custRes.data.name;
          setCustomers([custRes.data, ...customers]);
        } catch {
          // ignore, continue with manual name
        }
      } else if (selectedCustomer) {
        const found = customers.find((c) => c.id === selectedCustomer);
        if (found) finalCustName = found.name;
      }

      const res = await api.post('/repairs/', {
        customer: finalCustId,
        customer_name: finalCustName || 'عميل نقدي (Walk-in)',
        device_info: deviceInfo,
        issue_description: issueDescription,
        repair_cost: repairCost,
        customer_payment: customerPayment,
        deposit: deposit || '0.00',
        status: repairStatus,
      });

      setRepairs([res.data, ...repairs]);
      setDeviceInfo('');
      setIssueDescription('');
      setRepairCost('');
      setCustomerPayment('');
      setDeposit('0.00');
      setSelectedCustomer('');
      setCustomerName('');
      setCustomerPhone('');
      setRepairStatus('diagnosing');
      setIsAddModalOpen(false);

      toast.success(`تم استلام الجهاز وتسجيل تذكرة صيانة #${res.data.id} بنجاح!`);
    } catch (err) {
      console.error(err);
      toast.error('حدث خطأ أثناء حفظ تذكرة الصيانة');
    } finally {
      setSubmitting(false);
    }
  };

  // Filter repairs
  const filteredRepairs = useMemo(() => {
    return repairs.filter((rep) => {
      const matchesStatus = statusFilter === 'all' || rep.status === statusFilter;
      const query = searchQuery.toLowerCase();
      const matchesSearch =
        rep.device_info.toLowerCase().includes(query) ||
        rep.issue_description.toLowerCase().includes(query) ||
        (rep.customer_name || '').toLowerCase().includes(query) ||
        rep.id.toString().includes(query);

      return matchesStatus && matchesSearch;
    });
  }, [repairs, statusFilter, searchQuery]);

  // Statistics
  const stats = useMemo(() => {
    const total = repairs.length;
    const active = repairs.filter((r) => r.status !== 'delivered' && r.status !== 'cancelled').length;
    const completed = repairs.filter((r) => r.status === 'delivered').length;
    const totalRemaining = repairs.reduce((sum, r) => {
      const due = Number(r.remaining_balance || Number(r.customer_payment || 0) - Number(r.deposit || 0));
      return r.status !== 'delivered' && r.status !== 'cancelled' ? sum + Math.max(0, due) : sum;
    }, 0);

    return { total, active, completed, totalRemaining };
  }, [repairs]);

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
            <span>🛠️ قسم الصيانة وتتبع الأجهزة (Repair Management)</span>
          </h1>
          <p className="page-subtitle">
            استلام هواتف العملاء، تشخيص الأعطال، متابعة مراحل الصيانة والمدفوعات
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="btn btn-primary"
        >
          <span>➕</span>
          <span>استلام جهاز صيانة (New Ticket)</span>
        </button>
      </div>

      {/* Overview Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
        gap: 14,
        marginBottom: 22
      }}>
        <div className="glass-card" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>أجهزة قيد العمل بالورشة</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--primary-light)' }}>
              {stats.active} جهاز
            </div>
          </div>
          <span style={{ fontSize: '1.8rem' }}>⚙️</span>
        </div>

        <div className="glass-card" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>أجهزة تم تسليمها بنجاح</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981' }}>
              {stats.completed} جهاز
            </div>
          </div>
          <span style={{ fontSize: '1.8rem' }}>✅</span>
        </div>

        <div className="glass-card" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>مستحقات ومتبقيات لدى العملاء</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f59e0b' }}>
              {stats.totalRemaining.toLocaleString()} EGP
            </div>
          </div>
          <span style={{ fontSize: '1.8rem' }}>💳</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-card" style={{ padding: 18, marginBottom: 20 }}>
        <div style={{
          display: 'flex',
          gap: 14,
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          {/* Search Box */}
          <div style={{ flex: '1 1 300px', position: 'relative' }}>
            <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
              🔍
            </span>
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: 40 }}
              placeholder="ابحث برقم التذكرة، اسم الجهاز، العطل، أو اسم العميل..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Quick Count Badge */}
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            تذاكر معروضة: <strong>{filteredRepairs.length}</strong>
          </div>
        </div>

        {/* Status Filter Chips */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 14 }}>
          <button
            onClick={() => setStatusFilter('all')}
            style={{
              padding: '5px 12px',
              borderRadius: 20,
              fontSize: '0.78rem',
              border: '1px solid var(--border-color)',
              background: statusFilter === 'all' ? 'var(--primary)' : 'transparent',
              color: statusFilter === 'all' ? '#fff' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            جميع الحالات ({repairs.length})
          </button>
          {STATUS_CHOICES.map((choice) => {
            const count = repairs.filter((r) => r.status === choice.value).length;
            const isSelected = statusFilter === choice.value;
            return (
              <button
                key={choice.value}
                onClick={() => setStatusFilter(choice.value)}
                style={{
                  padding: '5px 12px',
                  borderRadius: 20,
                  fontSize: '0.78rem',
                  border: `1px solid ${isSelected ? choice.color : 'var(--border-color)'}`,
                  background: isSelected ? `${choice.color}25` : 'transparent',
                  color: isSelected ? choice.color : 'var(--text-secondary)',
                  cursor: 'pointer',
                  fontWeight: isSelected ? 700 : 500,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6
                }}
              >
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: choice.color }}></span>
                <span>{choice.label} ({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Repairs Table */}
      {loading ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          جاري تحميل تذاكر الصيانة...
        </div>
      ) : filteredRepairs.length === 0 ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🔧</div>
          <h4>لا توجد تذاكر صيانة مطابقة</h4>
          <p style={{ fontSize: '0.85rem', marginTop: 6 }}>اضغط على "استلام جهاز صيانة" لتسجيل أول جهاز</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: 70 }}>#تذكرة</th>
                <th>بيانات الجهاز</th>
                <th>وصف العطل</th>
                <th>العميل</th>
                <th>المطلوب / المدفوع</th>
                <th>المتبقي</th>
                <th>الربح</th>
                <th>الحالة والمرحلة</th>
                <th>تاريخ الاستلام</th>
              </tr>
            </thead>
            <tbody>
              {filteredRepairs.map((rep) => {
                const total = Number(rep.customer_payment || 0);
                const dep = Number(rep.deposit || 0);
                const remaining = total - dep;
                const profitNum = Number(rep.profit || 0);
                const currentStatus = STATUS_CHOICES.find((s) => s.value === rep.status) || STATUS_CHOICES[0];

                return (
                  <tr key={rep.id}>
                    <td>
                      <span style={{ fontWeight: 800, color: 'var(--primary-light)' }}>
                        #{rep.id}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{rep.device_info}</div>
                    </td>
                    <td>
                      <div style={{ maxWidth: 220, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {rep.issue_description}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{rep.customer_name || 'عميل نقدي'}</div>
                    </td>
                    <td>
                      <div><strong>{total.toLocaleString()} EGP</strong></div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        مقدم: {dep.toLocaleString()} EGP
                      </div>
                    </td>
                    <td>
                      {remaining <= 0 ? (
                        <span className="badge badge-success">خالص بالكامل</span>
                      ) : (
                        <span className="badge badge-warning">متبقي: {remaining.toLocaleString()} EGP</span>
                      )}
                    </td>
                    <td>
                      <span style={{ color: profitNum >= 0 ? '#10b981' : '#ef4444', fontWeight: 700 }}>
                        +{profitNum.toLocaleString()} EGP
                      </span>
                    </td>
                    <td>
                      <select
                        value={rep.status}
                        onChange={(e) => handleUpdateStatus(rep.id, e.target.value)}
                        className="form-select"
                        style={{
                          padding: '5px 8px',
                          fontSize: '0.8rem',
                          fontWeight: 700,
                          borderRadius: '6px',
                          border: `1px solid ${currentStatus.color}50`,
                          color: currentStatus.color,
                          background: 'var(--bg-surface-elevated)'
                        }}
                      >
                        {STATUS_CHOICES.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(rep.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add New Repair Ticket Modal */}
      {isAddModalOpen && (
        <div className="modal-overlay" onClick={() => setIsAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1.2rem' }}>استلام جهاز صيانة جديد (New Repair Ticket)</h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.3rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRepair}>
              <div className="modal-body">
                {/* Device Info */}
                <div className="form-group">
                  <label className="form-label">موديل ونوع الجهاز (Device Model & Color)</label>
                  <input
                    className="form-input"
                    placeholder="مثال: iPhone 13 Pro أزرق 128GB"
                    value={deviceInfo}
                    onChange={(e) => setDeviceInfo(e.target.value)}
                    required
                  />
                </div>

                {/* Issue Description */}
                <div className="form-group">
                  <label className="form-label">وصف المشكلة والعطل الفني بالتفصيل</label>
                  <textarea
                    className="form-input"
                    rows={2}
                    placeholder="مثال: الشاشة مكسورة - البصمة لا تعمل - يحتاج تغيير بطارية أصلية"
                    value={issueDescription}
                    onChange={(e) => setIssueDescription(e.target.value)}
                    required
                  />
                </div>

                {/* Customer Details */}
                <div className="form-group">
                  <label className="form-label">اختيار عميل مسجل (أو كتابة الاسم يدوياً)</label>
                  <select
                    className="form-select"
                    value={selectedCustomer}
                    onChange={(e) => setSelectedCustomer(Number(e.target.value))}
                  >
                    <option value="">-- عميل جديد أو يدوي أدناه --</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.phone})
                      </option>
                    ))}
                  </select>
                </div>

                {!selectedCustomer && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div className="form-group">
                      <label className="form-label">اسم العميل</label>
                      <input
                        className="form-input"
                        placeholder="اسم العميل"
                        value={customerName}
                        onChange={(e) => setCustomerName(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">رقم هاتف العميل</label>
                      <input
                        className="form-input"
                        placeholder="010xxxxxxxx"
                        value={customerPhone}
                        onChange={(e) => setCustomerPhone(e.target.value)}
                      />
                    </div>
                  </div>
                )}

                {/* Financial Details */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div className="form-group">
                    <label className="form-label">تكلفة قطع الغيار على المحل (EGP)</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-input"
                      placeholder="0.00"
                      value={repairCost}
                      onChange={(e) => setRepairCost(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">سعر الإصلاح المتفق مع العميل (EGP)</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-input"
                      placeholder="0.00"
                      value={customerPayment}
                      onChange={(e) => setCustomerPayment(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div className="form-group">
                    <label className="form-label">المبلغ المدفوع مقدماً (Deposit)</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-input"
                      placeholder="0.00"
                      value={deposit}
                      onChange={(e) => setDeposit(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">المرحلة الحالية</label>
                    <select
                      className="form-select"
                      value={repairStatus}
                      onChange={(e) => setRepairStatus(e.target.value)}
                    >
                      {STATUS_CHOICES.map((c) => (
                        <option key={c.value} value={c.value}>{c.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Summary calculation */}
                {customerPayment && repairCost && (
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: 8,
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.88rem'
                  }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>المتبقي على العميل: </span>
                      <strong>{(Number(customerPayment) - Number(deposit || 0)).toLocaleString()} EGP</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>صافي الربح: </span>
                      <strong style={{ color: '#10b981' }}>
                        +{(Number(customerPayment) - Number(repairCost)).toLocaleString()} EGP
                      </strong>
                    </div>
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
                  {submitting ? 'جاري الحفظ...' : 'تسجيل التذكرة واستلام الجهاز'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RepairManagement;
