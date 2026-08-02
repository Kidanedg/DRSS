import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';
import '../dashboard/dashboard_screen.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Center(
        child: SizedBox(
          width: 400,
          child: Card(
            elevation: 6,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    "DRSS Login",
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 30),

                  const TextField(
                    decoration: InputDecoration(
                      labelText: "Email",
                    ),
                  ),

                  const SizedBox(height: 16),

                  const TextField(
                    obscureText: true,
                    decoration: InputDecoration(
                      labelText: "Password",
                    ),
                  ),

                  const SizedBox(height: 30),

                  ElevatedButton(
                    onPressed: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const DashboardScreen(),
                        ),
                      );
                    },
                    child: const Text("Login"),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
