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
import shutil
import sys
import tempfile

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
datas = collect_data_files("librosa")

# ffmpeg 바이너리는 app/audio/ffmpeg_setup.py가 PATH에 등록해 mp3 디코딩에
# 쓴다. imageio_ffmpeg는 자기 패키지의 __file__ 기준 상대 경로로 바이너리를
# 찾는데, 이런 방식은 PyInstaller로 얼리면 깨지기 쉬운 잘 알려진 함정이다.
# 그래서 런타임에 그 경로 해석에 의존하는 대신, 지금(일반 Python 환경에서
# 실행되는 이 spec 파일 안)에 미리 "ffmpeg"라는 이름으로 복사해두고,
# 실행 파일(adofai_backend.exe)과 같은 폴더에 그대로 놓는다.
import imageio_ffmpeg  # noqa: E402

_ffmpeg_name = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
_ffmpeg_stage_dir = os.path.join(tempfile.gettempdir(), "adofai_pyinstaller_ffmpeg")
os.makedirs(_ffmpeg_stage_dir, exist_ok=True)
_ffmpeg_staged_path = os.path.join(_ffmpeg_stage_dir, _ffmpeg_name)
shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), _ffmpeg_staged_path)
binaries = [(_ffmpeg_staged_path, ".")]

a = Analysis(
    [os.path.join(SPEC_DIR, "run_backend.py")],
    pathex=[BACKEND_DIR],
    binaries=binaries,
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
