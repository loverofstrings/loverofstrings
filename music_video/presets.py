"""Genre-driven visual and motion presets for music videos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GenrePreset:
    name: str
    mood: str
    palette: tuple[str, str, str]  # primary, secondary, accent (hex)
    motion: str  # kenburns style key
    base_speed: float  # 1.0 = normal; higher = faster cuts / stronger zoom
    transition: str  # fade | cut | soft
    font_style: str  # bold | light | dramatic | handwritten
    story_arc: str  # rise-fall | tension-release | journey | loop | intimacy
    default_zoom: float  # zoom amplitude (0.05–0.35)
    caption_style: str  # center | lower-third | kinetic


GENRE_PRESETS: dict[str, GenrePreset] = {
    "pop": GenrePreset(
        name="pop",
        mood="bright, catchy, energetic",
        palette=("#FF6B9D", "#FFE66D", "#4ECDC4"),
        motion="pulse_zoom",
        base_speed=1.25,
        transition="cut",
        font_style="bold",
        story_arc="rise-fall",
        default_zoom=0.18,
        caption_style="center",
    ),
    "hip-hop": GenrePreset(
        name="hip-hop",
        mood="confident, rhythmic, urban",
        palette=("#111111", "#F5F5F5", "#C9A227"),
        motion="punch_in",
        base_speed=1.35,
        transition="cut",
        font_style="bold",
        story_arc="tension-release",
        default_zoom=0.22,
        caption_style="kinetic",
    ),
    "rap": GenrePreset(
        name="rap",
        mood="assertive, sharp, street",
        palette=("#0D0D0D", "#E8E8E8", "#E63946"),
        motion="punch_in",
        base_speed=1.45,
        transition="cut",
        font_style="bold",
        story_arc="tension-release",
        default_zoom=0.25,
        caption_style="kinetic",
    ),
    "r&b": GenrePreset(
        name="r&b",
        mood="smooth, sensual, warm",
        palette=("#2B1B17", "#D4A574", "#8B4513"),
        motion="slow_drift",
        base_speed=0.75,
        transition="soft",
        font_style="light",
        story_arc="intimacy",
        default_zoom=0.12,
        caption_style="lower-third",
    ),
    "soul": GenrePreset(
        name="soul",
        mood="warm, emotional, classic",
        palette=("#3D2314", "#E8C39E", "#B85C38"),
        motion="slow_drift",
        base_speed=0.7,
        transition="soft",
        font_style="dramatic",
        story_arc="intimacy",
        default_zoom=0.1,
        caption_style="lower-third",
    ),
    "rock": GenrePreset(
        name="rock",
        mood="raw, driving, rebellious",
        palette=("#1A1A1A", "#C0C0C0", "#FF4500"),
        motion="shake_zoom",
        base_speed=1.3,
        transition="cut",
        font_style="bold",
        story_arc="rise-fall",
        default_zoom=0.2,
        caption_style="center",
    ),
    "indie": GenrePreset(
        name="indie",
        mood="intimate, nostalgic, textured",
        palette=("#2C3E50", "#ECF0F1", "#E74C3C"),
        motion="film_pan",
        base_speed=0.85,
        transition="fade",
        font_style="handwritten",
        story_arc="journey",
        default_zoom=0.14,
        caption_style="lower-third",
    ),
    "folk": GenrePreset(
        name="folk",
        mood="storytelling, earthy, gentle",
        palette=("#3E2723", "#FFF8E7", "#8D6E63"),
        motion="film_pan",
        base_speed=0.65,
        transition="fade",
        font_style="handwritten",
        story_arc="journey",
        default_zoom=0.08,
        caption_style="lower-third",
    ),
    "country": GenrePreset(
        name="country",
        mood="open-road, honest, warm",
        palette=("#5D4037", "#FFF3E0", "#D84315"),
        motion="film_pan",
        base_speed=0.8,
        transition="fade",
        font_style="dramatic",
        story_arc="journey",
        default_zoom=0.1,
        caption_style="lower-third",
    ),
    "electronic": GenrePreset(
        name="electronic",
        mood="futuristic, pulsing, neon",
        palette=("#0A0A12", "#00F5FF", "#FF00AA"),
        motion="pulse_zoom",
        base_speed=1.4,
        transition="cut",
        font_style="bold",
        story_arc="loop",
        default_zoom=0.28,
        caption_style="kinetic",
    ),
    "edm": GenrePreset(
        name="edm",
        mood="euphoric, high-energy, festival",
        palette=("#050510", "#7B2FFF", "#00FFCC"),
        motion="pulse_zoom",
        base_speed=1.55,
        transition="cut",
        font_style="bold",
        story_arc="rise-fall",
        default_zoom=0.32,
        caption_style="kinetic",
    ),
    "techno": GenrePreset(
        name="techno",
        mood="hypnotic, industrial, dark",
        palette=("#0B0B0B", "#AAAAAA", "#39FF14"),
        motion="punch_in",
        base_speed=1.5,
        transition="cut",
        font_style="bold",
        story_arc="loop",
        default_zoom=0.3,
        caption_style="center",
    ),
    "ambient": GenrePreset(
        name="ambient",
        mood="spacious, meditative, slow",
        palette=("#0D1B2A", "#778DA9", "#E0E1DD"),
        motion="slow_drift",
        base_speed=0.45,
        transition="soft",
        font_style="light",
        story_arc="loop",
        default_zoom=0.06,
        caption_style="lower-third",
    ),
    "jazz": GenrePreset(
        name="jazz",
        mood="cool, improvisational, late-night",
        palette=("#1B1B2F", "#EAEAEA", "#F4A261"),
        motion="slow_drift",
        base_speed=0.7,
        transition="soft",
        font_style="light",
        story_arc="intimacy",
        default_zoom=0.09,
        caption_style="lower-third",
    ),
    "blues": GenrePreset(
        name="blues",
        mood="soulful, melancholic, deep",
        palette=("#1A237E", "#BBDEFB", "#FF6F00"),
        motion="slow_drift",
        base_speed=0.65,
        transition="fade",
        font_style="dramatic",
        story_arc="intimacy",
        default_zoom=0.1,
        caption_style="lower-third",
    ),
    "metal": GenrePreset(
        name="metal",
        mood="aggressive, dark, intense",
        palette=("#000000", "#8B0000", "#C0C0C0"),
        motion="shake_zoom",
        base_speed=1.5,
        transition="cut",
        font_style="bold",
        story_arc="tension-release",
        default_zoom=0.28,
        caption_style="center",
    ),
    "punk": GenrePreset(
        name="punk",
        mood="chaotic, loud, DIY",
        palette=("#000000", "#FFFF00", "#FF0000"),
        motion="shake_zoom",
        base_speed=1.6,
        transition="cut",
        font_style="bold",
        story_arc="tension-release",
        default_zoom=0.3,
        caption_style="kinetic",
    ),
    "lofi": GenrePreset(
        name="lofi",
        mood="chill, nostalgic, soft focus",
        palette=("#2D3436", "#DFE6E9", "#FD79A8"),
        motion="film_pan",
        base_speed=0.55,
        transition="soft",
        font_style="handwritten",
        story_arc="loop",
        default_zoom=0.07,
        caption_style="lower-third",
    ),
    "gospel": GenrePreset(
        name="gospel",
        mood="uplifting, spiritual, radiant",
        palette=("#1A237E", "#FFFDE7", "#FFD700"),
        motion="slow_drift",
        base_speed=0.8,
        transition="fade",
        font_style="dramatic",
        story_arc="rise-fall",
        default_zoom=0.12,
        caption_style="center",
    ),
    "latin": GenrePreset(
        name="latin",
        mood="vibrant, rhythmic, passionate",
        palette=("#C62828", "#FFEB3B", "#2E7D32"),
        motion="pulse_zoom",
        base_speed=1.2,
        transition="cut",
        font_style="bold",
        story_arc="rise-fall",
        default_zoom=0.2,
        caption_style="center",
    ),
    "reggae": GenrePreset(
        name="reggae",
        mood="laid-back, sunny, groove",
        palette=("#1B5E20", "#FDD835", "#C62828"),
        motion="film_pan",
        base_speed=0.85,
        transition="soft",
        font_style="bold",
        story_arc="loop",
        default_zoom=0.12,
        caption_style="center",
    ),
    "classical": GenrePreset(
        name="classical",
        mood="elegant, dramatic, timeless",
        palette=("#1C1C1C", "#F5F5DC", "#8B7355"),
        motion="slow_drift",
        base_speed=0.5,
        transition="fade",
        font_style="dramatic",
        story_arc="journey",
        default_zoom=0.08,
        caption_style="lower-third",
    ),
    "default": GenrePreset(
        name="default",
        mood="cinematic, balanced",
        palette=("#121212", "#F0F0F0", "#4A90A4"),
        motion="film_pan",
        base_speed=1.0,
        transition="fade",
        font_style="bold",
        story_arc="journey",
        default_zoom=0.15,
        caption_style="center",
    ),
}


# Aliases map common user spellings → canonical preset keys
GENRE_ALIASES: dict[str, str] = {
    "hiphop": "hip-hop",
    "hip hop": "hip-hop",
    "rnb": "r&b",
    "r and b": "r&b",
    "r&b / soul": "r&b",
    "electro": "electronic",
    "electronica": "electronic",
    "dance": "edm",
    "house": "edm",
    "trance": "edm",
    "lo-fi": "lofi",
    "lo fi": "lofi",
    "alt": "indie",
    "alternative": "indie",
    "singer-songwriter": "folk",
    "afrobeats": "latin",
    "reggaeton": "latin",
    "k-pop": "pop",
    "kpop": "pop",
    "trap": "hip-hop",
    "drill": "hip-hop",
    "heavy metal": "metal",
    "death metal": "metal",
    "orchestra": "classical",
}


def resolve_genre(genre: str) -> GenrePreset:
    key = (genre or "default").strip().lower()
    key = GENRE_ALIASES.get(key, key)
    return GENRE_PRESETS.get(key, GENRE_PRESETS["default"])


@dataclass
class UserCreativeInput:
    """Optional overrides supplied by the user."""

    theme: str | None = None
    story: str | None = None
    speed: float | None = None  # multiplier on genre base_speed
    mood: str | None = None
    palette: tuple[str, str, str] | None = None
    motion: str | None = None
    transition: str | None = None
    caption_style: str | None = None
    title: str | None = None
    artist: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
