"""Animate storyboard stills into video clips (image-to-video via agent-media/fal)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


class AnimationError(RuntimeError):
    pass


def fal_available() -> bool:
    return bool(os.environ.get("FAL_API_KEY") or os.environ.get("FAL_KEY"))


def animate_still(
    image: Path,
    prompt: str,
    out: Path,
    *,
    duration: float = 5.0,
    resolution: str = "720p",
    fps: int = 25,
) -> Path:
    """Run agent-media image-to-video. Requires FAL_API_KEY."""
    if not fal_available():
        raise AnimationError(
            "FAL_API_KEY is not set. Add it to the Cloud Agent environment secrets "
            "to animate storyboard stills into video clips."
        )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Cap duration for provider limits; caller may loop/trim later
    dur = max(2, min(8, int(round(duration))))
    cmd = [
        "npx",
        "--yes",
        "agent-media",
        "video",
        "generate",
        "--prompt",
        prompt,
        "--in",
        str(image),
        "--duration",
        str(dur),
        "--resolution",
        resolution,
        "--fps",
        str(fps),
        "--out",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # agent-media prints JSON
    payload = None
    for line in (result.stdout or "").strip().splitlines()[::-1]:
        line = line.strip()
        if line.startswith("{"):
            try:
                payload = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if result.returncode != 0 or (payload and payload.get("ok") is False):
        err = (payload or {}).get("error") or result.stderr or result.stdout
        raise AnimationError(f"animate failed for {image.name}: {err}")
    if not out.exists():
        # Some versions write beside --out with a generated name; search
        matches = sorted(out.parent.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            matches[0].replace(out)
        else:
            raise AnimationError(f"No output video written for {image.name}")
    return out


def motion_prompt(beat: str, kind: str, motion: str) -> str:
    """Text prompt guiding I2V motion without inventing new subjects."""
    base = (
        "Animate this cyberpunk neon digital pop-art frame with thick outlines. "
        "Keep the same composition and characters. Smooth cinematic camera motion, "
        "subtle neon flicker, parallax depth. No new text, no watermark. "
    )
    motion_hints = {
        "slow_drift": "Slow gentle drift and soft neon pulse.",
        "breathe_zoom": "Slow breathing zoom in and out.",
        "film_pan_left": "Slow pan left across the scene.",
        "film_pan_right": "Slow pan right across the scene.",
        "film_pan_up": "Slow tilt up.",
        "film_pan_down": "Slow tilt down.",
        "zoom_in": "Steady push-in zoom.",
        "zoom_out": "Steady pull-out zoom.",
        "zoom_out_soft": "Soft pull-back reveal.",
        "diagonal_in": "Diagonal push-in.",
        "orbit_drift": "Slight orbital drift around subject.",
        "pulse_zoom": "Rhythmic subtle zoom pulses.",
        "push_in_pan": "Push in while drifting sideways.",
        "punch_in": "Fast punch-in then settle.",
        "snap_zoom": "Quick snap zoom then hold.",
        "crash_zoom": "Dramatic crash zoom.",
        "whip_pan_left": "Quick whip pan left.",
        "whip_pan_right": "Quick whip pan right.",
        "shake_light": "Very light handheld micro-movement.",
        "shake_hard": "Light handheld energy, not chaotic.",
        "shake_zoom": "Light shake with gentle zoom.",
    }
    hint = motion_hints.get(motion, "Cinematic slow camera move.")
    role = "Hero character is the focus." if kind == "star" else (
        "Story atmosphere leads; keep any figure secondary." if kind == "supporting"
        else "No hero close-up; animate the environment and neon."
    )
    return f"{base}{hint} {role} Scene: {beat}"
