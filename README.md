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
- [ ] 2단계 — 오디오 분석 (BPM/비트/다운비트/드롭/음량 변화 검출)
- [ ] 3단계 — 맵 생성 엔진 (리듬 패턴 → ADOFAI 타일 시퀀스, 난이도 반영)
- [ ] 4단계 — Claude 연동 (패턴 생성 및 구간별 재생성 프롬프트/클라이언트)
- [ ] 5단계 — GUI 제작 (Flutter 데스크톱 앱)
- [ ] 6단계 — 파일 저장 (ADOFAI `.adofai` 커스텀 레벨 포맷 저장/불러오기)
- [ ] 7단계 — 테스트 (각 모듈 단위 테스트 + 통합 테스트)
- [ ] 8단계 — 배포용 실행 파일(.exe) 패키징 (백엔드: PyInstaller, GUI: Flutter Windows build)

## 현재 상태 (1단계)

`backend/` 아래에 FastAPI 프로젝트 골격을 구성했습니다. 이후 단계(오디오 분석, 맵 생성 엔진, AI 연동, 파일 저장)의 모듈 자리(`app/audio`, `app/mapgen`, `app/ai`, `app/storage`)를 미리 잡아두었고, 헬스체크 엔드포인트와 테스트가 동작합니다.

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
    api/routes/         # API 라우터
    audio/               # (2단계) 오디오 분석 모듈
    mapgen/              # (3단계) 맵 생성 엔진
    ai/                  # (4단계) Claude API 연동
    storage/             # (6단계) ADOFAI 레벨 파일 저장/불러오기
    models/              # 공용 데이터 모델 (Pydantic)
  tests/                # pytest 테스트
  requirements.txt
  pyproject.toml
  .env.example
frontend/               # (5단계) Flutter 데스크톱 UI
```
