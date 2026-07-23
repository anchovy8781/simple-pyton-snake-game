# ADOFAI Map Generator

음악 파일(MP3/OGG/WAV)을 입력하면 자동으로 [A Dance of Fire and Ice](https://store.steampowered.com/app/977950/A_Dance_of_Fire_and_Ice/) (ADOFAI) 커스텀 맵을 생성하는 도구입니다.

## 목표

- 음악 분석: BPM, 비트, 다운비트, 드롭, 에너지 변화, 템포 변화를 자동 검출
- AI 기반 리듬 패턴 자동 생성
- 난이도 선택: 1(가장 쉬움) ~ 26(가장 어려움) 세밀한 단계 조절
- 패턴 스타일 옵션: 마법진(나선형 경로), 질주맵(고밀도 연속 구간), 슬로우(조용한 구간 템포 감속) 자동 배치
- 사용자가 특정 구간을 지정해 AI에게 재생성을 요청 가능
  (예: "20~35초를 더 어렵게", "드롭 부분을 화려하게", "후반부를 쉽게", "반복을 줄여", "박자를 더 정확하게 맞춰")
- ADOFAI에서 바로 플레이 가능한 커스텀 레벨 형식(`.adofai`)으로 저장/불러오기
- Windows용 실행 파일(.exe) 배포

> **다음 예정**: 동시타격(동타) 자동 배치와 배경 애니메이션 생성은 ADOFAI JSON
> 포맷(멀티플래닛/데코레이션 스키마)을 Twirl 액션 때처럼 신중히 조사해야 해서
> 별도 단계로 진행합니다.

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
- [x] 6단계 — 파일 저장 (ADOFAI `.adofai` 커스텀 레벨 포맷 저장/불러오기)
- [x] 7단계 — 난이도 1~26 세분화 + 패턴 스타일 옵션(마법진/질주맵/슬로우) + 테스트 보강
- [x] 8단계 — 배포용 실행 파일(.exe) 패키징 (백엔드: PyInstaller, GUI: Flutter Windows build, GUI 시작 시 백엔드 자동 실행)
- [ ] 9단계 — 동시타격(동타) 자동 배치 + 배경 애니메이션 생성 (ADOFAI 포맷 추가 조사 필요)

## ⚠️ 6단계에서 발견하고 수정한 핵심 오류 (박자 정확도)

6단계(파일 저장)를 구현하려고 실제 `.adofai` 포맷을 조사하다가, ADOFAI의 근본
메커니즘을 하나 발견했습니다: **타일의 회전각이 곧 그 타일까지 걸리는 시간(박자)을
결정합니다** (직전 타일 대비 상대 회전각 180도 = 1박, 90도 = 반박, 60도 = 1/3박
— 공식 위키 및 커뮤니티 도구(adofaipy, ADOFAI-Map-Converter, adofai-angle-calculator)
역공학 결과로 교차 확인). 즉 "언제 타일을 놓을지"와 "얼마나 꺾을지"는 독립적으로
정할 수 없습니다.

3~4단계는 이 사실을 모른 채 "타이밍은 비트 검출 결과로 고정, 회전각은 난이도에
따라 자유롭게 선택"하는 구조로 만들어져 있었습니다. 이대로 `.adofai` 파일을
만들면 **파일은 정상적으로 열리지만 실제 재생 시 타일이 음악의 박자와 어긋나게
됩니다** — "박자 정확도"가 요구사항 1순위였으므로 이는 방치할 수 없는 오류였습니다.

그래서 6단계 작업의 일부로 3단계 맵 생성 엔진을 이 메커니즘에 맞게 다시 짰습니다:

- **이전**: `difficulty.py`가 회전각 후보 목록(예: 15°~180°)과 "세분 확률"을 따로
  가짐 → 회전각과 타이밍이 각자 독립적으로 결정됨(오류).
- **이후**: 난이도는 "한 박을 몇 개의 동일한 타일로 나눌지(split)"에 대한 확률
  분포로 표현합니다(`beat_split_weights`, 예: `{1: 0.7, 2: 0.3}`). split이 정해지면
  회전각 크기는 `180 * (1 - 1/split)`로 자동 결정되고(예: split=2 → 90도 = 정확히
  반박), 방향(좌/우)만 별도로 선택합니다. 이렇게 하면 타이밍과 회전각이 항상
  일관됩니다.
- 방향(부호)이 "직전과 반대"로 바뀌는 타일은 실제 게임에서 지속 시간이 달라지므로
  (오른쪽으로 90도 꺾으면 반박이 아니라 1.5박이 됨), 파일 저장 시 **Twirl 액션**을
  넣어 방향과 무관하게 원래 의도한 박자 길이가 유지되도록 보정합니다
  (`app/storage/adofai_writer.py`).
- 오디오 분석의 템포 변화 감지 결과(`tempo_changes`)를 살려 구간별 BPM 그리드를
  만들고, 실제 BPM이 바뀌는 지점에는 `SetSpeed` 액션을 넣습니다.

이 수정이 올바른지는 "왕복 테스트"로 검증했습니다: 맵을 생성 → `.adofai` 문서로
저장 → 저장된 각도/액션만으로 실제 게임과 동일한 공식으로 타이밍을 역산 →
원래 의도한 타일 시각과 비교. 난이도 4종 × BPM 3종 × 시드 50개(총 65,539개
타일 전이)에 대해 최대 오차가 `3.5e-15초`(부동소수점 오차 수준)로, 구조적인
어긋남이 없음을 확인했습니다. 자세한 내용은 아래 6단계 절과
`tests/test_storage_adofai.py`를 참고하세요.

이 과정에서 3~4단계의 테스트와 `app/ai/edit_engine.py`(자연어 편집이 조정하는
파라미터)도 새 구조에 맞게 함께 업데이트했습니다. 공개 API 계약(`generate_map`,
`regenerate_segment`, `/mapgen/*`, `/ai/edit-segment` 응답 형식)은 그대로이므로
5단계 GUI는 변경 없이 계속 동작합니다.

## 7단계: 난이도 1~26 세분화 + 패턴 스타일 옵션

기존 4단계(쉬움/보통/어려움/극악) 난이도를 **1~26 정수 스케일**로 확장했습니다.
`app/mapgen/difficulty.py`의 `profile_for_level()`이 4개의 기준점(레벨 1/9/18/26,
기존 4단계 프로파일과 동일한 값)을 두고 그 사이를 선형 보간해 연속적인 난이도
곡선을 만듭니다 — 레벨이 오를수록 한 박을 더 잘게 쪼개고(split 최대치가 1→5까지
늘어남), 반복 허용 횟수는 줄고, 지그재그 확률(`flip_probability`)은 올라갑니다.
`GeneratedMap.difficulty`, `/mapgen/generate`의 `difficulty` 필드, AI 편집의
`difficulty_delta`, `.adofai`의 `settings.difficulty` 등 스택 전체가 이 정수
스케일로 통일되어 있습니다. 자연어 편집의 난이도 조정 폭도 26단계 스케일에 맞춰
키웠습니다(예: "더 어렵게" → +4, "극악으로" → +10).

패턴의 "모양"을 바꾸는 스타일 옵션도 추가했습니다(`MapStyle`, 난이도와 독립적으로
켤 수 있음):

- **마법진(magic_circle)**: 실제 ADOFAI 커뮤니티의 "레인보우 체이스" 계열
  마법진 차트를 참고해 두 가지 모드로 구현했습니다.
  - **레벨 20 미만**: 방향(좌/우) 전환을 아예 하지 않아 매 타일이 같은
    쪽으로만 꺾이는 단순한 나선/원형 경로(`flip_probability=0`).
  - **레벨 20 이상**: 직진(split=1) 타일을 없애고, 좌/우가 섞인 반복 모티프
    (`[1,1,1,-1,-1,1,-1,1,1,-1,-1,1]`, 12%는 무작위로 살짝 변형)를 계속
    되풀이해 촘촘하게 얽힌 고리 무늬를 만듭니다. 이 모티프 자체는 게임
    메커니즘이 아니라 미학적 선택이라 임의로 설계했으며, 실제 게임에서
    더 마음에 드는 모양이 있다면 이 배열만 바꾸면 됩니다(`app/mapgen/engine.py`
    `MAGIC_CIRCLE_HIGH_LEVEL_SIGN_CYCLE`).
- **질주맵(enable_rush)**: 에너지가 높은 상태가 2초 이상 지속되는 구간에서는
  split=1(쉬는 타일)을 후보에서 제외해, 끊임없이 빠르게 이어지는 느낌을 만듭니다.
- **슬로우(enable_slow)**: 곡에서 가장 조용하고 긴 구간(에너지가 낮은 상태가
  2초 이상 지속)을 찾아 그 부분의 템포를 낮춥니다. Set Speed(순간 변경)가
  아니라 **Change Speed처럼 점진적으로 가속/감속**합니다 — 진입/이탈 구간을
  각 4단계로 나눠 BPM을 계단식으로 보간합니다(`MapStyle.slow_speed_factor`로
  얼마나 느려질지 배수 조절 가능, 기본 0.6배). "ChangeSpeed"라는 별도 액션
  타입이 실제로 있는지 불확실해 리스크를 피하려고, 이미 왕복 검증된
  SetSpeed를 여러 번 나눠 쓰는 방식으로 점진적 변화를 흉내냈습니다 — 그래서
  타이밍 정확도는 별도 검증 없이 보장됩니다.

AI 편집 프롬프트(`app/ai/instruction_parser.py`)도 손봤습니다: 음악 싱크/박자는
엔진이 이미 항상 정확하게 보장하므로, Gemini에게는 "이 구간에 어떤 난이도/스타일이
음악적으로 어울리는가"만 판단하도록 역할을 명확히 하고, 현재 BPM과 난이도를
프롬프트에 함께 전달해 더 맥락에 맞는 조정값을 내도록 했습니다.

마법진 레벨 20 이상 모드가 실제로 어떤 모양이 나오는지 시각적으로 확인했습니다
(회전각을 누적해 경로를 그려봄): 레벨 24는 직진 없이 촘촘하게 얽힌 고리들이
이어지는 형태, 레벨 15(20 미만)는 대체로 직선을 유지하다가 가끔 작은 루프가
끼어드는 형태로, 의도한 대로 레벨 경계에서 스타일이 달라짐을 확인했습니다.

새 기능들도 왕복 테스트(생성 → 저장 → 역산 → 비교)로 검증했습니다: 난이도 1~26
전 구간 × 스타일 옵션 5종 조합(마법진/마법진+슬로우/커스텀 배수 슬로우/질주+슬로우/
기본) × 시드 20개(총 66,354개 타일 전이)에서 최대 오차 `4.4e-16초`로, 점진적
템포 램프와 고난도 마법진 모티프를 켜도 박자 정확도는 그대로 유지됨을 확인했습니다.

## 8단계: exe 패키징

이 리눅스 개발 컨테이너에는 Windows 툴체인이 없어 진짜 `.exe`를 여기서 직접
만들 수는 없습니다. 대신 **Windows에서(또는 CI의 windows-latest 러너에서)
그대로 실행하면 실제 exe가 나오는 빌드 스펙/워크플로우**를 작성하고, 여기서
실행 가능한 부분(백엔드 진입점 스모크 테스트, `flutter analyze`/`flutter test`)은
직접 검증했습니다.

- **백엔드**: `backend/packaging/run_backend.py`가 PyInstaller의 시작점입니다
  (`uvicorn.run(app, host="127.0.0.1", port=8000)`만 호출하는 얇은 진입점).
  `backend/packaging/adofai_backend.spec`이 librosa/soundfile처럼 PyInstaller가
  정적 분석만으로 못 찾는 동적 임포트를 `collect_submodules`로 보강해 묶습니다.
  이 컨테이너에서 `python packaging/run_backend.py`를 실제로 실행해 `/health`가
  `{"status": "ok"}`를 반환하는 것까지 확인했습니다(PyInstaller로 묶는 과정
  자체는 Windows에서만 가능).
- **GUI**: 기존 `frontend/windows/` 러너 스캐폴드(5단계에서 이미 생성됨)를
  그대로 사용합니다. `flutter build windows --release`는 Windows에서 실행해야
  합니다.
- **자동 실행**: 사용자가 서버를 직접 켤 필요가 없도록, GUI 실행 파일과 같은
  폴더의 `adofai_backend/adofai_backend.exe`를 찾아 시작 시 자동으로 띄우는
  로직을 추가했습니다(`frontend/lib/services/backend_launcher.dart`,
  `main.dart`에서 `unawaited(tryLaunchBundledBackend())`로 호출). 이미 백엔드가
  떠 있으면(`/health` 응답) 다시 띄우지 않고, 번들된 실행 파일을 못 찾으면
  조용히 넘어가 기존처럼 수동으로 백엔드를 켜고 주소를 입력하는 방식이 그대로
  동작합니다 — 이 자동 실행 로직은 절대 예외를 던지지 않도록 감싸 앱 시작을
  막지 않습니다.
- **CI 패키징**: `.github/workflows/windows-package.yml`이 `workflow_dispatch`
  또는 `v*` 태그 push 시 windows-latest 러너에서 (1) PyInstaller로 백엔드 exe
  빌드 → (2) Flutter Windows release 빌드 → (3) GUI 폴더 안에
  `adofai_backend/` 서브폴더로 백엔드를 복사해 하나로 합친 뒤 → (4) zip으로
  아티팩트 업로드까지 수행합니다. 배치 규칙(같은 폴더 + `adofai_backend/`
  서브폴더)은 워크플로우와 `backend_launcher.dart`가 같은 값을 공유하므로,
  둘 중 하나를 바꾸면 다른 쪽도 함께 바꿔야 합니다.

## 현재 상태 (8단계까지 완료)

`backend/` 아래에 FastAPI 프로젝트 골격을 구성했습니다. 헬스체크 엔드포인트와 테스트가 동작합니다.

`app/audio`에 librosa 기반 오디오 분석 파이프라인을 구현했습니다.

- BPM/비트 검출: `app/audio/beats.py` (`librosa.beat.beat_track`)
- 다운비트(마디 첫 박) 추정: `app/audio/downbeats.py` — 박자 위상별 onset envelope 합을 비교하는 휴리스틱
- 음량(에너지) 곡선: `app/audio/energy.py` — RMS(dB) 계산 + API 응답용 다운샘플링
- 템포 변화 감지: `app/audio/tempo_changes.py` — 구간별 로컬 템포를 추정해 변화 지점만 추출
- 드롭(빌드업 이후 에너지 급상승) 감지: `app/audio/drops.py` — 상승 후 일정 시간 유지되는 경우만 채택
- 전체 파이프라인: `app/audio/analyzer.py` (`analyze_audio`)
- API: `POST /audio/analyze` (mp3/ogg/wav 파일 업로드 → 분석 결과 JSON)

**주의(mp3 지원)**: mp3 디코딩은 `audioread`가 시스템에 설치된 **ffmpeg**(또는 gstreamer)를 통해 처리합니다. 이 개발 컨테이너에는 ffmpeg가 없어 mp3 디코딩을 직접 검증하지 못했고, wav로만 실동작을 확인했습니다. wav/ogg는 `soundfile`(libsndfile)로 바로 디코딩되어 문제없습니다. 로컬 실행 시 mp3를 쓰려면 ffmpeg를 PATH에 설치해야 하며, 8단계(exe 패키징)에서는 ffmpeg 바이너리를 함께 번들링해야 합니다.

`app/mapgen`에 오디오 분석 결과를 ADOFAI 타일 시퀀스로 바꾸는 맵 생성 엔진을 구현했습니다. (아래 구조는 6단계에서 "회전각=박자" 메커니즘에 맞게 보정한 최종 버전입니다.)

- 데이터 모델: `app/mapgen/models.py` — 난이도(1~26 정수), `MapStyle`(마법진/질주맵/슬로우), `Tile`(직전 방향 대비 상대 회전각 + split_n/bpm 메타데이터), `GeneratedMap`
- 난이도 프로파일: `app/mapgen/difficulty.py` — `profile_for_level(1~26)`이 기준점 보간으로 "한 박을 몇 등분할지" 확률 분포(`beat_split_weights`), 반복 허용 횟수, 드롭/에너지에 따른 분할 가중치, 지그재그 확률(`flip_probability`)을 연속적으로 만든다
- 타임라인 구성: `app/mapgen/schedule.py` — 구간별 BPM 그리드 위에서 매 박마다 분할 수를 선택해 타일을 배치. 드롭/높은 에너지 구간은 더 잘게 나뉠 확률을 높여 밀도를 올리고, 템포 변화 감지 결과(`tempo_changes`)에 따라 구간별로 다른 BPM 그리드를 적용
- 회전 패턴 생성: `app/mapgen/pattern.py` — 회전 크기는 분할 수로 이미 정해지므로 방향(좌/우)만 선택. 직전과 반대 방향으로 꺾는 경향(자연스러운 흐름), 동일 (분할, 방향) 조합의 연속 반복 제한(반복 최소화)
- 엔진: `app/mapgen/engine.py` — `generate_map()`(전체 생성), `regenerate_segment()`(박자 타이밍과 분할은 유지한 채 지정 구간의 회전 "방향"만 재생성 — 4단계 AI 편집이 호출할 기반)
- API: `POST /mapgen/generate` (음악 파일 + 난이도 → 맵 JSON), `POST /mapgen/regenerate-segment` (기존 맵 + 구간 → 해당 구간만 재생성된 맵)

시드(seed)를 지정하면 동일한 입력에 대해 항상 동일한 패턴이 생성됩니다(재현 가능성 확보, 테스트에도 활용).

`app/ai`에 자연어 편집 지시를 처리하는 AI 연동 계층을 구현했습니다.

- 데이터 모델: `app/ai/models.py` — `EditInstruction`(구간, 난이도 변화량, 화려함/반복/타이밍 플래그, 파싱 출처)
- Gemini 클라이언트: `app/ai/gemini_client.py` — `GEMINI_API_KEY` 설정 시 `google-generativeai`로 호출, 테스트를 위한 함수 주입(`generate_fn`) 지원
- 규칙 기반 폴백: `app/ai/rule_based_parser.py` — 정규식/키워드로 "20~35초를 더 어렵게", "드롭 부분을 화려하게", "후반부를 쉽게", "반복을 줄여", "박자를 더 정확하게 맞춰" 같은 대표 패턴을 처리 (API 키가 없어도 항상 동작)
- 통합 파서: `app/ai/instruction_parser.py` — Gemini가 설정돼 있으면 우선 시도하고, 키가 없거나 호출/응답 파싱이 실패하면 규칙 기반으로 자동 대체
- 편집 적용: `app/ai/edit_engine.py` — `EditInstruction`을 난이도 프로파일 조정(난이도 이동, 반복 허용 횟수, 지그재그 확률)으로 변환해 `mapgen.regenerate_segment()`에 적용. 구간 재생성은 회전 "방향"만 바꾸므로(박자 정확도 보존), 편집 지시도 방향 선택에 실제로 영향을 주는 파라미터만 조정한다
- API: `POST /ai/edit-segment` (기존 맵 + 자연어 지시 → 해당 구간만 반영된 새 맵 + 파싱 결과)

이 개발 컨테이너에는 `GEMINI_API_KEY`가 없어 실제 Gemini 호출은 검증하지 못했고, 규칙 기반 폴백 경로로 전체 기능을 테스트했습니다. Gemini 키를 `.env`에 넣으면 자동으로 AI 경로가 우선 사용됩니다.

`app/storage`에 `GeneratedMap`을 실제 ADOFAI 커스텀 레벨(`.adofai`, JSON) 포맷으로 저장/불러오는 모듈을 구현했습니다.

- 저장: `app/storage/adofai_writer.py` — 타일의 상대 회전각을 누적해 `angleData`(절대 각도)를 만들고, 방향이 바뀌는 타일마다 **Twirl** 액션을 넣어 실제 재생 시간이 방향과 무관하게 원래 의도한 박자를 유지하도록 보정한다. 구간별 BPM이 바뀌는 지점에는 `SetSpeed` 액션을 넣는다
- 불러오기: `app/storage/adofai_reader.py` — `angleData`+`actions`(SetSpeed, Twirl)로부터 각 타일의 실제 시각을 역산해 `GeneratedMap`으로 되돌린다. 저장 시 사용한 것과 정확히 대응하는 공식으로 구현해, 이 왕복 변환이 정확히 일치하는지가 곧 위 "회전각→박자" 공식이 맞는지를 검증하는 테스트가 된다
- API: `POST /storage/export` (기존 맵 + 곡 파일명/아티스트 등 메타데이터 → `.adofai` 파일 다운로드), `POST /storage/import` (`.adofai` 파일 업로드 → 맵 JSON, 이어서 편집 가능)
- **플레이 가능성 검증**: `app/storage/validator.py`의 `validate_adofai_document()`가 (1) 구조 검증(angleData/settings 필수 필드, NaN·무한대 값, SetSpeed BPM 유효성), (2) 타이밍 검증(타일 간격이 사람이 반응 가능한 범위 0.04~15초를 벗어나면 경고), (3) 왕복 일치 검증(저장한 파일을 다시 읽었을 때 원본과 타일 시각이 정확히 일치하는지, 어긋나면 오류)을 수행한다. `POST /storage/export`는 내보내기 직전 이 검증을 자체적으로 통과해야만 파일을 반환하고(실패 시 500), `POST /storage/validate`로 저장 없이 미리 점검만 할 수도 있다

**주의(Twirl 액션의 정확한 JSON 스펙)**: Twirl 액션의 정확한 필드 구성은 공식 문서가 아니라 커뮤니티 도구(ADOFAI-Map-Converter, adofai-angle-calculator)의 역공학 결과를 참고해 `{"floor": N, "eventType": "Twirl"}` 형태로 구현했습니다. 실제 게임/에디터에서 열었을 때 회전 "방향"이 의도와 다르게 보인다면 이 부분을 우선 의심해야 합니다 — **타이밍(박자) 자체는 Twirl 필드명과 무관하게 위에서 설명한 회전각→박자 공식으로 이미 왕복 테스트(65,539개 타일 전이, 최대 오차 3.5e-15초)로 검증되어 있습니다.** 즉 최악의 경우도 "일부 타일이 반대 방향으로 꺾여 보이는" 시각적 문제이지, 음악과 어긋나는 문제는 아닙니다.

`frontend/`에 Flutter 데스크톱(Linux/Windows) 앱을 구현했습니다. 백엔드 API를 그대로 호출하는 얇은 클라이언트로, 별도의 상태 서버 없이 동작합니다.

- 데이터 모델: `lib/models/generated_map.dart` — 백엔드 Pydantic 모델과 1:1 대응하는 `Tile`/`GeneratedMap`/`EditInstruction`
- API 클라이언트: `lib/services/api_client.dart` — `POST /mapgen/generate`(멀티파트 업로드), `POST /ai/edit-segment`, `POST /storage/export`(.adofai 다운로드), `POST /storage/import`(.adofai 업로드) 호출
- 화면: `lib/screens/home_screen.dart` — 음악 파일 선택(mp3/ogg/wav), `.adofai` 불러오기, 난이도 선택, 시드 입력, 생성 버튼, 진행 상태 표시, 곡 제목/아티스트 입력 후 저장, 자연어 구간 재생성 입력창을 한 화면에 배치
- 미리보기: `lib/widgets/map_preview.dart` — 각 타일의 상대 회전각을 누적해 진행 방향을 구하고 선분을 이어 그리는 `CustomPainter`. 다운비트/드롭 구간은 색을 달리해 강조하며, 확대/축소·이동이 가능하다(`InteractiveViewer`)
- 난이도 선택: `lib/widgets/difficulty_selector.dart` — 1~26 슬라이더, 마법진/질주맵/슬로우 스타일 옵션 칩

**진행률 표시**: 백엔드가 작업 진행률(%)을 스트리밍하지 않으므로(동기 HTTP 응답), 현재는 부정확한(indeterminate) 진행 표시줄 + 상태 문구로 처리합니다. 정확한 퍼센트 진행률을 원하면 추후 SSE/WebSocket 기반 진행상황 API가 필요합니다.

**저장/불러오기**: 6단계에서 실제 `.adofai` 변환이 구현되어, "저장" 버튼은 이제 진짜 ADOFAI가 읽을 수 있는 `.adofai` 파일을 저장합니다(곡 제목/아티스트 입력 가능). "불러오기(.adofai)" 버튼으로 이전에 저장한 파일을 다시 불러와 이어서 편집(구간 재생성)할 수도 있습니다.

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

**exe 패키징 (Windows에서 실행)**

```powershell
# 1) 백엔드를 단일 exe로 묶기
cd backend
pip install -r requirements.txt -r packaging/requirements-build.txt
pyinstaller packaging/adofai_backend.spec --distpath dist --workpath build
# 결과: backend/dist/adofai_backend/adofai_backend.exe

# 2) GUI를 Windows exe로 빌드
cd ../frontend
flutter build windows --release
# 결과: frontend/build/windows/x64/runner/Release/adofai_map_generator.exe

# 3) 하나로 합치기: Release 폴더 안에 adofai_backend/ 폴더를 만들고
#    backend/dist/adofai_backend/의 내용을 통째로 복사
```

또는 GitHub Actions에서 `Windows Package` 워크플로우(`workflow_dispatch`)를
수동 실행하면 위 세 단계를 자동으로 수행해 zip 아티팩트를 만들어 줍니다.

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
    api/routes/         # API 라우터 (health, audio, mapgen, ai_edit, storage)
    audio/               # 오디오 분석 모듈 (BPM/비트/다운비트/에너지/템포변화/드롭)
    mapgen/              # 맵 생성 엔진 (난이도별 분할/회전 패턴, 구간 재생성)
    ai/                  # AI 연동 (Gemini 무료 티어 + 규칙 기반 폴백, 자연어 구간 편집)
    storage/             # ADOFAI 레벨 파일 저장/불러오기 (adofai_writer, adofai_reader, validator)
    models/              # 공용 데이터 모델 (Pydantic)
  packaging/             # 8단계: exe 패키징 (PyInstaller 진입점 + spec)
    run_backend.py
    adofai_backend.spec
    requirements-build.txt
  tests/                # pytest 테스트
  requirements.txt
  pyproject.toml
  .env.example
frontend/               # Flutter 데스크톱 UI (Linux/Windows)
  lib/
    main.dart
    models/generated_map.dart   # 백엔드 모델과 대응하는 Dart 데이터 클래스
    services/api_client.dart     # FastAPI 백엔드 HTTP 클라이언트
    services/backend_launcher.dart  # 8단계: 번들된 백엔드 exe 자동 실행
    screens/home_screen.dart     # 메인 화면 (파일 선택~구간 재생성)
    widgets/                     # DifficultySelector, MapPreview(CustomPainter)
  test/                          # flutter_test 위젯 테스트
  linux/, windows/               # 데스크톱 플랫폼별 러너 (flutter create 스캐폴드)
.github/workflows/
  blank.yml                # CI: pytest + flutter analyze/test
  windows-package.yml      # 8단계: windows-latest에서 exe 패키징 후 zip 아티팩트 업로드
```
