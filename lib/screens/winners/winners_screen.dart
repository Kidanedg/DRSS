import 'package:flutter/material.dart';

class WinnersScreen extends StatelessWidget {
  const WinnersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Winners"),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: const [
          Card(
            child: ListTile(
              leading: CircleAvatar(
                child: Icon(Icons.emoji_events),
              ),
              title: Text("Winner Name"),
              subtitle: Text("Selected by DRSS Lottery"),
            ),
          ),
        ],
      ),
    );
  }
}
