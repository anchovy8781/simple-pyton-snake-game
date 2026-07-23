import 'package:flutter/material.dart';

import '../models/generated_map.dart';

class DifficultySelector extends StatelessWidget {
  final int value;
  final ValueChanged<int> onChanged;

  const DifficultySelector({super.key, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text('난이도', style: Theme.of(context).textTheme.bodyMedium),
        Expanded(
          child: Slider(
            value: value.toDouble(),
            min: minDifficulty.toDouble(),
            max: maxDifficulty.toDouble(),
            divisions: maxDifficulty - minDifficulty,
            label: 'Lv.$value',
            onChanged: (v) => onChanged(clampDifficulty(v.round())),
          ),
        ),
        SizedBox(
          width: 56,
          child: Text('Lv.$value', textAlign: TextAlign.end, style: Theme.of(context).textTheme.titleSmall),
        ),
      ],
    );
  }
}
