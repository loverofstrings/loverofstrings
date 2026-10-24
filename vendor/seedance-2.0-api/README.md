# Seedance 2.0 API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES2020+-yellow.svg)](https://nodejs.org)
[![fal.ai](https://img.shields.io/badge/Platform-fal.ai-purple.svg)](https://fal.ai)

The official API for **Seedance 2.0** - ByteDance's most advanced video generation model. Cinematic-quality output with native audio, real-world physics, and director-level camera control.

Available now on [fal.ai](https://fal.ai).

> **[Get Started](https://fal.ai/models/bytedance/seedance-2.0/text-to-video)** - Try Seedance 2.0 directly on fal.ai.

## What is Seedance 2.0?

Seedance 2.0 is ByteDance's state-of-the-art video generation model, available as a text to video API and image to video API through [fal.ai](https://fal.ai). It supports text-to-video, image-to-video, and multi-modal reference-to-video generation with native audio synthesis, real-world physics simulation, and cinematic camera control. The Seedance 2.0 video generation API produces up to 15-second clips at 720p across multiple aspect ratios.

---

## Features

- **Text to Video** - Generate cinematic video from text prompts
- **Image to Video** - Animate static images with realistic motion
- **Reference to Video** - Multi-modal generation with image, video, and audio references
- **Native Audio** - Synchronized sound effects, ambient audio, and lip-synced speech
- **Director-Level Camera Control** - Precise control over camera movement and framing
- **Up to 15 seconds** - Generate 4-15 second clips at 480p or 720p
- **Multiple Aspect Ratios** - 16:9, 9:16, 4:3, 3:4, 1:1, 21:9 ultrawide

## Quick Start

### Seedance 2.0 Python

```bash
pip install fal-client
```

```python
import fal_client

result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "A cinematic slow-motion shot of a golden eagle soaring through a mountain valley at sunrise.",
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)

print(result["video"]["url"])
```

### Seedance 2.0 JavaScript

```bash
npm install @fal-ai/client
```

```javascript
import { fal } from "@fal-ai/client";

const result = await fal.subscribe("bytedance/seedance-2.0/text-to-video", {
  input: {
    prompt:
      "A cinematic slow-motion shot of a golden eagle soaring through a mountain valley at sunrise.",
    resolution: "720p",
    duration: "10",
    aspect_ratio: "16:9",
    generate_audio: true,
  },
});

console.log(result.data.video.url);
```

### cURL

```bash
curl -X POST https://fal.run/bytedance/seedance-2.0/text-to-video \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic slow-motion shot of a golden eagle soaring through a mountain valley at sunrise.",
    "resolution": "720p",
    "duration": "10",
    "aspect_ratio": "16:9",
    "generate_audio": true
  }'
```

---

## Endpoints

Seedance 2.0 is available in **standard** and **fast** tiers across three generation modes.

### Standard Tier

Higher quality output.

| Endpoint | Model ID | Pricing |
|---|---|---|
| [Text to Video](https://fal.ai/models/bytedance/seedance-2.0/text-to-video) | `bytedance/seedance-2.0/text-to-video` | $0.3034/sec |
| [Image to Video](https://fal.ai/models/bytedance/seedance-2.0/image-to-video) | `bytedance/seedance-2.0/image-to-video` | $0.3024/sec |
| [Reference to Video](https://fal.ai/models/bytedance/seedance-2.0/reference-to-video) | `bytedance/seedance-2.0/reference-to-video` | $0.3024/sec |

### Fast Tier

Lower cost, faster generation.

| Endpoint | Model ID | Pricing |
|---|---|---|
| [Text to Video (Fast)](https://fal.ai/models/bytedance/seedance-2.0/fast/text-to-video) | `bytedance/seedance-2.0/fast/text-to-video` | $0.2419/sec |
| [Image to Video (Fast)](https://fal.ai/models/bytedance/seedance-2.0/fast/image-to-video) | `bytedance/seedance-2.0/fast/image-to-video` | $0.2419/sec |
| [Reference to Video (Fast)](https://fal.ai/models/bytedance/seedance-2.0/fast/reference-to-video) | `bytedance/seedance-2.0/fast/reference-to-video` | $0.2419/sec |

> Reference to Video endpoints with video inputs receive a **0.6x price multiplier**.

---

## API Reference

### Text to Video

Generate video from a text prompt.

**Model IDs:** `bytedance/seedance-2.0/text-to-video` | `bytedance/seedance-2.0/fast/text-to-video`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `prompt` | string | Yes | - | Text description of the video to generate |
| `resolution` | string | No | `"720p"` | `"480p"` or `"720p"` |
| `duration` | string | No | `"auto"` | `"auto"` or `"4"` through `"15"` seconds |
| `aspect_ratio` | string | No | `"auto"` | `"auto"`, `"21:9"`, `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"` |
| `generate_audio` | boolean | No | `true` | Generate synchronized audio |
| `seed` | integer | No | - | Random seed for reproducibility |
| `end_user_id` | string | No | - | Unique identifier for end-user tracking |

```python
result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "A timelapse of a flower blooming in a sunlit garden, soft bokeh background.",
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

---

### Image to Video

Animate a static image with motion, physics, and optional audio.

**Model IDs:** `bytedance/seedance-2.0/image-to-video` | `bytedance/seedance-2.0/fast/image-to-video`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `prompt` | string | Yes | - | Text description of the desired motion |
| `image_url` | string | Yes | - | URL of the starting frame image (JPEG, PNG, WebP, max 30 MB) |
| `end_image_url` | string | No | - | URL of the ending frame for start-to-end transitions |
| `resolution` | string | No | `"720p"` | `"480p"` or `"720p"` |
| `duration` | string | No | `"auto"` | `"auto"` or `"4"` through `"15"` seconds |
| `aspect_ratio` | string | No | `"auto"` | `"auto"`, `"21:9"`, `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"` |
| `generate_audio` | boolean | No | `true` | Generate synchronized audio |
| `seed` | integer | No | - | Random seed for reproducibility |
| `end_user_id` | string | No | - | Unique identifier for end-user tracking |

```python
result = fal_client.subscribe(
    "bytedance/seedance-2.0/image-to-video",
    arguments={
        "prompt": "She slowly turns to face the camera, wind catching her hair.",
        "image_url": "https://example.com/portrait.jpg",
        "resolution": "720p",
        "duration": "8",
        "aspect_ratio": "auto",
        "generate_audio": True,
    },
)
```

#### Start-to-End Frame Transition

```python
result = fal_client.subscribe(
    "bytedance/seedance-2.0/image-to-video",
    arguments={
        "prompt": "Smooth transition from day to night, the sky gradually darkens as city lights turn on.",
        "image_url": "https://example.com/day.jpg",
        "end_image_url": "https://example.com/night.jpg",
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
    },
)
```

---

### Reference to Video (Omni-Modal)

The most powerful Seedance 2.0 endpoint. Generate video conditioned on any combination of reference images, videos, and audio - style transfer, lip-sync, motion transfer, character consistency, and scene composition all in one model.

Use `@Image1`, `@Video1`, `@Audio1` syntax in your prompt to reference inputs. Use scene cuts and timestamps to control pacing (e.g. "Cut scene to...", "At 5 seconds...").

**Model IDs:** `bytedance/seedance-2.0/reference-to-video` | `bytedance/seedance-2.0/fast/reference-to-video`

**Capabilities:** stylized generation, style transfer, lip-sync, motion transfer, character consistency, multi-scene composition

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `prompt` | string | Yes | - | Text prompt with `@Image1`, `@Video1`, `@Audio1` references. Supports scene cuts and timestamps for pacing control. |
| `image_urls` | list\<string\> | No | - | Up to 9 reference images (JPEG, PNG, WebP, max 30 MB each) |
| `video_urls` | list\<string\> | No | - | Up to 3 reference videos (MP4, MOV, 2-15s combined, max 50 MB, ~480p-720p resolution) |
| `audio_urls` | list\<string\> | No | - | Up to 3 audio files (MP3, WAV, max 15s combined, max 15 MB each). Requires at least one reference image or video. |
| `resolution` | string | No | `"720p"` | `"480p"` or `"720p"` |
| `duration` | string | No | `"auto"` | `"auto"` or `"4"` through `"15"` seconds |
| `aspect_ratio` | string | No | `"auto"` | `"auto"`, `"21:9"`, `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"` |
| `generate_audio` | boolean | No | `true` | Generate synchronized audio including sound effects, ambient sounds, and lip-synced speech |
| `seed` | integer | No | - | Random seed for reproducibility |
| `end_user_id` | string | No | - | Unique identifier for end-user tracking |

> Total files across all modalities must not exceed 12. Video inputs receive a **0.6x price multiplier**.

#### Character-Consistent Generation

```python
# Use an image reference to maintain character identity across scenes
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 walks confidently down a neon-lit city street at night, camera tracking alongside.",
        "image_urls": [
            "https://example.com/character.jpg",
        ],
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

#### Style Transfer

```python
# Apply the visual style of a reference image to generated video
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "A bustling Tokyo street scene at night in the style of @Image1, neon reflections on wet pavement.",
        "image_urls": ["https://example.com/art-style-reference.jpg"],
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "21:9",
        "generate_audio": True,
    },
)
```

#### Lip-Sync with Audio Reference

```python
# Generate a talking-head video with lip-synced speech from an audio reference
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 speaks directly to the camera in a professional studio setting while saying @Audio1.",
        "image_urls": ["https://example.com/speaker.jpg"],
        "audio_urls": ["https://example.com/speech.mp3"],
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

#### Motion Transfer from Video Reference

```python
# Transfer motion from a reference video onto a character from an image
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 performs the dance moves from @Video1 on a rooftop at sunset.",
        "image_urls": ["https://example.com/dancer.jpg"],
        "video_urls": ["https://example.com/dance-reference.mp4"],
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

#### Multi-Scene Composition with Scene Cuts

```python
# Use scene cuts in the prompt to control pacing and transitions
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 finds a football in the ocean and picks it up excitedly. Cut scene to @Image1 calling friends over. Cut scene to a group of characters playing football underwater.",
        "image_urls": [
            "https://example.com/character.jpg",
        ],
        "resolution": "720p",
        "duration": "15",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

#### Full Multi-Modal - Images, Video, and Audio Combined

```python
# Combine all modalities: image for character, video for motion, audio for soundtrack
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 performs the choreography from @Video1 on stage while @Audio1 plays in the background.",
        "image_urls": ["https://example.com/performer.jpg"],
        "video_urls": ["https://example.com/choreography.mp4"],
        "audio_urls": ["https://example.com/track.mp3"],
        "resolution": "720p",
        "duration": "15",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

---

## Prompt Guide

Writing good Seedance 2.0 prompts follows a simple structure: **Subject + Action + Camera + Scene/Lighting + Style**. Aim for 50-150 words. Be specific about camera movements ("slow dolly push in" not "camera moves forward") and always include lighting - it has the biggest single impact on output quality.

**Tips:**
- Use "Cut scene to..." for multi-scene videos
- Avoid the word "fast" - it tends to cause jitter. If you need pace, keep only one element fast.
- Describe camera and subject movement separately to avoid shaky output
- Longer prompts with more detail generally produce better results

### Cinematic / Film

```python
# Cinematic trailer - post-apocalyptic
result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "Slow dolly push in on a lone survivor standing atop a crumbled overpass, wind whipping dust across the frame. She stares into the distance at a ruined skyline, golden hour backlighting her silhouette. Camera drifts from a medium shot to a tight close-up on her face, catching the light in her eyes. Film grain, muted earth tones, anamorphic lens flare.",
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "21:9",
        "generate_audio": True,
    },
)
```

```python
# Film noir - detective scene
result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "A hard-faced detective in a long coat stands under a flickering streetlamp on a rain-soaked city street. He lights a cigarette, the flame briefly illuminating his scarred jawline. Camera starts wide, slowly pushing in as rain streaks catch the neon light from a bar sign behind him. High contrast black and white, deep shadows, 35mm grain.",
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

### Product / Commercial

```python
# Product showcase - smartphone
result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "A premium smartphone rotates slowly on a matte black surface, studio lighting reflecting off the glass edges. Camera orbits 360 degrees at eye level, then cuts to a macro shot of the camera module with lens flare. Minimal, clean aesthetic with soft gradient background shifting from deep navy to charcoal.",
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

```python
# Food commercial - coffee
result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "Overhead shot of freshly brewed coffee being poured into a ceramic mug on a rustic wooden table. Steam rises in soft curls, catching warm morning sunlight from a nearby window. Camera slowly descends and pushes in to capture the swirl of cream being added. Warm color palette, shallow depth of field, cozy atmosphere.",
        "resolution": "720p",
        "duration": "8",
        "aspect_ratio": "4:3",
        "generate_audio": True,
    },
)
```

### Talking Head / Lip-Sync

```python
# Lip-synced speaker with audio reference
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 speaks directly into the camera with confident, natural gestures. Professional studio setting with soft three-point lighting and a slightly blurred office background. Medium shot framing from the chest up, subtle head movements and eye contact throughout while delivering @Audio1.",
        "image_urls": ["https://example.com/speaker-headshot.jpg"],
        "audio_urls": ["https://example.com/voiceover.mp3"],
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

### Dance / Music Video

```python
# Dance video with motion transfer and scene cuts
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 performs the choreography from @Video1 on a rain-soaked rooftop at night, neon signs reflecting in puddles. Camera tracks alongside the movement. Cut scene to a wide shot from above as the dancer hits the final pose, city lights stretching out below. High contrast, vibrant neon color grading, cinematic slow-motion on the final beat.",
        "image_urls": ["https://example.com/dancer.jpg"],
        "video_urls": ["https://example.com/choreography.mp4"],
        "resolution": "720p",
        "duration": "15",
        "aspect_ratio": "9:16",
        "generate_audio": True,
    },
)
```

### Nature / Landscape

```python
# Nature timelapse
result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "Timelapse of a dramatic mountain landscape transitioning from dawn to midday. Fog rolls through the valley as the sun crests the peaks, casting long golden rays across alpine meadows. Clouds accelerate overhead in soft streaks. Camera holds steady on a wide establishing shot with a slow, barely perceptible zoom. Vivid natural colors, HDR dynamic range.",
        "resolution": "720p",
        "duration": "15",
        "aspect_ratio": "21:9",
        "generate_audio": True,
    },
)
```

### Anime / Stylized

```python
# Anime-style scene with style reference
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "In the style of @Image1, a young swordsman stands on a cliff edge overlooking a vast ocean at sunset. Wind catches his cloak and hair. He unsheathes a glowing blade and takes a battle stance. Camera sweeps from behind to a dramatic low-angle frontal shot. Vibrant anime color palette, dynamic action lines, cel-shaded lighting.",
        "image_urls": ["https://example.com/anime-style-ref.jpg"],
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

> **[Try it now](https://fal.ai/models/bytedance/seedance-2.0/text-to-video)** - generate videos with these prompts via the Seedance 2.0 API on fal.ai.

---

## Output Format

All endpoints return the same response structure:

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/output/video.mp4"
  },
  "seed": 42
}
```

---

## Authentication

Set your fal API key as an environment variable:

```bash
export FAL_KEY="your_fal_api_key"
```

The fal client libraries automatically read `FAL_KEY` from the environment. See [fal.ai authentication docs](https://docs.fal.ai/clients/authentication) for more options.

---

## Examples

Complete runnable examples in Python and JavaScript:

| Example | Python | JavaScript |
|---|---|---|
| Text to Video | [text_to_video.py](examples/text_to_video.py) | [text_to_video.js](examples/text_to_video.js) |
| Image to Video | [image_to_video.py](examples/image_to_video.py) | [image_to_video.js](examples/image_to_video.js) |
| Reference to Video | [reference_to_video.py](examples/reference_to_video.py) | [reference_to_video.js](examples/reference_to_video.js) |

---

## Resources

- [Seedance 2.0 on fal.ai](https://fal.ai/models/bytedance/seedance-2.0/text-to-video) - Try it in the playground
- [fal.ai Documentation](https://docs.fal.ai) - Platform docs
- [Python Client](https://docs.fal.ai/clients/python) - `fal-client` reference
- [JavaScript Client](https://docs.fal.ai/clients/javascript) - `@fal-ai/client` reference
- [fal.ai Pricing](https://fal.ai/pricing) - Full pricing details

## Disclaimer

Seedance 2.0 is developed by ByteDance. [fal.ai](https://fal.ai) is an authorized provider of Seedance 2.0 API access. This repository contains documentation and examples for the fal.ai platform. Seedance is a trademark of ByteDance Ltd. For terms of use, see [fal.ai Terms of Service](https://fal.ai/terms).
