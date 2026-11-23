"""Pi4 fallback: pointmap points keep the source frame pixel.

Pi4 is a learned pointmap model; this is not a COLMAP track. Every exported point
was sampled from one source frame, so clicking it opens that exact frame/pixel.
Label `pi4_pointmap`; no survey/reprojection claim.
"""
from __future__ import annotations

import argparse
import gc
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--images-dir", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--site-id", required=True)
    p.add_argument("--site-name", default="")
    p.add_argument("--stride", type=int, default=4)
    p.add_argument("--max-per-frame", type=int, default=2500)
    p.add_argument("--conf-quantile", type=float, default=0.50)
    p.add_argument("--max-frames", type=int, default=16)
    p.add_argument("--max-size", type=int, default=512)
    args = p.parse_args()

    import torch
    from pi4 import Pi4
    from pi4.io import load_images

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    by_stem = {Path(p["served_file"]).stem: p for p in manifest["photos"]}
    paths = sorted(Path(args.images_dir).glob("*.jpg"))
    paths = [q for q in paths if q.stem in by_stem][: args.max_frames]
    if len(paths) < 2:
        raise SystemExit("need at least 2 manifest images")
    frame_dir = Path(args.out) / "_input"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for q in paths:
        Image.open(q).convert("RGB").save(frame_dir / f"{q.stem}.jpg", "JPEG", quality=94)
    print(f"[pi4] {len(paths)} images")

    frames, _ = load_images(str(frame_dir), stride=1, max_frames=None, max_size=args.max_size)
    images = torch.from_numpy(frames.copy()).permute(0, 3, 1, 2).float().div(255).unsqueeze(0).cuda()
    model = Pi4.from_pretrained("yyfz233/Pi4").cuda()
    with torch.no_grad():
        pred = model(images, query_frame=None)
    pts = pred["local_points"][0].detach().float().cpu().numpy()
    conf = pred["confidence"][0].detach().float().cpu().numpy()
    cams = pred["camera_poses"][0].detach().float().cpu().numpy()
    scale = float(pred.get("metric_scale", 1.0))
    print("[pi4] points", pts.shape, "cams", cams.shape, "scale", scale)

    out = Path(args.out)
    photos = out / "photos"
    photos.mkdir(parents=True, exist_ok=True)
    records = []
    for i, q in enumerate(paths):
        pid = q.stem
        Image.fromarray(frames[i]).save(photos / f"{pid}.jpg", "JPEG", quality=94)
        rec = dict(by_stem[pid])
        rec.update({"photo_id": pid, "served_file": f"photos/{pid}.jpg", "width": int(frames.shape[2]), "height": int(frames.shape[1])})
        records.append(rec)

    rows: list[list[float]] = []
    offs = [0]
    op: list[int] = []
    ou: list[float] = []
    ov: list[float] = []
    stride = max(1, args.stride)
    S, H, W, _ = pts.shape
    for i in range(S):
        c = conf[i]
        if np.isfinite(c).any():
            thresh = float(np.quantile(c[np.isfinite(c)], args.conf_quantile))
        else:
            thresh = 0.0
        yy, xx = np.meshgrid(np.arange(0, H, stride), np.arange(0, W, stride), indexing="ij")
        valid = np.isfinite(c[yy, xx]) & (c[yy, xx] >= thresh)
        yy, xx = yy[valid], xx[valid]
        if len(yy) > args.max_per_frame:
            take = np.linspace(0, len(yy) - 1, args.max_per_frame).astype(int)
            yy, xx = yy[take], xx[take]
        local = pts[i][yy, xx]
        # Pi4 visualization convention: world = (local * scale) @ R^T + t
        R = cams[i, :3, :3]
        t = cams[i, :3, 3]
        world = (local * scale) @ R.T + t
        cols = frames[i][yy, xx].astype(np.float32)
        for x, y, w, col in zip(xx, yy, world, cols):
            if not np.all(np.isfinite(w)):
                continue
            if float(col.mean()) < 10:
                continue
            rows.append([float(w[0]), float(w[1]), float(w[2]), float(col[0]), float(col[1]), float(col[2]), 255.0])
            op.append(i); ou.append(float(x)); ov.append(float(y)); offs.append(len(op))

    arr = np.asarray(rows, dtype=np.float32)
    arr.tofile(out / "points.bin")
    np.savez_compressed(out / "observations.npz",
        offsets=np.asarray(offs, dtype=np.int64), photo_idx=np.asarray(op, dtype=np.int32),
        u=np.asarray(ou, dtype=np.float32), v=np.asarray(ov, dtype=np.float32),
        residual=np.zeros(len(op), dtype=np.float32))
    stats = {"registered_images": len(records), "points3d": len(rows), "observations": len(op),
             "confidence_quantile": args.conf_quantile, "pi4_scale": scale,
             "source": "Pi4 local pointmaps; one source pixel per point"}
    meta = {
        "schema_version": 1, "site_id": args.site_id, "site_name": args.site_name or args.site_id,
        "package_id": f"{args.site_id}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(rows), "members": ["unknown"], "units": "model units",
        "scale_status": "relative", "scale_note": "Pi4 predicted scale; no GCP verification.",
        "link_method": "pi4_pointmap",
        "note": "Pi4 pointmap from real source photographs. Each point opens its source pixel. Relative scale; not a survey.",
        "site": {"source": "pi4", "queries": manifest.get("queries", [])},
        "photos": records,
        "views": [{"id": r["photo_id"], "file": r["served_file"], "width": r["width"], "height": r["height"]} for r in records],
        "stats": stats, "pipeline": "backend.app.modules.rail.pi4_export",
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    qa = {"passed": len(rows) >= 200 and len(records) >= 2,
          "gates": {"points": len(rows) >= 200, "frames": len(records) >= 2},
          "stats": stats, "note": "Pi4 fallback: no multi-view reprojection gate."}
    (out / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(qa, ensure_ascii=False, indent=2))
    del model
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
