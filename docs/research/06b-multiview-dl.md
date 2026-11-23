# 06b — Tái dựng point cloud từ ảnh đa góc bằng deep learning và liên kết điểm–ảnh (マルチビュー点群復元)

> Tiếng Việt; thuật ngữ Nhật trong ngoặc đơn. Mỗi khẳng định kèm URL nguồn. Số liệu không đo trực tiếp đánh dấu [推定].

## 1) Phạm vi (適用範囲)

Trả lời một câu hỏi: **từ 10–30 ảnh một cầu/hầm đường sắt tái dựng point cloud (点群) để click từng điểm xem chỉ số (計測値) + ảnh gốc (対応画像)**.

Bao gồm:

- Mô hình DL 2026: DUSt3R, MASt3R/MASt3R-SfM, VGGT, Fast3R, CUT3R, MonST3R, MapAnything, MV-DUSt3R, **π⁴ Pi4 (Shanghai AI Lab)** theo yêu cầu bổ sung.
- Baseline cổ điển (従来手法): COLMAP, OpenMVS, OpenDroneMap (ODM).
- Neo metric scale (スケール復元) bằng khổ ray 1.067 m (軌間), GCP (対空標識), baseline camera, khoảng đo tay.
- Liên kết điểm–ảnh (点–画像対応): reproject điểm 3D vào camera, chọn ảnh, kiểm tra che khuất (オクルージョン).
- Viewer/picking (点群ビューア): Potree vs Three.js Points vs Cesium 3D Tiles; kế hoạch demo 3 ngày trên máy CPU-only.

Ngoài phạm vi (対象外): phát hiện defect bằng AI (xem 02-model); LiDAR thực; training/fine-tune — chỉ inference (推論) weights sẵn có.

Giả thiết: ảnh RGB overlap ≥ 60–70%, có EXIF tiêu cự nếu được; máy dev CPU-only, thuê GPU theo giờ cho bước tái dựng; demo gồm nội bộ + trình diễn khách JR (JR東日本) nên license thương mại (商用利用) phải nêu rõ.

## 2) Findings (調査結果)

### 2.1 Họ DUSt3R / MASt3R / MASt3R-SfM (đề xuất chính cho demo)

DUSt3R (*Geometric 3D Vision Made Easy*, CVPR 2024, [paper](https://openaccess.thecvf.com/content/CVPR2024/html/Wang_DUSt3R_Geometric_3D_Vision_Made_Easy_CVPR_2024_paper.html), [repo](https://github.com/naver/dust3r)) nhận **cặp ảnh không cần hiệu chuẩn (キャリブレーション不要)**, hồi quy pointmap (mảng H×W×3) + confidence. MASt3R ([paper](https://arxiv.org/abs/2406.09756)) thêm descriptor khớp dày đặc; MASt3R-SfM ([paper](https://arxiv.org/abs/2409.19152), [repo](https://github.com/naver/mast3r)) dựng đồ thị cặp ảnh (`make_pairs`), global alignment, tinh chỉnh pose bằng khớp 3D + reprojection loss, xuất **pose + point cloud**.

| Hạng mục | DUSt3R | MASt3R / MASt3R-SfM |
|---|---|---|
| License | **CC BY-NC-SA 4.0** ([LICENSE](https://github.com/naver/dust3r/blob/main/LICENSE)) + license dataset gốc | **CC BY-NC-SA 4.0** ([repo](https://github.com/naver/mast3r)); dataset Map-free hạn chế riêng |
| Đầu vào | Cặp ảnh, ~512 px cạnh dài | Tập ảnh không thứ tự + pure rotation; 10–30 ảnh là vùng mạnh nhất |
| Đầu ra | Pointmap + confidence từng cặp | Pointmap + pose + khớp dày đặc |
| VRAM / 10–30 ảnh | [推定] 8–16 GB, 5–20 phút (alignment pair-wise) | [推定] 4–8 GB độ phân giải thấp, 8–12 GB thoải mái; ~2–5 phút GPU (mốc 283 s/25 view, [benchmark](https://github.com/minoTrey/DUSt3R-Paper-Collection/blob/main/docs/reconstruction/light3r-sfm.md)) |
| CPU-only | Không thực tế (chậm hàng chục lần) [推定] | Không thực tế (matching CPU rất chậm) [推定] |
| Trưởng thành | Rất cao, nhiều fork | Cao; baseline cộng đồng 2025–2026 |

Mạnh: chịu ảnh không thứ tự, baseline ngắn; confidence lọc điểm rác. Yếu: ray thép (レール) mỏng/phản xạ, cấu trúc lặp (trụ/dầm giống nhau) gây khớp sai — cần ảnh bối cảnh (mố cầu, vách hầm, biển báo) neo pose.

### 2.2 VGGT — transformer hình học đa năng, dự phòng cho demo

VGGT (*Visual Geometry Grounded Transformer*, CVPR 2025 Best Paper, [repo](https://github.com/facebookresearch/vggt), [project](https://vgg-t.github.io/)) dự đoán pointmap + depth + pose + intrinsics + tracks trong **một forward pass**, không cần calibration; nhanh hơn MASt3R-SfM một bậc nên khâu point→photo rẻ hơn.

| Hạng mục | Chi tiết |
|---|---|
| License | Code theo **VGGT License riêng** ([LICENSE](https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt)); checkpoint **VGGT-1B phi thương mại**, bản **Commercial** phải nộp đơn xin quyền |
| Đầu vào | 1–200+ ảnh; benchmark 336×518 trên H100 ([paper](https://robots.ox.ac.uk/~vgg/publications/2025/Wang25/wang25.pdf)) |
| VRAM / tốc độ | 10 ảnh 3.63 GB/0.14 s; 20 ảnh 5.58 GB/0.31 s; 50 ảnh 11.41 GB/1.04 s (chỉ backbone — cộng thêm vài GB head + weights); [推定] 10–30 ảnh chạy được trên GPU 12 GB |
| CPU-only | Không thực tế [推定] |
| Trưởng thành | Cao; chạy `bfloat16` trên Ampere+ ([README](https://github.com/facebookresearch/vggt/blob/main/README.md)) |

### 2.3 Fast3R / CUT3R / MonST3R / MapAnything / MV-DUSt3R

| Mô hình | Paper / repo | License | Nhận xét |
|---|---|---|---|
| Fast3R (1000+ ảnh/forward, CVPR 2025) | [repo](https://github.com/facebookresearch/fast3r) | **FAIR NC**; **repo archive 01/07/2026** ([README](https://github.com/facebookresearch/fast3r/blob/main/README.md)) | Loại: dừng bảo trì |
| CUT3R (streaming + state, CVPR 2025 Oral) | [repo](https://github.com/CUT3R/CUT3R) / [paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_Continuous_3D_Perception_Model_with_Persistent_State_CVPR_2025_paper.pdf) | **CC BY-NC-SA 4.0** | Hợp drone livestream; bản hiện tại memory tăng tuyến tính theo frame |
| MonST3R (cảnh động, ICLR 2025) | [repo](https://github.com/Junyi42/monst3r) | **Không license rõ** | Chỉ khi ảnh có vật chuyển động; rủi ro pháp lý cao |
| MapAnything (metric feed-forward, 3DV 2026) | [repo](https://github.com/facebookresearch/map-anything) / [paper](https://map-anything.github.io/assets/MapAnything.pdf) | Code **Apache-2.0**; weights NC hoặc bản Apache sạch thương mại | Kênh thương mại duy nhất họ DL; scale ảnh-only kém trên dữ liệu lạ (paper tự nêu) |
| MV-DUSt3R+ (sparse view ~2 s, CVPR 2025) | [repo](https://github.com/facebookresearch/mvdust3r) | **CC BY-NC 4.0** | Chỉ cần khi có 2–4 ảnh thưa |

### 2.4 π⁴ Pi4 (bổ sung bắt buộc) — foundation model hình học + motion 0.5B

Pi4 (*Foundation Model for 4D Scene Geometry and Motion*, Physical Intelligence Team / Shanghai AI Lab, [model card](https://huggingface.co/yyfz233/Pi4), [repo](https://github.com/yyfz/Pi4)): một model ~0.5B tham số, nhận ảnh đơn / tập không thứ tự / video, không cần calibration, một forward pass chung.

**2.4.1 Output — CÓ đủ point cloud + pose để reproject.**

| Key | Shape | Dùng cho point→photo |
|---|---|---|
| `local_points` | [B,T,H,W,3] | Pointmap hệ camera, native scale |
| `camera_poses` | [B,T,4,4] | Pose camera-to-world |
| `metric_scale` | [B] | Hệ số native → metric dự đoán (`X = m·(R·P + t)`, nhân cả translation) |
| `confidence` | [B,T,H,W] | Lọc điểm trước picking |
| `tracks_2d` / `tracks_3d` | [B,T,H,W,2/3] | Tương ứng pixel query→target (khi có `query_frame`) |
| `visibility` / `tracking_confidence` | [B,T,H,W] | Kiểm tra che khuất |
| `dynamic_mask` | [B,T,H,W] | Mặt nạ vật chuyển động — loại khỏi đo đạc |
| Export | `pc_preview.ply` + `scene.json` + `tracks.bin` + viewer nhẹ | `scene.json` có pose metric; viewer xem lại không cần GPU ([guide](https://github.com/yyfz/Pi4/blob/main/docs/inference.md)) |

**2.4.2 VRAM / thời gian (đo trên A800 80 GB, 512×288, [guide](https://github.com/yyfz/Pi4/blob/main/docs/inference.md)):** 25 frame 4.13 GiB/4.1 s; 50 frame 5.22 GiB/8.6 s; 75 frame 7.26 GiB/14.1 s; 150 frame 12.03 GiB/48.7 s; 750 frame 33.99 GiB/223.7 s. Suy ra 10–30 ảnh [推定] forward < 10 s trên GPU ≥ 8 GB — nhưng **150-frame chưa validate trên GPU 8 GB thật**, và **CUDA bắt buộc** (Triton/FlexGEMM, PyTorch 2.12.1 + CUDA 12.6 + GCC). **CPU-only: không chạy được.** Cài đặt tốn nửa ngày công lần đầu [推定].

**2.4.3 Scale có ambiguity** — `metric_scale` dự đoán không cam kết trên dữ liệu lạ (cùng hạn chế MapAnything đã nêu, [paper](https://map-anything.github.io/assets/MapAnything.pdf)). Phải neo ngoài như §2.6 (`s = 1.067 / d_model` hoặc Umeyama ≥ 3 GCP).

**2.4.4 License: CHỈ nội bộ/đánh giá.** Weights **CC BY-NC 4.0** ([model card](https://huggingface.co/yyfz233/Pi4), [LICENSE_MODEL](https://huggingface.co/yyfz233/Pi4/blob/main/LICENSE_MODEL)); code repo **SPDX NOASSERTION** ([license API](https://api.github.com/repos/yyfz/Pi4/license)), nội dung LICENSE thực tế cũng là CC BY-NC 4.0 ("thương mại không được phép"). **Chiếu trước khách JR bằng weights này mà chưa xin phép là vi phạm.**

**2.4.5 Kết luận 26/11: KHÔNG thử Pi4 trong demo 3 ngày** (CUDA-only + install nửa ngày + chưa có số đo ảnh tĩnh + NC). Giữ cho vòng eval nội bộ sau demo, chạy cùng MASt3R-SfM trên cùng 20 ảnh rồi mới quyết MVP.

### 2.5 Baseline cổ điển: khi nào thắng DL

| Pipeline | License | CPU/GPU | 10–30 ảnh [推定] | Khi nào thắng DL |
|---|---|---|---|---|
| COLMAP sparse | **BSD-3-Clause** ([license](https://colmap.github.io/license.html)) | Sparse CPU được; dense cần GPU ([FAQ](https://colmap.github.io/faq.html)); exhaustive matching hợp tập nhỏ ([tutorial](https://colmap.github.io/tutorial)) | Sparse 10–30 phút CPU; dense GPU +10–60 phút | Cấu trúc lặp, texture yếu, cần pose chính xác để đo đạc |
| COLMAP + OpenMVS CPU | OpenMVS **AGPL-3.0** ([LICENSE](https://github.com/cdcseacave/openMVS/blob/develop/LICENSE)) | CPU-only toàn tuyến | 30 phút–vài giờ (dense là nút thắt) | Fallback không-GPU duy nhất cho hình học thật |
| ODM / WebODM | **AGPL-3.0** ([LICENSE](https://github.com/OpenDroneMap/ODM/blob/master/LICENSE)); GPU gần như không ảnh hưởng ([docs](https://docs.opendronemap.org/fil/installation/)) | CPU 4 GB tối thiểu; nên 16 GB + SSD | 10–60 phút/20–100 ảnh ([benchmarks](https://github.com/OpenDroneMap/odm-benchmarks/blob/master/data-parsed/by-dataset.md)) | Có ảnh drone + GPS: ortho/DSM/cloud geo-reference một bước; hợp MVP hơn demo |

AGPL cho phép dùng nội bộ/demo, nhưng **host thành dịch vụ mạng phải mở source phái sinh** — pháp chế chốt trước MVP. Nhóm sạch thương mại: COLMAP BSD + Potree BSD-2-Clause ([LICENSE](https://github.com/potree/potree/blob/develop/LICENSE)) + Three.js MIT ([LICENSE](https://github.com/mrdoob/three.js/blob/dev/LICENSE)) + Cesium Apache-2.0 ([README](https://github.com/CesiumGS/cesium/blob/main/README.md?plain=1)).

### 2.6 Metric scale: cách neo và câu chữ trung thực

Mọi pipeline thiếu priors metric đều **đúng tương đối, sai tuyệt đối** (up-to-scale, 相似変換の不定性):

| Cách neo | Thủ tục | Chính xác [推定] | Ghi chú |
|---|---|---|---|
| Khổ ray 1.067 m | ≥5 mặt cắt, median → `s = 1.067 / d_model` (khổ hẹp JR, [MLIT](https://www.mlit.go.jp/english/2006/h_railway_bureau/Laws_concerning/14.pdf?1673254464832=)) | ±3–8% | Ray phải hiện rõ; nên đặt thước chuẩn cạnh ray |
| Baseline / khoảng đo tay | RTK drone giữa 2 điểm chụp hoặc 1 cạnh mố cầu | ±1–5% | Rẻ nhất demo ("1-point scale") |
| GCP + Umeyama ≥ 3 điểm | GNSS/total station, giải similarity transform | ±cm ở 10–30 m | Chuẩn MVP; ODM ăn GCP trực tiếp |

Câu chữ được phép: **"hình học tương đối đúng (相対形状は正しい); kích thước tham khảo (参考値) tới khi có GCP"**. Không gắn nhãn cm/mm khi chưa neo GCP.

### 2.7 Độ chính xác kỳ vọng và failure modes (cầu/hầm đường sắt)

| Kỳ vọng (overlap tốt, GPU) | Mức [推定] |
|---|---|
| Sai số tương đối DL (MASt3R/VGGT/Pi4) mặt có texture | 1–3% kích thước cảnh |
| COLMAP sparse + BA loop closure | Tốt hơn DL 2–5× trên pose |
| Mật độ cloud sau lọc confidence | 100k–1M điểm/cảnh cầu 20 m |

| Chế độ hỏng (失敗モード) | Biểu hiện | Giảm thiểu |
|---|---|---|
| Bê tông phẳng (vách hầm T-07) | Lỗ/hõm giả | Ảnh xiên + đèn; lọc confidence |
| Cấu trúc lặp (trụ/dầm B-14) | Khớp nhầm chu kỳ → cong/gián đoạn | Ảnh toàn cảnh neo; kiểm tra loop thủ công |
| Ray mỏng + phản xạ | Ray đứt, "bay" khỏi mặt ray | Không đo trên ray DL; đo mố/tà vẹt |
| Blur / thiếu sáng hầm | Pose trôi | Màn trập nhanh + đèn; loại ảnh blur (Laplacian) |
| Overlap < 50% | SfM rớt frame; DL méo scale | Mỗi điểm ≥ 3 ảnh, baseline 1–3 m |

### 2.8 Liên kết điểm–ảnh: reproject + top-K + occlusion

Với điểm `X` và camera `(K, R, t)`: chiếu `x = K·(R·X + t)`; giữ quan sát thỏa z > 0, trong khung hình, góc nhìn < ~60° [推定], depth khớp (`|z − D(u,v)| < ε`, ε ≈ 1–2% tầm xa [推定]).

| Bước | Thuật toán | Output |
|---|---|---|
| Reproject | Ma trận chiếu từng view (numpy vector hóa) | Ứng viên `(image_id, u, v, depth)` |
| Top-K | Score = cos(góc)·confidence/(1 + khoảng cách), K = 3–5 | `source_view` xếp hạng |
| Occlusion | So depth render từ mesh/pointmap | Cờ `occluded` + `depth_residual` |
| Serve | Precompute offline, API chỉ đọc | < 50 ms/pick [推定] |

### 2.9 Viewer / picking

| Tiêu chí | Potree | Three.js `Points` | CesiumJS + 3D Tiles |
|---|---|---|---|
| License | BSD-2-Clause | MIT | Apache-2.0 |
| LOD lớn | Octree + point budget ([converter](https://github.com/potree/PotreeConverter)); offline qua HTTP local ([guide](https://github.com/baneesh/potree/blob/master/docs/getting_started.md)) | Tự xây chunk/load-unload | HLOD tileset; `pnts` deprecated từ 1.1, dùng glTF ([spec](https://docs.ogc.org/cs/22-025r4/22-025r4.html?swpmtx=ce4e01347d979a17a6c7f0bbf9c3eb20&swpmtxnonce=a8e2810d76)) |
| Picking | Mạnh nhất (picking + đo đạc chuyên dụng) | `Raycaster` threshold world-unit, đủ cloud < ~2M ([docs](https://threejs.org/docs/pages/Raycaster)); cloud dày cần index/GPU picking | `scene.pick` + `pickPosition` nội suy từ depth — vị trí render, không phải record gốc ([docs](https://cesium.com/learn/cesiumjs/ref-doc/Scene.html)) |
| Offline | Có | Có | Có nếu tileset + terrain local |
| Khuyến nghị | Cloud > 5M / cần đo ngay | **Demo 3 ngày** (sẵn stack Three.js + MapLibre) | Cần globe + nhiều lớp GIS |

Adapter: LAZ/PLY → PotreeConverter (octree) hoặc `pdal`/`laspy` → buffer Float32 nạp thẳng `THREE.Points` (budget demo ≤ 2M [推定]).

## 3) Bảng so sánh tổng (比較表)

| Pipeline | License | Phần cứng | 10–30 ảnh [推定] | Scale | Output | Photo link | Rủi ro |
|---|---|---|---|---|---|---|---|
| MASt3R-SfM ✅ demo | CC BY-NC-SA 4.0 ([r](https://github.com/naver/mast3r)) | GPU 8–12 GB | 2–5 phút | Up-to-scale → §2.6 | Pose + point + match | Tốt | NC chặn demo khách |
| DUSt3R | CC BY-NC-SA 4.0 ([r](https://github.com/naver/dust3r/blob/main/LICENSE)) | GPU 8–16 GB | 5–20 phút | Up-to-scale | Pointmap/confidence | Trung bình | NC; chậm hơn MASt3R-SfM |
| VGGT ✅ dự phòng | Code custom, weights NC ([r](https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt)) | GPU ≥12 GB | < 1 phút fwd | Up-to-scale | Pose + point + depth + track | Rất tốt | NC; VRAM tăng nhanh > 50 ảnh |
| MapAnything | Code Apache-2.0, weights NC/Apache ([r](https://github.com/facebookresearch/map-anything/blob/main/README.md?utm_source=openai)) | GPU 12 GB+ | Phút | **Metric显式** (yếu khi ảnh-only lạ) | Point metric + ray | Tốt | Mới (3DV 2026) |
| Pi4 ⛔ demo, ⏳ eval | Weights CC BY-NC 4.0 ([r](https://huggingface.co/yyfz233/Pi4/blob/main/LICENSE_MODEL)); code NOASSERTION ([r](https://api.github.com/repos/yyfz/Pi4/license)) | **CUDA bắt buộc**, ≥8 GB | < 10 s fwd | Metric dự đoán + neo ngoài | Pose + point + track + mask + viewer | Rất tốt | NC chặn demo JR; install nặng |
| CUT3R | CC BY-NC-SA 4.0 ([r](https://github.com/CUT3R/CUT3R)) | GPU streaming | Realtime-ish | Metric dự đoán | Point + pose online | Tốt | NC; memory tuyến tính |
| MV-DUSt3R+ | CC BY-NC 4.0 ([r](https://github.com/facebookresearch/mvdust3r)) | GPU | ~2 s sparse | Up-to-scale | Point sparse-view | Trung bình | NC; thừa cho 10–30 ảnh |
| MonST3R | Không license rõ ([r](https://github.com/Junyi42/monst3r)) | GPU | Phút | Up-to-scale | Point + motion | Trung bình | Pháp lý mở |
| Fast3R | FAIR NC ([r](https://github.com/facebookresearch/fast3r/blob/main/README.md)) | GPU | Giây | Up-to-scale | Point 1000+ ảnh | Tốt | **Đã archive — loại** |
| COLMAP+OpenMVS ✅ fallback | BSD + AGPL-3.0 ([r](https://colmap.github.io/license.html)) | **CPU-only được** | 30 phút–vài giờ | Up-to-scale → §2.6 | Sparse + dense + mesh | Tốt | AGPL khi host dịch vụ |
| ODM ✅ MVP drone | AGPL-3.0 ([r](https://github.com/OpenDroneMap/ODM/blob/master/LICENSE)) | CPU 16 GB+ | 10–60 phút | Geo-reference GPS/GCP | Ortho + DSM + cloud | Tốt | AGPL; nặng cho demo |

## 4) Khuyến nghị (推奨事項)

> ⚠️ **Cảnh báo license trước demo thương mại (商用デモ時の注意): MASt3R/DUSt3R/VGGT-1B/CUT3R/MV-DUSt3R/Pi4 đều phi thương mại (非商用). Chiếu trước khách JR dạng chào hàng mà chưa xin phép là vi phạm. Phần chiếu dùng COLMAP (BSD) + viewer MIT/BSD; output NC chỉ nội bộ (社内評価) hoặc có văn bản cho phép.**

**(a) Demo 3 ngày (26/11): MASt3R-SfM trên GPU thuê + fallback COLMAP CPU.** Bước nặng duy nhất (pose + cloud) chạy GPU thuê ([推定] 0.5–1 USD/h); backend/viewer/API chạy CPU local. Mọi số đo nhãn "参考値 — tương đối đúng, scale neo khổ ray 1.067 m, chờ GCP". Ảnh demo ghi rõ synthetic/reference (kế thừa 05b) — **không gắn nhãn "ảnh drone thực" nếu không phải**.

**(b) MVP drone thật: ODM (geo-reference + ortho) làm nền, MASt3R-SfM/VGGT dense chi tiết, MapAnything-Apache khi cần weights thương mại.**

No-go (中止条件):

1. Overlap < 50% hoặc > 30% ảnh rớt pose → chụp bổ sung, không cố dense.
2. Không thuê được GPU và COLMAP CPU > 4 h → fallback synthetic-depth (§6).
3. Khách đòi số cam kết (保証値) mà chưa có GCP → chỉ cho tương đối.
4. Pháp chế chưa duyệt NC → demo khách chỉ nhánh COLMAP/viewer sạch.
5. Pi4: không vào demo/MVP thương mại tới khi có license thương mại hoặc văn bản cho phép.

## 5) Kiến trúc / đặc tả (仕様)

Luồng: ảnh → (GPU thuê) MASt3R-SfM/VGGT → PLY + pose → reproject offline → Postgres → API → Three.js picking → panel ảnh + chỉ số.

### 5.1 Schema

`point_sample` (downsample voxel ~1–2 cm [推定], ≤ 2M điểm/cloud):

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | UUID PK | Ổn định qua re-export |
| `cloud_id` | UUID FK → `pointcloud(id)` | 1 cloud = 1 đối tượng B-14/T-07 |
| `x, y, z` | DOUBLE | World metric đã neo scale; kèm `scale_status` (`relative`/`gauge`/`gcp`) |
| `nx, ny, nz` | REAL NULL | Pháp tuyến |
| `r, g, b` | SMALLINT | Màu từ ảnh gốc |
| `confidence` | REAL | Lọc `≥ 0.3–0.5` [推定] khi render |
| `track_id` | BIGINT NULL | Nối track 2D/3D (VGGT/Pi4) |
| `created_at` | TIMESTAMPTZ | — |

`source_view` (top-K quan sát/điểm, K = 3–5):

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `point_id` | UUID FK | — |
| `image_id` | UUID FK → `image(id)` | Ảnh gốc + EXIF + pose `(K, R, t)` |
| `u, v` | REAL | Pixel reproject |
| `depth` | REAL | Độ sâu dọc tia (視深) |
| `view_angle_deg` | REAL | Góc tia nhìn vs pháp tuyến |
| `depth_residual` | REAL | `\|z − D(u,v)\|`; NULL nếu thiếu depth map |
| `occluded` | BOOL | TRUE khi residual > ε |
| `score` | REAL | cos(view)·confidence/(1+dist) |
| `rank` | SMALLINT | 1 = ảnh chính (代表画像) |

Khóa `(point_id, rank)` UNIQUE; index `(image_id)`, `(point_id, occluded, rank)`.

### 5.2 API

`GET /api/pointcloud/{id}` — metadata + tile + danh sách ảnh:

```json
{
  "id": "pc_b14_001", "object": "B-14", "status": "ready",
  "scale": {"status": "gauge", "factor": 1.023, "basis": "rail gauge 1.067 m"},
  "points": 842115, "tiles": "/static/pc/pc_b14_001/points.bin",
  "honest_label": "相対形状は正しい・寸法は参考値",
  "images": [{"id": "img_014", "url": "/static/img/img_014.jpg", "pose_available": true}]
}
```

`POST /api/point/{id}/pick` — click 1 điểm → chỉ số + ảnh:

```json
// request: {"top_k": 3, "max_angle_deg": 60, "include_occluded": false}
// response 200:
{
  "point": {"id": "pt_9f31", "x": 12.41, "y": 3.02, "z": -1.15, "confidence": 0.87},
  "metrics": {"nearest_rail_dist_m": 0.71, "scale_status": "gauge"},
  "views": [
    {"image_id": "img_014", "url": "/static/img/img_014.jpg", "u": 1823.4, "v": 1041.2,
     "depth": 8.42, "view_angle_deg": 23.5, "occluded": false, "score": 0.91, "rank": 1}
  ]
}
```

Lỗi: `404` cloud/point không tồn tại; `422` point bị lọc confidence; mọi response đo đạc kèm `scale_status`.

## 6) Kế hoạch 3 ngày vs MVP (3日計画)

Ngày 1 — tái dựng (GPU thuê, ~0.5 ngày công): chốt 10–20 ảnh + ghi nguồn từng file; chạy **MASt3R-SfM** → PLY + pose (rớt > 30% thì đổi **VGGT**); neo scale khổ ray, nhãn `gauge`.

Ngày 2 — backend (CPU local): 2 bảng §5.1 + script reproject numpy (project → lọc biên/góc → depth check → top-3 → bulk insert); 2 endpoint §5.2, test pick 20 điểm (đúng ảnh ≥ 90% [推定] mới qua).

Ngày 3 — viewer: Three.js `Points` (≤ 2M) + `Raycaster` threshold ≈ 2–3 cm world [推定]; click → POST pick → panel crop `(u,v)` + full ảnh + chỉ số; banner固定 "合成/参考値・相対形状"; rehearsal + checklist no-go §4.

Fallback không GPU (CPU-only 100%):

1. **Synthetic-depth (khuyến nghị):** render view + depth từ scene 3D sẵn có → backproject, pose hoàn hảo; nhãn "合成形状".
2. **COLMAP CPU + OpenMVS CPU** qua đêm ([推定] 1–4 h/20 ảnh 12 MP); pose sạch BSD.
3. **ODM Docker low-res** (`--pc-quality low`) lấy cloud nhanh, nâng quality sau.

MVP ([推定] 3–4 tuần): ODM geo-referenced nền + MASt3R-SfM/VGGT dense + GCP Umeyama + Potree khi > 5M điểm; eval nội bộ Pi4 vs MASt3R cùng 20 ảnh drone; pháp chế chốt NC/AGPL.

## 7) Rủi ro (リスク)

| Rủi ro | Mức | Đối sách |
|---|---|---|
| Weights NC chiếu trước khách JR | Cao | Nhánh sạch COLMAP/viewer; NC chỉ nội bộ + văn bản cho phép |
| AGPL khi host dịch vụ | Trung bình | Pháp chế duyệt; tách service biên |
| Khớp sai vùng lặp, scale trôi | Cao | Ảnh neo toàn cảnh; ≥5 mặt cắt gauge; không số tuyệt đối khi thiếu GCP |
| VRAM GPU thuê thiếu | Trung bình | ≤ 30 ảnh 512 px; hạ `--max-frames`; fallback COLMAP |
| Pi4 install nuốt ngày công | Trung bình | Cấm thử trong demo; env conda Python 3.11 riêng |
| Nhầm cloud tương đối thành cam kết | Cao | `scale_status` mọi API + banner 参考値 |
| Ảnh synthetic bị xem là drone thật | Cao | Ghi nguồn từng file; tách tab bối cảnh/kiểm tra (05b) |

## 8) References (参考文献・一次情報)

- DUSt3R: [paper (CVPR 2024)](https://openaccess.thecvf.com/content/CVPR2024/html/Wang_DUSt3R_Geometric_3D_Vision_Made_Easy_CVPR_2024_paper.html) | [repo + CC BY-NC-SA 4.0](https://github.com/naver/dust3r)
- MASt3R: [paper (ECCV 2024)](https://arxiv.org/abs/2406.09756) | [MASt3R-SfM paper (3DV 2025)](https://arxiv.org/abs/2409.19152) | [repo](https://github.com/naver/mast3r)
- VGGT: [repo](https://github.com/facebookresearch/vggt) | [LICENSE custom](https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt) | [paper + benchmark H100](https://robots.ox.ac.uk/~vgg/publications/2025/Wang25/wang25.pdf) | [project](https://vgg-t.github.io/) | [README bfloat16](https://github.com/facebookresearch/vggt/blob/main/README.md)
- Fast3R: [README (FAIR NC, archived 01/07/2026)](https://github.com/facebookresearch/fast3r/blob/main/README.md)
- CUT3R: [repo](https://github.com/CUT3R/CUT3R) | [paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_Continuous_3D_Perception_Model_with_Persistent_State_CVPR_2025_paper.pdf)
- MonST3R: [repo (license không rõ)](https://github.com/Junyi42/monst3r)
- MapAnything: [repo (Apache-2.0 / NC)](https://github.com/facebookresearch/map-anything/blob/main/README.md?utm_source=openai) | [paper](https://map-anything.github.io/assets/MapAnything.pdf)
- MV-DUSt3R+: [repo (CC BY-NC 4.0)](https://github.com/facebookresearch/mvdust3r)
- Pi4: [model card](https://huggingface.co/yyfz233/Pi4) | [README](https://huggingface.co/yyfz233/Pi4/raw/main/README.md) | [inference guide](https://github.com/yyfz/Pi4/blob/main/docs/inference.md) | [repo](https://github.com/yyfz/Pi4) | [code license NOASSERTION](https://api.github.com/repos/yyfz/Pi4/license) | [weights CC BY-NC 4.0](https://huggingface.co/yyfz233/Pi4/blob/main/LICENSE_MODEL)
- COLMAP: [license BSD-3-Clause](https://colmap.github.io/license.html) | [FAQ dense cần GPU](https://colmap.github.io/faq.html) | [tutorial](https://colmap.github.io/tutorial)
- OpenMVS: [LICENSE AGPL-3.0](https://github.com/cdcseacave/openMVS/blob/develop/LICENSE)
- ODM: [LICENSE AGPL-3.0](https://github.com/OpenDroneMap/ODM/blob/master/LICENSE) | [install](https://docs.opendronemap.org/fil/installation/) | [benchmarks](https://github.com/OpenDroneMap/odm-benchmarks/blob/master/data-parsed/by-dataset.md)
- MASt3R-SfM runtime (283 s/25 views): [benchmark](https://github.com/minoTrey/DUSt3R-Paper-Collection/blob/main/docs/reconstruction/light3r-sfm.md)
- Potree: [converter](https://github.com/potree/PotreeConverter) | [local serving](https://github.com/baneesh/potree/blob/master/docs/getting_started.md) | [LICENSE BSD-2](https://github.com/potree/potree/blob/develop/LICENSE)
- Three.js: [Raycaster](https://threejs.org/docs/pages/Raycaster) | [LICENSE MIT](https://github.com/mrdoob/three.js/blob/dev/LICENSE)
- Cesium: [Scene.pick](https://cesium.com/learn/cesiumjs/ref-doc/Scene.html) | [Apache-2.0](https://github.com/CesiumGS/cesium/blob/main/README.md?plain=1) | [3D Tiles 1.1 pnts deprecated](https://docs.ogc.org/cs/22-025r4/22-025r4.html?swpmtx=ce4e01347d979a17a6c7f0bbf9c3eb20&swpmtxnonce=a8e2810d76)
- Khổ ray JR 1.067 m: [MLIT](https://www.mlit.go.jp/english/2006/h_railway_bureau/Laws_concerning/14.pdf?1673254464832=)
- Mapillary CC BY-SA 4.0: [license](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data)

---

**KEY DECISIONS (≤8)**

1. Demo 26/11: MASt3R-SfM trên GPU thuê; VGGT dự phòng cùng dữ liệu.
2. Fallback không-GPU: synthetic-depth từ scene 3D hoặc COLMAP+OpenMVS CPU qua đêm.
3. Viewer demo: Three.js `Points` ≤ 2M + Raycaster; Potree để dành cloud > 5M ở MVP.
4. Mọi số đo gắn `scale_status`; scale demo neo khổ ray 1.067 m, nhãn 参考値.
5. Schema `point_sample` + `source_view` (top-3, precompute offline) + 2 endpoint §5.2.
6. Pi4 KHÔNG vào demo 26/11 (CUDA-only + install nặng + NC); chỉ eval nội bộ sau demo.
7. Chiếu khách JR chỉ dùng thành phần sạch thương mại; output NC nội bộ hoặc có văn bản cho phép.
8. MVP: ODM + GCP nền, dense DL chi tiết, pháp chế chốt NC/AGPL trước khi host.

**OPEN QUESTIONS (≤8)**

1. Thuê GPU 12–24 GB ở đâu trước 26/11 (RunPod/Lambda/Colab Pro)?
2. 10–20 ảnh demo từ ảnh tham chiếu hay render scene 3D — ai chốt danh sách + nhãn nguồn?
3. Pháp chế có cho chiếu output NC dạng "tham khảo kỹ thuật" trước khách JR không?
4. Khách cung cấp ảnh drone B-14/T-07 và GCP khi nào?
5. Ngưỡng confidence lọc điểm chốt bằng thực nghiệm trên ảnh nào?
6. Có đo trên ray thép không, hay chỉ mố/tà vẹt?
7. ODM/AGPL host nội bộ có trigger mở source không?
8. Pi4 eval sau demo: ai chuẩn bị env CUDA 12.6, tiêu chí thắng MASt3R là gì?
