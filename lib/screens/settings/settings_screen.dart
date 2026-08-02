import 'package:flutter/material.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Settings"),
        centerTitle: true,
      ),
      body: ListView(
        children: const [
          ListTile(
            leading: Icon(Icons.person),
            title: Text("User Profile"),
          ),
          Divider(),
          ListTile(
            leading: Icon(Icons.lock),
            title: Text("Change Password"),
          ),
          Divider(),
          ListTile(
            leading: Icon(Icons.backup),
            title: Text("Backup Data"),
          ),
          Divider(),
          ListTile(
            leading: Icon(Icons.logout),
            title: Text("Logout"),
          ),
        ],
      ),
    );
  }
}
