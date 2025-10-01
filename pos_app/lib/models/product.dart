// lib/models/product.dart

class Product {
  final int id;
  final String name;
  final String? description;
  final double price;
  final int stockQuantity;

  Product({
    required this.id,
    required this.name,
    this.description,
    required this.price,
    required this.stockQuantity,
  });

  // Factory constructor to create a Product from a JSON object
  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      price: (json['price'] as num).toDouble(),
      stockQuantity: json['stock_quantity'],
    );
  }
}
