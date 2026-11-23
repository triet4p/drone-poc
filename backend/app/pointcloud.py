"""Synthetic point cloud service: metadata, binary points, camera pick."""
import json, math, os
from pathlib import Path

import numpy as np

from .config import DATA

_DEFAULT = DATA / "pointcloud" / "demo"
PC = Path(os.environ.get("POINTCLOUD_DIR", str(_DEFAULT)))
if not PC.is_absolute():
    PC = (DATA.parent / PC).resolve()
_meta = None
_points = None
_depth = None
_obs = None


def _load():
    global _meta, _points, _depth, _obs
    if _meta is None:
        _meta = json.loads((PC / "meta.json").read_text(encoding="utf-8"))
        _points = np.memmap(PC / "points.bin", dtype=np.float32, mode="r").reshape(-1, 7)
        obs_path = PC / "observations.npz"
        if obs_path.exists():
            _obs = np.load(obs_path)
            _depth = None
        else:
            _depth = np.load(PC / "views.npz")
    return _meta, _points, _depth


def meta():
    m, _, _ = _load()
    out = {**m, "points_url": "/api/pointcloud/points.bin", "package_dir": PC.name}
    dense = PC / "dense.bin"
    if dense.exists():
        out["dense_url"] = "/api/pointcloud/dense.bin"
        out["dense_count"] = dense.stat().st_size // (7 * 4)
    return out


def view_file(name: str) -> Path | None:
    m, _, _ = _load()
    for v in m["views"]:
        if v["id"] == name:
            return PC / v["file"]
    return None


def _look_at(eye, target):
    eye = np.asarray(eye, float); target = np.asarray(target, float)
    f = target - eye; f /= (np.linalg.norm(f) + 1e-9)
    up = np.array([0.0, 0.0, 1.0])
    s = np.cross(f, up); s /= (np.linalg.norm(s) + 1e-9)
    u = np.cross(s, f)
    return np.stack([s, u, -f]), eye


def _pick_observation(index: int, top_k: int):
    m, pts, _ = _load()
    if _obs is None:
        raise RuntimeError("observations not loaded")
    if index < 0 or index >= len(pts):
        raise IndexError("point index out of range")
    row = pts[index]
    offsets = _obs["offsets"]
    start, end = int(offsets[index]), int(offsets[index + 1])
    photos = {p["photo_id"]: p for p in m.get("photos", [])}
    views_by_id = {v["id"]: v for v in m.get("views", [])}
    out = []
    for i in range(start, end):
        pidx = int(_obs["photo_idx"][i])
        if pidx < 0 or pidx >= len(m.get("photos", [])):
            continue
        photo = m["photos"][pidx]
        view = views_by_id.get(photo["photo_id"], {})
        w = int(view.get("width") or photo.get("width") or 0)
        h = int(view.get("height") or photo.get("height") or 0)
        u = float(_obs["u"][i]); v = float(_obs["v"][i])
        if not (0 <= u < w and 0 <= v < h):
            continue
        residual = float(_obs["residual"][i]) if "residual" in _obs else 0.0
        out.append({
            "image_id": photo["photo_id"],
            "url": f"/api/pointcloud/view/{photo['photo_id']}",
            "u": round(u, 1), "v": round(v, 1),
            "width": w, "height": h,
            "residual": round(residual, 3),
            "score": round(1.0 / (1.0 + residual), 4),
            "source_url": photo.get("source_url"),
            "captured_at": photo.get("captured_at"),
            "license": photo.get("license"),
            "artist": photo.get("artist"),
        })
    out.sort(key=lambda q: (q["residual"], -q["width"]))
    return {
        "index": index,
        "member": m.get("members", ["unknown"])[int(row[6])] if int(row[6]) < len(m.get("members", [])) else "unknown",
        "site": m.get("site_name") or m.get("site_id"),
        "scale_status": m.get("scale_status", "relative"),
        "link_method": m.get("link_method", "colmap_track"),
        "color": [int(row[3]), int(row[4]), int(row[5])],
        "local": {"x": round(float(row[0]), 3), "y": round(float(row[1]), 3), "z": round(float(row[2]), 3)},
        "observation_count": end - start,
        "views": out[:top_k],
    }


def pick(index: int, top_k: int = 3):
    m, pts, depth = _load()
    if _obs is not None:
        return _pick_observation(index, top_k)
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
        visible = (not np.isfinite(zb)) or d <= zb + 0.35
        if not visible:
            continue
        views.append({
            "image_id": v["id"], "url": f"/api/pointcloud/view/{v['id']}",
            "u": round(u, 1), "v": round(vv, 1), "depth": round(d, 2),
            "width": v["width"], "height": v["height"],
            "score": round(1.0 / (1.0 + abs(d - 25.0) / 40.0), 3),
        })
    views.sort(key=lambda q: -q["score"])
    return {
        "index": index,
        "member": member,
        "km": round(13150 + x, 1),
        "local": {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)},
        "color": [int(row[3]), int(row[4]), int(row[5])],
        "metrics": {
            "rail_offset_m": round(abs(abs(y) - 0.5335), 2),
            "height_vs_rail_m": round(z - 8.72, 2),
            "scale_status": "relative",
        },
        "views": views[:top_k],
    }
