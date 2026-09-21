import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/repairs_provider.dart';

class RepairsScreen extends StatefulWidget {
  const RepairsScreen({super.key});

  @override
  State<RepairsScreen> createState() => _RepairsScreenState();
}

class _RepairsScreenState extends State<RepairsScreen> {
  static const statusOptions = [
    ('all', 'الكل'),
    ('diagnosing', 'قيد الفحص والتشخيص'),
    ('waiting_parts', 'في انتظار قطع الغيار'),
    ('in_progress', 'قيد الصيانة والإصلاح'),
    ('ready', 'جاهز للاستلام'),
    ('delivered', 'تم التسليم ومكتمل'),
  ];

  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<RepairsProvider>().fetchRepairs());
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'diagnosing':
        return const Color(0xFF38BDF8); // Sky blue
      case 'waiting_parts':
        return const Color(0xFFFB923C); // Orange
      case 'in_progress':
        return const Color(0xFFFACC15); // Yellow
      case 'ready':
        return const Color(0xFF34D399); // Mint
      case 'delivered':
        return const Color(0xFF22C55E); // Green
      case 'cancelled':
        return const Color(0xFFEF4444); // Red
      default:
        return Colors.blue;
    }
  }

  void _showAddTicketDialog() {
    final custCtrl = TextEditingController();
    final devCtrl = TextEditingController();
    final issueCtrl = TextEditingController();
    final costCtrl = TextEditingController();
    final payCtrl = TextEditingController();
    final depCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: const Color(0xFF1E293B),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('تسجيل جهاز صيانة جديد', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: custCtrl,
                  decoration: const InputDecoration(labelText: 'اسم العميل', hintText: 'مثال: محمد علي'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: devCtrl,
                  decoration: const InputDecoration(labelText: 'نوع وموديل الجهاز', hintText: 'Samsung A54'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: issueCtrl,
                  maxLines: 2,
                  decoration: const InputDecoration(labelText: 'وصف المشكلة / العطل', hintText: 'تغيير شاشة أصلية أو باغة...'),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: costCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'التكلفة (قطع)'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: payCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'سعر العميل'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: depCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'المبلغ المدفوع مقدماً (عربون)'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              child: const Text('إلغاء', style: TextStyle(color: Color(0xFF94A3B8))),
              onPressed: () => Navigator.pop(ctx),
            ),
            ElevatedButton(
              child: const Text('حفظ التذكرة'),
              onPressed: () async {
                final cust = custCtrl.text.trim();
                final dev = devCtrl.text.trim();
                final issue = issueCtrl.text.trim();
                final cost = double.tryParse(costCtrl.text.trim()) ?? 0.0;
                final pay = double.tryParse(payCtrl.text.trim()) ?? 0.0;
                final dep = double.tryParse(depCtrl.text.trim()) ?? 0.0;

                if (cust.isEmpty || dev.isEmpty || issue.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('يرجى كتابة اسم العميل ونوع الجهاز ووصف العطل')),
                  );
                  return;
                }

                final ok = await context.read<RepairsProvider>().createTicket(
                      customerName: cust,
                      deviceInfo: dev,
                      issueDescription: issue,
                      repairCost: cost,
                      customerPayment: pay,
                      deposit: dep,
                    );

                if (!mounted) return;
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(ok ? 'تم تسجيل تذكرة الصيانة بنجاح' : 'حدث خطأ أثناء التسجيل')),
                );
              },
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final repairs = context.watch<RepairsProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('إدارة الصيانة (Repairs)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => repairs.fetchRepairs(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xFF0284C7),
        icon: const Icon(Icons.build, color: Colors.white),
        label: const Text('استلام جهاز', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        onPressed: _showAddTicketDialog,
      ),
      body: Column(
        children: [
          // Filter Chips
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: const Color(0xFF1E293B),
            child: SizedBox(
              height: 38,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: statusOptions.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, idx) {
                  final opt = statusOptions[idx];
                  final isSelected = opt.$1 == repairs.selectedStatus;
                  return ChoiceChip(
                    label: Text(opt.$2, style: TextStyle(fontSize: 11, color: isSelected ? Colors.white : const Color(0xFF94A3B8))),
                    selected: isSelected,
                    selectedColor: const Color(0xFF0284C7),
                    backgroundColor: const Color(0xFF0F172A),
                    onSelected: (_) => repairs.setSelectedStatus(opt.$1),
                  );
                },
              ),
            ),
          ),

          // Count Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: const Color(0xFF0F172A),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'أجهزة قيد العمل: ${repairs.activeRepairsCount} جهاز',
                  style: const TextStyle(color: Color(0xFFFACC15), fontSize: 12, fontWeight: FontWeight.bold),
                ),
                Text(
                  'المتبقي على العملاء: ${repairs.totalRemainingBalance.toStringAsFixed(2)} EGP',
                  style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 12, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),

          // Repairs List
          Expanded(
            child: repairs.isLoading
                ? const Center(child: CircularProgressIndicator())
                : repairs.filteredTickets.isEmpty
                    ? const Center(
                        child: Text('لا توجد تذاكر صيانة مسجلة في هذا القسم', style: TextStyle(color: Color(0xFF64748B))),
                      )
                    : RefreshIndicator(
                        onRefresh: () => repairs.fetchRepairs(),
                        child: ListView.separated(
                          padding: const EdgeInsets.all(16),
                          itemCount: repairs.filteredTickets.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 12),
                          itemBuilder: (context, idx) {
                            final ticket = repairs.filteredTickets[idx];
                            final statusColor = _getStatusColor(ticket.status);

                            return Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: const Color(0xFF1E293B),
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: const Color(0xFF334155)),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        '#${ticket.id} • ${ticket.customerName}',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white),
                                      ),
                                      // Status Dropdown
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8),
                                        decoration: BoxDecoration(
                                          color: statusColor.withOpacity(0.15),
                                          borderRadius: BorderRadius.circular(8),
                                          border: Border.all(color: statusColor.withOpacity(0.5)),
                                        ),
                                        child: DropdownButton<String>(
                                          value: ticket.status,
                                          underline: const SizedBox(),
                                          isDense: true,
                                          icon: Icon(Icons.arrow_drop_down, color: statusColor, size: 18),
                                          dropdownColor: const Color(0xFF1E293B),
                                          items: statusOptions
                                              .where((s) => s.$1 != 'all')
                                              .map((s) => DropdownMenuItem(
                                                    value: s.$1,
                                                    child: Text(s.$2, style: TextStyle(fontSize: 11, color: _getStatusColor(s.$1))),
                                                  ))
                                              .toList(),
                                          onChanged: (newVal) {
                                            if (newVal != null && newVal != ticket.status) {
                                              repairs.updateStatus(ticket.id, newVal);
                                            }
                                          },
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  Row(
                                    children: [
                                      const Icon(Icons.phone_android, size: 14, color: Color(0xFF94A3B8)),
                                      const SizedBox(width: 4),
                                      Text(
                                        ticket.deviceInfo,
                                        style: const TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF38BDF8), fontSize: 13),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    ticket.issueDescription,
                                    style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 12),
                                  ),
                                  const Divider(height: 20, color: Color(0xFF334155)),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        'سعر الإصلاح: ${ticket.customerPayment.toStringAsFixed(2)} EGP',
                                        style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                                      ),
                                      Text(
                                        'المتبقي: ${ticket.remainingBalance.toStringAsFixed(2)} EGP',
                                        style: TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.bold,
                                          color: ticket.remainingBalance > 0 ? const Color(0xFF38BDF8) : Colors.greenAccent,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}
