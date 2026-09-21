import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/sale_model.dart';
import '../providers/sales_provider.dart';

class SalesScreen extends StatefulWidget {
  const SalesScreen({super.key});

  @override
  State<SalesScreen> createState() => _SalesScreenState();
}

class _SalesScreenState extends State<SalesScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<SalesProvider>().fetchSales());
  }

  void _showNewSaleDialog() {
    final itemCtrl = TextEditingController();
    final custCtrl = TextEditingController(text: 'عميل نقدي');
    final qtyCtrl = TextEditingController(text: '1');
    final costCtrl = TextEditingController(text: '0.00');
    final saleCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: const Color(0xFF1E293B),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('تسجيل عملية بيع جديدة (POS)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: itemCtrl,
                  decoration: const InputDecoration(labelText: 'الصنف / الجهاز المبيع', hintText: 'شاحن 45W / جراب / هاتف...'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: custCtrl,
                  decoration: const InputDecoration(labelText: 'اسم العميل'),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: qtyCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'الكمية'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: costCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'التكلفة للوحدة'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: saleCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'سعر البيع للوحدة (EGP)'),
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
              child: const Text('إتمام البيع'),
              onPressed: () async {
                final item = itemCtrl.text.trim();
                final cust = custCtrl.text.trim();
                final qty = int.tryParse(qtyCtrl.text.trim()) ?? 1;
                final cost = double.tryParse(costCtrl.text.trim()) ?? 0.0;
                final sale = double.tryParse(saleCtrl.text.trim()) ?? 0.0;

                if (item.isEmpty || sale <= 0) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('يرجى كتابة وصف الصنف وسعر البيع بشكل صحيح')),
                  );
                  return;
                }

                final ok = await context.read<SalesProvider>().recordSale(
                      itemDescription: item,
                      customerName: cust,
                      quantity: qty,
                      costPrice: cost,
                      salePrice: sale,
                    );

                if (!mounted) return;
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(ok ? 'تم تسجيل الفاتورة بنجاح' : 'حدث خطأ أثناء حفظ الفاتورة')),
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
    final salesProv = context.watch<SalesProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('المبيعات والفواتير (Sales & POS)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => salesProv.fetchSales(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xFF10B981),
        icon: const Icon(Icons.shopping_cart_checkout, color: Colors.white),
        label: const Text('تسجيل بيع (POS)', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        onPressed: _showNewSaleDialog,
      ),
      body: Column(
        children: [
          // KPI Banner
          Container(
            margin: const EdgeInsets.all(16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF064E3B), Color(0xFF0F766E)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF059669)),
            ],
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'إجمالي المبيعات المحققة',
                        style: TextStyle(color: Color(0xFFA7F3D0), fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${salesProv.totalRevenue.toStringAsFixed(2)} EGP',
                        style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
                Container(width: 1, height: 35, color: const Color(0xFF059669)),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'صافي الأرباح المحققة',
                        style: TextStyle(color: Color(0xFFA7F3D0), fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '+${salesProv.totalProfit.toStringAsFixed(2)} EGP',
                        style: const TextStyle(color: Color(0xFF6EE7B7), fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Sales List
          Expanded(
            child: salesProv.isLoading
                ? const Center(child: CircularProgressIndicator())
                : salesProv.sales.isEmpty
                    ? const Center(
                        child: Text('لا توجد عمليات بيع مسجلة حتى الآن', style: TextStyle(color: Color(0xFF64748B))),
                      )
                    : RefreshIndicator(
                        onRefresh: () => salesProv.fetchSales(),
                        child: ListView.separated(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          itemCount: salesProv.sales.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (context, idx) {
                            final s = salesProv.sales[idx];
                            return Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: const Color(0xFF1E293B),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFF334155)),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF10B981).withOpacity(0.15),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: const Icon(Icons.receipt_long, color: Color(0xFF34D399), size: 24),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          s.itemDescription,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          'فاتورة #${s.invoiceId} • العميل: ${s.customerName}',
                                          style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          'الكمية: ${s.quantity} قطعة',
                                          style: const TextStyle(color: Color(0xFF64748B), fontSize: 11),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text(
                                        '${s.totalAmount.toStringAsFixed(2)} EGP',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'ربح: +${s.profit.toStringAsFixed(2)}',
                                        style: const TextStyle(color: Color(0xFF34D399), fontWeight: FontWeight.bold, fontSize: 11),
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
