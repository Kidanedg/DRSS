import 'package:flutter/material.dart';

class ParticipantsScreen extends StatelessWidget {
  const ParticipantsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Participants"),
        centerTitle: true,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: Add Participant
        },
        child: const Icon(Icons.person_add),
      ),
      body: const Center(
        child: Text(
          "No participants registered.",
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }
}
