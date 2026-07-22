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
    required Difficulty difficulty,
    int? seed,
  }) async {
    final request = http.MultipartRequest('POST', _uri('/mapgen/generate'))
      ..fields['difficulty'] = difficulty.apiValue
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
        if (seed != null) 'seed': seed,
      }),
    );

    _checkStatus(response.statusCode, response.body);

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return EditSegmentResult(
      map: GeneratedMap.fromJson(data['map'] as Map<String, dynamic>),
      parsedInstruction: EditInstruction.fromJson(data['parsed_instruction'] as Map<String, dynamic>),
    );
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
