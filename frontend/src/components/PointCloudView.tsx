import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { t, type Lang } from "../lib/i18n";

type View = { image_id: string; url: string; u: number; v: number; depth?: number; width: number; height: number; score: number; residual?: number; source_url?: string; captured_at?: string; license?: string; artist?: string };
type Pick = {
  index: number; member: string; site?: string; scale_status?: string; link_method?: string;
  km?: number; local?: { x: number; y: number; z: number };
  metrics?: { rail_offset_m: number; height_vs_rail_m: number; scale_status: string };
  views: View[];
};
type Meta = { id?: string; site_id?: string; site_name?: string; label?: string; count: number; points_url: string; note?: string; scale?: { status: string; basis: string }; scale_status?: string; link_method?: string; views: View[] };

export default function PointCloudView({ lang }: { lang: Lang }) {
  const host = useRef<HTMLDivElement>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [sel, setSel] = useState<Pick | null>(null);
  const [viewIdx, setViewIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);

  useEffect(() => {
    let disposed = false;
    const el = host.current;
    if (!el) return;
    let renderer: THREE.WebGLRenderer;
    let points: THREE.Points;
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
    const gm = grid.material as THREE.Material;
    gm.transparent = true; gm.opacity = 0.22;
    scene.add(grid);
    scene.add(new THREE.AxesHelper(20));

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
          body: JSON.stringify({ index: hit.index, top_k: 3 }),
        });
        if (!r.ok) throw new Error(await r.text());
        const data: Pick = await r.json();
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

    fetch("/api/pointcloud/meta")
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
          size: 0.075, vertexColors: true, sizeAttenuation: true,
        });
        points = new THREE.Points(geo, material);
        scene.add(points);
        if (m.link_method === "colmap_track" && geo.boundingSphere) {
          const sphere = geo.boundingSphere;
          const radius = Math.max(sphere.radius, 1);
          controls.target.copy(sphere.center);
          camera.position.set(
            sphere.center.x + radius * 1.2,
            sphere.center.y - radius * 1.7,
            sphere.center.z + radius * 1.05,
          );
          camera.near = Math.max(radius / 1000, 0.01);
          camera.far = radius * 100;
          camera.updateProjectionMatrix();
          controls.update();
          material.size = Math.max(radius * 0.0022, 0.002);
          raycaster.params.Points = { threshold: Math.max(radius * 0.008, 0.01) };
          grid.visible = false;
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
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  const view = sel?.views[viewIdx];

  return (
    <div className="pointcloud">
      <div ref={host} className="pc-canvas" />
      <div className="pc-badge">{meta?.site_name || meta?.label || t(lang, "pointCloud")} · {meta ? `${meta.count.toLocaleString()} pts` : "—"}</div>
      <div className="pc-hint">{t(lang, "pointPickHint")}</div>
      {loading && <div className="pc-loading">{t(lang, "loading")}</div>}
      {error && <div className="pc-error">{error}</div>}
      {sel && (
        <div className="pc-panel" role="dialog" aria-label={t(lang, "pointDetail")}>
          <div className="pc-head">
            <b>{sel.site || sel.member}</b>
            <button className="btn btn-sm" onClick={() => setSel(null)}>{t(lang, "prioClose")}</button>
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
            <dt>{t(lang, "pcScale")}</dt><dd>{t(lang, "pcScaleRelative")}</dd>
            {sel.link_method ? <><dt>{t(lang, "pcLinkMethod")}</dt><dd>{sel.link_method}</dd></> : null}
            {view?.residual != null ? <><dt>{t(lang, "pcResidual")}</dt><dd>{view.residual.toFixed(2)} px</dd></> : null}
          </dl>
          {view ? (
            <>
              <div className="pc-img-wrap">
                <img src={`${view.url}?v=${view.image_id}`} alt={view.image_id} />
                <i style={{ left: `${(view.u / view.width) * 100}%`, top: `${(view.v / view.height) * 100}%` }} />
              </div>
              <div className="pc-viewrow">
                {sel.views.map((v, i) => (
                  <button key={v.image_id} className="chip" aria-pressed={i === viewIdx}
                    onClick={() => setViewIdx(i)}>V{i + 1}</button>
                ))}
              </div>
              {view.source_url ? <p className="pc-note"><a href={view.source_url} target="_blank" rel="noreferrer">{t(lang, "pcSource")} ↗</a></p> : null}
              <p className="pc-note">{meta?.note || t(lang, "pointCloudNote")}</p>
            </>
          ) : <p className="pc-note">{t(lang, "pcNoView")}</p>}
        </div>
      )}
    </div>
  );
}
