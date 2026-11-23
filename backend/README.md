# Real upload demo — React + FastAPI + Grounding DINO

Upload ảnh thật → job inference nền → gán vị trí/quyền → kỹ sư confirm → 調書 DOCX.
Không train, không GPU. Seed 6 ảnh defect tham chiếu (rail-like, CC) nếu có `data/demo/extra/manifest.json`; fallback 3 ảnh CrackForest. Ảnh upload chạy model thật.

## Chạy

```bash
# lần đầu
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe --index-url https://download.pytorch.org/whl/cpu torch torchvision
uv pip install --python .venv/Scripts/python.exe transformers pillow fastapi uvicorn python-docx python-multipart
cd frontend && npm install && npm run build && cd ..

# chạy
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
```

Dev UI: `cd frontend && npm run dev` (proxy `/api` → 8080).

## 3D map (demo)

- `maplibre-gl@6.19.0`, self-hosted bundle; worker configured via Vite `?worker&url`.
- Base: GSI シームレス空中写真 / 標準地図 (toggle 写真/地図), attribution 地理院タイル.
- Buildings: OpenFreeMap vector `building` → `fill-extrusion` (© OpenStreetMap contributors, ODbL).
- Corridor: real 東海道本線 geometry near 根府川 (OSM, cached `data/rail_osm.json`), km 12k400–15k600 mapped onto it; B-14/T-07 geometry is demo.
- EPSG:4326 in data; MapLibre renders EPSG:3857. Demo terrain is flat (no DEM conversion).
- Rails: two rails generated from the OSM alignment at 1,067 mm gauge + ballast, labelled 模式 (not survey).
- Two views: **3D** (context, no measurement) and **計測** (model points A1/P1–P6/A2, deck ends, tunnel portals; horizontal / Δh / slope distance). The 計測 view is labelled 模式値 and must not be used as a survey result.
- Markers: images with `km_m`; click → select image; strip 縦断 syncs.
- Real-line context: 5 Commons photos (CC0/PD/CC BY/BY-SA) of 根府川–真鶴 with per-photo attribution; context only, not defect close-ups.
- **Requires internet** for GSI/OSM tiles at runtime. Post-meeting: prefetch/self-host PMTiles + PLATEAU/Cesium (see `docs/research/04a`, `04b`).
- No point cloud, no PLATEAU in the 26/11 demo; attribution bar is always visible.

## Luồng

0. Toggle **JP / EN / VI**; lưu `localStorage`. 調書 luôn tiếng Nhật.
1. Upload hoặc kéo-thả. Giữ **original bytes** (`data/originals/`), JPEG chuẩn hóa ≤6000px (`data/uploads/`), preview 2048 (`data/previews/`), thumb 640.
2. Job `queued → running → done`; 5 pass full-frame + 2×2 crack pass nếu cạnh dài >3000px. ~20 s/pass CPU; UI poll 1,5 s. Job lỗi có nút **再実行**.
3. Gán **構造物 / 部材 / キロ程 / 権利** ở panel phải; chọn 部材 tự điền km.
4. Kỹ sư chọn AA/A1/A2/B/C/S + comment → judgement append-only (trigger DB chặn UPDATE/DELETE).
5. **優先度** mở bảng confirmed, sort theo rank rồi km; click mở đúng ảnh/candidate.
6. **線路縦断**: dải 12k400–15k600, structure band + dot theo km; click chọn ảnh.
7. **調書**: chặn nếu còn candidate chưa xác nhận (confirm) và nếu có ảnh `license=unknown` (confirm force). DOCX có header 線名/区間/点検日/点検者/方法, 未確認 count, model line.

## API

| Endpoint | Việc |
|---|---|
| `POST /api/upload` | multipart, 40MB, JPEG/PNG/WebP |
| `PATCH /api/image/{id}` | km, structure_id, member_id, license |
| `POST /api/judgement` | rank + comment, append-only |
| `GET /api/state` | images + detections + latest judgement + jobs |
| `GET /api/assets` | structures + members |
| `POST /api/assets/import` | CSV: structure_id(optional),structure_code,structure_name,kind,km_start,km_end,member_code,member_name,km_m |
| `POST /api/job/{id}/retry` | chỉ job failed |
| `GET /api/report?force=true` | DOCX; 409 nếu license unknown |
| `GET /api/audit.csv` | audit export |
| `GET /api/model` | model card (license, mode, threshold) |
| `GET /api/original/{id}` | file gốc bất biến |
| `GET /api/pointcloud/meta` | synthetic B-14 cloud + camera views |
| `POST /api/pointcloud/pick` | point → metrics + matching view |

## Backup

```bash
.venv/Scripts/python.exe backend/scripts/backup.py --out backups
```

Tạo `demo-backup-<UTC>.tar.gz` (SQLite snapshot + media) và manifest SHA-256.

## Reset

Dừng server; xóa `data/demo.db`, `data/uploads`, `data/previews`, `data/originals`, `data/thumbs`; start lại → seed 3 ảnh + asset B-14/T-07.

## Giới hạn

- Zero-shot, không fine-tune: box thô, FP nhiều, score chưa calibration.
- Tiling chỉ 2×2 cho crack khi ảnh >3000px; chưa DZI/45MP viewer, chưa 3D/change/flight, chưa auth/role.
- SQLite + filesystem là demo-only; MVP dùng PostgreSQL/PostGIS + storage adapter.
- Ảnh seed từ CrackForest (phi thương mại), license `demo`; thay bằng ảnh của mình/khách trước khi chiếu.
- Không đo mm, không suy 判定区分 từ score.

## Cấu trúc

```
backend/app/api.py           HTTP routes + static
backend/app/config.py        paths/constants
backend/app/db.py            schema, seed, audit
backend/app/inference.py     model + jobs
backend/app/services/media.py
backend/app/modules/         geometry, drone (placeholders)
backend/scripts/             detect_batch, backup
frontend/src/app|components|features|lib|styles
data/                        originals, uploads, previews, thumbs, demo.db, seed
```
