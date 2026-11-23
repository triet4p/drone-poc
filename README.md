# Drone × AI Infrastructure Inspection — demo

React + FastAPI demo cho kiểm tra kết cấu đường sắt Nhật: upload ảnh drone, zero-shot defect candidates, kỹ sư xác nhận, 3D context, 調書 DOCX.

## Quick start

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe --index-url https://download.pytorch.org/whl/cpu torch torchvision
uv pip install --python .venv/Scripts/python.exe transformers pillow fastapi uvicorn python-docx python-multipart
cd frontend && npm install && npm run build && cd ..

.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
```

Mở `http://127.0.0.1:8080`.

## Đọc gì

| Tài liệu | Nội dung |
|---|---|
| `docs/ARCHITECTURE.md` | module tree, API, real vs demo, future geometry/drone |
| `docs/DATA.md` | schema, file lifecycle, CRS/km, license, report rules |
| `docs/REQUIREMENTS.md` | FR/NFR + acceptance |
| `docs/SCOPE.md` | MVP, demo slice, limits |
| `docs/research/` | data, model, architecture, 3D, geometry merge, imagery, token services |
| `docs/diagrams/` | architecture + data-flow SVG |
| `backend/README.md` | runbook, API, 3D, backup |

## Cấu trúc

```text
backend/app/       FastAPI, DB, inference, media, future modules
backend/scripts/   detect_batch, backup
frontend/src/      app shell, components, features, lib, styles
data/              runtime media + SQLite (seed 6 ảnh tham chiếu)
docs/              architecture, data, research, diagrams
```

## Trạng thái

- LIVE: 点検確認 (upload/infer/review/judgement), 保守優先度.
- DEMO: 飛行スケジュール, 撮影計画, 変位解析 — dữ liệu cố định, không ghi DB/report.
- 3D: MapLibre + GSI + OpenFreeMap; real OSM alignment, assets demo; cần internet.
- 計測 view: model points, `模式値`; đo thật cần point cloud + GCP.
- 点群 view: synthetic B-14 cloud (365k pts), click point → metrics + matching camera view; relative scale, labelled synthetic.
