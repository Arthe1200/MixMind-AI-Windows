"""Optional offline track-analysis helpers."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class TrackAnalysis:
    bpm: float | None
    duration_seconds: float | None
    sample_rate: int | None
    waveform: tuple[float, ...] = ()

def analyze_track(path: str | Path, waveform_points: int = 500) -> TrackAnalysis:
    """Estimate BPM and waveform envelope using the optional analysis dependencies.

    BPM values are estimates. Run this function in a worker, never on an audio callback.
    """
    if waveform_points < 1:
        raise ValueError("waveform_points must be positive")
    try:
        import librosa
        import numpy as np
        import soundfile as sf
    except ImportError as exc:
        raise ImportError("Install analysis dependencies with pip install -e '.[analysis]'") from exc
    info = sf.info(str(Path(path)))
    bpm = None
    waveform: tuple[float, ...] = ()
    try:
        signal, sample_rate = sf.read(str(Path(path)), dtype="float32", always_2d=True)
        mono = np.mean(signal, axis=1)
        if mono.size:
            tempo, _ = librosa.beat.beat_track(y=mono, sr=sample_rate)
            estimated = float(np.asarray(tempo).reshape(-1)[0])
            if 30.0 <= estimated <= 300.0:
                bpm = estimated
            edges = np.linspace(0, len(mono), min(waveform_points, len(mono)) + 1, dtype=int)
            envelope = [float(np.max(np.abs(mono[edges[i]:edges[i + 1]])))
                        if edges[i + 1] > edges[i] else 0.0 for i in range(len(edges) - 1)]
            peak = max(envelope, default=0.0)
            waveform = tuple(value / peak for value in envelope) if peak > 0 else tuple(envelope)
    except (RuntimeError, ValueError):
        pass
    return TrackAnalysis(bpm, float(info.duration), int(info.samplerate), waveform)
