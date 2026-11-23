"""CLI for the reusable rail acquisition/reconstruction pipeline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .commons import acquire
from .colmap import export_package, run_colmap


def cmd_acquire(args) -> None:
    manifest = acquire(
        site_id=args.site_id,
        site_name=args.site_name or args.site_id,
        work=Path(args.work),
        category=args.category,
        lat=args.lat,
        lon=args.lon,
        radius_m=args.radius_m,
        max_width=args.width,
        limit=args.limit,
        cached_dir=Path(args.cached_dir) if args.cached_dir else None,
    )
    print(json.dumps(manifest.get("counts"), ensure_ascii=False))


def cmd_reconstruct(args) -> None:
    work = Path(args.work)
    if not (work / "sparse_txt" / "images.txt").exists() or args.overwrite:
        run_colmap(
            site_id=args.site_id,
            work=work,
            colmap_bin=args.colmap,
            use_gpu=args.gpu,
            camera_model=args.camera_model,
            overwrite=args.overwrite,
        )
    result = export_package(
        site_id=args.site_id,
        work=work,
        out=Path(args.out),
        min_track=args.min_track,
        min_registered=args.min_registered,
        min_points=args.min_points,
    )
    print(json.dumps(result["qa"], ensure_ascii=False, indent=2))


def cmd_inspect(args) -> None:
    out = Path(args.out)
    for name in ("meta.json", "qa.json"):
        p = out / name
        if p.exists():
            print(f"--- {name} ---")
            print(p.read_text(encoding="utf-8"))
    manifest = Path(args.work) / "manifest.json"
    if manifest.exists():
        m = json.loads(manifest.read_text(encoding="utf-8"))
        print("--- manifest counts ---")
        print(json.dumps(m.get("counts", {}), ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rail")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("acquire")
    a.add_argument("--site-id", required=True)
    a.add_argument("--site-name", default="")
    a.add_argument("--work", required=True)
    a.add_argument("--category", default=None)
    a.add_argument("--lat", type=float, default=None)
    a.add_argument("--lon", type=float, default=None)
    a.add_argument("--radius-m", type=int, default=500)
    a.add_argument("--width", type=int, default=1600)
    a.add_argument("--limit", type=int, default=None)
    a.add_argument("--cached-dir", default=None)
    a.set_defaults(func=cmd_acquire)

    r = sub.add_parser("reconstruct")
    r.add_argument("--site-id", required=True)
    r.add_argument("--work", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--colmap", default="colmap")
    r.add_argument("--gpu", action="store_true")
    r.add_argument("--camera-model", default="SIMPLE_RADIAL")
    r.add_argument("--overwrite", action="store_true")
    r.add_argument("--min-track", type=int, default=2)
    r.add_argument("--min-registered", type=int, default=6)
    r.add_argument("--min-points", type=int, default=200)
    r.set_defaults(func=cmd_reconstruct)

    i = sub.add_parser("inspect")
    i.add_argument("--site-id", required=True)
    i.add_argument("--work", required=True)
    i.add_argument("--out", required=True)
    i.set_defaults(func=cmd_inspect)

    args = p.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
