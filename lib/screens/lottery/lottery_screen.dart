import 'package:flutter/material.dart';

class LotteryScreen extends StatelessWidget {
  const LotteryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Lottery"),
        centerTitle: true,
      ),
      body: Center(
        child: Card(
          elevation: 6,
          margin: const EdgeInsets.all(30),
          child: Padding(
            padding: const EdgeInsets.all(30),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.casino,
                  size: 90,
                  color: Colors.indigo,
                ),
                const SizedBox(height: 20),
                const Text(
                  "Ready to Draw Winners",
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 30),
                ElevatedButton.icon(
                  onPressed: () {
                    // TODO: Random Selection
                  },
                  icon: const Icon(Icons.play_arrow),
                  label: const Text("Start Lottery"),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }
}
