"""Render a full-length music video with ffmpeg (Ken Burns + lyrics + audio)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

from .effects import zoompan_filter
from .story import Storyboard
from .theme import ThemeSpec
from .timing import TimedShot

# Prefer expressive fonts when available
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def _pick_font() -> str | None:
    for p in _FONT_CANDIDATES:
        if Path(p).is_file():
            return p
    return None


def _hex_to_ass_bgr(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return "&H00FFFFFF"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _prepare_image(src: Path, dest: Path, width: int, height: int) -> None:
    img = Image.open(src).convert("RGB")
    # Cover-fit so zoompan has room (extra 20% canvas)
    cover_w, cover_h = int(width * 1.25), int(height * 1.25)
    fitted = ImageOps.fit(img, (cover_w, cover_h), method=Image.Resampling.LANCZOS)
    fitted.save(dest, quality=95)


def _write_ass(
    path: Path,
    shots: list[TimedShot],
    board: Storyboard,
    theme: ThemeSpec,
    width: int,
    height: int,
) -> None:
    font = "DejaVu Sans"
    primary = _hex_to_ass_bgr(theme.palette[2])
    outline = _hex_to_ass_bgr(theme.palette[0])
    fontsize = 52 if theme.caption_style == "kinetic" else 42
    if theme.caption_style == "lower-third":
        alignment = 2
        margin_v = int(height * 0.08)
    else:
        alignment = 5
        margin_v = int(height * 0.12)

    header = f"""[Script Info]
Title: {board.title}
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},{primary},&H000000FF,{outline},&H80000000,1,0,0,0,100,100,0,0,1,3,1,{alignment},60,60,{margin_v},1
Style: Title,{font},64,{primary},&H000000FF,{outline},&H80000000,1,0,0,0,100,100,0,0,1,4,2,8,60,60,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def ts(seconds: float) -> str:
        seconds = max(0.0, seconds)
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    events: list[str] = []
    title_line = board.title
    if board.artist:
        title_line = f"{board.title} — {board.artist}"
    events.append(
        f"Dialogue: 0,{ts(0)},{ts(min(4.0, board.duration * 0.08))},Title,,0,0,0,,{title_line}"
    )

    for shot in shots:
        if not shot.caption.strip():
            continue
        text = shot.caption.replace("\n", "\\N").replace("{", "(").replace("}", ")")
        events.append(
            f"Dialogue: 0,{ts(shot.start)},{ts(shot.end)},Default,,0,0,0,,{text}"
        )

    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def _render_shot(
    image: Path,
    shot: TimedShot,
    out: Path,
    width: int,
    height: int,
) -> None:
    zp = zoompan_filter(
        shot.motion,
        shot.zoom,
        shot.frames,
        width,
        height,
        intensity=getattr(shot, "intensity", 0.5),
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image),
        "-vf",
        zp,
        "-frames:v",
        str(shot.frames),
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def render_music_video(
    track: Path,
    images: list[Path],
    board: Storyboard,
    theme: ThemeSpec,
    shots: list[TimedShot],
    output: Path,
    width: int = 1920,
    height: int = 1080,
    work_dir: Path | None = None,
) -> Path:
    """Render full-length music video; returns output path."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    own_tmp = work_dir is None
    root = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="mv_"))
    root.mkdir(parents=True, exist_ok=True)

    try:
        prepared: list[Path] = []
        for i, img in enumerate(images):
            dest = root / f"img_{i:03d}.jpg"
            _prepare_image(img, dest, width, height)
            prepared.append(dest)

        clip_dir = root / "clips"
        clip_dir.mkdir(exist_ok=True)
        clip_paths: list[Path] = []

        for i, shot in enumerate(shots):
            img = prepared[shot.image_index % len(prepared)]
            clip = clip_dir / f"shot_{i:04d}.mp4"
            _render_shot(img, shot, clip, width, height)
            clip_paths.append(clip)

        concat_list = root / "concat.txt"
        with concat_list.open("w", encoding="utf-8") as f:
            for c in clip_paths:
                # ffmpeg concat demuxer needs escaped quotes
                escaped = str(c).replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

        silent = root / "silent.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(silent),
            ],
            check=True,
            capture_output=True,
        )

        ass_path = root / "lyrics.ass"
        _write_ass(ass_path, shots, board, theme, width, height)

        # Burn subtitles + mux original audio to exact duration
        # Escape ASS path for ffmpeg filter
        ass_esc = str(ass_path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        vf = f"ass='{ass_esc}'"

        # Soft fade in/out based on theme transition
        if theme.transition in ("fade", "soft"):
            fade_d = 0.8 if theme.transition == "fade" else 1.2
            vf += f",fade=t=in:st=0:d={fade_d},fade=t=out:st={max(0, board.duration - fade_d)}:d={fade_d}"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(silent),
            "-i",
            str(track),
            "-vf",
            vf,
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
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg mux failed:\n{result.stderr[-2000:]}")

        # Write sidecar plan for the user
        plan = {
            "title": board.title,
            "artist": board.artist,
            "genre": theme.genre,
            "theme": theme.theme_summary,
            "mood": theme.mood,
            "arc": board.arc,
            "synopsis": board.synopsis,
            "duration": board.duration,
            "speed": theme.speed,
            "palette": list(theme.palette),
            "scenes": [
                {
                    "role": s.role,
                    "start": s.start,
                    "end": s.end,
                    "narrative": s.narrative,
                    "text": s.text[:200],
                }
                for s in board.scenes
            ],
            "shots": len(shots),
            "output": str(output),
        }
        (output.with_suffix(".plan.json")).write_text(
            json.dumps(plan, indent=2), encoding="utf-8"
        )
        return output
    finally:
        if own_tmp and root.exists():
            shutil.rmtree(root, ignore_errors=True)
