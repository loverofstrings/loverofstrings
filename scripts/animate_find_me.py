#!/usr/bin/env python3
"""Animate every Find Me still with Seedance I2V, then mux to the dropped-in track.

Requires FAL_KEY (or FAL_API_KEY). Uses assets/find_me/track.* for duration + audio.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from music_video.assemble_animated import _concat_and_mux, _fit_clip  # noqa: E402
from music_video.fal_gen import (  # noqa: E402
    FalError,
    animate_image,
    fal_available,
    upload_file,
)

PLAN = ROOT / "examples/find_me/scene_plan.json"
SCENES = ROOT / "examples/find_me/scenes"
OUT = ROOT / "output/find_me/Find_Me_music_video.mp4"
CLIPS = ROOT / "output/find_me/seedance_clips"
WIDTH, HEIGHT = 1080, 1920


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


def motion_prompt(kind: str, beat: str) -> str:
    base = (
        "Animate this comic-book digital illustration into living motion. "
        "Keep the same composition, characters, and art style. "
        "Cinematic camera, subtle neon pulse, rain/steam parallax where present. "
        "No new text, no watermark, no morphing faces into other people."
    )
    if kind == "star":
        role = "Hero is the focus; natural hair, breath, rain, and light motion."
    elif kind == "supporting":
        role = "Atmosphere leads; keep any figure secondary and stable."
    elif kind == "broll":
        role = "B-roll texture plate: animate light, rain, steam, energy — no people."
    else:
        role = "Environment only: animate rain, gears, neon glow, parallax depth."
    return f"{base} {role} Scene: {beat}"


def main() -> int:
    if not fal_available():
        print(
            "FAL_KEY is required to turn stills into Seedance videos.\n"
            "Add FAL_KEY to Cloud Agent secrets (https://fal.ai/dashboard/keys), then rerun:\n"
            "  python3 scripts/animate_find_me.py",
            file=sys.stderr,
        )
        return 2

    plan = json.loads(PLAN.read_text())
    track = find_track()
    if track is None:
        print("Missing track — place audio at assets/find_me/track.mp3", file=sys.stderr)
        return 2

    target = probe_duration(track)
    scenes = scaled_scenes(plan, target)
    print(f"Animating {len(scenes)} stills → Seedance I2V for {track.name} ({target:.1f}s)")

    CLIPS.mkdir(parents=True, exist_ok=True)
    fitted: list[Path] = []
    for i, sc in enumerate(scenes):
        still = SCENES / sc["file"]
        if not still.exists():
            raise SystemExit(f"Missing still: {still}")
        shot_dur = max(0.5, float(sc["t_end"]) - float(sc["t_start"]))
        raw = CLIPS / f"raw_{sc['id']:02d}.mp4"
        fit = CLIPS / f"fit_{sc['id']:02d}.mp4"
        if fit.exists() and fit.stat().st_size > 50_000:
            print(f"  skip {sc['id']:02d} ({sc['kind']}, {shot_dur:.1f}s)")
            fitted.append(fit)
            continue
        print(f"  animate {sc['id']:02d}/{len(scenes)} ({sc['kind']}, {shot_dur:.1f}s)…")
        image_url = upload_file(still)
        # Seedance accepts 4–15s; generate enough motion then fit to shot length
        seed_dur = int(round(min(8.0, max(4.0, shot_dur))))
        animate_image(
            motion_prompt(sc["kind"], sc["beat"]),
            raw,
            image_url=image_url,
            duration=seed_dur,
            resolution="720p",
            aspect_ratio="9:16",
            generate_audio=False,
            fast=True,
        )
        _fit_clip(raw, fit, shot_dur, WIDTH, HEIGHT)
        fitted.append(fit)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("Assembling full music video…")
    _concat_and_mux(fitted, track, OUT, ass_path=None)
    meta = {
        "title": plan.get("track_title") or plan.get("title") or "Find Me",
        "animated": True,
        "generator": {"video": "bytedance/seedance-2.0/fast/image-to-video"},
        "track": str(track),
        "duration": target,
        "scenes": len(scenes),
        "output": str(OUT),
    }
    OUT.with_suffix(".plan.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote animated video: {OUT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FalError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace")[-2000:]
        print(f"ffmpeg failed:\n{err}", file=sys.stderr)
        raise SystemExit(1)
