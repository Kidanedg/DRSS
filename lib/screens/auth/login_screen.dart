import 'package:flutter/material.dart';

import '../dashboard/dashboard_screen.dart';

class LoginScreen extends StatelessWidget {

  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      appBar: AppBar(
        title: const Text("Login"),
      ),

      body: Padding(

        padding: const EdgeInsets.all(24),

        child: Column(

          children: [

            const SizedBox(height: 40),

            TextField(
              decoration: InputDecoration(
                labelText: "Email",
                border: OutlineInputBorder(),
              ),
            ),

            const SizedBox(height: 20),

            TextField(
              obscureText: true,
              decoration: InputDecoration(
                labelText: "Password",
                border: OutlineInputBorder(),
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
    );
  }
}
