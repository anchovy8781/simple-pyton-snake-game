# ADOFAI Map Generator

음악 파일(MP3/OGG/WAV)을 입력하면 자동으로 [A Dance of Fire and Ice](https://store.steampowered.com/app/977950/A_Dance_of_Fire_and_Ice/) (ADOFAI) 커스텀 맵을 생성하는 도구입니다.

## 목표

- 음악 분석: BPM, 비트, 다운비트, 드롭, 에너지 변화, 템포 변화를 자동 검출
- AI 기반 리듬 패턴 자동 생성
- 난이도 선택: 쉬움 / 보통 / 어려움 / 극악
- 사용자가 특정 구간을 지정해 AI에게 재생성을 요청 가능
  (예: "20~35초를 더 어렵게", "드롭 부분을 화려하게", "후반부를 쉽게", "반복을 줄여", "박자를 더 정확하게 맞춰")
- ADOFAI에서 바로 플레이 가능한 커스텀 레벨 형식(JSON)으로 저장
- Windows용 실행 파일(.exe) 배포

## 기술 스택

| 영역 | 기술 |
|---|---|
| 백엔드 | Python 3.12, FastAPI |
| 오디오 분석 | librosa, NumPy |
| 데스크톱 UI | Flutter |
| AI 패턴 생성/편집 | Google Gemini API (무료 티어) — 키 없으면 규칙 기반 파서로 대체 |
| 데이터 저장 | JSON |

> **참고**: 초기 기획 단계에서는 AI 연동에 Claude API를 검토했지만, 비용이 들지 않는 개발/테스트
> 환경을 원해 4단계부터는 **Google Gemini 무료 티어**로 대체했습니다. `GEMINI_API_KEY`가 없어도
> 규칙 기반 파서가 핵심 편집 기능을 대체 수행하므로 API 키 없이도 전체 기능을 테스트할 수 있습니다.

## 개발 로드맵

기존 코드를 임의로 삭제하지 않고, 각 단계가 끝날 때마다 실행 가능한 상태를 유지하며 순서대로 진행합니다.

- [x] 1단계 — 프로젝트 생성 (`backend/` FastAPI 스캐폴드, 테스트 환경)
- [x] 2단계 — 오디오 분석 (BPM/비트/다운비트/드롭/음량 변화/템포 변화 검출)
- [x] 3단계 — 맵 생성 엔진 (리듬 패턴 → ADOFAI 타일 시퀀스, 난이도 반영)
- [x] 4단계 — AI 연동 (Gemini 무료 티어 + 규칙 기반 폴백으로 자연어 구간 편집)
- [x] 5단계 — GUI 제작 (Flutter 데스크톱 앱)
- [ ] 6단계 — 파일 저장 (ADOFAI `.adofai` 커스텀 레벨 포맷 저장/불러오기)
- [ ] 7단계 — 테스트 (각 모듈 단위 테스트 + 통합 테스트)
- [ ] 8단계 — 배포용 실행 파일(.exe) 패키징 (백엔드: PyInstaller, GUI: Flutter Windows build)

## 현재 상태 (5단계까지 완료)

`backend/` 아래에 FastAPI 프로젝트 골격을 구성했습니다. 이후 단계(파일 저장)의 모듈 자리(`app/storage`)를 미리 잡아두었고, 헬스체크 엔드포인트와 테스트가 동작합니다.

`app/audio`에 librosa 기반 오디오 분석 파이프라인을 구현했습니다.

- BPM/비트 검출: `app/audio/beats.py` (`librosa.beat.beat_track`)
- 다운비트(마디 첫 박) 추정: `app/audio/downbeats.py` — 박자 위상별 onset envelope 합을 비교하는 휴리스틱
- 음량(에너지) 곡선: `app/audio/energy.py` — RMS(dB) 계산 + API 응답용 다운샘플링
- 템포 변화 감지: `app/audio/tempo_changes.py` — 구간별 로컬 템포를 추정해 변화 지점만 추출
- 드롭(빌드업 이후 에너지 급상승) 감지: `app/audio/drops.py` — 상승 후 일정 시간 유지되는 경우만 채택
- 전체 파이프라인: `app/audio/analyzer.py` (`analyze_audio`)
- API: `POST /audio/analyze` (mp3/ogg/wav 파일 업로드 → 분석 결과 JSON)

**주의(mp3 지원)**: mp3 디코딩은 `audioread`가 시스템에 설치된 **ffmpeg**(또는 gstreamer)를 통해 처리합니다. 이 개발 컨테이너에는 ffmpeg가 없어 mp3 디코딩을 직접 검증하지 못했고, wav로만 실동작을 확인했습니다. wav/ogg는 `soundfile`(libsndfile)로 바로 디코딩되어 문제없습니다. 로컬 실행 시 mp3를 쓰려면 ffmpeg를 PATH에 설치해야 하며, 8단계(exe 패키징)에서는 ffmpeg 바이너리를 함께 번들링해야 합니다.

`app/mapgen`에 오디오 분석 결과를 ADOFAI 타일 시퀀스로 바꾸는 맵 생성 엔진을 구현했습니다.

- 데이터 모델: `app/mapgen/models.py` — `Difficulty`(쉬움/보통/어려움/극악), `Tile`(직전 방향 대비 상대 회전각), `GeneratedMap`
- 난이도 프로파일: `app/mapgen/difficulty.py` — 난이도별 허용 회전각, 직진 확률, 세분(subdivision) 확률, 반복 허용 횟수, 드롭 강조 가중치
- 타임라인 구성: `app/mapgen/schedule.py` — 비트를 기본 그리드로 삼고 드롭 구간 근처는 세분 타일 확률을 높여 밀도를 올림
- 회전 패턴 생성: `app/mapgen/pattern.py` — 에너지가 높을수록 회전 선호, 드롭 구간엔 큰 각도 선호(화려함), 직전과 반대 방향으로 꺾는 경향(자연스러운 흐름), 동일 회전 연속 제한(반복 최소화)
- 엔진: `app/mapgen/engine.py` — `generate_map()`(전체 생성), `regenerate_segment()`(박자 타이밍은 유지한 채 지정 구간의 회전 패턴만 재생성 — 4단계 AI 편집이 호출할 기반)
- API: `POST /mapgen/generate` (음악 파일 + 난이도 → 맵 JSON), `POST /mapgen/regenerate-segment` (기존 맵 + 구간 → 해당 구간만 재생성된 맵)

시드(seed)를 지정하면 동일한 입력에 대해 항상 동일한 패턴이 생성됩니다(재현 가능성 확보, 테스트에도 활용).

`app/ai`에 자연어 편집 지시를 처리하는 AI 연동 계층을 구현했습니다.

- 데이터 모델: `app/ai/models.py` — `EditInstruction`(구간, 난이도 변화량, 화려함/반복/타이밍 플래그, 파싱 출처)
- Gemini 클라이언트: `app/ai/gemini_client.py` — `GEMINI_API_KEY` 설정 시 `google-generativeai`로 호출, 테스트를 위한 함수 주입(`generate_fn`) 지원
- 규칙 기반 폴백: `app/ai/rule_based_parser.py` — 정규식/키워드로 "20~35초를 더 어렵게", "드롭 부분을 화려하게", "후반부를 쉽게", "반복을 줄여", "박자를 더 정확하게 맞춰" 같은 대표 패턴을 처리 (API 키가 없어도 항상 동작)
- 통합 파서: `app/ai/instruction_parser.py` — Gemini가 설정돼 있으면 우선 시도하고, 키가 없거나 호출/응답 파싱이 실패하면 규칙 기반으로 자동 대체
- 편집 적용: `app/ai/edit_engine.py` — `EditInstruction`을 난이도 프로파일 조정(난이도 이동, 드롭 강조 가중치, 반복 허용 횟수, 세분 확률)으로 변환해 `mapgen.regenerate_segment()`에 적용
- API: `POST /ai/edit-segment` (기존 맵 + 자연어 지시 → 해당 구간만 반영된 새 맵 + 파싱 결과)

이 개발 컨테이너에는 `GEMINI_API_KEY`가 없어 실제 Gemini 호출은 검증하지 못했고, 규칙 기반 폴백 경로로 전체 기능을 테스트했습니다. Gemini 키를 `.env`에 넣으면 자동으로 AI 경로가 우선 사용됩니다.

`frontend/`에 Flutter 데스크톱(Linux/Windows) 앱을 구현했습니다. 백엔드 API를 그대로 호출하는 얇은 클라이언트로, 별도의 상태 서버 없이 동작합니다.

- 데이터 모델: `lib/models/generated_map.dart` — 백엔드 Pydantic 모델과 1:1 대응하는 `Tile`/`GeneratedMap`/`EditInstruction`
- API 클라이언트: `lib/services/api_client.dart` — `POST /mapgen/generate`(멀티파트 업로드), `POST /ai/edit-segment` 호출
- 화면: `lib/screens/home_screen.dart` — 음악 파일 선택(mp3/ogg/wav), 난이도 선택, 시드 입력, 생성 버튼, 진행 상태 표시, 저장 버튼, 자연어 구간 재생성 입력창을 한 화면에 배치
- 미리보기: `lib/widgets/map_preview.dart` — 각 타일의 상대 회전각을 누적해 진행 방향을 구하고 선분을 이어 그리는 `CustomPainter`. 다운비트/드롭 구간은 색을 달리해 강조하며, 확대/축소·이동이 가능하다(`InteractiveViewer`)
- 난이도 선택: `lib/widgets/difficulty_selector.dart` — 쉬움/보통/어려움/극악 세그먼트 버튼

**진행률 표시**: 백엔드가 작업 진행률(%)을 스트리밍하지 않으므로(동기 HTTP 응답), 현재는 부정확한(indeterminate) 진행 표시줄 + 상태 문구로 처리합니다. 정확한 퍼센트 진행률을 원하면 추후 SSE/WebSocket 기반 진행상황 API가 필요합니다.

**저장 버튼**: 현재는 맵 생성 엔진의 내부 표현(JSON)을 그대로 파일로 저장합니다. 실제 ADOFAI가 읽을 수 있는 `.adofai` 포맷 변환은 6단계에서 백엔드에 구현한 뒤 GUI에서 그 결과를 저장하도록 연결할 예정입니다.

이 컨테이너에는 GUI가 없어 실제 화면을 볼 수 없지만, Flutter SDK(3.44.7)를 설치하고 GTK3 개발 패키지를 추가해 **Linux 데스크톱 빌드를 실제로 컴파일·실행**해 검증했습니다: `flutter analyze`(경고 없음), `flutter test`(위젯 테스트 2개 통과), `flutter build linux --release` 성공, Xvfb 가상 디스플레이에서 앱을 직접 실행해 화면 렌더링과 입력 유효성 검사(파일 미선택 시 안내 스낵바)까지 스크린샷으로 확인했습니다. Windows용 `.exe`는 8단계에서 실제 Windows 환경(또는 CI의 windows 러너)으로 빌드해야 합니다 — Flutter는 Windows 데스크톱 앱을 크로스 컴파일할 수 없습니다.

### 실행 방법

**백엔드**

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

브라우저에서 http://127.0.0.1:8000/health 접속 시 `{"status": "ok"}` 응답을 확인할 수 있습니다.

**프론트엔드(Flutter 데스크톱)**

```bash
cd frontend
flutter pub get
flutter run -d linux    # 또는 -d windows (Windows 환경에서)
```

앱 실행 후 상단의 "백엔드 서버 주소"가 실행 중인 FastAPI 서버(기본 `http://127.0.0.1:8000`)를 가리키는지 확인하세요.

### 테스트

```bash
# 백엔드
cd backend
pip install -r requirements.txt
pytest

# 프론트엔드
cd frontend
flutter pub get
flutter analyze
flutter test
```

## 프로젝트 구조

```
backend/
  app/
    main.py            # FastAPI 앱 진입점
    core/config.py     # 환경설정 (Pydantic Settings)
    api/routes/         # API 라우터 (health, audio, mapgen, ai_edit)
    audio/               # 오디오 분석 모듈 (BPM/비트/다운비트/에너지/템포변화/드롭)
    mapgen/              # 맵 생성 엔진 (난이도별 회전 패턴, 구간 재생성)
    ai/                  # AI 연동 (Gemini 무료 티어 + 규칙 기반 폴백, 자연어 구간 편집)
    storage/             # (6단계) ADOFAI 레벨 파일 저장/불러오기
    models/              # 공용 데이터 모델 (Pydantic)
  tests/                # pytest 테스트
  requirements.txt
  pyproject.toml
  .env.example
frontend/               # Flutter 데스크톱 UI (Linux/Windows)
  lib/
    main.dart
    models/generated_map.dart   # 백엔드 모델과 대응하는 Dart 데이터 클래스
    services/api_client.dart     # FastAPI 백엔드 HTTP 클라이언트
    screens/home_screen.dart     # 메인 화면 (파일 선택~구간 재생성)
    widgets/                     # DifficultySelector, MapPreview(CustomPainter)
  test/                          # flutter_test 위젯 테스트
  linux/, windows/               # 데스크톱 플랫폼별 러너 (flutter create 스캐폴드)
```
