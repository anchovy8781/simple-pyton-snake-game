# Frontend (Flutter 데스크톱 UI)

FastAPI 백엔드(`../backend/`)와 통신하는 Flutter 데스크톱 앱입니다. 음악 파일
선택, 난이도 선택, 생성/진행 상태 표시, 타일 경로 미리보기, 저장, 자연어
구간 재생성 요청 UI를 하나의 화면에서 제공합니다.

## 실행

```bash
flutter pub get
flutter run -d linux    # 또는 -d windows
```

백엔드가 `http://127.0.0.1:8000`에서 실행 중이어야 합니다(앱 상단에서 주소
변경 가능). 자세한 내용은 저장소 루트 `README.md`의 "5단계" 절을 참고하세요.

## 테스트

```bash
flutter analyze
flutter test
```
