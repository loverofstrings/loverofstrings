"""Seedance 2.0 (fal.ai) image-to-video for storyboard stills."""

from __future__ import annotations

import os
import time
from pathlib import Path

import fal_client


class SeedanceError(RuntimeError):
    pass


# Prefer fast tier for 28-scene batch cost/latency
I2V_FAST = "bytedance/seedance-2.0/fast/image-to-video"
I2V_STD = "bytedance/seedance-2.0/image-to-video"


def fal_key_available() -> bool:
    return bool(os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY"))


def _ensure_fal_env() -> None:
    # fal-client reads FAL_KEY; accept FAL_API_KEY as alias
    if not os.environ.get("FAL_KEY") and os.environ.get("FAL_API_KEY"):
        os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]
    if not os.environ.get("FAL_KEY"):
        raise SeedanceError(
            "FAL_KEY is not set. Add your fal.ai API key as Cloud Agent secret "
            "FAL_KEY (see Seedance .env.example), then rerun."
        )


def upload_image(path: Path) -> str:
    _ensure_fal_env()
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    url = fal_client.upload_file(str(path))
    return url


def image_to_video(
    image: Path,
    prompt: str,
    *,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "9:16",
    generate_audio: bool = False,
    fast: bool = True,
    end_image: Path | None = None,
) -> str:
    """
    Animate a local still with Seedance 2.0. Returns hosted video URL.
    """
    _ensure_fal_env()
    duration = max(4, min(15, int(duration)))
    image_url = upload_image(image)
    args = {
        "prompt": prompt,
        "image_url": image_url,
        "resolution": resolution,
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
        "generate_audio": generate_audio,
    }
    if end_image is not None:
        args["end_image_url"] = upload_image(end_image)

    model = I2V_FAST if fast else I2V_STD

    def _on_update(update) -> None:
        if isinstance(update, fal_client.InProgress):
            for log in update.logs or []:
                msg = log.get("message") if isinstance(log, dict) else None
                if msg:
                    print(f"  [seedance] {msg}", flush=True)

    try:
        result = fal_client.subscribe(
            model,
            arguments=args,
            with_logs=True,
            on_queue_update=_on_update,
        )
    except Exception as exc:  # noqa: BLE001
        raise SeedanceError(f"Seedance subscribe failed: {exc}") from exc

    video = (result or {}).get("video") or {}
    url = video.get("url")
    if not url:
        raise SeedanceError(f"No video URL in Seedance result: {result}")
    return url


def download_video(url: str, dest: Path, retries: int = 3) -> Path:
    import urllib.request

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            urllib.request.urlretrieve(url, dest)
            if dest.stat().st_size > 1000:
                return dest
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(2 ** attempt)
    raise SeedanceError(f"Failed to download {url}: {last_err}")
