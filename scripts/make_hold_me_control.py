#!/usr/bin/env python3
"""
Hold Me Control — The Shadow Behind the Smile
NEW independent 16:9 YouTube pop-art music video (not an edit of prior cuts).

Pipeline: still boards → Seedance v1.5 Pro I2V → FFmpeg fit/loop → ASS comic SFX → mux track
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from music_video.assemble_animated import _concat_and_mux, _fit_clip  # noqa: E402
from music_video.seedance import (  # noqa: E402
    SeedanceError,
    download_video,
    fal_key_available,
    image_to_video,
)

CONFIG_PATH = ROOT / "examples/hold_me_control/config.json"
SHOT_BOARD_PATH = ROOT / "examples/hold_me_control/shot_board.json"
SCENES_DIR = ROOT / "examples/hold_me_control/scenes"
ORDER_PATH = ROOT / "examples/hold_me_control/scenes_order.txt"
CLIPS_DIR = ROOT / "output/hold_me_control/clips"
OUT_MP4 = ROOT / "output/hold_me_control/Hold_Me_Control_ShadowBehindSmile_16x9.mp4"
ASS_PATH = ROOT / "output/hold_me_control/comic_sfx.ass"

STYLE_LOCK = (
    "Magnific modern pop art, thick 4px black ink outlines, Ben-Day halftone dots, "
    "flat saturated cyan magenta bright yellow, bold comic graphic, NO photorealism, NO 3D CGI"
)

MOTION_TAIL = (
    "continuous motion only: orange hair blowing in wind, rain bouncing on wet asphalt, "
    "neon reflections shifting, shadow ink tendrils writhing and smoking when present, "
    "never a frozen still photograph"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def shot_windows(cfg: dict, board: dict) -> list[tuple[dict, float]]:
    """Distribute each scene's duration across its shots."""
    shots = board["shots"]
    out: list[tuple[dict, float]] = []
    for scene in cfg["scenes"]:
        sid = scene["id"]
        scene_shots = [s for s in shots if s["scene"] == sid]
        span = float(scene["t_end"]) - float(scene["t_start"])
        weights = [float(s.get("duration_hint", 5.0)) for s in scene_shots]
        tw = sum(weights) or 1.0
        for s, w in zip(scene_shots, weights):
            out.append((s, span * (w / tw)))
    return out


def write_ass(cfg: dict, path: Path) -> Path:
    """Comic SFX as ASS overlays (stylized event times from scene midpoints)."""
    header = textwrap.dedent(
        """\
        [Script Info]
        ScriptType: v4.00+
        PlayResX: 1920
        PlayResY: 1080
        WrapStyle: 0

        [V4+ Styles]
        Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
        Style: Whoosh,Impact,96,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,0,5,40,40,60,1
        Style: Crackle,Impact,84,&H00201040,&H000000FF,&H00FFFFFF,&H80000000,-1,0,0,0,100,100,3,-4,1,7,0,5,40,40,80,1
        Style: Pow,Impact,120,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,110,110,0,8,1,8,0,5,40,40,40,1
        Style: Skrrrt,Impact,92,&H00FF00AA,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,-6,1,7,0,7,40,40,100,1
        Style: Boom,Impact,100,&H00402060,&H000000FF,&H00FFFFFF,&H80000000,-1,0,0,0,100,100,4,0,1,8,0,2,40,40,120,1

        [Events]
        Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        """
    )

    def ts(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    events: list[str] = []
    mapping = {
        "WHOOSH!": "Whoosh",
        "CRACKLE...": "Crackle",
        "POW!": "Pow",
        "SKRRRRT!": "Skrrrt",
        "BOOM...": "Boom",
    }
    for scene in cfg["scenes"]:
        start = float(scene["t_start"])
        end = float(scene["t_end"])
        mid = (start + end) / 2
        for i, sfx in enumerate(scene.get("sfx", [])):
            text = sfx["text"]
            style = mapping.get(text, "Whoosh")
            # stagger multiple SFX inside a scene
            t0 = mid - 1.2 + i * 3.5
            t1 = t0 + 1.8
            t0 = max(start + 0.4, min(t0, end - 2.0))
            t1 = min(end - 0.2, t0 + 1.8)
            events.append(
                f"Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{text}"
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return path


def motion_prompt(shot: dict) -> str:
    return f"{shot['prompt_core']}. {STYLE_LOCK}. {MOTION_TAIL}."


def _animate_one(args: tuple) -> tuple[int, Path]:
    i, img, shot, dur, clips_root = args
    raw = clips_root / f"raw_{i:02d}.mp4"
    fit = clips_root / f"fit_{i:02d}.mp4"
    if fit.exists() and fit.stat().st_size > 1000:
        print(f"[{i+1}] reuse {fit.name}", flush=True)
        return i, fit
    prompt = motion_prompt(shot)
    gen_dur = max(4, min(8, int(round(max(4.0, min(dur, 8.0))))))
    print(f"[{i+1}] Seedance {img.name} ({gen_dur}s → fit {dur:.1f}s)…", flush=True)
    url = image_to_video(
        img,
        prompt,
        duration=gen_dur,
        resolution="720p",
        aspect_ratio="16:9",
        generate_audio=False,
    )
    download_video(url, raw)
    _fit_clip(raw, fit, dur, 1920, 1080)
    print(f"[{i+1}] done {fit.name}", flush=True)
    return i, fit


def run_generate(*, workers: int = 2) -> int:
    cfg = load_json(CONFIG_PATH)
    board = load_json(SHOT_BOARD_PATH)
    windows = shot_windows(cfg, board)

    if not ORDER_PATH.exists():
        print(f"ERROR: missing {ORDER_PATH} — generate stills first.", file=sys.stderr)
        return 2
    images = [ROOT / p for p in ORDER_PATH.read_text().splitlines() if p.strip()]
    if len(images) != len(windows):
        print(
            f"ERROR: {len(images)} images vs {len(windows)} shots",
            file=sys.stderr,
        )
        return 2
    for img in images:
        if not img.is_file():
            print(f"ERROR: missing still {img}", file=sys.stderr)
            return 2

    if not fal_key_available():
        print("ERROR: FAL_KEY not set.", file=sys.stderr)
        return 2

    track = ROOT / cfg["track"]
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    write_ass(cfg, ASS_PATH)

    jobs = []
    for i, ((shot, dur), img) in enumerate(zip(windows, images)):
        jobs.append((i, img, shot, dur, CLIPS_DIR))

    results: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_animate_one, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            i, path = fut.result()
            results[i] = path

    fitted = [results[i] for i in range(len(jobs))]
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    print("Concat + mux + comic SFX…", flush=True)
    _concat_and_mux(fitted, track, OUT_MP4, ass_path=ASS_PATH)

    # Outro grain pass on last ~6s (subtle)
    grain_out = OUT_MP4.with_name(OUT_MP4.stem + "_grain.mp4")
    dur = float(cfg["duration_sec"])
    grain_start = max(0.0, dur - 6.0)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(OUT_MP4),
            "-vf",
            f"noise=alls=12:allf=t+u:enable='gte(t,{grain_start})'",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "copy",
            str(grain_out),
        ],
        check=True,
    )
    grain_out.replace(OUT_MP4)

    plan_out = {
        "title": cfg["story_title"],
        "project": "independent_new_video",
        "engine": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        "aspect": "16:9",
        "duration": cfg["duration_sec"],
        "shots": len(jobs),
        "output": str(OUT_MP4),
    }
    OUT_MP4.with_suffix(".plan.json").write_text(json.dumps(plan_out, indent=2))
    print(f"Wrote {OUT_MP4}")
    return 0


def dry_run() -> int:
    cfg = load_json(CONFIG_PATH)
    board = load_json(SHOT_BOARD_PATH)
    windows = shot_windows(cfg, board)
    print(f"NEW VIDEO: {cfg['story_title']}")
    print(f"Track: {cfg['track']} ({cfg['duration_sec']}s)")
    print(f"Shots: {len(windows)} | Aspect: {cfg['aspect']}")
    for scene in cfg["scenes"]:
        n = sum(1 for s, _ in windows if s["scene"] == scene["id"])
        print(f"  Scene {scene['id']}: {n} shots | {scene['name']}")
    print("Dry run OK. Pass --generate to animate with Seedance.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generate", action="store_true", help="Run Seedance + assemble")
    p.add_argument("--workers", type=int, default=2)
    args = p.parse_args()
    if not args.generate:
        return dry_run()
    try:
        return run_generate(workers=args.workers)
    except SeedanceError as e:
        print(f"Seedance error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
