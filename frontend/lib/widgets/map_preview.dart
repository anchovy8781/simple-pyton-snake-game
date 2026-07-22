import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/generated_map.dart';

/// 생성된 맵의 타일 경로를 시각적으로 미리 보여주는 위젯.
///
/// 각 타일의 상대 회전각(turnAngleDeg)을 누적해 진행 방향을 구하고, 그
/// 방향으로 일정 길이의 선분을 이어 그린다. 다운비트/드롭 구간은 색을
/// 달리해 강조한다. 실제 ADOFAI 좌표계와 100% 동일하지는 않지만(6단계에서
/// 실제 파일 포맷으로 변환 시 정확한 규칙을 따른다), 패턴의 전체적인
/// 형태와 난이도 체감을 미리 확인하는 용도로는 충분하다.
class MapPreview extends StatelessWidget {
  final GeneratedMap map;

  const MapPreview({super.key, required this.map});

  @override
  Widget build(BuildContext context) {
    final side = 200.0 + map.tiles.length * 6.0;
    return InteractiveViewer(
      minScale: 0.1,
      maxScale: 8,
      constrained: false,
      child: CustomPaint(
        size: Size(side, side),
        painter: _MapPathPainter(map),
      ),
    );
  }
}

class _MapPathPainter extends CustomPainter {
  final GeneratedMap map;

  static const double _tileLength = 18.0;

  _MapPathPainter(this.map);

  @override
  void paint(Canvas canvas, Size size) {
    if (map.tiles.isEmpty) return;

    final normalPaint = Paint()
      ..color = Colors.blueGrey.shade300
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;
    final downbeatPaint = Paint()
      ..color = Colors.indigo
      ..strokeWidth = 4
      ..style = PaintingStyle.stroke;
    final dropPaint = Paint()
      ..color = Colors.deepOrange
      ..strokeWidth = 5
      ..style = PaintingStyle.stroke;

    var position = Offset(size.width / 2, size.height / 2);
    var headingDeg = 0.0;

    for (final tile in map.tiles) {
      headingDeg += tile.turnAngleDeg;
      final rad = headingDeg * math.pi / 180.0;
      final next = position + Offset(math.cos(rad), -math.sin(rad)) * _tileLength;

      final paint = tile.isDropEmphasis
          ? dropPaint
          : (tile.isDownbeat ? downbeatPaint : normalPaint);
      canvas.drawLine(position, next, paint);

      position = next;
    }
  }

  @override
  bool shouldRepaint(covariant _MapPathPainter oldDelegate) => !identical(oldDelegate.map, map);
}
