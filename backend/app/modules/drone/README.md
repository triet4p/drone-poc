# Drone imagery module (future)

Nhận video/ảnh gốc + telemetry + GCP; xuất frame/pose/point cloud/orthophoto có sai số.

## Pipeline

```text
ingest → frame extraction → blur/quality gate → photogrammetry (ODM) →
GCP/checkpoint → reconstruction (LAZ, orthophoto, COG) → web tiles
```

## Contracts

```text
survey(epoch, captured_at, gcp, checkpoint, crs, calibration)
media(frame, timestamp, pose, uncertainty)
reconstruction(point_cloud, orthophoto, checkpoint_metrics)
```

## Rules

- Không ghi đè bytes gốc.
- Không gán toạ độ tuyệt đối khi thiếu pose/GCP; ghi `位置未確定`.
- Point cloud measurement chỉ hợp lệ khi có GCP + checkpoint + `method=surveyed`.
- Reference: `docs/research/01-data.md`, `04b-3d-viewer.md`.
