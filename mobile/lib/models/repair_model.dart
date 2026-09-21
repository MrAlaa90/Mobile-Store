class RepairModel {
  final int id;
  final String customerName;
  final String deviceInfo;
  final String issueDescription;
  final double repairCost;
  final double customerPayment;
  final double deposit;
  final double profit;
  final String status;
  final String? createdAt;

  RepairModel({
    required this.id,
    required this.customerName,
    required this.deviceInfo,
    required this.issueDescription,
    required this.repairCost,
    required this.customerPayment,
    required this.deposit,
    required this.profit,
    required this.status,
    this.createdAt,
  });

  double get remainingBalance => customerPayment - deposit;

  String get statusLabel {
    switch (status) {
      case 'diagnosing':
        return 'قيد الفحص والتشخيص';
      case 'waiting_parts':
        return 'في انتظار قطع الغيار';
      case 'in_progress':
        return 'قيد الصيانة والإصلاح';
      case 'ready':
        return 'جاهز للاستلام';
      case 'delivered':
        return 'تم التسليم ومكتمل';
      case 'cancelled':
        return 'مرفوض / تعذر الإصلاح';
      default:
        return status;
    }
  }

  factory RepairModel.fromJson(Map<String, dynamic> json) {
    final cost = double.tryParse(json['repair_cost']?.toString() ?? '0') ?? 0.0;
    final payment = double.tryParse(json['customer_payment']?.toString() ?? '0') ?? 0.0;
    final dep = double.tryParse(json['deposit']?.toString() ?? '0') ?? 0.0;
    final prof = double.tryParse(json['profit']?.toString() ?? '') ?? (payment - cost);

    return RepairModel(
      id: json['id'] ?? 0,
      customerName: json['customer_name'] ?? 'Walk-in Customer',
      deviceInfo: json['device_info'] ?? '',
      issueDescription: json['issue_description'] ?? '',
      repairCost: cost,
      customerPayment: payment,
      deposit: dep,
      profit: prof,
      status: json['status'] ?? 'diagnosing',
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'customer_name': customerName,
      'device_info': deviceInfo,
      'issue_description': issueDescription,
      'repair_cost': repairCost.toStringAsFixed(2),
      'customer_payment': customerPayment.toStringAsFixed(2),
      'deposit': deposit.toStringAsFixed(2),
      'status': status,
    };
  }
}
