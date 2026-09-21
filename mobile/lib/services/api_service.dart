import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000/api'; // 10.0.2.2 for Android emulator
  String? accessToken;

  Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        accessToken = data['access'];
        return true;
      }
    } catch (e) {
      print('Login error: $e');
    }
    return false;
  }

  Future<List<dynamic>> getInventory() async {
    final response = await http.get(
      Uri.parse('$baseUrl/inventory/'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  Future<List<dynamic>> getSales() async {
    final response = await http.get(
      Uri.parse('$baseUrl/sales/'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }
}
