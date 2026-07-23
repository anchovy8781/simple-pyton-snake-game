"""PyInstaller로 패키징되는 백엔드(.exe) 실행 진입점.

`pyinstaller`는 이 스크립트 하나를 시작점으로 삼아 FastAPI 앱과 모든
의존성(librosa, numpy 등)을 하나의 실행 파일로 묶는다. 빌드된 .exe를
더블클릭하면 이 main()이 바로 실행되어 로컬에서만 접근 가능한 서버가 뜬다.

Flutter GUI(frontend)는 기본값으로 http://127.0.0.1:8000 에 접속하므로,
포트를 다른 값으로 바꾸려면 이 파일과 frontend의 기본 백엔드 주소를
함께 수정해야 한다.
"""

import sys
from pathlib import Path

# PyInstaller 번들 안에서도 `app` 패키지를 절대 임포트할 수 있도록
# backend/ 디렉터리를 경로에 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from app.main import app

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def main() -> None:
    # 데스크톱 앱 용도이므로 --reload 없이, 로컬 루프백 주소로만 바인딩한다.
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT, log_level="info")


if __name__ == "__main__":
    main()
