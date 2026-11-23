import sqlite3, json, hashlib, uuid
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
from .config import DATA, DEMO, DB, UPLOADS, PREVIEWS, ORIGINALS, THUMBS, STRUCTURES, MEMBERS
from .services.media import normalize

def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    for d in (DATA, UPLOADS, PREVIEWS, ORIGINALS, THUMBS):
        d.mkdir(exist_ok=True)
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS structure(
          id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
          kind TEXT NOT NULL, km_start REAL NOT NULL, km_end REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS member(
          id TEXT PRIMARY KEY, structure_id TEXT NOT NULL REFERENCES structure(id),
          code TEXT NOT NULL, name TEXT NOT NULL, km_m REAL, UNIQUE(structure_id, code));
        CREATE TABLE IF NOT EXISTS image(
          id TEXT PRIMARY KEY, filename TEXT NOT NULL, stored TEXT NOT NULL,
          preview TEXT, original TEXT, sha256 TEXT NOT NULL, width INTEGER, height INTEGER,
          km_m REAL, structure_id TEXT REFERENCES structure(id), member_id TEXT REFERENCES member(id),
          license TEXT NOT NULL DEFAULT 'unknown', attribution TEXT,
          source TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS detection(
          id INTEGER PRIMARY KEY AUTOINCREMENT, image_id TEXT NOT NULL REFERENCES image(id),
          label TEXT NOT NULL, score REAL NOT NULL, box_json TEXT NOT NULL,
          model TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS judgement(
          id INTEGER PRIMARY KEY AUTOINCREMENT, detection_id INTEGER NOT NULL REFERENCES detection(id),
          rank TEXT NOT NULL, comment TEXT NOT NULL DEFAULT '', actor TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS job(
          id TEXT PRIMARY KEY, image_id TEXT NOT NULL, status TEXT NOT NULL,
          progress REAL NOT NULL DEFAULT 0, error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(
          id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, entity TEXT NOT NULL,
          entity_id TEXT NOT NULL, actor TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_det_image ON detection(image_id);
        CREATE INDEX IF NOT EXISTS idx_jud_det ON judgement(detection_id);
        CREATE TRIGGER IF NOT EXISTS judgement_no_update BEFORE UPDATE ON judgement
          BEGIN SELECT RAISE(ABORT, 'judgement is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS judgement_no_delete BEFORE DELETE ON judgement
          BEGIN SELECT RAISE(ABORT, 'judgement is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
          BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
          BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
        """)
        # additive migration for DBs created by the previous build
        cols = {r[1] for r in con.execute("PRAGMA table_info(image)")}
        for name, ddl in [("preview", "TEXT"), ("original", "TEXT"), ("license", "TEXT NOT NULL DEFAULT 'unknown'"),
                          ("structure_id", "TEXT"), ("member_id", "TEXT"), ("attribution", "TEXT")]:
            if name not in cols:
                con.execute(f"ALTER TABLE image ADD COLUMN {name} {ddl}")


def audit(con, action: str, entity: str, entity_id: str, detail: str = "", actor: str = "技術者"):
    con.execute("INSERT INTO audit(action,entity,entity_id,actor,detail,created_at) VALUES(?,?,?,?,?,?)",
                (action, entity, entity_id, actor, detail, now()))


def seed_assets(con=None):
    own = con is None
    con = con or db()
    try:
        if con.execute("SELECT COUNT(*) FROM structure").fetchone()[0]:
            return
        con.executemany("INSERT INTO structure(id,code,name,kind,km_start,km_end) VALUES(?,?,?,?,?,?)", STRUCTURES)
        con.executemany("INSERT INTO member(id,structure_id,code,name,km_m) VALUES(?,?,?,?,?)", MEMBERS)
    finally:
        if own:
            con.close()



def seed_demo():
    with db() as con:
        seed_assets(con)
        if con.execute("SELECT COUNT(*) FROM image").fetchone()[0]:
            return
        extra = DEMO / "extra" / "manifest.json"
        if extra.exists():
            man = json.loads(extra.read_text(encoding="utf-8"))
            for im in man["images"]:
                src = DEMO / "extra" / im["file"]
                if not src.exists():
                    continue
                iid = uuid.uuid4().hex[:12]
                w, h = normalize(Image.open(src), iid)
                orig = ORIGINALS / f"{iid}.jpg"
                orig.write_bytes(src.read_bytes())
                con.execute("""INSERT INTO image(id,filename,stored,preview,original,sha256,width,height,km_m,
                               structure_id,member_id,license,attribution,source,created_at)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (iid, im["file"], f"{iid}.jpg", f"{iid}.jpg", orig.name,
                             hashlib.sha256(src.read_bytes()).hexdigest(), w, h,
                             im.get("km_m"), im.get("structure_id") or None, im.get("member_id") or None,
                             im.get("license") or "unknown", im.get("attribution"), "reference", now()))
                for d in im["detections"]:
                    box = d.get("box_norm") or d.get("box")
                    con.execute("INSERT INTO detection(image_id,label,score,box_json,model,created_at) VALUES(?,?,?,?,?,?)",
                                (iid, d["label"], d["score"], json.dumps(box), man["model"], now()))
            audit(con, "seed", "reference", str(len(man["images"])), "reference-defect dataset")
            return

        # legacy fallback: generic crack crops
        manifest = DEMO / "findings.json"
        if not manifest.exists():
            return
        man = json.loads(manifest.read_text(encoding="utf-8"))
        km = {"cf001": 13262, "cf002": 13330, "cf003": 13405}
        mem = {"cf001": "B14-P3", "cf002": "B14-P4", "cf003": "B14-G5"}
        for im in man["images"]:
            src = DEMO / "images" / im["file"]
            if not src.exists():
                continue
            iid = uuid.uuid4().hex[:12]
            w, h = normalize(Image.open(src), iid)
            orig = ORIGINALS / f"{iid}.jpg"
            orig.write_bytes(src.read_bytes())
            con.execute("""INSERT INTO image(id,filename,stored,preview,original,sha256,width,height,km_m,
                           structure_id,member_id,license,source,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (iid, im["file"], f"{iid}.jpg", f"{iid}.jpg", orig.name,
                         hashlib.sha256(src.read_bytes()).hexdigest(), w, h,
                         km.get(im["id"], im.get("km_m")), "B14", mem.get(im["id"]), "demo", "demo", now()))
            for d in im["detections"]:
                box = d.get("box_norm") or d.get("box")
                con.execute("INSERT INTO detection(image_id,label,score,box_json,model,created_at) VALUES(?,?,?,?,?,?)",
                            (iid, d["label"], d["score"], json.dumps(box), man["model"], now()))
        audit(con, "seed", "demo", str(len(man["images"])), "legacy demo dataset")


# ---------- api ----------
