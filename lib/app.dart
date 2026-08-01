import 'package:flutter/material.dart';

class DRSSApp extends StatelessWidget {
  const DRSSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Digital Registration and Selection System',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.indigo,
      ),
      home: Scaffold(
        appBar: AppBar(
          title: const Text('DRSS'),
          centerTitle: true,
        ),
        body: const Center(
          child: Text(
            'Welcome to DRSS\nDigital Registration and Selection System',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }
}
