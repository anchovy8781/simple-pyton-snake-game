import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:adofai_map_generator/main.dart';

void main() {
  testWidgets('홈 화면이 기본 컨트롤을 보여준다', (WidgetTester tester) async {
    await tester.pumpWidget(const AdofaiMapGeneratorApp());

    expect(find.text('ADOFAI Map Generator'), findsOneWidget);
    expect(find.text('음악 파일 선택 (mp3/ogg/wav)'), findsOneWidget);
    expect(find.text('생성'), findsOneWidget);
    expect(find.text('난이도'), findsOneWidget);
    expect(find.text('Lv.13'), findsOneWidget);
    expect(find.text('마법진(나선형)'), findsOneWidget);
    expect(find.text('질주맵'), findsOneWidget);
    expect(find.text('슬로우 구간'), findsOneWidget);

    // 아직 맵을 생성하지 않았으므로 안내 문구가 보여야 한다.
    expect(find.text('음악 파일을 선택하고 "생성"을 눌러 맵 미리보기를 확인하세요.'), findsOneWidget);
  });

  testWidgets('난이도 슬라이더를 움직이면 값이 바뀐다', (WidgetTester tester) async {
    await tester.pumpWidget(const AdofaiMapGeneratorApp());

    final slider = find.byType(Slider);
    expect(slider, findsOneWidget);

    await tester.drag(slider, const Offset(500, 0));
    await tester.pumpAndSettle();

    expect(find.text('Lv.13'), findsNothing);
  });

  testWidgets('스타일 옵션 칩을 누르면 선택된다', (WidgetTester tester) async {
    await tester.pumpWidget(const AdofaiMapGeneratorApp());

    final chip = find.widgetWithText(FilterChip, '질주맵');
    expect(chip, findsOneWidget);

    await tester.tap(chip);
    await tester.pumpAndSettle();

    final filterChip = tester.widget<FilterChip>(chip);
    expect(filterChip.selected, isTrue);
  });
}
