// lib/services/api_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product.dart';

class ApiService {
  // IMPORTANT: Use 10.0.2.2 for the Android emulator to connect to localhost
  // on your host machine. For iOS simulator, you can use localhost or 127.0.0.1.
  // For a physical device, use your computer's network IP address.
  static const String _baseUrl = "http://10.0.2.2:8000";

  Future<List<Product>> fetchProducts() async {
    final response = await http.get(Uri.parse('$_baseUrl/products/'));

    if (response.statusCode == 200) {
      // If the server returns a 200 OK response, parse the JSON.
      List<dynamic> body = jsonDecode(response.body);
      List<Product> products = body.map((dynamic item) => Product.fromJson(item)).toList();
      return products;
    } else {
      // If the server did not return a 200 OK response,
      // then throw an exception.
      throw Exception('Failed to load products');
    }
  }
}
