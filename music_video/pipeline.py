"""End-to-end: inputs → theme → story → timing → render."""

from __future__ import annotations

from pathlib import Path

from .audio import probe
from .presets import UserCreativeInput
from .render import render_music_video
from .story import build_storyboard
from .theme import ThemeSpec, build_theme, load_lyrics
from .timing import TimedShot, expand_shots


def generate(
    track: str | Path,
    images: list[str | Path],
    lyrics: str,
    genre: str,
    output: str | Path,
    user: UserCreativeInput | None = None,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    keep_work: Path | None = None,
) -> tuple[Path, ThemeSpec, object, list[TimedShot]]:
    """
    Create a full-length music video.

    Returns (output_path, theme, storyboard, shots).
    """
    user = user or UserCreativeInput()
    track_path = Path(track)
    image_paths = [Path(p) for p in images]
    for p in image_paths:
        if not p.is_file():
            raise FileNotFoundError(f"Image not found: {p}")

    lyrics_text = load_lyrics(lyrics)
    audio = probe(track_path)
    if audio.duration <= 0:
        raise ValueError(f"Could not read duration from {track_path}")

    theme = build_theme(genre, lyrics_text, user)
    board = build_storyboard(
        lyrics_text,
        theme,
        audio.duration,
        user=user,
        image_count=len(image_paths),
    )
    # Explicit scene counts map 1:1 to shots (no extra BPM subdivision)
    one_shot = user.scene_count is not None or len(image_paths) == len(board.scenes)
    shots = expand_shots(
        board,
        theme,
        audio.bpm_estimate,
        fps=fps,
        one_shot_per_scene=one_shot,
    )

    out = render_music_video(
        track=track_path,
        images=image_paths,
        board=board,
        theme=theme,
        shots=shots,
        output=Path(output),
        width=width,
        height=height,
        work_dir=keep_work,
    )
    return out, theme, board, shots
