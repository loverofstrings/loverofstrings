"""Seedance image-to-video via fal.ai (v1.5 Pro — accessible on this account)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import fal_client
import httpx


class SeedanceError(RuntimeError):
    pass


# Seedance 2.0 endpoints return resource_restricted on this key.
# v1.5 Pro image-to-video works.
I2V_MODEL = "fal-ai/bytedance/seedance/v1.5/pro/image-to-video"


def fal_key_available() -> bool:
    return bool(os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY"))


def _ensure_fal_env() -> None:
    if not os.environ.get("FAL_KEY") and os.environ.get("FAL_API_KEY"):
        os.environ["FAL_KEY"] = os.environ["FAL_API_KEY"]
    if not os.environ.get("FAL_KEY"):
        raise SeedanceError(
            "FAL_KEY is not set. Add your fal.ai API key, then rerun."
        )


def upload_image(path: Path) -> str:
    _ensure_fal_env()
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return fal_client.upload_file(str(path))


def image_to_video(
    image: Path,
    prompt: str,
    *,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "9:16",
    generate_audio: bool = False,
    fast: bool = True,  # kept for API compat; v1.5 pro is the working model
    end_image: Path | None = None,
    model: str = I2V_MODEL,
) -> str:
    """Animate a local still. Returns hosted video URL."""
    _ensure_fal_env()
    duration = max(4, min(12, int(duration)))
    image_url = upload_image(image)
    args: dict = {
        "prompt": prompt,
        "image_url": image_url,
        "resolution": resolution,
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
        "generate_audio": generate_audio,
    }
    if end_image is not None:
        args["end_image_url"] = upload_image(end_image)

    # Prefer REST queue — fal_client.subscribe ACL can falsely deny some models
    key = os.environ["FAL_KEY"]
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    submit = httpx.post(
        f"https://queue.fal.run/{model}",
        headers=headers,
        json=args,
        timeout=120.0,
    )
    if submit.status_code != 200:
        raise SeedanceError(f"Seedance submit failed: {submit.status_code} {submit.text[:400]}")
    data = submit.json()
    status_url = data["status_url"]
    response_url = data["response_url"]

    for _ in range(240):  # up to ~12 min per clip
        st = httpx.get(status_url, headers={"Authorization": f"Key {key}"}, timeout=60.0)
        status = st.json().get("status")
        if status == "COMPLETED":
            break
        if status in ("FAILED", "ERROR"):
            raise SeedanceError(f"Seedance job failed: {st.text[:400]}")
        time.sleep(3)
    else:
        raise SeedanceError("Seedance job timed out")

    res = httpx.get(response_url, headers={"Authorization": f"Key {key}"}, timeout=120.0)
    if res.status_code != 200:
        raise SeedanceError(f"Seedance result fetch failed: {res.status_code} {res.text[:400]}")
    body = res.json()
    video = (body or {}).get("video") or {}
    url = video.get("url")
    if not url:
        raise SeedanceError(f"No video URL in Seedance result: {body}")
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
