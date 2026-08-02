import 'package:flutter/material.dart';

import 'core/theme/app_theme.dart';
import 'screens/splash/splash_screen.dart';

class DRSSApp extends StatelessWidget {
  const DRSSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "DRSS",

      debugShowCheckedModeBanner: false,

      theme: AppTheme.lightTheme,

      home: const SplashScreen(),
    );
  }
}
