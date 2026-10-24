# Ramon — neon retrowave music video

Track: `assets/ramon/Ramon.m4a` (~130s)  
Style: neon retrowave / synthwave digital pop art  
Pipeline: **fal-ai/nano-banana-2** stills → **Seedance 2.0** image-to-video → ffmpeg assemble

## Run

```bash
# Requires FAL_KEY (or FAL_API_KEY) in the environment
pip install -r requirements.txt
python scripts/make_ramon.py
```

Output: `output/ramon/Ramon_music_video.mp4`

## Layout

| Path | Role |
|------|------|
| `scene_plan.json` | 24 scenes (~33% starring) |
| `lyrics.txt` | Sectioned lyric scaffold for timing |
| `STYLE_BIBLE.txt` | Locked visual rules |
| `scenes/` | Generated stills (created by the script) |
| `assets/ramon/hero/` | Likeness reference images for `/edit` |
| `assets/ramon/refs/` | Extra uploaded style / character references |

Without `FAL_KEY`, the script exits with instructions (and can only build a camera-motion preview if stills already exist).
