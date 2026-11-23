"""Site-aware point cloud packages (synthetic B-14 and real rail packages)."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np

from .config import DATA

SITES: dict[str, dict] = {
    "koma_bridge": {"dir": "koma_bridge", "name": "高麗川橋梁（八高線）", "kind": "real"},
    "koma_pi4": {"dir": "koma_pi4", "name": "高麗川橋梁（八高線・Pi4）", "kind": "real"},
}
DEFAULT_SITE = os.environ.get("POINTCLOUD_SITE", "koma_bridge")
_CACHE: dict[str, tuple] = {}


def pc_dir(site: str | None) -> Path:
    key = site or DEFAULT_SITE
    if key not in SITES:
        raise KeyError(f"unknown point cloud site: {key}")
    return DATA / "pointcloud" / SITES[key]["dir"]


def site_info(site: str | None) -> dict:
    key = site or DEFAULT_SITE
    if key not in SITES:
        raise KeyError(f"unknown point cloud site: {key}")
    d = pc_dir(key)
    return {"site": key, "name": SITES[key]["name"], "kind": SITES[key]["kind"],
            "available": (d / "meta.json").exists()}


def sites() -> list[dict]:
    keys = ["koma_bridge", "koma_pi4"]
    return [site_info(k) for k in keys if (pc_dir(k) / "meta.json").exists()]


def _load(site: str | None):
    key = site or DEFAULT_SITE
    if key in _CACHE:
        return _CACHE[key]
    d = pc_dir(key)
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    points = np.memmap(d / "points.bin", dtype=np.float32, mode="r").reshape(-1, 7)
    obs_path = d / "observations.npz"
    if obs_path.exists():
        cache = (meta, points, None, np.load(obs_path))
    else:
        cache = (meta, points, np.load(d / "views.npz"), None)
    _CACHE[key] = cache
    return cache


def meta(site: str | None = None):
    m, _, _, _ = _load(site)
    key = site or DEFAULT_SITE
    out = {**m, "site": key, "points_url": f"/api/pointcloud/points.bin?site={key}",
           "package_dir": pc_dir(key).name, "available_sites": sites()}
    dense = pc_dir(key) / "dense.bin"
    if dense.exists():
        out["dense_url"] = f"/api/pointcloud/dense.bin?site={key}"
        out["dense_count"] = dense.stat().st_size // (7 * 4)
    return out


def view_file(site: str | None, name: str) -> Path | None:
    m, _, _, _ = _load(site)
    for v in m.get("views", []):
        if v["id"] == name:
            return pc_dir(site) / v["file"]
    return None


def dense_file(site: str | None) -> Path | None:
    p = pc_dir(site) / "dense.bin"
    return p if p.exists() else None


def _look_at(eye, target):
    eye = np.asarray(eye, float); target = np.asarray(target, float)
    f = target - eye; f /= (np.linalg.norm(f) + 1e-9)
    up = np.array([0.0, 0.0, 1.0])
    s = np.cross(f, up); s /= (np.linalg.norm(s) + 1e-9)
    u = np.cross(s, f)
    return np.stack([s, u, -f]), eye


def _pick_observation(site: str | None, index: int, top_k: int):
    m, pts, depth, obs = _load(site)
    if index < 0 or index >= len(pts):
        raise IndexError("point index out of range")
    row = pts[index]
    offsets = obs["offsets"]
    start, end = int(offsets[index]), int(offsets[index + 1])
    views_by_id = {v["id"]: v for v in m.get("views", [])}
    photos = m.get("photos", [])
    out = []
    for i in range(start, end):
        pidx = int(obs["photo_idx"][i])
        if pidx < 0 or pidx >= len(photos):
            continue
        photo = photos[pidx]
        view = views_by_id.get(photo["photo_id"], {})
        w = int(view.get("width") or photo.get("width") or 0)
        h = int(view.get("height") or photo.get("height") or 0)
        u, v = float(obs["u"][i]), float(obs["v"][i])
        if not (0 <= u < w and 0 <= v < h):
            continue
        residual = float(obs["residual"][i]) if "residual" in obs else 0.0
        out.append({
            "image_id": photo["photo_id"],
            "url": f"/api/pointcloud/view/{photo['photo_id']}?site={site or DEFAULT_SITE}",
            "u": round(u, 1), "v": round(v, 1), "width": w, "height": h,
            "residual": round(residual, 3), "score": round(1.0 / (1.0 + residual), 4),
            "source_url": photo.get("source_url"), "captured_at": photo.get("captured_at"),
            "license": photo.get("license"), "artist": photo.get("artist"),
        })
    out.sort(key=lambda q: (q["residual"], -q["width"]))
    members = m.get("members", ["unknown"])
    mi = int(row[6])
    return {
        "index": index,
        "member": members[mi] if 0 <= mi < len(members) else "unknown",
        "site": m.get("site_name") or m.get("site_id"),
        "site_key": site or DEFAULT_SITE,
        "scale_status": m.get("scale_status", "relative"),
        "link_method": m.get("link_method", "colmap_track"),
        "color": [int(row[3]), int(row[4]), int(row[5])],
        "local": {"x": round(float(row[0]), 3), "y": round(float(row[1]), 3), "z": round(float(row[2]), 3)},
        "observation_count": end - start,
        "views": out[:top_k],
    }


def pick(site: str | None, index: int, top_k: int = 3):
    m, pts, depth, obs = _load(site)
    if obs is not None:
        return _pick_observation(site, index, top_k)
    if index < 0 or index >= len(pts):
        raise IndexError("point index out of range")
    row = pts[index]
    x, y, z = float(row[0]), float(row[1]), float(row[2])
    member = m["members"][int(row[6])]
    views = []
    for v in m["views"]:
        R, eye = _look_at(v["eye"], v["target"])
        pc = R @ (np.array([x, y, z]) - eye)
        d = -pc[2]
        if d <= 0.2:
            continue
        f = (v["height"] / 2) / math.tan(math.radians(v["fov"] / 2))
        u = f * pc[0] / d + v["width"] / 2
        vv = -f * pc[1] / d + v["height"] / 2
        if not (0 <= u < v["width"] and 0 <= vv < v["height"]):
            continue
        zb = float(depth[v["id"]][int(round(vv)), int(round(u))])
        if not (not np.isfinite(zb) or d <= zb + 0.35):
            continue
        views.append({
            "image_id": v["id"], "url": f"/api/pointcloud/view/{v['id']}?site={site or DEFAULT_SITE}",
            "u": round(u, 1), "v": round(vv, 1), "depth": round(d, 2),
            "width": v["width"], "height": v["height"],
            "score": round(1.0 / (1.0 + abs(d - 25.0) / 40.0), 3),
        })
    views.sort(key=lambda q: -q["score"])
    return {
        "index": index, "member": member, "site": m.get("site_name"),
        "site_key": site or DEFAULT_SITE, "scale_status": "relative", "link_method": "synthetic",
        "km": round(13150 + x, 1),
        "local": {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)},
        "color": [int(row[3]), int(row[4]), int(row[5])],
        "metrics": {"rail_offset_m": round(abs(abs(y) - 0.5335), 2),
                    "height_vs_rail_m": round(z - 8.72, 2), "scale_status": "relative"},
        "views": views[:top_k],
    }
