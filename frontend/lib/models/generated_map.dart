/// 백엔드(app/mapgen, app/ai)의 Pydantic 모델과 1:1로 대응하는 Dart 데이터 클래스.
library;

enum Difficulty { easy, normal, hard, extreme }

extension DifficultyJson on Difficulty {
  String get apiValue => name;

  String get label => switch (this) {
        Difficulty.easy => '쉬움',
        Difficulty.normal => '보통',
        Difficulty.hard => '어려움',
        Difficulty.extreme => '극악',
      };

  static Difficulty fromApiValue(String value) {
    return Difficulty.values.firstWhere(
      (d) => d.apiValue == value,
      orElse: () => Difficulty.normal,
    );
  }
}

class Tile {
  final int index;
  final double timeSec;
  final double turnAngleDeg;
  final bool isDownbeat;
  final bool isDropEmphasis;
  final double energyDb;

  const Tile({
    required this.index,
    required this.timeSec,
    required this.turnAngleDeg,
    required this.isDownbeat,
    required this.isDropEmphasis,
    required this.energyDb,
  });

  factory Tile.fromJson(Map<String, dynamic> json) {
    return Tile(
      index: json['index'] as int,
      timeSec: (json['time_sec'] as num).toDouble(),
      turnAngleDeg: (json['turn_angle_deg'] as num).toDouble(),
      isDownbeat: json['is_downbeat'] as bool? ?? false,
      isDropEmphasis: json['is_drop_emphasis'] as bool? ?? false,
      energyDb: (json['energy_db'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
        'index': index,
        'time_sec': timeSec,
        'turn_angle_deg': turnAngleDeg,
        'is_downbeat': isDownbeat,
        'is_drop_emphasis': isDropEmphasis,
        'energy_db': energyDb,
      };
}

class GeneratedMap {
  final double bpm;
  final Difficulty difficulty;
  final double durationSec;
  final List<Tile> tiles;

  const GeneratedMap({
    required this.bpm,
    required this.difficulty,
    required this.durationSec,
    required this.tiles,
  });

  factory GeneratedMap.fromJson(Map<String, dynamic> json) {
    return GeneratedMap(
      bpm: (json['bpm'] as num).toDouble(),
      difficulty: DifficultyJson.fromApiValue(json['difficulty'] as String),
      durationSec: (json['duration_sec'] as num).toDouble(),
      tiles: (json['tiles'] as List<dynamic>)
          .map((t) => Tile.fromJson(t as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'bpm': bpm,
        'difficulty': difficulty.apiValue,
        'duration_sec': durationSec,
        'tiles': tiles.map((t) => t.toJson()).toList(),
      };
}

/// 자연어 편집 지시가 구조화된 결과 (app/ai/models.py의 EditInstruction과 대응).
class EditInstruction {
  final double startSec;
  final double endSec;
  final int difficultyDelta;
  final bool emphasizeFlashy;
  final bool reduceRepetition;
  final bool tightenTiming;
  final String rawInstruction;
  final String source;

  const EditInstruction({
    required this.startSec,
    required this.endSec,
    required this.difficultyDelta,
    required this.emphasizeFlashy,
    required this.reduceRepetition,
    required this.tightenTiming,
    required this.rawInstruction,
    required this.source,
  });

  factory EditInstruction.fromJson(Map<String, dynamic> json) {
    return EditInstruction(
      startSec: (json['start_sec'] as num).toDouble(),
      endSec: (json['end_sec'] as num).toDouble(),
      difficultyDelta: json['difficulty_delta'] as int? ?? 0,
      emphasizeFlashy: json['emphasize_flashy'] as bool? ?? false,
      reduceRepetition: json['reduce_repetition'] as bool? ?? false,
      tightenTiming: json['tighten_timing'] as bool? ?? false,
      rawInstruction: json['raw_instruction'] as String? ?? '',
      source: json['source'] as String? ?? 'rule_based',
    );
  }
}
