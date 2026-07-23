# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 빌드 스펙: FastAPI 백엔드를 단일 실행 파일로 묶는다.

이 저장소를 개발 중인 리눅스 컨테이너에는 Windows 툴체인이 없어 실제 .exe를
여기서 만들 수는 없다. 대신 이 스펙 파일은 Windows 머신(또는
`.github/workflows/windows-package.yml`의 windows-latest CI 러너)에서
그대로 실행되어 진짜 .exe를 생성한다.

빌드 방법 (Windows, backend/ 디렉터리에서):
    pip install -r requirements.txt -r packaging/requirements-build.txt
    pyinstaller packaging/adofai_backend.spec --distpath dist --workpath build

결과물: backend/dist/adofai_backend/adofai_backend.exe
        (+ 같은 폴더에 필요한 라이브러리 전부 포함)
"""

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
BACKEND_DIR = os.path.dirname(SPEC_DIR)

# librosa/soundfile은 동적 임포트와 데이터 파일(예: librosa 예제/캐시 설정)이
# 많아 PyInstaller의 정적 분석만으로는 전부 찾지 못하는 경우가 있다.
hidden_imports = (
    collect_submodules("librosa")
    + collect_submodules("soundfile")
    + collect_submodules("uvicorn")
)
# imageio_ffmpeg의 정적 ffmpeg 바이너리(app/audio/ffmpeg_setup.py가 PATH에 등록해
# mp3 디코딩에 사용)도 데이터로 포함해야 exe만으로 ffmpeg 없이 동작한다.
datas = collect_data_files("librosa") + collect_data_files("imageio_ffmpeg")

a = Analysis(
    [os.path.join(SPEC_DIR, "run_backend.py")],
    pathex=[BACKEND_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="adofai_backend",
    debug=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="adofai_backend",
)
