import 'package:flutter_test/flutter_test.dart';
import 'package:drss/main.dart';

void main() {
  testWidgets('DRSS app loads', (WidgetTester tester) async {
    await tester.pumpWidget(const DRSSApp());

    expect(find.text('DRSS'), findsWidgets);
  });
}
