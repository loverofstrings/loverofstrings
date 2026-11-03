#!/usr/bin/env python3
"""Build Find Me: nano-banana-2 stills → Seedance 2.0 clips → full comic MV."""

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
    "Sophisticated comic-book digital illustration, graphic novel print feel, "
    "steampunk brass gears and copper pipes mixed with cyberpunk holograms and "
    "synthwave neon grid, rain-slicked noir, dramatic dark ink lines, rich shadows, "
    "sharp digital ink cross-hatching, high-contrast neon rim lighting. "
    "NOT a photograph, NOT photorealistic, no watermark, no logo, no text overlays."
)

HERO = (
    "Same young woman as the reference images: striking expressive blue eyes, "
    "long blonde hair in a high dramatic ponytail or swept back, fair skin, "
    "signature black leather jacket over neo-industrial clothing — rendered entirely "
    "in the comic-book digital art style."
)

COSTUME_PURSUIT = (
    "Black leather jacket with asymmetrical zippers over dark charcoal neo-industrial "
    "crop top; tactical pants with copper buckle accents; high sharp blonde ponytail."
)

COSTUME_FINALE = (
    "Black leather jacket seams crackling with glowing hot-pink synthwave grid lines; "
    "subtle cybernetic ocular enhancement over the right eye glowing brilliant indigo; "
    "high blonde ponytail."
)


def still_prompt(kind: str, beat: str, master_frame: int) -> str:
    costume = COSTUME_FINALE if master_frame >= 6 else COSTUME_PURSUIT
    if kind == "star":
        role = (
            f"{HERO} Costume: {costume} She is the clear hero of the frame, "
            "starring comic-panel composition."
        )
    elif kind == "supporting":
        role = (
            f"Story atmosphere leads. {HERO} May appear partial, distant, or at the edge — "
            "not the hero of the shot."
        )
    else:
        role = (
            "World / atmosphere only. No clear hero face. Empty rain-noir steampunk-cyber "
            "comic environment."
        )
    return f"{STYLE} {role} Scene: {beat}"


def motion_prompt(kind: str, beat: str) -> str:
    base = (
        "Animate this comic-book digital illustration. Keep the same composition and "
        "characters. Cinematic camera motion, subtle neon pulse, rain and steam parallax. "
        "No new text, no watermark."
    )
    if kind == "star":
        role = "Hero character is the focus; gentle hair, rain, and light motion."
    elif kind == "supporting":
        role = "Story atmosphere leads; keep any figure secondary."
    else:
        role = "No hero close-up; animate environment, rain, gears, neon glow."
    return f"{base} {role} Scene: {beat}"


def curated_hero_paths() -> list[Path]:
    hero_dir = ROOT / "assets/find_me/hero"
    hero_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(hero_dir.glob("hero_*.*"))
    if existing:
        return existing
    picks = [
        ROOT / "assets/musician_ref_up.jpg",
        ROOT / "assets/shadow_hero_ref_up.jpg",
        ROOT / "assets/ramon/hero/hero_01.jpg",
        ROOT / "assets/ramon/hero/hero_02.jpg",
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


def find_track() -> Path | None:
    candidates = [
        ROOT / "assets/find_me/Find_Me.m4a",
        ROOT / "assets/find_me/Find_Me.mp3",
        ROOT / "assets/find_me/find_me.m4a",
        ROOT / "assets/find_me/find_me.mp3",
        ROOT / "assets/Find_Me.m4a",
        ROOT / "assets/Find_Me.mp3",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def generate_stills(plan: dict, ref_urls: list[str], scenes_dir: Path) -> list[Path]:
    scenes_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for sc in plan["scenes"]:
        dest = scenes_dir / sc["file"]
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"  skip existing still {dest.name}")
            paths.append(dest)
            continue
        prompt = still_prompt(sc["kind"], sc["beat"], int(sc.get("master_frame", 1)))
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
    plan = json.loads((ROOT / "examples/find_me/scene_plan.json").read_text())
    lyrics_path = ROOT / "examples/find_me/lyrics.txt"
    scenes_dir = ROOT / "examples/find_me/scenes"
    out = ROOT / "output/find_me/Find_Me_music_video.mp4"
    clips_dir = ROOT / "output/find_me/clips"
    track = find_track()

    user = UserCreativeInput(
        theme=(
            "Comic-book steampunk-cyber noir — brass copper, neon violet/cyan, "
            "synthwave grid, rain isolation to velocity pursuit"
        ),
        story=plan["story"],
        speed=1.15,
        mood="cinematic isolation, kinetic drum & bass chase, reconnection",
        palette=("#05050A", "#BB00FF", "#00F0FF", "#FF007F", "#C8963E"),
        caption_style="kinetic",
        transition="cut",
        title="Find Me",
        scene_count=len(plan["scenes"]),
        extra={"star_ratio": 0.32, "allow_shake": False},
    )

    if not fal_available():
        print("FAL_KEY missing — using local comic-grade + camera-motion cut.", file=sys.stderr)
        print(
            "Add FAL_KEY for nano-banana-2 stills + Seedance animation "
            "(https://fal.ai/dashboard/keys), then rerun:",
            file=sys.stderr,
        )
        print("  python3 scripts/make_find_me.py", file=sys.stderr)
        import subprocess

        subprocess.run(
            [sys.executable, str(ROOT / "scripts/comic_grade_stills.py")],
            check=True,
        )
        existing = [scenes_dir / s["file"] for s in plan["scenes"]]
        if track is None:
            print(
                "Track missing — place audio at assets/find_me/Find_Me.m4a "
                "(or .mp3). Stills are ready under examples/find_me/scenes/.",
                file=sys.stderr,
            )
            return 0
        preview = ROOT / "output/find_me/Find_Me_comic_preview.mp4"
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
        print(f"Wrote comic camera-motion music video: {preview}")
        print("Re-run with FAL_KEY for Seedance-animated upgrade.")
        return 0

    if track is None:
        print(
            "Track missing — place audio at assets/find_me/Find_Me.m4a before full mux.",
            file=sys.stderr,
        )

    print("Uploading hero reference images…")
    heroes = curated_hero_paths()
    ref_urls = upload_many(heroes)
    print(f"  {len(ref_urls)} refs uploaded")

    print("Generating stills with fal-ai/nano-banana-2…")
    stills = generate_stills(plan, ref_urls, scenes_dir)

    if track is None:
        print("Stills complete. Add the track and rerun to animate + assemble.")
        return 0

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
        "title": "Find Me",
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
