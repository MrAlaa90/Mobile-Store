import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import 'login_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _storage = StorageService();
  String _currentBaseUrl = '';
  String _pingResult = '';
  bool _isPinging = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  void _loadSettings() async {
    final url = await _storage.getBaseUrl();
    setState(() => _currentBaseUrl = url);
  }

  void _testConnection() async {
    setState(() {
      _isPinging = true;
      _pingResult = 'جاري اختبار السيرفر...';
    });
    final ok = await ApiService().checkHealth();
    setState(() {
      _isPinging = false;
      _pingResult = ok ? '🟢 السيرفر متصل ويعمل بنجاح (HTTP 200)' : '🔴 تعذر الاتصال بالسيرفر، تحقق من الشبكة';
    });
  }

  void _editUrl() {
    final ctrl = TextEditingController(text: _currentBaseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('تعديل عنوان السيرفر'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(labelText: 'API Base URL'),
        ),
        actions: [
          TextButton(child: const Text('إلغاء'), onPressed: () => Navigator.pop(ctx)),
          ElevatedButton(
            child: const Text('حفظ'),
            onPressed: () async {
              await _storage.setBaseUrl(ctrl.text.trim());
              _loadSettings();
              if (!mounted) return;
              Navigator.pop(ctx);
            },
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('إعدادات النظام (Settings)')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // User Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF334155)),
            ),
            child: Row(
              children: [
                const CircleAvatar(
                  backgroundColor: Color(0xFF0284C7),
                  child: Icon(Icons.person, color: Colors.white),
                ),
                const SizedBox(width: 14),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      auth.username ?? 'admin',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                    ),
                    const Text(
                      'مدير النظام (Administrator)',
                      style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Server Connection Section
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF334155)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'عنوان السيرفر (API Host)',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                ),
                const SizedBox(height: 8),
                Text(
                  _currentBaseUrl.isEmpty ? 'Loading...' : _currentBaseUrl,
                  style: const TextStyle(color: Color(0xFF38BDF8), fontFamily: 'monospace', fontSize: 12),
                ),
                if (_pingResult.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(_pingResult, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ],
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        icon: _isPinging
                            ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.wifi_tethering, size: 16),
                        label: const Text('فحص الاتصال'),
                        onPressed: _isPinging ? null : _testConnection,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.edit, size: 16),
                        label: const Text('تغيير العنوان'),
                        onPressed: _editUrl,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 25),

          // Logout Button
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFEF4444),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            icon: const Icon(Icons.logout),
            label: const Text('تسجيل الخروج من الحساب', style: TextStyle(fontWeight: FontWeight.bold)),
            onPressed: () async {
              await auth.logout();
              if (!mounted) return;
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => const LoginScreen()),
                (route) => false,
              );
            },
          ),
        ],
      ),
    );
  }
}
