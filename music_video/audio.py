"""Audio / video track probing and lightweight BPM estimation."""

from __future__ import annotations

import json
import math
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioInfo:
    path: Path
    duration: float
    sample_rate: int | None
    channels: int | None
    has_video: bool
    bpm_estimate: float | None


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

    return AudioInfo(
        path=path,
        duration=duration,
        sample_rate=sample_rate,
        channels=channels,
        has_video=has_video,
        bpm_estimate=bpm,
    )


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
