"""Generate a deterministic synthetic point cloud of B-14 with camera views.

Output: data/pointcloud/demo/{points.bin, meta.json, views.npz, view_*.jpg}
Coordinates: metres, local engineering frame; x = chainage offset from km 13150,
y = lateral, z = up. Relative geometry is exact for the demo model; absolute
elevation is schematic.
"""
import json, math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "pointcloud" / "demo"
rng = np.random.default_rng(42)

MEMBERS = ["rail", "sleeper", "ballast", "deck", "pier", "abutment", "ground", "river"]
PIER_X = [50, 80, 112, 180, 250, 310]  # P1..P6 relative to km 13150
RAIL_Z = 8.72


def color(base, spread=8):
    c = np.array(base, dtype=float)
    c = c + rng.normal(0, spread, 3)
    return np.clip(c, 0, 255).astype(np.uint8)


def box_surface(x0, x1, y0, y1, z0, z1, n, base, member):
    areas = np.array([(x1-x0)*(y1-y0), (x1-x0)*(y1-y0), (x1-x0)*(z1-z0), (x1-x0)*(z1-z0),
                      (y1-y0)*(z1-z0), (y1-y0)*(z1-z0)], dtype=float)
    faces = rng.choice(6, size=n, p=areas/areas.sum())
    x = rng.uniform(x0, x1, n); y = rng.uniform(y0, y1, n); z = rng.uniform(z0, z1, n)
    for f, val in zip([0, 1, 2, 3, 4, 5], [z0, z1, y0, y1, x0, x1]):
        m = faces == f
        if f in (0, 1): z[m] = val
        elif f in (2, 3): y[m] = val
        else: x[m] = val
    return x, y, z, color(base), member


def collect():
    xs, ys, zs, cs, ms = [], [], [], [], []

    def add(x, y, z, c, m):
        n = len(x)
        c = np.asarray(c)
        if c.ndim == 1:
            c = np.tile(c, (n, 1))
        xs.append(x); ys.append(y); zs.append(z); cs.append(c); ms.append(np.full(n, m, np.float32))

    # rails
    for sign in (-1, 1):
        n = 30000
        x = rng.uniform(-2, 372, n)
        y = sign * 0.5335 + rng.normal(0, 0.035, n)
        z = RAIL_Z + rng.normal(0, 0.035, n)
        add(x, y, z, color((58, 58, 56), 5), 0)

    # sleepers every 0.6 m
    for sx in np.arange(0, 370, 0.6):
        n = 18
        add(rng.uniform(sx-0.1, sx+0.1, n), rng.uniform(-1.15, 1.15, n),
            rng.uniform(8.58, 8.66, n), color((116, 104, 86), 8), 1)

    # ballast / deck
    x, y, z, c, m = box_surface(0, 370, -1.9, 1.9, 8.30, 8.58, 30000, (125, 122, 112), 2)
    add(x, y, z, c, m)
    x, y, z, c, m = box_surface(-2, 372, -4.2, 4.2, 7.85, 8.35, 70000, (168, 165, 155), 3)
    add(x, y, z, c, m)

    # piers and abutments
    for px in PIER_X:
        x, y, z, c, m = box_surface(px-1.6, px+1.6, -1.5, 1.5, -1.0, 7.95, 8000, (156, 154, 147), 4)
        add(x, y, z, c, m)
    for ax in (-3.5, 367.5):
        x, y, z, c, m = box_surface(ax-2.5, ax+2.5, -4.2, 4.2, -1.0, 8.2, 6000, (150, 148, 141), 5)
        add(x, y, z, c, m)

    # ground and river
    for side in (-1, 1):
        n = 60000
        x = rng.uniform(-30, 400, n)
        y = side * rng.uniform(7, 32, n)
        z = rng.normal(0.0, 0.12, n)
        add(x, y, z, color((98, 120, 78), 10), 6)
    n = 14000
    add(rng.uniform(-20, 390, n), rng.uniform(-18, 18, n), rng.normal(-3.2, 0.05, n),
        color((70, 104, 138), 8), 7)

    P = np.column_stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)]).astype(np.float32)
    C = np.vstack(cs).astype(np.uint8)
    M = np.concatenate(ms).astype(np.float32)
    return P, C, M


def look_at(eye, target):
    eye = np.asarray(eye, float); target = np.asarray(target, float)
    f = target - eye; f /= np.linalg.norm(f)
    up = np.array([0.0, 0.0, 1.0])
    s = np.cross(f, up); s /= (np.linalg.norm(s) + 1e-9)
    u = np.cross(s, f)
    R = np.stack([s, u, -f])
    return R, eye


VIEWS = [
    ("view_01", (60, -30, 18), (110, 0, 8)),
    ("view_02", (160, 32, 20), (130, 0, 8)),
    ("view_03", (260, -26, 16), (220, 0, 8)),
    ("view_04", (185, 0, 48), (185, 0, 8)),
    ("view_05", (185, -24, 12), (185, 0, 8.8)),
    ("view_06", (330, 20, 18), (270, 0, 8)),
    ("view_07", (25, -22, 14), (70, 0, 8)),
    ("view_08", (185, 24, 12), (185, 0, 8.8)),
    ("view_09", (120, -18, 10), (120, 0, 8.7)),
    ("view_10", (250, -18, 10), (250, 0, 8.7)),
]
W, H = 1000, 700
FOV = 48


def render(P, C, eye, target):
    R, eye = look_at(eye, target)
    pc = (P - eye) @ R.T
    z = -pc[:, 2]
    ok = z > 0.2
    f = (H / 2) / math.tan(math.radians(FOV / 2))
    u = f * pc[:, 0] / np.maximum(z, 1e-6) + W / 2
    v = -f * pc[:, 1] / np.maximum(z, 1e-6) + H / 2
    ok &= (u >= 0) & (u < W - 1) & (v >= 0) & (v < H - 1)
    ui = np.round(u[ok]).astype(int); vi = np.round(v[ok]).astype(int)
    depth = z[ok]; cols = C[ok].astype(float)
    shade = np.clip(1.35 - depth / 110.0, 0.55, 1.15)[:, None]
    cols = np.clip(cols * shade, 0, 255).astype(np.uint8)

    sky = np.zeros((H, W, 3), np.float32)
    top = np.array([222, 231, 238], np.float32); bot = np.array([154, 168, 160], np.float32)
    for r in range(H):
        t = r / (H - 1)
        sky[r, :, :] = top * (1 - t) + bot * t
    img = sky.astype(np.uint8)

    order = np.argsort(-depth)
    ui, vi, cols, depth = ui[order], vi[order], cols[order], depth[order]
    zbuf = np.full((H, W), np.inf, np.float32)
    for dx in (0, 1):
        for dy in (0, 1):
            xx = np.clip(ui + dx, 0, W - 1); yy = np.clip(vi + dy, 0, H - 1)
            img[yy, xx] = cols
            zbuf[yy, xx] = np.minimum(zbuf[yy, xx], depth)
    return Image.fromarray(img), zbuf


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    P, C, M = collect()
    order = rng.permutation(len(P))
    P, C, M = P[order], C[order], M[order]
    data = np.column_stack([P, C.astype(np.float32), M]).astype(np.float32)
    data.tofile(OUT / "points.bin")

    depths = {}
    views = []
    for name, eye, target in VIEWS:
        img, zbuf = render(P, C, eye, target)
        img.save(OUT / f"{name}.jpg", quality=88)
        depths[name] = zbuf.astype(np.float16)
        views.append({"id": name, "file": f"{name}.jpg", "width": W, "height": H,
                      "fov": FOV, "eye": list(eye), "target": list(target)})
    np.savez_compressed(OUT / "views.npz", **depths)

    meta = {
        "id": "demo_b14", "label": "B-14 合成点群", "count": int(len(P)),
        "members": MEMBERS, "units": "m", "gauge_m": 1.067,
        "bounds": {"x": [float(P[:, 0].min()), float(P[:, 0].max())],
                   "y": [float(P[:, 1].min()), float(P[:, 1].max())],
                   "z": [float(P[:, 2].min()), float(P[:, 2].max())]},
        "scale": {"status": "relative", "basis": "synthetic B-14 model, gauge 1.067 m"},
        "note": "合成点群。相対形状はモデル通り、絶対標高・実測値ではありません。",
        "views": views,
    }
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(P)} points -> {OUT}")


if __name__ == "__main__":
    main()
