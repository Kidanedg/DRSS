import 'package:flutter/material.dart';

import 'config/app_routes.dart';
import 'config/app_theme.dart';

class DRSSApp extends StatelessWidget {
  const DRSSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Digital Registration and Selection System',

      debugShowCheckedModeBanner: false,

      theme: AppTheme.lightTheme,

      initialRoute: AppRoutes.splash,

      routes: AppRoutes.routes,
    );
  }
}
