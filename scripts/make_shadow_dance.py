#!/usr/bin/env python3
"""
The Golden Android's Mirage — combined graphic-novel + Magnific pop-art
full-length 16:9 music video (32 scenes, B-roll throughout).

- Sophisticated ink washes / cross-hatch + thick pop-art ink boundaries
- Anamorphic 35mm cinematic feel
- Alex + long-haired love interest → chrome/obsidian-gold companion android
- Evil robot stalker (corruption when Alex's back is turned)
- No comic text / SFX overlays
- Seedance continuous motion → FFmpeg stitch → /workspace/artifacts/
"""
from __future__ import annotations

import json
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

PLAN_PATH = ROOT / "examples/shadow_dance/scene_plan_golden_android.json"
SCENES_DIR = ROOT / "examples/shadow_dance/scenes_golden_android"
ORDER_PATH = ROOT / "examples/shadow_dance/scenes_golden_android_order.txt"
CLIPS_DIR = ROOT / "output/golden_android/clips"
ARTIFACTS_DIR = ROOT / "artifacts"
FINAL_NAME = "Golden_Android_Mirage_Combined_16x9.mp4"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
WORKERS = 2
SCENE_COUNT = 32

STYLE_LOCK = (
    "COMBINED sophisticated graphic novel AND Magnific modern pop-art: "
    "rich ink washes, detailed cross-hatch shading, subtle charcoal textures, "
    "thick clean ink boundary profiles, saturated cyan magenta bright-yellow accents, "
    "subtle Ben-Day/halftone on skin and sky, expressive atmospheric lighting, "
    "anamorphic 35mm cinematic widescreen look with gentle horizontal lens character, "
    "elegant elongated human proportions with significantly lengthened legs, "
    "micro-detailed clothing and utopian cyberpunk architecture. "
    "Absolutely NO comic book text, NO speech bubbles, NO sound-effect letters, "
    "NO onomatopoeia (no WHOOSH POW BOOM ZOOM)."
)

MOTION_LOCK = (
    "continuous non-freezing 30fps motion physics: active rain, wind in hair, "
    "hover vehicles gliding, neon dust drifting, chrome reflections fluid, "
    "shadow/robot corruption writhing when present, camera tracking or dolly drift. "
    "Never a frozen still photograph."
)

ALEX = (
    "Hero/Alex fierce female protagonist with long voluminous wavy golden-orange hair, "
    "studded black motorcycle leather jacket, sharp expressive eyes, "
    "elegant elongated proportions and lengthened legs"
)
LOVE = (
    "tall incredibly handsome pretty man with long flowing hair, charming grin, "
    "elegant body proportions, stylized buckled combat boots"
)
EVIL = (
    "menacing evil humanoid robot / jagged mechanical shell with terrifying grin, "
    "dark metallic energy"
)
ANDROID = (
    "strikingly handsome very tall humanoid companion android with high-gloss polished "
    "chrome and brushed obsidian-gold metallic finish, majestic low-angle presence"
)
CROWD = "massive crowd of many distinct utopian socialites and elite lounge characters"


def load_plan() -> dict:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def still_prompt(scene: dict) -> str:
    grade = ""
    if scene["kind"] == "nostalgic" or "sepia" in scene["beat"].lower():
        grade = (
            " Soft warm sepia-tone wash blended naturally into the combined "
            "graphic-novel/pop-art palette for nostalgic memory mood."
        )
    return (
        f"Widescreen 16:9 anamorphic 35mm cinematic panel. {STYLE_LOCK}.{grade} "
        f"Scene ({scene['kind']}): {scene['beat']}. "
        f"Cast vocabulary as needed: {ALEX}; {LOVE}; {EVIL}; {ANDROID}; {CROWD}. "
        f"Populate B-roll depth with background characters when the beat implies a social space. "
        f"No text of any kind in the image. Filename intent: scene {scene['id']:02d}."
    )


def motion_prompt_for(scene: dict) -> str:
    sepia = ""
    if scene["kind"] == "nostalgic" or "sepia" in scene["beat"].lower():
        sepia = " warm sepia memory grade holding,"
    return (
        f"{STYLE_LOCK}.{sepia} Animate continuously: {scene['beat']}. "
        f"Characters: {ALEX}; {LOVE}; {EVIL}; {ANDROID}; {CROWD}. {MOTION_LOCK}"
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
    output.parent.mkdir(parents=True, exist_ok=True)
    work_dir = ROOT / "output/golden_android"
    work_dir.mkdir(parents=True, exist_ok=True)
    work = work_dir / "_concat_list.txt"
    with work.open("w", encoding="utf-8") as f:
        for c in clips:
            esc = str(c.resolve()).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")

    silent = work_dir / "_silent_full.mp4"
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

    # No ASS / no comic SFX — 100% visual narrative
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


def shot_durations(plan: dict) -> list[float]:
    scenes = plan["scenes"]
    durs = []
    for s in scenes:
        d = float(s["t1"]) - float(s["t0"])
        durs.append(max(0.5, d))
    # Nudge to exact track length
    target = float(plan["duration_sec"])
    scale = target / sum(durs)
    return [d * scale for d in durs]


def scene_filename(scene: dict) -> str:
    return f"ga{scene['id']:02d}_{scene['kind']}.jpg"


def ensure_stills(plan: dict) -> list[Path]:
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    images: list[Path] = []
    lines: list[str] = []
    missing: list[str] = []
    prompts = []
    for s in plan["scenes"]:
        fn = scene_filename(s)
        s["file"] = fn
        p = SCENES_DIR / fn
        images.append(p)
        lines.append(str(p.relative_to(ROOT)))
        prompts.append({"id": s["id"], "file": fn, "kind": s["kind"], "prompt": still_prompt(s)})
        if not p.is_file() or p.stat().st_size < 1000:
            missing.append(fn)
    ORDER_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (SCENES_DIR / "STILL_PROMPTS.json").write_text(json.dumps(prompts, indent=2) + "\n")
    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} stills in {SCENES_DIR}: {', '.join(missing[:10])}"
            + ("…" if len(missing) > 10 else "")
        )
    return images


def _animate_one(args: tuple) -> tuple[int, Path]:
    i, img, scene, dur, clips_root = args
    raw = clips_root / f"raw_{i:02d}.mp4"
    fit = clips_root / f"fit_{i:02d}.mp4"
    if fit.exists() and fit.stat().st_size > 1000:
        print(f"[{i+1}/{SCENE_COUNT}] reuse {fit.name}", flush=True)
        return i, fit
    prompt = motion_prompt_for(scene)
    gen_dur = max(4, min(8, int(round(max(4.0, min(dur, 8.0))))))
    print(
        f"[{i+1}/{SCENE_COUNT}] Seedance {img.name} ({gen_dur}s → {dur:.1f}s) [{scene['kind']}]…",
        flush=True,
    )
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
    print(f"[{i+1}/{SCENE_COUNT}] done {fit.name}", flush=True)
    return i, fit


def main() -> int:
    plan = load_plan()
    assert len(plan["scenes"]) == SCENE_COUNT, len(plan["scenes"])
    track = ROOT / plan["track"]
    if not track.is_file():
        print(f"ERROR: missing track {track}", file=sys.stderr)
        return 2

    try:
        images = ensure_stills(plan)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not fal_key_available():
        print("ERROR: FAL_KEY not set.", file=sys.stderr)
        return 2

    durs = shot_durations(plan)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [
        (i, images[i], plan["scenes"][i], durs[i], CLIPS_DIR) for i in range(SCENE_COUNT)
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
                print(f"[{idx+1}/{SCENE_COUNT}] FAIL: {msg}", flush=True)
                if "Exhausted balance" in msg or "User is locked" in msg:
                    for f in futs:
                        f.cancel()
                    break
            except Exception as e:  # noqa: BLE001
                errors.append(f"shot {idx}: {e}")
                print(f"[{idx+1}/{SCENE_COUNT}] FAIL: {e}", flush=True)

    missing = [i for i in range(SCENE_COUNT) if i not in results]
    (CLIPS_DIR.parent / "progress.json").write_text(
        json.dumps(
            {"done": sorted(results), "missing": missing, "errors": errors[:12]},
            indent=2,
        )
        + "\n"
    )
    if missing:
        print(f"PARTIAL {len(results)}/{SCENE_COUNT}. Missing: {missing}", flush=True)
        return 4

    fitted = [results[i] for i in range(SCENE_COUNT)]
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS_DIR / FINAL_NAME
    print("FFmpeg stitch + mux → artifacts (no comic SFX)…", flush=True)
    ffmpeg_stitch_and_mux(fitted, track, out)

    plan_out = {
        "title": plan["title"],
        "style": "combined_graphic_novel_magnific_popart_anamorphic35mm",
        "engine": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        "aspect": "16:9",
        "fps": FPS,
        "scenes": SCENE_COUNT,
        "comic_text": False,
        "broll_in_all_acts": True,
        "duration_sec": plan["duration_sec"],
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
