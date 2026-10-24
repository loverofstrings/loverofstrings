"""Frame / cut timing derived from BPM, energy, lyric density, and genre speed."""

from __future__ import annotations

from dataclasses import dataclass

from .audio import EnergyEnvelope
from .effects import pick_effect
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
    intensity: float = 0.5


def _target_cut_length(bpm: float | None, speed: float) -> float:
    if bpm and bpm > 0:
        beats = 4.0 / max(0.5, speed)
        beats = max(1.0, min(8.0, beats))
        return (60.0 / bpm) * beats
    return max(0.8, min(6.0, 3.2 / speed))


def _lyric_density(text: str, span: float) -> float:
    """Words per second, normalized roughly into 0..1."""
    words = [w for w in (text or "").replace("\n", " ").split() if w.strip()]
    if span <= 0.05:
        return 0.5
    wps = len(words) / span
    # ~1 wps calm, ~4+ wps hot
    return max(0.0, min(1.0, (wps - 0.5) / 3.5))


def _scene_intensity(
    scene: Scene,
    energy: EnergyEnvelope | None,
) -> float:
    span = max(0.05, scene.end - scene.start)
    e = energy.mean(scene.start, scene.end) if energy else 0.5
    dens = _lyric_density(scene.text, span)
    role = scene.role.lower()
    role_boost = 0.0
    if "chorus" in role or "hook" in role:
        role_boost = 0.2
    elif "bridge" in role:
        role_boost = 0.1
    elif "intro" in role or "outro" in role:
        role_boost = -0.15
    return max(0.0, min(1.0, 0.45 * e + 0.35 * dens + 0.2 * (0.5 + role_boost)))


def retime_scenes_by_music(
    board: Storyboard,
    energy: EnergyEnvelope | None,
    theme: ThemeSpec,
) -> Storyboard:
    """Stretch/compress scene lengths from energy + lyric density (keep order)."""
    if len(board.scenes) < 2:
        return board

    weights: list[float] = []
    for scene in board.scenes:
        span = max(0.05, scene.end - scene.start)
        dens = _lyric_density(scene.text, span)
        e = energy.mean(scene.start, scene.end) if energy else 0.5
        # Hot/dense → shorter scenes (lower weight); calm → linger
        # weight proportional to desired duration
        intensity = 0.5 * e + 0.5 * dens
        # desired relative length: calm long (1.4), hot short (0.55)
        w = 1.4 - 0.85 * intensity
        role = scene.role.lower()
        if "chorus" in role or "hook" in role:
            w *= 0.75  # snappier chorus cuts
        elif "outro" in role or "intro" in role:
            w *= 1.2
        w *= 1.0 / max(0.5, theme.speed)
        weights.append(max(0.35, w))

    total_w = sum(weights) or 1.0
    duration = board.duration
    usable = max(1.0, duration - 0.05)
    t = 0.0
    new_scenes: list[Scene] = []
    n = len(board.scenes)
    for i, scene in enumerate(board.scenes):
        span = usable * (weights[i] / total_w)
        end = duration if i == n - 1 else t + span
        intensity = _scene_intensity(
            Scene(**{**scene.__dict__, "start": t, "end": end}),
            energy,
        )
        motion = pick_effect(intensity, i, scene.role)
        zoom = max(0.06, min(0.4, scene.zoom * (0.85 + 0.5 * intensity)))
        new_scenes.append(
            Scene(
                index=scene.index,
                role=scene.role,
                text=scene.text,
                start=round(t, 3),
                end=round(end, 3),
                narrative=scene.narrative,
                motion=motion,
                zoom=zoom,
                image_index=scene.image_index,
            )
        )
        t = end

    return Storyboard(
        title=board.title,
        artist=board.artist,
        arc=board.arc,
        synopsis=board.synopsis,
        scenes=new_scenes,
        duration=board.duration,
    )


def expand_shots(
    board: Storyboard,
    theme: ThemeSpec,
    bpm: float | None,
    fps: int = 30,
    *,
    one_shot_per_scene: bool = False,
    energy: EnergyEnvelope | None = None,
) -> list[TimedShot]:
    """Subdivide storyboard scenes into timed visual shots."""
    target = _target_cut_length(bpm, theme.speed)
    shots: list[TimedShot] = []

    for scene in board.scenes:
        span = max(0.05, scene.end - scene.start)
        intensity = _scene_intensity(scene, energy)

        if one_shot_per_scene:
            n = 1
        else:
            # Hotter music → more subdivisions inside the scene
            local_target = target / max(0.55, 0.6 + 0.8 * intensity)
            n = max(1, round(span / local_target))
            n = min(n, max(1, int(span / 0.55)))

        piece = span / n
        for j in range(n):
            start = scene.start + j * piece
            end = scene.start + (j + 1) * piece if j < n - 1 else scene.end
            dur = max(0.05, end - start)
            frames = max(1, int(round(dur * fps)))
            caption = _caption_slice(scene.text, j, n, theme.caption_style)
            # Rotate effects within the scene on subdivisions
            motion = (
                scene.motion
                if n == 1
                else pick_effect(intensity, scene.index * 7 + j, scene.role)
            )
            shots.append(
                TimedShot(
                    scene=scene,
                    start=round(start, 3),
                    end=round(end, 3),
                    duration=round(dur, 3),
                    fps=fps,
                    frames=frames,
                    motion=motion,
                    zoom=scene.zoom,
                    image_index=scene.image_index,
                    caption=caption,
                    intensity=round(intensity, 3),
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
        return lines[piece % len(lines)]
    if total == 1 or piece == 0:
        return "\n".join(lines[:2])
    if len(lines) > 2:
        return lines[2 + (piece - 1) % max(1, len(lines) - 2)]
    return lines[piece % len(lines)]
