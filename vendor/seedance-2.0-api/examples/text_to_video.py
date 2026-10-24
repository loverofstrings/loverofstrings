"""
Seedance 2.0 - Text to Video

Generate cinematic AI video from a text prompt.
https://fal.ai/models/bytedance/seedance-2.0/text-to-video
"""

import fal_client


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])


# Standard quality
result = fal_client.subscribe(
    "bytedance/seedance-2.0/text-to-video",
    arguments={
        "prompt": "A slow-motion cinematic shot of a golden eagle soaring through a mountain valley at sunrise, volumetric fog rolling between the peaks.",
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


# Fast variant (lower cost, faster generation)
# result = fal_client.subscribe(
#     "bytedance/seedance-2.0/fast/text-to-video",
#     arguments={
#         "prompt": "A slow-motion cinematic shot of a golden eagle soaring through a mountain valley at sunrise.",
#         "resolution": "720p",
#         "duration": "10",
#         "aspect_ratio": "16:9",
#         "generate_audio": True,
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
# )
