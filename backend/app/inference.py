import json, threading
from pathlib import Path
from PIL import Image
from .config import MODEL_ID, THRESHOLD, CLASSES
from .db import db, now, audit

_lock = threading.Lock()
_model = None
_processor = None

def is_loaded() -> bool:
    return _model is not None


def ensure_model():
    global _model, _processor
    if _model is not None:
        return
    with _lock:
        if _model is not None:
            return
        import torch
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
        _processor = AutoProcessor.from_pretrained(MODEL_ID)
        _model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID).eval()
        torch.set_num_threads(max(1, torch.get_num_threads()))


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _pass(image: Image.Image, cls: str):
    import torch
    w, h = image.size
    inputs = _processor(images=image, text=f"{cls}.", return_tensors="pt")
    with torch.no_grad():
        out = _model(**inputs)
    res = _processor.post_process_grounded_object_detection(
        out, inputs.input_ids, threshold=THRESHOLD, text_threshold=THRESHOLD, target_sizes=[(h, w)])[0]
    found = []
    for score, label, box in zip(res["scores"], res.get("text_labels", res["labels"]), res["boxes"]):
        x1, y1, x2, y2 = [float(v) for v in box]
        area = (x2 - x1) * (y2 - y1) / (w * h)
        if area < 0.003 or area > 0.85 or cls not in str(label):
            continue
        found.append({"label": cls, "score": round(float(score), 4),
                      "box": [x1 / w, y1 / h, x2 / w, y2 / h]})
    return found


def infer(path: Path, progress) -> list[dict]:
    ensure_model()
    img = Image.open(path).convert("RGB")
    w, h = img.size
    dets: list[dict] = []

    # full-frame pass for every class
    with _lock:
        for cls in CLASSES:
            dets.extend(_pass(img, cls))
            progress()

    # tiled crack pass: 2x2 with 10% overlap when the image is large enough
    if max(w, h) > 3000:
        tw, th = w // 2, h // 2
        ox, oy = int(tw * 0.1), int(th * 0.1)
        boxes = [(0, 0, tw + ox, th + oy), (tw - ox, 0, w, th + oy),
                 (0, th - oy, tw + ox, h), (tw - ox, th - oy, w, h)]
        with _lock:
            for (x1, y1, x2, y2) in boxes:
                tile = img.crop((max(0, x1), max(0, y1), min(w, x2), min(h, y2)))
                for d in _pass(tile, "crack"):
                    bx1, by1, bx2, by2 = d["box"]
                    d["box"] = [(bx1 * tile.width + x1) / w, (by1 * tile.height + y1) / h,
                                (bx2 * tile.width + x1) / w, (by2 * tile.height + y1) / h]
                    dets.append(d)
                progress()

    dets.sort(key=lambda d: -d["score"])
    kept = []
    for d in dets:
        if all(iou(d["box"], k["box"]) < 0.5 for k in kept):
            kept.append(d)
    return kept[:8]


def run_job(job_id: str, image_id: str, path: Path):
    def set_job(status: str, progress: float, error: str | None = None):
        with db() as con:
            con.execute("UPDATE job SET status=?,progress=?,error=?,updated_at=? WHERE id=?",
                        (status, progress, error, now(), job_id))

    try:
        set_job("running", 2)
        total = 5 + (4 if max(Image.open(path).size) > 3000 else 0)
        done = {"n": 0}
        def progress():
            done["n"] += 1
            set_job("running", min(94, 4 + 90 * done["n"] / total))
        dets = infer(path, progress)
        with db() as con:
            con.execute("DELETE FROM detection WHERE image_id=?", (image_id,))
            for d in dets:
                con.execute("INSERT INTO detection(image_id,label,score,box_json,model,created_at) VALUES(?,?,?,?,?,?)",
                            (image_id, d["label"], d["score"], json.dumps(d["box"]), MODEL_ID, now()))
            audit(con, "infer", "image", image_id, f"{len(dets)} candidates, {done['n']} passes")
        set_job("done", 100)
    except Exception as e:
        set_job("failed", 100, f"{type(e).__name__}: {e}")

