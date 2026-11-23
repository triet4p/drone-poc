# 点群ソース (Nguồn point-cloud): đám mây điểm có sẵn cho khu vực demo và khả năng gắn ảnh

> Ngôn ngữ: tiếng Việt; thuật ngữ gốc tiếng Nhật trong ngoặc đơn. Mọi khẳng định về giấy phép, hạn mức, URL đều kèm link nguồn. Số liệu không kiểm chứng trực tiếp được đánh dấu `[推定]`.

## 1) Phạm vi (範囲・スコープ)

**Mục tiêu:** trả lời hai câu hỏi trong 30 phút đọc: (a) nên tải một đám mây điểm thật (点群) hay tổng hợp (合成点群) từ geometry 3D nội bộ; (b) một điểm trong cloud có gắn được với ảnh (写真) gốc hay không, và cần metadata gì.

**Bối cảnh:** tuyến demo là hành lang fictional B-14/T-07 đặt trên hình học thật của tuyến 東海道本線 đoạn gần 根府川 (Nebukawa, 小田原) km 12k400–15k600. Yêu cầu: click một điểm trên ray → chi tiết có metrics + ảnh tương ứng; hình học tương đối (相対精度) phải đúng, cao độ tuyệt đối (絶対標高) bổ sung sau.

**Ràng buộc:** ngân sách zero, chỉ giấy phép mở; CPU-only cho demo, on-prem/offline về lâu dài; demo 26/11, MVP sau đó. Báo cáo này không phải tư vấn pháp lý (法的助言ではない); bảng license cần pháp chế xác nhận trước khi dùng thương mại.

**Ngoài phạm vi:** engine 3D và nền bản đồ đã có ở `04a-free-geo-data.md`, `04b-3d-viewer.md`; báo cáo này chỉ đi sâu vào point-cloud + ảnh/pose đi kèm.

## 2) Findings (調査結果)

### 2.1 Point-cloud mở của Nhật (日本のオープンデータ点群)

| Nguồn | Vùng phủ 根府川/小田原 | Đối tượng | Format | Dung lượng | License (nguyên văn) | Ảnh/pose đi kèm | Click-to-photo |
|---|---|---|---|---|---|---|---|
| 神奈川県 県西部 R1 ([G空間情報センター](https://www.geospatial.jp/ckan/dataset/kanagawa-2019-pointcloud)) — **ứng viên #1** | Có: 小田原市 trong 10市町 ([trang dataset](https://www.geospatial.jp/ckan/dataset/kanagawa-2019-pointcloud)) | Địa hình airborne, 4点/m²以上, mục đích森林資源解析 | LAS (オリジナル) + TXT + CSV 0.5 m + DXF + ortho JPEG/TIF | 1 file [推定]数百MB–数GB; corridor 3,2 km [推定] 1–5 GB raw | Điều khoản riêng của tỉnh, **không phải CC chuẩn**: 知りえた情報を犯罪に使用しないこと; 損害に県は責任を負わない; 制作物には「データ提供：（神奈川県環境農政局緑政部森林再生課）」と明示 ([cùng trang](https://www.geospatial.jp/ckan/dataset/kanagawa-2019-pointcloud)); ô 使用許諾 trống → pháp chế xác nhận trước thương mại | Ortho chụp cùng chuyến bay (空中写真を正射変換) nhưng là ảnh正射 ghép sẵn — **không pose từng tấm, không photo ID từng điểm** | Chỉ gián tiếp: tra ortho tile gần nhất |
| 神奈川県 R6 ([dataset](https://www.geospatial.jp/ckan/dataset/kanagawa-2024-pointcloud)) | Có: 小田原市 ([trang R1 trỏ sang](https://www.geospatial.jp/ckan/dataset/kanagawa-2019-pointcloud)) | Tương tự, đo令和6年 | LAS + TXT [推定] | Tương tự [推定] | Điều khoản tỉnh tương tự [推定 — kiểm tra trang R6 trước khi tải] | Ortho [推定] | Như trên |
| VIRTUAL SHIZUOKA ([tỉnh](https://www.pref.shizuoka.jp/machizukuri/1049255/1052183.html), [tải](https://www.geospatial.jp/ckan/dataset?q=VIRTUAL+SHIZUOKA&organization=shizuokapref&sort=metadata_modified+desc)) — **ứng viên #2 (dự phòng)** | Không phủ 根府川 (静岡県のみ); giá trị là tiền lệ license sạch | Địa hình + đô thị, có RGB +受光強度 ([trang tỉnh](https://www.pref.shizuoka.jp/machizukuri/1049255/1052183.html)) | LAS/LAZ [推定] | 1 tile [推定]数百MB | **CC BY 4.0**: 「CC BY 4.0に基づいたオープンデータ」「許可不要で二次利用できる商用可能データ」 ([nguyên văn](https://www.pref.shizuoka.jp/machizukuri/1049255/1052183.html)) | Viewer ([platform](https://3dview.tokyo-digitaltwin.metro.tokyo.lg.jp/#share=s-gju1p6ppJJ2Z6jea)); không pose từng tấm [推定] | Chỉ tra lân cận |
| 国土地理院 点群データ ([GSI](https://web1.gsi.go.jp/gazochosa/tengun.html)) | Xem [刊行範囲](https://maps.gsi.go.jp/#5/36.385913/138.669434/&base=blank&ls=blank%7C3d_pcd_area_dtil&disp=11&lcd=3d_pcd_area_dtil&vs=c1g1j0h0k0l0u0t0z0r1s0m0f1&d=m) — **loại vì mất phí** | 表層面 (địa hình + nhà +植生), 4点/m², 25 cm RMS ([GSI](https://web1.gsi.go.jp/gazochosa/tengun.html)) | LAZ (LAS 1.2 PDRF3), theo 2次メッシュ | 数100MB–数GB/file ([GSI](https://web1.gsi.go.jp/gazochosa/tengun.html)) | **Có phí + thủ tục**: 受注生産, ２次メッシュ 13,900円税込; 複製・使用は測量法29/30条申請 ([GSI](https://web1.gsi.go.jp/gazochosa/tengun.html)) | Không | Không |
| 国土交通データプラットフォーム 3次元点群 ([利用規約 PDF](https://www.mlit.go.jp/common/001389742.pdf)) | Tùy dataset | Tùy loại | Tùy (LAS/LAZ/E57) | Tùy | CC BY 4.0 mặc định nhưng **上位規約優先** — dataset có điều khoản riêng thì riêng thắng ([第11条](https://www.mlit.go.jp/common/001389742.pdf)) | Tùy | Tùy |
| 道路MMS (xRoad) ([database](https://www.xroad.mlit.go.jp/database/438/)) | 直轄国道のみ, không gồm tuyến JR | Đường bộ MMS + ảnh | Không tải trực tiếp | — | **Loại**: 要日本デジタル道路地図協会との使用許諾契約 ([xRoad](https://www.xroad.mlit.go.jp/database/438/)) | Có nhưng khóa | Không khả thi |

**Kết luận mục 2.1:**

- Vùng 根府川 chỉ có một nguồn mở miễn phí là Kanagawa R1/R6 (LAS, ghi công dòng chữ tỉnh). Nhưng ba giới hạn chí mạng: (1) đo cho rừng — 「市街地・港湾部は未取得」「国有林・軍事基地周辺も未取得」([dataset](https://www.geospatial.jp/ckan/dataset/kanagawa-2019-pointcloud)), ga根府川/khu ven biển có thể trống, phải kiểm tra範囲図 trước khi tải; (2) airborne 4点/m² không bắt mặt dưới cầu/chi tiết ray; (3) không pose/ID ảnh từng điểm, chỉ ortho ghép sẵn.
- **Không tồn tại point-cloud mở của đúng cầu/ray/hầm tuyến này** [推定 — đã tra G空間情報センター theo địa danh, GSI, MLIT platform; MMS đường bộ không áp dụng cho JR]. Đây là kết quả "none" có bằng chứng cho câu hỏi real rail cloud.

### 2.2 Point-cloud đường sắt/cầu/hầm quốc tế (海外の鉄道・橋梁点群)

| Dataset | Coverage | Đối tượng | Format | Size | License (nguyên văn) | Ảnh/pose | Click-to-photo |
|---|---|---|---|---|---|---|---|
| **ArchScanLib** ([Apollo](https://www.repository.cam.ac.uk/items/190195f8-082c-40eb-b240-d5c34c165b5a), DOI [10.17863/CAM.114586](https://doi.org/10.17863/CAM.114586)) — **ứng viên #3** | 16 cầu/viaduct vòm gạch UK | Cầu đường sắt thật (FARO Focus 3D nhiều trạm); đọc bằng CloudCompare (bật faro ls support) | `.fls` + `.lsproj` | **81.49 GB** ZIP tổng + README | **CC BY 4.0** ([CC deed](https://creativecommons.org/licenses/by/4.0/)) — thương mại được, ghi công | Dự án chị em ArchImageLib có ảnh nhưng record này chỉ có cloud, không pose từng điểm [推定] | Không trực tiếp |
| OpenTopography ([portal](https://portal.opentopography.org/datasets)) | Toàn cầu, từng survey | Địa hình + Class 10 Rail / Class 17 Bridge Deck (vd [Indiana](https://portal.opentopography.org/lidarDataset?opentopoID=OTLAS.062012.4326.1), [Utah](https://portal.opentopography.org/lidarDataset?opentopoID=OTLAS.092018.6326.1)) | LAZ theo vùng | [推定]数百MB–数GB | Tùy dataset, kiểm tra từng trang | Không | Không |
| USGS 3DEP ([products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services), [download FAQ](https://www.usgs.gov/faqs/how-do-i-download-national-map-data-products)) | Toàn Mỹ | Địa hình airborne | LAS/LAZ (S3 Requester Pays) | Tùy project | **Public domain**, free, no restrictions | Không | Không |
| AHN Hà Lan ([portal](https://basisdata.nl/hwh-portal/download/index.html), [dataroom](https://www.ahn.nl/dataroom)) | Toàn Hà Lan | Địa hình | LAZ, EPSG:7415 | Tùy tile | AHN1–4 **CC0**, AHN5–6 **CC BY 4.0** | Không | Không |
| UK Environment Agency ([portal](https://environment.data.gov.uk/survey), [programme](https://www.data.gov.uk/dataset/f0db0249-17b3-4036-9e65-309148c97ce4/lidar-composite-dtm)) | England | Địa hình ([archive](https://www.data.gov.uk/dataset/977a4ca4-175b-4f26-baa7-b566bd7ca7bf/lidar-time-stamped-point-cloud)) | LAZ tile 5 km | Tùy tile | **Open Government Licence** + attribution từng trang | Không | Không |
| OpenHeritage3D Alvord Lake Bridge ([project](https://openheritage3d.org/project.php?id=n8mh-mm15), DOI [10.26301/n8mh-mm15](https://doi.org/10.26301/n8mh-mm15)) | 1 cầu BT 1889, San Francisco | Cầu thật (Faro Focus S120); link tải gửi qua email | Terrestrial LiDAR | **4.02 GB** | **CC BY-NC-SA** — cấm thương mại → chỉ tham khảo nội bộ | Video ([YouTube](https://www.youtube.com/watch?v=_N5Mm-KNG78)), không pose gốc | Không |

**Kết luận mục 2.2:** cầu đường sắt thật duy nhất dùng được thương mại là ArchScanLib (CC BY 4.0), nhưng vòm gạch UK — sai typology so với B-14, sai khổ đường; chỉ làm reference nội bộ và phải ghi xuất xứ. Không dataset quốc tế nào phủ tuyến Nhật.

### 2.3 Dataset photogrammetry có ảnh + pose + cloud (画像・ポーズ付き)

| Dataset | Ảnh | Pose/intrinsics | Cloud | License | Rail relevance |
|---|---|---|---|---|---|
| ETH3D ([datasets](https://eth3d.ethz.ch/datasets), [docs](https://www.eth3d.net/documentation)) | Có | Có: `cameras.txt` + `images.txt` (COLMAP) | Có (scan + `points3D.txt`) | **CC BY-NC-SA 4.0** | Không có cảnh rail |
| Tanks and Temples ([download](https://tanksandtemples.org/download/)) | Có: video 4K + image set (có scene **Train**) | Một phần: COLMAP `.log`; intrinsics không công bố, gợi ý近似 fx=fy=0.7W | Có: `.ply` ground-truth | **Non-commercial** — mâu thuẫn CC BY trên trang license, coi như cấm thương mại | Train là đầu máy trưng bày, không phải corridor |
| DTU MVS ([official](https://roboimagedata.compute.dtu.dk/?page_id=36)) | Có (SampleSet 6.3 GB) | Có: calibration MATLAB + projection matrices | Có | **Citeware** (điều kiện trích dẫn, không phải license chuẩn) | Vật lab, không rail |
| Mip-NeRF 360 ([project](https://jonbarron.info/mipnerf360/)) | Có (`360_v2.zip`) | COLMAP poses tự chạy | Không (suy từ NeRF) | **Không công bố dataset license** — coi như chưa được phép | Không rail |

**Kết luận mục 2.3:** mọi dataset ảnh+pose+cloud học thuật đều cấm/không rõ thương mại và không có corridor đường sắt. Giá trị duy nhất: mượn **định dạng metadata** (COLMAP `cameras.txt`/`images.txt`) làm mẫu cho pipeline synthetic (mục 5).

### 2.4 Kho model 3D (3Dモデルリポジトリ)

| Kho | Cầu/hầm + cloud + ảnh? | License | Kết luận |
|---|---|---|---|
| Sketchfab ([filters](https://www.sketchfab.com/blogs/community/refine-downloadable-model-searches-with-new-license-filters/), [licenses](https://sketchfab.com/licenses)) | Listing "Bridge – Point cloud" ([model](https://sketchfab.com/3d-models/bridge-point-cloud-1a8837d2c77f4400a0893ae1c15e3057), `.las` ~100M/40M/10M pts, ghi NoAI) — NoAI ≠ CC, CC/download chưa xác nhận | Tùy model, kiểm tra tay | Loại cho 26/11 |
| Smithsonian 3D ([explore](https://3d.si.edu/explore)) | Model CC0 mọi mục đích, nhưng **không tìm thấy cầu/hầm đường sắt** | CC0 theo từng object | Loại: sai đối tượng |
| OpenHeritage3D ([home](https://openheritage3d.org/project.php?id=Home)) | Alvord (mục 2.2); Ponte Vecchio ([project](https://openheritage3d.org/project.php?id=D6FS3W)) Upcoming, chưa tải được | CC BY-NC-SA → cấm thương mại | Chỉ nội bộ |

### 2.5 Gắn điểm với ảnh: cần metadata gì (点と写真の対応付け)

Để click một điểm → hiện đúng ảnh, cần một trong hai cơ chế:

- (A) **Per-point linkage (厳密):** mỗi điểm mang `photoId` + tọa độ pixel. Cần lúc thu thập: intrinsics (fx, fy, cx, cy, méo), extrinsics từng tấm (R, t), timestamp đồng bộ LiDAR–camera, ID ảnh mỗi điểm.
- (B) **Proximity lookup (近傍検索):** click → `pickPosition` → tìm ảnh gần nhất trong bán kính; chỉ cần vị trí mỗi trạm ảnh.

Thực trạng dataset mở:

- LiDAR airborne (Kanagawa, GSI, USGS, AHN, EA, OpenTopography) đều **không có (A)**; Kanagawa chỉ có ortho正射 ghép sẵn, không pose/ID từng điểm.
- MMS đường bộ có rig đồng bộ nhưng **khóa sau hợp đồng DRM**.
- Dataset học thuật đủ (B), một phần (A) qua COLMAP, nhưng cấm thương mại + không phải rail.
- Trên CesiumJS, `scene.pick` + `scene.pickPosition` với `.pnts` chỉ cho **vị trí gần đúng từ depth buffer, không lộ photo URL** — phải giữ bảng `photos[{position, imageUrl}]` và tìm nearest trong ngưỡng ([Scene docs](https://cesium.com/learn/cesiumjs/ref-doc/Scene.html), [spec](https://github.com/CesiumGS/3d-tiles/blob/main/specification/TileFormats/PointCloud/README.adoc)). Muốn đúng từng điểm phải dùng attribute từng điểm hoặc spatial index riêng.

**Kết luận mục 2.5:** dữ liệu mở chỉ làm được (B) "gần đúng". Linkage (A) đúng từng điểm **chỉ khả thi trong pipeline synthetic (c)** nơi ta tự gán `photoId` lúc sampling.

### 2.6 Viewer + format + point budget (表示形式・容量)

| Đường đi | Convert tool (license) | Output/hosting | Size [推定] | Point budget demo |
|---|---|---|---|---|
| LAS/LAZ → Potree | [PotreeConverter](https://github.com/potree/PotreeConverter) **BSD 2-Clause** (`PotreeConverter input.las -o out`; v2.0 ra 3 file chưa nén, 1.7 có LAZ optional) | Self-host viewer + file tĩnh | Gấp 1–1,5× raw | 10–50M điểm; corridor mục tiêu **5–20M** |
| LAZ → 3D Tiles (giữ CesiumJS) | [py3dtiles](https://py3dtiles.org/main/) **Apache-2.0** ([LICENSE](https://github.com/Oslandia/py3dtiles/blob/master/LICENSE)): `pip install "py3dtiles[las]"`, `py3dtiles convert input.laz --out ./tiles` ([install](https://py3dtiles.org/main/install.html)) | `tileset.json` tĩnh cạnh app, không token | Tương tự | Cùng budget; chung globe với PLATEAU/terrain ở 04a |
| Giữ `.pnts` styling | CesiumJS **Apache-2.0** (đã chốt 04a) | Per-point color có trong tile nhưng **pick không lộ property điểm** ([spec](https://github.com/CesiumGS/3d-tiles/blob/main/specification/TileFormats/PointCloud/README.adoc)) → vẫn cần bảng ảnh riêng | — | Như trên |

**Kết luận mục 2.6:** cả hai đường đều self-host, offline, CPU-only (convert một lần). Vì frontend đã chốt CesiumJS, **ưu tiên py3dtiles → 3D Tiles**; Potree dự phòng khi cần tool đo đạc chuyên sâu.

### 2.7 Ba phương án thực tế (現実的な3案)

| Phương án | License | Effort [推定] | Visual credibility | Click-to-photo |
|---|---|---|---|---|
| (a) Cloud đường sắt thật corridor | **Không tồn tại** (chứng cứ mục 2.1) | ∞ | — | — |
| (a′) Terrain thật Kanagawa R1/R6 + cấu trúc synthetic | Điều khoản tỉnh + ghi công森林再生課 (pháp chế xác nhận) | 0,5–1 ngày: kiểm tra範囲図 → tải 1–2 tile → cắt bbox → convert | Cao cho địa hình; cầu/ray synthetic phải ghi rõ | (B) proximity với ortho |
| (b) Cầu thật generic (ArchScanLib CC BY 4.0) | CC BY 4.0 dùng được; Alvord NC chỉ nội bộ | 0,5 ngày tải mẫu 1 cầu (không tải cả 81 GB) + 0,5 ngày convert | Trung bình: vòm gạch UK ≠ B-14, stakeholder sẽ hỏi | Không (không ảnh gốc) |
| (c) **Synthetic từ geometry nội bộ (khuyến nghị)** | Nội bộ, sạch 100% | 1–1,5 ngày: sample mesh → gán photoId từ 11 ảnh demo → convert → viewer | Cao cho "tương đối đúng" (cùng geometry demo); ghi nhãn合成点群 | **(A) đúng từng điểm** qua attribute `photoId` + bảng ảnh |

## 3) Bảng so sánh tổng (比較表)

| Dataset | Coverage | Object | Format | Size | License | Ảnh/pose | Click-to-photo | Effort |
|---|---|---|---|---|---|---|---|---|
| Kanagawa R1/R6 ([link](https://www.geospatial.jp/ckan/dataset/kanagawa-2019-pointcloud)) | 小田原市含む | Địa hình airborne | LAS/TXT/ortho | Tile [推定]数百MB–GB | Điều khoản tỉnh + ghi công (phi CC) | Ortho, không pose | (B) lân cận | 0,5–1 ngày |
| VIRTUAL SHIZUOKA ([link](https://www.pref.shizuoka.jp/machizukuri/1049255/1052183.html)) | 静岡のみ | Địa hình+đô thị RGB | LAS/LAZ | [推定]数百MB/tile | **CC BY 4.0** | Viewer, không pose | (B) | Tham khảo |
| GSI点群 ([link](https://web1.gsi.go.jp/gazochosa/tengun.html)) | 全国一部 | 表層面 | LAZ | 数100MB–数GB/file | **Trả phí 13.900円 +測量法申請** | Không | Không | Loại |
| MLIT platform ([規約](https://www.mlit.go.jp/common/001389742.pdf)) | Tùy dataset | Tùy | Tùy | Tùy | CC BY 4.0 mặc định,上位規約優先 | Tùy | Tùy | Tra cứu |
| xRoad MMS ([link](https://www.xroad.mlit.go.jp/database/438/)) | 直轄国道 | Đường+MMS | Không tải trực tiếp | — | **Hợp đồng DRM** | Có nhưng khóa | Không | Loại |
| ArchScanLib ([link](https://www.repository.cam.ac.uk/items/190195f8-082c-40eb-b240-d5c34c165b5a)) | UK 16 cầu | Cầu vòm FARO | fls/lsproj | **81.49 GB** | **CC BY 4.0** | Không pose | Không | 1 ngày subsample |
| Alvord Lake ([link](https://openheritage3d.org/project.php?id=n8mh-mm15)) | 1 cầu SF | Cầu BT Faro | Terrestrial | **4.02 GB** | **CC BY-NC-SA** (phi thương mại) | Video only | Không | Nội bộ only |
| USGS 3DEP ([link](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)) | Mỹ | Địa hình | LAS/LAZ | Tùy | Public domain | Không | Không | Loại (sai nước) |
| AHN ([link](https://basisdata.nl/hwh-portal/download/index.html)) | Hà Lan | Địa hình | LAZ EPSG:7415 | Tùy | CC0 (1–4) / CC BY 4.0 (5–6) | Không | Không | Loại (sai nước) |
| UK EA ([link](https://environment.data.gov.uk/survey)) | England | Địa hình | LAZ 5 km | Tùy | OGL | Không | Không | Loại (sai nước) |
| ETH3D ([link](https://eth3d.ethz.ch/datasets)) | Generic | Cảnh + scan | images+txt+scan | [推定]数百MB/scene | **CC BY-NC-SA 4.0** | Có pose COLMAP | (B) tốt | Loại thương mại |
| T&T ([link](https://tanksandtemples.org/download/)) | Generic (+Train) | Cảnh + `.ply` | video/images/log/ply | [推定] GB/scene | **Non-commercial** | Pose một phần | (B) | Loại thương mại |
| Synthetic nội bộ (c) | Corridor B-14/T-07 | Ray/cầu/hầm | LAS→3D Tiles | 5–20M pts [推定] | Nội bộ | 11 ảnh + pose tự đặt | **(A) từng điểm** | 1–1,5 ngày |

## 4) Khuyến nghị (推奨)

| Quyết định | Chọn | Vì sao một dòng |
|---|---|---|
| Demo 26/11 | **(c) synthetic + nhãn合成点群**: sample từ mesh hiện có, gán photoId từ 11 ảnh demo, serve qua 3D Tiles trong CesiumJS sẵn có | Cách duy nhất đạt click-điểm→ảnh đúng từng điểm trong 1–1,5 ngày, license sạch,相対 đúng vì cùng geometry |
| Nền địa hình | **(a′) thử 1 tile Kanagawa R1/R6** song song (timebox 2 h kiểm tra範囲図; quá giờ bỏ) | Terrain thật tăng credibility; thất bại không chặn demo vì terrain phẳng vẫn chạy |
| Cầu thật | ArchScanLib subsample **chỉ nội bộ/so sánh**, không vào demo chính | Sai typology (vòm gạch UK vs B-14); stakeholder sẽ hỏi |
| Tuyệt đối không | GSI trả phí, MMS xin phép, dataset NC vào bản thương mại, tải cả 81 GB ArchScanLib | Tốn tiền/thời gian/phạm license |
| MVP | Terrain Kanagawa thật + cấu trúc synthetic đã đăng ký tọa độ; đo thật khi có hợp đồng riêng | On-prem sạch license, absolute height tính sau |

Thanh attribution demo (thường trực): `点群: 合成品（自社3Dモデルより抽出） · 地形: データ提供：（神奈川県環境農政局緑政部森林再生課）(nếu dùng) · 参考: ArchScanLib CC BY 4.0 (nếu trích)`.

## 5) Kiến trúc / đặc tả (構成・統合仕様)

```text
sampling (offline, 1 lần):
  mesh ray/cầu/hầm nội bộ → sample Poisson (mục tiêu 5–20M pts [推定])
    → mỗi điểm: {x,y,z (hệ corridor), normal, class (rail/sleeper/deck/pier/tunnel),
                 photoId (trạm ảnh gần/visible nhất), rgb (từ ảnh hoặc mã lớp)}
      → LAS (extra-bytes photoId) → py3dtiles convert → /public/tiles/corridor/tileset.json
frontend (CesiumJS sẵn có):
  Cesium3DTileset(corridor) + imagery GSI + terrain + GeoJSON B-14/T-07
  click → scene.pick trúng tileset → đọc photoId attribute (A), fallback pickPosition (B)
    → GET /api/photos/{photoId} → panel metrics + ảnh nội bộ
metadata ảnh (mẫu COLMAP-like, học từ ETH3D/T&T):
  photos.json: [{photoId, url, stationPos [lon,lat,h], intrinsics {fx,fy,cx,cy},
                 extrinsics {R,t}, timestamp, targetElement (P3/G2…)}]
```

**Đặc tả tích hợp tối thiểu:** `GET /api/pointcloud/config` → `{tilesetUrl, photosIndexUrl, offline}`; `GET /api/photos/nearest?x=&y=&z=` (dự phòng B); mọi URL qua allowlist `geoSources.ts` (kế thừa 04a). UI ghi rõ "相対表示・絶対標高は参考値".

## 6) Kế hoạch 2 ngày vs MVP (2日計画・MVP)

**Ngày 1 (24/11) — synthetic + click-to-photo:** sampler từ mesh hiện có (0,5 ngày); gán photoId + photos.json từ 11 ảnh demo (2–3 h); convert py3dtiles + gắn Cesium + panel ảnh/metrics (2–3 h). **Cuối ngày:** click điểm ray → ảnh đúng, geometry khớp B-14. Song song timebox 2 h: kiểm tra範囲図 Kanagawa tile phủ ga根府川.

**Ngày 2 (25/11) — nền thật + đóng băng:** tải 1–2 tile Kanagawa → cắt bbox → convert backdrop (0,5 ngày; bỏ qua nếu tile trống đô thị); gắn attribution + nhãn合成点群; rehearsal online/offline. **Đóng băng tối 25/11.**

**MVP tối thiểu:** corridor synthetic (A) + terrain Kanagawa (hoặc phẳng phóng đại) + photos.json đủ pose tự đặt. **Post-meeting:** đo MMS/cầm tay khi có hợp đồng;絶対標高 từ GSI DEM ở 04a.

## 7) Rủi ro (リスク)

| # | Rủi ro | Mức | Giảm thiểu |
|---|---|---|---|
| 1 | Stakeholder hiểu "point-cloud thật" = đo thật tuyến này | Cao nhất | Nhãn合成点群常時 + 1 slide相対/絶対; real rail cloud mở không tồn tại (mục 2.1) |
| 2 | Tile Kanagawa trống khu ga/cầu (rừng-only) | Cao | Kiểm tra範囲図/ortho trước khi tải full; fallback terrain phẳng |
| 3 | Điều khoản Kanagawa (phi CC) hiểu sai khi thương mại | Trung bình | Chỉ nền demo; pháp chế xác nhận; không redistribute tile gốc |
| 4 | photoId synthetic bị coi là "giả dữ liệu" | Trung bình | Ghi rõ pose ảnh minh họa theo trạm demo, không phải calibration đo đạc |
| 5 | Convert FARO 81 GB tốn ngày | Trung bình | Chỉ subsample 1 cầu nếu cần; ngoài critical path |
| 6 | pickPosition lệch so với điểm gốc | Thấp (đã có A bù) | photoId attribute làm truth, pickPosition chỉ dự phòng |
| 7 | License NC lọt vào bản giao | Thấp | Bảng mục 3 làm checklist; CI liệt kê nguồn tile |
| 8 | Kỳ vọng absolute height ngay ở demo | Thấp | UI ghi相対表示; GSI DEM 5 m ở 04a làm sau |

## 8) References (参考文献・URL一覧)

- 神奈川県 R1県西部3次元点群 (LAS, 小田原市含む, điều khoản tỉnh): https://www.geospatial.jp/ckan/dataset/kanagawa-2019-pointcloud
- 神奈川県 R6県西部・相模原: https://www.geospatial.jp/ckan/dataset/kanagawa-2024-pointcloud
- VIRTUAL SHIZUOKA (CC BY 4.0, RGB+強度): https://www.pref.shizuoka.jp/machizukuri/1049255/1052183.html
- VIRTUAL SHIZUOKA datasets (G空間情報センター): https://www.geospatial.jp/ckan/dataset?q=VIRTUAL+SHIZUOKA&organization=shizuokapref&sort=metadata_modified+desc
- VIRTUAL SHIZUOKA platform viewer: https://3dview.tokyo-digitaltwin.metro.tokyo.lg.jp/#share=s-gju1p6ppJJ2Z6jea
- GSI点群データ (LAZ, 受注生産13,900円, 測量法29/30条): https://web1.gsi.go.jp/gazochosa/tengun.html
- GSI刊行範囲: https://maps.gsi.go.jp/#5/36.385913/138.669434/&base=blank&ls=blank%7C3d_pcd_area_dtil&disp=11&lcd=3d_pcd_area_dtil&vs=c1g1j0h0k0l0u0t0z0r1s0m0f1&d=m
- 国土交通データプラットフォーム利用規約 (CC BY 4.0原則・上位規約優先, PDF): https://www.mlit.go.jp/common/001389742.pdf
- xRoad MMS (要DRM協会許諾契約): https://www.xroad.mlit.go.jp/database/438/
- ArchScanLib (CC BY 4.0, 81.49 GB, FARO, DOI:10.17863/CAM.114586): https://www.repository.cam.ac.uk/items/190195f8-082c-40eb-b240-d5c34c165b5a
- OpenHeritage3D Alvord Lake Bridge (CC BY-NC-SA, 4.02 GB, DOI:10.26301/n8mh-mm15): https://openheritage3d.org/project.php?id=n8mh-mm15
- Alvord preview video: https://www.youtube.com/watch?v=_N5Mm-KNG78
- OpenHeritage3D home: https://openheritage3d.org/project.php?id=Home
- OpenTopography Find Data: https://portal.opentopography.org/datasets
- OpenTopography Indiana (Class 10/17): https://portal.opentopography.org/lidarDataset?opentopoID=OTLAS.062012.4326.1
- OpenTopography Utah: https://portal.opentopography.org/lidarDataset?opentopoID=OTLAS.092018.6326.1
- USGS 3DEP products (public domain): https://www.usgs.gov/3d-elevation-program/about-3dep-products-services
- USGS download FAQ: https://www.usgs.gov/faqs/how-do-i-download-national-map-data-products
- AHN download portal: https://basisdata.nl/hwh-portal/download/index.html
- AHN dataroom (LAZ, EPSG:7415): https://www.ahn.nl/dataroom
- UK EA Survey portal: https://environment.data.gov.uk/survey
- UK National LIDAR Programme: https://www.data.gov.uk/dataset/f0db0249-17b3-4036-9e65-309148c97ce4/lidar-composite-dtm
- UK Time-Stamped Point Cloud (OGL): https://www.data.gov.uk/dataset/977a4ca4-175b-4f26-baa7-b566bd7ca7bf/lidar-time-stamped-point-cloud
- ETH3D datasets: https://eth3d.ethz.ch/datasets — docs: https://www.eth3d.net/documentation
- Tanks and Temples download (non-commercial): https://tanksandtemples.org/download/
- DTU MVS (citeware, 6.3 GB): https://roboimagedata.compute.dtu.dk/?page_id=36
- Mip-NeRF 360 (license未記載): https://jonbarron.info/mipnerf360/
- Sketchfab license filters: https://www.sketchfab.com/blogs/community/refine-downloadable-model-searches-with-new-license-filters/
- Sketchfab licenses: https://sketchfab.com/licenses
- Sketchfab bridge point-cloud (NoAI,要確認): https://sketchfab.com/3d-models/bridge-point-cloud-1a8837d2c77f4400a0893ae1c15e3057
- Smithsonian 3D explore: https://3d.si.edu/explore
- PotreeConverter (BSD 2-Clause): https://github.com/potree/PotreeConverter
- py3dtiles docs (Apache-2.0): https://py3dtiles.org/main/ — install: https://py3dtiles.org/main/install.html — LICENSE: https://github.com/Oslandia/py3dtiles/blob/master/LICENSE
- Cesium Scene.pick/pickPosition: https://cesium.com/learn/cesiumjs/ref-doc/Scene.html
- 3D Tiles PointCloud spec (pick制限): https://github.com/CesiumGS/3d-tiles/blob/main/specification/TileFormats/PointCloud/README.adoc

---

**KEY DECISIONS**

1. Demo 26/11 dùng合成点群 từ geometry nội bộ (c), không tải cloud thật làm nội dung chính.
2. Nền địa hình thử Kanagawa R1/R6 LAS timebox 2 h; thất bại thì terrain phẳng, không chặn demo.
3. Click-to-photo theo cơ chế (A) photoId attribute — chỉ pipeline synthetic mới có.
4. Viewer giữ CesiumJS + py3dtiles (Apache-2.0); Potree dự phòng.
5. ArchScanLib (CC BY 4.0) chỉ tham khảo nội bộ, không vào demo chính vì sai typology.
6. Loại: GSI trả phí, MMS cần hợp đồng, mọi dataset NC khỏi bản thương mại.
7. UI ghi常時「合成点群・相対表示」+ attribution tỉnh nếu dùng terrain Kanagawa.
8. Tuyệt đối cao độ dời sang MVP, dùng GSI DEM 5 m ở 04a.

**OPEN QUESTIONS**

1. Tile Kanagawa nào phủ đúng ga根府川 và có dữ liệu đô thị? — kiểm tra範囲図 trước 25/11.
2. Pháp chế có chấp nhận điều khoản tỉnh Kanagawa (phi CC) cho demo thương mại không?
3. 11 ảnh demo có đủ station ước lượng để gán photoId đáng tin không?
4. Point budget cuối cùng cho corridor 3,2 km là bao nhiêu trên máy demo thực tế?
5. Có cần đo đạc thật (MMS/cầm tay) cho MVP không, thủ tục tuyến JR ra sao?
6. PhotoId attribute có giữ được qua py3dtiles batch-table không, hay bảng tra cứu riêng?
7. Có công bố pipeline synthetic + photos.json mẫu cho đối tác kiểm chứng相対精度 không?
8. Khi nào xin thủ tục測量法 nếu redistribute tile Kanagawa/GSI trong bản on-prem?
