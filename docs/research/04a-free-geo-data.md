# Bản đồ 3D đường sắt Nhật Bản từ dữ liệu/API miễn phí (無料・オープンデータ) — Free geo-data landscape

> Ngôn ngữ: tiếng Việt; thuật ngữ gốc tiếng Nhật trong ngoặc đơn. Mọi khẳng định về giấy phép, hạn mức, URL đều kèm link nguồn. Số liệu không kiểm chứng trực tiếp được đánh dấu `[推定]`.

## 1) Phạm vi (範囲・スコープ)

**Mục tiêu:** chọn stack miễn phí/mở (オープンライセンス) để dựng bản đồ bối cảnh 3D (3Dコンテキストマップ) cho demo kiểm tra đường sắt Nhật (hành lang km 12k400–15k600, cầu B-14 P1–P6/G1–G5/A1–A2, hầm T-07 — toàn bộ geometry demo là dữ liệu giả lập nội bộ).

**Ràng buộc:**

- Ngân sách zero (ゼロ予算); chỉ dùng giấy phép mở (ODbL/CC BY/CC0/条件付きでGSI・PLATEAU) hoặc free tier có hạn mức công khai.
- Bao phủ Nhật Bản (日本カバレッジ) quan trọng hơn bao phủ toàn cầu.
- Chạy trong React (React統合); **không nhúng token thương mại (APIキー/トークン) vào client**.
- Sản phẩm cuối hướng tới on-premise/air-gap (オンプレミス・オフライン稼働); demo 26/11 có thể chấp nhận internet nhưng phải ghi rõ chỗ nào bắt buộc online.
**Ngoài phạm vi:** pipeline kiểm tra hiện tại (ảnh drone, Grounding DINO, DOCX). Báo cáo này không phải tư vấn pháp lý (法的助言ではない); bảng license cần pháp chế xác nhận trước khi dùng thương mại. "API Map của Meta" → trả lời ở mục 2.7: **không tồn tại**; Meta chỉ có ảnh đường phố Mapillary.

---

## 2) Findings (調査結果)

### 2.1 Nền bản đồ tile 2D (ベースマップ・タイル)

| Nguồn | URL mẫu | Token/key | Hạn mức công khai | Ghi chú dùng cho demo |
|---|---|---|---|---|
| OSM standard tiles (OSM本家タイル) | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | Không | **Không có quota số học công bố**; chính sách là "dùng hợp lý": User-Agent riêng, tôn trọng cache header (tối thiểu cache 7 ngày), cấm bulk download/offline archive, OSM có thể chặn traffic gây hại ([Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/), [bản dự phòng](https://openstreetmap.github.io/owg-website/policies/tiles/)). Từ 30/07/2025 OSM siết enforcement với app không định danh và tách cache CDN ([thông báo](https://community.openstreetmap.org/t/technical-updates-to-the-tile-openstreetmap-org-service-openstreetmap-org-standard-layer/133421)) | Chỉ dùng dev/test; **không** làm tile nền chính cho demo trước khách (rủi ro bị chặn, không SLA) |
| OpenFreeMap (ベクタータイル無料配信) | `https://tiles.openfreemap.org/styles/liberty` (+ positron/bright/dark/fiord/3D) | Không, không cần tài khoản | Public instance **không công bố quota tháng**; giới hạn duy nhất được nêu là cho offline download: ≤3.000 tiles hoặc 50 MB, ≤4 kết nối song song, User-Agent riêng; **không SLA, có thể dừng bất cứ lúc nào** ([openfreemap.org](https://openfreemap.org/)) | Ứng viên nền 2D tốt cho demo có mạng; style 3D sẵn; custom style phải tự host JSON (dùng Maputnik). Không có geocoding/routing/elevation |
| Protomaps hosted API (ホスト型タイルAPI) | `api.protomaps.com` | Key | Phi thương mại miễn phí với **soft limit ~1 triệu tile requests/tháng**; dùng thương mại yêu cầu GitHub Sponsor (không phải pay-as-you-go) ([protomaps.com/about](https://protomaps.com/about), [blog free-tier](https://protomaps.com/blog/free-tier-maps)) | Demo nội bộ OK; demo thương mại thì chuyển self-host |
| PMTiles tự host (セルフホスト単一ファイル) | File `.pmtiles` trên S3/R2/tĩnh | Không | **Không phí, không giới hạn của Protomaps**; chỉ trả tiền storage/băng thông cho nhà cung cấp ([PMTiles GitHub](https://github.com/protomaps/pmtiles), [cost calculator](https://docs.protomaps.com/deploy/cost)) | **Con đường offline/air-gap duy nhất cho vector tiles**; ví dụ chi phí minh họa 10M requests: ~$11.45/tháng trên R2+Workers vs ~$119.56 trên S3+CloudFront ([docs](https://docs.protomaps.com/deploy/cost)) — đây là ước tính của hãng, không phải báo giá |
| MapTiler Cloud Free (フリープラン) | `api.maptiler.com` + key | **Bắt buộc key** | **100.000 requests/tháng**, 5.000 map sessions, 1 key; hết quota **dừng đến hết tháng**; vector tile = 1 request, raster 512px = 4 ([pricing](https://www.maptiler.com/cloud/pricing/), [api-key docs](https://docs.maptiler.com/guides/developer/credentials/api-key/)) | Đủ cho demo 1 buổi (~25.000 views [推定]); free plan cho testing/phi thương mại |
| Mapbox Free | `api.mapbox.com` + token | **Bắt buộc token** | Web **50.000 map loads/tháng**; mobile **25.000 MAU/tháng**; quá thì trả theo nấc ([pricing](https://www.mapbox.com/pricing)) | Loại (token công khai + terms thương mại); nêu để phân biệt với "API của Meta" (mục 2.7) |
| Stadia Maps Free | `tiles.stadiamaps.com` + key | **Bắt buộc key** | **200.000 credits/tháng, free = phi thương mại**; tile thường = 1 credit, satellite = 4, geocoding/routing = 20/request; hết thì 429 đến kỳ sau ([pricing](https://stadiamaps.com/pricing), [limits](https://docs.stadiamaps.com/limits), [FAQ](https://stadiamaps.com/faqs/)) | Loại cho demo thương mại; dự phòng dev |
| GSI 地理院タイル (国土地理院) | 標準地図 `https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png`; 淡色地図 `.../xyz/pale/...`; 全国最新写真 `.../xyz/seamlessphoto/{z}/{x}/{y}.jpg` (chuẩn z5–18, ảnh z14–18) ([仕様](https://maps.gsi.go.jp/development/siyou.html), [一覧](https://maps.gsi.go.jp/development/ichiran.html)) | Không | **Không quota**; realtime miễn thủ tục nếu ghi nguồn; **tái phân phối/cache thành dataset độc lập có thể cần thủ tục 測量法**; 写真 theo コンテンツ利用規約 ([一覧](https://maps.gsi.go.jp/development/ichiran.html), [規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)) | **Nền chính demo**: std + seamlessphoto; attribution mẫu mục 2.8 |

**Kết luận nền 2D:** demo 26/11 (có mạng) → GSI std/seamlessphoto làm nền chính + OpenFreeMap dự phòng; cấm dùng OSM本家 tiles cho show. Air-gap (オフライン) → chỉ còn PMTiles tự host + tile GSI đã xin phép/cache đúng quy định.

### 2.2 Engine 3D miễn phí (無料3Dエンジン) — làm rõ "Meta có gì"

| Engine | License (ライブラリ) | 3D cần dữ liệu gì | Kết luận |
|---|---|---|---|
| CesiumJS | **Apache-2.0**, dùng thương mại tự do; ion content/service là thứ riêng ([README](https://github.com/CesiumGS/cesium/blob/main/README.md?plain=1), [LICENSE](https://github.com/CesiumGS/cesium/blob/main/LICENSE.md)) | Cần nguồn terrain + imagery + 3D Tiles do mình cấp | **Chọn cho demo**: true-3D globe, nuốt trực tiếp PLATEAU 3D Tiles + corridor point-cloud demo |
| MapLibre GL JS | **BSD-3-Clause**, tự host được; có 3D terrain nhưng phải tự cấp DEM ([README](https://github.com/maplibre/maplibre-gl-js/blob/main/README.md), [ví dụ terrain](https://maplibre.org/maplibre-gl-js/docs/examples/3d-terrain/)) | DEM tiles (Terrarium/GSI) + vector/raster style | Phương án B nếu chỉ cần "2.5D" nhẹ; không mạnh bằng Cesium cho point cloud/hầm-cầu |
| deck.gl | **MIT**; là framework trực quan hóa, `TerrainLayer` cũng cần nguồn độ cao ngoài ([LICENSE](https://github.com/visgl/deck.gl/blob/master/LICENSE)) | Elevation source ngoài | Chỉ dùng làm lớp phủ (縦断 profile, heatmap biến dạng), không làm engine chính |

**Meta và bản đồ 3D:** Mapillary là **sản phẩm của Meta (Meta product), được Meta mua lại năm 2020** ([help center](https://help.mapillary.com/hc/en-us/articles/115001770089-Meta-s-open-mapping-mission)). Meta **không cung cấp tile/map API hay 3D engine miễn phí** nào — chi tiết mục 2.7. Video flyover "NiMap" trên Facebook là sản phẩm dựng sẵn, không phải API mở.

### 2.3 Nhà 3D (3D建物モデル)

**Meta và bản đồ 3D:** Mapillary là **sản phẩm của Meta, được Meta mua lại năm 2020** ([help center](https://help.mapillary.com/hc/en-us/articles/115001770089-Meta-s-open-mapping-mission)). Meta **không cung cấp tile/map API hay engine 3D miễn phí** nào — chi tiết mục 2.7.

**PLATEAU (国交省3D都市モデル) là nguồn chính:**

- Bao phủ (カバレッジ): **329 thành phố (3/2026)** theo MLIT ([press release](https://www.mlit.go.jp/report/press/toshi03_hh_000223.html)); giữa 2025 là 236+ đô thị có building dataset ([SoTM 2025](https://2025.stateofthemap.org/sessions/N89YSU/)) — từng thành phố khác nhau về lớp dữ liệu/năm đo.
- Định dạng (形式): gốc **CityGML**; tùy thành phố có thêm **3D Tiles, MVT, OBJ, FBX, GeoJSON, GeoTIFF** ([học liệu MLIT](https://www.mlit.go.jp/plateau/learning/tpc03-1/)); tải qua [portal open-data](https://www.mlit.go.jp/plateau/open-data/) → trang dataset G-Spatial Information Center từng thành phố.
- Streaming (配信): ví dụ toàn quốc LOD1 `https://api.plateauview.mlit.go.jp/datacatalog/3dtiles/all-bldg-lod1-latest/tileset.json` (`latest` = năm mới nhất theo khu vực) nhưng **thử nghiệm (experimental), không đảm bảo uptime** ([docs 配信サービス](https://docs.plateauview.mlit.go.jp/datasets/3d-tiles/)).
- License (ライセンス): **không đồng nhất** — từng dataset thuộc **CC BY 4.0 / 国公共データ利用規約 / ODC-BY / ODbL**; thương mại nhìn chung được phép ([start guide](https://www.mlit.go.jp/plateau/start-guide/)). Dung lượng LOD1 mỗi thành phố [推定] **vài chục MB–hàng GB**; corridor 3,2 km cắt bbox [推定] **vài–vài chục MB**.

**Cesium OSM Buildings:** dữ liệu gốc OSM theo **ODbL**, Cesium yêu cầu attribution `© OpenStreetMap contributors` (SDK tự chèn) ([third-party terms](https://cesium.com/legal/third-party-terms/), [trang content](https://cesium.com/platform/cesium-ion/content/cesium-osm-buildings/)). Dùng được cho demo nhưng chất lượng chiều cao ở Nhật = chất lượng OSM (thưa) → thua PLATEAU trong vùng có PLATEAU. Không có "GSI 建物モデル" độc lập nào thay thế được PLATEAU [推定 — không tìm thấy sản phẩm tương đương trong 一覧 GSI].

### 2.4 Địa hình/DEM (地形・標高タイル)

| Nguồn | Độ phân giải ở Nhật | Tile URL / lấy dữ liệu | License + attribution phải hiện |
|---|---|---|---|
| GSI DEM (標高タイル) — **chọn cho demo** | DEM5A/5B/5C (5 m) + DEM10B (10 m) ([一覧](https://maps.gsi.go.jp/development/)) | `https://cyberjapandata.gsi.go.jp/xyz/dem_png/{z}/{x}/{y}.png` (= DEM10B dạng PNG mã hóa độ cao; còn `dem5a_png/dem5b_png/dem5c_png`) — giải mã pixel theo [仕様 GSI](https://maps.gsi.go.jp/development/) | Terms GSI ([規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)); realtime + ghi nguồn thì miễn thủ tục; tái phân phối cần kiểm tra 測量法 |
| AWS Terrain Tiles / Terrarium (Mapzen・Joerd) | Ghép nhiều nguồn toàn cầu (~30 m [推定]) | `s3://elevation-tiles-prod/terrarium/{z}/{x}/{y}.png` qua AWS Open Data ([marketplace](https://aws.amazon.com/marketplace/pp/prodview-x7vtai3hasf26)) | **Provenance hỗn hợp** — phần mềm Joerd MIT nhưng dữ liệu thì theo từng nguồn (ArcticDEM, EU-DEM, USGS, NOAA ETOPO1…), phải ghi credit theo [attribution Joerd](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) |
**Self-host terrain:** GSI dem_png decode → GeoTIFF → quantized-mesh ([推定] ~1–2 giờ cho bbox corridor, **< 50 MB**). Bắt buộc internet: streaming PLATEAU/AWS; tự host được: GSI DEM đã decode, Copernicus/Terrarium đã tải.


### 2.5 Ảnh (画像・オルソ写真・街頭画像)

| Nguồn | Coverage | License dùng demo thương mại | Ghi chú |
|---|---|---|---|
| GSI 全国最新写真 (シームレス空中写真) — **chọn cho demo** | Toàn quốc, z14–18 ([一覧](https://maps.gsi.go.jp/development/ichiran.html)) | Thuộc nhóm "基本測量成果以外" → theo コンテンツ利用規約 + lưu ý từng nguồn ảnh gốc ([同](https://maps.gsi.go.jp/development/ichiran.html)) | Làm imagery Cesium thay satellite thương mại; nông thôn có thể cũ/mờ — chấp nhận cho demo |
| Sentinel-2 (光学衛星) | Toàn cầu, 10 m/band nhìn thấy ([Sentinel-2](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2)) | **Miễn phí cả thương mại**; ghi `Contains modified Copernicus Sentinel data [year]` ([terms](https://dataspace.copernicus.eu/terms-and-conditions), [legal notice](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice)) | 10 m quá thô cho corridor 3,2 km — chỉ làm nền dự phòng/minh họa biến động lớn |
| Mapillary (Meta) street-level (ストリート画像) | Phụ thuộc ảnh cộng đồng dọc tuyến; kiểm tra thực tế theo tọa độ | Ảnh **CC BY-SA** — thương mại được phép nhưng **phải ghi công nhiếp ảnh gia + link ảnh + license, tác phẩm phái sinh chia sẻ cùng điều kiện ShareAlike** ([help](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data), [CC deed](https://creativecommons.org/licenses/by-sa/4.0/deed.en)); đồng thời tuân thủ [Terms/Commercial Terms](https://help.mapillary.com/hc/en-us/articles/4407521157138-Downloading-map-data-via-the-Mapillary-web-app) | API cần access token (server-side, không nhúng client); hạn mức báo cáo [推定, chưa kiểm chứng do docs yêu cầu login]: Entity ~60.000 req/phút, Search ~10.000/phút, Tiles ~50.000/ngày ([developer docs](https://www.mapillary.com/developer/api-documentation)) — xác nhận lại trước khi dùng |

### 2.6 Vector / routing / geocoding (ベクター・経路探索・ジオコーディング)

| Dịch vụ | Chính sách dùng chùa | Self-host | Dùng cho demo |
|---|---|---|---|
| Overpass API | Public instance: guideline **~10.000 requests/ngày, < 1 GB/ngày/user**, throttle theo thời gian/chạy bộ nhớ; 429 thì backoff; app production phải tự host ([commons](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html)) | Khuyến nghị instance riêng nếu query lặp lại | Query 1 lần lấy `railway=rail` + cầu/hầm corridor (mẫu dưới); cache GeoJSON vào repo, **không gọi live trong demo** |
| Nominatim | Public `nominatim.openstreetmap.org`: **1 req/s**, cần User-Agent/Referer, cấm autocomplete client-side và query hệ thống ([policy](https://operations.osmfoundation.org/policies/nominatim/)) | Planet import cần [推定] **128 GB RAM + 1 TB disk + ~2,5 ngày** ([install docs](https://nominatim.org/release-docs/develop/admin/Installation/)); extract vùng Nhật nhẹ hơn nhiều | Demo không cần geocoding — **loại khỏi MVP** |
| OSRM / Valhalla | Không có public production miễn phí đáng tin | **OSRM: BSD-2-Clause** ([GitHub](https://github.com/Project-OSRM/osrm-backend)); **Valhalla: MIT** ([GitHub](https://github.com/valhalla/valhalla)) — OSM data vẫn ODbL + attribution | Routing không cần cho demo kiểm tra cầu-hầm — **loại khỏi MVP**, ghi vào backlog on-prem |

**Truy vấn Overpass mẫu cho corridor (bbox thay bằng tuyến thực tế):**

```overpassql
[out:json][timeout:60];
(
  way["railway"="rail"](35.0,139.0,35.1,139.1);
  relation["route"="railway"](35.0,139.0,35.1,139.1);
  way["bridge"="yes"]["railway"](35.0,139.0,35.1,139.1);
  way["tunnel"="yes"]["railway"](35.0,139.0,35.1,139.1);
);
out geom;
**Chất lượng đường sắt Nhật trong OSM:** ~**83% mạng lưới có line relation** — chỉ số relation, **không đồng nghĩa track/station/thuộc tính đầy đủ** ([railreport](https://www.railreport.org/country/Japan)). Đủ vẽ tuyến tham chiếu; vị trí cầu B-14/hầm T-07 dùng tọa độ nội bộ. Mật độ building/height đúng bbox 12k400–15k600 **chưa đo — chạy Overpass 1 lần trước 25/11**.

### 2.7 "API Map của Meta" — kết luận (Meta社地図APIの正体)

1. **Sản phẩm bản đồ duy nhất của Meta là Mapillary (ảnh đường phố + dữ liệu bản đồ dẫn xuất), không có tile API, không có 3D map API, không có engine 3D miễn phí nào.** Truy cập dữ liệu qua [Mapillary API](https://www.mapillary.com/developer/api-documentation), xem ảnh qua web/app Mapillary ([truy cập API](https://help.mapillary.com/hc/en-us/articles/360010234680-Accessing-imagery-and-data-through-the-Mapillary-API)).
2. **Mapbox và MapTiler là công ty độc lập, không liên quan Meta** ([pricing Mapbox](https://www.mapbox.com/pricing), [pricing MapTiler](https://www.maptiler.com/cloud/pricing/)) — tên gần giống "Meta" nên dễ nhầm; cả hai đều cần token/key và free tier giới hạn (mục 2.1).
3. Không tìm thấy sản phẩm Meta nào khác là map tile/3D API mở (đã tìm developer docs + help center Mapillary). Nếu stakeholder nhắc "bản đồ free của Meta", câu trả lời: **đó chính là Mapillary, và nó chỉ cho ảnh + object detection, không cho nền 3D**.

### 2.8 Ma trận license + câu attribution bắt buộc (ライセンス・帰属表示)

| Dữ liệu/dịch vụ | License | Dùng demo thương mại | **Câu attribution phải hiển thị** |
|---|---|---|---|
| Dữ liệu OSM (data) | **ODbL** ([copyright](https://www.openstreetmap.org/copyright/sp), [FAQ](https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ)) | Được, kèm attribution; DB phái sinh phân phối lại thì ShareAlike ( Produced Work như ảnh render thì không) ([guideline](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline)) | `© OpenStreetMap contributors` + link https://www.openstreetmap.org/copyright |
| Tile OSM本家 / OpenFreeMap / Protomaps (dữ liệu OSM trong tile) | ODbL (data) + terms từng provider | Theo bảng 2.1 | `© OpenStreetMap contributors` (OpenFreeMap/Protomaps style thường đã có) |
| GSI tiles + DEM | コンテンツ利用規約 / 測量法 ([規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)) | Realtime + attribution thì OK; phân phối lại cần thủ tục | `<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル（国土地理院）</a>`; có chế biến thì ghi thêm nội dung chế biến, **không trình bày như sản phẩm của GSI** ([明示方法](https://www.gsi.go.jp/LAW/2930-meizi.html)) |
| PLATEAU | Từng dataset: CC BY 4.0 / 公共データ利用規約 / ODC-BY / ODbL ([guide](https://www.mlit.go.jp/plateau/start-guide/)) | Nhìn chung được | Ghi theo trang dataset từng thành phố (ví dụ `© MLIT PLATEAU — [City] [year], CC BY 4.0`) — **kiểm tra từng file tải** |
| Cesium OSM Buildings | ODbL via OSM ([terms](https://cesium.com/legal/third-party-terms/)) | Được | `© OpenStreetMap contributors` |
| Copernicus DEM | License Copernicus ([PDF](https://dataspace.copernicus.eu/sites/default/files/media/files/2025-06/copernicus_contributing_mission_data_access_v2_cop_dem_licenses.pdf)) | Được | Nguyên văn mục 2.4 |
| Sentinel-2 | Sentinel legal notice ([notice](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice)) | Được | `Contains modified Copernicus Sentinel data [2024]` |
| Mapillary ảnh | **CC BY-SA 4.0** ([help](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data)) | Được, nhưng ShareAlike cho phái sinh | Mẫu hãng đề xuất: `"[Title]" [link ảnh] by [username] [link profile], CC BY-SA`; UI tối thiểu: `© Mapillary contributors, CC BY-SA` + link ảnh gốc |
| Engine (CesiumJS/MapLibre/deck.gl) | Apache-2.0 / BSD-3 / MIT | Được | Giữ license header theo từng license (không cần attribution UI) |
| OSRM/Valhalla (backlog) | BSD-2 / MIT | Được | Giữ copyright notice khi phân phối |

---

## 3) Bảng so sánh tổng (比較表)

Cột: option | license | limit | Japan coverage | offline | effort | risk.

| Option | License | Limit | Japan coverage | Offline | Effort | Risk |
|---|---|---|---|---|---|---|
| GSI 標準地図 + シームレス写真 (nền chính) | GSI terms, attribution bắt buộc | Không quota; realtime miễn thủ tục, phân phối lại cần thủ tục | ★★★ (Nhật, z5–18/ảnh z14–18) | △ (cache ngắn hạn OK; offline phát hành cần thủ tục) | Thấp (1–2 h gắn XYZ vào Cesium) | Thấp cho demo có mạng |
| OpenFreeMap styles (dự phòng 2D) | ODbL + no-SLA terms | Không quota công bố; không SLA | ★★ (OSM global, Nhật đủ đường sắt) | △ (tự host cần ≥300 GB SSD [docs](https://docsearch.algolia.com/mcp/docs/repo/hyperknot/openfreemap)) | Thấp (URL style) | Trung bình (có thể sập giữa demo) |
| PLATEAU 3D Tiles streaming | Từng dataset (CC BY 4.0…) | Không quota; experimental, không uptime cam kết | ★★★ (329 TP; ngoài vùng phủ = trống) | ✗ (streaming) → ○ nếu tải file về | Thấp (paste tileset.json vào Cesium) | Trung bình (ngoài vùng phủ/bản thử nghiệm) |
| PLATEAU file tải về + tự host | Như trên | Dung lượng server mình | ★★★ trong vùng phủ | ○ (file tĩnh/Cesium ion self) | Trung bình (tải + cắt bbox [推定] 0,5–1 ngày) | Thấp sau khi có file |
| GSI DEM → terrain tự host | GSI terms | Không quota realtime | ★★★ (5 m/10 m) | ○ (quantized-mesh/Terrarium self) | Trung bình ([推定] 0,5–1 ngày convert) | Thấp |
| AWS Terrarium (fallback terrain) | Hỗn hợp (ghi credit Joerd) | Giới hạn băng thông S3/AWS | ★★ (~30 m [推定]) | △ (cache) | Thấp | Trung bình (provenance rắc rối) |
| Copernicus GLO-30 (fallback) | License Copernicus + câu attribution cố định | Tải theo Data Space quota tài khoản | ★★ (30 m) | ○ (đã tải) | Thấp–trung bình | Thấp |
| Sentinel-2 nền phụ | Sentinel legal notice | Tài khoản Data Space | ★★ (10 m — thô) | ○ (đã tải) | Trung bình | Thấp nhưng ít giá trị demo |
| Mapillary ảnh đường phố | CC BY-SA + token server-side | [推定] ceilings chưa xác minh (mục 2.5) | ★ (tùy tuyến có ảnh cộng đồng) | ✗ (cần API) | Thấp (link/viewer embed) | Trung bình (ShareAlike + coverage hên xui) |
| Overpass 1-shot + cache | ODbL | ~10k req/ngày guideline | ★★ (rail 83% relation) | ○ (sau khi cache GeoJSON) | Thấp (vài giờ) | Thấp nếu chỉ query 1 lần |
| Nominatim / OSRM / Valhalla | ODbL + BSD/MIT | 1 req/s (public) / tự host nặng | ★★ | ○ (tự host) | Cao (ngày–tuần) | Cao → **loại khỏi MVP** |
| MapTiler/Mapbox/Stadia hosted | Terms hãng + key/token | 100k req / 50k loads / 200k credits | ★★★ | ✗ | Thấp | Cao (key ở client, free=phi thương mại) → **loại** |

---

## 4) Khuyến nghị (推奨スタック)

| Lớp | Chọn | Lý do (1 dòng) |
|---|---|---|
| Engine 3D (3Dエンジン) | **CesiumJS (Apache-2.0)** tự host bundle | True-3D duy nhất nuốt PLATEAU 3D Tiles + point-cloud corridor + terrain mà không cần token |
| Nền 2D/imagery (背景地図・画像) | **GSI 標準地図 + シームレス写真** (chính), OpenFreeMap Liberty (dự phòng) | Nhật chi tiết nhất, không key, realtime miễn thủ tục + attribution chuẩn |
| Nhà 3D (建物) | **PLATEAU 3D Tiles** vùng corridor (tải file nếu kịp, stream nếu không) + fallback Cesium OSM Buildings | Chiều cao/sàn chỉ PLATEAU mới có; OSM height 4,7% là không dùng được |
| Địa hình (地形) | **GSI DEM5/10 → quantized-mesh tự host**; fallback Terrarium/Copernicus | 5–10 m cho cầu-hầm; fallback 30 m khi GSI convert chưa xong |
| Ảnh đường phố (街頭画像) | **Mapillary viewer link/embed theo tọa độ** (token ở server proxy) | Bối cảnh mặt đất miễn phí duy nhất của "nhà Meta"; không nhúng vào 3D scene vì ShareAlike |
| Vector tuyến (路線ベクター) | **Overpass 1-shot → GeoJSON tĩnh** trong repo | Tránh gọi live giữa demo; OSM rail chỉ làm nền tham chiếu |
| Loại bỏ | Mapbox/MapTiler/Stadia key, Nominatim, OSRM/Valhalla, Sentinel-2 nền chính | Token ở client / effort cao / độ phân giải không hợp — dời post-meeting |

Thanh attribution demo (hiển thị thường trực góc bản đồ): `© OpenStreetMap contributors · 地理院タイル（国土地理院） · [City] PLATEAU [license] · 地形: GSI · 街頭画像: © Mapillary contributors, CC BY-SA` (+ link đầy đủ trong About).

## 5) Kiến trúc / đặc tả tích hợp (構成・統合仕様)

```
React (点検確認 tab)
 └─ CesiumJS (npm bundle, self-host, không CDN ngoài)
     ├─ Imagery: GSI std (mặc định) ⇄ seamlessphoto (toggle) [online]
     │            └─ fallback: OpenFreeMap vector draped [online]
     ├─ Terrain: quantized-mesh tự host từ GSI DEM [có thể offline]
     │            └─ fallback: Terrarium S3 [online] / mặt phẳng + exaggeration
     ├─ 3D Tiles: PLATEAU LOD1 bbox corridor [stream→file] + corridor point-cloud demo (riêng)
     ├─ Vector: GeoJSON tĩnh (rail OSM 1-shot + B-14/T-07 nội bộ) + 縦断 profile (deck.gl overlay hoặc SVG)
     └─ Mapillary: nút "xem ảnh mặt đất" mở viewer theo lat/lon (token từ /api proxy, không lộ client)
AttributionBar (thường trực) + About dialog (license đầy đủ) + OfflineBadge (báo online/offline)
```

**Đặc tả tích hợp tối thiểu (MVP interface):**

- `GET /api/geo/config` → `{ imagery, terrain, plateauTilesetUrl, corridorGeoJsonUrl, offline }` — tab 3D render thuần từ config, không hardcode URL trong component.
- `tileset.json` PLATEAU + GeoJSON corridor + terrain mesh dưới `/public/geo/` khi đã tải (air-gap ready); streaming URL chỉ trong config dev. Token Mapillary (nếu dùng) ở server (`/api/geo/mapillary`), **không** `REACT_APP_*` token. Mọi URL ngoài qua allowlist 1 file `geoSources.ts`.

## 6) Kế hoạch 2 ngày demo 26/11 vs MVP (2日計画・MVP)

**Ngày 1 (24/11) — nền + nhà:** CesiumJS + GSI std/seamlessphoto toggle (1–2 h); PLATEAU streaming tileset + screenshot bằng chứng (2–3 h); Overpass 1-shot → GeoJSON tĩnh (2 h); AttributionBar + About (1 h). **Cuối ngày:** globe quay được, nhà 3D hiện (hoặc screenshot + lý do vùng phủ).

**Ngày 2 (25/11) — địa hình + tab + dự phòng:** convert GSI DEM bbox → terrain tự host, fallback Terrarium (0,5–1 ngày); khôi phục 5 tab đúng thứ tự 飛行スケジュール/撮影計画/点検確認 (3D + 縦断)/変位解析/保守優先度 (0,5 ngày); nút Mapillary + OfflineBadge + rehearsal có/không mạng. **Đóng băng tối 25/11.**

**MVP tối thiểu:** Cesium + GSI imagery + terrain phẳng phóng đại + PLATEAU stream + GeoJSON tĩnh + attribution. **Post-meeting:** terrain mesh hoàn chỉnh, PLATEAU/PMTiles tự host, Nominatim/OSRM/Valhalla on-prem, Sentinel-2.

## 7) Rủi ro (リスク)

| # | Rủi ro | Mức | Giảm thiểu |
|---|---|---|---|
| 1 | PLATEAU streaming (experimental) sập/giữa demo; vùng corridor ngoài 329 TP phủ | Cao nhất | Tải file bbox trước 25/11; screenshot/video dự phòng; fallback OSM Buildings |
| 2 | GSI tile / DEM bị hiểu sai terms khi cache/phân phối lại (測量法) | Trung bình | Chỉ realtime + attribution; cache demo ghi rõ tạm thời; thủ tục trước khi đóng gói offline |
| 3 | Mapillary CC BY-SA ShareAlike lan vào sản phẩm phái sinh; coverage tuyến không có ảnh | Trung bình | Chỉ link/viewer + credit nhiếp ảnh gia; không bake ảnh vào scene; kiểm tra coverage trước |
| 4 | OSM rail/building thưa (height 4,7%) khiến nền 3D trống nếu PLATEAU vắng | Trung bình | Dùng tọa độ cầu-hầm nội bộ làm truth; OSM chỉ nền tham chiếu |
| 5 | Free tier key (MapTiler/Mapbox/Stadia) hết quota / cấm dùng thương mại / lộ token | Trung bình | Không dùng cho demo; OpenFreeMap/GSI không key |
| 6 | Overpass/Nominatim public bị throttle giữa chuẩn bị | Thấp | Query 1 lần + cache; không gọi live trong demo |
| 7 | Air-gap cuối cùng vs demo có mạng (kỳ vọng stakeholder) | Trung bình | Ghi rõ trong slide: "demo online, bản on-prem dùng file tự host" + thư mục `/public/geo/` chứng minh |
| 8 | Nhầm "Meta map API" → stakeholder đòi tính năng không tồn tại | Thấp (sau báo cáo này) | Mục 2.7 + slide 1 trang: Meta = Mapillary ảnh, không phải nền 3D |

## 8) References (参考文献・URL一覧)

- OSMF Tile Usage Policy: https://operations.osmfoundation.org/policies/tiles/ (dự phòng: https://openstreetmap.github.io/owg-website/policies/tiles/)
- OSM tile CDN enforcement 30/07/2025: https://community.openstreetmap.org/t/technical-updates-to-the-tile-openstreetmap-org-service-openstreetmap-org-standard-layer/133421
- OSM Copyright/ODbL: https://www.openstreetmap.org/copyright/sp — Licence FAQ: https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ — Produced Work: https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline
- OpenFreeMap: https://openfreemap.org/ — self-host yêu cầu (~300 GB): https://docsearch.algolia.com/mcp/docs/repo/hyperknot/openfreemap
- Protomaps about/pricing: https://protomaps.com/about — free-tier: https://protomaps.com/blog/free-tier-maps — PMTiles: https://github.com/protomaps/pmtiles — cost: https://docs.protomaps.com/deploy/cost
- MapTiler pricing: https://www.maptiler.com/cloud/pricing/ — API key: https://docs.maptiler.com/guides/developer/credentials/api-key/
- Mapbox pricing: https://www.mapbox.com/pricing
- Stadia pricing: https://stadiamaps.com/pricing — limits: https://docs.stadiamaps.com/limits — FAQ commercial: https://stadiamaps.com/faqs/
- GSI タイル一覧: https://maps.gsi.go.jp/development/ichiran.html — 仕様: https://maps.gsi.go.jp/development/siyou.html (portal: https://maps.gsi.go.jp/development/)
- GSI コンテンツ利用規約: https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html — 出典明示: https://www.gsi.go.jp/LAW/2930-meizi.html — 資料2014 (cache): https://maps.gsi.go.jp/pn/meeting_partners/data/20141120/02.pdf
- PLATEAU open data: https://www.mlit.go.jp/plateau/open-data/ — start guide (license): https://www.mlit.go.jp/plateau/start-guide/ — 形式: https://www.mlit.go.jp/plateau/learning/tpc03-1/ — 3D Tiles配信docs: https://docs.plateauview.mlit.go.jp/datasets/3d-tiles/ — 329都市press: https://www.mlit.go.jp/report/press/toshi03_hh_000223.html
- Cesium OSM Buildings: https://cesium.com/platform/cesium-ion/content/cesium-osm-buildings/ — third-party terms: https://cesium.com/legal/third-party-terms/
- CesiumJS README/AP2.0: https://github.com/CesiumGS/cesium/blob/main/README.md?plain=1 — LICENSE: https://github.com/CesiumGS/cesium/blob/main/LICENSE.md
- MapLibre README: https://github.com/maplibre/maplibre-gl-js/blob/main/README.md — terrain example: https://maplibre.org/maplibre-gl-js/docs/examples/3d-terrain/
- deck.gl LICENSE: https://github.com/visgl/deck.gl/blob/master/LICENSE
- AWS Terrain Tiles: https://aws.amazon.com/marketplace/pp/prodview-x7vtai3hasf26 — Joerd attribution: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- Copernicus DEM collection: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM — license PDF: https://dataspace.copernicus.eu/sites/default/files/media/files/2025-06/copernicus_contributing_mission_data_access_v2_cop_dem_licenses.pdf
- Sentinel-2: https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2 — terms: https://dataspace.copernicus.eu/terms-and-conditions — legal notice: https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice
- Mapillary (Meta product): https://help.mapillary.com/hc/en-us/articles/115001770089-Meta-s-open-mapping-mission — CC BY-SA: https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data — API access: https://help.mapillary.com/hc/en-us/articles/360010234680-Accessing-imagery-and-data-through-the-Mapillary-API — download terms: https://help.mapillary.com/hc/en-us/articles/4407521157138-Downloading-map-data-via-the-Mapillary-web-app — dev docs: https://www.mapillary.com/developer/api-documentation — CC deed: https://creativecommons.org/licenses/by-sa/4.0/deed.en
- Overpass commons: https://dev.overpass-api.de/overpass-doc/en/preface/commons.html — Nominatim policy: https://operations.osmfoundation.org/policies/nominatim/ — Nominatim install: https://nominatim.org/release-docs/develop/admin/Installation/
- OSRM: https://github.com/Project-OSRM/osrm-backend — Valhalla: https://github.com/valhalla/valhalla
- OSM Japan rail stats: https://www.railreport.org/country/Japan — building height paper: https://isprs-archives.copernicus.org/articles/XLVIII-4-W15-2025/149/2025/isprs-archives-XLVIII-4-W15-2025-149-2025.pdf — SoTM 2025 PLATEAU×OSM: https://2025.stateofthemap.org/sessions/N89YSU/
