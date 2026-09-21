import 'package:flutter/material.dart';
import '../models/sale_model.dart';
import '../services/api_service.dart';

class SalesProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<SaleModel> _sales = [];
  bool _isLoading = false;

  List<SaleModel> get sales => _sales;
  bool get isLoading => _isLoading;

  double get totalRevenue => _sales.fold(0.0, (sum, s) => sum + s.totalAmount);
  double get totalProfit => _sales.fold(0.0, (sum, s) => sum + s.profit);

  Future<void> fetchSales() async {
    _isLoading = true;
    notifyListeners();

    _sales = await _api.getSales();
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> recordSale({
    required String itemDescription,
    required String customerName,
    required int quantity,
    required double costPrice,
    required double salePrice,
  }) async {
    final invoiceId = 'MOB-${DateTime.now().millisecondsSinceEpoch.toRadixString(16).toUpperCase()}';
    final newSale = SaleModel(
      id: 0,
      invoiceId: invoiceId,
      itemDescription: itemDescription,
      customerName: customerName,
      quantity: quantity,
      costPrice: costPrice,
      salePrice: salePrice,
      profit: (salePrice - costPrice) * quantity,
    );

    final created = await _api.createSale(newSale);
    if (created != null) {
      _sales.insert(0, created);
      notifyListeners();
      return true;
    }
    return false;
  }
}
