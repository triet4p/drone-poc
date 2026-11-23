"""COLMAP sparse reconstruction and click-to-photo package export."""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np


def _run(cmd: list[str], log_path: Path) -> None:
    print("[colmap] " + " ".join(cmd))
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n$ " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"COLMAP command failed ({proc.returncode}): {' '.join(cmd)}")


def run_colmap(
    *,
    site_id: str,
    work: Path,
    colmap_bin: str = "colmap",
    use_gpu: bool = False,
    camera_model: str = "SIMPLE_RADIAL",
    overwrite: bool = False,
) -> Path:
    """Run feature extraction, exhaustive matching and sparse mapping.

    Returns the directory containing COLMAP text output.
    """
    work = Path(work)
    photos = work / "photos"
    if not photos.is_dir():
        raise FileNotFoundError(f"missing photos directory: {photos}")
    db = work / "database.db"
    sparse = work / "sparse"
    txt = work / "sparse_txt"
    if overwrite:
        for p in (db, sparse, txt):
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
    sparse.mkdir(parents=True, exist_ok=True)
    txt.mkdir(parents=True, exist_ok=True)
    log = work / "colmap.log"
    log.write_text("", encoding="utf-8")

    gpu = "1" if use_gpu else "0"
    _run([
        colmap_bin, "feature_extractor",
        "--database_path", str(db),
        "--image_path", str(photos),
        "--ImageReader.camera_model", camera_model,
        "--ImageReader.single_camera", "0",
        "--SiftExtraction.use_gpu", gpu,
    ], log)
    _run([
        colmap_bin, "exhaustive_matcher",
        "--database_path", str(db),
        "--SiftMatching.use_gpu", gpu,
    ], log)
    _run([
        colmap_bin, "mapper",
        "--database_path", str(db),
        "--image_path", str(photos),
        "--output_path", str(sparse),
    ], log)

    models = sorted([p for p in sparse.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not models:
        raise RuntimeError("COLMAP mapper produced no model")
    model = models[0]
    _run([
        colmap_bin, "model_converter",
        "--input_path", str(model),
        "--output_path", str(txt),
        "--output_type", "TXT",
    ], log)
    return txt


def _read_cameras(path: Path) -> dict[int, dict[str, Any]]:
    cams: dict[int, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        cid = int(parts[0])
        cams[cid] = {
            "model": parts[1], "width": int(parts[2]), "height": int(parts[3]),
            "params": [float(x) for x in parts[4:]],
        }
    return cams


def _read_images(path: Path) -> tuple[dict[int, dict[str, Any]], dict[tuple[int, int], tuple[float, float]]]:
    """Return image metadata and (image_id, point2D_idx) -> observed pixel."""
    images: dict[int, dict[str, Any]] = {}
    points2d: dict[tuple[int, int], tuple[float, float]] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 10:
            continue
        iid = int(parts[0])
        images[iid] = {
            "qvec": [float(x) for x in parts[1:5]],
            "tvec": [float(x) for x in parts[5:8]],
            "camera_id": int(parts[8]),
            "name": " ".join(parts[9:]),
        }
        if i < len(lines):
            obs_line = lines[i].strip()
            i += 1
            obs = obs_line.split() if obs_line else []
            for j in range(0, len(obs) - 2, 3):
                try:
                    x, y, pid = float(obs[j]), float(obs[j + 1]), int(obs[j + 2])
                except ValueError:
                    break
                if pid > 0:
                    points2d[(iid, j // 3)] = (x, y)
    return images, points2d


def _read_points(path: Path) -> dict[int, dict[str, Any]]:
    points: dict[int, dict[str, Any]] = {}
    if not path.exists():
        return points
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        pid = int(parts[0])
        xyz = [float(x) for x in parts[1:4]]
        rgb = [int(x) for x in parts[4:7]]
        err = float(parts[7])
        track = []
        rest = parts[8:]
        for j in range(0, len(rest) - 1, 2):
            try:
                track.append((int(rest[j]), int(rest[j + 1])))
            except ValueError:
                break
        points[pid] = {"xyz": xyz, "rgb": rgb, "error": err, "track": track}
    return points


def export_package(
    *,
    site_id: str,
    work: Path,
    out: Path,
    min_track: int = 2,
    min_registered: int = 6,
    min_points: int = 200,
) -> dict[str, Any]:
    """Convert COLMAP text output into the app's observation-mode package."""
    work = Path(work)
    out = Path(out)
    manifest = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
    txt = work / "sparse_txt"
    cameras = _read_cameras(txt / "cameras.txt")
    images, points2d = _read_images(txt / "images.txt")
    points = _read_points(txt / "points3D.txt")

    # Keep a stable photo order: COLMAP image id order.
    photo_records = {p["photo_id"]: p for p in manifest.get("photos", [])}
    image_ids = sorted(images.keys())
    photo_order: list[dict[str, Any]] = []
    image_to_photo_idx: dict[int, int] = {}
    for iid in image_ids:
        name = Path(images[iid]["name"]).name
        pid = Path(name).stem
        rec = photo_records.get(pid)
        if not rec:
            continue
        cam = cameras.get(images[iid]["camera_id"], {})
        image_to_photo_idx[iid] = len(photo_order)
        photo_order.append({
            "photo_id": pid,
            "provider": rec.get("provider"),
            "provider_id": rec.get("provider_id"),
            "source_url": rec.get("source_url"),
            "license": rec.get("license"),
            "artist": rec.get("artist"),
            "captured_at": rec.get("captured_at"),
            "sha256": rec.get("sha256"),
            "served_file": f"photos/{pid}.jpg",
            "width": int(cam.get("width") or rec.get("width") or 0),
            "height": int(cam.get("height") or rec.get("height") or 0),
            "camera_model": cam.get("model"),
            "camera_params": cam.get("params"),
        })

    rows: list[list[float]] = []
    obs_offsets: list[int] = [0]
    obs_photo: list[int] = []
    obs_u: list[float] = []
    obs_v: list[float] = []
    obs_residual: list[float] = []
    dropped = {"track_too_short": 0, "missing_image": 0, "out_of_bounds": 0}

    for pid in sorted(points.keys()):
        p = points[pid]
        valid: list[tuple[int, float, float]] = []
        for iid, p2d_idx in p["track"]:
            if iid not in image_to_photo_idx:
                dropped["missing_image"] += 1
                continue
            uv = points2d.get((iid, p2d_idx))
            if uv is None:
                dropped["missing_image"] += 1
                continue
            idx = image_to_photo_idx[iid]
            w = photo_order[idx]["width"]
            h = photo_order[idx]["height"]
            u, v = uv
            if not (0 <= u < w and 0 <= v < h):
                dropped["out_of_bounds"] += 1
                continue
            valid.append((idx, u, v))
        if len(valid) < min_track:
            dropped["track_too_short"] += 1
            continue
        rows.append([p["xyz"][0], p["xyz"][1], p["xyz"][2],
                     p["rgb"][0], p["rgb"][1], p["rgb"][2], 255.0])
        for idx, u, v in valid:
            obs_photo.append(idx)
            obs_u.append(u)
            obs_v.append(v)
            obs_residual.append(p["error"])
        obs_offsets.append(len(obs_photo))

    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work / "manifest.json", out / "source_manifest.json")
    (out / "photos").mkdir(parents=True, exist_ok=True)
    for rec in photo_order:
        src = work / "photos" / f"{rec['photo_id']}.jpg"
        if src.exists():
            shutil.copy2(src, out / "photos" / src.name)

    rows_arr = np.asarray(rows, dtype=np.float32)
    if rows_arr.size == 0:
        rows_arr = np.zeros((0, 7), dtype=np.float32)
    rows_arr.tofile(out / "points.bin")
    np.savez_compressed(
        out / "observations.npz",
        offsets=np.asarray(obs_offsets, dtype=np.int64),
        photo_idx=np.asarray(obs_photo, dtype=np.int32),
        u=np.asarray(obs_u, dtype=np.float32),
        v=np.asarray(obs_v, dtype=np.float32),
        residual=np.asarray(obs_residual, dtype=np.float32),
    )

    residuals = np.asarray(obs_residual, dtype=np.float32)
    median_residual = float(np.median(residuals)) if residuals.size else None
    stats = {
        "registered_images": len(photo_order),
        "points3d": len(rows),
        "observations": len(obs_photo),
        "median_residual_px": None if median_residual is None else round(median_residual, 4),
        "dropped": dropped,
    }
    gates = {
        "registered_images": stats["registered_images"] >= min_registered,
        "points": stats["points3d"] >= min_points,
        "observations_per_point": bool(rows) and all(
            (obs_offsets[i + 1] - obs_offsets[i]) >= min_track for i in range(len(rows))
        ),
        "median_residual": median_residual is not None and median_residual <= 2.0,
    }
    qa = {"passed": all(gates.values()), "gates": gates, "stats": stats}
    (out / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = {
        "schema_version": 1,
        "site_id": site_id,
        "site_name": manifest.get("site_name") or site_id,
        "package_id": f"{site_id}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(rows),
        "members": ["unknown"],
        "units": "model units",
        "scale_status": "relative",
        "scale_note": "No GCP or surveyed anchor in this pilot package.",
        "link_method": "colmap_track",
        "note": "Photogrammetric sparse cloud from real Wikimedia Commons photographs. Relative scale; not a survey.",
        "site": {"source": "wikimedia_commons", "queries": manifest.get("queries", [])},
        "photos": photo_order,
        "views": [
            {"id": p["photo_id"], "file": p["served_file"], "width": p["width"], "height": p["height"]}
            for p in photo_order
        ],
        "stats": stats,
        "pipeline": "backend.app.modules.rail",
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"meta": meta, "qa": qa}
