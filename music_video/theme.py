"""Derive visual theme from genre, lyrics, and optional user overrides."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .presets import GenrePreset, UserCreativeInput, resolve_genre


# Lightweight lyric keyword → mood hints (no ML dependency)
_MOOD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "love": ("love", "heart", "kiss", "baby", "darling", "romance", "hold me"),
    "heartbreak": ("cry", "tears", "gone", "leave", "lonely", "broken", "miss you", "goodbye"),
    "party": ("dance", "night", "club", "party", "drink", "friday", "wild"),
    "empowerment": ("strong", "rise", "fight", "power", "free", "queen", "king", "alive"),
    "reflection": ("remember", "dream", "time", "think", "wonder", "memory", "past"),
    "faith": ("pray", "god", "heaven", "soul", "bless", "grace", "light"),
    "street": ("street", "city", "grind", "money", "hustle", "block", "ride"),
    "nature": ("sky", "ocean", "river", "sun", "moon", "stars", "rain", "wind"),
}


@dataclass
class ThemeSpec:
    genre: str
    mood: str
    palette: tuple[str, str, str]
    motion: str
    speed: float
    transition: str
    font_style: str
    story_arc: str
    zoom: float
    caption_style: str
    theme_summary: str
    lyric_moods: list[str]
    user_theme: str | None = None


def _detect_lyric_moods(lyrics: str) -> list[str]:
    text = lyrics.lower()
    found: list[str] = []
    for mood, words in _MOOD_KEYWORDS.items():
        if any(w in text for w in words):
            found.append(mood)
    return found or ["reflection"]


def _blend_mood(preset: GenrePreset, lyric_moods: list[str], user: UserCreativeInput) -> str:
    if user.mood:
        return user.mood
    if user.theme:
        return f"{user.theme}; {preset.mood}"
    primary = lyric_moods[0] if lyric_moods else "reflection"
    return f"{preset.mood}; lyric focus: {', '.join(lyric_moods[:3])} ({primary})"


def build_theme(
    genre: str,
    lyrics: str,
    user: UserCreativeInput | None = None,
) -> ThemeSpec:
    user = user or UserCreativeInput()
    preset = resolve_genre(genre)
    lyric_moods = _detect_lyric_moods(lyrics)

    speed = preset.base_speed
    if user.speed is not None:
        speed = max(0.25, min(3.0, float(user.speed)))

    palette = user.palette or preset.palette
    motion = user.motion or preset.motion
    transition = user.transition or preset.transition
    caption_style = user.caption_style or preset.caption_style
    mood = _blend_mood(preset, lyric_moods, user)

    theme_summary = user.theme or (
        f"A {preset.name} music video with a {lyric_moods[0]} tone — "
        f"{preset.mood}."
    )

    # Slight zoom nudge from lyric intensity
    intensity = min(1.0, len(lyric_moods) / 4.0)
    zoom = preset.default_zoom * (0.9 + 0.2 * intensity)

    return ThemeSpec(
        genre=preset.name,
        mood=mood,
        palette=palette,
        motion=motion,
        speed=speed,
        transition=transition,
        font_style=preset.font_style,
        story_arc=preset.story_arc if not user.story else "custom",
        zoom=zoom,
        caption_style=caption_style,
        theme_summary=theme_summary,
        lyric_moods=lyric_moods,
        user_theme=user.theme,
    )


def load_lyrics(path_or_text: str) -> str:
    """Load lyrics from a file path, or treat the string as inline lyrics."""
    stripped = path_or_text.strip()
    if "\n" not in stripped and re.search(r"\.(txt|lrc|md)$", stripped, re.I):
        with open(stripped, encoding="utf-8") as f:
            return f.read()
    try:
        # Heuristic: short path-looking strings that exist as files
        from pathlib import Path

        p = Path(stripped)
        if p.is_file() and p.stat().st_size < 500_000:
            return p.read_text(encoding="utf-8")
    except OSError:
        pass
    return path_or_text
