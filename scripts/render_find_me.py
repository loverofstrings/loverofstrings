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
    """Any licensed track in assets/find_me/ (song-agnostic)."""
    track_dir = ROOT / "assets/find_me"
    for name in ("track.m4a", "track.mp3", "track.wav"):
        p = track_dir / name
        if p.exists():
            return p
    audio: list[Path] = []
    for ext in ("*.m4a", "*.mp3", "*.wav", "*.aac", "*.flac"):
        audio.extend(track_dir.glob(ext))
    audio = [p for p in audio if "timing_bed" not in p.name.lower()]
    audio.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return audio[0] if audio else None


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
    """Gentle camera motion; starring pushes in, world/b-roll drifts, supporting pans."""
    if kind == "star":
        return (
            f"scale=8000:-1,zoompan=z='min(zoom+0.0009,1.18)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if kind == "supporting":
        return (
            f"scale=8000:-1,zoompan=z='1.08':"
            f"x='iw/2-(iw/zoom/2)+on*0.35':y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if kind == "broll":
        # slower texture drift for inserts
        return (
            f"scale=8000:-1,zoompan=z='min(1.04+on*0.00025,1.1)':"
            f"x='iw/2-(iw/zoom/2)+on*0.12':y='ih/2-(ih/zoom/2)-on*0.08':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
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


def probe_duration(path: Path) -> float:
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


def scaled_scenes(plan: dict, target_duration: float) -> list[dict]:
    """Stretch/compress scene_plan cue lengths to match the dropped-in track."""
    base = float(plan.get("scaffold_duration_sec") or plan["duration_sec"]) or 1.0
    scale = target_duration / base
    out: list[dict] = []
    for sc in plan["scenes"]:
        item = dict(sc)
        item["t_start"] = round(float(sc["t_start"]) * scale, 3)
        item["t_end"] = round(float(sc["t_end"]) * scale, 3)
        out.append(item)
    # Snap last end to exact track length
    if out:
        out[-1]["t_end"] = round(target_duration, 3)
    return out


def main() -> int:
    plan = json.loads(PLAN.read_text())
    out = OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    clips_dir = out.parent / "render_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    track = find_track()
    if track:
        target_duration = probe_duration(track)
        print(f"Track: {track.name} ({target_duration:.1f}s) — scaling 48-scene plan")
        label = f"track:{track.name}"
        used_track = track
    else:
        target_duration = float(plan["duration_sec"])
        bed = ROOT / "assets/find_me/_timing_bed.m4a"
        print(f"No track in assets/find_me/ — silent {target_duration:.0f}s scaffold")
        used_track = ensure_timing_bed(target_duration, bed)
        label = "silent_timing_bed"

    scenes = scaled_scenes(plan, target_duration)
    # Namespace clips by rounded duration so a new track forces rebuilds
    tag = f"{int(round(target_duration))}s"
    tagged_dir = clips_dir / tag
    tagged_dir.mkdir(parents=True, exist_ok=True)

    clips: list[Path] = []
    for sc in scenes:
        still = SCENES / sc["file"]
        if not still.exists():
            raise SystemExit(f"Missing still: {still}")
        dur = max(0.4, float(sc["t_end"]) - float(sc["t_start"]))
        clip = tagged_dir / f"clip_{sc['id']:02d}.mp4"
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
        "plan_duration_sec": plan["duration_sec"],
        "render_duration_sec": target_duration,
        "scenes": len(scenes),
        "output": str(out),
        "width": WIDTH,
        "height": HEIGHT,
        "fal": "skipped_optional",
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
