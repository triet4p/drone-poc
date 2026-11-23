"""Consistent backup: SQLite snapshot + media, as one tar.gz with a manifest.

Usage: .venv/Scripts/python.exe scripts/backup.py --out backups
"""
import argparse, hashlib, json, sqlite3, tarfile, tempfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
DIRS = ["uploads", "previews", "originals", "thumbs", "pointcloud"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(BASE / "backups"))
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = out / f"demo-backup-{stamp}.tar.gz"
    manifest = {"created_at": stamp, "files": {}}

    with tempfile.TemporaryDirectory() as tmp:
        snap = Path(tmp) / "demo.db"
        src = sqlite3.connect(DATA / "demo.db")
        dst = sqlite3.connect(snap)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(snap, arcname="demo.db")
            manifest["files"]["demo.db"] = hashlib.sha256(snap.read_bytes()).hexdigest()
            for d in DIRS:
                root = DATA / d
                if not root.exists():
                    continue
                for f in root.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(DATA).as_posix()
                        tar.add(f, arcname=rel)
                        manifest["files"][rel] = hashlib.sha256(f.read_bytes()).hexdigest()
        (out / f"demo-backup-{stamp}.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{archive}  ({len(manifest['files'])} files)")
    print(f"{out / f'demo-backup-{stamp}.json'}")


if __name__ == "__main__":
    main()
