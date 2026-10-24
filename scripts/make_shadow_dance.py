#!/usr/bin/env python3
"""Build Shadow Dance with Seedance v1.5 Pro animated scenes."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from music_video.animate import motion_prompt  # noqa: E402
from music_video.assemble_animated import _concat_and_mux, _fit_clip  # noqa: E402
from music_video.audio import probe  # noqa: E402
from music_video.presets import UserCreativeInput  # noqa: E402
from music_video.seedance import SeedanceError, download_video, fal_key_available, image_to_video  # noqa: E402
from music_video.story import build_storyboard  # noqa: E402
from music_video.theme import build_theme, load_lyrics  # noqa: E402
from music_video.timing import expand_shots, retime_scenes_by_music  # noqa: E402


def _animate_one(args: tuple) -> tuple[int, Path]:
    i, img, meta, shot, clips_root = args
    raw = clips_root / f"raw_{i:02d}.mp4"
    fit = clips_root / f"fit_{i:02d}.mp4"
    if fit.exists() and fit.stat().st_size > 1000:
        print(f"[{i+1}/28] reuse {fit.name}", flush=True)
        return i, fit
    prompt = motion_prompt(meta.get("beat", ""), meta.get("kind", "world"), shot.motion)
    gen_dur = max(4, min(8, int(round(max(4.0, shot.duration)))))
    print(f"[{i+1}/28] Seedance {img.name} ({gen_dur}s, {shot.motion})…", flush=True)
    url = image_to_video(
        img,
        prompt,
        duration=gen_dur,
        resolution="720p",
        aspect_ratio="9:16",
        generate_audio=False,
    )
    download_video(url, raw)
    _fit_clip(raw, fit, shot.duration, 1080, 1920)
    print(f"[{i+1}/28] done {fit.name}", flush=True)
    return i, fit


def main() -> int:
    plan = json.loads((ROOT / "examples/shadow_dance/scene_plan.json").read_text())
    order = [p for p in (ROOT / "examples/shadow_dance/scenes_order.txt").read_text().splitlines() if p.strip()]
    images = [Path(p) for p in order]
    assert len(images) == 28, len(images)
    meta = plan["scenes"]

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
    )

    track = ROOT / "assets/Shadow_Dance.mp3"
    lyrics = load_lyrics(str(ROOT / "examples/shadow_dance/lyrics.txt"))
    audio = probe(track)
    theme = build_theme("electronic", lyrics, user)
    board = build_storyboard(lyrics, theme, audio.duration, user, len(images))
    board = retime_scenes_by_music(board, audio.energy, theme)
    shots = expand_shots(
        board, theme, audio.bpm_estimate, fps=30, one_shot_per_scene=True, energy=audio.energy
    )

    if not fal_key_available():
        print("ERROR: FAL_KEY not set.", file=sys.stderr)
        return 2

    clips_root = ROOT / "output/shadow_dance/seedance_clips"
    clips_root.mkdir(parents=True, exist_ok=True)

    jobs = []
    for i, shot in enumerate(shots):
        img = images[shot.image_index % len(images)]
        m = meta[i] if i < len(meta) else {"kind": "world", "beat": ""}
        jobs.append((i, img, m, shot, clips_root))

    results: dict[int, Path] = {}
    # 2 concurrent — Seedance jobs are long; keep pressure modest
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(_animate_one, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            i, path = fut.result()
            results[i] = path

    fitted = [results[i] for i in range(len(shots))]
    out = ROOT / "output/shadow_dance/Shadow_Dance_seedance.mp4"
    print("Concat + mux full track…", flush=True)
    _concat_and_mux(fitted, track, out, ass_path=None)
    plan_out = {
        "title": "Shadow Dance",
        "engine": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        "duration": board.duration,
        "scenes": [
            {
                "index": i,
                "kind": meta[i]["kind"],
                "beat": meta[i]["beat"],
                "start": board.scenes[i].start,
                "end": board.scenes[i].end,
                "motion": shots[i].motion,
            }
            for i in range(len(board.scenes))
        ],
        "output": str(out),
    }
    out.with_suffix(".plan.json").write_text(json.dumps(plan_out, indent=2))
    print(f"Wrote {out}")
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
