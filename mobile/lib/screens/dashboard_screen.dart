import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/inventory_provider.dart';
import '../providers/repairs_provider.dart';
import '../providers/sales_provider.dart';
import '../widgets/kpi_card.dart';
import 'inventory_screen.dart';
import 'repairs_screen.dart';
import 'sales_screen.dart';
import 'settings_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<InventoryProvider>().fetchInventory();
      context.read<RepairsProvider>().fetchRepairs();
      context.read<SalesProvider>().fetchSales();
    });
  }

  void _refreshAll() {
    context.read<InventoryProvider>().fetchInventory();
    context.read<RepairsProvider>().fetchRepairs();
    context.read<SalesProvider>().fetchSales();
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      _buildDashboardHome(),
      const InventoryScreen(),
      const RepairsScreen(),
      const SalesScreen(),
    ];

    return Scaffold(
      body: screens[_currentIndex],
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Color(0xFF334155), width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          backgroundColor: const Color(0xFF1E293B),
          selectedItemColor: const Color(0xFF38BDF8),
          unselectedItemColor: const Color(0xFF94A3B8),
          type: BottomNavigationBarType.fixed,
          selectedFontSize: 12,
          unselectedFontSize: 11,
          onTap: (idx) => setState(() => _currentIndex = idx),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_outlined),
              activeIcon: Icon(Icons.dashboard),
              label: 'الرئيسية',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.inventory_2_outlined),
              activeIcon: Icon(Icons.inventory_2),
              label: 'المخزون',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.build_outlined),
              activeIcon: Icon(Icons.build),
              label: 'الصيانة',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.point_of_sale_outlined),
              activeIcon: Icon(Icons.point_of_sale),
              label: 'المبيعات',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDashboardHome() {
    final auth = context.watch<AuthProvider>();
    final inv = context.watch<InventoryProvider>();
    final repairs = context.watch<RepairsProvider>();
    final sales = context.watch<SalesProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF0284C7).withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.phone_android, color: Color(0xFF38BDF8), size: 18),
            ),
            const SizedBox(width: 8),
            const Text('Mobile Store Dashboard', style: TextStyle(fontSize: 16)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _refreshAll,
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Settings',
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => _refreshAll(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Welcome Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF0284C7), Color(0xFF1E3A8A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'أهلاً بك، ${auth.username ?? "Admin"} 👋',
                          style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'لوحة التحكم المباشرة - جاهز لإدارة العمليات',
                          style: TextStyle(color: Color(0xFFBAE6FD), fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.fiber_manual_record, color: Colors.greenAccent, size: 10),
                        SizedBox(width: 4),
                        Text('متصل', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 4 KPI Cards Grid
            Row(
              children: [
                Expanded(
                  child: KpiCard(
                    title: 'إجمالي المبيعات',
                    value: '${sales.totalRevenue.toStringAsFixed(0)} EGP',
                    subtitle: 'إجمالي المحصل',
                    icon: Icons.attach_money,
                    color: const Color(0xFF38BDF8),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: KpiCard(
                    title: 'صافي الأرباح',
                    value: '+${sales.totalProfit.toStringAsFixed(0)} EGP',
                    subtitle: 'هامش ربح ممتاز',
                    icon: Icons.trending_up,
                    color: const Color(0xFF10B981),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: KpiCard(
                    title: 'أجهزة الصيانة',
                    value: '${repairs.activeRepairsCount} جهاز',
                    subtitle: 'قيد الصيانة والفحص',
                    icon: Icons.build_circle_outlined,
                    color: const Color(0xFFFACC15),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: KpiCard(
                    title: 'المخزون المتوفر',
                    value: '${inv.totalStockCount} جهاز',
                    subtitle: 'جاهز للبيع الفوري',
                    icon: Icons.inventory_2_outlined,
                    color: const Color(0xFFA855F7),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 22),

            // Quick Nav Banner
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'أحدث تذاكر الصيانة',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                TextButton(
                  onPressed: () => setState(() => _currentIndex = 2),
                  child: const Text('عرض الكل', style: TextStyle(color: Color(0xFF38BDF8), fontSize: 12)),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // Recent Repairs Preview List
            if (repairs.tickets.isEmpty)
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Center(
                  child: Text('لا توجد تذاكر صيانة حالياً', style: TextStyle(color: Color(0xFF64748B))),
                ),
              )
            else
              ...repairs.tickets.take(3).map((t) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF334155)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.build, color: Color(0xFFFACC15), size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${t.customerName} - ${t.deviceInfo}',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white),
                            ),
                            Text(
                              t.statusLabel,
                              style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11),
                            ),
                          ],
                        ),
                      ),
                      Text(
                        '${t.customerPayment.toStringAsFixed(0)} EGP',
                        style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF38BDF8), fontSize: 12),
                      ),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }
}
