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
