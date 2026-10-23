# Music Video Generator

Turn a **music track + image(s) + lyrics + genre** into a **full-length** MP4 music video.

Lyrics and genre choose theme, story arc, and cut speed. Your flags override any of those.

## What you provide

| Input | Required | Role |
|-------|----------|------|
| `--track` | yes | Song audio (mp3/wav) or video with audio (mp4) |
| `--image` | yes | Still art (repeat flag for multiple images) |
| `--lyrics` | yes | Inline text or path to `.txt` / `.lrc` |
| `--genre` | yes | Drives palette, motion, default speed, story arc |
| `--theme` | no | Your thematic direction |
| `--story` | no | Your narrative / synopsis |
| `--speed` | no | `slow` / `medium` / `fast` / `veryfast` or a float |
| `--title` / `--artist` | no | Opening title card |
| `--mood`, `--motion`, `--transition`, `--palette`, `--caption-style` | no | Fine visual control |

### Lyrics tips

Mark sections so the storyboard lands correctly:

```text
[Intro]
soft instruments

[Verse 1]
line one
line two

[Chorus]
the hook goes here

[Bridge]
turning point

[Outro]
fade
```

Blank lines also split unmarked verses.

## Quick start

```bash
pip install -r requirements.txt

python -m music_video \
  --track song.mp4 \
  --image cover.jpg \
  --lyrics lyrics.txt \
  --genre hip-hop \
  --title "My Song" \
  --artist "Me" \
  --theme "neon city at midnight" \
  --story "A lone walker crosses empty streets toward one lit window" \
  --speed medium \
  --output output/my_song.mp4
```

Vertical (TikTok/Reels size):

```bash
python -m music_video ... --vertical -o output/vertical.mp4
```

Preview the plan without rendering:

```bash
python -m music_video ... --plan-only
```

List genres:

```bash
python -m music_video --list-genres
```

## How it works

1. **Probe** the track for duration and a rough BPM estimate  
2. **Theme** from genre presets + lyric mood keywords + your overrides  
3. **Storyboard** scenes from lyric sections along a genre story arc  
4. **Timing** subdivides scenes into cuts from BPM × speed  
5. **Render** Ken Burns motion on your image(s), burn-in lyric captions, mux the full audio  

Sidecar `*.plan.json` next to the MP4 documents theme, scenes, and timing.

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe` on `PATH`
- `Pillow` (see `requirements.txt`)
