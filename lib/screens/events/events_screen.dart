import 'package:flutter/material.dart';

class EventsScreen extends StatelessWidget {
  const EventsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Events'),
        centerTitle: true,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: Open Create Event Screen
        },
        child: const Icon(Icons.add),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Card(
              elevation: 4,
              child: ListTile(
                leading: const Icon(
                  Icons.event,
                  color: Colors.indigo,
                  size: 40,
                ),
                title: const Text(
                  'Sample Registration Event',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: const Text(
                  'Registration Deadline: 31 August 2026',
                ),
                trailing: PopupMenuButton<String>(
                  onSelected: (value) {
                    // TODO: Handle menu actions
                  },
                  itemBuilder: (context) => const [
                    PopupMenuItem(
                      value: 'view',
                      child: Text('View'),
                    ),
                    PopupMenuItem(
                      value: 'edit',
                      child: Text('Edit'),
                    ),
                    PopupMenuItem(
                      value: 'delete',
                      child: Text('Delete'),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            Expanded(
              child: Center(
                child: Text(
                  'No additional events available.',
                  style: TextStyle(
                    color: Colors.grey.shade600,
                    fontSize: 18,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
