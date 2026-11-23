"""Mapillary SfM cluster -> point cloud package with projected photo observations.

Mapillary exposes a precomputed OpenSfM cluster as a zlib-compressed JSON blob.
It contains cameras, shots (poses), points and a reference LLA. There are no
per-point track IDs, so observations here are *projected*, not observed tracks:
the package is labelled `mapillary_sfm_projected` and must not be described as
surveyed or as COLMAP tracks.
"""
from __future__ import annotations

import argparse
import calendar
import json
import math
import shutil
import time
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def load_token(env_file: Path) -> str:
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("MAPILLARY_ACCESS_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("MAPILLARY_ACCESS_TOKEN missing")


def fetch_cluster(image_id: str, token: str, cache: Path) -> dict[str, Any]:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        raw = cache.read_bytes()
        return json.loads(zlib.decompress(raw))[0]
    url = "https://graph.mapillary.com/" + image_id + "?" + urllib.parse.urlencode({
        "access_token": token, "fields": "id,sfm_cluster",
    })
    meta = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "rail-pipeline/1.0"}), timeout=60))
    cluster = meta.get("sfm_cluster") or {}
    if not cluster.get("url"):
        raise RuntimeError(f"no sfm_cluster url for {image_id}")
    raw = urllib.request.urlopen(urllib.request.Request(cluster["url"], headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()
    cache.write_bytes(raw)
    return json.loads(zlib.decompress(raw))[0]


def rodrigues(r: list[float]) -> np.ndarray:
    v = np.asarray(r, float)
    th = float(np.linalg.norm(v))
    if th < 1e-12:
        return np.eye(3)
    k = v / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def _epoch(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def build_cluster_package(
    *, cluster: dict[str, Any], manifest_path: Path, work: Path, out: Path,
    site_id: str, site_name: str, top_k: int = 3,
) -> dict[str, Any]:
    work, out = Path(work), Path(out)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    photos = manifest.get("photos", [])
    by_seq: dict[str, list[dict[str, Any]]] = {}
    for p in photos:
        by_seq.setdefault(p.get("sequence") or "", []).append(p)

    matched: dict[str, dict[str, Any]] = {}
    for sk, shot in cluster.get("shots", {}).items():
        cand = by_seq.get(shot.get("skey") or "", [])
        if not cand:
            continue
        target = float(shot.get("capture_time") or 0)
        def dist(p):
            t = _epoch(p.get("captured_at"))
            return abs((t or 0) - target)
        best = min(cand, key=dist)
        if dist(best) <= 5.0:
            matched[sk] = best

    # Stable view order and a photo record for every used shot.
    used_photos: list[dict[str, Any]] = []
    photo_index: dict[str, int] = {}
    for sk in sorted(matched, key=lambda k: cluster["shots"][k].get("capture_time", 0)):
        p = matched[sk]
        pid = p["photo_id"]
        if pid not in photo_index:
            photo_index[pid] = len(used_photos)
            used_photos.append(p)

    cams = cluster.get("cameras", {})
    rows: list[list[float]] = []
    obs_offsets = [0]
    obs_photo: list[int] = []
    obs_u: list[float] = []
    obs_v: list[float] = []
    obs_residual: list[float] = []
    for pid, point in cluster.get("points", {}).items():
        X = np.asarray(point.get("coordinates", []), float)
        if X.shape != (3,) or not np.all(np.isfinite(X)):
            continue
        obs = []
        for sk, p in matched.items():
            shot = cluster["shots"][sk]
            cam = cams.get(shot.get("camera") or "")
            if not cam:
                continue
            R = rodrigues(shot.get("rotation", [0, 0, 0]))
            t = np.asarray(shot.get("translation", [0, 0, 0]), float)
            pc = R @ X + t
            if pc[2] <= 1e-6:
                continue
            f = float(cam.get("focal", 1.0)) * int(cam.get("width", 1))
            cx = int(cam.get("width", 1)) / 2
            cy = int(cam.get("height", 1)) / 2
            # Simple pinhole; Mapillary's k1/k2 are small and ignored for the marker.
            u = f * pc[0] / pc[2] + cx
            v = f * pc[1] / pc[2] + cy
            if not (0 <= u < cam["width"] and 0 <= v < cam["height"]):
                continue
            # Projection is in the original camera raster; the served photo is resized.
            sw = float(p.get("width") or cam["width"])
            sh = float(p.get("height") or cam["height"])
            obs.append((photo_index[p["photo_id"]], u * sw / cam["width"], v * sh / cam["height"],
                        1.0 / (1.0 + abs(u - cx) / cam["width"])))
        if not obs:
            continue
        obs.sort(key=lambda z: -z[3])
        rows.append([*X, *[float(c) for c in point.get("color", [180, 180, 180])[:3]], 255.0])
        for pidx, u, v, score in obs[:top_k]:
            obs_photo.append(pidx); obs_u.append(u); obs_v.append(v); obs_residual.append(1.0 - score)
        obs_offsets.append(len(obs_photo))

    out.mkdir(parents=True, exist_ok=True)
    (out / "photos").mkdir(parents=True, exist_ok=True)
    for rec in used_photos:
        src = work / "photos" / f"{rec['photo_id']}.jpg"
        if src.exists():
            shutil.copy2(src, out / "photos" / src.name)
    np.asarray(rows, dtype=np.float32).tofile(out / "points.bin")
    np.savez_compressed(
        out / "observations.npz",
        offsets=np.asarray(obs_offsets, dtype=np.int64),
        photo_idx=np.asarray(obs_photo, dtype=np.int32),
        u=np.asarray(obs_u, dtype=np.float32),
        v=np.asarray(obs_v, dtype=np.float32),
        residual=np.asarray(obs_residual, dtype=np.float32),
    )
    meta = {
        "schema_version": 1,
        "site_id": site_id,
        "site_name": site_name or site_id,
        "package_id": f"{site_id}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(rows),
        "members": ["unknown"],
        "units": "Mapillary SfM units",
        "scale_status": "relative",
        "scale_note": "Mapillary SfM cluster; no GCP verification in this package.",
        "link_method": "mapillary_sfm_projected",
        "note": "Mapillary SfM cluster; click observations are projections into registered Mapillary photos, not per-point tracks.",
        "site": {"source": "mapillary_sfm", "cluster_points": len(cluster.get("points", {})), "shots": len(cluster.get("shots", {}))},
        "photos": used_photos,
        "views": [{"id": p["photo_id"], "file": p["served_file"], "width": p.get("width", 0), "height": p.get("height", 0)} for p in used_photos],
        "stats": {"registered_images": len(used_photos), "points3d": len(rows), "observations": len(obs_photo), "cluster_points": len(cluster.get("points", {})), "shots": len(cluster.get("shots", {})), "matched_shots": len(matched)},
        "pipeline": "backend.app.modules.rail.mapillary_sfm",
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    qa = {
        "passed": len(rows) >= 200 and len(used_photos) >= 2,
        "gates": {"points": len(rows) >= 200, "views": len(used_photos) >= 2},
        "stats": meta["stats"],
        "note": "Projected Mapillary SfM cluster; no track residual gate.",
    }
    (out / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"meta": meta, "qa": qa}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--image-id", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--work", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--site-id", required=True)
    p.add_argument("--site-name", default="")
    p.add_argument("--env-file", default=".env")
    p.add_argument("--cache", default="")
    args = p.parse_args()
    token = load_token(Path(args.env_file))
    cache = Path(args.cache) if args.cache else Path(args.work) / "sfm_cluster.zlib"
    cluster = fetch_cluster(args.image_id, token, cache)
    result = build_cluster_package(
        cluster=cluster, manifest_path=Path(args.manifest), work=Path(args.work), out=Path(args.out),
        site_id=args.site_id, site_name=args.site_name,
    )
    print(json.dumps(result["qa"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
