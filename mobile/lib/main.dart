import 'package:flutter/material.dart';

void main() {
  runApp(const MobileStoreApp());
}

class MobileStoreApp extends StatelessWidget {
  const MobileStoreApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Mobile Store POS',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const MobileStoreLogin(),
    );
  }
}

class MobileStoreLogin extends StatefulWidget {
  const MobileStoreLogin({super.key});

  @override
  State<MobileStoreLogin> createState() => _MobileStoreLoginState();
}

class _MobileStoreLoginState extends State<MobileStoreLogin> {
  final _usernameController = TextEditingController(text: 'store_a');
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  void _login() async {
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));
    setState(() => _isLoading = false);
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const MobileStoreDashboard()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mobile Store Login')),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _usernameController,
              decoration: const InputDecoration(labelText: 'Username', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 15),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Password', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isLoading ? null : _login,
              child: _isLoading ? const CircularProgressIndicator() : const Text('Sign In'),
            ),
          ],
        ),
      ),
    );
  }
}

class MobileStoreDashboard extends StatelessWidget {
  const MobileStoreDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mobile Store Dashboard')),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: const [
          Card(
            child: ListTile(
              leading: Icon(Icons.inventory, color: Colors.blue),
              title: Text('Inventory Management'),
              subtitle: Text('Manage phones and accessories in stock'),
            ),
          ),
          Card(
            child: ListTile(
              leading: Icon(Icons.point_of_sale, color: Colors.green),
              title: Text('Sales & Invoices'),
              subtitle: Text('Record new sales and customer receipts'),
            ),
          ),
          Card(
            child: ListTile(
              leading: Icon(Icons.build, color: Colors.orange),
              title: Text('Repairs & Maintenance'),
              subtitle: Text('Track maintenance status and costs'),
            ),
          ),
        ],
      ),
    );
  }
}
