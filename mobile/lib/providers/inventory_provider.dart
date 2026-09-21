import 'package:flutter/material.dart';
import '../models/inventory_model.dart';
import '../services/api_service.dart';

class InventoryProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<InventoryModel> _items = [];
  bool _isLoading = false;
  String _searchQuery = '';
  String _selectedBrand = 'All';

  List<InventoryModel> get items => _items;
  bool get isLoading => _isLoading;
  String get searchQuery => _searchQuery;
  String get selectedBrand => _selectedBrand;

  List<String> get availableBrands {
    final brands = _items.map((e) => e.brand.trim()).where((b) => b.isNotEmpty).toSet().toList();
    brands.sort();
    return ['All', ...brands];
  }

  List<InventoryModel> get filteredItems {
    return _items.where((item) {
      final matchesSearch = _searchQuery.isEmpty ||
          item.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          item.brand.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          item.model.toLowerCase().contains(_searchQuery.toLowerCase());

      final matchesBrand = _selectedBrand == 'All' ||
          item.brand.toLowerCase() == _selectedBrand.toLowerCase();

      return matchesSearch && matchesBrand;
    }).toList();
  }

  int get totalStockCount => _items.where((i) => i.isAvailable).length;
  double get totalInventoryValue => _items
      .where((i) => i.isAvailable)
      .fold(0.0, (sum, item) => sum + item.purchasePrice);

  Future<void> fetchInventory() async {
    _isLoading = true;
    notifyListeners();

    _items = await _api.getInventory();
    _isLoading = false;
    notifyListeners();
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  void setSelectedBrand(String brand) {
    _selectedBrand = brand;
    notifyListeners();
  }

  Future<bool> addItem({
    required String name,
    required String brand,
    required String model,
    required double purchasePrice,
    required double salePrice,
  }) async {
    final newItem = InventoryModel(
      id: 0,
      name: name,
      brand: brand,
      model: model,
      purchasePrice: purchasePrice,
      salePrice: salePrice,
      status: 'available',
    );

    final created = await _api.createInventory(newItem);
    if (created != null) {
      _items.insert(0, created);
      notifyListeners();
      return true;
    }
    return false;
  }
}
