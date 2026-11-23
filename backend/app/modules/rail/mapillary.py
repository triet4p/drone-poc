"""Mapillary image adapter (token from environment / .env, never logged)."""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

API = "https://graph.mapillary.com/images"
UA = "drone-poc-research/1.0 (rail pipeline)"


def load_token(env_file: Path | None = None) -> str | None:
    token = os.environ.get("MAPILLARY_ACCESS_TOKEN")
    if token:
        return token
    if env_file and Path(env_file).exists():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("MAPILLARY_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _get(lat: float, lon: float, radius_m: int, token: str, limit: int) -> list[dict[str, Any]]:
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * max(0.2, math.cos(math.radians(lat))))
    if dlat * 2 >= 0.009 or dlon * 2 >= 0.009:
        raise ValueError("radius too large for one Mapillary bbox; use <=400 m")
    bbox = f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}"
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": "id,geometry,computed_geometry,captured_at,sequence,camera_type,thumb_2048_url",
        "limit": str(min(limit, 100)),
    }
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r).get("data", []) or []
        except Exception as exc:
            if attempt == 3:
                raise
            wait = 5 * (attempt + 1)
            print(f"[mapillary] API retry {attempt + 1}: {type(exc).__name__}; sleep {wait}s")
            time.sleep(wait)
    return []


def acquire_mapillary(
    *,
    site_id: str,
    work: Path,
    lat: float,
    lon: float,
    radius_m: int = 200,
    site_name: str = "",
    limit: int = 100,
    width: int = 1600,
    env_file: Path | None = None,
    cached_dir: Path | None = None,
) -> dict[str, Any]:
    token = load_token(env_file)
    if not token:
        raise RuntimeError("MAPILLARY_ACCESS_TOKEN missing")
    work = Path(work)
    photos = work / "photos"
    photos.mkdir(parents=True, exist_ok=True)
    images = _get(lat, lon, radius_m, token, limit)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "site_id": site_id,
        "site_name": site_name or site_id,
        "queries": [{"provider": "mapillary", "lat": lat, "lon": lon, "radius_m": radius_m}],
        "photos": [],
        "errors": [],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    seen = set()
    for i, im in enumerate(images[:limit]):
        mid = str(im.get("id"))
        if not mid or mid in seen:
            continue
        seen.add(mid)
        url = im.get("thumb_2048_url")
        if not url:
            manifest["errors"].append({"photo_id": mid, "error": "no_thumb"})
            continue
        try:
            cached = None
            if cached_dir:
                for cand in (Path(cached_dir) / f"mapillary-{mid}.jpg", Path(cached_dir) / f"{mid}.jpg"):
                    if cand.exists():
                        cached = cand
                        break
            if cached:
                raw = cached.read_bytes()
            else:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    raw = r.read()
            with Image.open(io.BytesIO(raw)) as src:
                src = ImageOps.exif_transpose(src)
                if src.mode != "RGB":
                    src = src.convert("RGB")
                if max(src.size) > width:
                    src.thumbnail((width, width), Image.Resampling.LANCZOS)
                dest = photos / f"mapillary-{mid}.jpg"
                src.save(dest, "JPEG", quality=92, optimize=True)
                w, h = src.size
            cap = im.get("captured_at")
            captured = None
            if cap:
                captured = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(cap) / 1000))
            geo = im.get("computed_geometry") or im.get("geometry") or {}
            coords = (geo.get("coordinates") if isinstance(geo, dict) else None) or []
            manifest["photos"].append({
                "photo_id": f"mapillary-{mid}",
                "provider": "mapillary",
                "provider_id": mid,
                "title": f"Mapillary {mid}",
                "source_url": f"https://www.mapillary.com/app/?pKey={mid}",
                "file_url": url,
                "served_file": f"photos/{dest.name}",
                "width": w,
                "height": h,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "license": "Mapillary contributor terms",
                "artist": "Mapillary contributors",
                "captured_at": captured,
                "sequence": im.get("sequence"),
                "camera_type": im.get("camera_type"),
                "lon": coords[0] if len(coords) > 0 else None,
                "lat": coords[1] if len(coords) > 1 else None,
            })
            print(f"[mapillary] {i + 1}/{len(images)} {mid} {w}x{h}")
            (work / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(0.15)
        except Exception as exc:
            manifest["errors"].append({"photo_id": mid, "error": type(exc).__name__})
    manifest["counts"] = {
        "candidates": len(images),
        "downloaded": len(manifest["photos"]),
        "errors": len(manifest["errors"]),
    }
    (work / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
