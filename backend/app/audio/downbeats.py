"""다운비트(마디의 첫 박) 감지."""

import librosa
import numpy as np

from app.audio.beats import DEFAULT_HOP_LENGTH


def detect_downbeats(
    beat_times: np.ndarray,
    onset_env: np.ndarray,
    sr: int,
    hop_length: int = DEFAULT_HOP_LENGTH,
    beats_per_bar: int = 4,
) -> np.ndarray:
    """마디의 시작 박(다운비트) 위치를 추정한다.

    별도의 마디 인식 모델 없이, 박자를 `beats_per_bar`개씩 묶었을 때 가능한
    각 위상(phase)마다 onset envelope 합을 비교해 가장 강조되는 위상을
    마디의 시작으로 가정하는 휴리스틱이다. 대부분의 대중음악은 다운비트에서
    타격감(킥/스네어)이 가장 강하게 나타난다는 경향에 기반한다.
    """
    if len(beat_times) < beats_per_bar:
        return beat_times.copy()

    beat_frames = librosa.time_to_frames(beat_times, sr=sr, hop_length=hop_length)
    beat_frames = np.clip(beat_frames, 0, len(onset_env) - 1)
    beat_strengths = onset_env[beat_frames]

    best_phase = 0
    best_score = -np.inf
    for phase in range(beats_per_bar):
        score = float(beat_strengths[phase::beats_per_bar].sum())
        if score > best_score:
            best_score = score
            best_phase = phase

    return beat_times[best_phase::beats_per_bar]
