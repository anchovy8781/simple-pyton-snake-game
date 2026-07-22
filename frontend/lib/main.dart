import 'package:flutter/material.dart';

import 'screens/home_screen.dart';

void main() {
  runApp(const AdofaiMapGeneratorApp());
}

class AdofaiMapGeneratorApp extends StatelessWidget {
  const AdofaiMapGeneratorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ADOFAI Map Generator',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
