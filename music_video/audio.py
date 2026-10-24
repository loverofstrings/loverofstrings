"""Audio / video track probing and lightweight BPM estimation."""

from __future__ import annotations

import json
import math
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EnergyEnvelope:
    """Per-window RMS energy normalized 0..1 across the full track."""

    hop_sec: float
    values: list[float]  # one value per hop

    def at(self, t: float) -> float:
        if not self.values:
            return 0.5
        i = int(t / self.hop_sec)
        i = max(0, min(len(self.values) - 1, i))
        return self.values[i]

    def mean(self, start: float, end: float) -> float:
        if not self.values or end <= start:
            return self.at(start)
        i0 = max(0, int(start / self.hop_sec))
        i1 = min(len(self.values), max(i0 + 1, int(math.ceil(end / self.hop_sec))))
        chunk = self.values[i0:i1]
        return sum(chunk) / len(chunk) if chunk else 0.5


@dataclass
class AudioInfo:
    path: Path
    duration: float
    sample_rate: int | None
    channels: int | None
    has_video: bool
    bpm_estimate: float | None
    energy: EnergyEnvelope | None = None


def _ffprobe(path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def probe(path: str | Path) -> AudioInfo:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Track not found: {path}")

    data = _ffprobe(path)
    duration = float(data.get("format", {}).get("duration") or 0)
    streams = data.get("streams") or []
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    has_video = any(s.get("codec_type") == "video" for s in streams)

    sample_rate = int(audio["sample_rate"]) if audio and audio.get("sample_rate") else None
    channels = int(audio["channels"]) if audio and audio.get("channels") else None

    bpm = _estimate_bpm(path, duration) if duration > 0 else None
    energy = _energy_envelope(path, duration) if duration > 0 else None

    return AudioInfo(
        path=path,
        duration=duration,
        sample_rate=sample_rate,
        channels=channels,
        has_video=has_video,
        bpm_estimate=bpm,
        energy=energy,
    )


def _energy_envelope(path: Path, duration: float, hop_sec: float = 0.25) -> EnergyEnvelope | None:
    """Full-track mono energy curve for music-reactive timing/motion."""
    wav_path = path.with_suffix(".mv_energy.wav")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(path),
                "-ac",
                "1",
                "-ar",
                "8000",
                "-f",
                "wav",
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
        import array

        with wave.open(str(wav_path), "rb") as wf:
            rate = wf.getframerate()
            samples = array.array("h")
            samples.frombytes(wf.readframes(wf.getnframes()))
        if not samples:
            return None
        hop = max(1, int(rate * hop_sec))
        raw: list[float] = []
        for i in range(0, len(samples) - hop, hop):
            chunk = samples[i : i + hop]
            raw.append(math.sqrt(sum(s * s for s in chunk) / len(chunk)))
        if not raw:
            return None
        # Smooth + normalize
        smoothed = raw[:]
        for i in range(1, len(raw) - 1):
            smoothed[i] = 0.25 * raw[i - 1] + 0.5 * raw[i] + 0.25 * raw[i + 1]
        lo, hi = min(smoothed), max(smoothed)
        span = (hi - lo) or 1.0
        values = [(v - lo) / span for v in smoothed]
        return EnergyEnvelope(hop_sec=hop_sec, values=values)
    except (subprocess.CalledProcessError, OSError, wave.Error):
        return None
    finally:
        if wav_path.exists():
            wav_path.unlink(missing_ok=True)


def _estimate_bpm(path: Path, duration: float) -> float | None:
    """Rough BPM from energy onset density via ffmpeg silencedetect / pcm."""
    # Extract mono 8kHz PCM for a short analysis window (middle of track)
    if duration < 2:
        return None
    start = max(0.0, duration * 0.25)
    window = min(30.0, duration * 0.5)
    wav_path = path.with_suffix(".mv_analyze.wav")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{start:.3f}",
                "-t",
                f"{window:.3f}",
                "-i",
                str(path),
                "-ac",
                "1",
                "-ar",
                "8000",
                "-f",
                "wav",
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
        return _bpm_from_wav(wav_path)
    except (subprocess.CalledProcessError, OSError, wave.Error):
        return None
    finally:
        if wav_path.exists():
            wav_path.unlink(missing_ok=True)


def _bpm_from_wav(wav_path: Path) -> float | None:
    with wave.open(str(wav_path), "rb") as wf:
        n = wf.getnframes()
        rate = wf.getframerate()
        raw = wf.readframes(n)
    if n < rate:
        return None

    # 16-bit mono
    import array

    samples = array.array("h")
    samples.frombytes(raw)
    if not samples:
        return None

    # Frame energy (hop ~ 50ms)
    hop = max(1, rate // 20)
    energies: list[float] = []
    for i in range(0, len(samples) - hop, hop):
        chunk = samples[i : i + hop]
        e = math.sqrt(sum(s * s for s in chunk) / len(chunk))
        energies.append(e)

    if len(energies) < 8:
        return None

    mean = sum(energies) / len(energies)
    threshold = mean * 1.25
    peaks: list[int] = []
    for i in range(1, len(energies) - 1):
        if energies[i] > threshold and energies[i] >= energies[i - 1] and energies[i] >= energies[i + 1]:
            if not peaks or i - peaks[-1] >= 2:
                peaks.append(i)

    if len(peaks) < 4:
        return 100.0  # neutral fallback

    intervals = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
    avg_hop = sum(intervals) / len(intervals)
    seconds_per_beat = (avg_hop * hop) / rate
    if seconds_per_beat <= 0:
        return None
    bpm = 60.0 / seconds_per_beat
    # Fold into musical range
    while bpm < 70:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return round(bpm, 1)
