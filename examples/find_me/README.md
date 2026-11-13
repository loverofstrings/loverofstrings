# Find Me — comic-book storyboard music video

Style: sophisticated comic-book digital art (steampunk brass + cyberpunk neon + synthwave grid)  
Pipeline: **fal-ai/nano-banana-2** stills → **Seedance 2.0** image-to-video → ffmpeg assemble

**Current track:** `assets/find_me/track.mp3` — *I Like It Like That* (~214s). Swap the file anytime; the 48-scene cut scales from a 204s scaffold to the track length on render.

## Animate stills → video (Seedance)

Requires `FAL_KEY`. Turns **all 48** storyboard stills into motion clips, then muxes `track.mp3`.

```bash
python3 scripts/animate_find_me.py
# → output/find_me/Find_Me_music_video.mp4
```

## Run

```bash
# Optional: place track at assets/find_me/track.m4a
# Requires FAL_KEY for AI stills + Seedance
pip install -r requirements.txt
python3 scripts/make_find_me.py
```

Without `FAL_KEY`, the script builds comic-graded local stills and a camera-motion preview if a track is present.

## Render (Ken Burns / camera-motion)

```bash
python3 scripts/render_find_me.py
```

Uses exact scene_plan timings (9:16). Muxes whatever track is in `assets/find_me/`; otherwise a silent timing bed.

Output: `output/find_me/Find_Me_render.mp4`  
Animated (FAL) output: `output/find_me/Find_Me_music_video.mp4`

## Layout

| Path | Role |
|------|------|
| `scene_plan.json` | **48 scenes** — 13 star / 9 supporting / 18 world / **8 b-roll** |
| `lyrics.txt` | Sectioned lyric scaffold for timing (replace with your song’s sections) |
| `STYLE_BIBLE.txt` | Locked visual / costume / palette rules |
| `scenes/` | Generated stills |
| `assets/find_me/hero/` | Likeness reference images for `/edit` |
| `assets/find_me/track.*` | Your audio (any song) |

## Master frames (relative sync)

| Frame | Relative cue | Title |
|-------|--------------|-------|
| 01 | open | The Rain-Slicked Void |
| 02 | early | Copper & Neon Isolation |
| 03 | spark | The Synthwave Spark |
| 04 | build | Steam & Pressure Build-up |
| 05 | drop | The Drop (Velocity Pursuit) |
| 06 | breakdown | The Mid-Song Breakdown |
| 07 | climb | The Climactic Build |
| 08 | finale | The Grand Finale Drop |

B-roll inserts (texture / skyline / steam / energy / vortex) sit at the top of each arc for breathing room.
