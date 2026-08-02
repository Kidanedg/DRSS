import 'package:flutter/material.dart';

class DashboardScreen extends StatelessWidget {

  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      appBar: AppBar(
        title: const Text("DRSS Dashboard"),
      ),

      body: GridView.count(

        padding: const EdgeInsets.all(20),

        crossAxisCount: 2,

        crossAxisSpacing: 20,

        mainAxisSpacing: 20,

        children: const [

          _Card("Events", Icons.event),

          _Card("Participants", Icons.people),

          _Card("Lottery", Icons.casino),

          _Card("Winners", Icons.emoji_events),
        ],
      ),
    );
  }
}

class _Card extends StatelessWidget {

  final String title;
  final IconData icon;

  const _Card(this.title, this.icon);

  @override
  Widget build(BuildContext context) {

    return Card(

      elevation: 3,

      child: Column(

        mainAxisAlignment: MainAxisAlignment.center,

        children: [

          Icon(
            icon,
            size: 50,
          ),

          const SizedBox(height: 15),

          Text(
            title,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
