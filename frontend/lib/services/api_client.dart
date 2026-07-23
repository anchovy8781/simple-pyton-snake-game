/// FastAPI 백엔드(backend/app) 호출 클라이언트.
library;

import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../models/generated_map.dart';

class ApiException implements Exception {
  final String message;

  ApiException(this.message);

  @override
  String toString() => message;
}

class EditSegmentResult {
  final GeneratedMap map;
  final EditInstruction parsedInstruction;

  const EditSegmentResult({required this.map, required this.parsedInstruction});
}

class ApiClient {
  final String baseUrl;
  final http.Client _client;

  ApiClient({required this.baseUrl, http.Client? client}) : _client = client ?? http.Client();

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  /// POST /mapgen/generate — 음악 파일을 업로드해 새 맵을 생성한다.
  Future<GeneratedMap> generateMap({
    required Uint8List audioBytes,
    required String fileName,
    required int difficulty,
    int? seed,
    MapStyle style = const MapStyle(),
  }) async {
    final request = http.MultipartRequest('POST', _uri('/mapgen/generate'))
      ..fields['difficulty'] = difficulty.toString()
      ..fields['magic_circle'] = style.magicCircle.toString()
      ..fields['enable_rush'] = style.enableRush.toString()
      ..fields['enable_slow'] = style.enableSlow.toString()
      ..fields['enable_sync_hits'] = style.enableSyncHits.toString()
      ..files.add(http.MultipartFile.fromBytes('file', audioBytes, filename: fileName));

    if (seed != null) {
      request.fields['seed'] = seed.toString();
    }

    final body = await _send(request);
    return GeneratedMap.fromJson(jsonDecode(body) as Map<String, dynamic>);
  }

  /// POST /ai/edit-segment — 자연어 지시로 기존 맵의 한 구간을 재생성한다.
  Future<EditSegmentResult> editSegment({
    required GeneratedMap existingMap,
    required String instruction,
    int? seed,
  }) async {
    final response = await _client.post(
      _uri('/ai/edit-segment'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({
        'existing_map': existingMap.toJson(),
        'instruction': instruction,
        'seed': ?seed,
      }),
    );

    _checkStatus(response.statusCode, response.body);

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return EditSegmentResult(
      map: GeneratedMap.fromJson(data['map'] as Map<String, dynamic>),
      parsedInstruction: EditInstruction.fromJson(data['parsed_instruction'] as Map<String, dynamic>),
    );
  }

  /// POST /storage/export — 맵을 실제 ADOFAI 커스텀 레벨(.adofai) 파일 내용으로 변환한다.
  Future<Uint8List> exportAdofai({
    required GeneratedMap existingMap,
    required String songFilename,
    String songName = '',
    String artist = '',
    String author = '',
    int offsetMs = 0,
    String outputFilename = 'level',
  }) async {
    final response = await _client.post(
      _uri('/storage/export'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({
        'existing_map': existingMap.toJson(),
        'song_filename': songFilename,
        'song_name': songName,
        'artist': artist,
        'author': author,
        'offset_ms': offsetMs,
        'output_filename': outputFilename,
      }),
    );

    _checkStatus(response.statusCode, response.body);
    return response.bodyBytes;
  }

  /// POST /storage/import — 기존 .adofai 파일을 업로드해 맵으로 되돌린다.
  Future<GeneratedMap> importAdofai({required Uint8List fileBytes, required String fileName}) async {
    final request = http.MultipartRequest('POST', _uri('/storage/import'))
      ..files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: fileName));

    final body = await _send(request);
    return GeneratedMap.fromJson(jsonDecode(body) as Map<String, dynamic>);
  }

  Future<String> _send(http.MultipartRequest request) async {
    final streamedResponse = await _client.send(request);
    final response = await http.Response.fromStream(streamedResponse);
    _checkStatus(response.statusCode, response.body);
    return response.body;
  }

  void _checkStatus(int statusCode, String body) {
    if (statusCode >= 200 && statusCode < 300) return;

    String detail = body;
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map && decoded['detail'] != null) {
        detail = decoded['detail'].toString();
      }
    } on FormatException {
      // 본문이 JSON이 아니면 원문을 그대로 사용한다.
    }
    throw ApiException('요청이 실패했습니다 ($statusCode): $detail');
  }

  void dispose() => _client.close();
}
