import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/inventory_model.dart';
import '../models/repair_model.dart';
import '../models/sale_model.dart';
import '../models/customer_model.dart';
import 'storage_service.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final StorageService _storage = StorageService();

  Future<String> get baseUrl async => await _storage.getBaseUrl();

  Future<Map<String, String>> _getHeaders({bool auth = true}) async {
    final headers = {'Content-Type': 'application/json'};
    if (auth) {
      final token = await _storage.getAccessToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return headers;
  }

  // -------------------------------------------------------------
  // HEALTH & AUTHENTICATION
  // -------------------------------------------------------------
  Future<bool> checkHealth([String? customUrl]) async {
    try {
      final targetUrl = customUrl ?? await baseUrl;
      final uri = Uri.parse('$targetUrl/health/');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<bool> login(String username, String password) async {
    try {
      final url = await baseUrl;
      final res = await http.post(
        Uri.parse('$url/auth/login/'),
        headers: await _getHeaders(auth: false),
        body: jsonEncode({'username': username.trim(), 'password': password}),
      ).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final access = data['access'];
        final refresh = data['refresh'];
        if (access != null) {
          await _storage.saveTokens(access: access, refresh: refresh);
          await _storage.saveUsername(username);
          return true;
        }
      }
    } catch (e) {
      print('Login error: $e');
    }
    return false;
  }

  Future<bool> refreshToken() async {
    final refresh = await _storage.getRefreshToken();
    if (refresh == null) return false;

    try {
      final url = await baseUrl;
      final res = await http.post(
        Uri.parse('$url/auth/refresh/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': refresh}),
      ).timeout(const Duration(seconds: 5));

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final newAccess = data['access'];
        if (newAccess != null) {
          await _storage.saveTokens(access: newAccess);
          return true;
        }
      }
    } catch (e) {
      print('Refresh token error: $e');
    }
    return false;
  }

  Future<void> logout() async {
    await _storage.clearAll();
  }

  // -------------------------------------------------------------
  // INVENTORY
  // -------------------------------------------------------------
  Future<List<InventoryModel>> getInventory() async {
    try {
      final url = await baseUrl;
      var res = await http.get(
        Uri.parse('$url/inventory/'),
        headers: await _getHeaders(),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.get(
          Uri.parse('$url/inventory/'),
          headers: await _getHeaders(),
        );
      }

      if (res.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(res.bodyBytes));
        return data.map((json) => InventoryModel.fromJson(json)).toList();
      }
    } catch (e) {
      print('getInventory error: $e');
    }
    return [];
  }

  Future<InventoryModel?> createInventory(InventoryModel item) async {
    try {
      final url = await baseUrl;
      var res = await http.post(
        Uri.parse('$url/inventory/'),
        headers: await _getHeaders(),
        body: jsonEncode(item.toJson()),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.post(
          Uri.parse('$url/inventory/'),
          headers: await _getHeaders(),
          body: jsonEncode(item.toJson()),
        );
      }

      if (res.statusCode == 200 || res.statusCode == 201) {
        return InventoryModel.fromJson(jsonDecode(utf8.decode(res.bodyBytes)));
      }
    } catch (e) {
      print('createInventory error: $e');
    }
    return null;
  }

  // -------------------------------------------------------------
  // REPAIRS
  // -------------------------------------------------------------
  Future<List<RepairModel>> getRepairs() async {
    try {
      final url = await baseUrl;
      var res = await http.get(
        Uri.parse('$url/repairs/'),
        headers: await _getHeaders(),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.get(
          Uri.parse('$url/repairs/'),
          headers: await _getHeaders(),
        );
      }

      if (res.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(res.bodyBytes));
        return data.map((json) => RepairModel.fromJson(json)).toList();
      }
    } catch (e) {
      print('getRepairs error: $e');
    }
    return [];
  }

  Future<RepairModel?> createRepair(RepairModel repair) async {
    try {
      final url = await baseUrl;
      var res = await http.post(
        Uri.parse('$url/repairs/'),
        headers: await _getHeaders(),
        body: jsonEncode(repair.toJson()),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.post(
          Uri.parse('$url/repairs/'),
          headers: await _getHeaders(),
          body: jsonEncode(repair.toJson()),
        );
      }

      if (res.statusCode == 200 || res.statusCode == 201) {
        return RepairModel.fromJson(jsonDecode(utf8.decode(res.bodyBytes)));
      }
    } catch (e) {
      print('createRepair error: $e');
    }
    return null;
  }

  Future<bool> updateRepairStatus(int id, String newStatus) async {
    try {
      final url = await baseUrl;
      var res = await http.patch(
        Uri.parse('$url/repairs/$id/'),
        headers: await _getHeaders(),
        body: jsonEncode({'status': newStatus}),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.patch(
          Uri.parse('$url/repairs/$id/'),
          headers: await _getHeaders(),
          body: jsonEncode({'status': newStatus}),
        );
      }

      return res.statusCode == 200 || res.statusCode == 204;
    } catch (e) {
      print('updateRepairStatus error: $e');
    }
    return false;
  }

  // -------------------------------------------------------------
  // SALES
  // -------------------------------------------------------------
  Future<List<SaleModel>> getSales() async {
    try {
      final url = await baseUrl;
      var res = await http.get(
        Uri.parse('$url/sales/'),
        headers: await _getHeaders(),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.get(
          Uri.parse('$url/sales/'),
          headers: await _getHeaders(),
        );
      }

      if (res.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(res.bodyBytes));
        return data.map((json) => SaleModel.fromJson(json)).toList();
      }
    } catch (e) {
      print('getSales error: $e');
    }
    return [];
  }

  Future<SaleModel?> createSale(SaleModel sale) async {
    try {
      final url = await baseUrl;
      var res = await http.post(
        Uri.parse('$url/sales/'),
        headers: await _getHeaders(),
        body: jsonEncode(sale.toJson()),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.post(
          Uri.parse('$url/sales/'),
          headers: await _getHeaders(),
          body: jsonEncode(sale.toJson()),
        );
      }

      if (res.statusCode == 200 || res.statusCode == 201) {
        return SaleModel.fromJson(jsonDecode(utf8.decode(res.bodyBytes)));
      }
    } catch (e) {
      print('createSale error: $e');
    }
    return null;
  }

  // -------------------------------------------------------------
  // CUSTOMERS
  // -------------------------------------------------------------
  Future<List<CustomerModel>> getCustomers() async {
    try {
      final url = await baseUrl;
      var res = await http.get(
        Uri.parse('$url/customers/'),
        headers: await _getHeaders(),
      );

      if (res.statusCode == 401 && await refreshToken()) {
        res = await http.get(
          Uri.parse('$url/customers/'),
          headers: await _getHeaders(),
        );
      }

      if (res.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(res.bodyBytes));
        return data.map((json) => CustomerModel.fromJson(json)).toList();
      }
    } catch (e) {
      print('getCustomers error: $e');
    }
    return [];
  }
}
