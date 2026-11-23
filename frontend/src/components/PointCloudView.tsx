import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { t, type Lang } from "../lib/i18n";

type View = { image_id: string; url: string; u: number; v: number; depth?: number; width: number; height: number; score: number; residual?: number; source_url?: string; captured_at?: string; license?: string; artist?: string };
type Pick = {
  index: number; member: string; site?: string; scale_status?: string; link_method?: string;
  observation_count?: number;
  km?: number; local?: { x: number; y: number; z: number };
  metrics?: { rail_offset_m: number; height_vs_rail_m: number; scale_status: string };
  views: View[];
};
type Meta = { id?: string; site?: string; site_id?: string; site_name?: string; label?: string; count: number; points_url: string; dense_url?: string; dense_count?: number; note?: string; scale?: { status: string; basis: string }; scale_status?: string; link_method?: string; views: View[]; camera_track?: [number, number, number][]; track_note?: string };

function heightColor(z: number, z0: number, z1: number): [number, number, number] {
  const h = z1 > z0 ? (z - z0) / (z1 - z0) : 0;
  if (h < 0.16) return [0.43, 0.50, 0.53];       // ground / deck level
  if (h < 0.42) return [0.28, 0.68, 0.55];       // low structure
  if (h < 0.72) return [0.96, 0.68, 0.24];       // elevated structure
  return [0.91, 0.33, 0.28];                     // high structure
}

function colorByHeight(pos: Float32Array, z0: number, z1: number): Float32Array {
  const out = new Float32Array(pos.length);
  for (let i = 0, k = 0; i < pos.length; i += 3, k += 3) {
    const [r, g, b] = heightColor(pos[i + 2], z0, z1);
    out[k] = r; out[k + 1] = g; out[k + 2] = b;
  }
  return out;
}
type Site = { site: string; name: string; kind: string; available: boolean };

export default function PointCloudView({ lang, siteId }: { lang: Lang; siteId: string | null }) {
  const host = useRef<HTMLDivElement>(null);
  const [cloudSite, setCloudSite] = useState(siteId ?? "koma_bridge");
  useEffect(() => { if (siteId) setCloudSite(siteId); }, [siteId]);
  const [meta, setMeta] = useState<Meta | null>(null);

  const [sel, setSel] = useState<Pick | null>(null);
  const [viewIdx, setViewIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const homeRef = useRef<{ pos: THREE.Vector3; target: THREE.Vector3 } | null>(null);
  const pointsRef = useRef<THREE.Points | null>(null);
  const gridRef = useRef<THREE.GridHelper | null>(null);
  const axesRef = useRef<THREE.AxesHelper | null>(null);
  const groundRef = useRef<THREE.Mesh | null>(null);
  const trackRef = useRef<THREE.Object3D | null>(null);
  const trackCamRef = useRef<THREE.Line | null>(null);
  const trackPostsRef = useRef<THREE.LineSegments | null>(null);
  const [showCloud, setShowCloud] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [showGround, setShowGround] = useState(true);
  const [showTrack, setShowTrack] = useState(true);
  const [showPhoto, setShowPhoto] = useState(true);
  const [showDense, setShowDense] = useState(true);
  const [colorMode, setColorMode] = useState<"photo" | "height">("height");
  const colorModeRef = useRef<"photo" | "height">("height");
  const colorApplyRef = useRef<((mode: "photo" | "height") => void) | null>(null);
  const boundsRef = useRef<{ center: THREE.Vector3; radius: number; z0: number; z1: number } | null>(null);
  const denseRef = useRef<THREE.Points | null>(null);
  const [pointSize, setPointSize] = useState(1);
  const [pointOpacity, setPointOpacity] = useState(1);
  const baseSizeRef = useRef(1);

  useEffect(() => {
    if (!cloudSite) { setLoading(false); setSel(null); setMeta(null); return; }
    let disposed = false;
    const el = host.current;
    if (!el) return;
    setLoading(true);
    setError(null);
    setSel(null);
    let renderer: THREE.WebGLRenderer;
    let points: THREE.Points;
    let positions: Float32Array | null = null;
    let cloudRadius = 1;
    let selectedMarker: THREE.Mesh | null = null;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch {
      setError("WebGL unavailable");
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.setSize(el.clientWidth, el.clientHeight);
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#1b252c");
    const camera = new THREE.PerspectiveCamera(48, el.clientWidth / el.clientHeight, 0.5, 2500);
    camera.up.set(0, 0, 1);
    camera.position.set(95, -120, 72);
    cameraRef.current = camera;
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(175, 0, 8);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxDistance = 900;
    controls.minDistance = 6;
    controls.update();
    controlsRef.current = controls;

    const grid = new THREE.GridHelper(420, 42, 0x4f6670, 0x344750);
    grid.rotation.x = Math.PI / 2;
    grid.position.set(180, 0, 0);
    gridRef.current = grid;
    const gm = grid.material as THREE.Material;
    gm.transparent = true; gm.opacity = 0.55;
    scene.add(grid);

    // A reference ground plane: the photogrammetric cloud does not contain bare
    // ground, so this is explicitly a reference plane, not surveyed terrain.
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({ color: 0x26343b, transparent: true, opacity: 0.72, side: THREE.DoubleSide, depthWrite: false }),
    );
    ground.renderOrder = -1;
    scene.add(ground);
    groundRef.current = ground;

    const axes = new THREE.AxesHelper(20);
    axesRef.current = axes;
    scene.add(axes);

    const markerGeo = new THREE.SphereGeometry(1, 16, 16);
    selectedMarker = new THREE.Mesh(markerGeo, new THREE.MeshBasicMaterial({ color: 0xffd166 }));
    selectedMarker.visible = false;
    scene.add(selectedMarker);

    const raycaster = new THREE.Raycaster();
    raycaster.params.Points = { threshold: 0.25 };
    const ndc = new THREE.Vector2();
    const down = { x: 0, y: 0 };

    const pickAt = async (clientX: number, clientY: number) => {
      const rect = renderer.domElement.getBoundingClientRect();
      ndc.set(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
      raycaster.setFromCamera(ndc, camera);
      const hit = raycaster.intersectObject(points, false)[0];
      if (!hit || hit.index == null) return;
      try {
        const r = await fetch("/api/pointcloud/pick", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ index: hit.index, top_k: 3, site: cloudSite }),
        });
        if (!r.ok) throw new Error(await r.text());
        const data: Pick = await r.json();
        if (positions && selectedMarker) {
          const k = hit.index * 3;
          selectedMarker.position.set(positions[k], positions[k + 1], positions[k + 2]);
          selectedMarker.scale.setScalar(Math.max(cloudRadius * 0.018, 0.01));
          selectedMarker.visible = true;
        }
        setSel(data);
        setViewIdx(0);
      } catch (e) {
        setError(String(e));
      }
    };

    const onDown = (e: PointerEvent) => { down.x = e.clientX; down.y = e.clientY; };
    const onUp = (e: PointerEvent) => {
      if (Math.hypot(e.clientX - down.x, e.clientY - down.y) < 5) pickAt(e.clientX, e.clientY);
    };
    renderer.domElement.addEventListener("pointerdown", onDown);
    renderer.domElement.addEventListener("pointerup", onUp);

    fetch(`/api/pointcloud/meta?site=${encodeURIComponent(cloudSite)}`)
      .then((r) => r.json())
      .then(async (m: Meta) => {
        if (disposed) return;
        setMeta(m);
        const buf = await (await fetch(m.points_url)).arrayBuffer();
        const f = new Float32Array(buf);
        const n = Math.floor(f.length / 7);
        const pos = new Float32Array(n * 3);
        const col = new Float32Array(n * 3);
        for (let i = 0, j = 0, k = 0; i < n; i++, j += 7, k += 3) {
          pos[k] = f[j]; pos[k + 1] = f[j + 1]; pos[k + 2] = f[j + 2];
          col[k] = f[j + 3] / 255; col[k + 1] = f[j + 4] / 255; col[k + 2] = f[j + 5] / 255;
        }
        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
        geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
        geo.computeBoundingSphere();
        const material = new THREE.PointsMaterial({
          size: 0.075, vertexColors: true, sizeAttenuation: true, transparent: true, opacity: 1,
        });
        points = new THREE.Points(geo, material);
        pointsRef.current = points;
        scene.add(points);
        let densePositions: Float32Array | null = null;
        let densePhotoColors: Float32Array | null = null;
        if (m.dense_url) {
          const dbuf = await (await fetch(m.dense_url)).arrayBuffer();
          const df = new Float32Array(dbuf);
          const dn = Math.floor(df.length / 7);
          const dpos = new Float32Array(dn * 3);
          const dcol = new Float32Array(dn * 3);
          for (let i = 0, j = 0, k = 0; i < dn; i++, j += 7, k += 3) {
            dpos[k] = df[j]; dpos[k + 1] = df[j + 1]; dpos[k + 2] = df[j + 2];
            dcol[k] = df[j + 3] / 255; dcol[k + 1] = df[j + 4] / 255; dcol[k + 2] = df[j + 5] / 255;
          }
          const dgeo = new THREE.BufferGeometry();
          dgeo.setAttribute("position", new THREE.BufferAttribute(dpos, 3));
          dgeo.setAttribute("color", new THREE.BufferAttribute(dcol, 3));
          dgeo.computeBoundingSphere();
          const dmat = new THREE.PointsMaterial({ size: 0.1, vertexColors: true, sizeAttenuation: true, transparent: true, opacity: 0.86 });
          denseRef.current = new THREE.Points(dgeo, dmat);
          denseRef.current.visible = showDense;
          scene.add(denseRef.current);
          densePositions = dpos;
          densePhotoColors = dcol;
        }

        // Robust framing, using the dense surface when present.
        const framing = densePositions ?? pos;
        const stride = Math.max(1, Math.floor(framing.length / 3 / 8000));
        const xs: number[] = [], ys: number[] = [], zs: number[] = [];
        for (let i = 0; i < framing.length; i += stride * 3) {
          xs.push(framing[i]); ys.push(framing[i + 1]); zs.push(framing[i + 2]);
        }
        const q = (a: number[], f: number) => a[Math.min(a.length - 1, Math.max(0, Math.floor(a.length * f)))];
        xs.sort((a, b) => a - b); ys.sort((a, b) => a - b); zs.sort((a, b) => a - b);
        const z0 = q(zs, 0.02);
        const z1 = q(zs, 0.98);
        let center = new THREE.Vector3(q(xs, 0.5), q(ys, 0.5), (z0 + z1) / 2);
        let radius = Math.max(
          (q(xs, 0.98) - q(xs, 0.02)) / 2,
          (q(ys, 0.98) - q(ys, 0.02)) / 2,
          (q(zs, 0.98) - q(zs, 0.02)) / 2,
          0.05,
        );
        const sparseHeight = colorByHeight(pos, z0, z1);
        const denseHeight = densePositions ? colorByHeight(densePositions, z0, z1) : null;
        const applyColors = (mode: "photo" | "height") => {
          const set = (obj: THREE.Points | null, photo: Float32Array, height: Float32Array) => {
            if (!obj) return;
            const attr = obj.geometry.getAttribute("color") as THREE.BufferAttribute;
            (attr.array as Float32Array).set(mode === "height" ? height : photo);
            attr.needsUpdate = true;
          };
          set(points, col, sparseHeight);
          set(denseRef.current, densePhotoColors ?? col, denseHeight ?? sparseHeight);
        };
        colorApplyRef.current = applyColors;
        applyColors(colorModeRef.current);

        controls.target.copy(center);
        camera.position.set(center.x + radius * 1.35, center.y - radius * 1.55, center.z + radius * 1.1);
        camera.up.set(0, 0, 1);
        camera.near = Math.max(radius / 1000, 0.001);
        camera.far = radius * 200;
        camera.updateProjectionMatrix();
        controls.update();
        cloudRadius = radius;
        material.size = Math.max(radius * 0.018, 0.02);
        baseSizeRef.current = material.size;
        if (denseRef.current) {
          (denseRef.current.material as THREE.PointsMaterial).size = Math.max(radius * 0.007, 0.02);
        }
        raycaster.params.Points = { threshold: Math.max(radius * 0.012, 0.005) };
        homeRef.current = { pos: camera.position.clone(), target: controls.target.clone() };

        const span = Math.max(radius * 3.2, 8);
        ground.scale.set(span, span, 1);
        ground.position.set(center.x, center.y, z0 - Math.max(radius * 0.004, 0.01));
        ground.visible = showGround;
        grid.scale.setScalar(span / 420);
        grid.position.set(center.x, center.y, z0 - Math.max(radius * 0.004, 0.01));
        grid.visible = showGrid;
        axes.visible = false;
        boundsRef.current = { center, radius, z0, z1 };

        // The cab camera runs along the rail. Frame that local corridor, not the
        // distant background tracks, so the track line is actually readable.
        if (m.camera_track?.length) {
          const a = m.camera_track[0], b = m.camera_track[m.camera_track.length - 1];
          let dx = b[0] - a[0], dy = b[1] - a[1];
          let len = Math.hypot(dx, dy);
          if (len < 0.05) { dx = 1; dy = 0; len = 1; }
          dx /= len; dy /= len;
          const px = -dy, py = dx;
          const mid = m.camera_track[Math.floor(m.camera_track.length / 2)];
          const half = Math.max(radius * 1.6, 2.0);
          const gauge = Math.max(radius * 0.035, 0.22);
          const floorZ = z0 + Math.max(radius * 0.002, 0.02);
          const railGroup = new THREE.Group();
          for (const side of [-1, 1]) {
            const p1 = new THREE.Vector3(mid[0] + px * gauge * side - dx * half, mid[1] + py * gauge * side - dy * half, floorZ);
            const p2 = new THREE.Vector3(mid[0] + px * gauge * side + dx * half, mid[1] + py * gauge * side + dy * half, floorZ);
            const curve = new THREE.LineCurve3(p1, p2);
            const rail = new THREE.Mesh(
              new THREE.TubeGeometry(curve, 2, Math.max(radius * 0.008, 0.035), 6, false),
              new THREE.MeshBasicMaterial({ color: 0x39d5ff, transparent: true, opacity: 0.95, depthTest: false }),
            );
            rail.renderOrder = 6;
            railGroup.add(rail);
          }
          // The cab camera moves along the rail; this is a schematic extension of
          // its direction, not a surveyed track alignment.
          scene.add(railGroup);
          trackRef.current = railGroup;
        }
        setLoading(false);
      })
      .catch((e) => { if (!disposed) { setError(String(e)); setLoading(false); } });

    const ro = new ResizeObserver(() => {
      const w = el.clientWidth, h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    });
    ro.observe(el);

    let raf = 0;
    const loop = () => { controls.update(); renderer.render(scene, camera); raf = requestAnimationFrame(loop); };
    loop();

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      ro.disconnect();
      renderer.domElement.removeEventListener("pointerdown", onDown);
      renderer.domElement.removeEventListener("pointerup", onUp);
      controls.dispose();
      if (points) { points.geometry.dispose(); (points.material as THREE.Material).dispose(); }
      if (selectedMarker) { selectedMarker.geometry.dispose(); (selectedMarker.material as THREE.Material).dispose(); }
      if (denseRef.current) { denseRef.current.geometry.dispose(); (denseRef.current.material as THREE.Material).dispose(); }
      groundRef.current?.geometry.dispose();
      (groundRef.current?.material as THREE.Material | undefined)?.dispose();
      trackRef.current?.traverse((obj) => {
        const mesh = obj as THREE.Mesh;
        mesh.geometry?.dispose();
        const sm = mesh.material as THREE.Material | THREE.Material[] | undefined;
        if (Array.isArray(sm)) sm.forEach((m) => m.dispose());
        else sm?.dispose();
      });
      trackCamRef.current?.geometry.dispose();
      (trackCamRef.current?.material as THREE.Material | undefined)?.dispose();
      trackPostsRef.current?.geometry.dispose();
      (trackPostsRef.current?.material as THREE.Material | undefined)?.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [cloudSite]);


  useEffect(() => {
    colorModeRef.current = colorMode;
    colorApplyRef.current?.(colorMode);
  }, [colorMode]);

  useEffect(() => {
    if (groundRef.current) groundRef.current.visible = showGround;
  }, [showGround]);

  useEffect(() => {
    if (trackRef.current) trackRef.current.visible = showTrack;
    if (trackCamRef.current) trackCamRef.current.visible = showTrack;
  }, [showTrack]);

  const setView = (kind: "top" | "iso" | "side") => {
    const b = boundsRef.current, camera = cameraRef.current, controls = controlsRef.current;
    if (!b || !camera || !controls) return;
    const { center: c, radius: r } = b;
    camera.up.set(0, 0, 1);
    if (kind === "top") {
      camera.up.set(0, 1, 0);
      camera.position.set(c.x, c.y, c.z + r * 2.6);
    } else if (kind === "side") {
      camera.position.set(c.x, c.y - r * 2.8, c.z + r * 0.02);
    } else {
      camera.position.set(c.x + r * 1.35, c.y - r * 1.55, c.z + r * 1.1);
    }
    controls.target.copy(c);
    camera.lookAt(c);
    controls.update();
  };

  const view = sel?.views[viewIdx];

  if (!cloudSite) {
    return (
      <div className="pointcloud pc-empty-state">
        <div>
          <b>{t(lang, "pcNoSite")}</b>
          <p>{t(lang, "pcNoSiteBody")}</p>

        </div>
      </div>
    );
  }

  return (
    <div className="pointcloud">
      <div ref={host} className="pc-canvas" />
      <div className="pc-badge">{meta?.site_name || meta?.label || t(lang, "pointCloud")} · {meta ? `${meta.count.toLocaleString()} pts${meta.dense_count ? ` + ${meta.dense_count.toLocaleString()} dense` : ""}` : "—"}</div>
      <div className="pc-hint">{t(lang, "pointPickHint")}</div>
      <div className="pc-layers" role="group" aria-label={t(lang, "pcLayers")}>
        <select className="pc-pkg" value={cloudSite} onChange={(e) => setCloudSite(e.target.value)} aria-label={t(lang, "pcPackage")}>
          <option value="koma_bridge">{t(lang, "pcColmap")}</option>
          <option value="koma_pi4">{t(lang, "pcPi4")}</option>
        </select>

        <button className="chip" aria-pressed={showCloud} onClick={() => {
          const next = !showCloud; setShowCloud(next);
          if (pointsRef.current) pointsRef.current.visible = next;
        }}>{t(lang, "pcCloud")}</button>
        <button className="chip" aria-pressed={showGrid} onClick={() => {
          const next = !showGrid; setShowGrid(next);
          if (gridRef.current) gridRef.current.visible = next;
        }}>{t(lang, "pcGrid")}</button>
        <button className="chip" aria-pressed={showPhoto} onClick={() => setShowPhoto(!showPhoto)}>{t(lang, "pcPhoto")}</button>
        {meta?.dense_url ? <button className="chip" aria-pressed={showDense} onClick={() => {
          const next = !showDense; setShowDense(next);
          if (denseRef.current) denseRef.current.visible = next;
        }}>{t(lang, "pcDense")}</button> : null}
        <button className="chip" aria-pressed={showGround} onClick={() => setShowGround(!showGround)}>{t(lang, "pcGround")}</button>
        <button className="chip" aria-pressed={showTrack} onClick={() => setShowTrack(!showTrack)}>{t(lang, "pcTrack")}</button>
        <button className="chip" aria-pressed={colorMode === "height"} onClick={() => setColorMode(colorMode === "height" ? "photo" : "height")}>{t(lang, "pcHeightColor")}</button>
        <label className="pc-slider">{t(lang, "pcSize")}
          <input type="range" min="0.5" max="3" step="0.1" value={pointSize} onChange={(e) => {
            const v = Number(e.target.value); setPointSize(v);
            if (pointsRef.current) (pointsRef.current.material as THREE.PointsMaterial).size = baseSizeRef.current * v;
          }} />
        </label>
        <label className="pc-slider">{t(lang, "pcOpacity")}
          <input type="range" min="0.2" max="1" step="0.05" value={pointOpacity} onChange={(e) => {
            const v = Number(e.target.value); setPointOpacity(v);
            if (pointsRef.current) (pointsRef.current.material as THREE.PointsMaterial).opacity = v;
          }} />
        </label>
      </div>
      <div className="pc-presets" role="group" aria-label="camera">
        <button className="chip" onClick={() => setView("top")}>{t(lang, "pcTop")}</button>
        <button className="chip" onClick={() => setView("iso")}>{t(lang, "pcIso")}</button>
        <button className="chip" onClick={() => setView("side")}>{t(lang, "pcSide")}</button>
      </div>
      <div className="pc-legend">
        <span><i className="lg-ground" />{t(lang, "pcLegendGround")}</span>
        <span><i className="lg-rail" />{t(lang, "pcLegendRail")}</span>
        <span><i className="lg-high" />{t(lang, "pcHeightColor")}</span>
        <em>{t(lang, "pcApproxGround")}</em>
      </div>
      <div className="pc-sparse-note">{t(lang, "pcSparseNote")}</div>
      {!sel && meta?.views?.[0] ? (() => {
        const v = meta.views[0] as View & { id?: string; file?: string };
        const id = v.id ?? v.image_id;
        return (
          <div className="pc-context">
            <img src={v.url ?? `/api/pointcloud/view/${encodeURIComponent(id)}?site=${encodeURIComponent(siteId)}`} alt={id} />
            <span>{t(lang, "pcSource")} · {id}</span>
          </div>
        );
      })() : null}
      {loading && <div className="pc-loading">{t(lang, "loading")}</div>}
      {error && <div className="pc-error">{error}</div>}
      {sel && (
        <div className="pc-panel" role="dialog" aria-label={t(lang, "pointDetail")}>
          <div className="pc-head">
            <b>{sel.site || sel.member}</b>
            <span className="pc-actions">
              <button className="btn btn-sm" onClick={() => {
                if (homeRef.current && cameraRef.current && controlsRef.current) {
                  cameraRef.current.position.copy(homeRef.current.pos);
                  controlsRef.current.target.copy(homeRef.current.target);
                  controlsRef.current.update();
                }
              }}>{t(lang, "pcReset")}</button>
              <button className="btn btn-sm" onClick={() => setSel(null)}>{t(lang, "prioClose")}</button>
            </span>
          </div>
          <dl className="pc-metrics">
            {sel.metrics ? (
              <>
                <dt>{t(lang, "pcKm")}</dt><dd>{(sel.km! / 1000).toFixed(3)}k</dd>
                <dt>{t(lang, "pcLocal")}</dt><dd>X {sel.local!.x} · Y {sel.local!.y} · Z {sel.local!.z} m</dd>
                <dt>{t(lang, "pcRailOffset")}</dt><dd>{sel.metrics.rail_offset_m.toFixed(2)} m</dd>
                <dt>{t(lang, "pcHeight")}</dt><dd>{sel.metrics.height_vs_rail_m >= 0 ? "+" : ""}{sel.metrics.height_vs_rail_m.toFixed(2)} m</dd>
              </>
            ) : null}
            {sel.local ? <><dt>{t(lang, "pcLocal")}</dt><dd>X {sel.local.x} · Y {sel.local.y} · Z {sel.local.z}</dd></> : null}
            <dt>{t(lang, "pcScale")}</dt><dd>{t(lang, "pcScaleRelative")}</dd>
            {sel.observation_count != null ? <><dt>{t(lang, "pcObservations")}</dt><dd>{sel.observation_count}</dd></> : null}
            {sel.link_method ? <><dt>{t(lang, "pcLinkMethod")}</dt><dd>{sel.link_method}</dd></> : null}
            {view?.residual != null ? <><dt>{t(lang, "pcResidual")}</dt><dd>{view.residual.toFixed(2)} px</dd></> : null}
          </dl>
          {view && showPhoto ? (
            <>
              <div className="pc-img-wrap">
                <img src={view.url} alt={view.image_id} />
                <i style={{ left: `${(view.u / view.width) * 100}%`, top: `${(view.v / view.height) * 100}%` }} />
              </div>
              <div className="pc-source-meta">{view.image_id} · {view.captured_at || ""}</div>
              <div className="pc-viewrow">
                {sel.views.map((v, i) => (
                  <button key={v.image_id} className="chip" aria-pressed={i === viewIdx}
                    onClick={() => setViewIdx(i)}>V{i + 1}</button>
                ))}
              </div>
              {view.source_url ? <p className="pc-note"><a href={view.source_url} target="_blank" rel="noreferrer">{t(lang, "pcSource")} ↗</a></p> : null}
              <p className="pc-note">{meta?.note || t(lang, "pointCloudNote")}</p>
            </>
          ) : showPhoto ? <p className="pc-note">{t(lang, "pcNoView")}</p> : null}
        </div>
      )}
    </div>
  );
}
