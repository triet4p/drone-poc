# Point cloud view — synthetic B-14

Mục tiêu: click một điểm trên ray/kết cấu → xem số liệu tương đối + ảnh nguồn tương ứng.

## 1. Trạng thái

- **Chưa có point cloud thật** của corridor 12k400–15k600 kèm ảnh/pose. Nguồn mở đã kiểm tra: Kanagawa R1 (LAS, điều khoản riêng, chủ yếu rừng), VIRTUAL SHIZUOKA (CC BY 4.0, ngoài corridor), ArchScanLib (16 cầu UK, CC BY 4.0, 81 GB, khác typology). Không nguồn nào có per-point photo link.
- **Hiện tại**: point cloud tổng hợp B-14, 365.106 điểm, sinh từ mô hình hình học nội bộ. Đúng tương đối theo mô hình; cao độ tuyệt đối không phải đo đạc.
- Nhãn UI: **点群（合成）**, scale `relative`, note cố định.

## 2. Hệ toạ độ

- Mét, local engineering: `x` dọc tuyến từ km 13150, `y` ngang, `z` cao.
- Khổ ray neo **1.067 m**; ray ở `z=8.72`, tim ray `y=±0.5335`.
- Trụ P1–P6 tại x = 50, 80, 112, 180, 250, 310 (từ km 13150).
- Không dùng Web Mercator để đo.

## 3. Dữ liệu sinh

`backend/scripts/build_pointcloud.py` (deterministic, seed 42) sinh:

```text
data/pointcloud/demo/points.bin    # float32: x,y,z,r,g,b,member_idx (365k rows)
data/pointcloud/demo/meta.json     # bounds, members, scale, views
data/pointcloud/demo/views.npz     # z-buffer cho occlusion
data/pointcloud/demo/view_*.jpg    # 10 camera views (1000x700)
```

Thành phần: rail, sleeper, ballast, deck, pier, abutment, ground, river.
Camera views: 10 vị trí quanh cầu, FOV 48°, có pose để reproject.

## 4. API

| Endpoint | Việc |
|---|---|
| `GET /api/pointcloud/meta` | metadata + `points_url` |
| `GET /api/pointcloud/points.bin` | binary cloud |
| `GET /api/pointcloud/view/{id}` | ảnh view |
| `POST /api/pointcloud/pick` | `{index}` → point + metrics + top-3 views |

Pick trả: `member`, `km`, local XYZ, `rail_offset_m`, `height_vs_rail_m`, `scale_status`, và view có `u,v` để đặt marker trên ảnh.

## 5. UI

`frontend/src/components/PointCloudView.tsx` (Three.js):

- 365k `Points`, màu từ ảnh, OrbitControls.
- Raycast threshold 0.25 m; click → POST pick.
- Panel: member, km, XYZ, lệch tim ray, cao độ so mặt ray, scale; ảnh view + marker đỏ; nút V01–V03.
- Cảnh báo cố định: **合成点群・相対形状・実測値ではない**.

## 6. Nâng lên cloud thật

1. Ảnh drone overlap ≥ 60–70% + GCP/checkpoint.
2. COLMAP (BSD) + OpenMVS/ODM (AGPL) hoặc model DL có license thương mại (MapAnything bản Apache; Pi4/DUSt3R/MASt3R/VGGT-1B là NC → chỉ nội bộ).
3. Xuất `points.bin` + `meta.json` + `views.npz` cùng schema; thay thư mục `data/pointcloud/demo` bằng `data/pointcloud/<survey_id>`.
4. Reproject point → camera, lưu `u,v,depth,visible`; API giữ nguyên.
5. Chỉ gắn `scale_status=surveyed` khi có ≥3 GCP + Umeyama và sai số công bố.

Chi tiết research: `docs/research/06a-pointcloud-sources.md`, `06b-multiview-dl.md`.
