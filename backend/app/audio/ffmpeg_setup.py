"""시스템에 ffmpeg가 설치되어 있지 않아도 mp3를 디코딩할 수 있게 한다.

librosa.load()는 mp3 등 압축 포맷을 읽을 때 우선 soundfile(libsndfile)을
시도하고, 그게 실패하면 audioread로 넘어간다. audioread는 PATH에서
정확히 "ffmpeg"(Windows는 "ffmpeg.exe") 또는 "avconv"라는 이름의 실행
파일을 찾는데, 사용자 PC(특히 exe로 패키징해 배포한 경우)에는 ffmpeg가
설치되어 있지 않은 경우가 많다 — 이때 soundfile도 실패하는 mp3(예:
특정 인코더/VBR 조합)를 만나면 "NoBackendError"로 오디오 로딩 전체가
실패한다.

exe로 패키징된 경우와 일반 개발 환경, 두 경로를 모두 처리한다:

1. **패키징된 exe(PyInstaller로 얼린 상태)**: `imageio_ffmpeg`처럼 자기
   패키지의 `__file__` 기준 상대 경로로 내부 바이너리를 찾는 라이브러리는
   PyInstaller로 얼리면 그 경로 해석이 깨지기 쉬운 잘 알려진 함정이 있다.
   그래서 런타임에 imageio_ffmpeg를 다시 임포트해 경로를 찾는 대신,
   **빌드 시점**(`packaging/adofai_backend.spec`, 일반 Python 환경에서 실행됨)에
   미리 "ffmpeg" 이름으로 바이너리를 실행 파일과 같은 폴더에 복사해두고,
   여기서는 그 폴더만 확인한다 — 훨씬 더 안정적이다.
2. **개발 환경(얼려지지 않은 일반 실행)**: `imageio-ffmpeg`가 pip 설치
   시점에 함께 받아오는 정적 바이너리를 "ffmpeg"라는 이름으로 복사해
   PATH에 추가한다(라이선스상 재배포 가능한 빌드).
"""

import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

_FFMPEG_SHIM_DIR = Path(tempfile.gettempdir()) / "adofai_map_generator_ffmpeg"


def _ffmpeg_name() -> str:
    return "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"


def ensure_ffmpeg_on_path() -> None:
    """PATH에 "ffmpeg"라는 이름의 실행 파일이 없으면 찾아서(또는 준비해서) 등록한다.

    실패해도(패키지가 없거나 파일 시스템 쓰기 권한이 없는 등) 예외를 던지지
    않는다 — 이 함수는 어디까지나 mp3 디코딩 성공률을 높이는 보강 조치이고,
    실패하면 기존처럼 시스템 ffmpeg/soundfile만으로 동작을 시도하면 된다.
    """
    ffmpeg_name = _ffmpeg_name()
    if shutil.which(ffmpeg_name):
        return  # 이미 시스템에 ffmpeg가 있다.

    if getattr(sys, "frozen", False):
        # PyInstaller onedir 빌드에서는 실행 파일과 번들된 파일들이 같은
        # 폴더에 있다 — adofai_backend.spec이 여기에 ffmpeg를 놓아둔다.
        bundled = Path(sys.executable).parent / ffmpeg_name
        if bundled.exists():
            _prepend_to_path(bundled.parent)
            return

    try:
        import imageio_ffmpeg

        _FFMPEG_SHIM_DIR.mkdir(parents=True, exist_ok=True)
        shim_path = _FFMPEG_SHIM_DIR / ffmpeg_name
        if not shim_path.exists():
            shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), shim_path)
            shim_path.chmod(shim_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        return

    _prepend_to_path(_FFMPEG_SHIM_DIR)


def _prepend_to_path(directory: Path) -> None:
    path_dir = str(directory)
    current_path = os.environ.get("PATH", "")
    if path_dir not in current_path.split(os.pathsep):
        os.environ["PATH"] = path_dir + os.pathsep + current_path
