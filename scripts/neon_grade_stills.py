#!/usr/bin/env python3
"""Build neon-retrowave stills from local refs (no fal) for camera-motion preview."""

from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "examples/ramon/scene_plan.json"
OUT = ROOT / "examples/ramon/scenes"
HERO = ROOT / "assets/ramon/hero"
REFS = ROOT / "assets/ramon/refs"


def _load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def neon_grade(im: Image.Image, *, seed: int, world: bool) -> Image.Image:
    """Push magenta/cyan retrowave look with soft vignette."""
    rng = random.Random(seed)
    # Fit to 9:16 canvas
    target_w, target_h = 1080, 1920
    im = ImageOps.fit(im, (target_w, target_h), method=Image.Resampling.LANCZOS)

    r, g, b = im.split()
    # Magenta/cyan bias
    r = r.point(lambda x: min(255, int(x * 1.12 + 12)))
    b = b.point(lambda x: min(255, int(x * 1.18 + 18)))
    g = g.point(lambda x: max(0, int(x * 0.88)))
    im = Image.merge("RGB", (r, g, b))

    im = ImageEnhance.Color(im).enhance(1.45)
    im = ImageEnhance.Contrast(im).enhance(1.25)
    im = ImageEnhance.Brightness(im).enhance(0.95)

    # Soft neon glow
    glow = im.filter(ImageFilter.GaussianBlur(radius=8))
    im = Image.blend(im, glow, 0.18)

    # Vignette
    vignette = Image.new("L", (target_w, target_h), 0)
    # radial falloff via resized ellipse mask
    mask = Image.new("L", (target_w, target_h), 0)
    from PIL import ImageDraw

    draw = ImageDraw.Draw(mask)
    pad = int(min(target_w, target_h) * 0.08)
    draw.ellipse(
        (-pad, -pad * 2, target_w + pad, target_h + pad * 2),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=120))
    black = Image.new("RGB", (target_w, target_h), (8, 0, 24))
    im = Image.composite(im, black, mask)

    # Subtle scanline feel for world/atmosphere
    if world or rng.random() < 0.35:
        px = im.load()
        for y in range(0, target_h, 3):
            for x in range(target_w):
                pr, pg, pb = px[x, y]
                px[x, y] = (max(0, pr - 8), max(0, pg - 6), max(0, pb - 4))

    return im


def pick_sources() -> dict[str, list[Path]]:
    heroes = sorted(HERO.glob("hero_*.*"))
    refs = sorted(REFS.glob("ref_*.jpg")) if REFS.exists() else []
    # Prefer face-ish smaller portraits for star; larger neon for style
    star = heroes + [p for p in refs if p.name in {"ref_19.jpg", "ref_18.jpg", "ref_01.jpg", "ref_02.jpg"}]
    supporting = heroes[1:] + [p for p in refs if p.name in {"ref_10.jpg", "ref_14.jpg", "ref_08.jpg", "ref_21.jpg"}]
    world = [p for p in refs if p.name in {
        "ref_07.jpg", "ref_09.jpg", "ref_11.jpg", "ref_15.jpg", "ref_17.jpg",
        "ref_20.jpg", "ref_22.jpg", "ref_05.jpg", "ref_06.jpg", "ref_12.jpg",
    }] or refs or heroes
    return {
        "star": star or heroes or refs,
        "supporting": supporting or heroes or refs,
        "world": world or refs or heroes,
    }


def main() -> int:
    plan = json.loads(PLAN.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    pools = pick_sources()
    counters = {"star": 0, "supporting": 0, "world": 0}
    written = []
    for sc in plan["scenes"]:
        kind = sc["kind"]
        pool = pools[kind]
        src = pool[counters[kind] % len(pool)]
        counters[kind] += 1
        dest = OUT / sc["file"]
        graded = neon_grade(_load(src), seed=sc["id"] * 17, world=(kind == "world"))
        graded.save(dest, quality=92)
        written.append(dest)
        print(f"wrote {dest.name} from {src.name} ({kind})")
    print(f"Done: {len(written)} stills → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
