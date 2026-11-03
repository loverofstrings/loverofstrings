# Find Me — comic-book storyboard music video

Track: **Find Me** — Sigma feat. Birdy (~204s)  
Style: sophisticated comic-book digital art (steampunk brass + cyberpunk neon + synthwave grid)  
Pipeline: **fal-ai/nano-banana-2** stills → **Seedance 2.0** image-to-video → ffmpeg assemble

## Run

```bash
# Place the track at assets/find_me/Find_Me.m4a (or .mp3)
# Requires FAL_KEY (or FAL_API_KEY) for AI stills + Seedance
pip install -r requirements.txt
python scripts/make_find_me.py
```

Without `FAL_KEY`, the script builds comic-graded local stills (from hero refs) and a
camera-motion preview if the track file is present.

Output: `output/find_me/Find_Me_music_video.mp4`

## Layout

| Path | Role |
|------|------|
| `scene_plan.json` | 28 scenes (~32% starring) mapped to 8 master frames |
| `lyrics.txt` | Sectioned lyric scaffold for timing |
| `STYLE_BIBLE.txt` | Locked visual / costume / palette rules |
| `scenes/` | Generated stills |
| `assets/find_me/hero/` | Likeness reference images for `/edit` |

## Master frames (audio sync)

| Frame | Cue | Title |
|-------|-----|-------|
| 01 | 0:00–0:15 | The Rain-Slicked Void |
| 02 | 0:15–0:34 | Copper & Neon Isolation |
| 03 | 0:34–0:52 | The Synthwave Spark |
| 04 | 0:52–1:12 | Steam & Pressure Build-up |
| 05 | 1:12–1:45 | The Drop (Velocity Pursuit) |
| 06 | 1:45–2:20 | The Mid-Song Breakdown |
| 07 | 2:20–2:40 | The Climactic Build |
| 08 | 2:40–3:24 | The Grand Finale Drop |
