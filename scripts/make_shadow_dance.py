#!/usr/bin/env python3
"""Build Shadow Dance: storyboard stills → animate → full music video."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from music_video.animate import AnimationError, fal_available  # noqa: E402
from music_video.assemble_animated import (  # noqa: E402
    fallback_camera_motion_render,
    generate_animated,
)
from music_video.presets import UserCreativeInput


def main() -> int:
    plan = json.loads((ROOT / "examples/shadow_dance/scene_plan.json").read_text())
    order = (ROOT / "examples/shadow_dance/scenes_order.txt").read_text().splitlines()
    images = [Path(p) for p in order if p.strip()]
    assert len(images) == 28, len(images)

    user = UserCreativeInput(
        theme="Cyberpunk neon retro-hell digital pop art with thick outlines — shadow dance, let it fall",
        story=plan["story"],
        speed=1.0,
        mood="cyberpunk neon retro hell, futuristic, rhythmic",
        palette=("#0A0014", "#FF2BD6", "#00F0FF"),
        caption_style="kinetic",
        transition="cut",
        title="Shadow Dance",
        scene_count=28,
        extra={"star_ratio": 0.35, "allow_shake": False},
    )

    out = ROOT / "output/shadow_dance/Shadow_Dance_music_video.mp4"
    meta = plan["scenes"]

    if fal_available():
        print("Animating 28 scenes with fal image-to-video…")
        path = generate_animated(
            track=ROOT / "assets/Shadow_Dance.mp3",
            images=images,
            lyrics=str(ROOT / "examples/shadow_dance/lyrics.txt"),
            genre="electronic",
            output=out,
            scene_meta=meta,
            user=user,
            width=1080,
            height=1920,
            clips_dir=ROOT / "output/shadow_dance/clips",
        )
        print(f"Wrote animated video: {path}")
        return 0

    print("FAL_API_KEY missing — cannot animate scenes yet.", file=sys.stderr)
    print("Add FAL_API_KEY to Cloud Agent secrets, then rerun this script.", file=sys.stderr)
    # Still produce a less-shake camera preview so assets are validated
    preview = ROOT / "output/shadow_dance/Shadow_Dance_preview_camera.mp4"
    fallback_camera_motion_render(
        track=ROOT / "assets/Shadow_Dance.mp3",
        images=images,
        lyrics=str(ROOT / "examples/shadow_dance/lyrics.txt"),
        genre="electronic",
        output=preview,
        user=user,
        width=1080,
        height=1920,
    )
    print(f"Wrote camera-motion PREVIEW only (not final): {preview}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
