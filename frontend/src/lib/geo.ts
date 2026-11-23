export type LngLat = [number, number];

// Demo alignment traced from the real 東海道本線 around 根府川 (OSM), simplified.
// km 12k400 is anchored at the south end, 15k600 at the north end.
const TRACK: LngLat[] = [
  [139.134413, 35.183192], [139.134535, 35.183389], [139.135438, 35.184877], [139.135739, 35.185415], [139.135888, 35.185766], [139.135937, 35.185919],
  [139.135966, 35.186040], [139.136024, 35.186277], [139.136089, 35.186732], [139.136113, 35.187315], [139.136209, 35.190241], [139.136210, 35.190311],
  [139.136249, 35.191311], [139.136260, 35.191591], [139.136297, 35.192524], [139.136310, 35.192874], [139.136344, 35.193736], [139.136353, 35.194162],
  [139.136339, 35.194475], [139.136300, 35.194778], [139.136225, 35.195117], [139.136133, 35.195435], [139.135797, 35.196494], [139.135715, 35.196835],
  [139.135683, 35.197249], [139.135706, 35.197683], [139.135757, 35.198008], [139.135967, 35.198591], [139.135993, 35.198645], [139.136038, 35.198734],
  [139.136211, 35.199037], [139.136601, 35.199614], [139.136993, 35.200202], [139.137245, 35.200584], [139.137690, 35.201243], [139.137823, 35.201444],
  [139.137897, 35.201552], [139.138267, 35.202096], [139.138669, 35.202686], [139.138870, 35.202993], [139.139085, 35.203315], [139.139303, 35.203637],
  [139.139752, 35.204347], [139.140028, 35.204793], [139.140177, 35.205052], [139.140316, 35.205319], [139.140422, 35.205578], [139.140518, 35.205861],
  [139.140592, 35.206151], [139.140645, 35.206433], [139.140686, 35.206731], [139.140759, 35.207334], [139.140816, 35.207781], [139.140851, 35.208120],
  [139.140861, 35.208323], [139.140847, 35.208579], [139.140832, 35.208768], [139.140810, 35.208958], [139.140745, 35.209241], [139.140707, 35.209391],
  [139.140603, 35.209670], [139.140445, 35.209983], [139.140306, 35.210193], [139.140198, 35.210325], [139.140109, 35.210434], [139.139616, 35.210980],
  [139.139190, 35.211422], [139.138999, 35.211647], [139.138789, 35.211990], [139.138611, 35.212430], [139.138560, 35.212569], [139.138463, 35.212987],
  [139.138431, 35.213416], [139.138439, 35.213687], [139.138476, 35.213982], [139.138546, 35.214305], [139.138640, 35.214576], [139.138756, 35.214853],
  [139.138920, 35.215142], [139.139092, 35.215396], [139.139222, 35.215569], [139.139245, 35.215593], [139.139368, 35.215720], [139.139552, 35.215891],
  [139.139788, 35.216115], [139.140107, 35.216360], [139.140379, 35.216565], [139.140647, 35.216780], [139.140814, 35.216923], [139.140968, 35.217075],
  [139.141024, 35.217137], [139.141056, 35.217174], [139.141217, 35.217360], [139.141387, 35.217604], [139.141515, 35.217817], [139.141623, 35.218032],
  [139.141705, 35.218234], [139.141774, 35.218449], [139.141833, 35.218668], [139.141875, 35.218896], [139.141896, 35.219107], [139.141905, 35.219327],
  [139.141897, 35.219521], [139.141871, 35.219752], [139.141823, 35.219990], [139.141777, 35.220193], [139.141724, 35.220363], [139.141587, 35.220792],
  [139.141284, 35.221738], [139.140810, 35.223452], [139.140601, 35.224033], [139.140570, 35.224333], [139.140568, 35.224521], [139.140569, 35.224771],
  [139.140589, 35.224960], [139.140610, 35.225113], [139.140682, 35.225471], [139.140774, 35.225818], [139.140921, 35.226149], [139.141074, 35.226469],
  [139.141144, 35.226596],
];

const R = 6371000;
const rad = (d: number) => (d * Math.PI) / 180;
const dist = (a: LngLat, b: LngLat) => {
  const dLat = rad(b[1] - a[1]), dLon = rad(b[0] - a[0]);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a[1])) * Math.cos(rad(b[1])) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
};

const CUM: number[] = [0];
for (let i = 1; i < TRACK.length; i++) CUM.push(CUM[i - 1] + dist(TRACK[i - 1], TRACK[i]));
export const TRACK_LENGTH = CUM[CUM.length - 1];
export const KM_MIN = 12400;
export const KM_MAX = 15600;

/** Chainage (m) -> lon/lat along the demo alignment. Fictional stationing, real geometry. */
export function kmToLngLat(km: number): LngLat {
  const t = Math.min(1, Math.max(0, (km - KM_MIN) / (KM_MAX - KM_MIN)));
  const target = t * TRACK_LENGTH;
  let i = 1;
  while (i < CUM.length - 1 && CUM[i] < target) i++;
  const seg = CUM[i] - CUM[i - 1] || 1;
  const u = (target - CUM[i - 1]) / seg;
  return [TRACK[i - 1][0] + (TRACK[i][0] - TRACK[i - 1][0]) * u,
          TRACK[i - 1][1] + (TRACK[i][1] - TRACK[i - 1][1]) * u];
}

/** Small local offset in metres: d = lateral (right positive), up is ignored. */
export function offset(p: LngLat, dLatM: number, dLonM: number): LngLat {
  return [p[0] + dLonM / (111320 * Math.cos(rad(p[1]))), p[1] + dLatM / 111320];
}

export function square(c: LngLat, metres: number): LngLat[] {
  const h = metres / 2;
  return [
    offset(c, -h, -h), offset(c, -h, h), offset(c, h, h), offset(c, h, -h), offset(c, -h, -h),
  ];
}

export const TRACK_LINE: LngLat[] = Array.from({ length: 80 }, (_, i) =>
  kmToLngLat(KM_MIN + ((KM_MAX - KM_MIN) * i) / 79)
);

/** Two rails at ±half gauge, offset from the alignment. */
export function railCurves(halfGaugeM = 0.5335): { left: LngLat[]; right: LngLat[] } {
  const left: LngLat[] = [], right: LngLat[] = [];
  for (let i = 0; i < TRACK_LINE.length; i++) {
    const a = TRACK_LINE[Math.max(0, i - 1)];
    const b = TRACK_LINE[Math.min(TRACK_LINE.length - 1, i + 1)];
    const p = TRACK_LINE[i];
    const dx = (b[0] - a[0]) * 111320 * Math.cos(rad(p[1]));
    const dy = (b[1] - a[1]) * 111320;
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len, ny = dx / len;
    left.push(offset(p, ny * halfGaugeM, nx * halfGaugeM));
    right.push(offset(p, -ny * halfGaugeM, -nx * halfGaugeM));
  }
  return { left, right };
}

export const RAILS = railCurves();

export type SurveyPoint = {
  id: string; label: string; km: number; elev: number; kind: "pier" | "abutment" | "portal" | "deck";
};

export const SURVEY_POINTS: SurveyPoint[] = [
  { id: "A1", label: "A1 橋台", km: 13168, elev: 8, kind: "abutment" },
  { id: "P1", label: "P1 橋脚", km: 13200, elev: 0, kind: "pier" },
  { id: "P2", label: "P2 橋脚", km: 13230, elev: 0, kind: "pier" },
  { id: "P3", label: "P3 橋脚", km: 13262, elev: 0, kind: "pier" },
  { id: "P4", label: "P4 橋脚", km: 13330, elev: 0, kind: "pier" },
  { id: "P5", label: "P5 橋脚", km: 13400, elev: 0, kind: "pier" },
  { id: "P6", label: "P6 橋脚", km: 13460, elev: 0, kind: "pier" },
  { id: "A2", label: "A2 橋台", km: 13505, elev: 8, kind: "abutment" },
  { id: "D1", label: "桁端 起点", km: 13150, elev: 8, kind: "deck" },
  { id: "D2", label: "桁端 終点", km: 13520, elev: 8, kind: "deck" },
  { id: "T1", label: "T-07 起点坑口", km: 14205, elev: 8, kind: "portal" },
  { id: "T2", label: "T-07 終点坑口", km: 14975, elev: 8, kind: "portal" },
];

export function pointLngLat(p: SurveyPoint): LngLat {
  return kmToLngLat(p.km);
}

/** Geodesic distance in metres between two lon/lat points. */
export function distanceMeters(a: LngLat, b: LngLat): number {
  return dist(a, b);
}
