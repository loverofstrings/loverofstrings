# Hold Me Control — Pipeline Architecture (CONFIRM BEFORE RUN)

**Status:** NEW independent video in progress (not an edit). 30/30 stills ready. Seedance partial — fal balance exhausted; resume with `--generate` after top-up.

## Project lock

| Field | Value |
|-------|-------|
| Track | `assets/hold_me_control/Hold_Me_Control_Remastered.mp3` (~163.75s) |
| Title | Hold Me Control (Remastered) |
| Story | **The Shadow Behind the Smile** |
| Aspect | **16:9 YouTube widescreen** (`1920×1080`) |
| Style lock | Magnific modern pop art — thick ~4px black ink outlines, Ben-Day/halftone, flat cyan/magenta/yellow. One style for entire video. |
| Underlying tone | Luis Royo fantasy DNA (subtle) + cyberpunk/futuristic emo world |
| Engine | Fal Seedance `fal-ai/bytedance/seedance/v1.5/pro/image-to-video` → FFmpeg fit/loop/concat + ASS comic SFX |
| Motion rule | **No static stills as final.** Every beat = Seedance clip with continuous motion, then loop/trim to music window. |

## Character matrix

### Lexxi Red (protagonist)
- Likeness from `assets/hold_me_control/lexxi_ref.jpg` (**reference only** — never paste the photo)
- Long voluminous wavy **golden-orange** hair, fair skin, sharp confident eyes
- Signature **black studded motorcycle leather jacket**
- Pop-art vector: thick ink outlines + halftone shading

### Love Interest → Monster
- Messy dark undercut, white tee + distressed denim vest
- Progression: clean pop-art human → warping lines → liquid-black eldritch shadow (glowing hollow eyes)
- Shadow only fully reveals when Lexxi’s back is turned

### Syndicate (chars 3–4)
- Generic neon-masked enforcers for combat B-roll only

## Music-timed scene map (proposed)

| # | Role | Time (approx) | Duration | Beats per window | Comic SFX |
|---|------|---------------|----------|------------------|-----------|
| 1 | Intro / Verse 1 | 0.0 → 33.3s | ~33.3s | 5–6 Seedance loops | WHOOSH! |
| 2 | Pre-Chorus Shift | 33.3 → 62.3s | ~29.0s | 5 Seedance beats | CRACKLE… |
| 3 | Chorus Action | 62.3 → 101.4s | ~39.1s | 7–8 hard cuts | POW! / SKRRRRT! |
| 4 | Verse 2 Climax | 101.4 → 137.7s | ~36.2s | 6 tracking loops | BOOM… |
| 5 | Outro | 137.7 → 163.8s | ~26.1s | 4–5 close-up loops | (grain/static) |

Total Seedance clips ≈ **28–30** short animated shots (same count discipline as Shadow Dance), each ~4–6s generated, looped/trimmed to fill music windows. Chorus uses shorter cuts / higher intensity motions.

## Shot-by-shot board

### Scene 1 — Rain alley (tracking)
1. Lexxi + partner sprint toward camera / down rainy alley (hair + rain in motion)
2. Lateral track as they vault/slide toward brick cover
3. They slam cover behind wall; rain sheets sideways
4. Comic burst **WHOOSH!** (ASS overlay, stylized — not plain UI text)
5. Hold cover: breath, neon puddle ripples, partner glances back human

### Scene 2 — First shift (medium)
1. Lexxi peers around corner (back to partner)
2. Partner silhouette ripples; tendrils erupt; jaw splits (shadow writhes continuously)
3. Jagged **CRACKLE…** pulse in BG
4. Lexxi turns; partner snaps human + breathless grin
5. Beat of false safety (neon flicker, hair still moving)

### Scene 3 — Chorus combat (hard cuts)
1. Lexxi leap-kick into neon-masked enforcer
2. Impact frame + giant yellow **POW!**
3. Second enforcer / drone enters
4. Behind Lexxi: partner’s shadow claw expands, crushes drone
5. Purple jagged **SKRRRRT!**
6–8. Additional fight B-roll (Lexxi strikes; shadow assists only when she’s not looking)

### Scene 4 — Climax trail (split-panel track)
1. Split-panel / comic gutter: Lexxi walks forward neon street (back to camera)
2. Lower/behind panel: full ink-monster guardian trailing her
3. Continuous ink smoke / negative-space tendrils
4. Distorted **BOOM…** bleeds into environment
5–6. Push-in on Lexxi’s confident walk vs growing monster silhouette

### Scene 5 — Outro realization
1. Tight Lexxi face loop (hair micro-motion, neon reflections)
2. Black shadow drop hits jacket stud
3. Eyes lift to camera — realization
4. Analog grain / static fade to black over last bars

## Pipeline architecture

```
Hold_Me_Control_Remastered.mp3
        │
        ▼
┌───────────────────┐
│ 1. Probe + energy │  duration, BPM/energy envelope
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 2. Storyboard JSON│  5 narrative scenes → ~28 timed shots
│    (this doc)     │  comic SFX timestamps
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 3. Keyframe stills│  GenerateImage 16:9 pop-art boards
│    (Lexxi ref)    │  1 still per Seedance beat (consistency locks)
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 4. Seedance I2V   │  fal-ai/bytedance/seedance/v1.5/pro/image-to-video
│    continuous FX  │  prompt forces: hair wind, rain bounce, shadow writhe
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 5. FFmpeg fit     │  scale/crop 1920x1080, loop/trim to shot duration
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 6. ASS overlays   │  WHOOSH / CRACKLE / POW / SKRRRRT / BOOM
│                   │  comic fonts, jagged styles; burn-in
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 7. Concat + mux   │  full track AAC, outro grain/static filter
└─────────┬─────────┘
          ▼
   Hold_Me_Control_ShadowBehindSmile_16x9.mp4
```

## Config script (to execute after you say YES)

Path: `scripts/make_hold_me_control.py` (will be created on confirm)

```python
# CONFIG — Hold Me Control / Shadow Behind the Smile
TRACK = "assets/hold_me_control/Hold_Me_Control_Remastered.mp3"
LEXXI_REF = "assets/hold_me_control/lexxi_ref.jpg"
STYLE_REFS = [
    "assets/style_refs/house_popart_thickline_example.png",
    "assets/style_refs/magnific_popart/ref_01.jpg",
]
OUTPUT = "output/hold_me_control/Hold_Me_Control_ShadowBehindSmile_16x9.mp4"
ASPECT = "16:9"
WIDTH, HEIGHT = 1920, 1080
SEEDANCE_MODEL = "fal-ai/bytedance/seedance/v1.5/pro/image-to-video"
GENERATE_AUDIO = False          # mux song separately
CLIP_GEN_SEC = (4, 6)           # Seedance duration per beat
WORKERS = 2
SCENE_COUNT_TARGET = 28         # subdivided beats across 5 story scenes
STAR_RATIO = 0.35               # Lexxi hero frames vs world/supporting
MOTION_POLICY = "continuous"    # reject static: force rain/hair/shadow verbs in prompts
COMIC_SFX = {
    1: [("WHOOSH!", "yellow")],
    2: [("CRACKLE...", "dark")],
    3: [("POW!", "yellow"), ("SKRRRRT!", "purple")],
    4: [("BOOM...", "distorted")],
    5: [],  # grain/static only
}
REQUIRES_CONFIRM = True
```

## Motion prompt contract (every Seedance call)

Must include continuous physics language, e.g.:

- Lexxi: orange hair blowing, jacket studs catching neon, rain bouncing
- Partner human: breathing, wet asphalt reflections moving
- Partner shadow: ink tendrils writhing, smoke shifting, hollow eyes pulsing
- Never: “still image”, “frozen pose”, “photograph”

## Cost note (approx)

~28 Seedance clips × ~4–6s @ v1.5 Pro no-audio ≈ **similar ballpark to Shadow Dance (~$3.50–$5)** depending on exact durations. Confirm balance on fal dashboard before run.

## What I need from you

Reply **YES — generate** (or note changes) on:

1. Timing weights above OK for this track?  
2. ~28 animated beats across 5 story scenes OK?  
3. Comic SFX words as specified?  
4. 16:9 / 1920×1080 confirmed?  
5. Proceed with Seedance v1.5 Pro + FFmpeg pipeline as above?
