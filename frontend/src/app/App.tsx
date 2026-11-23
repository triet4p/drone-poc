import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DEFECTS, LANGS, LOCALE, RANK_TIP, t, type Lang, type TKey } from "../lib/i18n";
import MapView from "../components/MapView";
import PointCloudView from "../components/PointCloudView";
import { AnalysisView } from "../features/analysis/AnalysisView";
import { PlanView } from "../features/plan/PlanView";
import { PriorityView } from "../features/priority/PriorityView";
import { ScheduleView } from "../features/schedule/ScheduleView";
import { RAIL_PHOTOS, type RailPhoto } from "../lib/railContext";

type Judgement = { rank: string; comment: string; actor: string; created_at: string };
type Detection = {
  id: number; image_id: string; label: string; score: number;
  box: [number, number, number, number]; model: string; judgement: Judgement | null;
};
type ImageRow = {
  id: string; filename: string; width: number; height: number;
  km_m: number | null; structure_id: string | null; member_id: string | null; site_id: string | null;
  structure_name: string | null; member_name: string | null; license: string;
  source: string; attribution?: string | null; detections: Detection[]; thumb: string;
};
type Member = { id: string; structure_id: string; code: string; name: string; km_m: number | null };
type Structure = {
  id: string; code: string; name: string; kind: string;
  km_start: number; km_end: number; members: Member[];
};
type Job = { id: string; image_id: string; status: string; progress: number; error?: string | null };
type State = {
  model: string; images: ImageRow[]; jobs: Job[];
  counts: { images: number; candidates: number; confirmed: number };
};

const RANKS = ["AA", "A1", "A2", "B", "C", "S"];
const TABS: { id: "sched" | "plan" | "inspect" | "anal" | "prio"; key: TKey; live: boolean }[] = [
  { id: "sched", key: "tabSched", live: false },
  { id: "plan", key: "tabPlan", live: false },
  { id: "inspect", key: "tabInspect", live: true },
  { id: "anal", key: "tabAnal", live: false },
  { id: "prio", key: "tabPrio", live: true },
];
const TAB_ICON: Record<string, string> = {
  sched: "M3 4h10v9H3zM3 7h10M5 2v3M11 2v3",
  plan: "M2 5h3l1-2h4l1 2h3v8H2zM8 7a2 2 0 1 0 0 4 2 2 0 0 0 0-4",
  inspect: "M2 3l4-1 4 1 4-1v11l-4 1-4-1-4 1zM6 2v11M10 3v11",
  anal: "M2 13h12M4 10l3-3 2 2 4-5",
  prio: "M3 4h10M3 8h10M3 12h7",
};
const LICENSES = ["client", "cc-by", "cc0", "pd", "demo", "unknown"] as const;

const fmtKm = (v: number | null) => (v == null ? "—" : `${(v / 1000).toFixed(3)}k`);
const fmtTime = (s: string, lang: Lang) => {
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleString(LOCALE[lang], {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hour12: false,
  });
};
function initialLang(): Lang {
  const v = localStorage.getItem("lang");
  return v === "en" || v === "vi" || v === "ja" ? v : "ja";
}

function Strip({ assets, images, onPick }: { assets: Structure[]; images: ImageRow[]; onPick: (id: string) => void }) {
  if (!assets.length) return null;
  const from = Math.min(...assets.map((a) => a.km_start));
  const to = Math.max(...assets.map((a) => a.km_end));
  const X = (km: number) => ((km - from) / (to - from)) * 1000;
  return (
    <svg className="strip" viewBox="0 0 1000 72" role="img" aria-label="longitudinal profile">
      {assets.map((a) => {
        const x = X(a.km_start), w = X(a.km_end) - x;
        const fill = a.kind === "bridge" ? "var(--accent)" : a.kind === "tunnel" ? "#3A4249" : "var(--surface2)";
        return (
          <g key={a.id}>
            <rect x={x + 1} y={12} width={Math.max(1, w - 2)} height={24} rx={3} fill={fill} opacity={a.kind === "earth" ? .9 : .85} />
            {w > 90 && <text x={x + w / 2} y={29} textAnchor="middle" fontSize="12" fill={a.kind === "earth" ? "var(--ink2)" : "#fff"}>{a.code}</text>}
          </g>
        );
      })}
      <line x1="0" x2="1000" y1="48" y2="48" stroke="var(--line)" />
      {images.filter((i) => i.km_m != null).map((i) => (
        <g key={i.id} className="strip-dot" onClick={() => onPick(i.id)}>
          <circle cx={X(i.km_m!)} cy={48} r="6" fill={i.detections.some((d) => d.judgement) ? "var(--h-A2)" : "var(--accent)"} stroke="var(--surface)" strokeWidth="2" />
          <title>{`${i.filename} ${fmtKm(i.km_m)}`}</title>
        </g>
      ))}
      <text x="0" y="67" fontSize="11" fill="var(--ink3)">{(from / 1000).toFixed(2)}k</text>
      <text x="1000" y="67" fontSize="11" fill="var(--ink3)" textAnchor="end">{(to / 1000).toFixed(2)}k</text>
    </svg>
  );
}

export default function App() {
  const [data, setData] = useState<State | null>(null);
  const [assets, setAssets] = useState<Structure[]>([]);
  const [imgId, setImgId] = useState<string | null>(null);

  const [detId, setDetId] = useState<number | null>(null);
  const [filter, setFilter] = useState<"all" | "open" | "done">("all");
  const [rank, setRank] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [stage, setStage] = useState({ w: 0, h: 0 });
  const [busy, setBusy] = useState(0);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLangState] = useState<Lang>(initialLang);
  const [tab, setTab] = useState<"sched" | "plan" | "inspect" | "anal" | "prio">("inspect");
  const [edit, setEdit] = useState({ structure_id: "", member_id: "", km: "", license: "unknown" });
  const [saving, setSaving] = useState(false);
  const [mode, setMode] = useState<"map" | "point" | "measure" | "photo">("map");
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [railPhoto, setRailPhoto] = useState<RailPhoto | null>(null);

  const tr = useCallback((k: TKey, v?: Record<string, string | number>) => t(lang, k, v), [lang]);
  const setLang = (l: Lang) => { setLangState(l); localStorage.setItem("lang", l); };

  const wrapRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const dragRef = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const toastTimer = useRef<number | undefined>(undefined);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.title = t(lang, "appTitle");
  }, [lang]);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => { document.documentElement.dataset.theme = mq.matches ? "dark" : "light"; };
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  const notify = (m: string) => {
    setToast(m);
    window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(null), 2600);
  };

  const refresh = useCallback(async (): Promise<State | null> => {
    try {
      const r = await fetch("/api/state");
      if (!r.ok) throw new Error(await r.text());
      const s: State = await r.json();
      setData(s);
      setError(null);
      return s;
    } catch (e) {
      setError(String(e));
      return null;
    }
  }, []);

  useEffect(() => {
    refresh();
    fetch("/api/assets").then((r) => r.json()).then(setAssets).catch(() => {});
  }, [refresh]);
  useEffect(() => {
    if (imgId || !data?.images.length) return;
    setImgId(data.images[0].id);
  }, [data, imgId]);

  const running = useMemo(
    () => (data?.jobs ?? []).filter((j) => j.status === "queued" || j.status === "running"),
    [data?.jobs]
  );
  const failed = useMemo(
    () => (data?.jobs ?? []).filter((j) => j.status === "failed"),
    [data?.jobs]
  );
  useEffect(() => {
    if (!running.length) return;
    const timer = window.setInterval(refresh, 1500);
    return () => window.clearInterval(timer);
  }, [running.length, refresh]);

  const image = data?.images.find((i) => i.id === imgId) ?? null;
  const imageSite = image?.site_id ?? null;
  const det = image?.detections.find((d) => d.id === detId) ?? null;

  useEffect(() => {
    setDetId((prev) => {
      const im = data?.images.find((i) => i.id === imgId);
      return prev && im?.detections.some((d) => d.id === prev) ? prev : null;
    });
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [imgId]);
  useEffect(() => {
    setRank(det?.judgement?.rank ?? null);
    setComment(det?.judgement?.comment ?? "");
  }, [det?.id, det?.judgement?.rank, det?.judgement?.comment]);
  useEffect(() => {
    if (!image) return;
    setEdit({
      structure_id: image.structure_id ?? "",
      member_id: image.member_id ?? "",
      km: image.km_m == null ? "" : String(image.km_m),
      license: image.license ?? "unknown",
    });
  }, [image?.id, image?.structure_id, image?.member_id, image?.km_m, image?.license]);

  const fit = useCallback(() => {
    const im = imgRef.current, wrap = wrapRef.current;
    if (!im || !wrap || !im.naturalWidth) return;
    const s = Math.min(wrap.clientWidth / im.naturalWidth, wrap.clientHeight / im.naturalHeight);
    setStage({ w: im.naturalWidth * s, h: im.naturalHeight * s });
  }, []);

  useEffect(() => {
    if (!wrapRef.current) return;
    const ro = new ResizeObserver(fit);
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, [fit, image?.id]);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      setZoom((z) => {
        const n = Math.min(5, Math.max(1, z * (e.deltaY < 0 ? 1.12 : 1 / 1.12)));
        if (n === 1) setPan({ x: 0, y: 0 });
        return n;
      });
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const uploadFiles = async (files: FileList | File[]) => {
    const list = Array.from(files).filter((f) => f.type.startsWith("image/"));
    if (!list.length) return;
    setBusy((b) => b + list.length);
    let lastId: string | null = null;
    for (const file of list) {
      try {
        const fd = new FormData();
        fd.append("file", file);
        const r = await fetch("/api/upload", { method: "POST", body: fd });
        if (!r.ok) {
          notify(tr("uploadFail", { f: file.name }));
          setError(tr("errorPrefix") + (await r.text()));
        } else {
          const res = await r.json();
          lastId = res.image_id;
          notify(tr("uploadedToast", { f: file.name }));
        }
      } finally {
        setBusy((b) => Math.max(0, b - 1));
      }
    }
    const s = await refresh();
    if (lastId) setImgId(lastId);
    else if (s?.images.length && !imgId) setImgId(s.images[0].id);
  };

  const confirm = async () => {
    if (!det) return;
    if (!rank) { notify(tr("chooseRank")); return; }
    const r = await fetch("/api/judgement", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ detection_id: det.id, rank, comment }),
    });
    if (!r.ok) { notify(tr("saveFail")); return; }
    notify(tr("confirmedToast", { label: DEFECTS[lang][det.label] ?? det.label, rank }));
    await refresh();
  };

  const saveLocation = async () => {
    if (!image) return;
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        structure_id: edit.structure_id || null,
        member_id: edit.member_id || null,
        license: edit.license,
      };
      if (edit.km !== "") body.km_m = Number(edit.km);
      const r = await fetch(`/api/image/${image.id}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      if (!r.ok) { notify(tr("saveFail")); setError(await r.text()); return; }
      notify(tr("locSaved"));
      await refresh();
    } finally {
      setSaving(false);
    }
  };

  const retry = async (jobId: string) => {
    await fetch(`/api/job/${jobId}/retry`, { method: "POST" });
    await refresh();
  };

  const downloadReport = async (force = false) => {
    if (!force && data && data.counts.candidates > data.counts.confirmed) {
      const n = data.counts.candidates - data.counts.confirmed;
      if (!window.confirm(tr("reportPending", { n }))) return;
    }
    const r = await fetch(`/api/report${force ? "?force=true" : ""}`);
    if (r.status === 409) {
      if (window.confirm(tr("reportLicense"))) return downloadReport(true);
      return;
    }
    if (!r.ok) { notify(tr("saveFail")); return; }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "調書_draft.docx"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  };

  const nextOpen = () => {
    if (!image) return;
    const i = image.detections.findIndex((d) => d.id === detId);
    const next = image.detections.find((d, k) => k > i && !d.judgement) ?? image.detections.find((d) => !d.judgement);
    if (next) setDetId(next.id);
    else notify(tr("allDone"));
  };

  const shown = (data?.images ?? [])
    .filter((im) => imageSite != null && im.site_id === imageSite)
    .filter((im) =>
      filter === "all" ? true :
      filter === "open" ? im.detections.some((d) => !d.judgement) :
      im.detections.some((d) => d.judgement)
    );

  const structures = assets;
  const members = structures.find((s) => s.id === edit.structure_id)?.members ?? [];
  const licLabel = (v: string) => tr(v === "client" ? "licClient" : v === "cc-by" ? "licCcby" : v === "cc0" ? "licCc0" : v === "pd" ? "licPd" : v === "demo" ? "licDemo" : "licUnknown");

  const current = TABS.find((x) => x.id === tab)!;
  return (
    <div className="dws-shell">
      <a className="skip-link" href="#main">本文へスキップ</a>
      <header className="dws-topbar appbar">
        <button className="btn btn-sm nav-toggle" onClick={() => setNavCollapsed((v) => !v)}
          aria-label="Toggle sidebar" title="Toggle sidebar">☰</button>
        <div className="brand"><span className="mark">軌</span><span className="brand-name">{tr("appTitle")}</span><span className="tag">{tr("appTag")}</span></div>
        <div className="ctx">{imageSite === "koma_bridge"
          ? <><b>高麗川橋梁（八高線）</b>　35.909N / 139.334E　11/2026</>
          : <><b>{tr("ctxLine")}</b>　12k400–15k600　{tr("ctxPeriod")}</>}</div>
        <div className="spacer" />
        <div className="lang" role="group" aria-label={tr("language")}>
          {LANGS.map((l) => (
            <button key={l.id} aria-pressed={lang === l.id} onClick={() => setLang(l.id)}>{l.label}</button>
          ))}
        </div>
        <input ref={fileRef} type="file" accept="image/*" multiple hidden onChange={(e) => e.target.files && uploadFiles(e.target.files)} />
        <button className="btn" onClick={() => fileRef.current?.click()} disabled={busy > 0}
          aria-label={tr("upload")} title={tr("upload")}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><path d="M8 10V3M5 6l3-3 3 3M3 10v3h10v-3"/></svg>
          <span className="btn-label">{busy > 0 ? tr("uploading", { n: busy }) : tr("upload")}</span>
        </button>
        <button className="btn btn-primary" onClick={() => downloadReport()}
          aria-label={tr("report")} title={tr("report")}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><path d="M4 2h6l2 2v10H4zM10 2v3h3M6 8h6M6 11h4"/></svg>
          <span className="btn-label">{tr("report")}</span>
        </button>
      </header>

      <div className={`dws-workspace ${navCollapsed ? "nav-collapsed" : ""}`}>
        <aside className="dws-sidebar sidenav" aria-label="画面">
          <div className="side-label">点検ワークスペース</div>
          {TABS.map((x) => (
            <button key={x.id} className="dws-nav-item nav-item" aria-current={tab === x.id ? "page" : undefined}
              onClick={() => setTab(x.id)}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true">
                <path d={TAB_ICON[x.id]} />
              </svg>
              <span className="nav-label">{tr(x.key)}</span>
              <span className={`nav-badge ${x.live ? "live" : "demo"}`}>{x.live ? "LIVE" : "DEMO"}</span>
            </button>
          ))}
          <div className="side-foot">
            <div className="side-label">凡例</div>
            <p><span className="nav-badge live">LIVE</span> DB・API 実データ</p>
            <p><span className="nav-badge demo">DEMO</span> 説明用の固定データ</p>
          </div>
        </aside>

        <main className="dws-main main" id="main">
          <header className="page-head">
            <div>
              <h1 className="dws-title">{tr(current.key)}</h1>
              <p className="dws-muted">{current.live ? "実データ（DB/API）" : "デモデータ（画面説明用）"}</p>
            </div>
            <span className={`nav-badge ${current.live ? "live" : "demo"}`}>{current.live ? "LIVE" : "DEMO"}</span>
          </header>

      {tab === "inspect" && (
        <p className="banner"><b>{tr("bannerStrong")}</b> {tr("bannerBody")}</p>
      )}
      {error && <div className="errorbar">{tr("errorPrefix")}{error}</div>}

      {(running.length > 0 || failed.length > 0) && (
        <div className="jobbar" role="status">
          {running.map((j) => {
            const im = data?.images.find((i) => i.id === j.image_id);
            return (
              <div className="job" key={j.id}>
                <span className="job-name">{im?.filename ?? j.image_id}</span>
                <span className="job-state">{j.status === "queued" ? tr("queued") : tr("running", { p: Math.round(j.progress) })}</span>
                <div className="bar"><i style={{ width: `${Math.max(3, j.progress)}%` }} /></div>
              </div>
            );
          })}
          {failed.map((j) => {
            const im = data?.images.find((i) => i.id === j.image_id);
            return (
              <div className="job failed" key={j.id}>
                <span className="job-name">{im?.filename ?? j.image_id}</span>
                <span className="job-state">{tr("jobFailed")}: {j.error}</span>
                <div className="actions"><button className="btn btn-sm" onClick={() => retry(j.id)}>{tr("jobRetry")}</button></div>
              </div>
            );
          })}
        </div>
      )}

      {tab === "inspect" && (
      <div className={`layout ${mode === "point" ? "point-layout" : ""}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); uploadFiles(e.dataTransfer.files); }}>
        <aside className="panel list" aria-label={tr("listTitle")}>
          <div className="list-head">
            <h2>{tr("listTitle")}</h2>
            <div className="counts">
              {data ? tr("counts", {
                i: shown.length,
                c: shown.reduce((n, im) => n + im.detections.length, 0),
                f: shown.reduce((n, im) => n + im.detections.filter((d) => d.judgement).length, 0),
              }) : tr("loading")}
            </div>
            <div className="chips" role="group">
              {(["all", "open", "done"] as const).map((f) => (
                <button key={f} className="chip" aria-pressed={filter === f} onClick={() => setFilter(f)}>
                  {f === "all" ? tr("filterAll") : f === "open" ? tr("filterOpen") : tr("filterDone")}
                </button>
              ))}
            </div>
          </div>
          <ul>
            {shown.map((im) => {
              const done = im.detections.filter((d) => d.judgement).length;
              const active = running.find((j) => j.image_id === im.id);
              return (
                <li key={im.id}>
                  <button className={im.id === imgId ? "sel" : ""} onClick={() => setImgId(im.id)}>
                    <img className="thumb" src={im.thumb} alt="" />
                    <span className="meta">
                      <b>{im.member_name || im.filename}</b>
                      <span>{im.structure_name || tr("none")}　{fmtKm(im.km_m)}</span>
                      <span>{active ? tr("processing") : tr("cand", { n: im.detections.length, m: done })}</span>
                    </span>
                  </button>
                </li>
              );
            })}
            {!shown.length && <li><p className="empty-small">{tr("listEmpty")}</p></li>}
          </ul>
        </aside>

        <section className="panel viewer" aria-label={tr("listTitle")}>
          <div className="viewer-head">
            <b>{image?.filename ?? tr("noImage")}</b>
            <span>{image ? tr("meta", { w: image.width, h: image.height, n: image.detections.length }) : ""}</span>
            <div className="view-toggle" role="group" aria-label="3D / photo">
              <button aria-pressed={mode === "map"} onClick={() => setMode("map")}>3D</button>
              <button aria-pressed={mode === "point"} onClick={() => setMode("point")}>{tr("pointCloud")}</button>
              <button aria-pressed={mode === "measure"} onClick={() => setMode("measure")}>{tr("measure")}</button>
              <button aria-pressed={mode === "photo"} onClick={() => setMode("photo")}>写真</button>
            </div>
            {image && <a className="mini-link" href={`/api/original/${image.id}`} target="_blank" rel="noreferrer">{tr("original")}</a>}
          </div>
          {mode === "point" ? (
            <PointCloudView lang={lang} siteId={imageSite} />
          ) : mode !== "photo" ? (
            <MapView images={data?.images ?? []} selectedId={imgId} lang={lang} siteId={imageSite}
              measure={mode === "measure"} onSelect={(id) => setImgId(id)} />
          ) : (
          <div className="stage-wrap" ref={wrapRef}
            onPointerDown={(e) => {
              if (zoom > 1) { dragRef.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y }; e.currentTarget.setPointerCapture(e.pointerId); }
            }}
            onPointerMove={(e) => {
              const d = dragRef.current; if (!d) return;
              setPan({ x: d.px + e.clientX - d.x, y: d.py + e.clientY - d.y });
            }}
            onPointerUp={() => { dragRef.current = null; }}>
            {image ? (
              <div className="stage" style={{
                width: stage.w || undefined, height: stage.h || undefined,
                transform: `translate(-50%,-50%) translate(${pan.x}px,${pan.y}px) scale(${zoom})`,
              }}>
                <img ref={imgRef} src={`/api/media/${image.id}`} alt={image.filename}
                  onLoad={() => { fit(); setZoom(1); setPan({ x: 0, y: 0 }); }} />
                <div className="overlay">
                  {image.detections.map((d) => {
                    const [x1, y1, x2, y2] = d.box;
                    const label = DEFECTS[lang][d.label] ?? d.label;
                    return (
                      <button key={d.id}
                        className={`box ${detId === d.id ? "sel" : ""}`}
                        style={{ left: `${x1 * 100}%`, top: `${y1 * 100}%`, width: `${(x2 - x1) * 100}%`, height: `${(y2 - y1) * 100}%` }}
                        onClick={(e) => { e.stopPropagation(); setDetId(d.id); }}
                        title={`${label} ${d.score.toFixed(2)}`}>
                        <span className="cap">{label} {d.score.toFixed(2)}{d.judgement ? " ✓" : ""}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="drop">
                <p>{tr("drop")}</p>
                <button className="btn" onClick={() => fileRef.current?.click()}>{tr("choose")}</button>
              </div>
            )}
          </div>
          )}
          <div className="viewer-foot">
            <span>{tr("hint")}</span>
            <span>{image?.source === "demo" ? tr("demo") : image?.source === "reference" ? tr("reference") : image ? tr("uploaded") : ""}</span>
          </div>
          {imageSite !== "koma_bridge" && (
            <div className="strip-wrap">
              <div className="strip-title">{tr("stripTitle")}</div>
              <Strip assets={assets} images={data?.images ?? []} onPick={setImgId} />
            </div>
          )}
        </section>

        <aside className="panel detail">
          {image && imageSite !== "koma_bridge" && (
            <section className="loc">
              <h3>{tr("locTitle")}</h3>
              <div className="loc-grid">
                <label>{tr("locStructure")}
                  <select value={edit.structure_id} onChange={(e) => setEdit({ ...edit, structure_id: e.target.value, member_id: "" })}>
                    <option value="">—</option>
                    {structures.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </label>
                <label>{tr("locMember")}
                  <select value={edit.member_id} onChange={(e) => {
                    const m = members.find((x) => x.id === e.target.value);
                    setEdit({ ...edit, member_id: e.target.value, km: m?.km_m != null ? String(m.km_m) : edit.km });
                  }}>
                    <option value="">—</option>
                    {members.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
                  </select>
                </label>
                <label>{tr("locKm")}
                  <input type="number" value={edit.km} onChange={(e) => setEdit({ ...edit, km: e.target.value })} />
                </label>
                <label>{tr("locLicense")}
                  <select value={edit.license} onChange={(e) => setEdit({ ...edit, license: e.target.value })}>
                    {LICENSES.map((l) => <option key={l} value={l}>{licLabel(l)}</option>)}
                  </select>
                </label>
              </div>
              <button className="btn btn-sm" onClick={saveLocation} disabled={saving}>{tr("locSave")}</button>
              {image.attribution && <p className="attr">{image.attribution}</p>}
              {image.source === "reference" && <p className="attr">{tr("referenceNote")}</p>}
            </section>
          )}

          {!det ? (
            <div className="empty">
              {imageSite === "koma_bridge"
                ? <><b>Point cloud sample</b><p>この画像は点群の実在サイト確認用です。欠損の AI 候補は 0 件です。「点群」で点をクリックすると、その点を観測した元フレームが表示されます。</p></>
                : image ? tr("pick", { n: image.detections.length }) : tr("uploadFirst")}
            </div>
          ) : (
            <>
              <h2>{image?.member_name || tr("memberUnknown")}</h2>
              <p className="sub">{image?.structure_name || tr("none")}　{fmtKm(image?.km_m ?? null)}{image?.source === "reference" ? `　（${tr("reference")}）` : ""}</p>
              <div className="score">{det.score.toFixed(3)}</div>
              <p className="note">{tr("scoreNote")}</p>
              <dl className="facts">
                <dt>{tr("defect")}</dt><dd>{DEFECTS[lang][det.label] ?? det.label}</dd>
                <dt>{tr("model")}</dt><dd>{det.model.split("/").pop()}</dd>
                <dt>{tr("evidence")}</dt><dd>{tr("evidenceOf", { f: image?.filename ?? "" })}</dd>
              </dl>
              <div className="ranks" role="group" aria-label="AA / A1 / A2 / B / C / S">
                {RANKS.map((r) => (
                  <button key={r} data-r={r} aria-pressed={rank === r}
                    title={RANK_TIP[lang][r]}
                    style={{ ["--hc" as string]: `var(--h-${r})`, ["--hci" as string]: `var(--h-${r}-i)` }}
                    onClick={() => setRank(r)}>{r}</button>
                ))}
              </div>
              <p className="note">{tr("rankNote")}</p>
              <label>{tr("comment")}
                <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder={tr("placeholder")} />
              </label>
              <div className="actions">
                <button className="btn btn-primary" onClick={confirm}>
                  {det.judgement ? tr("change") : tr("confirm")}
                </button>
                <button className="btn" onClick={nextOpen}>{tr("next")}</button>
              </div>
              {det.judgement && (
                <div className="done">
                  {tr("done", {
                    rank: det.judgement.rank,
                    time: fmtTime(det.judgement.created_at, lang),
                    actor: det.judgement.actor === "技術者" ? tr("engineer") : det.judgement.actor,
                  })}
                </div>
              )}
            </>
          )}
        </aside>

        {imageSite !== "koma_bridge" && (
        <section className="panel rail-context" aria-label={tr("railTitle")}>
          <div className="rc-head">
            <h3>{tr("railTitle")}</h3>
            <span>{tr("railNote")}</span>
          </div>
          <div className="rc-strip">
            {RAIL_PHOTOS.map((p) => (
              <button className="rc-card" key={p.src} onClick={() => setRailPhoto(p)}>
                <img src={p.src} alt={p.title} loading="lazy" />
                <span>{p.title}</span>
                <small>{p.date} · {p.license} · {p.credit}</small>
              </button>
            ))}
          </div>
        </section>
        )}
      </div>
      )}

      {tab === "sched" && <ScheduleView lang={lang} />}
      {tab === "plan" && <PlanView lang={lang} />}
      {tab === "anal" && <AnalysisView lang={lang} />}
      {tab === "prio" && (
        <PriorityView lang={lang} images={data?.images ?? []}
          onOpen={(iid, did) => { setImgId(iid); setDetId(did); setTab("inspect"); }} />
      )}

        </main>
      </div>

      {railPhoto && (
        <div className="modal" role="dialog" aria-modal="true" onClick={() => setRailPhoto(null)}>
          <figure className="lightbox" onClick={(e) => e.stopPropagation()}>
            <img src={railPhoto.src} alt={railPhoto.title} />
            <figcaption>
              <span>{railPhoto.title} / {railPhoto.date} / {railPhoto.license} / {railPhoto.credit} /</span>
              <a href={railPhoto.source} target="_blank" rel="noreferrer">Wikimedia Commons</a>
              <button className="btn btn-sm" onClick={() => setRailPhoto(null)}>{tr("prioClose")}</button>
            </figcaption>
          </figure>
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
