import { Fragment } from "react";
import { t, type Lang } from "../../lib/i18n";

const DAYS = [
  { d: "11/30", w: "月", wx: "晴れ", wind: 3, closure: true },
  { d: "12/1", w: "火", wx: "くもり", wind: 4, closure: true },
  { d: "12/2", w: "水", wx: "雨", wind: 6, closure: true },
  { d: "12/3", w: "木", wx: "晴れ", wind: 8, closure: true },
  { d: "12/4", w: "金", wx: "くもり", wind: 5.5, closure: true },
  { d: "12/5", w: "土", wx: "晴れ", wind: 2, closure: false },
  { d: "12/6", w: "日", wx: "晴れ", wind: 3, closure: true },
];
type SchedRow = { name: string; km: string; flights: Record<number, string[]> };
const ROWS: SchedRow[] = [
  { name: "盛土・B-14 橋梁", km: "12k400–13k520", flights: { 0: ["F1 全景動画", "F2 部材静止画"], 1: ["F3 近接静止画"] } },
  { name: "切土", km: "13k520–14k200", flights: {} },
  { name: "T-07 トンネル坑口", km: "14k200–14k980", flights: {} },
  { name: "盛土", km: "14k980–15k600", flights: { 6: ["F6 全景動画"] } },
];

const status = (d: typeof DAYS[number]) => {
  if (!d.closure) return { text: "線路閉鎖なし", cls: "ng" };
  if (d.wx === "雨") return { text: "降雨", cls: "ng" };
  if (d.wind >= 7) return { text: `風速${d.wind}m/s`, cls: "ng" };
  if (d.wind >= 5) return { text: "注意", cls: "warn" };
  return { text: "飛行可", cls: "ok" };
};

export function ScheduleView({ lang }: { lang: Lang }) {
  return (
    <section className="demo-view">
      <div className="demo-head">
        <div>
          <h2>{t(lang, "schedTitle")}</h2>
          <p>{t(lang, "schedSub")}</p>
        </div>
      </div>
      <div className="sched-grid">
        <div />
        {DAYS.map((d) => {
          const st = status(d);
          return (
            <div className="sched-h" key={d.d}>
              <b>{d.d}</b>（{d.w}）<br />{d.wx} {d.wind}m/s<br />
              <span className={`st ${st.cls}`}>{st.text}</span>
            </div>
          );
        })}
        {ROWS.map((r) => (
          <Fragment key={r.name}>
            <div className="sched-row"><b>{r.name}</b><span>{r.km}</span></div>
            {DAYS.map((_, i) => (
              <div className={`sched-cell ${status(DAYS[i]).cls === "ng" ? "off" : ""}`} key={i}>
                {(r.flights[i] ?? []).map((f: string) => <span className="fchip" key={f}>{f}</span>)}
              </div>
            ))}
          </Fragment>
        ))}
      </div>
      <p className="mini">条件例：降雨・風速7m/s以上は飛行しない。1晩120分まで。実際の運用基準に合わせて設定します。</p>
    </section>
  );
}
