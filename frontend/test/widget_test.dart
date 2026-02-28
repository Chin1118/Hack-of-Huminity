// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/auth/application/user_provider.dart';
import 'package:frontend/features/auth/data/session_storage.dart';

import 'package:frontend/main.dart';

void main() {
  testWidgets('App boots with dependency-injected session', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MyApp(
        sessionStorage: SessionStorage(),
        userProvider: UserProvider(
          storage: SessionStorage(),
          initialSession: null,
        ),
      ),
    );
    expect(find.byType(MyApp), findsOneWidget);
  });
}
