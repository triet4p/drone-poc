"""Convert a COLMAP/OpenMVS PLY to the viewer's dense.bin layer."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def convert(ply: Path, out: Path, max_points: int = 600000) -> int:
    from plyfile import PlyData
    data = PlyData.read(str(ply))
    v = data["vertex"].data
    names = v.dtype.names or ()
    if not all(k in names for k in ("x", "y", "z")):
        raise RuntimeError("PLY has no x/y/z vertex properties")
    n = len(v)
    take = np.arange(n)
    if n > max_points:
        take = np.linspace(0, n - 1, max_points).astype(np.int64)
    xyz = np.stack([v["x"], v["y"], v["z"]], axis=1)[take].astype(np.float32)
    if all(k in names for k in ("red", "green", "blue")):
        rgb = np.stack([v["red"], v["green"], v["blue"]], axis=1)[take].astype(np.float32)
    else:
        rgb = np.full((len(xyz), 3), 180, dtype=np.float32)
    rows = np.concatenate([xyz, rgb, np.full((len(xyz), 1), 255, dtype=np.float32)], axis=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows.tofile(out)
    return len(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ply", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-points", type=int, default=600000)
    a = p.parse_args()
    count = convert(Path(a.ply), Path(a.out), a.max_points)
    print(f"dense points: {count}")


if __name__ == "__main__":
    main()
