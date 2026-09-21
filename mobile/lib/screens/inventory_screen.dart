import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/inventory_model.dart';
import '../providers/inventory_provider.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => context.read<InventoryProvider>().fetchInventory());
  }

  void _showAddDeviceDialog() {
    final nameCtrl = TextEditingController();
    final brandCtrl = TextEditingController();
    final modelCtrl = TextEditingController();
    final costCtrl = TextEditingController();
    final saleCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: const Color(0xFF1E293B),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('إضافة جهاز / صنف جديد', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: 'اسم الجهاز الوصفي', hintText: 'مثال: iPhone 15 Pro Max 256GB'),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: brandCtrl,
                        decoration: const InputDecoration(labelText: 'الماركة', hintText: 'Apple'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: modelCtrl,
                        decoration: const InputDecoration(labelText: 'الموديل', hintText: '15 Pro Max'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: costCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'سعر الشراء (EGP)'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: saleCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'سعر البيع (EGP)'),
                      ),
                    ),
                  ],
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
              child: const Text('حفظ الجهاز'),
              onPressed: () async {
                final name = nameCtrl.text.trim();
                final brand = brandCtrl.text.trim();
                final model = modelCtrl.text.trim();
                final cost = double.tryParse(costCtrl.text.trim()) ?? 0.0;
                final sale = double.tryParse(saleCtrl.text.trim()) ?? 0.0;

                if (name.isEmpty || brand.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('يرجى كتابة اسم الجهاز والماركة')),
                  );
                  return;
                }

                final ok = await context.read<InventoryProvider>().addItem(
                      name: name,
                      brand: brand,
                      model: model,
                      purchasePrice: cost,
                      salePrice: sale,
                    );

                if (!mounted) return;
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(ok ? 'تم إضافة الجهاز للمخزن بنجاح' : 'حدث خطأ أثناء الإضافة')),
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
    final inv = context.watch<InventoryProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('المخزون والأجهزة (Inventory)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => inv.fetchInventory(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xFF0284C7),
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('إضافة جهاز', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        onPressed: _showAddDeviceDialog,
      ),
      body: Column(
        children: [
          // Search & Filter Box
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: const Color(0xFF1E293B),
            child: Column(
              children: [
                TextField(
                  onChanged: (val) => inv.setSearchQuery(val),
                  decoration: const InputDecoration(
                    hintText: 'بحث بالاسم، الماركة، أو الموديل...',
                    prefixIcon: Icon(Icons.search, color: Color(0xFF38BDF8)),
                    contentPadding: EdgeInsets.symmetric(vertical: 10),
                  ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  height: 35,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: inv.availableBrands.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 8),
                    itemBuilder: (context, idx) {
                      final brand = inv.availableBrands[idx];
                      final isSelected = brand == inv.selectedBrand;
                      return ChoiceChip(
                        label: Text(brand, style: TextStyle(fontSize: 12, color: isSelected ? Colors.white : const Color(0xFF94A3B8))),
                        selected: isSelected,
                        selectedColor: const Color(0xFF0284C7),
                        backgroundColor: const Color(0xFF0F172A),
                        onSelected: (_) => inv.setSelectedBrand(brand),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),

          // Items Count Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: const Color(0xFF0F172A),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'الأجهزة المتاحة: ${inv.totalStockCount} جهاز',
                  style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12, fontWeight: FontWeight.bold),
                ),
                Text(
                  'إجمالي النتائج: ${inv.filteredItems.length}',
                  style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 12),
                ),
              ],
            ),
          ),

          // Inventory List
          Expanded(
            child: inv.isLoading
                ? const Center(child: CircularProgressIndicator())
                : inv.filteredItems.isEmpty
                    ? const Center(
                        child: Text('لا توجد أجهزة مطابقة للبحث', style: TextStyle(color: Color(0xFF64748B))),
                      )
                    : RefreshIndicator(
                        onRefresh: () => inv.fetchInventory(),
                        child: ListView.separated(
                          padding: const EdgeInsets.all(16),
                          itemCount: inv.filteredItems.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (context, idx) {
                            final item = inv.filteredItems[idx];
                            return Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: const Color(0xFF1E293B),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: const Color(0xFF334155)),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: item.isAvailable ? Colors.green.withOpacity(0.15) : Colors.red.withOpacity(0.15),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Icon(
                                      Icons.phone_android,
                                      color: item.isAvailable ? Colors.greenAccent : Colors.redAccent,
                                      size: 24,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          item.name,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                                        ),
                                        const SizedBox(height: 3),
                                        Text(
                                          '${item.brand} • ${item.model}',
                                          style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                                        ),
                                        const SizedBox(height: 8),
                                        Row(
                                          children: [
                                            Text(
                                              'سعر البيع: ${item.salePrice.toStringAsFixed(2)} EGP',
                                              style: const TextStyle(color: Color(0xFF38BDF8), fontWeight: FontWeight.bold, fontSize: 12),
                                            ),
                                            const Spacer(),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                              decoration: BoxDecoration(
                                                color: item.isAvailable ? Colors.green.withOpacity(0.2) : Colors.grey.withOpacity(0.2),
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: Text(
                                                item.isAvailable ? 'متوفر بالمخزن' : 'مباع',
                                                style: TextStyle(
                                                  color: item.isAvailable ? Colors.greenAccent : Colors.grey,
                                                  fontSize: 10,
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
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
