"""Batch zero-shot detection -> findings manifest for the demo UI.

Runs Grounding DINO tiny once per class (avoids merged phrase labels), on CPU.
No training, no network after weights are cached.

Usage:
  .venv/Scripts/python.exe scripts/detect_batch.py --images data/demo/images --out data/demo
Optional meta.csv in --images: filename,km_m,structure,member
"""
import argparse, csv, json, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import torch
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

MODEL_ID = "IDEA-Research/grounding-dino-tiny"
CLASSES = ["crack", "spalling", "rust", "water leakage", "exposed rebar"]
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--images", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--threshold", type=float, default=0.18)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--per-class-top", type=int, default=4)
    return p.parse_args()


def main():
    a = parse_args()
    src, out = Path(a.images), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)[: a.limit or None]
    if not files:
        raise SystemExit(f"no images in {src}")

    meta = {}
    if (src / "meta.csv").exists():
        with open(src / "meta.csv", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                meta[row["filename"]] = row

    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID).eval()

    items, lat = [], []
    for p in files:
        img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        w, h = img.size
        dets = []
        for cls in CLASSES:
            inputs = processor(images=img, text=f"{cls}.", return_tensors="pt")
            t = time.perf_counter()
            with torch.no_grad():
                outputs = model(**inputs)
            dt = time.perf_counter() - t
            lat.append(dt)
            res = processor.post_process_grounded_object_detection(
                outputs, inputs.input_ids, threshold=a.threshold, text_threshold=a.threshold,
                target_sizes=[(h, w)],
            )[0]
            cand = []
            for score, label, box in zip(res["scores"], res.get("text_labels", res["labels"]), res["boxes"]):
                x1, y1, x2, y2 = [float(v) for v in box]
                area = (x2 - x1) * (y2 - y1) / (w * h)
                if area < 0.003 or area > 0.85:
                    continue
                if str(cls) not in str(label):
                    continue
                cand.append({"label": cls, "score": round(float(score), 4),
                             "box_px": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]})
            cand.sort(key=lambda d: -d["score"])
            keep = []
            for c in cand:
                if all(iou(c["box_px"], k["box_px"]) < 0.5 for k in keep):
                    keep.append(c)
            dets.extend(keep[: a.per_class_top])

        for d in dets:
            d["box_norm"] = [round(d["box_px"][0] / w, 5), round(d["box_px"][1] / h, 5),
                             round(d["box_px"][2] / w, 5), round(d["box_px"][3] / h, 5)]

        # cross-class NMS: one region often fires as crack + water leakage
        dets.sort(key=lambda d: -d["score"])
        kept = []
        for d in dets:
            if all(iou(d["box_px"], k["box_px"]) < 0.5 for k in kept):
                kept.append(d)
        dets = kept[:6]

        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        for d in dets:
            x1, y1, x2, y2 = d["box_px"]
            draw.rectangle([x1, y1, x2, y2], outline=(255, 200, 0), width=max(2, round(w / 800)))
            draw.text((x1 + 4, max(0, y1 - 14)), f'{d["label"]} {d["score"]:.2f}', fill=(20, 20, 20), font=font)
        vis = out / f"{p.stem}_detected.jpg"
        img.save(vis, quality=90)

        m = meta.get(p.name, {})
        items.append({
            "id": p.stem, "file": p.name, "preview": vis.name,
            "width": w, "height": h,
            "km_m": float(m["km_m"]) if m.get("km_m") else None,
            "structure": m.get("structure"), "member": m.get("member"),
            "structure_id": m.get("structure_id"), "member_id": m.get("member_id"),
            "license": m.get("license") or "unknown", "attribution": m.get("attribution"),
            "detections": dets,
        })
        print(f"{p.name}: {len(dets)} dets, {len(CLASSES)} passes")

    manifest = {
        "model": MODEL_ID, "classes": CLASSES, "threshold": a.threshold,
        "note": "zero-shot, not trained; scores uncalibrated",
        "images": items,
        "latency_s": {"mean_per_pass": round(sum(lat) / len(lat), 2), "max": round(max(lat), 2)},
    }
    (out / "findings.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out / 'findings.json'} ({len(items)} images, {len(lat)} passes)")


if __name__ == "__main__":
    main()
