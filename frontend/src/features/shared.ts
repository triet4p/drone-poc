type PDet = { id: number; label: string; score: number; judgement: { rank: string; comment: string } | null };
type PImg = { id: string; filename: string; km_m: number | null; member_name: string | null; structure_name: string | null; detections: PDet[] };

export const km = (v: number | null) => (v == null ? "—" : `${(v / 1000).toFixed(3)}k`);
export const rankColor: Record<string, string> = { AA: "#7a1a10", A1: "#c2410c", A2: "#efa24a", B: "#2f6ea8", C: "#9dbedb", S: "#c3cad0" };
export type { PDet, PImg };
