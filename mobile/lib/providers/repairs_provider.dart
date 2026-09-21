import 'package:flutter/material.dart';
import '../models/repair_model.dart';
import '../services/api_service.dart';

class RepairsProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<RepairModel> _tickets = [];
  bool _isLoading = false;
  String _selectedStatus = 'all';

  List<RepairModel> get tickets => _tickets;
  bool get isLoading => _isLoading;
  String get selectedStatus => _selectedStatus;

  List<RepairModel> get filteredTickets {
    if (_selectedStatus == 'all') {
      return _tickets;
    }
    return _tickets.where((t) => t.status == _selectedStatus).toList();
  }

  int get activeRepairsCount => _tickets
      .where((t) => t.status != 'delivered' && t.status != 'cancelled')
      .length;

  double get totalRemainingBalance => _tickets
      .where((t) => t.status != 'delivered' && t.status != 'cancelled')
      .fold(0.0, (sum, t) => sum + t.remainingBalance);

  Future<void> fetchRepairs() async {
    _isLoading = true;
    notifyListeners();

    _tickets = await _api.getRepairs();
    _isLoading = false;
    notifyListeners();
  }

  void setSelectedStatus(String status) {
    _selectedStatus = status;
    notifyListeners();
  }

  Future<bool> updateStatus(int ticketId, String newStatus) async {
    final success = await _api.updateRepairStatus(ticketId, newStatus);
    if (success) {
      final index = _tickets.indexWhere((t) => t.id == ticketId);
      if (index != -1) {
        final current = _tickets[index];
        _tickets[index] = RepairModel(
          id: current.id,
          customerName: current.customerName,
          deviceInfo: current.deviceInfo,
          issueDescription: current.issueDescription,
          repairCost: current.repairCost,
          customerPayment: current.customerPayment,
          deposit: current.deposit,
          profit: current.profit,
          status: newStatus,
          createdAt: current.createdAt,
        );
        notifyListeners();
      }
      return true;
    }
    return false;
  }

  Future<bool> createTicket({
    required String customerName,
    required String deviceInfo,
    required String issueDescription,
    required double repairCost,
    required double customerPayment,
    required double deposit,
    String status = 'diagnosing',
  }) async {
    final newTicket = RepairModel(
      id: 0,
      customerName: customerName,
      deviceInfo: deviceInfo,
      issueDescription: issueDescription,
      repairCost: repairCost,
      customerPayment: customerPayment,
      deposit: deposit,
      profit: customerPayment - repairCost,
      status: status,
    );

    final created = await _api.createRepair(newTicket);
    if (created != null) {
      _tickets.insert(0, created);
      notifyListeners();
      return true;
    }
    return false;
  }
}
