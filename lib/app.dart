import 'package:flutter/material.dart';
import 'screens/splash/splash_screen.dart';

class DRSSApp extends StatelessWidget {
  const DRSSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DRSS',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.indigo,
      ),
      home: const SplashScreen(),
    );
  }
}
