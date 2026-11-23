import { Fragment } from "react";
import { t, type Lang } from "../../lib/i18n";

const PLAN = [
  { l: "準備・機材点検", a: 70, b: 85, k: "prep" },
  { l: "F1　B-14 全景動画（3D化・位置合わせ用）", a: 85, b: 110, k: "video" },
  { l: "F2　B-14 橋脚P1〜P6 部材単位の静止画", a: 115, b: 155, k: "still" },
  { l: "F3　P3・P4 近接静止画（ひび割れ幅の推定用）", a: 160, b: 185, k: "close" },
  { l: "撤収・線路閉鎖の解除", a: 190, b: 210, k: "prep" },
];
const hm = (v: number) => `${String(Math.floor(v / 60)).padStart(2, "0")}:${String(v % 60).padStart(2, "0")}`;
const pct = (v: number) => `${(((v - 60) / 180) * 100).toFixed(2)}%`;

export function PlanView({ lang }: { lang: Lang }) {
  return (
    <section className="demo-view">
      <div className="demo-head">
        <div>
          <h2>{t(lang, "planTitle")}</h2>
          <p>{t(lang, "planSub")}</p>
        </div>
      </div>
      <div className="gantt2">
        <div />
        <div className="g2-axis">
          {[60, 90, 120, 150, 180, 210, 240].map((m) => (
            <div className="g2-tick" style={{ left: pct(m) }} key={m}>{hm(m)}</div>
          ))}
        </div>
        {PLAN.map((r) => (
          <Fragment key={r.l}>
            <div className="g2-label">{r.l}</div>
            <div className="g2-track">
              <div className="g2-window" style={{ left: pct(70), width: `calc(${pct(230)} - ${pct(70)})` }} />
              <div className={`g2-bar ${r.k}`} style={{ left: pct(r.a), width: `calc(${pct(r.b)} - ${pct(r.a)})` }}>
                {hm(r.a)}
              </div>
            </div>
          </Fragment>
        ))}
      </div>
      <p className="mini">線路閉鎖 01:10–03:50（例）。再撮影が増えた場合は別の閉鎖日に分割します。</p>
    </section>
  );
}
