# 05c — Dịch vụ bản đồ/3D/imagery miễn phí nhưng cần token: có đáng thay stack GSI/OSM cho demo 26/11?

Ngày tra cứu: 23-11-2026. Hạn mức theo trang pricing gốc; số ước tính ghi `[推定]`, đơn vị USD trừ khi ghi khác.
Câu hỏi trung tâm: dịch vụ token-free-tier nào cho nhà 3D (3D buildings) / địa hình (地形) / 3D Tiles ảnh thật (Photorealistic) / ảnh vệ tinh (衛星画像) vượt trội rõ rệt so với GSI/OSM mà vẫn an toàn trong 2 ngày còn lại?
Mười dịch vụ: Mapbox, MapTiler, Stadia, Cesium ion, Google, Azure, Apple MapKit JS, ArcGIS, HERE, TomTom, kèm phụ lục Mapillary. Liên quan: PLATEAU/GSI (`04a`), viewer (`04b`), ảnh thực tuyến (`05b`).

## 1) Phạm vi (Scope)

- Demo: tuyến 東海道本線 (Tōkaidō) giả định quanh 根府川 (Nebukawa), hành lang ~3,2 km, 1–2 ngày trước doanh nghiệp đường sắt Nhật (26/11/2026). Stack: MapLibre 6.19 + 地理院タイル (GSI, không token) + OpenFreeMap buildings, tài sản 3D tự dựng (cầu B-14, hầm T-07).
- "Miễn phí nhưng cần token" gồm cả gói free không thẻ và gói pay-as-you-go có free quota nhưng bắt buộc tài khoản thanh toán.
- Ngoài phạm vi: chi tiết PLATEAU (`04a`), kiến trúc viewer (`04b`), ảnh thực tế đường sắt (`05b`).

## 2) Findings

### 2.1 Dịch vụ nào thực sự có dữ liệu 3D (không chỉ tile 2D)?

| Dịch vụ | Nhà 3D gốc | Địa hình 3D | 3D Tiles ảnh thật | Ảnh vệ tinh | Kết luận 3D |
|---|---|---|---|---|---|
| Mapbox | Có — Standard style có nhà 3D, cây 3D dựng sẵn ([nguồn](https://www.mapbox.com/maps)) | Có — terrain vector toàn cầu | Không (chỉ Tilesets API tự host, tính phí riêng) | Có — Satellite | 3D đầy đủ nhất nhóm map SDK; đổi lại dính license GL JS v2+ |
| MapTiler | Có — Planet/Streets có chiều cao nhà, đùn khối client-side; Nhật dùng thêm dữ liệu GSI qua MIERUNE ([nguồn](https://docs.maptiler.com/guides/map-tiling-hosting/data-hosting/origin-of-the-maptiler-planet-data/)) | Có — Terrain-RGB/quantized-mesh, tính trong map session ([nguồn](https://www.maptiler.com/cloud/pricing/)) | Không — "3D sessions" 2.000/tháng của Free chỉ cho GeoSplats tự upload | Có — pha nhiều nguồn, riêng Nhật pha thêm ảnh hàng không chính phủ ([nguồn](https://docs.maptiler.com/schema-raster/satellite/)) | 3D tốt, nguồn Nhật rõ, nhưng Free cấm dùng thương mại |
| Stadia | Không — chỉ tile 2D; muốn nhà 3D phải tự đùn bằng MapLibre fill-extrusion `[推定]` | Không `[推定]` | Không | Không `[推定]` | Không phải ứng viên 3D; chỉ là tile 2D dự phòng |
| Cesium ion | Có — OSM Buildings + World Terrain qua streaming quota | Có — World Terrain, tính vào 15 GB/tháng gói Community | Có — Google Photorealistic qua Asset Depot (asset 2275207), quota riêng 1.000 root tiles/tháng gói Community ([nguồn](https://cesium.com/platform/cesium-ion/pricing/)) | Có — Global Imagery (Bing/Google/Azure), 1.000 sessions/tháng | Cửa duy nhất vào Photorealistic 3D không cần thẻ Google, nhưng quota nhỏ + vướng điều khoản thương mại |
| Google | Có — trong Photorealistic 3D Tiles (mesh纹理 thật, không phải block sạch) | Có — terrain toàn cầu; bề mặt 3D chỉ ở khu vực highlight ([nguồn](https://developers.google.com/maps/documentation/javascript/3d/coverage)) | Có — trực tiếp, 1.000 sự kiện/tháng free rồi $6/1.000 ([nguồn](https://developers.google.com/maps/billing-and-pricing/pricing)) | Có — Map Tiles API 2D: 100.000 tile/tháng free rồi $0,60/1.000 | Ảnh thật tốt nhất; Nhật (Tokyo/Osaka) có phủ ([nguồn](https://developers.google.cn/maps/coverage?hl=en)); bắt buộc billing account + quota cap tay |
| Azure Gen2 | Không — đùn khối client-side `[推定]` | Có elevation API, không phải terrain render sẵn `[推定]` | Không | Có — imagery tiles | 2D + ảnh; không vượt GSI/OSM về 3D |
| Apple MapKit JS | Một phần — camera pitch + nhà 3D nơi Apple có dữ liệu; phủ Nhật yếu `[推定]` | Hạn chế `[推定]` | Không | Có | Cần membership $99/năm; không đáng cho demo 2 ngày |
| ArcGIS | Không — Basemap Styles chuẩn không hỗ trợ 3D basemap ([nguồn](https://developers.arcgis.com/rest/basemap-styles/)) | Không trong free chuẩn | Không | Có — imagery 2D (2 triệu tile free/tháng) | Free hào phóng cho 2D, vô dụng cho 3D |
| HERE / TomTom | Đùn khối client-side (HERE SDK / TomTom plugin không tốn request riêng, ([nguồn](https://docs.tomtom.com/pricing))) | Không | Không | Có (raster) | Tương đương thứ MapLibre đã làm miễn phí |

Điểm mấu chốt: chỉ ba nguồn mang lại thứ GSI/OSM không có — Mapbox Standard 3D, MapTiler Satellite Nhật + terrain, Google Photorealistic 3D Tiles. Còn lại là "2D + tự đùn khối".

### 2.2 Hạn mức free và thẻ tín dụng (クレジットカード)

| Dịch vụ | Free quota (công bố) | Cần thẻ? | Vượt quota thì sao? |
|---|---|---|---|
| Mapbox (GL JS) | 50.000 map loads/tháng; Vector Tiles 200.000 requests/tháng ([nguồn](https://www.mapbox.com/pricing)) | Không cần để đăng ký; cần payment method cho quyền production chuẩn, không có spending cap ([nguồn](https://docs.mapbox.com/accounts/guides/signup/)), ([nguồn](https://docs.mapbox.com/accounts/faq/how-does-pay-as-you-go-billing-work/)) | Tự tính tiền (VD $5/1.000 loads cho 50.001–100.000) |
| MapTiler Free | 100.000 requests + 5.000 sessions/tháng; 5 GB storage ([nguồn](https://www.maptiler.com/cloud/pricing/)) | Không | Dừng/paused đến kỳ sau, không tính tiền |
| Stadia Free | 200.000 credits/tháng (1 tile chuẩn = 1 credit) ([nguồn](https://stadiamaps.com/pricing)) | Không ([nguồn](https://stadiamaps.com/faqs/)) | Chặn cứng HTTP 429 đến kỳ sau ([nguồn](https://docs.stadiamaps.com/limits)) |
| Cesium ion Community | 10 GB storage; 15 GB stream/tháng; Google 3D 1.000 root tiles/tháng; Imagery 1.000 sessions/tháng ([nguồn](https://cesium.com/platform/cesium-ion/pricing/)) | Không | Hết quota thì ngừng stream; không tự tính tiền |
| Google 3D Tiles | 1.000 events/tháng/account, sau đó $6/1.000 ([nguồn](https://developers.google.com/maps/billing-and-pricing/pricing)) | Bắt buộc billing account; vượt free bị charge cuối kỳ ([nguồn](https://developers.google.com/maps/billing-and-pricing/overview?hl=en)) | Tự tính tiền — budget alert chỉ là thông báo, phải đặt quota cap tay ([nguồn](https://developers.google.com/maps/billing-and-pricing/manage-costs)) |
| Google 2D tiles | 100.000 requests/tháng, sau đó $0,60/1.000; default quota 100.000 requests/ngày/project ([nguồn](https://developers.google.com/maps/billing-and-pricing/pricing)), ([nguồn](https://developers.google.com/maps/documentation/tile/release-notes)) | Như trên | Như trên |
| Azure Gen2 | Base tiles 5.000 transactions/tháng (~75.000 requests, 1 tx = 15 tiles `[推定]`); imagery 1.000 tx/tháng ([nguồn](https://azure.microsoft.com/en-us/pricing/details/azure-maps/)), ([nguồn](https://learn.microsoft.com/en-us/azure/azure-maps/understanding-azure-maps-transactions)) | Cần subscription Azure | Tự tính tiền theo meter |
| Apple MapKit JS | 250.000 views/ngày + 25.000 service calls/ngày/membership ([nguồn](https://developer.apple.com/maps/web/)) | Cần membership $99/năm | Vượt quota trả `TooManyRequests`, không tự charge ([nguồn](https://developer.apple.com/maps/resources/)) |
| ArcGIS | 2 triệu tiles + 1.000 sessions/tháng, sau đó $0,15/1.000 tiles hoặc $4/1.000 sessions ([nguồn](https://developers.arcgis.com/rest/basemap-styles/)) | Pay-as-you-go nếu vượt | Tự tính tiền nếu bật pay-as-you-go |
| TomTom / HERE | TomTom 200K vector tiles/tháng ([nguồn](https://docs.tomtom.com/pricing)); HERE free theo từng service, gói Limited đã khai tử 31-08-2025 ([nguồn](https://knowledge.here.com/csm_kb?id=public_kb_csm_details&number=KB0028268)) | Không (freemium) | Chặn API hết quota đến kỳ sau |
| Mapillary (extra) | Free, không quota công bố; giới hạn kỹ thuật ~50K tile req/app/ngày `[推定]` ([nguồn](https://forum.mapillary.com/t/50-000-requests-day-rate-limit-scope/10644)) | Không | Chặn/IP-block khi vượt, không tính tiền ([nguồn](https://help.mapillary.com/hc/en-us/articles/8348198426396-Mapillary-FAQ)) |

### 2.3 Demo thương mại trước khách (商用デモ): free tier có cho phép không?

Đây là điểm loại trừ quan trọng nhất:

- MapTiler Free: chỉ testing/PoC/personal/non-commercial; commercial thuộc Flex/Custom ([nguồn](https://www.maptiler.com/cloud/pricing/)). Dùng Free demo cho JR là sai ToS — loại làm basemap chính.
- Stadia Free: development/evaluation/non-commercial; commercial từ Starter $20/tháng ([nguồn](https://docs.stadiamaps.com/limits)). Loại tương tự.
- Cesium ion Community: personal/non-commercial; cho phép "exploratory commercial development" và demo cho khách tiềm năng trong giới hạn plan, nhưng công ty >$50K doanh thu/vốn hoặc dự án chính phủ phải mua commercial ([nguồn](https://cesium.com/platform/cesium-ion/pricing/)), ([nguồn](https://cesium.com/legal/terms-of-service)). Chiếu thử nội bộ được; làm nền chính cho demo khách thì rủi ro điều khoản.
- Mapbox pay-as-you-go, Google (billing), Azure, ArcGIS, Apple (membership): cho phép thương mại. Nhóm duy nhất "sạch" pháp lý cho demo 26/11.
- Mapillary: free kể cả commercial use ([nguồn](https://help.mapillary.com/hc/en-us/articles/8348198426396-Mapillary-FAQ)). Extra an toàn.

### 2.4 Phủ Nhật (日本カバレッジ) và so với PLATEAU/GSI

- Google Photorealistic: Nhật có phủ (Tokyo/Osaka tốt nhất) nhưng là mesh纹理 từ ảnh, chi tiết theo khu vực; ven biển như 根府川 phải kiểm tra thực tế ([nguồn](https://developers.google.com/maps/documentation/javascript/3d/coverage)), ([nguồn](https://developers.google.cn/maps/coverage?hl=en)). Đẹp khi flyover nhưng không thay mô hình cầu/hầm kỹ thuật.
- MapTiler: nguồn Nhật rõ nhất — nhà dùng dữ liệu GSI (qua MIERUNE), imagery pha ảnh hàng không chính phủ Nhật ([nguồn](https://docs.maptiler.com/guides/map-tiling-hosting/data-hosting/origin-of-the-maptiler-planet-data/)), ([nguồn](https://docs.maptiler.com/schema-raster/satellite/)). Vùng 根府川 hưởng lợi từ ảnh hàng không hơn nhà 3D.
- Mapbox Standard 3D: đô thị Nhật tốt, ven biển thưa `[推定]` — kiểm tra tile thực tế.
- Cesium OSM Buildings cùng nguồn OSM như OpenFreeMap hiện tại → giá trị Cesium nằm ở terrain + Google 3D Tiles.
- So với PLATEAU (xem `04a`): PLATEAU LOD1/LOD2 mở, không token, chính xác hình học hơn mọi dịch vụ trên; nhược điểm là phủ thành phố lớn, 根府川 có thể ngoài phủ `[推定]`. Google 3D thắng "nhìn thật", thua độ chính xác và quyền tái sử dụng.

### 2.5 Gắn với engine (エンジン結合): license và khả thi không trả tiền SDK

- Mapbox GL JS v2+: license proprietary theo ToS Mapbox ([nguồn](https://github.com/mapbox/mapbox-gl-js/blob/main/LICENSE.txt)). Render style Mapbox bằng MapLibre (BSD-3-Clause, fork từ v1.13, ([nguồn](https://maplibre.org/maplibre-gl-js/docs/guides/mapbox-migration-guide/))) là cấu hình phổ biến — kiểm tra ToS mới nhất trước demo thương mại; 2 ngày còn lại không cần Mapbox GL JS.
- Cesium ion + CesiumJS (Apache-2.0, ([nguồn](https://cesium.com/platform/cesiumjs))): cặp chuẩn, hai đường lấy Google 3D — (a) `fromIonAssetId(2275207)` + ion token (quota ion), (b) `createGooglePhotorealistic3DTileset({key})` + Google key (billing Google) ([nguồn](https://cesium.com/learn/ion-sdk/ref-doc/global.html)). Chỉ nhúng cho một tab flyover riêng (thêm ~MB JS + worker Vite, xem `04b`).
- Google 3D trong Three.js (VD `3DTilesRendererJS`, MIT): tự code camera tốn thời gian — xếp sau CesiumJS. Apple MapKit JS (JWT ký server-side) không hợp demo MapLibre 2 ngày.

### 2.6 Quota math cho demo (~25K tile views `[推定]`, hành lang 3,2 km, 1–2 ngày)

Giả định `[推定]`: một "view" nạp ~8–12 vector tiles + 4–8 raster/terrain tiles ở zoom 14–16; ~25K lượt/2 ngày gồm dev/test lặp lại.

| Dịch vụ | Tiêu thụ `[推定]` | Vừa free? | Vượt quota giữa demo thì sao? |
|---|---|---|---|
| GSI + OpenFreeMap | ~0 ¥, không quota thanh toán | Vừa | Chậm khi nghẽn, không sập billing |
| Mapbox GL JS loads | 25K loads (init = 1, tương tác không tính thêm) | Vừa trong 50K | Tự charge $5/1.000 |
| Mapbox Vector Tiles (qua MapLibre) | 25K × 10 ≈ 250K requests | Vượt 200K free ~50K → ~$12 | Tự charge $0,25/1.000 |
| MapTiler (sessions hoặc tiles) | 25K sessions / ~250K requests | Vượt 5K sessions và 100K requests | Map xám giữa demo — rủi ro trình diễn cao |
| Stadia | ~250K credits | Vượt 200K | Tile 429 giữa demo — rủi ro cao |
| Cesium ion Google 3D | Flyover 3,2 km vài trăm–vài nghìn root tiles/lượt; 5–10 lượt test là chạm 1.000/tháng | Vừa nếu ≤ ~3 lượt bay hạn chế | Hết root tiles → tileset không load session mới |
| Google 3D trực tiếp | Một flyover chi tiết hàng nghìn events | 1.000 free/tháng hết sau 1 buổi test | Tự charge $6/1.000 — bắt buộc daily cap |
| Google 2D / Azure base | ~100–200K requests / ~75K requests | Vừa khít free | Tự charge theo meter |
| Mapillary extra | Vài chục viewer loads | Vừa xa | Không ảnh hưởng basemap |

Bài học: quota "block" (MapTiler/Stadia/Cesium) có thể chạm trần giữa demo; quota "bill" (Mapbox/Google/Azure) cần cap + thẻ. GSI/OSM là thứ duy nhất không có failure mode thanh toán/block.

### 2.7 Bảo mật token (トークン管理): public vs secret, proxy

- Public token trong browser là chuẩn (Mapbox public token, MapTiler key, Cesium ion token, Google API key, Mapillary client token). An toàn dựa vào giới hạn referrer/origin + quota cap, không dựa vào giấu key.
- Giới hạn domain: Mapbox "Allowed URLs" (không wildcard, token default không gắn được, `localhost` khai riêng) ([nguồn](https://docs.mapbox.com/accounts/guides/tokens/)); MapTiler "Allowed origins" (hỗ trợ `*.example.com`) ([nguồn](https://docs.maptiler.com/guides/developer/credentials/api-key/)); Cesium ion "Allowed URLs" (phân biệt http/https) ([nguồn](https://cesium.com/learn/ion/cesium-ion-access-tokens/)); Google key giới hạn HTTP referrers; Apple dùng JWT ký server-side.
- Secret không bao giờ xuống client; mọi ký JWT/quản trị quota làm ở FastAPI.
- Server proxy tile 2D (gắn key phía server) khả thi kỹ thuật nhưng kiểm tra ToS từng nhà — đa số cấm cache dài ngày/phân phối lại; proxy Google Photorealistic 3D để giấu key hầu như chắc chắn vi phạm và phá billing theo session ([nguồn](https://developers.google.com/maps/documentation/tile/usage-and-billing)). Quy tắc: 3D luôn load trực tiếp bằng public key giới hạn referrer.

## 3) Bảng so sánh (比較表)

| Service | 3D data | Free quota | Cần thẻ? | Commercial demo? | Token exposure | Japan (日本) | Risk tổng |
|---|---|---|---|---|---|---|---|
| Mapbox | Nhà 3D + terrain + satellite (Standard) | 50K loads / 200K tiles/tháng | Cần payment cho production | Được (pay-as-you-go) | Public token + Allowed URLs | Đô thị tốt, ven biển kiểm tra thêm | Trung — hóa đơn nếu vượt; license GL v2+ |
| MapTiler | Nhà (GSI) + terrain + satellite JP | 100K req + 5K sessions/tháng | Không | Không (Free cấm commercial) | Key + allowed origins (wildcard) | Tốt nhất nhóm (GSI + ảnh CQ Nhật) | Cao — vi phạm ToS + block |
| Stadia | Không (2D only) | 200K credits/tháng | Không | Không (Free non-commercial) | Key + referrer | Thường (OSM) | Cao — block 429, không hơn OSM |
| Cesium ion | OSM buildings + terrain + Google 3D | 10 GB / 15 GB stream / 1K root tiles/tháng | Không | Xám (chỉ eval nội bộ) | Token + Allowed URLs | Theo Google/OSM | Trung-cao — hết root tiles giữa demo |
| Google | Photorealistic 3D + 2D tiles + terrain | 1K 3D events + 100K 2D tiles/tháng | Bắt buộc billing | Được (pay-as-you-go) | Public key + referrer + daily cap | Tốt (Tokyo/Osaka; 根府川 kiểm tra) | Trung — tự charge; bắt buộc cap |
| Azure Gen2 | 2D + imagery (không 3D thật) | ~75K tile req + imagery 1K tx/tháng | Cần subscription | Được | Key/Entra | Thường | Thấp pháp lý, thấp giá trị 3D |
| Apple MapKit JS | 3D một phần | 250K views/ngày | Membership $99/năm | Được | JWT server-side | Yếu hơn Google `[推定]` | Không đáng cho 2 ngày |
| ArcGIS | 2D (không 3D basemap free) | 2M tiles + 1K sessions/tháng | Pay-as-you-go nếu vượt | Được | API key + referrer | Thường | Thấp pháp lý, bằng 0 về 3D |
| HERE / TomTom | Extrusion client-side | TomTom 200K tiles/tháng; HERE theo service | Không | Kiểm tra ToS hiện hành | Public key | Thường | Không hơn MapLibre tự đùn |
| Mapillary (extra) | Ảnh mặt đường (không phải 3D) | Free, ~50K req/app/ngày `[推定]` | Không | Được (cả commercial) | Client token browser OK | Kiểm tra phủ 根府川駅 `[推定]` | Thấp — lớp bổ sung |

## 4) Khuyến nghị (推奨): giữ GSI/OSM, token chỉ làm "extras"

**Verdict: KHÔNG chuyển basemap demo sang bất kỳ dịch vụ token nào. Giữ GSI + OpenFreeMap làm nền chính; chỉ dùng token cho tối đa 2 extras, mỗi extra có công tắc tắt (feature flag) và fallback về no-token.**

Lý do quyết định trong 10 phút:

1. Pháp lý: hai ứng viên "ngon-bổ-không thẻ" (MapTiler, Stadia) cấm commercial use ở Free — demo trước JR dùng Free là sai ToS; muốn sạch phải trả Flex/Starter, trái zero-budget.
2. Failure mode: quota "block" (MapTiler/Stadia/Cesium) chết cứng giữa demo; quota "bill" (Mapbox/Google) cần thẻ — đều tệ hơn GSI/OSM vốn không sập vì billing.
3. Giá trị/2 ngày: thứ duy nhất đáng tiền là "ảnh thật" (Google 3D flyover, Mapillary mặt đường cho tab 点検) — không cần thay toàn bộ basemap.

Thứ tự ưu tiên:

1. **Extra A — Mapillary (làm trước, ~2 giờ).** Free kể cả commercial, client token để browser được, lỗi widget không sập bản đồ. Điều kiện: có phủ quanh 根府川; không có thì bỏ.
2. **Extra B — Google Photorealistic MỘT cảnh flyover (nếu còn ≥ nửa ngày + có thẻ).** Qua ion Community nếu không thẻ (eval-only, ≤3 lượt bay `[推定]`), hoặc Google key + daily cap nếu có thẻ. CesiumJS trong tab riêng, default TẮT.
3. **Không làm:** chuyển nền sang Mapbox/MapTiler/Stadia; Apple/HERE/TomTom/Azure/ArcGIS dưới mọi hình thức đợt này.

| Cost-risk | Chi phí `[推定]` | Rủi ro demo day | Giá trị visual |
|---|---|---|---|
| GSI/OSM (baseline) | 0 | Không có | Đủ "bản đồ đáng tin" |
| + Mapillary | 0 | Thấp (cô lập) | Trung (ảnh thật mặt đường) |
| + Google 3D flyover (ion, không thẻ) | 0 | Trung (hết 1K root tiles) | Cao (1 cảnh "wow") |
| + Google 3D trực tiếp (có thẻ + cap) | $0–10 | Thấp nếu cap đúng | Cao |
| Chuyển nền Mapbox pay-as-you-go | $0–15 | Trung (hóa đơn + license v2) | Trung-cao |
| Chuyển nền MapTiler/Stadia Free | 0 | Rất cao (ToS + block) | Trung — cấm |

## 5) Kiến trúc / tích hợp (統合アーキテクチャ)

Extras theo nguyên tắc "progressive enhancement + kill switch" trên stack React 19 + Vite + FastAPI (xem `03-architecture.md`, `04b-3d-viewer.md`):

- Key/token đọc từ env server (`MAPILLARY_TOKEN`, `GOOGLE_MAPS_KEY`, `CESIUM_ION_TOKEN`); Vite chỉ nhận public key giới hạn referrer qua `VITE_*`; secret không xuống client. Endpoint `/api/map-config` cho client biết extra nào bật, không hardcode.
- Extra A: `Viewer({accessToken, container, imageId})` ([nguồn](https://mapillary.github.io/mapillary-js/docs/intro/try/)); container cố định chiều cao; lỗi → fallback ảnh GSI. Attribution: `© Mapillary contributors, CC BY-SA` + tên photographer ([nguồn](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data)).
- Extra B: `fromIonAssetId(2275207)` (ion token) hoặc `createGooglePhotorealistic3DTileset({key})` (Google key) ([nguồn](https://cesium.com/learn/ion-sdk/ref-doc/global.html)); camera固定 dọc hành lang 3,2 km; tắt mặc định. Không proxy 3D Tiles qua FastAPI.
- Fallback: extra lỗi → ẩn tab/widget, log về `/api/client-error`, demo tiếp tục trên GSI/OSM.

### Token setup + attribution cho top 2

**Top 1 — Mapbox (nếu có thẻ, đường sạch cho commercial):**

1. Đăng ký tại [mapbox.com](https://www.mapbox.com/pricing), thêm payment method, tạo **public token** mới (không dùng default) ([nguồn](https://docs.mapbox.com/accounts/guides/tokens/)).
2. Allowed URLs: `https://demo.<domain>/*` + `http://localhost:5173/*` (không wildcard domain, khai riêng từng host).
3. Style `mapbox://styles/mapbox/standard` qua MapLibre (kiểm tra ToS mới nhất), giới hạn số init Map object để ở trong 50K loads.
4. Budget alert + theo dõi usage mỗi buổi test.
5. Attribution: giữ nguyên control `© Mapbox © OpenStreetMap | Improve this map`, không ẩn/CSS che.

**Top 2 — Google Photorealistic 3D Tiles (cảnh wow, bắt buộc thẻ nếu đi trực tiếp):**

1. Tạo project + billing account, enable "Map Tiles API", tạo key giới hạn HTTP referrers (domain demo + localhost) ([nguồn](https://developers.google.com/maps/documentation/tile/3d-tiles-overview?hl=en)).
2. Đặt **daily quota cap** (VD 500 events/ngày `[推定]`) + budget alert — bắt buộc vì alert không phải spending cap ([nguồn](https://developers.google.com/maps/billing-and-pricing/manage-costs)).
3. Load bằng CesiumJS `createGooglePhotorealistic3DTileset`, hoặc ion asset 2275207 nếu dùng ion token.
4. Giữ Google logo + data attribution renderer tự vẽ; screenshot/video giữ nguyên attribution.
5. Bản không-thẻ: dùng ion Community token (Asset Depot thêm asset 2275207), chấp nhận 1.000 root tiles/tháng, chỉ eval nội bộ.

## 6) Kế hoạch 2 ngày vs MVP (2日計画)

**Plan A (khuyến nghị):**

- Sáng ngày 1 (3 giờ): kiểm tra phủ Mapillary quanh 根府川駅 + phủ Google 3D tại corridor ([nguồn](https://developers.google.com/maps/documentation/javascript/3d/coverage)); quyết định Extra A/B đi tiếp hay cắt.
- Chiều ngày 1 (4 giờ): gắn MapillaryJS vào tab kiểm tra + feature flag + fallback; tạo key giới hạn referrer.
- Sáng ngày 2 (3 giờ): nếu còn sức — tab flyover Cesium riêng, camera固定, default tắt; test ≤3 lượt bay trên ion `[推定]`.
- Chiều ngày 2 (2 giờ): tổng duyệt mất mạng/giả lập token die — extra tắt thì demo vẫn chạy trên GSI/OSM; chụp screenshot dự phòng cảnh wow.

**Plan B — MVP (một người, nửa ngày):** chỉ Extra A + screenshot/video Google 3D quay sẵn làm slide tĩnh. Không nhúng CesiumJS, không thêm dependency, không token billing nào.

## 7) Rủi ro (リスク)

| # | Rủi ro | Xác suất `[推定]` | Tác động | Giảm thiểu |
|---|---|---|---|---|
| R1 | MapTiler/Stadia/Cesium Free hết quota giữa demo → map xám/429 | Trung-cao với 25K views | Demo sập | Không làm basemap chính; extra có kill switch |
| R2 | Google/Mapbox charge thẻ vì quên cap | Trung | Hóa đơn bất ngờ | Daily cap + key riêng demo, xóa sau 26/11 |
| R3 | Dùng Free sai mục đích commercial trước JR | Chắc chắn nếu dùng MapTiler/Stadia Free | Pháp lý/hình ảnh | Chỉ chiếu trước khách thứ thuộc nhóm pay-as-you-go/membership |
| R4 | Google 3D mesh vùng 根府川 xấu/thiếu | Trung | Cảnh wow thành xấu | Kiểm tra coverage trước khi code; xấu thì cắt |
| R5 | Mapillary không phủ quanh tuyến | Trung | Extra A vô dụng | Kiểm tra phủ ngày 1; không có thì cắt trong 30 phút |
| R6 | CesiumJS nặng, lag máy demo | Thấp-trung | Lag khi chuyển tab | Tab riêng lazy-load, default tắt; test máy demo chiều ngày 2 |
| R7 | Key lộ qua DevTools/Git | Thấp | Quota bị đốt | Public key giới hạn referrer xuống client; secret ở server; rotate sau demo |
| R8 | Proxy/cache tile vi phạm ToS (nhất là Google 3D) | Thấp nếu làm đúng | Khóa tài khoản | 3D load trực tiếp; cache 2D ngắn hạn chỉ khi ToS cho phép |

## 8) References (参考文献・URL)

- Pricing: [Mapbox](https://www.mapbox.com/pricing) · [MapTiler](https://www.maptiler.com/cloud/pricing/) · [Stadia](https://stadiamaps.com/pricing) · [Cesium ion](https://cesium.com/platform/cesium-ion/pricing/) · [Google](https://developers.google.com/maps/billing-and-pricing/pricing) · [Azure](https://azure.microsoft.com/en-us/pricing/details/azure-maps/) · [TomTom](https://docs.tomtom.com/pricing)
- Billing/quota: [Mapbox signup](https://docs.mapbox.com/accounts/guides/signup/) · [Mapbox pay-as-you-go](https://docs.mapbox.com/accounts/faq/how-does-pay-as-you-go-billing-work/) · [Google pricing overview](https://developers.google.com/maps/billing-and-pricing/overview?hl=en) · [Google manage costs](https://developers.google.com/maps/billing-and-pricing/manage-costs) · [Google tile billing](https://developers.google.com/maps/documentation/tile/usage-and-billing) · [Google release notes](https://developers.google.com/maps/documentation/tile/release-notes) · [Stadia limits](https://docs.stadiamaps.com/limits) · [Stadia FAQ](https://stadiamaps.com/faqs/) · [Azure transactions](https://learn.microsoft.com/en-us/azure/azure-maps/understanding-azure-maps-transactions)
- Token/security: [Mapbox tokens](https://docs.mapbox.com/accounts/guides/tokens/) · [MapTiler API key](https://docs.maptiler.com/guides/developer/credentials/api-key/) · [Cesium ion tokens](https://cesium.com/learn/ion/cesium-ion-access-tokens/) · [Cesium ToS](https://cesium.com/legal/terms-of-service) · [MapTiler sessions vs requests](https://docs.maptiler.com/guides/account/sessions-vs-requests/)
- 3D/engine: [Mapbox Standard](https://www.mapbox.com/maps) · [mapbox-gl-js LICENSE](https://github.com/mapbox/mapbox-gl-js/blob/main/LICENSE.txt) · [MapLibre migration guide](https://maplibre.org/maplibre-gl-js/docs/guides/mapbox-migration-guide/) · [MapTiler Planet origin](https://docs.maptiler.com/guides/map-tiling-hosting/data-hosting/origin-of-the-maptiler-planet-data/) · [MapTiler Satellite](https://docs.maptiler.com/schema-raster/satellite/) · [CesiumJS API](https://cesium.com/learn/ion-sdk/ref-doc/global.html) · [CesiumJS 3D Tiles tutorial](https://cesium.com/learn/cesiumjs-learn/cesiumjs-photorealistic-3d-tiles) · [CesiumJS platform](https://cesium.com/platform/cesiumjs) · [Cesium attribution](https://cesium.com/learn/ion/content-usage-and-attribution-guide/) · [Google 3D coverage](https://developers.google.com/maps/documentation/javascript/3d/coverage) · [Google coverage Japan](https://developers.google.cn/maps/coverage?hl=en) · [ArcGIS basemap styles](https://developers.arcgis.com/rest/basemap-styles/)
- Platform khác: [Apple MapKit JS](https://developer.apple.com/maps/web/) · [Apple resources](https://developer.apple.com/maps/resources/) · [HERE Base plan](https://knowledge.here.com/csm_kb?id=public_kb_csm_details&number=KB0028268)
- Mapillary: [FAQ](https://help.mapillary.com/hc/en-us/articles/8348198426396-Mapillary-FAQ) · [MapillaryJS](https://mapillary.github.io/mapillary-js/docs/intro/try/) · [rate limit](https://forum.mapillary.com/t/50-000-requests-day-rate-limit-scope/10644) · [CC BY-SA](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data)

## KEY DECISIONS

1. Giữ GSI + OpenFreeMap làm basemap duy nhất cho demo 26/11; không chuyển nền sang dịch vụ token nào.
2. Token chỉ dùng cho tối đa 2 extras có kill switch: Mapillary trước, Google 3D flyover sau (nếu đủ thời gian/thẻ).
3. Loại MapTiler/Stadia Free khỏi mọi thứ chiếu trước khách vì cấm commercial use.
4. Mọi dịch vụ "bill" (Mapbox/Google/Azure) bắt buộc daily quota cap + key riêng demo, xóa key sau 26/11.
5. Không proxy và không cache dài ngày 3D Tiles; 3D luôn load trực tiếp bằng public key giới hạn referrer.
6. Không nhúng CesiumJS vào luồng chính; flyover (nếu có) là tab riêng lazy-load, mặc định tắt.
7. Kiểm tra phủ thực tế (Mapillary quanh 根府川, Google 3D tại corridor) sáng ngày 1 trước khi viết code extra.
8. Chuẩn bị screenshot/video dự phòng cho cảnh wow để demo không phụ thuộc mạng/token tại chỗ.

## OPEN QUESTIONS

1. Phủ Mapillary thực tế quanh 根府川駅 và cầu B-14 có đủ ảnh mới không?
2. Google Photorealistic mesh tại hành lang 3,2 km ven biển có đẹp ở zoom trình diễn không?
3. Có thẻ/billing account nào của công ty dùng được cho Mapbox/Google demo không, và ai phê duyệt?
4. Daily quota cap cụ thể đặt bao nhiêu cho Google 3D (500 hay 1.000 events/ngày)?
5. Máy demo tại chỗ có GPU/RAM chịu nổi tab CesiumJS flyover không?
6. PLATEAU khu 小田原 có phủ đúng đoạn tuyến để thay Google 3D bằng dữ liệu mở không?
7. Domain demo chính thức là gì để khai Allowed URLs/origins/referrers cho key?
8. Khách hàng JR có quy định chụp màn hình/loại bản đồ nền nào được phép xuất hiện trong tài liệu sau demo không?
