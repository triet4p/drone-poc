# Context for task-advisor — reusable real rail data pipeline for Japan

Task ID: TASK-REAL-DATA-02
Date: 2026-11-23. Self-contained. Read-only advisory; do not implement or install.

## 1. User decision (current, supersedes earlier Landwasser/drone plan)

> "drone x rail có thể để sau, hiện chỉ cần rail , ở nhật bản, có thể nhân bản cách làm
> được, research + advisor lại. Server cũng đã được dọn dẹp, trống khoảng 40-50GB"

> "Ưu tiên các giải pháp có thể tái sử dụng sau này, từ việc lấy hình ảnh, infer, restruct.
> Cho mọi vị trí trên map nhật bản"

Hard requirements:
- Real photographs + real point cloud, same real site, click point -> corresponding real photo.
- Site must be **rail in Japan**. Drone is explicitly deferred; no drone requirement now.
- The solution must be **reusable**: image acquisition, inference, reconstruction for
  arbitrary/other locations on the Japan map, not a one-off asset.
- 1–2 pilot cases.
- CUDA allowed. License selection deferred.
- Prefer automation and a provider strategy over manual per-site photo selection.
- Do not propose synthetic geometry + rendered views as the primary answer.

## 2. Existing application contract (what the pipeline should feed)

Repo: `F:/DataImpact/drone-poc`; local git remote `https://github.com/triet4p/drone-poc.git`
exists, repo has no commits yet. Backend FastAPI + SQLite; frontend React/Vite/Three.js.

Current point-cloud feature is synthetic but interaction is proven:
- `backend/app/pointcloud.py` loads `data/pointcloud/demo/points.bin` (float32, 7 values:
  x,y,z,r,g,b,member_idx), `meta.json`, `views.npz`.
- `POST /api/pointcloud/pick` `{index, top_k}` returns point metrics and top views with
  `u,v`, depth and a rendered image URL.
- `PointCloudView.tsx`: Three.js `Points`, raycast, panel, marker on image.
- Current views are renders from the same synthetic cloud; `scale_status=relative`.
- The app has Grounding DINO tiny zero-shot inference (CPU) on uploaded/reference images,
  engineer confirmation, report. `image`/`detection`/`judgement` tables exist.
- Existing demo corridor is fictional B-14/T-07 on real Tokaido alignment near 根府川.

A reusable pipeline should replace the synthetic source with per-site real data while
keeping the pick/UI interaction, ideally with a `site_id` and provider provenance.

## 3. Research findings (verified where marked)

### 3.1 Image providers for Japan

| Provider | Coverage mechanism | Rail relevance | Pose/metadata | Auth | Reusability | Verified status |
|---|---|---|---|---|---|---|
| Wikimedia Commons categories | Category per station/bridge/tunnel | High for named stations/landmarks | EXIF sometimes; no poses | None | High if OSM/Wikidata maps asset -> category | Categories exist: Nebukawa 43 files, Yokokawa 53, Tanna Tunnel 7 files + 4 subcats, Odawara 24 + 14 subcats, Tokyo 6 + 19 subcats |
| Wikimedia Commons geosearch | lat/lon + radius | Depends on coverage | EXIF; no poses | None | High API, sparse data | 500 m Nebukawa: 3 images; 1 km Tokyo: 50, Tanna: 34 |
| Mapillary | small bbox (<0.01 sq deg), many tiles; no semantic rail filter | Street-level, may miss track/underside | GPS, sequence, camera type; not full pose | Token required | High where coverage exists | Coverage around Japanese rail **unverified**; API docs confirm bbox/tile limits |
| KartaView | bbox <=0.06 deg or radius | Street-level | GPS, sequence | None/limited | Medium | API works at `api.kartaview.org`; sample bboxes around Nebukawa and Tokyo returned **0 images**, so Japan coverage is weak/unverified |
| Commons cab-view / rail videos | One video per line/section | High (track corridor) | No poses; frames | None | Medium, per-line not arbitrary | Hachiko line 4K video 2.78 GB (CC BY 3.0); Kiha 110 Koma River bridge 42 MB 1080p (CC BY 3.0) |
| User/field upload | Any site | Highest | Optional telemetry/GCP | — | Manual | Not available yet |
| Google Street View/Flickr | global/geo | variable | pose/EXIF | keys/ToS | high coverage but deferred license | Do not rely on for reusable pipeline until legal |

Prior research already established:
- No open Japanese rail corridor point cloud with per-point photos exists.
- Kanagawa R1/R6 airborne cloud is forest/terrain, no rail detail; GSI cloud is paid;
  xRoad MMS is DRM-locked; PLATEAU is city models, not inspection photos.
- ArchScanLib is UK masonry rail bridges, FARO, 81.49 GB, no photos/poses.
- OpenHeritage3D Alvord is a US concrete bridge, FARO 4.02 GB, no poses.
- COLMAP is the reproducible CPU path; Pi4/DUSt3R/MASt3R/VGGT are CUDA/NC options;
  license deferred.

### 3.2 Candidate first Japanese sites

| Site | Category/photo count | Rail type | Why | Risk |
|---|---|---|---|---|
| 根府川駅 (Nebukawa Station), JR Tokaido, Kanagawa | 43 files + 2 subcats | Station/platform/seaside | On existing demo corridor; map/OSM context already built | Many platform/interior/train shots; few clean exterior angles; dynamic scenes |
| 横川駅 (Yokokawa Station), JR Shinetsu, Gunma | 53 files | Station, historic Usui Pass | Many exterior photos across years/angles; strong station building | Mixed eras/seasons; people/trains; 1.067 m gauge |
| 丹那トンネル (Tanna Tunnel), JR Tokaido, Shizuoka | 7 files + 4 subcats | Tunnel portal | Real famous rail tunnel; portal geometry | Few modern photos; historic images; limited parallax |
| 東京駅 (Tokyo Station) | 6 files + 19 subcats | Major station | Huge photo coverage, iconic | Large scale, crowds, many subcategories, hard reconstruction |
| 小田原駅/熱海駅 | 24/11 files + subcats | Stations | Tokaido corridor | Fewer angles, complex buildings |

### 3.3 Reconstruction methods

- COLMAP sparse: known, repeatable, CPU/GPU; sequential matching for video, exhaustive for
  unordered Commons; outputs `points3D` + track observations (`image_id,u,v`). This is the
  strongest fit for "click point -> actual observed pixel".
- COLMAP dense/MVS: optional for visual cloud; sparse is enough for linkage.
- Pi4: 0.5B model, 150 frames ~12 GiB peak on A800; 16 GB 4060 Ti can do fewer frames;
  CUDA 12.6-compatible stack; install heavy; license NC. Use only after sparse works.
- Scale: no GCP. For rail, gauge (1.067 m on many JR lines, 1.435 m Shinkansen) can anchor
  scale if track is visible; otherwise relative/unverified. Do not claim survey accuracy.

## 4. Remote compute (verified)

- SSH PowerShell 7: `ssh trietlm@192.168.99.214`; host `di-server`.
- Ubuntu 23.10, 12 vCPU, 62 GB RAM; RTX 4060 Ti 16,380 MiB; driver 580.126.20.
- `/` now 916 GB with **54 GB free** (user cleaned it); `/dev/shm` 32 GB.
- CUDA toolkit `/usr/local/cuda-12.1`; system Python 3.11.6; torch not installed.
- Passwordless sudo; apt candidate `colmap 3.8-1build1`.
- Existing home has many other run directories; do not touch.

## 5. Reusability requirement

The user does not want a hand-curated one-off. Advice must define a pipeline with clear
provider adapters and interfaces, e.g.:

```text
site input (lat/lon/radius, OSM rail asset, or Commons category)
  -> resolve rail asset + identity (OSM/Overpass/Wikidata)
  -> discover images (Commons category/geosearch; optional Mapillary/KartaView; video)
  -> quality/dedup/coverage gate
  -> reconstruct (COLMAP; optional dense/Pi4)
  -> select static structure points + track observations
  -> per-site pointcloud package (points, meta, observations, provenance)
  -> inference (Grounding DINO) on the same real images
  -> UI: site -> cloud -> click -> real photo + marker
```

Key questions:
- Which provider order gives the best "any rail site in Japan" coverage without paid keys?
- Should the canonical unit be OSM `railway=station/halt` / bridge / tunnel, or arbitrary
  lat/lon? How to map OSM/Wikidata to Commons categories automatically?
- What is the minimum coverage/quality gate before a site is marked "available" vs
  "insufficient data"? How to avoid a failed reconstruction being shown as success?
- How to make per-site ingestion idempotent and cacheable; how to store provenance and
  source URLs.
- Where does defect inference fit: run on all downloaded photos, only registered frames,
  or only close-ups? How to tie a detection to a 3D point/member.

## 6. Required advisory output

1. **Provider decision**: ranked, reusable image-acquisition strategy for Japan rail.
   State what works without a token, what needs one, and what is unverified.
2. **First pilot site**: choose one from the candidates (or justify another), with why;
   optional second site. Prioritize reproducibility and click-to-photo evidence, not
   visual impressiveness.
3. **Repeatable pipeline design**: modules, interfaces, commands, quality gates,
   reconstruction/linkage, scale, inference, caching, failure states.
4. **Data contract**: how to evolve the current `points.bin + meta.json + views.npz` to
   multi-site real data with `site_id`, `observations`, `photo_id`, `u,v`, `source_url`,
   `scale_status`, provenance; what API/UI changes are minimal.
5. **Pilot plan**: 1–2 day sequence, exact acceptance gates, fallback if Commons photos
   lack overlap or COLMAP fails.
6. **Risks / kill criteria** and what not to do.
7. Only genuinely blocking questions for the user.

Do not implement. Do not edit. Mark uncertain facts `[unverified]`.
