import 'package:flutter/material.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.how_to_reg,
              size: 100,
              color: Colors.indigo,
            ),
            SizedBox(height: 20),
            Text(
              "DRSS",
              style: TextStyle(
                fontSize: 36,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 10),
            Text(
              "Digital Registration and Selection System",
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
