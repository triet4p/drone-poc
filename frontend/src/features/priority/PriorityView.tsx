import { DEFECTS, t, type Lang } from "../../lib/i18n";
import { km, rankColor, type PImg } from "../shared";

export function PriorityView({ lang, images, onOpen }: { lang: Lang; images: PImg[]; onOpen: (imgId: string, detId: number) => void }) {
  const rows = images.flatMap((im) => im.detections.filter((d) => d.judgement).map((d) => ({ im, d })))
    .sort((a, b) => "AA A1 A2 B C S".split(" ").indexOf(a.d.judgement!.rank) - "AA A1 A2 B C S".split(" ").indexOf(b.d.judgement!.rank));
  return (
    <section className="demo-view">
      <div className="demo-head">
        <div>
          <h2>{t(lang, "prioTitle2")}</h2>
          <p>確定した判定のみ。行をクリックすると 3D/写真で開きます。</p>
        </div>
      </div>
      {rows.length ? (
        <table className="demo-table">
          <thead><tr><th>#</th><th>キロ程</th><th>構造物・部材</th><th>変状</th><th>判定</th><th>所見</th></tr></thead>
          <tbody>{rows.map(({ im, d }, i) => (
            <tr key={d.id} onClick={() => onOpen(im.id, d.id)}>
              <td>{i + 1}</td>
              <td>{km(im.km_m)}</td>
              <td>{im.structure_name} {im.member_name}</td>
              <td>{DEFECTS[lang][d.label] ?? d.label}</td>
              <td><b style={{ color: rankColor[d.judgement!.rank] }}>{d.judgement!.rank}</b></td>
              <td>{d.judgement!.comment}</td>
            </tr>
          ))}</tbody>
        </table>
      ) : <p className="empty">まだ確定した判定がありません。</p>}
    </section>
  );
}
