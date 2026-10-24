"""Build a scene storyboard from lyrics, genre arc, and user story notes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .presets import UserCreativeInput
from .theme import ThemeSpec


@dataclass
class Scene:
    index: int
    role: str  # intro | verse | prechorus | chorus | bridge | outro | instrumental
    text: str
    start: float
    end: float
    narrative: str
    motion: str
    zoom: float
    image_index: int


@dataclass
class Storyboard:
    title: str
    artist: str | None
    arc: str
    synopsis: str
    scenes: list[Scene]
    duration: float


_SECTION_MARKERS = re.compile(
    r"^\s*\[?\s*(intro|verse\s*\d*|pre[- ]?chorus|chorus|hook|bridge|outro|instrumental|break|refrain)\s*\]?\s*:?\s*$",
    re.I,
)


def _split_lyric_blocks(lyrics: str) -> list[tuple[str, str]]:
    """Return list of (section_role, text)."""
    lines = [ln.rstrip() for ln in lyrics.replace("\r\n", "\n").split("\n")]
    blocks: list[tuple[str, list[str]]] = []
    current_role = "verse"
    current: list[str] = []
    verse_n = 0

    def flush() -> None:
        nonlocal current, current_role
        text = "\n".join(ln for ln in current if ln.strip()).strip()
        if text:
            blocks.append((current_role, text.split("\n")))
        current = []

    for ln in lines:
        m = _SECTION_MARKERS.match(ln.strip())
        if m:
            flush()
            label = m.group(1).lower().replace(" ", "")
            if label.startswith("verse"):
                verse_n += 1
                current_role = f"verse{verse_n}"
            elif "pre" in label:
                current_role = "prechorus"
            elif label in ("hook", "refrain"):
                current_role = "chorus"
            else:
                current_role = label
            continue
        if not ln.strip():
            if current:
                flush()
                # blank line between unmarked verses
                if current_role.startswith("verse"):
                    verse_n += 1
                    current_role = f"verse{verse_n}"
            continue
        current.append(ln.strip())

    flush()

    if not blocks:
        # Fall back: chunk by ~2 lines
        words = [ln.strip() for ln in lines if ln.strip()]
        if not words:
            return [("instrumental", "")]
        chunk_size = max(1, min(3, len(words) // 4 or 1))
        out: list[tuple[str, str]] = []
        for i in range(0, len(words), chunk_size):
            chunk = words[i : i + chunk_size]
            role = "chorus" if i // chunk_size % 3 == 2 else f"verse{(i // chunk_size) + 1}"
            out.append((role, "\n".join(chunk)))
        return out

    return [(role, "\n".join(lines)) for role, lines in blocks]


_ARC_BEATS: dict[str, list[str]] = {
    "rise-fall": [
        "Establish the world and desire",
        "Raise the stakes",
        "Peak emotion / hook lands",
        "Aftermath and resolve",
    ],
    "tension-release": [
        "Pressure builds",
        "Confrontation",
        "Release / flex",
        "Cool down",
    ],
    "journey": [
        "Departure",
        "Crossing",
        "Revelation",
        "Return",
    ],
    "loop": [
        "Enter the groove",
        "Deepen the pattern",
        "Shift color, same pulse",
        "Fade into the loop",
    ],
    "intimacy": [
        "Close distance",
        "Confession",
        "Vulnerability",
        "Quiet hold",
    ],
    "custom": [
        "Follow the user's story",
        "Develop the beat",
        "Emotional turn",
        "Close the chapter",
    ],
}


def _role_to_beat(role: str, arc: str, index: int, total: int) -> str:
    beats = _ARC_BEATS.get(arc, _ARC_BEATS["journey"])
    # Map position along the song to an arc beat
    pos = index / max(1, total - 1)
    beat_i = min(len(beats) - 1, int(pos * len(beats)))
    base = beats[beat_i]
    clean = re.sub(r"\d+", "", role)
    return f"{base} ({clean})"


def _motion_for_role(role: str, theme: ThemeSpec) -> tuple[str, float]:
    r = role.lower()
    zoom = theme.zoom
    motion = theme.motion
    if "chorus" in r or "hook" in r:
        return motion, min(0.4, zoom * 1.35)
    if "bridge" in r:
        return "slow_drift" if motion != "slow_drift" else motion, zoom * 0.85
    if "intro" in r or "outro" in r:
        return "slow_drift", zoom * 0.7
    if "instrumental" in r:
        return motion, zoom * 1.1
    return motion, zoom


_MOTIONS = ("slow_drift", "film_pan", "pulse_zoom", "punch_in", "shake_zoom")


def _block_weight(role: str) -> float:
    if "chorus" in role or "hook" in role:
        return 1.35
    if "bridge" in role:
        return 1.1
    if "intro" in role or "outro" in role:
        return 0.85
    return 1.0


def _expand_to_scene_count(
    blocks: list[tuple[str, str]],
    target: int,
) -> list[tuple[str, str]]:
    """Split lyric blocks into exactly `target` (role, text) pieces."""
    if target < 1:
        target = 1
    if not blocks:
        return [("instrumental", "")] * target

    weights = [_block_weight(r) for r, _ in blocks]
    total_w = sum(weights) or 1.0
    # Allocate scene slots proportionally, ensure every block gets ≥1 if target >= len(blocks)
    raw = [max(1, round(target * (w / total_w))) for w in weights] if target >= len(blocks) else [
        max(1, int(target * (w / total_w))) for w in weights
    ]
    # Fix rounding to exact target
    while sum(raw) > target:
        # shrink the largest allocation above 1
        i = max(range(len(raw)), key=lambda j: (raw[j], j))
        if raw[i] <= 1:
            break
        raw[i] -= 1
    while sum(raw) < target:
        i = max(range(len(raw)), key=lambda j: (weights[j] / raw[j], j))
        raw[i] += 1

    out: list[tuple[str, str]] = []
    for (role, text), count in zip(blocks, raw):
        lines = [ln for ln in text.split("\n") if ln.strip()] or [""]
        for j in range(count):
            # Rotate lyric lines across sub-scenes
            if len(lines) == 1:
                piece = lines[0]
            else:
                # take 1–2 lines advancing through the block
                a = (j * 2) % len(lines)
                piece = "\n".join(lines[a : a + 2]) or lines[j % len(lines)]
            out.append((role, piece))
    return out[:target]


def build_storyboard(
    lyrics: str,
    theme: ThemeSpec,
    duration: float,
    user: UserCreativeInput | None = None,
    image_count: int = 1,
) -> Storyboard:
    user = user or UserCreativeInput()
    blocks = _split_lyric_blocks(lyrics)
    image_count = max(1, image_count)

    target = user.scene_count
    if target is None and image_count > len(blocks):
        # Prefer one scene per starring image when many stills are provided
        target = image_count
    if target is not None:
        blocks = _expand_to_scene_count(blocks, int(target))

    n = len(blocks)
    weights = [_block_weight(role) for role, _ in blocks]
    total_w = sum(weights) or 1.0
    usable = max(1.0, duration - 0.05)

    scenes: list[Scene] = []
    t = 0.0
    synopsis_parts: list[str] = []
    if user.story:
        synopsis_parts.append(user.story.strip())
    synopsis_parts.append(theme.theme_summary)

    for i, (role, text) in enumerate(blocks):
        span = usable * (weights[i] / total_w)
        end = duration if i == n - 1 else t + span
        motion, zoom = _motion_for_role(role, theme)
        # Vary motion across a long scene list so the cut feels intentional
        if user.scene_count or image_count > 4:
            motion = _MOTIONS[i % len(_MOTIONS)] if not user.motion else motion
            if "chorus" in role:
                zoom = min(0.4, zoom * 1.2)
        narrative = _role_to_beat(role, theme.story_arc, i, n)
        if user.story and i == 0:
            narrative = f"{user.story.strip()} — {narrative}"
        scenes.append(
            Scene(
                index=i,
                role=role,
                text=text,
                start=round(t, 3),
                end=round(end, 3),
                narrative=narrative,
                motion=motion,
                zoom=zoom,
                image_index=i % image_count,
            )
        )
        t = end

    title = user.title or "Untitled"
    return Storyboard(
        title=title,
        artist=user.artist,
        arc=theme.story_arc,
        synopsis=" ".join(synopsis_parts),
        scenes=scenes,
        duration=duration,
    )
