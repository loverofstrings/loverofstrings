#!/usr/bin/env python3
"""Turn every Find Me still into a motion video clip (local ffmpeg), then mux track.

This is the no-FAL path: each still becomes a real timed MP4 with stronger camera
motion + rain/energy overlays by scene kind — not a static slideshow.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "examples/find_me/scene_plan.json"
SCENES = ROOT / "examples/find_me/scenes"
OUT = ROOT / "output/find_me/Find_Me_music_video.mp4"
CLIPS = ROOT / "output/find_me/motion_clips"
WIDTH, HEIGHT = 1080, 1920
FPS = 30


def find_track() -> Path | None:
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


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        text=True,
    )
    return float(json.loads(out)["format"]["duration"])


def scaled_scenes(plan: dict, target_duration: float) -> list[dict]:
    base = float(plan.get("scaffold_duration_sec") or plan["duration_sec"]) or 1.0
    scale = target_duration / base
    out: list[dict] = []
    for sc in plan["scenes"]:
        item = dict(sc)
        item["t_start"] = round(float(sc["t_start"]) * scale, 3)
        item["t_end"] = round(float(sc["t_end"]) * scale, 3)
        out.append(item)
    if out:
        out[-1]["t_end"] = round(target_duration, 3)
    return out


def motion_filter(kind: str, frames: int, master_frame: int) -> str:
    """Aggressive still→video motion so frames read as clips, not photos."""
    # Larger virtual canvas for zoompan travel
    base = f"scale=9000:-1"
    if kind == "star":
        # Strong push-in + slight vertical drift
        zp = (
            f"zoompan=z='min(zoom+0.0018,1.32)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-on*0.15':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    elif kind == "supporting":
        zp = (
            f"zoompan=z='1.15+0.0004*sin(on/18)':"
            f"x='iw/2-(iw/zoom/2)+on*0.55':y='ih/2-(ih/zoom/2)+on*0.1':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    elif kind == "broll":
        # Continuous drift + slow pulse zoom for texture plates
        zp = (
            f"zoompan=z='1.08+0.04*sin(on/25)':"
            f"x='iw/2-(iw/zoom/2)+on*0.4':y='ih/2-(ih/zoom/2)-on*0.25':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    else:
        # world — diagonal drift, chase frames get faster feel via master_frame
        speed = 0.55 if master_frame in {4, 5, 8} else 0.28
        zp = (
            f"zoompan=z='min(1.06+on*0.0007,1.22)':"
            f"x='iw/2-(iw/zoom/2)-on*{speed}':y='ih/2-(ih/zoom/2)+on*{speed*0.6}':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )

    parts = [base, zp]

    # Rain streaks for rain-forward frames
    if master_frame in {1, 2, 5} or kind == "broll" and master_frame == 1:
        parts.append(
            "geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)',"
            # lighten diagonal rain via noise blend
            "noise=alls=8:allf=t+u"
        )
    elif master_frame in {3, 7, 8}:
        # neon energy — slight saturation pulse via eq
        parts.append("eq=saturation=1.15:contrast=1.05")
    else:
        parts.append("eq=contrast=1.04:saturation=1.08")

    # Micro shake on kinetic frames
    if master_frame in {5, 8} and kind in {"star", "world"}:
        parts.append(
            "crop=w=in_w-12:h=in_h-12:"
            "x='6+3*sin(n/3)':y='6+2*cos(n/4)',"
            f"scale={WIDTH}:{HEIGHT}"
        )

    parts.append("format=yuv420p")
    return ",".join(parts)


def prepare_still(src: Path, dest: Path) -> None:
    img = Image.open(src).convert("RGB")
    cover_w, cover_h = int(WIDTH * 1.45), int(HEIGHT * 1.45)
    ImageOps.fit(img, (cover_w, cover_h), method=Image.Resampling.LANCZOS).save(dest, quality=95)


def render_clip(still: Path, dest: Path, duration: float, kind: str, master_frame: int) -> None:
    frames = max(1, int(round(duration * FPS)))
    with tempfile.TemporaryDirectory() as td:
        prep = Path(td) / "prep.jpg"
        prepare_still(still, prep)
        vf = motion_filter(kind, frames, master_frame)
        r = subprocess.run(
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
            capture_output=True,
        )
        if r.returncode != 0:
            # Fallback: simpler zoompan if complex filter fails
            simple = (
                f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.25)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p"
            )
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(prep),
                    "-vf",
                    simple,
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
    track = find_track()
    if track is None:
        print("Missing assets/find_me/track.mp3", file=sys.stderr)
        return 2
    target = probe_duration(track)
    scenes = scaled_scenes(plan, target)
    print(f"Still→video for {len(scenes)} scenes @ {target:.1f}s ({track.name})")

    tag = f"motion_{int(round(target))}s"
    clips_dir = CLIPS / tag
    clips_dir.mkdir(parents=True, exist_ok=True)

    clips: list[Path] = []
    for sc in scenes:
        still = SCENES / sc["file"]
        if not still.exists():
            raise SystemExit(f"Missing still {still}")
        dur = max(0.5, float(sc["t_end"]) - float(sc["t_start"]))
        dest = clips_dir / f"clip_{sc['id']:02d}.mp4"
        if dest.exists() and dest.stat().st_size > 20_000:
            print(f"  skip {sc['id']:02d}")
        else:
            print(f"  video {sc['id']:02d}/{len(scenes)} ({sc['kind']}, {dur:.1f}s)…")
            render_clip(still, dest, dur, sc["kind"], int(sc.get("master_frame", 1)))
        clips.append(dest)

    concat = OUT.parent / "_motion_concat.txt"
    with concat.open("w") as f:
        for c in clips:
            esc = str(c.resolve()).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")

    silent = OUT.parent / "_motion_silent.mp4"
    print("Concatenating…")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent)],
        check=True,
        capture_output=True,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("Muxing track…")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent),
            "-i",
            str(track),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
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
            str(OUT),
        ],
        check=True,
        capture_output=True,
    )
    meta = {
        "title": plan.get("track_title") or "Find Me",
        "animated": True,
        "method": "local_still_to_video_ffmpeg",
        "track": str(track),
        "duration": target,
        "scenes": len(scenes),
        "output": str(OUT),
        "note": "FAL/Seedance unavailable; each still converted to timed motion MP4 locally.",
    }
    OUT.with_suffix(".plan.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace")[-2000:]
        print(f"ffmpeg failed:\n{err}", file=sys.stderr)
        raise SystemExit(1)
