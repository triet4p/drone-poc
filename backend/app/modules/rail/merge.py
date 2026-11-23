"""Merge real image sources for one site into a single manifest.

There is deliberately no "one provider per site" rule. A site can combine a
video segment, Mapillary images, Commons stills, and user uploads. Duplicate
bytes are removed by sha256; provenance stays on each photo.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def merge_manifests(*, site_id: str, site_name: str, work: Path, inputs: list[Path]) -> dict[str, Any]:
    work = Path(work)
    photos_dir = work / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    merged: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen_sha: set[str] = set()
    seen_ids: set[str] = set()
    for inp in inputs:
        manifest = json.loads(Path(inp).read_text(encoding="utf-8"))
        queries.extend(manifest.get("queries", []))
        for rec in manifest.get("photos", []):
            pid = rec.get("photo_id")
            sha = rec.get("sha256")
            if not pid or not sha:
                errors.append({"photo_id": pid, "error": "missing_id_or_hash"})
                continue
            if pid in seen_ids or sha in seen_sha:
                errors.append({"photo_id": pid, "error": "duplicate"})
                continue
            src = Path(inp).parent / rec["served_file"]
            if not src.exists():
                errors.append({"photo_id": pid, "error": "missing_file"})
                continue
            dst = photos_dir / f"{pid}.jpg"
            shutil.copy2(src, dst)
            rec = dict(rec)
            rec["served_file"] = f"photos/{dst.name}"
            rec["merged_from_manifest"] = str(inp)
            merged.append(rec)
            seen_ids.add(pid)
            seen_sha.add(sha)
    manifest = {
        "schema_version": 1,
        "site_id": site_id,
        "site_name": site_name or site_id,
        "queries": queries,
        "photos": merged,
        "errors": errors,
        "counts": {"candidates": len(merged), "downloaded": len(merged), "errors": len(errors)},
        "providers": sorted({p.get("provider", "unknown") for p in merged}),
    }
    (work / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
