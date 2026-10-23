#!/usr/bin/env python3
"""CLI for full-length music video generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import generate
from .presets import UserCreativeInput, resolve_genre


def _parse_speed(value: str | None) -> float | None:
    if value is None:
        return None
    named = {"slow": 0.6, "medium": 1.0, "normal": 1.0, "fast": 1.5, "veryfast": 2.0}
    key = value.strip().lower()
    if key in named:
        return named[key]
    return float(value)


def _parse_palette(value: str | None) -> tuple[str, str, str] | None:
    if not value:
        return None
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("palette must be three hex colors: #111,#eee,#f00")
    return (parts[0], parts[1], parts[2])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="music-video",
        description=(
            "Create a full-length music video from a track + image(s). "
            "Lyrics and genre set theme, story, and frame speed; "
            "your flags override any of those."
        ),
    )
    p.add_argument("--track", "-t", required=True, help="Audio or video file (mp3/wav/mp4/...)")
    p.add_argument(
        "--image",
        "-i",
        action="append",
        required=True,
        dest="images",
        help="Cover/art image (repeat for multiple)",
    )
    p.add_argument(
        "--lyrics",
        "-l",
        required=True,
        help="Lyrics text, or path to a .txt/.lrc file (optional [Verse]/[Chorus] markers)",
    )
    p.add_argument("--genre", "-g", required=True, help="Music genre (pop, hip-hop, rock, ...)")
    p.add_argument("--output", "-o", default="output/music_video.mp4", help="Output mp4 path")

    # User creative overrides
    p.add_argument("--theme", help="Override visual/thematic direction in your own words")
    p.add_argument("--story", help="Override story synopsis / narrative direction")
    p.add_argument(
        "--speed",
        help="Frame/cut speed: slow|medium|fast|veryfast or a float multiplier (e.g. 1.2)",
    )
    p.add_argument("--mood", help="Mood override (e.g. 'neon loneliness')")
    p.add_argument("--motion", choices=["slow_drift", "film_pan", "pulse_zoom", "punch_in", "shake_zoom"])
    p.add_argument("--transition", choices=["fade", "cut", "soft"])
    p.add_argument("--caption-style", choices=["center", "lower-third", "kinetic"])
    p.add_argument("--palette", type=_parse_palette, help="Three hex colors: primary,secondary,accent")
    p.add_argument("--title", help="Song title (shown at start)")
    p.add_argument("--artist", help="Artist name")

    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--vertical", action="store_true", help="Shorthand for 1080x1920")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--keep-work", type=Path, help="Keep intermediate files in this directory")
    p.add_argument("--plan-only", action="store_true", help="Print theme/story/timing JSON; do not render")
    p.add_argument("--list-genres", action="store_true", help="List built-in genres and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    # Allow --list-genres without required args
    if "--list-genres" in argv:
        from .presets import GENRE_PRESETS

        for name, preset in sorted(GENRE_PRESETS.items()):
            if name == "default":
                continue
            print(f"{name:12} speed={preset.base_speed:.2f}  {preset.mood}")
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.vertical:
        args.width, args.height = 1080, 1920

    # Validate genre early with a friendly message
    resolve_genre(args.genre)

    user = UserCreativeInput(
        theme=args.theme,
        story=args.story,
        speed=_parse_speed(args.speed),
        mood=args.mood,
        palette=args.palette,
        motion=args.motion,
        transition=args.transition,
        caption_style=args.caption_style,
        title=args.title,
        artist=args.artist,
    )

    if args.plan_only:
        from .audio import probe
        from .story import build_storyboard
        from .theme import build_theme, load_lyrics
        from .timing import expand_shots

        lyrics = load_lyrics(args.lyrics)
        audio = probe(args.track)
        theme = build_theme(args.genre, lyrics, user)
        board = build_storyboard(lyrics, theme, audio.duration, user, len(args.images))
        shots = expand_shots(board, theme, audio.bpm_estimate, fps=args.fps)
        plan = {
            "duration": audio.duration,
            "bpm_estimate": audio.bpm_estimate,
            "theme": theme.__dict__,
            "synopsis": board.synopsis,
            "arc": board.arc,
            "scenes": [s.__dict__ for s in board.scenes],
            "shot_count": len(shots),
            "avg_shot_sec": round(sum(s.duration for s in shots) / max(1, len(shots)), 3),
        }
        # ThemeSpec has nested tuples — make JSON safe
        plan["theme"]["palette"] = list(theme.palette)
        print(json.dumps(plan, indent=2, default=str))
        return 0

    out, theme, board, shots = generate(
        track=args.track,
        images=args.images,
        lyrics=args.lyrics,
        genre=args.genre,
        output=args.output,
        user=user,
        width=args.width,
        height=args.height,
        fps=args.fps,
        keep_work=args.keep_work,
    )
    print(f"Wrote {out}")
    print(f"Theme: {theme.theme_summary}")
    print(f"Genre={theme.genre} speed={theme.speed:.2f} shots={len(shots)} duration={board.duration:.1f}s")
    print(f"Plan:  {Path(out).with_suffix('.plan.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
