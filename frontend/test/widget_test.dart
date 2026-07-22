import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:adofai_map_generator/main.dart';
import 'package:adofai_map_generator/models/generated_map.dart';

void main() {
  testWidgets('홈 화면이 기본 컨트롤을 보여준다', (WidgetTester tester) async {
    await tester.pumpWidget(const AdofaiMapGeneratorApp());

    expect(find.text('ADOFAI Map Generator'), findsOneWidget);
    expect(find.text('음악 파일 선택 (mp3/ogg/wav)'), findsOneWidget);
    expect(find.text('생성'), findsOneWidget);
    expect(find.text('쉬움'), findsOneWidget);
    expect(find.text('보통'), findsOneWidget);
    expect(find.text('어려움'), findsOneWidget);
    expect(find.text('극악'), findsOneWidget);

    // 아직 맵을 생성하지 않았으므로 안내 문구가 보여야 한다.
    expect(find.text('음악 파일을 선택하고 "생성"을 눌러 맵 미리보기를 확인하세요.'), findsOneWidget);
  });

  testWidgets('난이도를 선택하면 선택 상태가 바뀐다', (WidgetTester tester) async {
    await tester.pumpWidget(const AdofaiMapGeneratorApp());

    await tester.tap(find.text('극악'));
    await tester.pumpAndSettle();

    final segmentedButton = tester.widget<SegmentedButton<Difficulty>>(
      find.byType(SegmentedButton<Difficulty>),
    );
    expect(segmentedButton.selected.single, Difficulty.extreme);
  });
}
