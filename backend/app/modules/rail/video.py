"""Video adapter: real frame acquisition for a named rail site.

The output manifest is identical to the Commons adapter, so reconstruction and
packaging do not know which provider produced the photographs.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from PIL import Image


def _probe(video: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video),
    ], text=True).strip()
    return float(out)


def acquire_video(
    *,
    site_id: str,
    work: Path,
    video: Path,
    site_name: str = "",
    start: float = 0.0,
    end: float | None = None,
    every_s: float = 1.5,
    width: int = 1600,
    crop: str | None = None,
    source_url: str = "",
    license: str = "",
    artist: str = "",
) -> dict[str, Any]:
    video = Path(video)
    if not video.exists():
        raise FileNotFoundError(video)
    work = Path(work)
    photos = work / "photos"
    photos.mkdir(parents=True, exist_ok=True)
    duration = _probe(video)
    stop = duration if end is None else min(end, duration)
    if stop <= start:
        raise ValueError("empty video interval")
    pattern = photos / "video-%05d.jpg"
    vf = (f"crop={crop}," if crop else "") + f"fps=1/{every_s},scale='min({width},iw)':-2"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(start), "-to", str(stop), "-i", str(video),
        "-vf", vf, "-q:v", "2", str(pattern),
    ], check=True)

    records = []
    for i, path in enumerate(sorted(photos.glob("video-*.jpg"))):
        with Image.open(path) as im:
            w, h = im.size
        records.append({
            "photo_id": path.stem,
            "provider": "video_frame",
            "provider_id": f"{video.name}#{start + i * every_s:.3f}",
            "title": f"{site_name or site_id} frame {i}",
            "source_url": source_url,
            "file_url": source_url,
            "served_file": f"photos/{path.name}",
            "width": w,
            "height": h,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "license": license,
            "artist": artist,
            "captured_at": f"video t={start + i * every_s:.2f}s",
        })
    manifest = {
        "schema_version": 1,
        "site_id": site_id,
        "site_name": site_name or site_id,
        "queries": [{
            "provider": "video", "file": video.name, "start_s": start,
            "end_s": stop, "every_s": every_s, "source_url": source_url,
        }],
        "photos": records,
        "errors": [],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": {"candidates": len(records), "downloaded": len(records), "errors": 0},
    }
    (work / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
