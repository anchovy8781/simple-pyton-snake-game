import 'package:flutter/material.dart';

import '../models/generated_map.dart';

class DifficultySelector extends StatelessWidget {
  final Difficulty value;
  final ValueChanged<Difficulty> onChanged;

  const DifficultySelector({super.key, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<Difficulty>(
      segments: Difficulty.values
          .map((d) => ButtonSegment(value: d, label: Text(d.label)))
          .toList(growable: false),
      selected: {value},
      onSelectionChanged: (selected) => onChanged(selected.first),
    );
  }
}
