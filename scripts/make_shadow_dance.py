#!/usr/bin/env python3
"""
Shadow Dance — full-length graphic novel music video pipeline.

Mature ink-wash graphic novel aesthetic (NOT cartoon pop-art).
No comic text / SFX overlays. Alex + Companion Android.
30 Seedance clips → FFmpeg stitch → /workspace/artifacts/

Master audio: Hold Me Control Remastered (~163.7s) for full-length 16:9 YouTube.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from music_video.seedance import (  # noqa: E402
    SeedanceError,
    download_video,
    fal_key_available,
    image_to_video,
)

PLAN_PATH = ROOT / "examples/shadow_dance/scene_plan_graphic_novel.json"
SCENES_DIR = ROOT / "examples/shadow_dance/scenes_graphic_novel"
ORDER_PATH = ROOT / "examples/shadow_dance/scenes_graphic_novel_order.txt"
CLIPS_DIR = ROOT / "output/shadow_dance_graphic_novel/clips"
ARTIFACTS_DIR = ROOT / "artifacts"
FINAL_NAME = "Shadow_Dance_GraphicNovel_Full_16x9.mp4"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
WORKERS = 2

STYLE_LOCK = (
    "mature high-end graphic novel illustration, rich ink washes, detailed hatch shading, "
    "subtle charcoal textures, expressive atmospheric lighting, thick clean ink boundary profiles, "
    "micro-detailed clothing and cyberpunk architecture, elegant elongated human proportions "
    "with significantly lengthened legs, cinematic composition. "
    "Absolutely NO comic book text, NO speech bubbles, NO sound-effect letters, "
    "NO onomatopoeia, NO words like WHOOSH POW BOOM ZOOM, NO cartoon Ben-Day pop-art flatness."
)

MOTION_LOCK = (
    "continuous non-freezing motion physics only: active rain dynamics, wind sweeping hair, "
    "writhing atmospheric shadow forms, fluid chrome reflections on metal, drifting neon dust, "
    "slow camera drift. Never a frozen still photograph."
)

ALEX = (
    "Alex, female protagonist, long wavy golden-orange hair, fair skin, sharp expressive eyes, "
    "edgy studded black motorcycle leather jacket with metallic micro-detail, "
    "elegant elongated proportions and lengthened legs"
)

ANDROID = (
    "Companion Android, very tall strikingly handsome humanoid robot, "
    "high-gloss polished chrome and brushed obsidian-gold metallic finish, "
    "majestic cinematic low-angle presence, fluid chrome surface reflections"
)


def load_plan() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def still_prompt(scene: dict) -> str:
    grade = scene.get("grade", "graphic")
    sepia = (
        " soft warm sepia-tone wash blended naturally into the graphic novel ink palette, "
        "nostalgic melancholic memory mood,"
        if grade == "sepia"
        else ""
    )
    cast = ""
    kind = scene["kind"]
    if kind == "star":
        cast = f" Feature {ALEX}."
    elif kind == "android":
        cast = f" Feature {ANDROID}."
    elif kind in ("poetic", "supporting") or "Alex" in scene["beat"] or "android" in scene["beat"].lower():
        cast = f" Feature {ALEX} and/or {ANDROID} as appropriate to the beat."
    return (
        f"Widescreen 16:9 {STYLE_LOCK}.{sepia} Scene: {scene['beat']}.{cast} "
        f"No text of any kind in the image."
    )


def motion_prompt_for(scene: dict) -> str:
    grade = scene.get("grade", "graphic")
    sepia = " warm sepia memory grade holding," if grade == "sepia" else ""
    return (
        f"{STYLE_LOCK}.{sepia} Animate: {scene['beat']}. "
        f"Characters if present: {ALEX}; {ANDROID}. {MOTION_LOCK}"
    )


def ffprobe_dur(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def fit_clip(src: Path, dest: Path, duration: float) -> None:
    """Loop/trim to exact duration; scale/crop to 1920x1080 @ 30fps."""
    src_dur = max(0.1, ffprobe_dur(src))
    loops = max(1, int(duration / src_dur) + 1)
    dest.parent.mkdir(parents=True, exist_ok=True)
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
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},fps={FPS},format=yuv420p",
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


def ffmpeg_stitch_and_mux(clips: list[Path], track: Path, output: Path) -> None:
    """
    Automated FFmpeg assembly:
    1) concat all fitted clips into silent video
    2) mux with master audio
    3) write final full-length render
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    work = output.parent / "_concat_list.txt"
    with work.open("w", encoding="utf-8") as f:
        for c in clips:
            esc = str(c.resolve()).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")

    silent = output.parent / "_silent_full.mp4"
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
            "-r",
            str(FPS),
            "-an",
            str(silent),
        ],
        check=True,
        capture_output=True,
    )

    # No ASS / no comic SFX — narrative is 100% visual
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
            "1:a:0?",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
        capture_output=True,
    )


def shot_durations(plan: dict, n: int) -> list[float]:
    total = float(plan.get("duration_sec") or 163.75)
    # Slight weight: poetic/nostalgic a bit longer; world shorter
    weights: list[float] = []
    for s in plan["scenes"][:n]:
        k = s["kind"]
        if k in ("poetic", "nostalgic"):
            weights.append(1.2)
        elif k in ("star", "android"):
            weights.append(1.1)
        else:
            weights.append(1.0)
    tw = sum(weights) or 1.0
    return [total * (w / tw) for w in weights]


def ensure_order(plan: dict) -> list[Path]:
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    images: list[Path] = []
    lines: list[str] = []
    missing: list[str] = []
    for s in plan["scenes"]:
        p = SCENES_DIR / s["file"]
        images.append(p)
        lines.append(str(p.relative_to(ROOT)))
        if not p.is_file() or p.stat().st_size < 1000:
            missing.append(s["file"])
    ORDER_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} graphic-novel stills in {SCENES_DIR}: "
            f"{', '.join(missing[:8])}{'…' if len(missing) > 8 else ''}. "
            "Generate stills first."
        )
    return images


def _animate_one(args: tuple) -> tuple[int, Path]:
    i, img, scene, dur, clips_root = args
    raw = clips_root / f"raw_{i:02d}.mp4"
    fit = clips_root / f"fit_{i:02d}.mp4"
    if fit.exists() and fit.stat().st_size > 1000:
        print(f"[{i+1}/30] reuse {fit.name}", flush=True)
        return i, fit
    prompt = motion_prompt_for(scene)
    gen_dur = max(4, min(8, int(round(max(4.0, min(dur, 8.0))))))
    print(f"[{i+1}/30] Seedance {img.name} ({gen_dur}s → {dur:.1f}s)…", flush=True)
    url = image_to_video(
        img,
        prompt,
        duration=gen_dur,
        resolution="720p",
        aspect_ratio="16:9",
        generate_audio=False,
    )
    download_video(url, raw)
    fit_clip(raw, fit, dur)
    print(f"[{i+1}/30] done {fit.name}", flush=True)
    return i, fit


def write_still_prompt_sheet(plan: dict) -> Path:
    """Helper sheet for external still generation."""
    sheet = SCENES_DIR / "STILL_PROMPTS.json"
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        {"file": s["file"], "kind": s["kind"], "grade": s.get("grade"), "prompt": still_prompt(s)}
        for s in plan["scenes"]
    ]
    sheet.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return sheet


def main() -> int:
    plan = load_plan()
    track = ROOT / plan["track"]
    if not track.is_file():
        print(f"ERROR: missing track {track}", file=sys.stderr)
        return 2

    write_still_prompt_sheet(plan)
    try:
        images = ensure_order(plan)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not fal_key_available():
        print("ERROR: FAL_KEY not set.", file=sys.stderr)
        return 2

    n = len(plan["scenes"])
    assert n == 30 and len(images) == 30
    durs = shot_durations(plan, n)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    jobs = [
        (i, images[i], plan["scenes"][i], durs[i], CLIPS_DIR) for i in range(n)
    ]

    results: dict[int, Path] = {}
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_animate_one, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            idx = futs[fut]
            try:
                i, path = fut.result()
                results[i] = path
            except SeedanceError as e:
                msg = str(e)
                errors.append(f"shot {idx}: {msg}")
                print(f"[{idx+1}/30] FAIL: {msg}", flush=True)
                if "Exhausted balance" in msg or "User is locked" in msg:
                    for f in futs:
                        f.cancel()
                    break
            except Exception as e:  # noqa: BLE001
                errors.append(f"shot {idx}: {e}")
                print(f"[{idx+1}/30] FAIL: {e}", flush=True)

    missing = [i for i in range(n) if i not in results]
    progress = {
        "done": sorted(results),
        "missing": missing,
        "errors": errors[:10],
    }
    (CLIPS_DIR.parent / "progress.json").write_text(json.dumps(progress, indent=2) + "\n")
    if missing:
        print(f"PARTIAL {len(results)}/{n}. Missing: {missing}", flush=True)
        return 4

    fitted = [results[i] for i in range(n)]
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS_DIR / FINAL_NAME
    print("FFmpeg stitch + mux master audio → artifacts…", flush=True)
    ffmpeg_stitch_and_mux(fitted, track, out)

    # Mirror under output/ for workspace convenience
    mirror = ROOT / "output/shadow_dance_graphic_novel" / FINAL_NAME
    mirror.parent.mkdir(parents=True, exist_ok=True)
    if out.resolve() != mirror.resolve():
        subprocess.run(["cp", "-f", str(out), str(mirror)], check=False)

    plan_out = {
        "title": plan["title"],
        "style": "mature_graphic_novel",
        "engine": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        "aspect": "16:9",
        "fps": FPS,
        "duration_sec": plan["duration_sec"],
        "shots": n,
        "comic_text": False,
        "output": str(out),
        "track": str(track),
    }
    out.with_suffix(".plan.json").write_text(json.dumps(plan_out, indent=2) + "\n")
    print(f"Wrote {out} ({ffprobe_dur(out):.2f}s)", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SeedanceError as exc:
        print(f"Seedance error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
