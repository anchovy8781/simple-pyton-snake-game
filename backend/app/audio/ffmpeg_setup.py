"""시스템에 ffmpeg가 설치되어 있지 않아도 mp3를 디코딩할 수 있게 한다.

librosa.load()는 mp3 등 압축 포맷을 읽을 때 우선 soundfile(libsndfile)을
시도하고, 그게 실패하면 audioread로 넘어간다. audioread는 PATH에서
정확히 "ffmpeg"(Windows는 "ffmpeg.exe") 또는 "avconv"라는 이름의 실행
파일을 찾는데, 사용자 PC(특히 exe로 패키징해 배포한 경우)에는 ffmpeg가
설치되어 있지 않은 경우가 많다 — 이때 soundfile도 실패하는 mp3(예:
특정 인코더/VBR 조합)를 만나면 "NoBackendError"로 오디오 로딩 전체가
실패한다.

`imageio-ffmpeg` 패키지가 정적 ffmpeg 바이너리를 pip 설치 시점에 함께
받아오므로(라이선스상 재배포 가능한 빌드), 그 바이너리를 "ffmpeg"라는
이름으로 복사해 PATH에 추가해두면 사용자가 ffmpeg를 따로 설치하지 않아도
동작한다. PyInstaller로 묶을 때도 이 바이너리가 함께 포함된다
(packaging/adofai_backend.spec).
"""

import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

_FFMPEG_SHIM_DIR = Path(tempfile.gettempdir()) / "adofai_map_generator_ffmpeg"


def ensure_ffmpeg_on_path() -> None:
    """PATH에 "ffmpeg"라는 이름의 실행 파일이 없으면 imageio-ffmpeg가 제공하는
    정적 바이너리를 그 이름으로 복사해 PATH 맨 앞에 추가한다.

    실패해도(패키지가 없거나 파일 시스템 쓰기 권한이 없는 등) 예외를 던지지
    않는다 — 이 함수는 어디까지나 mp3 디코딩 성공률을 높이는 보강 조치이고,
    실패하면 기존처럼 시스템 ffmpeg/soundfile만으로 동작을 시도하면 된다.
    """
    ffmpeg_name = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
    if shutil.which(ffmpeg_name):
        return  # 이미 시스템에 ffmpeg가 있다.

    try:
        import imageio_ffmpeg

        _FFMPEG_SHIM_DIR.mkdir(parents=True, exist_ok=True)
        shim_path = _FFMPEG_SHIM_DIR / ffmpeg_name
        if not shim_path.exists():
            shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), shim_path)
            shim_path.chmod(shim_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        return

    path_dir = str(_FFMPEG_SHIM_DIR)
    current_path = os.environ.get("PATH", "")
    if path_dir not in current_path.split(os.pathsep):
        os.environ["PATH"] = path_dir + os.pathsep + current_path
