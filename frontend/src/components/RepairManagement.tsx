import React, { useEffect, useState } from 'react';
import api from '../api';

const STATUS_CHOICES = [
  { value: 'diagnosing', label: 'قيد الفحص والتشخيص' },
  { value: 'waiting_parts', label: 'في انتظار قطع الغيار' },
  { value: 'in_progress', label: 'قيد الصيانة والإصلاح' },
  { value: 'ready', label: 'جاهز للاستلام' },
  { value: 'delivered', label: 'تم التسليم ومكتمل' },
  { value: 'cancelled', label: 'مرفوض / تعذر الإصلاح' },
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
  status_display?: string;
  created_at: string;
}

interface Customer {
  id: number;
  name: string;
  phone: string;
}

const RepairManagement: React.FC = () => {
  const [repairs, setRepairs] = useState<Repair[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  // New repair form
  const [selectedCustomer, setSelectedCustomer] = useState<number | ''>('');
  const [customerName, setCustomerName] = useState('');
  const [deviceInfo, setDeviceInfo] = useState('');
  const [issueDescription, setIssueDescription] = useState('');
  const [repairCost, setRepairCost] = useState('');
  const [customerPayment, setCustomerPayment] = useState('');
  const [deposit, setDeposit] = useState('0.00');
  const [repairStatus, setRepairStatus] = useState('diagnosing');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

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
      setError('Failed to load repairs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateRepair = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deviceInfo || !issueDescription || !repairCost || !customerPayment) {
      setError('Please fill in all repair fields.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const custObj = customers.find(c => c.id === selectedCustomer);
      const res = await api.post('/repairs/', {
        customer: selectedCustomer || null,
        customer_name: custObj ? custObj.name : (customerName || 'عميل نقدي'),
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
    } catch (err) {
      console.error(err);
      setError('Failed to record repair ticket.');
    } finally {
      setSubmitting(false);
    }
  };

  const updateStatus = async (repairId: number, newStatus: string) => {
    try {
      const res = await api.patch(`/repairs/${repairId}/`, { status: newStatus });
      setRepairs(repairs.map(r => r.id === repairId ? res.data : r));
    } catch (err) {
      console.error(err);
      setError('Failed to update status.');
    }
  };

  const remaining = (Number(customerPayment || 0) - Number(deposit || 0)).toFixed(2);
  const estimatedProfit = (Number(customerPayment || 0) - Number(repairCost || 0)).toFixed(2);

  return (
    <div style={{ maxWidth: 1100, margin: '20px auto', fontFamily: 'sans-serif' }}>
      <h2>Repairs Management (إدارة الصيانة)</h2>
      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      <div style={{ background: '#f9f9f9', padding: 18, borderRadius: 8, marginBottom: 20, border: '1px solid #e2e8f0' }}>
        <h3 style={{ margin: '0 0 12px 0' }}>New Repair Ticket (تذكرة صيانة جديدة)</h3>
        <form onSubmit={handleCreateRepair} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
          <select
            value={selectedCustomer}
            onChange={e => {
              const val = e.target.value ? Number(e.target.value) : '';
              setSelectedCustomer(val);
              const cust = customers.find(c => c.id === val);
              if (cust) setCustomerName(cust.name);
            }}
            style={{ padding: 8 }}
          >
            <option value="">-- اختر عميل مسجل أو اكتب بالأسفل --</option>
            {customers.map(c => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.phone})
              </option>
            ))}
          </select>

          <input
            placeholder="اسم العميل / الهاتف"
            value={customerName}
            onChange={e => setCustomerName(e.target.value)}
            style={{ padding: 8 }}
          />

          <input
            placeholder="نوع الجهاز (مثلاً: iPhone 13)"
            value={deviceInfo}
            onChange={e => setDeviceInfo(e.target.value)}
            required
            style={{ padding: 8 }}
          />

          <input
            placeholder="وصف العطل (مثلاً: تغيير شاشة)"
            value={issueDescription}
            onChange={e => setIssueDescription(e.target.value)}
            required
            style={{ padding: 8 }}
          />

          <input
            type="number"
            step="0.01"
            placeholder="تكلفة المحل (Cost)"
            value={repairCost}
            onChange={e => setRepairCost(e.target.value)}
            required
            style={{ padding: 8 }}
          />

          <input
            type="number"
            step="0.01"
            placeholder="سعر الإصلاح للعميل (Price)"
            value={customerPayment}
            onChange={e => setCustomerPayment(e.target.value)}
            required
            style={{ padding: 8 }}
          />

          <input
            type="number"
            step="0.01"
            placeholder="المبلغ المدفوع تحت الحساب (Deposit)"
            value={deposit}
            onChange={e => setDeposit(e.target.value)}
            required
            style={{ padding: 8 }}
          />

          <select
            value={repairStatus}
            onChange={e => setRepairStatus(e.target.value)}
            style={{ padding: 8 }}
          >
            {STATUS_CHOICES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          <button type="submit" disabled={submitting} style={{ padding: 8, background: '#0284c7', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer', fontWeight: 'bold' }}>
            {submitting ? 'Creating...' : 'إنشاء تذكرة صيانة'}
          </button>
        </form>

        {(customerPayment || repairCost) && (
          <div style={{ display: 'flex', gap: 20, marginTop: 12, fontSize: 13, color: '#475569' }}>
            <span>المتبقي على العميل: <strong>{remaining} EGP</strong></span>
            <span>صافي الربح المتوقع: <strong style={{ color: Number(estimatedProfit) >= 0 ? '#16a34a' : '#dc2626' }}>{estimatedProfit} EGP</strong></span>
          </div>
        )}
      </div>

      {loading ? (
        <p>Loading repair tickets...</p>
      ) : repairs.length === 0 ? (
        <p>No repair tickets found.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ccc', background: '#f1f5f9' }}>
              <th style={{ padding: 8 }}>ID</th>
              <th style={{ padding: 8 }}>العميل</th>
              <th style={{ padding: 8 }}>الجهاز</th>
              <th style={{ padding: 8 }}>العطل</th>
              <th style={{ padding: 8 }}>التكلفة</th>
              <th style={{ padding: 8 }}>سعر الإصلاح</th>
              <th style={{ padding: 8 }}>تحت الحساب</th>
              <th style={{ padding: 8 }}>المتبقي</th>
              <th style={{ padding: 8 }}>الربح</th>
              <th style={{ padding: 8 }}>الحالة</th>
            </tr>
          </thead>
          <tbody>
            {repairs.map(r => {
              const rem = r.remaining_balance ?? (Number(r.customer_payment) - Number(r.deposit || 0)).toFixed(2);
              return (
                <tr key={r.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: 8 }}>#{r.id}</td>
                  <td style={{ padding: 8 }}><strong>{r.customer_name || `عميل #${r.customer}`}</strong></td>
                  <td style={{ padding: 8 }}>{r.device_info}</td>
                  <td style={{ padding: 8 }}>{r.issue_description}</td>
                  <td style={{ padding: 8 }}>{r.repair_cost} EGP</td>
                  <td style={{ padding: 8 }}>{r.customer_payment} EGP</td>
                  <td style={{ padding: 8, color: '#0284c7' }}>{r.deposit || '0.00'} EGP</td>
                  <td style={{ padding: 8, color: Number(rem) > 0 ? '#dc2626' : '#16a34a', fontWeight: 'bold' }}>
                    {rem} EGP
                  </td>
                  <td style={{ padding: 8, color: '#16a34a', fontWeight: 'bold' }}>{r.profit} EGP</td>
                  <td style={{ padding: 8 }}>
                    <select
                      value={r.status}
                      onChange={e => updateStatus(r.id, e.target.value)}
                      style={{ padding: 4, borderRadius: 4 }}
                    >
                      {STATUS_CHOICES.map(s => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default RepairManagement;
