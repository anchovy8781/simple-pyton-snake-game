from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from app.audio.exceptions import AudioLoadError, UnsupportedAudioFormatError
from app.audio.loader import load_audio


def test_load_audio_reads_valid_wav(tmp_path: Path) -> None:
    sr = 22050
    y = np.sin(2 * np.pi * 440 * np.arange(sr) / sr).astype(np.float32)
    wav_path = tmp_path / "tone.wav"
    sf.write(wav_path, y, sr)

    loaded_y, loaded_sr = load_audio(wav_path)

    assert loaded_sr == sr
    assert len(loaded_y) == pytest.approx(sr, abs=10)


def test_load_audio_rejects_unsupported_extension(tmp_path: Path) -> None:
    bad_path = tmp_path / "song.flac"
    bad_path.write_bytes(b"not a real audio file")

    with pytest.raises(UnsupportedAudioFormatError):
        load_audio(bad_path)


def test_load_audio_raises_when_file_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.wav"

    with pytest.raises(AudioLoadError):
        load_audio(missing_path)


def test_load_audio_reads_valid_mp3(tmp_path: Path) -> None:
    sr = 22050
    y = np.sin(2 * np.pi * 440 * np.arange(sr * 2) / sr).astype(np.float32) * 0.3
    mp3_path = tmp_path / "tone.mp3"
    sf.write(mp3_path, y, sr, format="MP3")

    loaded_y, loaded_sr = load_audio(mp3_path)

    assert loaded_sr == sr
    assert len(loaded_y) > 0


def test_ensure_ffmpeg_on_path_puts_a_real_ffmpeg_binary_on_path() -> None:
    import shutil
    import sys

    from app.audio.ffmpeg_setup import ensure_ffmpeg_on_path

    ensure_ffmpeg_on_path()

    ffmpeg_name = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
    found = shutil.which(ffmpeg_name)
    assert found is not None
