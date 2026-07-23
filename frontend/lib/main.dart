import 'dart:async';

import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'services/backend_launcher.dart';

void main() {
  // exe로 패키징된 경우 같은 폴더의 백엔드를 자동으로 띄운다. 개발 모드나
  // 번들이 없는 환경에서는 조용히 아무 일도 하지 않는다(backend_launcher 참고).
  unawaited(tryLaunchBundledBackend());
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
