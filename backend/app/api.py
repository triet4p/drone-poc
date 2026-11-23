"""Demo API: upload -> zero-shot (tiled) inference -> review -> governed DOCX.

Run:
  .venv/Scripts/python.exe -m uvicorn backend.app.main:app --port 8080
"""
import hashlib, io, json, sqlite3, threading, uuid
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
from .config import (BASE, DATA, UPLOADS, PREVIEWS, ORIGINALS, THUMBS, DB, DIST,
                     MODEL_ID, THRESHOLD, CLASSES, MAX_BYTES, LABEL_JA)
from .db import db, now, init_db, audit, seed_assets, seed_demo
from .inference import ensure_model, run_job, is_loaded
from .schemas import JudgementIn, ImagePatch, PointPick
from . import pointcloud
from .services.media import normalize

app = FastAPI(title="Drone Inspection API")

@app.on_event("startup")
def startup():
    init_db()
    seed_demo()
    threading.Thread(target=lambda: ensure_model(), daemon=True).start()


@app.get("/api/pointcloud/meta")
def pc_meta():
    return pointcloud.meta()


@app.get("/api/pointcloud/points.bin")
def pc_points():
    return FileResponse(pointcloud.PC / "points.bin", media_type="application/octet-stream")


@app.get("/api/pointcloud/view/{name}")
def pc_view(name: str):
    p = pointcloud.view_file(name)
    if not p or not p.is_file():
        raise HTTPException(404, "view not found")
    return FileResponse(p, headers={"Cache-Control": "public, max-age=3600"})


@app.post("/api/pointcloud/pick")
def pc_pick(q: PointPick):
    try:
        return pointcloud.pick(q.index, q.top_k)
    except IndexError:
        raise HTTPException(404, "point not found")


@app.get("/api/health")
def health():
    return {"ok": True, "model_loaded": is_loaded(), "model": MODEL_ID}


@app.get("/api/model")
def model_card():
    return {"id": MODEL_ID, "license": "Apache-2.0", "mode": "zero-shot, no fine-tuning",
            "training_data": "none (pretrained public weights)", "threshold": THRESHOLD,
            "classes": CLASSES, "tiling": "2x2 crack pass when max dimension > 3000 px"}


@app.get("/api/audit.csv")
def audit_csv():
    import csv, io
    with db() as con:
        rows = [dict(r) for r in con.execute("SELECT * FROM audit ORDER BY id")]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["id", "at", "action", "entity", "entity_id", "actor", "detail"])
    buf.write("\ufeff")
    w.writeheader()
    for r in rows:
        w.writerow({"id": r["id"], "at": r["created_at"], "action": r["action"], "entity": r["entity"],
                    "entity_id": r["entity_id"], "actor": r["actor"], "detail": r["detail"]})
    from fastapi import Response
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="audit.csv"'})


@app.post("/api/assets/import")
async def import_assets(file: UploadFile = File(...)):
    import csv, io
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception:
        raise HTTPException(400, "CSV を読み込めませんでした")
    if not rows:
        raise HTTPException(400, "CSV が空です")
    need = {"structure_code", "structure_name", "kind", "km_start", "km_end"}
    if not need.issubset(rows[0].keys()):
        raise HTTPException(400, f"必須列: {', '.join(sorted(need))}")
    n_s = n_m = 0
    with db() as con:
        for r in rows:
            kind = r["kind"]
            if kind not in {"bridge", "tunnel", "earth"}:
                raise HTTPException(400, f"kind が不正: {kind}")
            sid = r.get("structure_id") or r["structure_code"]
            con.execute("""INSERT INTO structure(id,code,name,kind,km_start,km_end) VALUES(?,?,?,?,?,?)
                ON CONFLICT(code) DO UPDATE SET name=excluded.name, kind=excluded.kind,
                km_start=excluded.km_start, km_end=excluded.km_end""",
                        (sid, r["structure_code"], r["structure_name"], kind,
                         float(r["km_start"]), float(r["km_end"])))
            n_s += 1
            sid = con.execute("SELECT id FROM structure WHERE code=?", (r["structure_code"],)).fetchone()[0]
            if r.get("member_code"):
                mid = f"{sid}-{r['member_code']}"
                con.execute("""INSERT INTO member(id,structure_id,code,name,km_m) VALUES(?,?,?,?,?)
                    ON CONFLICT(structure_id,code) DO UPDATE SET name=excluded.name, km_m=excluded.km_m""",
                            (mid, sid, r["member_code"], r.get("member_name") or r["member_code"],
                             float(r["km_m"]) if r.get("km_m") else None))
                n_m += 1
        audit(con, "import", "assets", "csv", f"{n_s} structures, {n_m} members")
    return {"structures": n_s, "members": n_m}


@app.get("/api/assets")
def assets():
    with db() as con:
        rows = []
        for s in con.execute("SELECT * FROM structure ORDER BY km_start"):
            ms = [dict(m) for m in con.execute("SELECT * FROM member WHERE structure_id=? ORDER BY km_m", (s["id"],))]
            rows.append({**dict(s), "members": ms})
    return rows


@app.get("/api/state")
def state():
    with db() as con:
        images = []
        for im in con.execute("""
            SELECT i.*, s.name AS structure_name, m.name AS member_name
            FROM image i
            LEFT JOIN structure s ON s.id=i.structure_id
            LEFT JOIN member m ON m.id=i.member_id
            ORDER BY i.created_at DESC, i.rowid DESC"""):
            rows = [dict(r) for r in con.execute("""
                SELECT d.*, j.rank, j.comment, j.actor, j.created_at AS judged_at
                FROM detection d
                LEFT JOIN judgement j ON j.id=(SELECT MAX(id) FROM judgement WHERE detection_id=d.id)
                WHERE d.image_id=? ORDER BY d.id""", (im["id"],))]
            dets = []
            for r in rows:
                j = ({"rank": r["rank"], "comment": r["comment"], "actor": r["actor"],
                      "created_at": r["judged_at"]} if r["rank"] else None)
                dets.append({"id": r["id"], "image_id": r["image_id"], "label": r["label"],
                             "score": r["score"], "box": json.loads(r["box_json"]),
                             "model": r["model"], "judgement": j})
            images.append({**dict(im), "detections": dets, "thumb": f"/api/thumb/{im['id']}"})
        jobs = [dict(r) for r in con.execute("SELECT * FROM job ORDER BY created_at DESC LIMIT 12")]
    confirmed = sum(1 for i in images for d in i["detections"] if d["judgement"])
    return {"model": MODEL_ID, "images": images, "jobs": jobs,
            "counts": {"images": len(images),
                       "candidates": sum(len(i["detections"]) for i in images),
                       "confirmed": confirmed}}


@app.post("/api/upload")
async def upload(background: BackgroundTasks, file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(400, "JPEG/PNG/WebP のみ対応しています")
    raw = await file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "40MB を超えています")
    iid = uuid.uuid4().hex[:12]
    try:
        img = Image.open(io.BytesIO(raw))
        w, h = normalize(img, iid)
    except Exception:
        raise HTTPException(400, "画像を読み込めませんでした")
    (ORIGINALS / f"{iid}{ext}").write_bytes(raw)
    job_id = uuid.uuid4().hex[:12]
    with db() as con:
        con.execute("""INSERT INTO image(id,filename,stored,preview,original,sha256,width,height,km_m,
                       structure_id,member_id,license,source,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (iid, file.filename or f"{iid}.jpg", f"{iid}.jpg", f"{iid}.jpg", f"{iid}{ext}",
                     hashlib.sha256(raw).hexdigest(), w, h, None, None, None, "unknown", "upload", now()))
        con.execute("INSERT INTO job(id,image_id,status,progress,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                    (job_id, iid, "queued", 0, now(), now()))
        audit(con, "upload", "image", iid, file.filename or "")
    background.add_task(run_job, job_id, iid, UPLOADS / f"{iid}.jpg")
    return {"image_id": iid, "job_id": job_id, "width": w, "height": h}


@app.patch("/api/image/{image_id}")
def patch_image(image_id: str, p: ImagePatch):
    with db() as con:
        im = con.execute("SELECT * FROM image WHERE id=?", (image_id,)).fetchone()
        if not im:
            raise HTTPException(404, "image not found")
        structure_id = p.structure_id if p.structure_id is not None else im["structure_id"]
        member_id = p.member_id if p.member_id is not None else im["member_id"]
        km = p.km_m if p.km_m is not None else im["km_m"]
        lic = p.license if p.license is not None else im["license"]
        if member_id:
            m = con.execute("SELECT * FROM member WHERE id=?", (member_id,)).fetchone()
            if not m:
                raise HTTPException(400, "member not found")
            structure_id = m["structure_id"]
            if p.km_m is None and m["km_m"] is not None:
                km = m["km_m"]
        con.execute("UPDATE image SET km_m=?,structure_id=?,member_id=?,license=? WHERE id=?",
                    (km, structure_id, member_id, lic, image_id))
        audit(con, "edit", "image", image_id, f"km={km} member={member_id} license={lic}")
    return {"ok": True}


@app.get("/api/job/{job_id}")
def job(job_id: str):
    with db() as con:
        r = con.execute("SELECT * FROM job WHERE id=?", (job_id,)).fetchone()
    if not r:
        raise HTTPException(404, "job not found")
    return dict(r)


@app.post("/api/job/{job_id}/retry")
def retry(job_id: str, background: BackgroundTasks):
    with db() as con:
        r = con.execute("SELECT * FROM job WHERE id=?", (job_id,)).fetchone()
        if not r:
            raise HTTPException(404, "job not found")
        if r["status"] != "failed":
            raise HTTPException(409, "only failed jobs can be retried")
        con.execute("UPDATE job SET status='queued',progress=0,error=NULL,updated_at=? WHERE id=?", (now(), job_id))
        audit(con, "retry", "job", job_id)
    background.add_task(run_job, job_id, r["image_id"], UPLOADS / f"{r['image_id']}.jpg")
    return {"ok": True}


@app.get("/api/media/{image_id}")
def media(image_id: str):
    with db() as con:
        r = con.execute("SELECT stored,preview FROM image WHERE id=?", (image_id,)).fetchone()
    if not r:
        raise HTTPException(404, "image not found")
    p = PREVIEWS / (r["preview"] or "")
    if not p.is_file():
        p = UPLOADS / r["stored"]
    if not p.is_file():
        raise HTTPException(404, "file missing")
    return FileResponse(p, headers={"Cache-Control": "no-store"})


@app.get("/api/full/{image_id}")
def full(image_id: str):
    with db() as con:
        r = con.execute("SELECT stored FROM image WHERE id=?", (image_id,)).fetchone()
    p = UPLOADS / (r["stored"] if r else "")
    if not p.is_file():
        raise HTTPException(404, "file missing")
    return FileResponse(p)


@app.get("/api/original/{image_id}")
def original(image_id: str):
    with db() as con:
        r = con.execute("SELECT original,filename FROM image WHERE id=?", (image_id,)).fetchone()
    p = ORIGINALS / (r["original"] if r else "")
    if not p.is_file():
        raise HTTPException(404, "file missing")
    return FileResponse(p, filename=(r["filename"] if r else "original"))


@app.get("/api/thumb/{image_id}")
def thumb(image_id: str):
    with db() as con:
        r = con.execute("SELECT stored FROM image WHERE id=?", (image_id,)).fetchone()
    p = THUMBS / (Path(r["stored"]).stem + ".jpg")
    return FileResponse(p if p.is_file() else UPLOADS / r["stored"])


@app.post("/api/judgement")
def judge(j: JudgementIn):
    with db() as con:
        d = con.execute("SELECT * FROM detection WHERE id=?", (j.detection_id,)).fetchone()
        if not d:
            raise HTTPException(404, "detection not found")
        con.execute("INSERT INTO judgement(detection_id,rank,comment,actor,created_at) VALUES(?,?,?,?,?)",
                    (j.detection_id, j.rank, j.comment, j.actor, now()))
        audit(con, "judge", "detection", str(j.detection_id), j.rank)
    return {"ok": True, "rank": j.rank}


def _jp(run, size=10.5):
    run.font.name = "Yu Gothic"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Yu Gothic")
    run.font.size = Pt(size)


@app.get("/api/report")
def report(force: bool = False):
    with db() as con:
        pending = con.execute("""SELECT COUNT(*) FROM detection d
            WHERE NOT EXISTS (SELECT 1 FROM judgement j WHERE j.detection_id=d.id)""").fetchone()[0]
        rows = [dict(r) for r in con.execute("""
            SELECT i.km_m, i.filename, i.license, s.name AS structure, m.name AS member,
                   d.label, d.score, j.rank, j.comment, j.created_at
            FROM judgement j
            JOIN detection d ON d.id=j.detection_id
            JOIN image i ON i.id=d.image_id
            LEFT JOIN structure s ON s.id=i.structure_id
            LEFT JOIN member m ON m.id=i.member_id
            WHERE j.id=(SELECT MAX(id) FROM judgement WHERE detection_id=j.detection_id)
            ORDER BY i.km_m IS NULL, i.km_m, d.id""")]
        blocked = sorted({r["filename"] for r in rows if r["license"] == "unknown"})
        if blocked and not force:
            raise HTTPException(409, f"license unset: {', '.join(blocked)}")
        audit(con, "export", "report", "docx", f"{len(rows)} rows, pending={pending}")

    doc = Document()
    h = doc.add_heading("", level=1)
    _jp(h.add_run("点検調書（下書き）"), 18)
    p = doc.add_paragraph()
    _jp(p.add_run("AI（zero-shot／追加学習なし）の候補に対し、技術者が確定した判定のみを記載しています。"), 9)

    meta = doc.add_table(rows=3, cols=4)
    meta.style = "Table Grid"
    fields = [("線名", "〇〇線 上り", "区間", "12k400–15k600"),
              ("点検日", datetime.now().strftime("%Y-%m-%d"), "点検者", "技術者"),
              ("点検方法", "ドローン撮影＋AI候補抽出＋技術者確認", "", "")]
    for r, row in enumerate(fields):
        for c, v in enumerate(row):
            cell = meta.rows[r].cells[c]
            cell.text = ""
            _jp(cell.paragraphs[0].add_run(v), 9.5)
    doc.add_paragraph()

    t = doc.add_table(rows=1, cols=6)
    t.style = "Table Grid"
    for i, text in enumerate(["キロ程", "構造物・部材", "変状", "AI score", "判定", "所見"]):
        c = t.rows[0].cells[i]
        c.text = ""
        _jp(c.paragraphs[0].add_run(text), 9.5)

    for r in rows:
        cells = t.add_row().cells
        vals = [f'{int(r["km_m"])}' if r["km_m"] else "未設定",
                f'{r["structure"] or ""} {r["member"] or ""}'.strip() or r["filename"],
                LABEL_JA.get(r["label"], r["label"]), f'{r["score"]:.2f}', r["rank"], r["comment"] or ""]
        for c, v in zip(cells, vals):
            c.text = ""
            _jp(c.paragraphs[0].add_run(v), 9.5)

    doc.add_paragraph()
    p = doc.add_paragraph()
    _jp(p.add_run(f"確定件数: {len(rows)}　未確認: {pending}　出力: {datetime.now().strftime('%Y-%m-%d %H:%M')}　※本ファイルは下書きです。"), 9)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p2 = doc.add_paragraph()
    _jp(p2.add_run(f"使用モデル: {MODEL_ID}（Apache-2.0 / zero-shot・追加学習なし）"), 8)
    out = DATA / "調書_draft.docx"
    doc.save(out)
    return FileResponse(out, filename="調書_draft.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="web")
else:
    @app.get("/", response_class=HTMLResponse)
    def no_build():
        return "<p>frontend を build してください: <code>cd frontend && npm install && npm run build</code></p>"
