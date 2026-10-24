"""
Seedance 2.0 - Reference to Video (Omni-Modal)

The most powerful Seedance 2.0 endpoint. Generate video conditioned on any
combination of reference images, videos, and audio. Supports style transfer,
lip-sync, motion transfer, character consistency, and multi-scene composition.

Use @Image1, @Video1, @Audio1 syntax in prompts to reference inputs.
Use scene cuts and timestamps in prompts to control pacing.

https://fal.ai/models/bytedance/seedance-2.0/reference-to-video
"""

import fal_client


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])


# -------------------------------------------------------------------
# Example 1: Character-consistent generation with image reference
# -------------------------------------------------------------------
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 walks confidently down a neon-lit city street at night, camera tracking alongside.",
        "image_urls": [
            "https://example.com/character-reference.jpg",
        ],
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)

print(f"Video URL: {result['video']['url']}")
print(f"Seed: {result['seed']}")


# -------------------------------------------------------------------
# Example 2: Style transfer from a reference image
# -------------------------------------------------------------------
# result = fal_client.subscribe(
#     "bytedance/seedance-2.0/reference-to-video",
#     arguments={
#         "prompt": "A bustling Tokyo street scene at night in the style of @Image1, neon reflections on wet pavement.",
#         "image_urls": ["https://example.com/art-style-reference.jpg"],
#         "resolution": "720p",
#         "duration": "10",
#         "aspect_ratio": "21:9",
#         "generate_audio": True,
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
# )


# -------------------------------------------------------------------
# Example 3: Lip-sync with audio reference
# -------------------------------------------------------------------
# result = fal_client.subscribe(
#     "bytedance/seedance-2.0/reference-to-video",
#     arguments={
#         "prompt": "@Image1 speaks directly to the camera in a professional studio setting while saying @Audio1.",
#         "image_urls": ["https://example.com/speaker.jpg"],
#         "audio_urls": ["https://example.com/speech.mp3"],
#         "resolution": "720p",
#         "duration": "10",
#         "aspect_ratio": "16:9",
#         "generate_audio": True,
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
# )


# -------------------------------------------------------------------
# Example 4: Motion transfer from video reference
# -------------------------------------------------------------------
# result = fal_client.subscribe(
#     "bytedance/seedance-2.0/reference-to-video",
#     arguments={
#         "prompt": "@Image1 performs the dance moves from @Video1 on a rooftop at sunset.",
#         "image_urls": ["https://example.com/dancer.jpg"],
#         "video_urls": ["https://example.com/dance-reference.mp4"],
#         "resolution": "720p",
#         "duration": "10",
#         "aspect_ratio": "16:9",
#         "generate_audio": True,
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
# )


# -------------------------------------------------------------------
# Example 5: Multi-scene composition with scene cuts
# -------------------------------------------------------------------
# result = fal_client.subscribe(
#     "bytedance/seedance-2.0/reference-to-video",
#     arguments={
#         "prompt": "@Image1 finds a football in the ocean and picks it up excitedly. Cut scene to @Image1 calling friends over. Cut scene to a group of characters playing football underwater.",
#         "image_urls": ["https://example.com/character.jpg"],
#         "resolution": "720p",
#         "duration": "15",
#         "aspect_ratio": "16:9",
#         "generate_audio": True,
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
# )


# -------------------------------------------------------------------
# Example 6: Full multi-modal - images + video + audio combined
# -------------------------------------------------------------------
# result = fal_client.subscribe(
#     "bytedance/seedance-2.0/reference-to-video",
#     arguments={
#         "prompt": "@Image1 performs the choreography from @Video1 on stage while @Audio1 plays in the background.",
#         "image_urls": ["https://example.com/performer.jpg"],
#         "video_urls": ["https://example.com/choreography.mp4"],
#         "audio_urls": ["https://example.com/background-music.mp3"],
#         "resolution": "720p",
#         "duration": "15",
#         "aspect_ratio": "16:9",
#         "generate_audio": True,
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
# )


# -------------------------------------------------------------------
# Fast variant (lower cost, faster generation)
# Use "bytedance/seedance-2.0/fast/reference-to-video" for any of the
# examples above. Same capabilities, same parameters.
# Video inputs receive a 0.6x price multiplier on both tiers.
# -------------------------------------------------------------------
