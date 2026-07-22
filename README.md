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
| AI 패턴 생성/편집 | Claude API |
| 데이터 저장 | JSON |

## 개발 로드맵

기존 코드를 임의로 삭제하지 않고, 각 단계가 끝날 때마다 실행 가능한 상태를 유지하며 순서대로 진행합니다.

- [x] 1단계 — 프로젝트 생성 (`backend/` FastAPI 스캐폴드, 테스트 환경)
- [x] 2단계 — 오디오 분석 (BPM/비트/다운비트/드롭/음량 변화/템포 변화 검출)
- [x] 3단계 — 맵 생성 엔진 (리듬 패턴 → ADOFAI 타일 시퀀스, 난이도 반영)
- [ ] 4단계 — Claude 연동 (패턴 생성 및 구간별 재생성 프롬프트/클라이언트)
- [ ] 5단계 — GUI 제작 (Flutter 데스크톱 앱)
- [ ] 6단계 — 파일 저장 (ADOFAI `.adofai` 커스텀 레벨 포맷 저장/불러오기)
- [ ] 7단계 — 테스트 (각 모듈 단위 테스트 + 통합 테스트)
- [ ] 8단계 — 배포용 실행 파일(.exe) 패키징 (백엔드: PyInstaller, GUI: Flutter Windows build)

## 현재 상태 (3단계까지 완료)

`backend/` 아래에 FastAPI 프로젝트 골격을 구성했습니다. 이후 단계(AI 연동, 파일 저장)의 모듈 자리(`app/ai`, `app/storage`)를 미리 잡아두었고, 헬스체크 엔드포인트와 테스트가 동작합니다.

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

### 실행 방법

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

브라우저에서 http://127.0.0.1:8000/health 접속 시 `{"status": "ok"}` 응답을 확인할 수 있습니다.

### 테스트

```bash
cd backend
pip install -r requirements.txt
pytest
```

## 프로젝트 구조

```
backend/
  app/
    main.py            # FastAPI 앱 진입점
    core/config.py     # 환경설정 (Pydantic Settings)
    api/routes/         # API 라우터 (health, audio, mapgen)
    audio/               # 오디오 분석 모듈 (BPM/비트/다운비트/에너지/템포변화/드롭)
    mapgen/              # 맵 생성 엔진 (난이도별 회전 패턴, 구간 재생성)
    ai/                  # (4단계) Claude API 연동
    storage/             # (6단계) ADOFAI 레벨 파일 저장/불러오기
    models/              # 공용 데이터 모델 (Pydantic)
  tests/                # pytest 테스트
  requirements.txt
  pyproject.toml
  .env.example
frontend/               # (5단계) Flutter 데스크톱 UI
```
