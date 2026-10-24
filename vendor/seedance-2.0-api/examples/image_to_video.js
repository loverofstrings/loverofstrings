/**
 * Seedance 2.0 - Image to Video
 *
 * Animate a static image into cinematic video with motion and audio.
 * https://fal.ai/models/bytedance/seedance-2.0/image-to-video
 */

import { fal } from "@fal-ai/client";

// Standard quality
const result = await fal.subscribe("bytedance/seedance-2.0/image-to-video", {
  input: {
    prompt:
      "The woman slowly turns her head and smiles, a gentle breeze moves her hair. Soft natural lighting.",
    image_url: "https://example.com/your-image.jpg",
    resolution: "720p",
    duration: "10",
    aspect_ratio: "auto",
    generate_audio: true,
  },
  logs: true,
  onQueueUpdate: (update) => {
    if (update.status === "IN_PROGRESS") {
      update.logs.map((log) => log.message).forEach(console.log);
    }
  },
});

console.log("Video URL:", result.data.video.url);
console.log("Seed:", result.data.seed);
