"""Frame / cut timing derived from BPM, genre speed, and storyboard scenes."""

from __future__ import annotations

from dataclasses import dataclass

from .story import Scene, Storyboard
from .theme import ThemeSpec


@dataclass
class TimedShot:
    scene: Scene
    start: float
    end: float
    duration: float
    fps: int
    frames: int
    motion: str
    zoom: float
    image_index: int
    caption: str


def _target_cut_length(bpm: float | None, speed: float) -> float:
    """Ideal seconds between visual cuts."""
    if bpm and bpm > 0:
        # One cut every 2–4 beats depending on speed
        beats = 4.0 / max(0.5, speed)
        beats = max(1.0, min(8.0, beats))
        return (60.0 / bpm) * beats
    # No BPM: map speed to 1.2–5s cuts
    return max(0.8, min(6.0, 3.2 / speed))


def expand_shots(
    board: Storyboard,
    theme: ThemeSpec,
    bpm: float | None,
    fps: int = 30,
    *,
    one_shot_per_scene: bool = False,
) -> list[TimedShot]:
    """Subdivide storyboard scenes into timed visual shots.

    When ``one_shot_per_scene`` is True (used with an explicit scene count),
    each storyboard scene becomes exactly one shot — no BPM subdivision.
    """
    target = _target_cut_length(bpm, theme.speed)
    shots: list[TimedShot] = []

    for scene in board.scenes:
        span = max(0.05, scene.end - scene.start)
        if one_shot_per_scene:
            n = 1
        else:
            n = max(1, round(span / target))
            n = min(n, max(1, int(span / 0.6)))
        piece = span / n
        for j in range(n):
            start = scene.start + j * piece
            end = scene.start + (j + 1) * piece if j < n - 1 else scene.end
            dur = max(0.05, end - start)
            frames = max(1, int(round(dur * fps)))
            caption = _caption_slice(scene.text, j, n, theme.caption_style)
            shots.append(
                TimedShot(
                    scene=scene,
                    start=round(start, 3),
                    end=round(end, 3),
                    duration=round(dur, 3),
                    fps=fps,
                    frames=frames,
                    motion=scene.motion,
                    zoom=scene.zoom,
                    image_index=scene.image_index,
                    caption=caption,
                )
            )
    return shots


def _caption_slice(text: str, piece: int, total: int, style: str) -> str:
    if not text.strip():
        return ""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    if style == "kinetic":
        # One line (or short phrase) per piece
        return lines[piece % len(lines)]
    if total == 1 or piece == 0:
        # Show up to 2 lines at scene start
        return "\n".join(lines[:2])
    # Later pieces: rotate remaining lines
    if len(lines) > 2:
        return lines[2 + (piece - 1) % max(1, len(lines) - 2)]
    return lines[piece % len(lines)]
