import { t, type Lang } from "../../lib/i18n";

const gauss = (x: number, m: number, sd: number) => Math.exp(-((x - m) ** 2) / (2 * sd * sd));
const settle = (s: number) => -34 * gauss(s, 12885, 45) - 22 * gauss(s, 13532, 20) - 9 * gauss(s, 15120, 32)
  + 2.2 * Math.sin(s * 0.01) + 1.4 * Math.sin(s * 0.031);
const track = (s: number) => 9 * gauss(s, 12885, 24) + 2.5 * Math.sin(s * 0.02);

function Chart({ mode }: { mode: "settle" | "track" }) {
  const from = 12400, to = 15600, W = 820, H = 230, L = 46, R = 12, T = 18, B = 26;
  const min = mode === "settle" ? -40 : -12, max = mode === "settle" ? 15 : 12;
  const X = (s: number) => L + ((s - from) / (to - from)) * (W - L - R);
  const Y = (v: number) => T + ((max - v) / (max - min)) * (H - T - B);
  const f = mode === "settle" ? settle : track;
  const pts = Array.from({ length: 161 }, (_, i) => from + ((to - from) * i) / 160);
  const d = pts.map((s, i) => `${i ? "L" : "M"}${X(s).toFixed(1)} ${Y(Math.max(min, Math.min(max, f(s)))).toFixed(1)}`).join(" ");
  return (
    <svg className="demo-chart" viewBox={`0 0 ${W} ${H}`} role="img">
      <rect x={L} y={Y(15)} width={W - L - R} height={Y(-15) - Y(15)} fill="var(--surface2)" />
      {[min, (min + max) / 2, max].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={Y(v)} y2={Y(v)} stroke="var(--line)" />
          <text x={L - 6} y={Y(v) + 4} textAnchor="end" fontSize="11" fill="var(--ink3)">{Math.round(v)}</text>
        </g>
      ))}
      {mode === "settle" && (
        <line x1={L} x2={W - R} y1={Y(-20)} y2={Y(-20)} stroke="var(--h-A1)" strokeDasharray="6 4" />
      )}
      <path d={d} fill="none" stroke="var(--accent)" strokeWidth="2.4" />
      {[12885, 13532, 15120].map((s) => <circle key={s} cx={X(s)} cy={Y(Math.max(min, Math.min(max, f(s))))} r="3.4" fill="var(--h-A2)" />)}
      {[12500, 13000, 13500, 14000, 14500, 15000, 15500].map((s) => (
        <text key={s} x={X(s)} y={H - 6} textAnchor="middle" fontSize="11" fill="var(--ink2)">{(s / 1000).toFixed(1)}k</text>
      ))}
      <text x={L - 6} y={11} textAnchor="end" fontSize="10" fill="var(--ink3)">mm</text>
    </svg>
  );
}

const FINDINGS = [
  { id: "D1", km: "12k820–12k950", title: "盛土のり肩の沈下", val: "最大 約−34mm", conf: "中" },
  { id: "D2", km: "13k500–13k565", title: "橋台背面の沈下", val: "約−22mm", conf: "中" },
  { id: "D3", km: "15k080–15k160", title: "側溝付近の沈下", val: "約−9mm", conf: "低" },
  { id: "D4", km: "12k860–12k910", title: "通りの変化", val: "約+9mm", conf: "低" },
];

export function AnalysisView({ lang }: { lang: Lang }) {
  return (
    <section className="demo-view">
      <div className="demo-head">
        <div>
          <h2>{t(lang, "analTitle")}</h2>
          <p>{t(lang, "analSub")}</p>
        </div>
      </div>
      <div className="fig-legend" aria-label="凡例">
        <span><i className="lg-line" />推定値（ドローン点群）</span>
        <span><i className="lg-band" />誤差の目安 ±15mm</span>
        <span><i className="lg-thr" />要確認しきい値 −20mm</span>
      </div>
      <div className="anal-grid">
        <div className="demo-panel">
          <h3>路盤・地盤の沈下（推定）</h3>
          <Chart mode="settle" />
          <p className="mini">網掛けは誤差の目安 ±15mm。mm単位の判定には使わず、現地測量・検測車で確認する箇所の絞り込みに使います。</p>
        </div>
        <div className="demo-panel">
          <h3>軌道の変形（通り）</h3>
          <Chart mode="track" />
          <p className="mini">点群から抽出したレール位置の推定値です。欠測・補間区間は対象外です。</p>
        </div>
      </div>
      <div className="demo-panel">
        <h3>検出された変位</h3>
        <table className="demo-table">
          <thead><tr><th>ID</th><th>キロ程</th><th>内容</th><th>推定値</th><th>信頼度</th></tr></thead>
          <tbody>{FINDINGS.map((f) => (
            <tr key={f.id}><td>{f.id}</td><td>{f.km}</td><td>{f.title}</td><td>{f.val}</td><td>{f.conf}</td></tr>
          ))}</tbody>
        </table>
      </div>
    </section>
  );
}
