import { useEffect, useMemo, useRef, useState } from "react";
import {
  Map as MlMap, NavigationControl, AttributionControl, setWorkerUrl,
  type StyleSpecification, type GeoJSONSource, type RasterTileSource, type MapLayerMouseEvent,
} from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import "maplibre-gl/dist/maplibre-gl.css";
import { KM_MAX, KM_MIN, RAILS, SURVEY_POINTS, TRACK_LINE, distanceMeters, kmToLngLat, pointLngLat, square } from "../lib/geo";
import { t, type Lang } from "../lib/i18n";

type Img = {
  id: string;
  km_m: number | null;
  member_name: string | null;
  detections: { judgement: { rank: string } | null }[];
};

const GSI_PHOTO = "https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg";
const GSI_STD = "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png";

setWorkerUrl(workerUrl);

function style(photo: boolean): StyleSpecification {
  return {
    version: 8,
    sources: {
      gsi: {
        type: "raster", tiles: [photo ? GSI_PHOTO : GSI_STD], tileSize: 256, maxzoom: 18,
        attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">地理院タイル</a>',
      },
    },
    layers: [
      { id: "bg", type: "background", paint: { "background-color": "#dfe3da" } },
      { id: "gsi", type: "raster", source: "gsi" },
    ],
  };
}

export default function MapView({
  images, selectedId, onSelect, measure = false, lang, siteId,
}: { images: Img[]; selectedId: string | null; onSelect: (id: string) => void; measure?: boolean; lang: Lang; siteId?: string | null }) {
  const koma = siteId === "koma_bridge";
  const box = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [ready, setReady] = useState(false);
  const [photo, setPhoto] = useState(true);
  const [picks, setPicks] = useState<string[]>([]);
  const imagesRef = useRef(images);
  imagesRef.current = images;

  const track = useMemo(() => {
    const line = { type: "Feature" as const, properties: {}, geometry: { type: "LineString" as const, coordinates: TRACK_LINE } };
    const measured = [
      [12400, 13260], [13410, 14230], [14950, 15600],
    ].map(([a, b]) => ({
      type: "Feature" as const, properties: {},
      geometry: { type: "LineString" as const, coordinates: Array.from({ length: 24 }, (_, i) => kmToLngLat(a + ((b - a) * i) / 23)) },
    }));
    const interp = [
      [13260, 13410], [14230, 14950],
    ].map(([a, b]) => ({
      type: "Feature" as const, properties: {},
      geometry: { type: "LineString" as const, coordinates: Array.from({ length: 12 }, (_, i) => kmToLngLat(a + ((b - a) * i) / 11)) },
    }));
    return {
      line, measured: { type: "FeatureCollection" as const, features: measured },
      interp: { type: "FeatureCollection" as const, features: interp },
    };
  }, []);

  const structures = useMemo(() => {
    const piers = [13200, 13230, 13262, 13330, 13400, 13460].map((km) => ({
      type: "Feature" as const, properties: { kind: "pier", height: 12 },
      geometry: { type: "Polygon" as const, coordinates: [square(kmToLngLat(km), 7)] },
    }));
    const portals = [14200, 14980].map((km) => ({
      type: "Feature" as const, properties: { kind: "portal", height: 10 },
      geometry: { type: "Polygon" as const, coordinates: [square(kmToLngLat(km), 14)] },
    }));
    const deck = {
      type: "Feature" as const, properties: {},
      geometry: { type: "LineString" as const, coordinates: Array.from({ length: 20 }, (_, i) => kmToLngLat(13150 + (370 * i) / 19)) },
    };
    return { fills: { type: "FeatureCollection" as const, features: [...piers, ...portals] }, deck };
  }, []);

  const markers = useMemo(() => ({
    type: "FeatureCollection" as const,
    features: images.filter((i) => i.km_m != null).map((i, n) => ({
      type: "Feature" as const,
      properties: {
        id: i.id,
        rank: i.detections.find((d) => d.judgement)?.judgement?.rank ?? "",
        selected: i.id === selectedId,
      },
      geometry: { type: "Point" as const, coordinates: kmToLngLat(i.km_m! + (n % 3) * 2) },
    })),
  }), [images, selectedId]);

  useEffect(() => {
    if (!box.current || mapRef.current) return;
    const map = new MlMap({
      container: box.current,
      style: style(true),
      center: koma ? [139.33398, 35.908963] : kmToLngLat(13450),
      zoom: koma ? 14.4 : 13.9,
      pitch: koma ? 45 : 58,
      bearing: koma ? 0 : -12,
      attributionControl: false,
      maxPitch: 80,
    });
    mapRef.current = map;
    map.addControl(new NavigationControl({ visualizePitch: true }), "top-left");
    map.addControl(new AttributionControl({
      compact: true,
      customAttribution: '© OpenStreetMap contributors · 地理院タイル（国土地理院）',
    }));

    const addLayers = () => {
      if (map.getSource("track") || map.getSource("koma-site")) return;
      if (koma) {
        map.addSource("koma-site", {
          type: "geojson",
          data: { type: "Feature", properties: {}, geometry: { type: "Point", coordinates: [139.33398, 35.908963] } },
        });
        map.addLayer({
          id: "koma-site", type: "circle", source: "koma-site",
          paint: { "circle-radius": 9, "circle-color": "#d9a800", "circle-stroke-color": "#1d2328", "circle-stroke-width": 2 },
        });
        setReady(true);
        (window as unknown as { __map?: MlMap }).__map = map;
        return;
      }
      map.addSource("track", { type: "geojson", data: track.line });
      map.addSource("ballast", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: TRACK_LINE } } });
      map.addSource("railL", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: RAILS.left } } });
      map.addSource("railR", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: RAILS.right } } });
      map.addSource("measured", { type: "geojson", data: track.measured });
      map.addSource("interp", { type: "geojson", data: track.interp });
      map.addSource("structures", { type: "geojson", data: structures.fills });
      map.addSource("deck", { type: "geojson", data: structures.deck });
      map.addSource("findings", { type: "geojson", data: markers });

      map.addLayer({
        id: "ballast", type: "line", source: "ballast",
        paint: { "line-color": "#8a877d", "line-width": 10, "line-opacity": 0.9 },
      });
      map.addLayer({
        id: "railL", type: "line", source: "railL",
        paint: { "line-color": "#1d2328", "line-width": 1.8 },
      });
      map.addLayer({
        id: "railR", type: "line", source: "railR",
        paint: { "line-color": "#1d2328", "line-width": 1.8 },
      });
      map.addLayer({
        id: "interp", type: "line", source: "interp",
        paint: { "line-color": "#d9a800", "line-width": 4, "line-dasharray": [2, 1.5] },
      });
      map.addLayer({
        id: "measured", type: "line", source: "measured",
        paint: { "line-color": "#d9d5c8", "line-width": 0.8, "line-opacity": 0.6 },
      });
      map.addLayer({
        id: "deck", type: "line", source: "deck",
        paint: { "line-color": "#1f4e79", "line-width": 9, "line-opacity": 0.95 },
      });
      map.addLayer({
        id: "structures", type: "fill-extrusion", source: "structures",
        paint: {
          "fill-extrusion-color": ["match", ["get", "kind"], "portal", "#4a545d", "#1f4e79"],
          "fill-extrusion-height": ["get", "height"],
          "fill-extrusion-opacity": 0.85,
        },
      });
      try {
        map.addSource("ofm", { type: "vector", url: "https://tiles.openfreemap.org/planet" });
        map.addLayer({
          id: "buildings", type: "fill-extrusion", source: "ofm", "source-layer": "building", minzoom: 13,
          paint: {
            "fill-extrusion-color": "#c8c3b6",
            "fill-extrusion-height": ["coalesce", ["get", "render_height"], 9],
            "fill-extrusion-opacity": 0.8,
          },
        });
      } catch { /* optional context */ }
      map.addLayer({
        id: "findings", type: "circle", source: "findings",
        paint: {
          "circle-radius": 7,
          "circle-color": ["match", ["get", "rank"],
            "AA", "#7a1a10", "A1", "#c2410c", "A2", "#efa24a", "B", "#2f6ea8", "C", "#9dbedb", "S", "#c3cad0", "#1f4e79"],
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });
      map.addSource("survey", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: SURVEY_POINTS.map((p) => ({
            type: "Feature", properties: { id: p.id, label: p.label, km: p.km, elev: p.elev },
            geometry: { type: "Point", coordinates: pointLngLat(p) },
          })),
        },
      });
      map.addLayer({
        id: "survey", type: "circle", source: "survey",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": 7, "circle-color": "#f2c200",
          "circle-stroke-color": "#1d2328", "circle-stroke-width": 2,
        },
      });
      map.addSource("measure-line", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "measure-line", type: "line", source: "measure-line",
        paint: { "line-color": "#f2c200", "line-width": 2.5, "line-dasharray": [2, 1] },
      });
      map.addLayer({
        id: "selected", type: "circle", source: "findings",
        filter: ["==", ["get", "id"], selectedId ?? ""],
        paint: { "circle-radius": 12, "circle-color": "transparent", "circle-stroke-color": "#1f4e79", "circle-stroke-width": 3 },
      });
      if (selectedId) {
        const im = imagesRef.current.find((i) => i.id === selectedId);
        if (im?.km_m != null) map.flyTo({ center: kmToLngLat(im.km_m), zoom: 16, duration: 800 });
      }
      setReady(true);
      (window as unknown as { __map?: MlMap }).__map = map;
    };
    if (map.isStyleLoaded()) addLayers();
    map.on("style.load", addLayers);
    map.on("load", addLayers);

    if (!koma) map.on("click", "findings", (e: MapLayerMouseEvent) => {
      const id = e.features?.[0]?.properties?.id;
      if (typeof id === "string") {
        onSelect(id);
        const c = (e.features?.[0]?.geometry as { coordinates?: [number, number] } | undefined)?.coordinates;
        if (c) map.flyTo({ center: c, zoom: 15.4, duration: 650 });
      }
    });
    if (!koma) map.on("click", "survey", (e: MapLayerMouseEvent) => {
      const id = e.features?.[0]?.properties?.id;
      if (typeof id !== "string") return;
      setPicks((prev) => prev.length === 0 ? [id] : prev.length === 1 ? (prev[0] === id ? prev : [prev[0], id]) : [id]);
    });
    if (!koma) {
      map.on("mouseenter", "survey", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "survey", () => { map.getCanvas().style.cursor = ""; });
      map.on("mouseenter", "findings", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "findings", () => { map.getCanvas().style.cursor = ""; });
    }

    const ro = new ResizeObserver(() => map.resize());
    ro.observe(box.current);
    return () => { ro.disconnect(); map.remove(); mapRef.current = null; };
    // re-create when the area changes
  }, [koma]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const fs = map.getSource("findings") as GeoJSONSource | undefined;
    if (!fs) return;
    fs.setData(markers);
    map.setFilter("selected", ["==", ["get", "id"], selectedId ?? ""]);
  }, [markers, selectedId, ready, images]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (!map.getLayer("survey")) return;
    map.setLayoutProperty("survey", "visibility", measure ? "visible" : "none");
    map.setLayoutProperty("measure-line", "visibility", measure ? "visible" : "none");
    if (!measure) setPicks([]);
  }, [measure, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const a = SURVEY_POINTS.find((p) => p.id === picks[0]);
    const b = SURVEY_POINTS.find((p) => p.id === picks[1]);
    const data = {
      type: "FeatureCollection" as const,
      features: a && b ? [{
        type: "Feature" as const, properties: {},
        geometry: { type: "LineString" as const, coordinates: [pointLngLat(a), pointLngLat(b)] },
      }] : [],
    };
    const ms = map.getSource("measure-line") as GeoJSONSource | undefined;
    if (ms) ms.setData(data);
  }, [picks, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const src = map.getSource("gsi") as RasterTileSource | undefined;
    src?.setTiles([photo ? GSI_PHOTO : GSI_STD]);
  }, [photo, ready]);

  const a = SURVEY_POINTS.find((p) => p.id === picks[0]);
  const b = SURVEY_POINTS.find((p) => p.id === picks[1]);
  const horiz = a && b ? distanceMeters(pointLngLat(a), pointLngLat(b)) : null;
  const dh = a && b ? b.elev - a.elev : null;
  const slope = horiz != null && dh != null ? Math.hypot(horiz, dh) : null;

  return (
    <div className="map3d">
      <div ref={box} className="map3d-canvas" />
      <div className="map3d-tools">
        <button className="btn btn-sm" aria-pressed={photo} onClick={() => setPhoto(true)}>写真</button>
        <button className="btn btn-sm" aria-pressed={!photo} onClick={() => setPhoto(false)}>地図</button>
      </div>
      {measure && (
        <div className="measure-panel">
          <div className="mp-head">{t(lang, "measureHint")}</div>
          <div className="mp-points">
            <div><b>{t(lang, "measureA")}</b> {a ? `${a.label}（${(a.km / 1000).toFixed(3)}k / +${a.elev.toFixed(1)}m）` : "—"}</div>
            <div><b>{t(lang, "measureB")}</b> {b ? `${b.label}（${(b.km / 1000).toFixed(3)}k / +${b.elev.toFixed(1)}m）` : "—"}</div>
          </div>
          {horiz != null && dh != null && slope != null && (
            <dl className="mp-values">
              <dt>{t(lang, "measureHoriz")}</dt><dd>{horiz.toFixed(2)} m</dd>
              <dt>{t(lang, "measureDh")}</dt><dd>{dh >= 0 ? "+" : ""}{dh.toFixed(2)} m</dd>
              <dt>{t(lang, "measureSlope")}</dt><dd>{slope.toFixed(2)} m</dd>
            </dl>
          )}
          <div className="mp-actions">
            <button className="btn btn-sm" onClick={() => setPicks([])}>{t(lang, "measureClear")}</button>
          </div>
          <p className="mp-note">{t(lang, "measureNote")}</p>
        </div>
      )}
      <div className="map3d-hint">{koma
        ? "高麗川橋梁（八高線）・35.909N / 139.334E・実在サイト（点群は相対スケール）"
        : <>軌間1,067mm（模式）・ドラッグで回転、ホイールで拡大。点をクリック（km {Math.round(KM_MIN / 100) / 10}k–{Math.round(KM_MAX / 100) / 10}k）</>}</div>
    </div>
  );
}
