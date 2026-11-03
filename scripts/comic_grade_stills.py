#!/usr/bin/env python3
"""Build comic/steampunk-cyber stills from local hero refs (no fal) for Find Me preview."""

from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "examples/find_me/scene_plan.json"
OUT = ROOT / "examples/find_me/scenes"
HERO = ROOT / "assets/find_me/hero"

# Palette from STYLE_BIBLE
VOID = (5, 5, 10)
CYAN = (0, 240, 255)
VIOLET = (187, 0, 255)
PINK = (255, 0, 127)
BRASS = (200, 150, 62)
INDIGO = (75, 0, 130)


def _load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def comic_grade(im: Image.Image, *, seed: int, kind: str, master_frame: int) -> Image.Image:
    """Push rain-noir comic look: violet/cyan rim bias, ink contrast, vignette."""
    rng = random.Random(seed)
    target_w, target_h = 1080, 1920
    im = ImageOps.fit(im, (target_w, target_h), method=Image.Resampling.LANCZOS)

    # Phase shift: pursuit (1-5) vs finale void (6-8)
    finale = master_frame >= 6

    r, g, b = im.split()
    if finale:
        r = r.point(lambda x: min(255, int(x * 1.15 + 18)))
        b = b.point(lambda x: min(255, int(x * 1.22 + 28)))
        g = g.point(lambda x: max(0, int(x * 0.78)))
    else:
        r = r.point(lambda x: min(255, int(x * 1.05 + 8)))
        b = b.point(lambda x: min(255, int(x * 1.25 + 22)))
        g = g.point(lambda x: max(0, int(x * 0.85)))
    im = Image.merge("RGB", (r, g, b))

    im = ImageEnhance.Color(im).enhance(1.55 if finale else 1.35)
    im = ImageEnhance.Contrast(im).enhance(1.45)
    im = ImageEnhance.Sharpness(im).enhance(1.35)
    im = ImageEnhance.Brightness(im).enhance(0.88)

    # Soft neon glow
    glow = im.filter(ImageFilter.GaussianBlur(radius=10))
    im = Image.blend(im, glow, 0.22)

    # Ink-edge feel via unsharp + slight posterize
    im = ImageOps.posterize(im, 6)
    im = ImageEnhance.Contrast(im).enhance(1.15)

    # Vignette toward void black
    mask = Image.new("L", (target_w, target_h), 0)
    draw = ImageDraw.Draw(mask)
    pad = int(min(target_w, target_h) * 0.06)
    draw.ellipse((-pad, -pad * 2, target_w + pad, target_h + pad * 2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=140))
    black = Image.new("RGB", (target_w, target_h), VOID)
    im = Image.composite(im, black, mask)

    # Diagonal rain streaks for world / rain frames
    if kind == "world" or master_frame in {1, 2, 5} or rng.random() < 0.4:
        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for _ in range(90):
            x = rng.randint(-40, target_w)
            y = rng.randint(-40, target_h)
            length = rng.randint(18, 55)
            color = (*CYAN, rng.randint(35, 90)) if rng.random() < 0.5 else (*VIOLET, rng.randint(30, 80))
            od.line([(x, y), (x + length // 3, y + length)], fill=color, width=1)
        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

    # Hot pink grid accent for finale frames
    if finale and (kind == "star" or rng.random() < 0.5):
        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        step = 48
        for gx in range(0, target_w, step):
            od.line([(gx, int(target_h * 0.55)), (gx, target_h)], fill=(*PINK, 40), width=1)
        for gy in range(int(target_h * 0.55), target_h, step):
            od.line([(0, gy), (target_w, gy)], fill=(*PINK, 35), width=1)
        # brass flecks
        for _ in range(40):
            x, y = rng.randint(0, target_w - 1), rng.randint(0, target_h - 1)
            od.ellipse([x, y, x + 2, y + 2], fill=(*BRASS, 120))
        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

    # Halftone-ish scan for steam / industrial world
    if kind == "world" and master_frame in {2, 4, 5}:
        px = im.load()
        for y in range(0, target_h, 4):
            for x in range(0, target_w, 4):
                pr, pg, pb = px[x, y]
                px[x, y] = (
                    min(255, pr + 6),
                    max(0, pg - 4),
                    min(255, pb + 4),
                )

    return im


def pick_sources() -> dict[str, list[Path]]:
    heroes = sorted(HERO.glob("hero_*.*"))
    if not heroes:
        raise SystemExit(f"No hero refs in {HERO}")
    # Rotate pools so world stills aren't always the same tight portrait crop
    return {
        "star": heroes,
        "supporting": list(reversed(heroes)),
        "world": heroes[::1],
    }


def main() -> int:
    plan = json.loads(PLAN.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    pools = pick_sources()
    counters = {"star": 0, "supporting": 0, "world": 0}
    for sc in plan["scenes"]:
        kind = sc["kind"]
        pool = pools[kind]
        src = pool[counters[kind] % len(pool)]
        counters[kind] += 1
        dest = OUT / sc["file"]
        if dest.exists() and dest.stat().st_size > 10_000:
            # Keep AI / previously generated stills
            print(f"  skip {dest.name}")
            continue
        im = comic_grade(
            _load(src),
            seed=sc["id"] * 97,
            kind=kind,
            master_frame=int(sc.get("master_frame", 1)),
        )
        im.save(dest, quality=92)
        print(f"  wrote {dest.name} from {src.name}")
    print(f"Comic-graded stills → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
