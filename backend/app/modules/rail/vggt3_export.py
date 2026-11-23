"""VGG-T³ exporter: pointmap points keep their source pixel.

This is intentionally not presented as a multi-view track. Each exported point was
sampled from one VGGT depth map; its `u,v` is the pixel that generated it. The viewer
can therefore open the exact source frame and marker. Label `vggt_pointmap`.
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
    p.add_argument("--max-per-frame", type=int, default=3000)
    p.add_argument("--conf-quantile", type=float, default=0.60)
    p.add_argument("--target-size", type=int, default=518)
    args = p.parse_args()

    import torch
    from vggttt.nets.vggt.models.vggt import VGGT
    from vggttt.nets.vggt.img import load_and_preprocess_images

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    by_stem = {Path(p["served_file"]).stem: p for p in manifest["photos"]}
    paths = sorted(Path(args.images_dir).glob("*.jpg"))
    paths = [q for q in paths if q.stem in by_stem]
    if len(paths) < 2:
        raise SystemExit("need at least 2 manifest images")
    print(f"[vggt] {len(paths)} images")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" and torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    print(f"[vggt] device={device} dtype={dtype}")
    model = VGGT.from_pretrained("nvidia/vgg-ttt").eval().cuda()
    images = load_and_preprocess_images([str(q) for q in paths], mode="pad", target_size=args.target_size).to(device)
    with torch.no_grad():
        preds = model.infer(images, memory_efficient_inference=True)
    points3d = preds["pts3d"].detach().float().cpu().numpy()
    conf = preds["conf"].detach().float().cpu().numpy()
    print("[vggt3] pts3d", points3d.shape, "conf", conf.shape)

    # Save exactly the 518-square images used by VGGT, so u,v are exact.
    out = Path(args.out)
    photos = out / "photos"
    photos.mkdir(parents=True, exist_ok=True)
    img_np = (images.detach().cpu().permute(0, 2, 3, 1).numpy() * 255).astype(np.uint8)
    photo_records = []
    for i, path in enumerate(paths):
        pid = path.stem
        name = f"{pid}.jpg"
        Image.fromarray(img_np[i]).save(photos / name, "JPEG", quality=94)
        rec = dict(by_stem[pid])
        rec.update({"photo_id": pid, "served_file": f"photos/{name}", "width": args.target_size, "height": args.target_size})
        photo_records.append(rec)

    rows: list[list[float]] = []
    obs_offsets = [0]
    obs_photo: list[int] = []
    obs_u: list[float] = []
    obs_v: list[float] = []
    stride = max(1, args.stride)
    for i in range(depth.shape[0]):
        c = conf[i]
        if np.isfinite(c).any():
            thresh = float(np.quantile(c[np.isfinite(c)], args.conf_quantile))
        else:
            thresh = 0.0
        ys = np.arange(0, c.shape[0], stride)
        xs = np.arange(0, c.shape[1], stride)
        yy, xx = np.meshgrid(ys, xs, indexing="ij")
        valid = np.isfinite(c[yy, xx]) & (c[yy, xx] >= thresh)
        valid &= (img_np[i].mean(axis=2)[yy, xx] < 245)
        yy, xx = yy[valid], xx[valid]
        if len(yy) > args.max_per_frame:
            take = np.linspace(0, len(yy) - 1, args.max_per_frame).astype(int)
            yy, xx = yy[take], xx[take]
        pts = points3d[i][yy, xx]
        cols = img_np[i][yy, xx]
        for (x, y, p3, col) in zip(xx, yy, pts, cols):
            if not np.all(np.isfinite(p3)):
                continue
            if float(col.mean()) < 12:
                continue
            rows.append([float(p3[0]), float(p3[1]), float(p3[2]),
                         float(col[0]), float(col[1]), float(col[2]), 255.0])
            obs_photo.append(i)
            obs_u.append(float(x))
            obs_v.append(float(y))
            obs_offsets.append(len(obs_photo))

    rows_arr = np.asarray(rows, dtype=np.float32)
    rows_arr.tofile(out / "points.bin")
    np.savez_compressed(
        out / "observations.npz",
        offsets=np.asarray(obs_offsets, dtype=np.int64),
        photo_idx=np.asarray(obs_photo, dtype=np.int32),
        u=np.asarray(obs_u, dtype=np.float32),
        v=np.asarray(obs_v, dtype=np.float32),
        residual=np.zeros(len(obs_photo), dtype=np.float32),
    )
    stats = {
        "registered_images": len(photo_records),
        "points3d": len(rows),
        "observations": len(obs_photo),
        "confidence_quantile": args.conf_quantile,
        "source": "VGG-T³ depth pointmap (one source pixel per point)",
    }
    meta = {
        "schema_version": 1,
        "site_id": args.site_id,
        "site_name": args.site_name or manifest.get("site_name") or args.site_id,
        "package_id": f"{args.site_id}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(rows),
        "members": ["unknown"],
        "units": "model units",
        "scale_status": "relative",
        "scale_note": "No GCP; VGGT depth pointmap scale, not surveyed.",
        "link_method": "vggt3_pointmap",
        "note": "VGG-T³ pointmap from real source photographs. Each point opens its source pixel. Relative scale; not a survey.",
        "site": {"source": manifest.get("queries", [{}])[0].get("provider", "mapillary"), "queries": manifest.get("queries", [])},
        "photos": photo_records,
        "views": [{"id": r["photo_id"], "file": r["served_file"], "width": args.target_size, "height": args.target_size} for r in photo_records],
        "stats": stats,
        "pipeline": "backend.app.modules.rail.vggt3_export",
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    qa = {
        "passed": len(rows) >= 200 and len(photo_records) >= 2,
        "gates": {"points": len(rows) >= 200, "frames": len(photo_records) >= 2},
        "stats": stats,
        "note": "VGG-T³: no multi-view reprojection gate; click marker is the source pixel of the pointmap sample.",
    }
    (out / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(qa, ensure_ascii=False, indent=2))
    del model
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
