#!/usr/bin/env python3
"""
Hold Me Control — The Shadow Behind the Smile
16:9 YouTube pop-art Seedance pipeline.

CONFIRMATION GATE:
  This script refuses to call Seedance / spend fal credits unless you pass:
      --confirm-generate

  Dry-run (default): validates config, prints shot plan + cost estimate, exits.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIG_PATH = ROOT / "examples/hold_me_control/config.json"
SHOT_BOARD_PATH = ROOT / "examples/hold_me_control/shot_board.json"
ARCH_PATH = ROOT / "examples/hold_me_control/PIPELINE_ARCHITECTURE.md"

SEEDANCE_MODEL = "fal-ai/bytedance/seedance/v1.5/pro/image-to-video"
# Rough public ballpark for planning only (not a bill):
USD_PER_CLIP_HINT = 0.14


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def print_plan(cfg: dict, board: dict) -> None:
    shots = board["shots"]
    print("=" * 64)
    print(f"PROJECT: {cfg['story_title']}")
    print(f"TRACK:   {cfg['track']} ({cfg['duration_sec']}s)")
    print(f"OUTPUT:  {cfg['output']}")
    print(f"ASPECT:  {cfg['aspect']} {cfg['width']}x{cfg['height']}")
    print(f"ENGINE:  {cfg['engine']['i2v']}")
    print(f"STYLE:   {cfg['style']['lock']}")
    print(f"SHOTS:   {len(shots)} (target {cfg['scene_count_target']})")
    print("=" * 64)
    for scene in cfg["scenes"]:
        sid = scene["id"]
        n = sum(1 for s in shots if s["scene"] == sid)
        sfx = ", ".join(x["text"] for x in scene.get("sfx", [])) or "(none)"
        print(
            f"Scene {sid} [{scene['t_start']:.1f}-{scene['t_end']:.1f}s] "
            f"{scene['name']} | {n} shots | SFX: {sfx}"
        )
        print(f"  → {scene['action']}")
    est = len(shots) * USD_PER_CLIP_HINT
    print("-" * 64)
    print(f"Cost hint (planning only): ~${est:.2f} for {len(shots)} Seedance clips")
    print(f"Motion policy: {cfg['motion_policy']['mode']}")
    print(f"Architecture: {ARCH_PATH}")
    print("=" * 64)


def dry_run() -> int:
    cfg = load_json(CONFIG_PATH)
    board = load_json(SHOT_BOARD_PATH)
    print_plan(cfg, board)
    print("\nDRY RUN ONLY — no Seedance calls. Pass --confirm-generate to execute.")
    return 0


def run_generate() -> int:
    """Wire into music_video Seedance assembler when confirmed."""
    cfg = load_json(CONFIG_PATH)
    board = load_json(SHOT_BOARD_PATH)
    print_plan(cfg, board)

    # Deferred imports so dry-run works without fal key.
    from music_video.seedance import ensure_fal_key  # type: ignore

    ensure_fal_key()

    out_dir = ROOT / "output" / "hold_me_control"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "status": "confirmed",
                "config": cfg,
                "shots": board["shots"],
                "model": SEEDANCE_MODEL,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nManifest written: {out_dir / 'run_manifest.json'}")
    print(
        "Next stage on confirm: still boards → Seedance I2V → FFmpeg fit/loop → "
        "ASS comic SFX → mux track → final 16:9 mp4."
    )
    print(
        "NOTE: Full still+Seedance execution will be triggered in a follow-up "
        "agent step after this gate; this confirm run locks the plan."
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--confirm-generate",
        action="store_true",
        help="Spend fal credits and start sequence generation",
    )
    p.add_argument(
        "--print-architecture",
        action="store_true",
        help="Print PIPELINE_ARCHITECTURE.md and exit",
    )
    args = p.parse_args()

    if args.print_architecture:
        print(ARCH_PATH.read_text(encoding="utf-8"))
        return 0

    if not args.confirm_generate:
        return dry_run()
    return run_generate()


if __name__ == "__main__":
    raise SystemExit(main())
