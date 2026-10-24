"""
Seedance 2.0 - Image to Video

Animate a static image into cinematic video with motion and audio.
https://fal.ai/models/bytedance/seedance-2.0/image-to-video
"""

import fal_client


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])


# Standard quality
result = fal_client.subscribe(
    "bytedance/seedance-2.0/image-to-video",
    arguments={
        "prompt": "The woman slowly turns her head and smiles, a gentle breeze moves her hair. Soft natural lighting.",
        "image_url": "https://example.com/your-image.jpg",
        "resolution": "720p",
        "duration": "10",
        "aspect_ratio": "auto",
        "generate_audio": True,
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)

print(f"Video URL: {result['video']['url']}")
print(f"Seed: {result['seed']}")


# With end frame (start-to-end image transition)
# result = fal_client.subscribe(
#     "bytedance/seedance-2.0/image-to-video",
#     arguments={
#         "prompt": "Smooth transition from day to night, the sky gradually darkens.",
#         "image_url": "https://example.com/start-frame.jpg",
#         "end_image_url": "https://example.com/end-frame.jpg",
#         "resolution": "720p",
#         "duration": "10",
#         "aspect_ratio": "16:9",
#         "generate_audio": True,
#     },
#     with_logs=True,
#     on_queue_update=on_queue_update,
# )
