"""Token-free Wikimedia Commons discovery and image normalization.

The contract is deliberately provider-neutral:
  acquire(site, work) -> manifest.json + photos/*.jpg
A later adapter can replace Commons without changing reconstruction/packaging.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

API = "https://commons.wikimedia.org/w/api.php"
UA = "drone-poc-research/1.0 (real rail pipeline; local demo)"
MIN_WIDTH = 700
MIN_HEIGHT = 500


@dataclass
class Candidate:
    pageid: int
    title: str
    imageinfo: dict[str, Any]

    @property
    def photo_id(self) -> str:
        return f"commons-{self.pageid}"


def _request(params: dict[str, Any], retries: int = 5) -> dict[str, Any]:
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception as exc:
            if attempt == retries - 1:
                raise
            wait = 5 * (attempt + 1)
            print(f"[commons] API retry {attempt + 1}: {exc}; sleep {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def _download(url: str, dest: Path, retries: int = 6) -> None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if not data:
                raise RuntimeError("empty response")
            dest.write_bytes(data)
            return
        except Exception as exc:
            if attempt == retries - 1:
                raise
            wait = 10 * (attempt + 1)
            print(f"[commons] download retry {attempt + 1}: {exc}; sleep {wait}s")
            time.sleep(wait)


def _clean(value: Any) -> str:
    text = html.unescape(str(value or ""))
    return re.sub(r"<[^>]+>", "", text).strip()


def _license(info: dict[str, Any]) -> tuple[str, str, str]:
    meta = info.get("extmetadata") or {}
    lic = _clean((meta.get("LicenseShortName") or {}).get("value"))
    artist = _clean((meta.get("Artist") or {}).get("value"))
    captured = _clean((meta.get("DateTimeOriginal") or {}).get("value"))
    return lic, artist, captured


def _candidate(page: dict[str, Any]) -> Candidate | None:
    info = (page.get("imageinfo") or [{}])[0]
    mime = info.get("mime", "")
    if not mime.startswith("image/"):
        return None
    if mime in ("image/svg+xml", "image/gif"):
        return None
    if int(info.get("width") or 0) < MIN_WIDTH or int(info.get("height") or 0) < MIN_HEIGHT:
        return None
    return Candidate(int(page["pageid"]), page["title"], info)


def collect_category(category: str) -> list[Candidate]:
    if not category.startswith("Category:"):
        category = "Category:" + category
    data = _request({
        "action": "query", "generator": "categorymembers",
        "gcmtitle": category, "gcmtype": "file", "gcmlimit": "max",
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": "1600", "format": "json",
    })
    out = []
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        c = _candidate(page)
        if c:
            out.append(c)
    return out


def collect_geosearch(lat: float, lon: float, radius_m: int) -> list[Candidate]:
    data = _request({
        "action": "query", "generator": "geosearch",
        "ggscoord": f"{lat}|{lon}", "ggsradius": str(radius_m),
        "ggsnamespace": "6", "ggslimit": "50",
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": "1600", "format": "json",
    })
    out = []
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        c = _candidate(page)
        if c:
            out.append(c)
    return out


def _normalize(raw: bytes, dest: Path, max_width: int) -> tuple[int, int, str]:
    with Image.open(io.BytesIO(raw)) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > max_width:
            im.thumbnail((max_width, max_width), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "JPEG", quality=92, optimize=True)
        served = Image.open(dest)
        sw, sh = served.size
        served.close()
    return sw, sh, hashlib.sha256(raw).hexdigest()


def acquire(
    *,
    site_id: str,
    work: Path,
    site_name: str = "",
    category: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_m: int = 500,
    max_width: int = 1600,
    limit: int | None = None,
    cached_dir: Path | None = None,
) -> dict[str, Any]:
    """Discover, download, normalize and deduplicate images for one site."""
    work = Path(work)
    photos_dir = work / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = work / "manifest.json"

    candidates: list[Candidate] = []
    queries: list[dict[str, Any]] = []
    if category:
        candidates += collect_category(category)
        queries.append({"provider": "commons_category", "category": category})
    if lat is not None and lon is not None:
        candidates += collect_geosearch(lat, lon, radius_m)
        queries.append({"provider": "commons_geosearch", "lat": lat, "lon": lon, "radius_m": radius_m})

    # Deduplicate by pageid/title, preserving first provider.
    unique: dict[str, Candidate] = {}
    for c in candidates:
        unique.setdefault(c.photo_id, c)
    candidates = list(unique.values())
    if limit:
        candidates = candidates[:limit]

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "site_id": site_id,
        "site_name": site_name or site_id,
        "queries": queries,
        "photos": [],
        "errors": [],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if manifest_path.exists():
        try:
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
            if old.get("site_id") == site_id:
                manifest = old
        except Exception:
            pass

    known = {p["photo_id"]: p for p in manifest.get("photos", [])}
    hashes = {p.get("sha256") for p in manifest.get("photos", []) if p.get("sha256")}

    for idx, cand in enumerate(candidates, 1):
        pid = cand.photo_id
        if pid in known:
            continue
        info = cand.imageinfo
        title = cand.title[5:] if cand.title.startswith("File:") else cand.title
        # Special:Redirect serves an allowed thumbnail. Requesting a width larger
        # than the original redirects to upload.wikimedia.org, which returns 429.
        # Use a MediaWiki-approved bucket no larger than the original.
        allowed = [1920, 1280, 1024, 800, 640, 500, 320, 250]
        original_w = int(info.get("width") or max_width)
        target_w = next((w for w in allowed if w <= min(original_w, max(1920, max_width))), 250)
        url = ("https://commons.wikimedia.org/wiki/Special:Redirect/file/"
               + urllib.parse.quote(title, safe="()_,!~;@$&'*+=:")
               + f"?width={target_w}")
        if not info.get("url"):
            manifest["errors"].append({"photo_id": pid, "error": "no_url"})
            continue
        raw_path = work / "raw" / f"{pid}.jpg"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        cached = Path(cached_dir) / f"{cand.pageid}.jpg" if cached_dir else None
        try:
            if cached and cached.exists():
                raw = cached.read_bytes()
                raw_path.write_bytes(raw)
            else:
                if not raw_path.exists():
                    _download(url, raw_path)
                raw = raw_path.read_bytes()
            dest = photos_dir / f"{pid}.jpg"
            sw, sh, sha = _normalize(raw, dest, max_width)
            if sha in hashes:
                manifest["errors"].append({"photo_id": pid, "error": "duplicate_sha256"})
                continue
            lic, artist, captured = _license(info)
            record = {
                "photo_id": pid,
                "provider": "wikimedia_commons",
                "provider_id": str(cand.pageid),
                "title": cand.title,
                "source_url": info.get("descriptionurl") or "",
                "file_url": info.get("url") or "",
                "served_file": f"photos/{dest.name}",
                "width": sw,
                "height": sh,
                "original_width": info.get("width"),
                "original_height": info.get("height"),
                "sha256": sha,
                "license": lic,
                "artist": artist,
                "captured_at": captured,
            }
            manifest["photos"].append(record)
            known[pid] = record
            hashes.add(sha)
            print(f"[commons] {idx}/{len(candidates)} {pid} {sw}x{sh} {cand.title[:70]}")
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(0.5)
        except Exception as exc:
            manifest["errors"].append({"photo_id": pid, "error": str(exc)})
            print(f"[commons] FAILED {pid}: {exc}")
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest["counts"] = {
        "candidates": len(candidates),
        "downloaded": len(manifest.get("photos", [])),
        "errors": len(manifest.get("errors", [])),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
