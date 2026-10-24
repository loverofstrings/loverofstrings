"""Assemble animated scene clips into a full-length music video."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .animate import AnimationError, animate_still, fal_available, motion_prompt
from .audio import probe
from .pipeline import generate
from .presets import UserCreativeInput
from .story import build_storyboard
from .theme import build_theme, load_lyrics
from .timing import expand_shots, retime_scenes_by_music


def _ffprobe_dur(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(path),
        ],
        text=True,
    )
    return float(json.loads(out)["format"]["duration"])


def _fit_clip(src: Path, dest: Path, duration: float, width: int, height: int) -> None:
    """Loop or trim a clip to exact duration and scale to target size."""
    src_dur = max(0.1, _ffprobe_dur(src))
    # Loop enough then trim with -t
    loops = max(1, int(duration / src_dur) + 1)
    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        str(loops),
        "-i",
        str(src),
        "-t",
        f"{duration:.3f}",
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30,format=yuv420p",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _concat_and_mux(
    clips: list[Path],
    track: Path,
    output: Path,
    ass_path: Path | None,
) -> None:
    work = output.parent / "_concat_list.txt"
    with work.open("w") as f:
        for c in clips:
            esc = str(c).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")
    silent = output.parent / "_silent_anim.mp4"
    # Re-encode on concat — Seedance clips can have incompatible bitstream params for -c copy
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(work),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-an",
            str(silent),
        ],
        check=True,
        capture_output=True,
    )
    vf = None
    if ass_path and ass_path.exists():
        ass_esc = str(ass_path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        vf = f"ass='{ass_esc}'"
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(track)]
    if vf:
        cmd += ["-vf", vf]
    cmd += [
        "-map",
        "0:v:0",
        "-map",
        "1:a:0?",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def generate_animated(
    track: str | Path,
    images: list[str | Path],
    lyrics: str,
    genre: str,
    output: str | Path,
    scene_meta: list[dict],
    user: UserCreativeInput | None = None,
    width: int = 1080,
    height: int = 1920,
    clips_dir: Path | None = None,
) -> Path:
    """
    Storyboard → (existing stills) → animate each → music-timed assemble.

    ``scene_meta`` items: {kind, beat, file} aligned with images order.
    """
    if not fal_available():
        raise AnimationError(
            "FAL_API_KEY is required to animate scenes. "
            "Add it in Cloud Agent environment secrets, then rerun."
        )

    user = user or UserCreativeInput()
    user.scene_count = user.scene_count or len(images)
    track_path = Path(track)
    image_paths = [Path(p) for p in images]
    lyrics_text = load_lyrics(lyrics)
    audio = probe(track_path)
    theme = build_theme(genre, lyrics_text, user)
    board = build_storyboard(lyrics_text, theme, audio.duration, user, len(image_paths))
    board = retime_scenes_by_music(board, audio.energy, theme)
    shots = expand_shots(
        board, theme, audio.bpm_estimate, fps=30, one_shot_per_scene=True, energy=audio.energy
    )

    clips_root = Path(clips_dir or (Path(output).parent / "clips"))
    clips_root.mkdir(parents=True, exist_ok=True)
    fitted: list[Path] = []

    for i, shot in enumerate(shots):
        img = image_paths[shot.image_index % len(image_paths)]
        meta = scene_meta[i] if i < len(scene_meta) else {"kind": "world", "beat": ""}
        raw = clips_root / f"raw_{i:02d}.mp4"
        fit = clips_root / f"fit_{i:02d}.mp4"
        prompt = motion_prompt(meta.get("beat", ""), meta.get("kind", "world"), shot.motion)
        # Generate ~4–6s clip then fit to shot duration
        animate_still(img, prompt, raw, duration=min(6.0, max(3.0, shot.duration)))
        _fit_clip(raw, fit, shot.duration, width, height)
        fitted.append(fit)

    # Captions via still pipeline ASS helper: render a temp plan then reuse write
    # Simpler: mux without ASS first; captions optional
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    _concat_and_mux(fitted, track_path, out, ass_path=None)

    plan = {
        "title": board.title,
        "animated": True,
        "duration": board.duration,
        "scenes": [
            {
                "index": s.index,
                "role": s.role,
                "start": s.start,
                "end": s.end,
                "motion": shots[i].motion if i < len(shots) else s.motion,
                "kind": scene_meta[i]["kind"] if i < len(scene_meta) else None,
                "beat": scene_meta[i].get("beat") if i < len(scene_meta) else None,
            }
            for i, s in enumerate(board.scenes)
        ],
        "output": str(out),
    }
    out.with_suffix(".plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return out


def fallback_camera_motion_render(
    track: str | Path,
    images: list[str | Path],
    lyrics: str,
    genre: str,
    output: str | Path,
    user: UserCreativeInput | None = None,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    """Camera-motion assembly when FAL is unavailable (not preferred)."""
    out, _, _, _ = generate(
        track=track,
        images=images,
        lyrics=lyrics,
        genre=genre,
        output=output,
        user=user,
        width=width,
        height=height,
    )
    return out
