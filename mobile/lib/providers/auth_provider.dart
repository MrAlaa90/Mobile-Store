import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  final StorageService _storage = StorageService();

  bool _isLoading = false;
  bool _isAuthenticated = false;
  String? _username;
  String? _errorMessage;

  bool get isLoading => _isLoading;
  bool get isAuthenticated => _isAuthenticated;
  String? get username => _username;
  String? get errorMessage => _errorMessage;

  Future<void> checkSession() async {
    final token = await _storage.getAccessToken();
    _username = await _storage.getUsername();
    if (token != null) {
      _isAuthenticated = true;
      notifyListeners();
    }
  }

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final success = await _api.login(username, password);
    _isLoading = false;

    if (success) {
      _isAuthenticated = true;
      _username = username;
    } else {
      _isAuthenticated = false;
      _errorMessage = 'فشل تسجيل الدخول. تحقق من اسم المستخدم أو كلمة المرور أو اتصال السيرفر.';
    }

    notifyListeners();
    return success;
  }

  Future<void> logout() async {
    await _api.logout();
    _isAuthenticated = false;
    _username = null;
    notifyListeners();
  }
}
