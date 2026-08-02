import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    colorSchemeSeed: Colors.blue,
    scaffoldBackgroundColor: Colors.grey.shade100,
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
    ),
  );
}
