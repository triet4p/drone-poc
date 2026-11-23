# Geometry module (future)

Biến alignment + cross-section + DEM thành corridor 3D có version.

## Input contract

```text
alignment: [{ km_m, lon, lat }]        # EPSG:4326
gauge_mm: 1067
dem_source: GSI-dem5a | FGD-DEM5A | none
structures: [{ id, kind: bridge|tunnel|earthwork, km_start, km_end, source }]
cross_sections: templates (rail, sleeper, ballast, catenary)
```

## Output

```text
corridor.glb / tileset.json
qa-report.json  # input hash, template version, void coverage, manifold, assumed dimensions
```

## Rules

- Deterministic: same input/template/code → same bytes hash.
- Every procedural dimension carries `source: assumed` and is labelled 模式 in UI.
- Never writes `judgement` or `report`; geometry is context.
- Reference: `docs/research/05a-geometry-merge.md`.
