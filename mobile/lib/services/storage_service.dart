import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  final _storage = const FlutterSecureStorage();

  static const _keyAccess = 'access_token';
  static const _keyRefresh = 'refresh_token';
  static const _keyBaseUrl = 'api_base_url';
  static const _keyUsername = 'saved_username';

  static const defaultBaseUrl = 'http://10.0.2.2:8000/api';

  Future<void> saveTokens({required String access, String? refresh}) async {
    await _storage.write(key: _keyAccess, value: access);
    if (refresh != null) {
      await _storage.write(key: _keyRefresh, value: refresh);
    }
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: _keyAccess);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: _keyRefresh);
  }

  Future<void> saveUsername(String username) async {
    await _storage.write(key: _keyUsername, value: username);
  }

  Future<String?> getUsername() async {
    return await _storage.read(key: _keyUsername);
  }

  Future<void> setBaseUrl(String url) async {
    await _storage.write(key: _keyBaseUrl, value: url.trim().replaceAll(RegExp(r'/+$'), ''));
  }

  Future<String> getBaseUrl() async {
    final saved = await _storage.read(key: _keyBaseUrl);
    return saved ?? defaultBaseUrl;
  }

  Future<void> clearAll() async {
    await _storage.delete(key: _keyAccess);
    await _storage.delete(key: _keyRefresh);
    await _storage.delete(key: _keyUsername);
  }
}
