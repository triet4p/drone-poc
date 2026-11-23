# Phạm vi MVP — Drone × AI Infrastructure Inspection

| | |
|---|---|
| Phiên bản | 0.2 (đã đối chiếu research; ước lượng 19–28 pw) |
| Ngày | 2026-11-20 |
| Liên quan | `REQUIREMENTS.md`, `research/01-data.md`, `research/02-model.md`, `research/03-architecture.md` |
| Mốc gần nhất | Demo khách hàng 2026-11-26 (6 ngày) |
| Mốc MVP | 12 tuần với 2 người; 18–20 tuần với 1 người `[推定 19–28 person-week]` |

---

## 1. Định nghĩa MVP

MVP = một hệ thống chạy on-prem, nhận **dữ liệu drone thật**, chạy **model thật**, cho ra **danh sách 変状 có vị trí và lịch sử**, và **xuất 調書 chỉ chứa mục kỹ sư đã xác nhận** — với đủ 5 màn hình của prototype, nhưng mỗi con số đều truy được về dữ liệu và model version.

Ba tiêu chí "thật" (không thương lượng):

1. **Dữ liệu thật**: ảnh/video từ một lần bay thật (của khách hoặc của mình), có EXIF/thời gian; không dùng ảnh minh họa SVG.
2. **Model thật**: trọng số đã train/fine-tune, có báo cáo precision/recall trên tập giữ riêng; không hardcode kết quả.
3. **Truy vết thật**: click một 変状 → thấy media gốc, model version, confidence, ai xác nhận, khi nào; sửa được nhưng có audit.

Hệ quả: mọi `const C = [...]` kiểu demo phải biến mất. Nếu thiếu dữ liệu, UI hiển thị trạng thái trống — **không bịa số**.

---

## 2. Trong phạm vi

| Khối | Nội dung | Màn hình demo tương ứng |
|---|---|---|
| Nhập liệu | Upload ảnh/video/point cloud, tách frame, gán km/部材, job queue | (mới) |
| Asset | Tuyến, cầu, trụ, dầm, mố, cửa hầm, mái dốc | 点検確認, 縦断図 |
| AI | Detection/segmentation 変状, tiling, gộp frame, model version | 点検確認 |
| Review | Candidate list, media thật + overlay, 判定 AA–S, comment, confirm, 再撮影 | 点検確認 |
| 3D | Point cloud thật, marker theo 部材, đoạn thực đo vs nội suy | 3D軌道マップ |
| 縦断 | Structure + coverage + candidate theo km | 線路縦断 |
| Thay đổi | So 2 epoch, heat map/profile, error band, phân loại 拡大/新規/変化なし | 変位解析 |
| Ưu tiên | Xếp hạng theo rank + thay đổi, lý do xếp hạng | 保守優先度 |
| 調書 | DOCX/PDF tiếng Nhật, chỉ mục đã confirm | 調書 dialog |
| Bay | Lịch 7 ngày, thời tiết/閉鎖/cap, gán chuyến, Gantt, reshoot | 飛行スケジュール, 撮影計画 |
| Audit | Log bất biến, role, backup | (mới) |

**Phạm vi dữ liệu**: 1 cầu bê tông (≥3 trụ, dầm, mố) + 1 cửa hầm + 1 mái dốc. Không mở rộng tuyến.

---

## 3. Ngoài phạm vi

- Điều khiển bay, autopilot, telemetry, lập đường bay tự động.
- Work order/CMMS, hóa đơn, vật tư, tích hợp ERP.
- Multi-tenant, SaaS, SSO, phân quyền chi tiết.
- App mobile, chế độ offline hiện trường.
- Tự động kết luận 判定区分, tự động nộp 調書.
- Đo bề rộng nứt tuyệt đối cấp mm như số liệu chính thức.
- Nhận dạng 変状 mới ngoài 7 lớp đã chọn (chỉ gắn cờ bất thường nếu kịp).

---

## 4. Hai mốc giao hàng

### 4.1 Bản demo 26/11 (6 ngày: 20–25/11)

Mục tiêu: chứng minh "model thật trên ảnh thật" + vòng lặp kỹ sư. Đây là **lát cắt dọc**, không phải thu nhỏ của MVP: bỏ 3D, video, change analysis, priority scoring và flight planning thật.

| Ngày | Việc | Điều kiện xong |
|---|---|---|
| 20–21/11 | Cài Grounding DINO tiny; chạy zero-shot trên 20–50 ảnh thật; tune prompt/ngưỡng; đo latency CPU | Có detections thật + số giây/ảnh, không train |
| 21–22/11 | API tối thiểu: asset/member, media, finding, suggestion, judgement, audit; upload + checksum | Import ảnh, detect sinh finding có provenance |
| 22–23/11 | Review UI: list + ảnh gốc zoom + overlay + chọn AA–S + comment + confirm | Confirm ghi audit; reload còn dữ liệu |
| 24/11 | 縦断 đơn giản từ DB; 調書 DOCX từ mục đã confirm | Xuất file tiếng Nhật mở được |
| 25/11 | Đóng gói offline, rehearsal toàn luồng, đo latency CPU | Chạy không Internet; có số p50/p95 thật |

| Hạng mục | Demo 26/11 | Ghi chú |
|---|---|---|
| Ảnh thật | 20–50 ảnh một cầu; nếu không kịp: ảnh public + ghi rõ nguồn | Không dùng ảnh SVG |
| Model | **Zero-shot** Grounding DINO tiny (Apache-2.0), prompt EN, ngưỡng thấp; không train | Kết quả là candidate thô, gắn nhãn "zero-shot（未検証）" |
| 3D | **Không có** (cần 100–200 ảnh + GCP + ODM 0,5–1 ngày) | Ẩn, không giả |
| Video/HLS | **Không có** | Ẩn |
| 変位解析 | **Không có** 2 epoch | Ẩn, ghi "データ未提供" |
| 優先度 | Chỉ sort theo rank đã confirm | Không có risk score |
| Bay/撮影計画 | Prototype tĩnh, nhãn "planned" | Không tuyên bố nối pipeline |
| 調書 | DOCX template tối thiểu, chỉ mục confirmed | Font Noto Sans JP nhúng |
| Offline | Chạy local, không CDN | Bắt buộc |

**Điều kiện hủy/hoãn**: không có ảnh thật trước 22/11 → demo dùng prototype + mô tả pipeline; nói thẳng trong họp, không diễn kịch. Nếu chỉ có 1 người, bỏ mục 縦断 khỏi demo.

**Trạng thái 23/11**: 5 tab; 3D context + **計測 view** (model points, distance/Δh/slope, 模式値); ray đôi 1.067mm; 5 ảnh tuyến thật (Commons). 3D cần internet; đo thật cần point cloud + GCP. Research: `04a`, `04b`, `05a`, `05b`, `05c`.

### 4.2 MVP 12 tuần

| Sprint | Tuần | Nội dung | Exit |
|---|---|---|---|
| S1 | 1–3 | Nền tảng: DB asset, upload, job queue, inference service, review UI thật | End-to-end 1 cầu trên dữ liệu thật |
| S2 | 4–6 | Video → frame, point cloud/orthophoto, 3D + strip thật | 3D mở được point cloud thật, marker đúng 部材 |
| S3 | 7–9 | Change detection 2 epoch, error band, ưu tiên, 調書 template khách | Xuất 調書 được review bởi kỹ sư |
| S4 | 10–12 | Flight planning thật, audit/role, offline install, đo hiệu năng, eval report | Cài trên máy sạch, chạy air-gapped, có báo cáo metric |

Thứ tự này cố ý: **giá trị nằm ở review + 調書**, không phải 3D đẹp. 3D có thể trượt sang S2 mà không chặn demo.

### 4.3 Năng lực thực hiện

Ước lượng từng khối `[推定]`: khung app/auth/DB/audit 3–4 pw; upload/DZI/HLS/viewer 3–4; Potree/COG/CRS/strip 3–4; model/worker 2–4; lịch/thời tiết 2–3; so sánh kỳ/sai số 2–3; ưu tiên/調書/deploy/backup 4–6. Tổng **19–28 person-week**, chưa tính thu thập–gán nhãn dữ liệu và phê duyệt phía khách.

Hệ quả: 12 tuần × 1 người = 12 pw < 19 → **không khả thi**. Cần 2 người (24 pw) hoặc chấp nhận 18–20 tuần. Nếu chỉ 1 người, phải cắt một trong: flight planning thật, video/HLS, hoặc change analysis — và ghi rõ cắt gì trước khi bắt đầu.

Đường găng không phải code mà là **dữ liệu thật + quyền sử dụng + kỳ cũ**. Chốt trong tuần 1, nếu không thì mọi sprint sau đều trượt.

---

## 5. Acceptance của MVP

Một buổi nghiệm thu đạt khi:

1. Cài từ zero trên máy Linux sạch, không Internet, trong ≤ 2 giờ.
2. Import 100 ảnh thật + 1 video; job chạy xong, không mất ảnh.
3. Detection chạy trên GPU nếu có, CPU fallback nếu không; mỗi finding mở được ảnh gốc đúng vị trí, zoom thấy vết nứt; có p50/p95 thực đo.
4. Kỹ sư confirm 10 mục; audit log ghi đủ; reload vẫn còn.
5. Strip hiển thị đúng cầu/trụ/coverage; chọn finding đồng bộ 3 nơi.
6. So sánh 2 epoch cho ra heat map + error band; vùng nội suy bị loại.
7. Xuất DOCX mở được trên Word Nhật, chỉ chứa mục đã confirm.
8. 再撮影 → xuất hiện trong lịch bay; gán được; vượt cap bị chặn.
9. Báo cáo model: precision/recall/FP per ảnh trên tập giữ riêng, có model version.
10. Không có request ra Internet trong suốt buổi nghiệm thu.

---

## 6. Giả định và phụ thuộc

| ID | Giả định/phụ thuộc | Ảnh hưởng nếu sai | Xử lý |
|---|---|---|---|
| A1 | Thuê được GPU ≥16GB theo giờ (máy dev hiện không có CUDA) | Train chậm, demo phải chạy CPU | Thuê GPU cho fine-tune; đóng gói model ONNX chạy CPU cho demo |
| A2 | Có ảnh/video thật trước 22/11 | Demo mất phần "thật" | Dùng bộ public + nói rõ |
| A3 | Khách cho phép dùng footage trong demo | Không được chiếu | Dùng flight của mình |
| A4 | Point cloud từ video đủ overlap | 3D lỗi/không có | Bay bổ sung hoặc ẩn 3D |
| A5 | Hồ sơ cũ ở dạng số hóa được | Không có so sánh nhiều năm | Chỉ so 2 epoch mới |
| A6 | Font Nhật có license nhúng PDF/DOCX | 調書 lỗi font | Dùng Noto Sans JP (OFL) |
| A7 | Có quyền vào site + đo GCP trong 1 tuần | Không có 3D/định vị | Dùng ảnh 2D, ẩn 3D |

---

## 7. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| 6 ngày không đủ cho model + pipeline + 3D | Cao | Cắt 3D khỏi demo; chỉ hứa vertical slice |
| 1 người không đủ 19–28 pw cho 12 tuần | Cao | Chốt 2 người, hoặc cắt flight/video/change và dời mốc |
| Domain gap ảnh public → bê tông đường sắt Nhật | Cao | Fine-tune trên ảnh thật; báo cáo cả 2 tập |
| Photogrammetry tốn thời gian, sai số định vị | Trung bình | Đo trước bằng 1 bộ nhỏ; có ngưỡng sai số công bố |
| Khách hiểu "AI thay kỹ sư" | Cao | UI + lời nói: AI đề xuất, kỹ sư quyết; 調書 chỉ từ mục confirm |
| Đo mm bị chất vấn | Cao | Không cam kết; luôn kèm "参考値" + error band |
| Dữ liệu khách không được mang ra ngoài | Cao | On-prem, offline, backup nội bộ |

---

## 8. Những gì không được phép giả

- Không hardcode finding/defect trong code production.
- Không hiển thị metric chưa đo.
- Không dùng ảnh minh họa thay ảnh thật mà không gắn nhãn rõ.
- Không hiển thị point cloud tổng hợp như dữ liệu bay thật.
- Không tự confirm thay kỹ sư.
- Không xuất 調書 chứa mục chưa xác nhận.

---

## 9. Thay đổi phạm vi

Mọi yêu cầu mới phải trả lời: (a) thuộc sprint nào, (b) đẩy lùi mốc nào, (c) thay thế hạng mục nào. Không nhận "làm thêm nhanh" mà không cắt.
