#!/usr/bin/env python3
"""Build Ramon: nano-banana-2 stills → Seedance 2.0 clips → full neon retrowave MV."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from music_video.assemble_animated import (  # noqa: E402
    _concat_and_mux,
    _fit_clip,
    fallback_camera_motion_render,
)
from music_video.audio import probe  # noqa: E402
from music_video.fal_gen import (  # noqa: E402
    FalError,
    animate_image,
    fal_available,
    generate_still,
    upload_file,
    upload_many,
)
from music_video.presets import UserCreativeInput  # noqa: E402
from music_video.story import build_storyboard  # noqa: E402
from music_video.theme import build_theme, load_lyrics  # noqa: E402
from music_video.timing import expand_shots, retime_scenes_by_music  # noqa: E402

STYLE = (
    "Neon retrowave synthwave digital pop-art illustration, sunset magenta-to-orange "
    "gradient sky, electric cyan perspective grid, chrome highlights, palm silhouettes, "
    "thick graphic shapes, poster print feel. NOT a photograph, NOT photorealistic, "
    "no watermark, no logo, no text overlays."
)

HERO = (
    "Same young woman as the reference images: long reddish-blonde / strawberry-blonde "
    "hair, fair skin, rendered entirely in the neon retrowave illustration style."
)


def still_prompt(kind: str, beat: str) -> str:
    if kind == "star":
        role = f"{HERO} She is the clear hero of the frame, starring close composition."
    elif kind == "supporting":
        role = (
            f"Story atmosphere leads. {HERO} May appear partial, distant, or at the edge — "
            "not the hero of the shot."
        )
    else:
        role = "World / atmosphere only. No clear hero face. Empty neon retrowave environment."
    return f"{STYLE} {role} Scene: {beat}"


def motion_prompt(kind: str, beat: str) -> str:
    base = (
        "Animate this neon retrowave synthwave illustration. Keep the same composition "
        "and characters. Smooth cinematic camera motion, subtle neon pulse, parallax depth. "
        "No new text, no watermark."
    )
    if kind == "star":
        role = "Hero character is the focus; gentle hair and light motion."
    elif kind == "supporting":
        role = "Story atmosphere leads; keep any figure secondary."
    else:
        role = "No hero close-up; animate environment, grid, and neon glow."
    return f"{base} {role} Scene: {beat}"


def curated_hero_paths() -> list[Path]:
    """Likeness refs: prefer committed hero/ set; otherwise seed from uploads."""
    hero_dir = ROOT / "assets/ramon/hero"
    hero_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(hero_dir.glob("hero_*.*"))
    if existing:
        return existing
    picks = [
        ROOT / "assets/musician_ref_up.jpg",
        ROOT / "assets/ramon/refs/ref_19.jpg",  # close portrait match
        ROOT / "assets/ramon/refs/ref_18.jpg",  # street portrait
        ROOT / "assets/ramon/refs/ref_10.jpg",  # neon stage energy / style
    ]
    out: list[Path] = []
    for i, src in enumerate(picks):
        if not src.exists():
            continue
        dest = hero_dir / f"hero_{i:02d}{src.suffix.lower()}"
        dest.write_bytes(src.read_bytes())
        out.append(dest)
    if not out:
        raise SystemExit("No hero reference images found")
    return out


def generate_stills(plan: dict, ref_urls: list[str], scenes_dir: Path) -> list[Path]:
    scenes_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for sc in plan["scenes"]:
        dest = scenes_dir / sc["file"]
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"  skip existing still {dest.name}")
            paths.append(dest)
            continue
        prompt = still_prompt(sc["kind"], sc["beat"])
        # Star/supporting: edit with likeness refs. World: pure T2I (cleaner empty scenes).
        urls = ref_urls if sc["kind"] in ("star", "supporting") else None
        print(f"  generating still {sc['id']:02d} ({sc['kind']})…")
        generate_still(prompt, dest, image_urls=urls, aspect_ratio="9:16", resolution="1K")
        paths.append(dest)
    return paths


def generate_clips(
    plan: dict,
    stills: list[Path],
    shots: list,
    clips_dir: Path,
) -> list[Path]:
    clips_dir.mkdir(parents=True, exist_ok=True)
    fitted: list[Path] = []
    for i, (sc, still, shot) in enumerate(zip(plan["scenes"], stills, shots)):
        raw = clips_dir / f"raw_{i:02d}.mp4"
        fit = clips_dir / f"fit_{i:02d}.mp4"
        if fit.exists() and fit.stat().st_size > 50_000:
            print(f"  skip existing clip {fit.name}")
            fitted.append(fit)
            continue
        print(f"  animating scene {sc['id']:02d} ({shot.duration:.1f}s)…")
        image_url = upload_file(still)
        dur = int(round(min(8.0, max(4.0, shot.duration))))
        animate_image(
            motion_prompt(sc["kind"], sc["beat"]),
            raw,
            image_url=image_url,
            duration=dur,
            resolution="720p",
            aspect_ratio="9:16",
            generate_audio=False,
            fast=True,
        )
        _fit_clip(raw, fit, shot.duration, 1080, 1920)
        fitted.append(fit)
    return fitted


def main() -> int:
    plan = json.loads((ROOT / "examples/ramon/scene_plan.json").read_text())
    track = ROOT / "assets/ramon/Ramon.m4a"
    lyrics_path = ROOT / "examples/ramon/lyrics.txt"
    scenes_dir = ROOT / "examples/ramon/scenes"
    out = ROOT / "output/ramon/Ramon_music_video.mp4"
    clips_dir = ROOT / "output/ramon/clips"

    user = UserCreativeInput(
        theme="Neon retrowave synthwave digital pop art — chrome, sunset grid, calling Ramon",
        story=plan["story"],
        speed=1.0,
        mood="neon retrowave, synthwave, nostalgic night drive",
        palette=("#0A0018", "#FF2BD6", "#00E5FF", "#FF6A00"),
        caption_style="kinetic",
        transition="cut",
        title="Ramon",
        scene_count=len(plan["scenes"]),
        extra={"star_ratio": 0.33, "allow_shake": False},
    )

    if not fal_available():
        print("FAL_KEY missing — cannot generate/animate yet.", file=sys.stderr)
        print(
            "Add FAL_KEY to Cloud Agent secrets (https://fal.ai/dashboard/keys), then rerun:",
            file=sys.stderr,
        )
        print("  python scripts/make_ramon.py", file=sys.stderr)
        # Camera-motion preview only if we already have stills
        existing = [scenes_dir / s["file"] for s in plan["scenes"]]
        if all(p.exists() for p in existing):
            preview = ROOT / "output/ramon/Ramon_preview_camera.mp4"
            fallback_camera_motion_render(
                track=track,
                images=existing,
                lyrics=str(lyrics_path),
                genre="electronic",
                output=preview,
                user=user,
                width=1080,
                height=1920,
            )
            print(f"Wrote camera-motion PREVIEW only: {preview}")
            return 2
        print("No stills yet — waiting on FAL_KEY to generate neon retrowave frames.")
        return 2

    print("Uploading hero reference images…")
    heroes = curated_hero_paths()
    ref_urls = upload_many(heroes)
    print(f"  {len(ref_urls)} refs uploaded")

    print("Generating stills with fal-ai/nano-banana-2…")
    stills = generate_stills(plan, ref_urls, scenes_dir)

    lyrics_text = load_lyrics(str(lyrics_path))
    audio = probe(track)
    theme = build_theme("electronic", lyrics_text, user)
    board = build_storyboard(lyrics_text, theme, audio.duration, user, len(stills))
    board = retime_scenes_by_music(board, audio.energy, theme)
    shots = expand_shots(
        board, theme, audio.bpm_estimate, fps=30, one_shot_per_scene=True, energy=audio.energy
    )

    print("Animating stills with Seedance 2.0…")
    fitted = generate_clips(plan, stills, shots, clips_dir)

    out.parent.mkdir(parents=True, exist_ok=True)
    print("Assembling full music video…")
    _concat_and_mux(fitted, track, out, ass_path=None)
    plan_out = {
        "title": "Ramon",
        "animated": True,
        "generator": {
            "stills": "fal-ai/nano-banana-2 (+ /edit with refs)",
            "video": "bytedance/seedance-2.0/fast/image-to-video",
        },
        "duration": audio.duration,
        "scenes": plan["scenes"],
        "output": str(out),
    }
    out.with_suffix(".plan.json").write_text(json.dumps(plan_out, indent=2), encoding="utf-8")
    print(f"Wrote animated video: {out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FalError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
