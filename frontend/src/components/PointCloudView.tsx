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
type Meta = { id?: string; site?: string; site_id?: string; site_name?: string; label?: string; count: number; points_url: string; dense_url?: string; dense_count?: number; note?: string; scale?: { status: string; basis: string }; scale_status?: string; link_method?: string; views: View[] };
type Site = { site: string; name: string; kind: string; available: boolean };

export default function PointCloudView({ lang, siteId, onSite }: { lang: Lang; siteId: string | null; onSite: (s: string | null) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
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
  const [showCloud, setShowCloud] = useState(true);
  const [showGrid, setShowGrid] = useState(false);
  const [showPhoto, setShowPhoto] = useState(true);
  const [showDense, setShowDense] = useState(true);
  const denseRef = useRef<THREE.Points | null>(null);
  const [pointSize, setPointSize] = useState(1);
  const [pointOpacity, setPointOpacity] = useState(1);
  const baseSizeRef = useRef(1);

  useEffect(() => {
    fetch("/api/pointcloud/sites").then((r) => r.json()).then((d) => setSites(d.sites || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!siteId) { setLoading(false); setSel(null); setMeta(null); return; }
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
    scene.background = new THREE.Color("#11171c");
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

    const grid = new THREE.GridHelper(420, 42, 0x2e3a46, 0x252f36);
    grid.rotation.x = Math.PI / 2;
    grid.position.set(180, 0, 0);
    gridRef.current = grid;
    const gm = grid.material as THREE.Material;
    gm.transparent = true; gm.opacity = 0.22;
    scene.add(grid);
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
          body: JSON.stringify({ index: hit.index, top_k: 3, site: siteId }),
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

    fetch(`/api/pointcloud/meta?site=${encodeURIComponent(siteId)}`)
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
          const dmat = new THREE.PointsMaterial({ size: Math.max(0.002, (dgeo.boundingSphere?.radius || 1) * 0.0012), vertexColors: true, sizeAttenuation: true, transparent: true, opacity: 0.55 });
          denseRef.current = new THREE.Points(dgeo, dmat);
          denseRef.current.visible = showDense;
          scene.add(denseRef.current);
        }
        if (m.link_method && geo.boundingSphere) {
          // Robust framing: Mapillary/learned clouds often have distant outliers.
          const stride = Math.max(1, Math.floor(n / 6000));
          const xs: number[] = [], ys: number[] = [], zs: number[] = [];
          for (let i = 0; i < n; i += stride) {
            xs.push(pos[i * 3]); ys.push(pos[i * 3 + 1]); zs.push(pos[i * 3 + 2]);
          }
          const q = (a: number[], f: number) => a[Math.min(a.length - 1, Math.max(0, Math.floor(a.length * f)))];
          xs.sort((a, b) => a - b); ys.sort((a, b) => a - b); zs.sort((a, b) => a - b);
          const center = new THREE.Vector3(q(xs, 0.5), q(ys, 0.5), q(zs, 0.5));
          const radius = Math.max(
            (q(xs, 0.98) - q(xs, 0.02)) / 2,
            (q(ys, 0.98) - q(ys, 0.02)) / 2,
            (q(zs, 0.98) - q(zs, 0.02)) / 2,
            0.05,
          );
          controls.target.copy(center);
          camera.position.set(center.x + radius * 1.0, center.y - radius * 1.8, center.z + radius * 0.9);
          camera.near = Math.max(radius / 1000, 0.001);
          camera.far = radius * 200;
          camera.updateProjectionMatrix();
          controls.update();
          cloudRadius = radius;
          material.size = Math.max(radius * 0.02, 0.01);
          baseSizeRef.current = material.size;
          raycaster.params.Points = { threshold: Math.max(radius * 0.012, 0.005) };
          grid.visible = false;
          axes.visible = false;
          homeRef.current = { pos: camera.position.clone(), target: controls.target.clone() };
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
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [siteId]);

  const view = sel?.views[viewIdx];

  if (!siteId) {
    return (
      <div className="pointcloud pc-empty-state">
        <div>
          <b>{t(lang, "pcNoSite")}</b>
          <p>{t(lang, "pcNoSiteBody")}</p>
          <label>{t(lang, "pcSite")}
            <select value="" onChange={(e) => onSite(e.target.value || null)}>
              <option value="">—</option>
              {sites.map((x) => <option key={x.site} value={x.site}>{x.name}</option>)}
            </select>
          </label>
        </div>
      </div>
    );
  }

  return (
    <div className="pointcloud">
      <div ref={host} className="pc-canvas" />
      <div className="pc-badge">{meta?.site_name || meta?.label || t(lang, "pointCloud")} · {meta ? `${meta.count.toLocaleString()} pts` : "—"}</div>
      <div className="pc-hint">{t(lang, "pointPickHint")}</div>
      <div className="pc-layers" role="group" aria-label={t(lang, "pcLayers")}>
        <label className="pc-slider">{t(lang, "pcSite")}
          <select value={siteId} onChange={(e) => onSite(e.target.value || null)}>
            {sites.map((x) => <option key={x.site} value={x.site}>{x.name}</option>)}
          </select>
        </label>
        <button className="chip" aria-pressed={showCloud} onClick={() => {
          const next = !showCloud; setShowCloud(next);
          if (pointsRef.current) pointsRef.current.visible = next;
        }}>{t(lang, "pcCloud")}</button>
        <button className="chip" aria-pressed={showGrid} onClick={() => {
          const next = !showGrid; setShowGrid(next);
          if (gridRef.current) gridRef.current.visible = next;
          if (axesRef.current) axesRef.current.visible = next;
        }}>{t(lang, "pcGrid")}</button>
        <button className="chip" aria-pressed={showPhoto} onClick={() => setShowPhoto(!showPhoto)}>{t(lang, "pcPhoto")}</button>
        {meta?.dense_url ? <button className="chip" aria-pressed={showDense} onClick={() => {
          const next = !showDense; setShowDense(next);
          if (denseRef.current) denseRef.current.visible = next;
        }}>{t(lang, "pcDense")}</button> : null}
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
      <div className="pc-sparse-note">{t(lang, "pcSparseNote")}</div>
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
