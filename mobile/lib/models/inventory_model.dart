class InventoryModel {
  final int id;
  final String name;
  final String brand;
  final String model;
  final double purchasePrice;
  final double salePrice;
  final String status;
  final String? createdAt;

  InventoryModel({
    required this.id,
    required this.name,
    required this.brand,
    required this.model,
    required this.purchasePrice,
    required this.salePrice,
    required this.status,
    this.createdAt,
  });

  bool get isAvailable => status == 'available';
  double get estimatedProfit => salePrice - purchasePrice;

  factory InventoryModel.fromJson(Map<String, dynamic> json) {
    return InventoryModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      brand: json['brand'] ?? '',
      model: json['model'] ?? '',
      purchasePrice: double.tryParse(json['purchase_price']?.toString() ?? '0') ?? 0.0,
      salePrice: double.tryParse(json['sale_price']?.toString() ?? '0') ?? 0.0,
      status: json['status'] ?? 'available',
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'brand': brand,
      'model': model,
      'purchase_price': purchasePrice.toStringAsFixed(2),
      'sale_price': salePrice.toStringAsFixed(2),
      'status': status,
    };
  }
}
