"""fal.ai helpers: Nano Banana 2 stills + Seedance 2.0 animation."""

from __future__ import annotations

import os
import time
import urllib.request
from pathlib import Path
from typing import Iterable, Sequence


class FalError(RuntimeError):
    pass


def fal_key() -> str | None:
    return os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")


def fal_available() -> bool:
    return bool(fal_key())


def _ensure_client():
    if not fal_available():
        raise FalError(
            "FAL_KEY is not set. Add it to Cloud Agent environment secrets "
            "(fal.ai dashboard → API keys), then rerun."
        )
    # fal_client reads FAL_KEY; also accept FAL_API_KEY
    if not os.environ.get("FAL_KEY") and os.environ.get("FAL_API_KEY"):
        os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]
    try:
        import fal_client  # noqa: WPS433
    except ImportError as e:
        raise FalError("fal-client is not installed. Run: pip install fal-client") from e
    return fal_client


def upload_file(path: Path) -> str:
    """Upload a local file to fal storage; return a public URL."""
    fal_client = _ensure_client()
    path = Path(path)
    if not path.exists():
        raise FalError(f"Missing file: {path}")
    return fal_client.upload_file(str(path))


def download(url: str, dest: Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return dest


def generate_still(
    prompt: str,
    out: Path,
    *,
    image_urls: Sequence[str] | None = None,
    aspect_ratio: str = "9:16",
    resolution: str = "1K",
    num_images: int = 1,
) -> Path:
    """
    Text-to-image via fal-ai/nano-banana-2, or edit/reference via
    fal-ai/nano-banana-2/edit when image_urls are provided.
    """
    fal_client = _ensure_client()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if image_urls:
        endpoint = "fal-ai/nano-banana-2/edit"
        arguments = {
            "prompt": prompt,
            "image_urls": list(image_urls),
            "num_images": num_images,
            "aspect_ratio": aspect_ratio,
            "output_format": "jpeg",
            "resolution": resolution,
        }
    else:
        endpoint = "fal-ai/nano-banana-2"
        arguments = {
            "prompt": prompt,
            "num_images": num_images,
            "aspect_ratio": aspect_ratio,
            "output_format": "jpeg",
            "resolution": resolution,
        }

    result = fal_client.subscribe(endpoint, arguments=arguments)
    images = result.get("images") or []
    if not images:
        raise FalError(f"No images returned from {endpoint}: {result!r}")
    url = images[0]["url"]
    return download(url, out)


def animate_image(
    prompt: str,
    out: Path,
    *,
    image_url: str,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "9:16",
    generate_audio: bool = False,
    fast: bool = True,
) -> Path:
    """Image-to-video via Seedance 2.0 (fast tier by default)."""
    fal_client = _ensure_client()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = max(4, min(15, int(duration)))
    endpoint = (
        "bytedance/seedance-2.0/fast/image-to-video"
        if fast
        else "bytedance/seedance-2.0/image-to-video"
    )
    result = fal_client.subscribe(
        endpoint,
        arguments={
            "prompt": prompt,
            "image_url": image_url,
            "resolution": resolution,
            "duration": str(dur),
            "aspect_ratio": aspect_ratio,
            "generate_audio": generate_audio,
        },
    )
    video = result.get("video") or {}
    url = video.get("url")
    if not url:
        raise FalError(f"No video returned from {endpoint}: {result!r}")
    return download(url, out)


def reference_to_video(
    prompt: str,
    out: Path,
    *,
    image_urls: Sequence[str],
    audio_urls: Sequence[str] | None = None,
    duration: int = 10,
    resolution: str = "720p",
    aspect_ratio: str = "9:16",
    generate_audio: bool = False,
    fast: bool = True,
) -> Path:
    """Omni-modal Seedance 2.0 reference-to-video."""
    fal_client = _ensure_client()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = max(4, min(15, int(duration)))
    endpoint = (
        "bytedance/seedance-2.0/fast/reference-to-video"
        if fast
        else "bytedance/seedance-2.0/reference-to-video"
    )
    arguments: dict = {
        "prompt": prompt,
        "image_urls": list(image_urls),
        "resolution": resolution,
        "duration": str(dur),
        "aspect_ratio": aspect_ratio,
        "generate_audio": generate_audio,
    }
    if audio_urls:
        arguments["audio_urls"] = list(audio_urls)
    result = fal_client.subscribe(endpoint, arguments=arguments)
    video = result.get("video") or {}
    url = video.get("url")
    if not url:
        raise FalError(f"No video returned from {endpoint}: {result!r}")
    return download(url, out)


def upload_many(paths: Iterable[Path]) -> list[str]:
    urls: list[str] = []
    for p in paths:
        urls.append(upload_file(Path(p)))
        time.sleep(0.05)
    return urls
