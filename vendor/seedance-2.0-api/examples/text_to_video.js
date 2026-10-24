/**
 * Seedance 2.0 - Text to Video
 *
 * Generate cinematic AI video from a text prompt.
 * https://fal.ai/models/bytedance/seedance-2.0/text-to-video
 */

import { fal } from "@fal-ai/client";

// Standard quality
const result = await fal.subscribe("bytedance/seedance-2.0/text-to-video", {
  input: {
    prompt:
      "A slow-motion cinematic shot of a golden eagle soaring through a mountain valley at sunrise, volumetric fog rolling between the peaks.",
    resolution: "720p",
    duration: "10",
    aspect_ratio: "16:9",
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
