# Yêu cầu hệ thống — Drone × AI Infrastructure Inspection MVP

| | |
|---|---|
| Phiên bản | 0.2 (đã đối chiếu 3 tài liệu research, 20-11-2026) |
| Ngày | 2026-11-20 |
| Mục tiêu demo | 2026-11-26, khách hàng đường sắt Nhật |
| Tài liệu liên quan | `research/01-data.md`, `research/02-model.md`, `research/03-architecture.md`, `SCOPE.md` |
| Nguyên tắc | Dữ liệu thật, model thật, chạy on-prem, AI chỉ đề xuất — kỹ sư quyết định |

Tài liệu này mô tả **hệ thống phải làm gì**, không mô tả cách làm. Mọi yêu cầu đều có mã để trace sang test/acceptance và sang màn hình demo gốc (`docs/軌道・構造物点検 確認アプリ（デモ）.html`).

---

## 1. Mục tiêu

Biến ảnh/video drone thành danh sách 変状 (defect) có vị trí theo キロ程 và 部材, có lịch sử so sánh giữa các lần kiểm tra, và bản nháp 点検調書 mà kỹ sư đã xác nhận — trong một vòng lặp vận hành khép kín: kế hoạch bay → chụp → AI trích xuất → kỹ sư xác nhận → yêu cầu chụp lại → ưu tiên bảo trì → 調書.

**Giá trị khác biệt không nằm ở detector**, mà ở: (a) ràng buộc vận hành thật (線路閉鎖, thời tiết, giới hạn giờ bay), (b) truy vết nguồn gốc từng kết luận, (c) vòng lặp chụp lại, (d) 調書 chỉ chứa nội dung đã được kỹ sư xác nhận.

---

## 2. Personas và workflow

| Persona | Việc chính | Quyền |
|---|---|---|
| 点検技術者 (kỹ sư kiểm tra) | Xem candidate, đối chiếu ảnh, chọn 判定区分, comment, yêu cầu chụp lại, xuất 調書 | Review, confirm, export |
| 撮影担当 (người lập kế hoạch bay) | Nhập lịch bay, gán chuyến, kiểm tra ràng buộc, xem tuyến | Flight planning |
| 管理者 | Tài khoản, cấu hình ngưỡng, model version, backup | Admin |
| 閲覧者 (khách hàng) | Xem dashboard/調書 đã xuất | Read-only (COULD) |

Workflow chuẩn: **計画 → 撮影 → 取込 → AI抽出 → 技術者確認 → 解析/比較 → 優先度 → 調書**.

---

## 3. Ranh giới hệ thống

**Trong phạm vi MVP**
- 1 tuyến, 1 hướng, một đoạn ~1–3 km: 1 cầu bê tông (trụ, dầm, mố), 1 cửa hầm, 1 mái dốc.
- Nhập ảnh tĩnh độ phân giải cao, video, point cloud/orthophoto.
- Inference thật, đánh giá model thật, review của kỹ sư, so sánh 2 epoch, xếp ưu tiên, xuất 調書.
- Chạy hoàn toàn on-prem, không phụ thuộc Internet khi vận hành.

**Ngoài phạm vi (WON'T trong MVP)**
- Điều khiển drone/autopilot, telemetry thời gian thực.
- Tích hợp CMMS/work order, ERP, SSO doanh nghiệp.
- Multi-tenant, multi-line, cloud SaaS.
- App mobile native; offline field app.
- Tự động ra kết luận cuối cùng hoặc tự động nộp 調書.
- Đo bề rộng nứt tuyệt đối cấp mm như số liệu chính thức.

**Kiến trúc tham chiếu** (chi tiết `research/03-architecture.md`): Next.js 16/React 19 + TS; FastAPI + Celery/Redis; PostgreSQL 18.7 + PostGIS 3.7; filesystem private sau storage adapter (không MinIO CE); tusd upload; DZI/OpenSeadragon, HLS, Potree, TiTiler; DOCX bằng python-docx + PDF qua LibreOffice; judgement append-only. Mọi service chạy trong Compose nội bộ, không CDN.

---

## 4. Yêu cầu chức năng

Mức ưu tiên: **M** = bắt buộc cho demo 26/11; **S** = nên có; **C** = có thì tốt; **W** = không làm trong MVP.

### 4.1 Nhập liệu và truy vết nguồn gốc (FR-ING)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| ING-01 | Upload video (MP4/MOV), tách frame theo cấu hình, lưu timestamp + video ID | M | Video 4K 10 phút → frame + manifest; tiến trình hiển thị; job lỗi có thông báo |
| ING-02 | Upload ảnh tĩnh JPEG/TIFF, đọc EXIF (thời gian, thiết bị, GPS nếu có) | M | Ảnh hiển thị đúng hướng; EXIF lưu vào DB; ảnh không EXIF vẫn nhập được |
| ING-03 | Gán キロ程/部材 cho media: thủ công và import CSV; không tự suy đoán âm thầm | M | Mỗi media có station + member + confidence nguồn; UI hiển thị nguồn gán |
| ING-04 | Nhập point cloud LAS/LAZ và orthophoto; chuyển sang định dạng web nền (background job) | S | Point cloud 20M điểm chuyển xong và hiển thị; lỗi file sai định dạng bị chặn |
| ING-05 | Job queue có trạng thái queued/running/failed/done + progress + retry | M | UI thấy tiến trình; kill/retry không mất dữ liệu gốc |
| ING-06 | Media gốc bất biến (checksum); artifact dẫn xuất có version | M | Sửa/xóa media gốc bị chặn; checksum hiển thị trong chi tiết |
| ING-07 | Ghi license/quyền sử dụng cho từng media và dataset; chặn dùng media không rõ quyền trong 調書/demo | M | Media thiếu `license_ref` bị đánh dấu; export cảnh báo và loại khỏi file |
| ING-08 | Pipeline media: DZI cho ảnh lớn, HLS cho video, Potree octree cho point cloud; bản gốc giữ nguyên | M | Ảnh 45MP zoom mượt không tải cả file; video seek được; point cloud LOD theo point budget |

### 4.2 Asset registry (FR-AST)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| AST-01 | Quản lý tuyến/hướng, structure (earth/bridge/tunnel) với from/to km, cây 部材 (bridge → pier/girder/abutment; tunnel → portal/lining) | M | Tạo được B-14 với P1–P6 và G1–G5; strip và 3D đọc từ DB, không hardcode |
| AST-02 | Mỗi finding tham chiếu đúng 1 部材 + km + tọa độ trên media | M | Không tồn tại finding mồ côi; validation khi tạo |
| AST-03 | Asset ID ổn định, người đọc được (B-14/P3) | M | Đổi tên hiển thị không đổi ID; export giữ ID |
| AST-04 | Import danh mục asset từ CSV | S | Import 50 dòng < 5 s; dòng lỗi báo rõ dòng nào |

### 4.3 AI extraction (FR-AI)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| AI-01 | Chạy inference trên media/batch; sinh finding gồm class, geometry, confidence, model version, media ref, frame time | M | Chạy trên bộ ảnh thật; kết quả mở được trong UI; mỗi finding truy được về ảnh gốc |
| AI-02 | Tiling ảnh độ phân giải cao; ngưỡng confidence theo class cấu hình được | M | Ảnh 45MP không bị resize mất chi tiết; ngưỡng đổi không cần deploy lại |
| AI-03 | Gộp candidate trùng giữa các frame/tile chồng lấn thành 1 finding nhiều media ref | S | Cùng vết nứt qua 3 frame → 1 finding, 3 refs; không mất ref |
| AI-04 | Cờ bất thường/out-of-distribution cho 変状 lạ | C | Finding lạ được đánh dấu, không tự gán class |
| AI-05 | AI không bao giờ tự confirm; AI rank và engineer rank lưu riêng | M | Confirm bắt buộc có user + timestamp; sửa AI rank không thể từ UI |
| AI-06 | Model version ghi trên từng finding; chạy lại tạo suggestion mới, không ghi đè lịch sử | M | Re-run 2 lần → 2 suggestion versions, UI chọn được bản active |
| AI-07 | Chế độ đánh giá: chạy model trên tập labeled, xuất precision/recall per class, FP/ảnh | M | Xuất được báo cáo số thật để đưa vào tài liệu khách hàng |
| AI-08 | Đo kích thước (dài/rộng) từ ảnh có scale, kèm sai số | S | Giá trị luôn kèm error band; UI ghi "参考値" |

### 4.4 Màn hình xác nhận của kỹ sư (FR-REV)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| REV-01 | Danh sách candidate, filter all/未確認/確定/再撮影 kèm số lượng | M | Count khớp dữ liệu; filter đồng bộ 3D + strip |
| REV-02 | Chọn candidate → đồng bộ marker 3D, marker strip, mở chi tiết | M | Một click cập nhật cả 3 nơi < 100 ms với dữ liệu local |
| REV-03 | Chi tiết hiển thị media thật (zoom/pan) + overlay hình học + AI note + confidence + provenance | M | Zoom tới mức thấy chi tiết vết nứt; overlay khớp ảnh khi zoom |
| REV-04 | Chọn 判定区分 AA/A1/A2/B/C/S, comment, confirm | M | Confirm ghi audit event (user, time, before/after); reload vẫn còn |
| REV-05 | Yêu cầu chụp lại → tạo reshoot task | M | Task xuất hiện trong 飛行スケジュール dưới dạng chuyến chưa gán |
| REV-06 | So sánh 前回/今回 bằng 2 media đã đăng ký | S | Hiển thị cạnh nhau, cùng tỉ lệ; ghi rõ nếu khác góc chụp |
| REV-07 | Thao tác bàn phím, focus visible, aria cho toàn bộ luồng review | M | Đi hết luồng không cần chuột; focus không bị mất |
| REV-08 | Confirm hàng loạt có chọn lọc | C | Không cho confirm khi chưa xem media |

### 4.5 3D và định vị (FR-3D)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| 3D-01 | Render point cloud thật ≥ 20M điểm, LOD, xoay/zoom mượt trên GPU tầm trung | M | ≥ 30 fps khi xoay ở mức overview trên RTX 4090; degrade có kiểm soát trên CPU |
| 3D-02 | Phân biệt đoạn track thực đo và đoạn nội suy; vùng nội suy bị loại khỏi phân tích, có lý do | M | Tooltip hiển thị lý do (点群欠測 / トンネル内); analysis không trả giá trị trong vùng đó |
| 3D-03 | Marker đặt theo 部材 + offset; click chọn; focus animation | M | Click marker mở đúng finding; focus không làm mất context |
| 3D-04 | Nhãn structure và mốc km, ẩn khi ngoài khung hình | S | Nhãn không chồng nhau; ẩn đúng khi xoay |
| 3D-05 | Fallback khi không có WebGL: strip + list vẫn dùng được | M | Chặn WebGL → app không crash, luồng review hoàn tất |
| 3D-06 | Hệ tọa độ công bố rõ (local engineering + stationing), không phải 3D trang trí | M | Tài liệu hóa phép biến đổi; sai số định vị có ngưỡng |

### 4.6 縦断図 theo キロ程 (FR-STR)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| STR-01 | Hiển thị structure, trụ cầu, coverage (measured/interp), candidate, đường chọn, trục km | M | Dữ liệu lấy từ DB + coverage thật |
| STR-02 | Click/keyboard chọn candidate; đồng bộ list/3D | M | Chọn từ strip mở đúng chi tiết |
| STR-03 | Ứng biến theo bề rộng; candidate sát nhau không đè nhãn | M | Ở 320px vẫn đọc được; 15 km scale vẫn phân biệt được cụm |

### 4.7 Phân tích thay đổi (FR-CHG)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| CHG-01 | So sánh 2 epoch (bộ media/point cloud) sau đăng ký; tính biến dạng kèm dải sai số | M | Kết quả có error band; vùng không đăng ký được bị loại và báo |
| CHG-02 | Heat map + profile dọc tuyến, ngưỡng cảnh báo, loại vùng invalid | S | Click heat map chọn đúng finding |
| CHG-03 | Phân loại 拡大/新規/変化なし/縮小 bằng rule + confidence; độ tin thấp phải ghi rõ | M | Không có nhãn "拡大" khi thiếu 2 epoch hợp lệ |
| CHG-04 | Finding phân tích liên kết với 変状 liên quan và hành động (khảo sát lại/chụp lại) | S | Từ finding mở được 3D và chuyến bay tương ứng |
| CHG-05 | Thêm finding phân tích thành 変状候補, giữ trace | S | Candidate mới có `from_analysis_id`; xóa candidate không xóa analysis |
| CHG-06 | Biểu đồ xu hướng theo finding từ các lần đo (AI + thủ công), xử lý khoảng trống | M | 3 mốc thời gian hiển thị đúng; thiếu mốc không nối tuyến tính |
| CHG-07 | Không có dữ liệu 検測車 thì ẩn lớp tham chiếu, hiển thị "データ未提供" | M | Không tồn tại đường 検測車 sinh bằng công thức; UI nói rõ lý do thiếu |
| CHG-08 | Error band tính từ residual/độ bất định của từng kỳ, không dùng hằng số chung | M | Đổi bộ dữ liệu → band đổi; UI ghi phương pháp và giá trị |

### 4.8 Ưu tiên và 調書 (FR-PRI)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| PRI-01 | Xếp hạng theo 判定区分 + thay đổi + tuổi 変状; rule giải thích được | M | Mỗi dòng có "vì sao xếp hạng này" |
| PRI-02 | Bảng sort/filter; phân biệt AI提案 vs 確定 | M | Cột trạng thái khớp audit |
| PRI-03 | Sinh 調書 nháp chỉ từ mục đã confirm; hiển thị số mục chưa xác nhận | M | Không có dòng nào chưa confirm trong file xuất |
| PRI-04 | Xuất DOCX/PDF tiếng Nhật, template có tuyến/ngày/người/方法; AI note ghi rõ "AI所見（参考）" | M | Font Nhật nhúng; mở được trên Word/LibreOffice; layout không vỡ |
| PRI-05 | Không cho xuất khi còn candidate chưa xử lý ở trạng thái bắt buộc | S | Cảnh báo rõ, có override kèm lý do (audit) |

### 4.9 Kế hoạch bay và chụp (FR-FLT)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| FLT-01 | Lịch 7 ngày với thời tiết/gió/線路閉鎖; ngưỡng cấu hình (mưa, gió stop/warn, cap phút/đêm) | M | Đổi ngưỡng → trạng thái ngày đổi ngay; lý do chặn hiển thị |
| FLT-02 | Gán chuyến từ queue vào ngày; auto-assign; bỏ gán; validate section/ngày/cap | M | Không gán sai section; vượt cap bị chặn kèm thông báo |
| FLT-03 | Hiển thị tải bay/ngày so với cap | M | Thanh tải khớp tổng duration |
| FLT-04 | Sơ đồ tuyến theo loại chuyến (video/still/close/survey) + thông số (高度, 離隔, thời lượng) | S | Sơ đồ phản ánh đúng loại; thông số lấy từ flight record |
| FLT-05 | Gantt trong cửa sổ 線路閉鎖, cảnh báo tràn, chèn dòng reshoot | M | Thêm reshoot → cảnh báo tràn bật/tắt đúng |
| FLT-06 | Reshoot task từ review tự động thành chuyến chưa gán | M | Confirm 再撮影 → queue tăng 1, không nhân bản khi bấm lại |
| FLT-07 | Dữ liệu lịch/weather/flight nhập từ DB/CSV, không hardcode | M | Xóa seed → màn hình trống có hướng dẫn, không crash |

### 4.10 Quản trị, audit, model ops (FR-ADM)

| ID | Yêu cầu | Mức | Acceptance |
|---|---|---|---|
| ADM-01 | Tài khoản local, 3 role; session timeout | M | Role chặn đúng hành động; logout hết hạn |
| ADM-02 | Audit log append-only cho confirm/đổi judgement/xuất 調書/xóa; export CSV | M | Không sửa được log qua API/UI; export đủ trường |
| ADM-03 | Danh mục model version + chọn active model + xem metric của version | M | Đổi active model chỉ ảnh hưởng lần chạy sau |
| ADM-04 | Backup/restore dữ liệu và media; không gửi dữ liệu ra ngoài | M | Restore trên máy sạch → app chạy, ảnh còn |
| ADM-05 | Seed data tách khỏi production; có cảnh báo khi đang ở chế độ demo | S | Banner demo hiển thị; xóa seed không ảnh hưởng dữ liệu thật |
| ADM-06 | Mỗi model version ghi dataset + license; chặn train/deploy từ dataset phi thương mại | M | Model card hiển thị nguồn; pipeline từ chối dataset không được phép |
| ADM-07 | Thao tác ghi (upload, job, judgement, report, phân lịch) idempotent; retry không tạo bản trùng | M | Gửi lại cùng key không tạo bản ghi thứ hai; key khác body trả 409 |

---

## 5. Yêu cầu phi chức năng

| ID | Yêu cầu | Acceptance |
|---|---|---|
| NFR-01 | Offline runtime: không gọi CDN/Google Fonts/external API; model, font, JS đóng gói local | Chạy trong mạng air-gapped vẫn đủ chức năng; DevTools không có request ngoài |
| NFR-02 | Hiệu năng UI: list < 100 ms, mở chi tiết < 300 ms (dữ liệu local) | Đo bằng Performance panel, ghi lại số |
| NFR-03 | Inference budget: ảnh 45MP ~70 tile; GPU 5–25 s/ảnh, CPU 60–300 s/ảnh; 4K frame GPU 1–6 s, CPU 12–70 s `[推定]`; có CPU fallback chạy nền | Benchmark p50/p95 trên máy demo, ghi trong repo |
| NFR-04 | Bảo mật: validate loại file, chống path traversal, upload size limit, không render HTML từ dữ liệu người dùng | Test với file độc hại; CSP chặn inline script lạ |
| NFR-05 | Audit bất biến: mọi thay đổi judgement có actor + timestamp + diff | Thử sửa/xóa log qua DB/API → bị chặn hoặc phát hiện |
| NFR-06 | Tiếng Nhật: IME, font nhúng, date format, không lỗi mojibake trong DB/export | Nhập 変状/ひび割れ/再撮影; xuất DOCX kiểm tra bằng mắt |
| NFR-07 | Accessibility luồng review: WCAG 2.1 AA (focus, contrast, keyboard) | axe không lỗi serious/critical ở 3 màn chính |
| NFR-08 | Trình duyệt: Chrome/Edge bản hiện hành; không hỗ trợ IE | Smoke test 2 bản |
| NFR-09 | Sao lưu/khôi phục: RPO 24h, RTO 4h | Diễn tập restore 1 lần trước demo |
| NFR-10 | Observability: health endpoint, job log, lỗi inference có stack + media id | Giả lập lỗi → tìm được nguyên nhân từ log |

---

## 6. Yêu cầu dữ liệu (tóm tắt — chi tiết ở `research/01-data.md`)

**Bộ demo tối thiểu** (mỗi site): 100–200 ảnh cho 3D + 50–100 ảnh 近接 (có ảnh nền và ảnh có 変状), 1 video 全景, ≥5 GCP + ≥3 checkpoint độc lập. Cầu + cửa hầm + mái dốc; nếu thiếu site nào thì ẩn tính năng tương ứng. Đây là **bộ trình diễn**, không phải bộ huấn luyện: model cần 200–500 ảnh dương tính độc lập/lớp (xem §7), nên MVP dùng pretrained + fine-tune nhỏ và công bố N thật.

**Thông số chụp**:
- 部材単位: 0,4–1 mm/px (H 2–5 m, p 4 µm, f 20 mm), ảnh vuông góc + xiên, có bảng ID 部材.
- 近接: ≤0,1 mm/px để *sàng lọc* nứt 0,2 mm; ≤0,04 mm/px nếu muốn thử đo. Có thước chuẩn cùng mặt phẳng.
- 3D: overlap dọc ≥80%, ngang ≥70%, ảnh tĩnh gốc ưu tiên hơn frame video; GCP phân bố biên/giữa/cao-thấp.
- Nhòe mục tiêu ≤0,5 px; ở 0,1 mm/px cần phơi ≤1/1000 s với chuyển động 0,05 m/s.

**License**: chỉ SDNET2018, Concrete Crack Images (CC BY 4.0) và CTCD (CC BY 4.0) được dùng cho demo/huấn luyện thương mại, kèm attribution. CODEBRIM, CrackForest, DeepCrack, MCDS **bị loại** khỏi demo và train thương mại cho đến khi có phép. Ảnh khách hàng cần văn bản cho phép chụp/lưu/train/demo.

**Quy tắc dữ liệu thiếu**: không có 2 kỳ → hiển thị "chưa đủ kỳ"; không có 検測車 → ẩn lớp; không có GCP/checkpoint → không công bố sai số 3D; không đủ GSD → không báo số đo.

**Nhãn**: class, geometry (mask/polyline/box), member_id, severity scheme + rank (null = chưa đánh giá, không phải S), occluded/uncertain + lý do, width + uncertainty (chỉ khi hiệu chuẩn), annotator/reviewer/revision. Hai người gán độc lập ≥20% ảnh, phân xử bởi kỹ sư.

**Tách tập**: theo structure/chuyến bay/kỳ, không random theo crop; toàn bộ ảnh đêm hiện trường giữ riêng để đánh giá.

**Công cụ**: ODM 3.6.2 (AGPL, CPU) cho photogrammetry; CVAT 2.83.0 cho annotation; Metashape Professional chỉ khi ODM thất bại và license offline được duyệt.

## 7. Yêu cầu model (tóm tắt — chi tiết ở `research/02-model.md`)

**Kiến trúc**: U-Net/ResNet34 multi-label (7 kênh + ignore) qua `segmentation-models-pytorch` 0.6.0, chạy tiled 1024×1024 overlap 20%; xuất ONNX FP32 cho CPU và TensorRT FP16 khi có GPU. YOLO26s-seg chỉ dùng làm baseline so sánh nếu giải quyết được license Ultralytics (AGPL hoặc Enterprise); không đưa vào runtime trước khi duyệt.

**Ngưỡng PoC đề xuất** (thảo luận với khách, không phải cam kết): crack/spalling recall ≥ 0,80, precision ≥ 0,70, FP ≤ 1/ảnh; mask IoU median ≥ 0,50 cho spalling; các lớp khác chỉ báo khi ≥100 sự kiện độc lập. Báo N, Wilson CI, FN theo lớp/kích thước/GSD. Tách test theo công trình, không theo tile.

**Serving**: 45MP → ~70 tile; GPU 5–25 s/ảnh, CPU 60–300 s/ảnh `[推定]`; 4K frame 15 tile, GPU 1–6 s, CPU 12–70 s `[推定]`. Phải đo p50/p95 trên máy demo trước 26/11.

**Đo và thay đổi**: đo dài/rộng chỉ khi có scale + GSD cục bộ, luôn kèm bất định; không cam kết mm tuyệt đối. Thay đổi dùng M3C2 (CloudCompare/PDAL) hoặc đăng ký ảnh, xuất d ± LoD95 theo từng vị trí. **±15 mm chỉ là ví dụ, không hardcode**.

**Chế độ demo (zero-shot, 26/11)**: Grounding DINO tiny (Apache-2.0), prompt tiếng Anh ("crack", "spalling", "rust", "water leakage", "exposed rebar"), box-only, chạy CPU và precompute. **Không train.** Score là raw score chưa hiệu chỉnh → UI ghi "zero-shot（未検証）", không gọi là 信頼度 đã hiệu chỉnh, không đo kích thước, không suy ra 判定区分. Kỳ vọng recall thấp và nhiều false positive; đó là lý do vẫn cần kỹ sư xác nhận.

**Giới hạn mẫu**: 200–500 ảnh dương tính độc lập/lớp mới đủ để nói về khả năng tổng quát; bộ demo 50–100 ảnh/site **không đủ**. Vì vậy MVP phải dùng pretrained có license rõ + fine-tune nhỏ, báo N và khoảng tin cậy, gọi kết quả là "exploratory", không tuyên bố năng lực production.

**調書**: template render từ finding đã confirm; LLM/VLM không nằm trên đường quyết định (chỉ thí nghiệm nội bộ, offline).

## 8. Traceability: demo gốc → yêu cầu

| Màn hình demo | FR |
|---|---|
| 点検確認 (3D map, list, detail, strip) | REV-01..08, 3D-01..06, STR-01..03, AI-01..06 |
| 飛行スケジュール | FLT-01..07, REV-05 |
| 撮影計画 | FLT-04, FLT-05, FLT-06 |
| 変位解析 | CHG-01..06, 3D-02 |
| 保守優先度 + 調書 dialog | PRI-01..05, ADM-02 |
| App bar, theme, responsive | NFR-06..08 |

## 9. Quyết định còn mở

| ID | Vấn đề | Ai quyết | Hạn |
|---|---|---|---|
| OD-01 | Có video thật từ khách trước 26/11 hay dùng flight tự bay? | Khách + mình | 2026-11-22 |
| OD-02 | Point cloud: ODM 3.6.2 từ ảnh tự bay + ≥5 GCP; nếu không kịp thì ẩn 3D | Kỹ thuật | Đã chốt |
| OD-03 | 調書 export: DOCX template riêng của khách hay template chung? | Khách | Trong họp |
| OD-04 | Model chính: U-Net SMP 0.6.0 + ONNX; YOLO26s-seg chỉ khi license được duyệt | Kỹ thuật | Đã chốt |
| OD-05 | Ngưỡng chấp nhận recall/precision/FP cho PoC | Khách | Trong họp |
| OD-06 | Dữ liệu lịch sử có được số hóa không, ai làm? | Khách | Trong họp |
| OD-07 | Nhân lực MVP: 2 người (12 tuần) hay 1 người (18–20 tuần, cắt scope) | Mình | 2026-11-27 |
