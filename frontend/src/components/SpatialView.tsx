import { t, type Lang } from "../lib/i18n";
import MapView from "./MapView";
import PointCloudView from "./PointCloudView";

type Img = {
  id: string;
  km_m: number | null;
  member_name: string | null;
  detections: { judgement: { rank: string } | null }[];
};

export type SpatialLayer = "map" | "cloud";

/** One 3D workspace: map and point cloud are layers, not separate tabs. */
export default function SpatialView({
  layer, onLayerChange, images, selectedId, onSelect, lang, siteId,
}: {
  layer: SpatialLayer;
  onLayerChange: (layer: SpatialLayer) => void;
  images: Img[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  lang: Lang;
  siteId: string | null;
}) {
  return (
    <div className="spatial-view">
      <div className="spatial-switch" role="group" aria-label={t(lang, "pcLayers")}>
        <span>{t(lang, "pcLayers")}</span>
        <button aria-pressed={layer === "map"} onClick={() => onLayerChange("map")}>{t(lang, "spatial3d")}</button>
        <button aria-pressed={layer === "cloud"} onClick={() => onLayerChange("cloud")}>{t(lang, "pointCloud")}</button>
      </div>
      {layer === "map" ? (
        <MapView images={images} selectedId={selectedId} lang={lang} siteId={siteId}
          onSelect={onSelect} />
      ) : (
        <PointCloudView lang={lang} siteId={siteId} />
      )}
    </div>
  );
}
