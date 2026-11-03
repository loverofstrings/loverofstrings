#!/usr/bin/env python3
"""Render Find Me storyboard: Ken Burns clips timed to scene_plan, mux track if present."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PLAN = ROOT / "examples/find_me/scene_plan.json"
SCENES = ROOT / "examples/find_me/scenes"
OUT = ROOT / "output/find_me/Find_Me_render.mp4"
WIDTH, HEIGHT = 1080, 1920
FPS = 30


def find_track() -> Path | None:
    for p in [
        ROOT / "assets/find_me/Find_Me.m4a",
        ROOT / "assets/find_me/Find_Me.mp3",
        ROOT / "assets/find_me/find_me.m4a",
        ROOT / "assets/find_me/find_me.mp3",
    ]:
        if p.exists():
            return p
    return None


def ensure_timing_bed(duration: float, dest: Path) -> Path:
    """Silent AAC bed so we can mux a full-length preview without the licensed track."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        # Refresh if duration drifted
        pass
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t",
            f"{duration:.3f}",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    return dest


def zoompan(kind: str, frames: int) -> str:
    """Gentle camera motion; starring pushes in, world drifts, supporting pans."""
    if kind == "star":
        # Slow push-in
        return (
            f"scale=8000:-1,zoompan=z='min(zoom+0.0009,1.18)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if kind == "supporting":
        return (
            f"scale=8000:-1,zoompan=z='1.08':"
            f"x='iw/2-(iw/zoom/2)+on*0.35':y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    # world — slow drift + slight zoom
    return (
        f"scale=8000:-1,zoompan=z='min(1.05+on*0.0004,1.12)':"
        f"x='iw/2-(iw/zoom/2)-on*0.2':y='ih/2-(ih/zoom/2)+on*0.15':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
    )


def prepare_still(src: Path, dest: Path) -> None:
    img = Image.open(src).convert("RGB")
    cover_w, cover_h = int(WIDTH * 1.3), int(HEIGHT * 1.3)
    ImageOps.fit(img, (cover_w, cover_h), method=Image.Resampling.LANCZOS).save(dest, quality=95)


def render_clip(still: Path, dest: Path, duration: float, kind: str) -> None:
    frames = max(1, int(round(duration * FPS)))
    with tempfile.TemporaryDirectory() as td:
        prep = Path(td) / "prep.jpg"
        prepare_still(still, prep)
        vf = zoompan(kind, frames) + ",format=yuv420p"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(prep),
                "-vf",
                vf,
                "-t",
                f"{duration:.3f}",
                "-r",
                str(FPS),
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                str(dest),
            ],
            check=True,
            capture_output=True,
        )


def main() -> int:
    plan = json.loads(PLAN.read_text())
    scenes = plan["scenes"]
    out = OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    clips_dir = out.parent / "render_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clips: list[Path] = []
    for sc in scenes:
        still = SCENES / sc["file"]
        if not still.exists():
            raise SystemExit(f"Missing still: {still}")
        dur = float(sc["t_end"]) - float(sc["t_start"])
        clip = clips_dir / f"clip_{sc['id']:02d}.mp4"
        if clip.exists() and clip.stat().st_size > 20_000:
            print(f"  skip clip {sc['id']:02d} ({dur:.1f}s)")
        else:
            print(f"  render clip {sc['id']:02d} ({sc['kind']}, {dur:.1f}s)…")
            render_clip(still, clip, dur, sc["kind"])
        clips.append(clip)

    concat_list = out.parent / "_render_concat.txt"
    with concat_list.open("w") as f:
        for c in clips:
            esc = str(c.resolve()).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")

    silent_video = out.parent / "_render_silent.mp4"
    print("Concatenating…")
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
            str(silent_video),
        ],
        check=True,
        capture_output=True,
    )

    track = find_track()
    used_track: Path
    if track:
        print(f"Muxing licensed track: {track.name}")
        used_track = track
        label = "track"
    else:
        duration = float(plan["duration_sec"])
        bed = ROOT / "assets/find_me/Find_Me_timing_bed.m4a"
        print(f"No track found — muxing silent {duration:.0f}s timing bed")
        used_track = ensure_timing_bed(duration, bed)
        label = "silent_timing_bed"

    print("Muxing audio…")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(used_track),
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
            str(out),
        ],
        check=True,
        capture_output=True,
    )

    meta = {
        "title": "Find Me",
        "render": "ken_burns_scene_plan",
        "audio": label,
        "duration_sec": plan["duration_sec"],
        "scenes": len(scenes),
        "output": str(out),
        "width": WIDTH,
        "height": HEIGHT,
    }
    out.with_suffix(".plan.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace")[-2000:]
        print(f"ffmpeg failed:\n{err}", file=sys.stderr)
        raise SystemExit(1)
