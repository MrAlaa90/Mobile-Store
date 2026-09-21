class SaleModel {
  final int id;
  final String invoiceId;
  final String itemDescription;
  final String customerName;
  final int quantity;
  final double costPrice;
  final double salePrice;
  final double profit;
  final String? date;

  SaleModel({
    required this.id,
    required this.invoiceId,
    required this.itemDescription,
    required this.customerName,
    required this.quantity,
    required this.costPrice,
    required this.salePrice,
    required this.profit,
    this.date,
  });

  double get totalAmount => salePrice * quantity;

  factory SaleModel.fromJson(Map<String, dynamic> json) {
    final cost = double.tryParse(json['cost_price']?.toString() ?? '0') ?? 0.0;
    final sale = double.tryParse(json['sale_price']?.toString() ?? '0') ?? 0.0;
    final qty = json['quantity'] ?? 1;
    final prof = double.tryParse(json['profit']?.toString() ?? '') ?? ((sale - cost) * qty);

    return SaleModel(
      id: json['id'] ?? 0,
      invoiceId: json['invoice_id'] ?? '',
      itemDescription: json['item_description'] ?? 'POS Item',
      customerName: json['customer_name'] ?? 'Walk-in Customer',
      quantity: qty,
      costPrice: cost,
      salePrice: sale,
      profit: prof,
      date: json['date'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'invoice_id': invoiceId,
      'item_description': itemDescription,
      'customer_name': customerName,
      'quantity': quantity,
      'cost_price': costPrice.toStringAsFixed(2),
      'sale_price': salePrice.toStringAsFixed(2),
    };
  }
}
