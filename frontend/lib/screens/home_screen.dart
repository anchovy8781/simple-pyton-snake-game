import 'dart:convert';
import 'dart:io' as io;

import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';

import '../models/generated_map.dart';
import '../services/api_client.dart';
import '../widgets/difficulty_selector.dart';
import '../widgets/map_preview.dart';

const _audioTypeGroup = XTypeGroup(
  label: '음악 파일',
  extensions: ['mp3', 'ogg', 'wav'],
);

const _jsonTypeGroup = XTypeGroup(
  label: 'JSON',
  extensions: ['json'],
);

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _backendUrlController =
      TextEditingController(text: 'http://127.0.0.1:8000');
  final TextEditingController _seedController = TextEditingController();
  final TextEditingController _instructionController = TextEditingController();

  XFile? _selectedAudioFile;
  Difficulty _selectedDifficulty = Difficulty.normal;

  bool _isGenerating = false;
  bool _isEditing = false;
  String? _statusMessage;

  GeneratedMap? _generatedMap;
  EditInstruction? _lastParsedInstruction;

  @override
  void dispose() {
    _backendUrlController.dispose();
    _seedController.dispose();
    _instructionController.dispose();
    super.dispose();
  }

  ApiClient _buildClient() => ApiClient(baseUrl: _backendUrlController.text.trim());

  int? _parseSeed() {
    final text = _seedController.text.trim();
    if (text.isEmpty) return null;
    return int.tryParse(text);
  }

  Future<void> _pickAudioFile() async {
    final file = await openFile(acceptedTypeGroups: const [_audioTypeGroup]);
    if (file == null) return;
    setState(() => _selectedAudioFile = file);
  }

  Future<void> _generateMap() async {
    final audioFile = _selectedAudioFile;
    if (audioFile == null) {
      _showMessage('먼저 음악 파일을 선택하세요.');
      return;
    }

    setState(() {
      _isGenerating = true;
      _statusMessage = '음악을 분석하고 맵을 생성하는 중입니다... (길이에 따라 수십 초 걸릴 수 있어요)';
    });

    final client = _buildClient();
    try {
      final bytes = await audioFile.readAsBytes();
      final map = await client.generateMap(
        audioBytes: bytes,
        fileName: audioFile.name,
        difficulty: _selectedDifficulty,
        seed: _parseSeed(),
      );
      setState(() {
        _generatedMap = map;
        _lastParsedInstruction = null;
        _statusMessage = '생성 완료: 타일 ${map.tiles.length}개';
      });
    } on ApiException catch (e) {
      _showMessage(e.message);
      setState(() => _statusMessage = null);
    } catch (e) {
      _showMessage('알 수 없는 오류: $e');
      setState(() => _statusMessage = null);
    } finally {
      client.dispose();
      if (mounted) setState(() => _isGenerating = false);
    }
  }

  Future<void> _editSegment() async {
    final map = _generatedMap;
    final instruction = _instructionController.text.trim();
    if (map == null) {
      _showMessage('먼저 맵을 생성하세요.');
      return;
    }
    if (instruction.isEmpty) {
      _showMessage('구간 재생성 지시를 입력하세요. 예: "20~35초를 더 어렵게"');
      return;
    }

    setState(() {
      _isEditing = true;
      _statusMessage = '지시를 해석하고 구간을 재생성하는 중입니다...';
    });

    final client = _buildClient();
    try {
      final result = await client.editSegment(
        existingMap: map,
        instruction: instruction,
        seed: _parseSeed(),
      );
      setState(() {
        _generatedMap = result.map;
        _lastParsedInstruction = result.parsedInstruction;
        _statusMessage = '구간 재생성 완료 '
            '(${result.parsedInstruction.startSec.toStringAsFixed(1)}~'
            '${result.parsedInstruction.endSec.toStringAsFixed(1)}초, '
            '${result.parsedInstruction.source == 'gemini' ? 'Gemini' : '규칙 기반'} 해석)';
      });
    } on ApiException catch (e) {
      _showMessage(e.message);
      setState(() => _statusMessage = null);
    } catch (e) {
      _showMessage('알 수 없는 오류: $e');
      setState(() => _statusMessage = null);
    } finally {
      client.dispose();
      if (mounted) setState(() => _isEditing = false);
    }
  }

  Future<void> _saveMap() async {
    final map = _generatedMap;
    if (map == null) {
      _showMessage('먼저 맵을 생성하세요.');
      return;
    }

    final location = await getSaveLocation(
      suggestedName: 'adofai_map.json',
      acceptedTypeGroups: const [_jsonTypeGroup],
    );
    if (location == null) return;

    // 실제 .adofai 파일 포맷 변환은 6단계(파일 저장)에서 구현한다.
    // 지금은 맵 생성/편집 엔진의 내부 표현(JSON)을 그대로 저장한다.
    final content = const JsonEncoder.withIndent('  ').convert(map.toJson());
    await io.File(location.path).writeAsString(content);
    _showMessage('저장했습니다: ${location.path}');
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final map = _generatedMap;
    final busy = _isGenerating || _isEditing;

    return Scaffold(
      appBar: AppBar(title: const Text('ADOFAI Map Generator')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _backendUrlController,
              decoration: const InputDecoration(
                labelText: '백엔드 서버 주소',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: busy ? null : _pickAudioFile,
              icon: const Icon(Icons.audiotrack),
              label: Text(_selectedAudioFile?.name ?? '음악 파일 선택 (mp3/ogg/wav)'),
            ),
            const SizedBox(height: 12),
            DifficultySelector(
              value: _selectedDifficulty,
              onChanged: (d) => setState(() => _selectedDifficulty = d),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _seedController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: '시드(선택, 같은 결과를 재현하고 싶을 때)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton.icon(
                  onPressed: busy ? null : _generateMap,
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text('생성'),
                ),
              ],
            ),
            if (busy) ...[
              const SizedBox(height: 12),
              const LinearProgressIndicator(),
              const SizedBox(height: 4),
              Text(_statusMessage ?? '처리 중입니다...', style: Theme.of(context).textTheme.bodySmall),
            ] else if (_statusMessage != null) ...[
              const SizedBox(height: 12),
              Text(_statusMessage!, style: Theme.of(context).textTheme.bodySmall),
            ],
            const SizedBox(height: 16),
            if (map != null)
              Expanded(child: _GeneratedMapPanel(
                map: map,
                busy: busy,
                instructionController: _instructionController,
                lastParsedInstruction: _lastParsedInstruction,
                onSave: _saveMap,
                onEditSegment: _editSegment,
              ))
            else
              const Expanded(
                child: Center(
                  child: Text('음악 파일을 선택하고 "생성"을 눌러 맵 미리보기를 확인하세요.'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _GeneratedMapPanel extends StatelessWidget {
  final GeneratedMap map;
  final bool busy;
  final TextEditingController instructionController;
  final EditInstruction? lastParsedInstruction;
  final VoidCallback onSave;
  final VoidCallback onEditSegment;

  const _GeneratedMapPanel({
    required this.map,
    required this.busy,
    required this.instructionController,
    required this.lastParsedInstruction,
    required this.onSave,
    required this.onEditSegment,
  });

  @override
  Widget build(BuildContext context) {
    final parsed = lastParsedInstruction;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _MapStats(map: map),
        const SizedBox(height: 8),
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: Theme.of(context).dividerColor),
              borderRadius: BorderRadius.circular(8),
            ),
            clipBehavior: Clip.antiAlias,
            child: MapPreview(map: map),
          ),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: busy ? null : onSave,
          icon: const Icon(Icons.save_alt),
          label: const Text('저장 (JSON)'),
        ),
        const SizedBox(height: 16),
        Text('구간 재생성 (자연어 지시)', style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 8),
        TextField(
          controller: instructionController,
          decoration: const InputDecoration(
            hintText: '예: 20~35초를 더 어렵게 / 드롭 부분을 화려하게 / 반복을 줄여',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        FilledButton.tonalIcon(
          onPressed: busy ? null : onEditSegment,
          icon: const Icon(Icons.auto_fix_high),
          label: const Text('구간 재생성'),
        ),
        if (parsed != null) ...[
          const SizedBox(height: 8),
          Text(
            '해석 결과: ${parsed.startSec.toStringAsFixed(1)}~${parsed.endSec.toStringAsFixed(1)}초, '
            '난이도 변화 ${parsed.difficultyDelta}, '
            '${[
              if (parsed.emphasizeFlashy) '화려하게',
              if (parsed.reduceRepetition) '반복 감소',
              if (parsed.tightenTiming) '타이밍 정밀화',
            ].join(', ')}'
            ' (${parsed.source == 'gemini' ? 'Gemini' : '규칙 기반'})',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ],
    );
  }
}

class _MapStats extends StatelessWidget {
  final GeneratedMap map;

  const _MapStats({required this.map});

  @override
  Widget build(BuildContext context) {
    final minutes = map.durationSec ~/ 60;
    final seconds = (map.durationSec % 60).round();
    return Wrap(
      spacing: 12,
      runSpacing: 4,
      children: [
        Chip(label: Text('BPM ${map.bpm.toStringAsFixed(1)}')),
        Chip(label: Text('난이도 ${map.difficulty.label}')),
        Chip(label: Text('길이 $minutes:${seconds.toString().padLeft(2, '0')}')),
        Chip(label: Text('타일 ${map.tiles.length}개')),
      ],
    );
  }
}
