import 'package:flutter/material.dart';

import '../events/events_screen.dart';
import '../participants/participants_screen.dart';
import '../lottery/lottery_screen.dart';
import '../winners/winners_screen.dart';
import '../settings/settings_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  Widget buildCard(
    BuildContext context,
    IconData icon,
    String title,
    Widget screen,
  ) {
    return Card(
      elevation: 5,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => screen,
            ),
          );
        },
        child: SizedBox(
          width: 170,
          height: 150,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 50,
                color: Colors.indigo,
              ),
              const SizedBox(height: 15),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("DRSS Dashboard"),
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Wrap(
            alignment: WrapAlignment.center,
            spacing: 20,
            runSpacing: 20,
            children: [
              buildCard(
                context,
                Icons.event,
                "Events",
                const EventsScreen(),
              ),
              buildCard(
                context,
                Icons.people,
                "Participants",
                const ParticipantsScreen(),
              ),
              buildCard(
                context,
                Icons.casino,
                "Lottery",
                const LotteryScreen(),
              ),
              buildCard(
                context,
                Icons.emoji_events,
                "Winners",
                const WinnersScreen(),
              ),
              buildCard(
                context,
                Icons.settings,
                "Settings",
                const SettingsScreen(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
