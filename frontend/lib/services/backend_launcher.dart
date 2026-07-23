/// 8단계: exe 패키징 시, GUI(.exe)와 같은 폴더에 백엔드(.exe)를 함께 배포하고
/// 앱 시작 시 자동으로 띄워서 사용자가 서버를 직접 실행하지 않아도 되게 한다.
///
/// 개발 중(`flutter run`)이거나 번들된 백엔드가 없는 환경에서는 아무 것도
/// 찾지 못하고 조용히 넘어간다 — 이 경우 사용자는 기존처럼 `uvicorn`을 직접
/// 실행하고 GUI의 "백엔드 서버 주소"에 입력하면 된다.
library;

import 'dart:async';
import 'dart:io';

import 'package:http/http.dart' as http;

const _backendHealthUrl = 'http://127.0.0.1:8000/health';

/// 번들된 백엔드 실행 파일을 찾아 백그라운드로 띄운다.
///
/// 데스크톱(Windows/Linux)이 아니거나, 이미 다른 백엔드가 떠 있거나,
/// 번들된 실행 파일을 찾지 못하면 아무 것도 하지 않는다. 이 함수는 절대
/// 예외를 던지지 않는다 — 실패하더라도 사용자가 수동으로 백엔드를 켜면 되므로
/// 앱 시작을 막을 이유가 없다.
Future<void> tryLaunchBundledBackend() async {
  try {
    if (!Platform.isWindows && !Platform.isLinux) return;
    if (await _isBackendAlreadyRunning()) return;

    final executable = _findBundledBackendExecutable();
    if (executable == null) return;

    await Process.start(
      executable.path,
      const [],
      mode: ProcessStartMode.detached,
      workingDirectory: executable.parent.path,
    );
  } catch (_) {
    // 자동 실행은 어디까지나 편의 기능이다. 실패해도 무시하고 수동 실행으로
    // 안내하는 기존 흐름(백엔드 서버 주소 입력)이 그대로 동작한다.
  }
}

Future<bool> _isBackendAlreadyRunning() async {
  try {
    final response = await http.get(Uri.parse(_backendHealthUrl)).timeout(
          const Duration(seconds: 1),
        );
    return response.statusCode == 200;
  } catch (_) {
    return false;
  }
}

/// GUI 실행 파일(`Platform.resolvedExecutable`)과 같은 폴더 아래
/// `adofai_backend/` 디렉터리에서 번들된 백엔드를 찾는다.
///
/// `.github/workflows/windows-package.yml`이 정확히 이 배치(같은 폴더에
/// `adofai_backend/adofai_backend.exe`)로 패키징하므로 이 경로 규칙과 워크플로우는
/// 함께 바뀌어야 한다.
File? _findBundledBackendExecutable() {
  final guiDir = File(Platform.resolvedExecutable).parent;
  final backendName = Platform.isWindows ? 'adofai_backend.exe' : 'adofai_backend';
  final candidate = File('${guiDir.path}${Platform.pathSeparator}adofai_backend'
      '${Platform.pathSeparator}$backendName');
  return candidate.existsSync() ? candidate : null;
}
