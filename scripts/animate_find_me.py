#!/usr/bin/env python3
"""Animate every Find Me still with Seedance I2V (local motion fallback), mux track.

Requires FAL_KEY. Seedance often rejects hero-likeness stills (content policy);
those scenes fall back to strong local camera-motion clips so the full cut completes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageOps

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
FPS = 30
WORKERS = 3


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


def _is_policy_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return (
        "content_policy" in text
        or "likeness" in text
        or "real people" in text
        or "model_moderated" in text
        or "422" in text
    )


def local_motion_clip(still: Path, dest: Path, duration: float, kind: str) -> None:
    """Fallback: turn still into timed motion MP4 when Seedance rejects likeness."""
    frames = max(1, int(round(duration * FPS)))
    with tempfile.TemporaryDirectory() as td:
        prep = Path(td) / "prep.jpg"
        img = Image.open(still).convert("RGB")
        ImageOps.fit(
            img, (int(WIDTH * 1.4), int(HEIGHT * 1.4)), method=Image.Resampling.LANCZOS
        ).save(prep, quality=95)
        if kind == "star":
            zp = (
                f"scale=9000:-1,zoompan=z='min(zoom+0.0018,1.3)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
            )
        elif kind == "supporting":
            zp = (
                f"scale=9000:-1,zoompan=z='1.12':"
                f"x='iw/2-(iw/zoom/2)+on*0.45':y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
            )
        else:
            zp = (
                f"scale=9000:-1,zoompan=z='min(1.06+on*0.0006,1.2)':"
                f"x='iw/2-(iw/zoom/2)-on*0.35':y='ih/2-(ih/zoom/2)+on*0.2':"
                f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
            )
        vf = zp + ",eq=contrast=1.05:saturation=1.1,format=yuv420p"
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
    if not fal_available():
        print(
            "FAL_KEY is required for Seedance. Add it, then rerun:\n"
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
    print(f"Animating {len(scenes)} stills → Seedance (+ local fallback) for {track.name} ({target:.1f}s)")

    CLIPS.mkdir(parents=True, exist_ok=True)
    methods: dict[int, str] = {}

    def animate_one(sc: dict) -> tuple[int, Path, str]:
        still = SCENES / sc["file"]
        if not still.exists():
            raise FileNotFoundError(f"Missing still: {still}")
        shot_dur = max(0.5, float(sc["t_end"]) - float(sc["t_start"]))
        raw = CLIPS / f"raw_{sc['id']:02d}.mp4"
        fit = CLIPS / f"fit_{sc['id']:02d}.mp4"
        if fit.exists() and fit.stat().st_size > 50_000:
            print(f"  skip {sc['id']:02d} ({sc['kind']}, {shot_dur:.1f}s)", flush=True)
            return sc["id"], fit, "existing"

        # Prefer Seedance for world/broll; still try star/supporting then fall back
        try:
            print(f"  animate {sc['id']:02d}/{len(scenes)} ({sc['kind']}, {shot_dur:.1f}s)…", flush=True)
            image_url = upload_file(still)
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
            print(f"  done {sc['id']:02d} seedance", flush=True)
            return sc["id"], fit, "seedance"
        except Exception as e:
            if not _is_policy_error(e) and not isinstance(e, FalError):
                # transient / unexpected — still try local so the cut completes
                print(f"  warn {sc['id']:02d} seedance failed ({type(e).__name__}); local fallback", flush=True)
            else:
                print(f"  policy/fallback {sc['id']:02d} ({sc['kind']}) → local motion", flush=True)
            local_motion_clip(still, fit, shot_dur, sc["kind"])
            print(f"  done {sc['id']:02d} local", flush=True)
            return sc["id"], fit, "local_fallback"

    results: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(animate_one, sc) for sc in scenes]
        for fut in as_completed(futures):
            sid, path, method = fut.result()
            results[sid] = path
            methods[sid] = method

    fitted = [results[sc["id"]] for sc in scenes]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print("Assembling full music video…")
    _concat_and_mux(fitted, track, OUT, ass_path=None)
    meta = {
        "title": plan.get("track_title") or plan.get("title") or "Find Me",
        "animated": True,
        "generator": {
            "video": "bytedance/seedance-2.0/fast/image-to-video",
            "fallback": "local_ffmpeg_motion",
        },
        "methods": {str(k): v for k, v in sorted(methods.items())},
        "seedance_count": sum(1 for v in methods.values() if v == "seedance"),
        "local_fallback_count": sum(1 for v in methods.values() if v == "local_fallback"),
        "track": str(track),
        "duration": target,
        "scenes": len(scenes),
        "output": str(OUT),
    }
    OUT.with_suffix(".plan.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(
        f"Wrote {OUT} (seedance={meta['seedance_count']}, "
        f"local_fallback={meta['local_fallback_count']}, existing={sum(1 for v in methods.values() if v=='existing')})"
    )
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
