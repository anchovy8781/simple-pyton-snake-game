"""오디오 분석 파이프라인 진입점.

파일 로딩부터 BPM/비트/다운비트/에너지/템포 변화/드롭 검출까지의 개별
단계를 조합해 하나의 `AudioAnalysisResult`를 만든다.
"""

from pathlib import Path

from app.audio.beats import DEFAULT_HOP_LENGTH, compute_onset_envelope, detect_tempo_and_beats
from app.audio.downbeats import detect_downbeats
from app.audio.drops import detect_drops
from app.audio.energy import build_energy_profile, compute_rms_curve
from app.audio.loader import load_audio
from app.audio.tempo_changes import detect_tempo_changes
from app.models.audio import AudioAnalysisResult


def analyze_audio(
    file_path: Path,
    hop_length: int = DEFAULT_HOP_LENGTH,
    beats_per_bar: int = 4,
) -> AudioAnalysisResult:
    y, sr = load_audio(file_path)
    duration_sec = float(len(y) / sr)

    onset_env = compute_onset_envelope(y, sr, hop_length)
    bpm, beat_times = detect_tempo_and_beats(y, sr, onset_env=onset_env, hop_length=hop_length)
    downbeat_times = detect_downbeats(beat_times, onset_env, sr, hop_length, beats_per_bar)

    times, rms_db = compute_rms_curve(y, sr, hop_length)
    energy_profile = build_energy_profile(times, rms_db, sr, hop_length)
    tempo_changes = detect_tempo_changes(onset_env, sr, hop_length)
    drops = detect_drops(times, rms_db, sr, hop_length)

    return AudioAnalysisResult(
        duration_sec=duration_sec,
        sample_rate=sr,
        bpm=bpm,
        beat_times=[float(t) for t in beat_times],
        downbeat_times=[float(t) for t in downbeat_times],
        energy_profile=energy_profile,
        tempo_changes=tempo_changes,
        drops=drops,
    )
