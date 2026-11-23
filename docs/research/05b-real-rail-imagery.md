# Ảnh thực tế của tuyến đường sắt thật (実線区の実写画像) — có lấy miễn phí được không?

> Ngôn ngữ: tiếng Việt; thuật ngữ gốc tiếng Nhật trong ngoặc đơn. Mọi khẳng định về giấy phép, hạn mức, URL đều kèm link nguồn. Số liệu không kiểm chứng trực tiếp được đánh dấu `[推定]`.

## 1) Phạm vi (範囲・スコープ)

**Mục tiêu:** trả lời "ảnh ưu tiên có thể lấy chính từ các đường ray thực tế đó được không" — tức là tìm ảnh miễn phí, dùng được cho demo thương mại (商用デモ), chụp đúng hành lang demo (根府川/Nebukawa — 早川/Hayakawa–真鶴/Manazuru thuộc 東海道本線, bbox [推定] 35.18–35.23, 139.13–139.15), để hiển thị trong app kiểm tra và hỗ trợ review của AI.

**Phân biệt hai nhu cầu khác nhau:**

| Nhu cầu | Yêu cầu ảnh | Nguồn mở có đáp ứng? |
|---|---|---|
| A. Bối cảnh tuyến thật (実線区コンテキスト): dải ảnh dọc hành lang, nhà ga, cầu — tạo niềm tin "đây là tuyến thật" | Góc rộng, chụp từ đường bộ/ga, độ phân giải thường | **Có** — Wikimedia Commons + GSI + Mapillary |
| B. Review khuyết tật (変状レビュー): nứt (ひび割れ), bong tróc (剥落), cốt thép lộ (鉄筋露出) ở cự ly gần để AI/ người chấm | Cự ly 0.5–3 m, thấy chi tiết mm–cm | **Không** — không nguồn mở nào có |

**Ngoài phạm vi:** geometry 3D của hành lang (thuộc báo cáo module geometry song song); pipeline phát hiện nứt hiện tại (CrackForest). Báo cáo này không phải tư vấn pháp lý (法的助言ではない); bảng license cần pháp chế xác nhận trước khi dùng thương mại.

---

## 2) Findings (調査結果)

### 2.1 Mapillary (Meta) — nguồn ảnh đường phố chính

**API (API v4):** hai bề mặt — entity endpoint `https://graph.mapillary.com` và vector tiles `https://tiles.mapillary.com` ([API Documentation](https://www.mapillary.com/developer/api-documentation/)).

**Token (トークン取得, đã kiểm chứng trang docs):** mọi request tới cả hai endpoint đều **bắt buộc token**. Token lấy từ `https://mapillary.com/dashboard/developers` (client token), gửi qua header `Authorization: OAuth XXX` cho Entity API hoặc `?access_token=XXX` cho tiles; docs **khuyên mạnh không** nhúng user token vào URL ([Authentication](https://www.mapillary.com/developer/api-documentation/)). Quy trình: tạo app trên dashboard → nhận client ID/secret → (nếu cần quyền user) OAuth 2.0 authorization-code flow qua `GET https://www.mapillary.com/connect`, đổi code lấy token qua `POST https://graph.mapillary.com/token` ([OAuth 2.0](https://www.mapillary.com/developer/api-documentation/)). Thời gian [推定]: ~15–30 phút nếu đã có tài khoản Meta/Facebook.

**Truy vấn quanh tuyến (đã kiểm chứng changelog 2026 trong docs):**

- **Image Radius Search** (thêm 02/04/2026): tìm ảnh quanh 1 điểm bằng `lat` + `lng` + `radius` (**tối đa 50 m**), `limit` tối đa 100; không kết hợp với `bbox` ([Changelog](https://www.mapillary.com/developer/api-documentation/)). → Đúng công cụ cho "buffer 50–100 m quanh tim tuyến": chia tim tuyến OSM thành điểm mỗi ~80 m, gọi radius search từng điểm.
- **Ràng buộc bbox** (từ 16/01/2026): truy vấn `bbox` vào `/images` phải **nhỏ hơn 0.01 độ vuông**; vùng lớn hơn phải dùng tiles hoặc [mapillary-python-sdk](https://github.com/mapillary/mapillary-python-sdk) ([Changelog](https://www.mapillary.com/developer/api-documentation/)).
- Fields trả về gồm `id, captured_at, geometry, compass_angle, thumb_*_url, sequence, is_pano, creator` ([API Documentation](https://www.mapillary.com/developer/api-documentation/), [API Demo](https://github.com/mapillary/api-demo)); ví dụ:

```bash
curl -G 'https://graph.mapillary.com/images' \
  -H 'Authorization: OAuth MAPILLARY_CLIENT_TOKEN' \
  --data-urlencode 'lat=35.2027' --data-urlencode 'lng=139.1385' \
  --data-urlencode 'radius=50' --data-urlencode 'limit=50' \
  --data-urlencode 'fields=id,captured_at,geometry,compass_angle,thumb_1024_url,sequence,is_pano'
```

**Hạn mức (レート制限):** docs chi tiết yêu cầu đăng nhập nên không kiểm chứng trực tiếp được; diễn đàn ghi nhận **vector-tile requests giới hạn 50.000/ngày** (reset 24 h), lỗi throttle đôi khi trả về HTML với HTTP 200 thay vì JSON ([forum thread](https://forum.mapillary.com/t/receiving-html-response-instead-of-json/8336)). Diễn đàn cũ (2022) từng nêu 50.000 requests/phút/app cho Graph API ([thread](https://forum.mapillary.com/t/hitting-request-limit/5820)) — con số này **cũ, không dùng làm căn cứ** [推定]. Thực tế cho corridor 3,2 km (~40 điểm radius search) làTraffic rất nhỏ, không đáng lo [推定].

**License (ライセンス, đã kiểm chứng):** mọi ảnh Mapillary chia sẻ dưới **CC BY-SA 4.0** — được xem, phân phối, sửa đổi nhẹ **kể cả thương mại**, với điều kiện ghi công ([CC-BY-SA license](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data)). Mẫu attribution chuẩn của hãng:

> *"[Title]" <Link to Mapillary image> by "[username]" <Link to user profile>, licensed under [CC-BY-SA](https://creativecommons.org/licenses/by-sa/4.0/).*

Điểm ShareAlike (継承条件): chỉ **ảnh phái sinh (adapted image) đem phân phối lại** mới phải giữ CC BY-SA; không "lây" sang toàn bộ app/website — CC chỉ cấp phép bản quyền ảnh, không bao gồm quyền nhân thân/thương hiệu xuất hiện trong ảnh ([CC BY-SA 4.0 Legal Code §3(b)](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en)). Thực tế cho demo: hiển thị ảnh + crop/resize + ghi công là đủ; **không được** re-license ảnh Mapillary (kể cả đã crop) thành độc quyền.

**Coverage đường sắt Nhật (鉄道カバレッジ):** Mapillary là crowdsource từ đường bộ — **không có bản đồ phủ riêng cho đường ray**. Kiểm tra không cần token: mở bản đồ web [Mapillary App](https://www.mapillary.com/app/?lat=35.2027&lng=139.1385&z=14) hoặc [API Demo](https://mapillary.github.io/api-demo/) zoom vào 根府川, xem vệt xanh (sequence) rồi bấm vào từng ảnh đối chiếu. Nhận định [推定]: sẽ có ảnh dọc 国道135号・県道740号 chạy song song tuyến và quanh ga — tức **nhìn thấy hành lang từ bên cạnh**, chứ không có ảnh cự ly gần trên ray (đứng trên đường ray chụp là xâm phạm đường sắt, contributor không làm vậy).

### 2.2 KartaView (旧OpenStreetCam, Grab)

- API ảnh: `GET https://api.openstreetcam.org/2.0/photo/?lat=..&lng=..&radius=..`, chi tiết sequence qua `.../2.0/sequence/?sequenceId=..` rồi tải `fileUrl` ([KartaView Docs FAQ](https://kartaview.org/doc/faq), [Docs](https://kartaview.org/doc/)); thường **không cần token** cho truy vấn ảnh lẻ.
- License: **CC BY-SA 4.0**, credit bắt buộc `"© Grab and KartaView Contributors"` ([Terms](https://kartaview.org/terms), [OSM Wiki](https://wiki.openstreetmap.org/wiki/KartaView)). Muốn bulk/offline dataset thì đăng ký qua [Open Imagery](https://kartaview.org/landing/open-imagery).
- Coverage Nhật: thưa hơn Mapillary nhiều [推定] — coi là nguồn dự phòng, kiểm tra trực tiếp trên bản đồ [kartaview.org](https://kartaview.org/) quanh bbox demo trước khi viết code.

### 2.3 Wikidata / Wikimedia Commons (ウィキメディア・コモンズ) — nguồn tốt nhất cho demo 26/11

**Đã kiểm chứng trực tiếp bằng API:** geosearch bán kính 3 km quanh ga 根府川 (35.2027, 139.1385) trả về **30+ file**; riêng trong vòng ~50 m quanh ga có 7 file; truy vấn dọc tuyến phía nam (35.19, 139.135) cho thấy ảnh rải dọc hành lang. Cách truy vấn (không cần key/token):

```
https://commons.wikimedia.org/w/api.php?action=query&list=geosearch
  &gscoord=35.2027|139.1385&gsradius=3000&gslimit=50&gsnamespace=6&format=json
```

Metadata + license từng file (máy đọc được, dùng cho attribution tự động):

```
https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo
  &iiprop=user|url|size|extmetadata&titles=File:...&format=json
```

(`extmetadata` chứa `LicenseShortName, UsageTerms, LicenseUrl, Artist, GPSLatitude/GPSLongitude` — đã kiểm chứng trả về đầy đủ.)

**Category chính:** [Category:Nebukawa Station](https://commons.wikimedia.org/wiki/Category:Nebukawa_Station) — **47 file** (sân ga, biển tên, view biển), thuộc [Stations of Tōkaidō Main Line (JR East)](https://commons.wikimedia.org/wiki/Category:Stations_of_T%C5%8Dkaid%C5%8D_Main_Line_%28JR_East%29). Ảnh chụp **trên tuyến** (tàu chạy giữa các ga) nằm rải trong các category tàu/cầu — tìm bằng search `Nebukawa railway` (14 hits, đã kiểm chứng) thay vì duyệt category.

**6 file ứng viên đã kiểm chứng license/tọa độ (toàn bộ là ảnh thật của tuyến/ga):**

| # | File (URL) | Nội dung | Phân giải / ngày | License (đã kiểm chứng extmetadata) |
|---|---|---|---|---|
| 1 | [185 hayanebu.jpg](https://commons.wikimedia.org/wiki/File:185_hayanebu.jpg) | Tàu 185系 特急踊り子 chạy **giữa Hayakawa–Nebukawa**, trên cầu 白糸川 (Shiraitogawa Bridge) | 4857×3217, 25/10/2020 | **CC0** (không cần ghi công) |
| 2 | [Ef65 freight.jpg](https://commons.wikimedia.org/wiki/File:Ef65_freight.jpg) | Tàu hàng đầu máy EF65 **giữa Nebukawa–Manazuru**, cầu 白糸川 | 2592×1800, chụp 10/12/1982 | **CC0** |
| 3 | [JRE EC211 Tokaido Ishibashiyama.jpg](https://commons.wikimedia.org/wiki/File:JRE_EC211_Tokaido_Ishibashiyama.jpg) | Tàu 211系 chạy **giữa Hayakawa–Nebukawa**, cầu 玉川 (Tamagawa Bridge) | 1280×960, 24/02/2010 | **Public Domain** (không cần ghi công) |
| 4 | [Nebukawa-STA Home2-3.jpg](https://commons.wikimedia.org/wiki/File:Nebukawa-STA_Home2-3.jpg) | Sân ga 2–3番線 根府川駅 | 5472×3648, 20/03/2022 | **CC BY-SA 4.0**, MaedaAkihiko |
| 5 | [Nebukawa Station platforms Dec 20 2021 02-35PM.jpeg](https://commons.wikimedia.org/wiki/File:Nebukawa_Station_platforms_Dec_20_2021_02-35PM.jpeg) | Sân ga, GPS 35.202469, 139.138472 | 4032×3024, 20/12/2021 | **CC BY 4.0**, Nesnad |
| 6 | [Nebukawa Station platforms July 5 2020.jpeg](https://commons.wikimedia.org/wiki/File:Nebukawa_Station_platforms_July_5_2020.jpeg) | Sân ga, GPS 35.202931, 139.138961 | 4025×3021, 05/07/2020 | **CC BY 4.0**, Nesnad |

Tải gốc: `https://upload.wikimedia.org/...` (trường `url` trong imageinfo) hoặc shortcut `https://commons.wikimedia.org/wiki/Special:FilePath/<tên file>?width=1280` cho thumbnail đúng cỡ.

### 2.4 GSI シームレス空中写真 / 国土変遷アーカイブ (地理院空中写真)

- **全国最新写真（シームレス）**: tile `https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg`, zoom ảnh z14–18 ([仕様](https://maps.gsi.go.jp/development/siyou.html), [一覧](https://maps.gsi.go.jp/development/ichiran.html)). GSD ở z18 ≈ **0.5 m/px** tại vĩ độ demo [推定 — toán Web Mercator chuẩn].
- License: nhóm "基本測量成果以外で出典の記載のみで利用可能なもの" — **ghi nguồn là dùng được, kể cả thương mại, realtime không cần thủ tục**; nguồn ghi `"国土地理院" / "地理院タイル"` + link tới [一覧](https://maps.gsi.go.jp/development/ichiran.html); một số vùng dùng ảnh GRUS thì ghi thêm `© Axelspace` ([一覧](https://maps.gsi.go.jp/development/ichiran.html), [利用規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)). **Tái phân phối/cache thành dataset độc lập có thể cần thủ tục 測量法** — demo hiển thị realtime thì không vướng.
- **国土変遷アーカイブ** (ảnh các thời kỳ 1945–: [年代別の写真 trong 一覧](https://maps.gsi.go.jp/development/ichiran.html)): giá trị là **so sánh biến遷 (trước/sau)** ven tuyến, không phải chi tiết kết cấu.
- **Không được khẳng định:** GSD 0.5 m **không thể** thấy nứt/bong tróc/cốt thép; crop GSI chỉ dùng làm "bối cảnh tuyến thật" (vị trí cầu/hầm trên ảnh hàng không), không bao giờ gắn nhãn "ảnh kiểm tra".

### 2.5 Các nguồn khác (その他) — loại nhanh

| Nguồn | Dùng được cho demo thương mại? | Lý do |
|---|---|---|
| MLIT 国土数値情報 N02 (鉄道データ) | **Được** — vector tuyến/ga, **CC BY 4.0** từ bản 2020 ([N02-2025](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html), [利用規約](https://nlftp.mlit.go.jp/ksj/other/agreement.html)) | Là **dữ liệu tuyến**, không phải ảnh — dùng để vẽ tim tuyến chuẩn hơn OSM |
| Ảnh báo chí JR東日本 (プレスリリース・報道写真) | **Không** | Bản quyền đóng (all rights reserved) [推定 — site JR không có điều khoản mở]; muốn dùng phải xin phép/nhờ khách hàng cung cấp |
| YouTube / X / SNS ảnh đường sắt (鉄道写真) | **Không** | Mặc định bản quyền thuộc người đăng; điều khoản nền tảng không chuyển quyền tái sử dụng ([YouTube Terms](https://www.youtube.com/t/terms)) — nhúng player thì được, tải về chiếu trong demo thì không |
| Google Street View | **Hạn chế nặng** | Chỉ hiển thị **live qua API có billing**, giữ attribution; **cấm tải/cache/tái phân phối/screenshot** ([Street View Policies](https://developers.google.com/maps/documentation/streetview/policies)); xe Street View cũng không vào hành lang ray [推定] → loại cho offline, yếu cho online |
| OpenRailwayMap | **Được** — overlay vector, ODbL/OSM | Không phải ảnh; dùng làm lớp hạ tầng đường ray ([openrailwaymap.org](https://www.openrailwaymap.org/)) |
| Dataset ảnh đường sắt ML (chung chung, không phải tuyến này) | Tùy license | Không phải "ảnh tuyến thật" — loại khỏi báo cáo này |

### 2.6 Kiểm chứng thực địa quanh corridor (35.18–35.23, 139.13–139.15)

| Nguồn | Đếm được (đã kiểm chứng) | Đánh giá |
|---|---|---|
| Commons trong 3 km quanh ga | **30+ file** (geosearch API); 7 file trong 50 m | Đủ làm dải context + ảnh ga/cầu |
| Commons ảnh **trên tuyến** Hayakawa–Nebukawa–Manazuru | **14 hits** search, ≥3 file CC0/PD cự ly hành lang | File #1–#3 ở §2.3 là bằng chứng |
| Mapillary quanh tuyến | Chưa đếm (cần token cho API; bản đồ web xem không cần đăng nhập) | Phải kiểm tra bằng mắt trên [Mapillary App](https://www.mapillary.com/app/?lat=35.2027&lng=139.1385&z=14) trước khi code; kỳ vọng [推定]: có ảnh đường bộ ven tuyến, không có close-up ray |
| KartaView quanh tuyến | Chưa đếm | Kiểm tra trên [kartaview.org](https://kartaview.org/) song song |
| GSI seamlessphoto | Phủ toàn quốc, gồm cả corridor | Chắc chắn có; GSD ~0.5 m |

---

## 3) Bảng so sánh (比較表)

| Nguồn | Coverage tuyến demo | Phân giải thực | License | Geotag | Demo thương mại | Effort tích hợp [推定] |
|---|---|---|---|---|---|---|
| **Commons CC0/PD** (tàu trên tuyến) | Ảnh thật đúng đoạn Hayakawa–Nebukawa–Manazuru | 1–16 MP (file #1: 4857×3217) | CC0 / Public Domain — **không cần ghi công** (khuyến nghị vẫn ghi) | Có/không tùy file | ✅ tốt nhất, zero friction | 0.5 ngày (geosearch → chọn tay → cache) |
| **Commons CC BY / BY-SA** (ga, sân ga) | Ga 根府川 + ven tuyến | 12–20 MP | CC BY 4.0 / BY-SA 4.0 — **ghi công bắt buộc** | Có (GPS WGS-84) | ✅ + thanh attribution | 0.5 ngày (chung pipeline trên) |
| **GSI seamlessphoto** | Phủ 100% corridor | ~0.5 m/px | Ghi nguồn GSI + link 一覧 (GRUS: +© Axelspace) | Tile xyz (tự suy tọa độ) | ✅ realtime | ~0 (đã có trong 04a) |
| **Mapillary** | Đường bộ ven tuyến [推定], không close-up ray | 2–12 MP street-level [推定] | CC BY-SA 4.0 + attribution chuẩn hãng | Có (lat/lng, compass, captured_at) | ✅ + proxy token + attribution | 1–2 ngày (token, proxy, dedupe, km-map) |
| **KartaView** | Thưa [推定] | Tương tự street-level | CC BY-SA 4.0, credit Grab/KartaView | Có | ✅ | 0.5 ngày nếu coverage đủ, else bỏ |
| MLIT N02 | Tuyến vector chuẩn | — (không phải ảnh) | CC BY 4.0 | Tuyến/ga | ✅ | 0.5 ngày (thay/cặp với OSM) |
| Street View / JR press / SNS | — | — | Đóng / cấm tái phân phối | — | ❌ loại | 0 |

---

## 4) Khuyến nghị (推奨ミックス)

**Cho demo 26/11 (không cần token, không rủi ro license):**

1. **6 file Commons §2.3** làm "dải ảnh tuyến thật": file CC0/PD (#1–#3) cho cảnh tàu trên cầu giữa đúng đoạn tuyến; file ga (#4–#6) cho điểm neo 根府川駅. Cache thumbnail 1280px trong `frontend/public/rail/` + attribution bar.
2. **GSI seamlessphoto** làm nền context (đã có từ 04a) — crop corridor kèm disclaimer "ảnh hàng không bối cảnh, không phải ảnh kiểm tra".
3. Khung pipeline Mapillary (proxy + km-map + UI) viết sẵn nhưng **chạy với dữ liệu mẫu/thủ công** nếu token chưa về kịp; bật live ngay khi có token.

**Cho MVP (sau demo):**

1. Hoàn thiện Mapillary live: server-side token proxy → radius search dọc tim tuyến → dải context ảnh ven tuyến có timestamp/la bàn, mỗi ảnh link về trang Mapillary gốc.
2. Giữ nguyên tắc: **ảnh defect phục vụ AI review chỉ lấy từ drone/khách hàng chụp** — ảnh mở chỉ làm context và định vị.
3. Xin khách hàng: (a) ảnh drone cận cảnh các cầu/hầm tương đương B-14/T-07; (b) giấy phép dùng ảnh tư liệu JR東日本 nếu muốn ảnh tuyến "chính chủ".

---

## 5) Kiến trúc / đặc tả module (パイプライン仕様)

```
OSM/N02 alignment → buffer 50–100 m → query (Mapillary radius / Commons geosearch)
  → dedupe (sequence/id + 画像ハッシュ) → download (thumb + gốc)
  → map to km (最近傍投影 lên tim tuyến) → store + attribution
  → serve (server proxy, token chỉ ở server) → display (thanh attribution)
```

**Đặc tả từng bước:**

1. **Alignment (基準線):** dùng tim tuyến từ `data/rail_osm.json` (67 ways 東海道本線, đã có); MVP cân nhắc thay bằng MLIT N02 cho chuẩn (CC BY 4.0).
2. **Buffer → query:** tim tuyến resample mỗi ~80 m; mỗi điểm gọi Mapillary radius 50 m (`lat,lng,radius,limit≤100`) hoặc gom bbox < 0.01°²; Commons gọi 1 lần geosearch `gsradius=3000` rồi lọc trong buffer bằng shapely [推定] (thư viện nội bộ đã có hay chưa do module geometry quyết).
3. **Dedupe:** giữ 1 ảnh/sequence (`sequence_id`), ưu tiên gần tim nhất + mới nhất + `is_pano=false` cho thumbnail (pano để riêng cho view 360°); Commons dedupe theo pageid.
4. **Download:** Mapillary `thumb_1024_url` cho xem nhanh + URL gốc cho zoom; Commons `Special:FilePath?...?width=1280/2560`. Chỉ tải thứ đã chọn, tôn trọng cache.
5. **Map to km:** chiếu gần nhất lên tim tuyến → gán km tuyến (cùng hệ km 12k400–15k600 của demo); ảnh ngoài buffer ghi `km=NULL + khoảng cách`.
6. **Store attribution (bắt buộc mỗi record):** `{source, file_url/page_url, author, license, license_url, captured_at, lat, lng, km}` — render **mọi nơi hiển thị ảnh**.
7. **Serve:** token Mapillary **chỉ nằm server** (proxy `/api/real-imagery/*`); client không bao giờ thấy token (đồng nhất quy tắc 04a: không nhúng token thương mại vào client).

**Chuỗi attribution mẫu (dán trực tiếp vào UI):**

- CC0: `185系 特急「踊り子」早川–根府川間 (白糸川橋梁), 2020-10-25 — CC0 (Public Domain), via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:185_hayanebu.jpg)`
- PD: `211系 早川–根府川間 (玉川橋梁), 2010-02-24 — Public Domain, via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:JRE_EC211_Tokaido_Ishibashiyama.jpg)`
- CC BY 4.0: `根府川駅ホーム, 2021-12-20, © [Nesnad](https://commons.wikimedia.org/wiki/User:Nesnad), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), via [Commons](https://commons.wikimedia.org/wiki/File:Nebukawa_Station_platforms_Dec_20_2021_02-35PM.jpeg)`
- CC BY-SA 4.0: `根府川駅2・3番線ホーム, 2022-03-20, © [MaedaAkihiko](https://commons.wikimedia.org/wiki/User:MaedaAkihiko), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), via [Commons](https://commons.wikimedia.org/wiki/File:Nebukawa-STA_Home2-3.jpg)`
- Mapillary: `"[title]" ([image link]) by [username] ([profile link]), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).`
- GSI: `出典：国土地理院「[地理院タイル（全国最新写真（シームレス））](https://maps.gsi.go.jp/development/ichiran.html)」(＋該当範囲のみ © Axelspace)`

---

## 6) Kế hoạch (2 ngày vs MVP)

**2 ngày cho demo 26/11 (1 người, không token):**

| Ngày | Việc | Xong khi |
|---|---|---|
| 1 sáng | Chạy Commons geosearch bbox demo, chọn 8–12 file (ưu tiên CC0/PD + ga), tải thumbnail 1280px | Có thư mục ảnh + file `attribution.json` |
| 1 chiều | Component "dải ảnh tuyến thật": carousel theo km + thanh attribution + disclaimer bối cảnh | Chạy được trong app, mọi ảnh đều có nguồn |
| 2 sáng | Mắt kiểm Mapillary/KartaView trên bản đồ web quanh corridor; nếu phủ tốt → xin token (dashboard developers) | Biết có/không coverage; token đang về (nếu có) |
| 2 chiều | Khung proxy + km-map chạy với dữ liệu mẫu; GSI crop corridor; viết disclaimer + docs | Demo kể được câu chuyện "tuyến thật", code MVP tái dùng |

**MVP (sau demo, [推定] 4–6 ngày công):** token Mapillary → proxy server → radius search toàn tuyến → dedupe → km-map → UI context strip + link gốc; thay tim OSM bằng N02 nếu cần; xin ảnh drone cận cảnh từ khách; pháp chế duyệt bảng license.

---

## 7) Rủi ro (リスク)

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Hiểu nhầm ảnh context thành "ảnh kiểm tra" trước khách | Cao | Disclaimer cố định + tách tab "tuyến thật (bối cảnh)" vs "ảnh kiểm tra (drone)" |
| ShareAlike: re-license ảnh Mapillary/CC BY-SA Commons thành độc quyền | Trung bình | Attribution bar bắt buộc; không gắn license khác lên ảnh phái sinh khi phân phối lại |
| Token Mapillary lộ ra client | Trung bình | Chỉ server giữ token; quy tắc đã chốt ở 04a |
| Coverage Mapillary/KartaView ven tuyến quá thưa | Trung bình | Đã có Commons + GSI độc lập token; kiểm tra bằng mắt trước khi code |
| Tái phân phối tile GSI (cache thành dataset) vướng 測量法 | Thấp (demo realtime) | Demo chỉ realtime + ghi nguồn; offline tính sau, xin phép khi cần |
| Ảnh Commons cũ (1982/2010) bị hỏi "sao dùng ảnh cũ" | Thấp | Ghi rõ ngày chụp; ảnh cũ dùng cho cầu/đoạn tuyến (kết cấu ít đổi), ảnh ga dùng bản 2020–2022 |

---

## 8) References (参考文献・URL一覧)

- Mapillary API Documentation (auth, radius search ≤50 m, bbox <0.01°², OAuth/token): https://www.mapillary.com/developer/api-documentation/
- Mapillary CC BY-SA license + mẫu attribution: https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data
- Mapillary API access (help center): https://help.mapillary.com/hc/en-us/articles/360010234680-Accessing-imagery-and-data-through-the-Mapillary-API
- Mapillary App (kiểm coverage không cần đăng nhập): https://www.mapillary.com/app/?lat=35.2027&lng=139.1385&z=14
- Mapillary API Demo: https://mapillary.github.io/api-demo/
- Mapillary Python SDK: https://github.com/mapillary/mapillary-python-sdk
- Mapillary tile rate-limit report (50.000/ngày): https://forum.mapillary.com/t/receiving-html-response-instead-of-json/8336
- CC BY-SA 4.0 Legal Code (§3(b) ShareAlike): https://creativecommons.org/licenses/by-sa/4.0/legalcode.en
- KartaView Docs / FAQ: https://kartaview.org/doc/ — https://kartaview.org/doc/faq
- KartaView Terms (CC BY-SA + credit): https://kartaview.org/terms
- KartaView Open Imagery (bulk): https://kartaview.org/landing/open-imagery
- KartaView (OSM Wiki): https://wiki.openstreetmap.org/wiki/KartaView
- Category:Nebukawa Station (47 files): https://commons.wikimedia.org/wiki/Category:Nebukawa_Station
- Stations of Tōkaidō Main Line (JR East): https://commons.wikimedia.org/wiki/Category:Stations_of_T%C5%8Dkaid%C5%8D_Main_Line_%28JR_East%29
- File:185 hayanebu.jpg (CC0): https://commons.wikimedia.org/wiki/File:185_hayanebu.jpg
- File:Ef65 freight.jpg (CC0): https://commons.wikimedia.org/wiki/File:Ef65_freight.jpg
- File:JRE EC211 Tokaido Ishibashiyama.jpg (PD): https://commons.wikimedia.org/wiki/File:JRE_EC211_Tokaido_Ishibashiyama.jpg
- File:Nebukawa-STA Home2-3.jpg (CC BY-SA 4.0): https://commons.wikimedia.org/wiki/File:Nebukawa-STA_Home2-3.jpg
- File:Nebukawa Station platforms Dec 20 2021 (CC BY 4.0): https://commons.wikimedia.org/wiki/File:Nebukawa_Station_platforms_Dec_20_2021_02-35PM.jpeg
- File:Nebukawa Station platforms July 5 2020 (CC BY 4.0): https://commons.wikimedia.org/wiki/File:Nebukawa_Station_platforms_July_5_2020.jpeg
- Commons API geosearch (toạ độ→file): https://www.mediawiki.org/wiki/Extension:GeoData#API
- GSI 地理院タイル一覧 (seamlessphoto, 年代別写真, điều khoản): https://maps.gsi.go.jp/development/ichiran.html
- GSI 仕様 (zoom/merator): https://maps.gsi.go.jp/development/siyou.html
- GSI コンテンツ利用規約: https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html
- MLIT N02 鉄道データ (CC BY 4.0): https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html
- MLIT 国土数値情報 利用規約: https://nlftp.mlit.go.jp/ksj/other/agreement.html
- Google Street View Policies (cấm tải/tái phân phối): https://developers.google.com/maps/documentation/streetview/policies
- YouTube Terms (bản quyền người đăng): https://www.youtube.com/t/terms
- OpenRailwayMap: https://www.openrailwaymap.org/

---

## KEY DECISIONS

1. **Đủ ảnh tuyến thật cho demo: YES cho bối cảnh, NO cho defect** — verdict chính của báo cáo.
2. Demo 26/11 dùng **6 file Commons đã kiểm chứng (CC0/PD/BY/BY-SA) + GSI seamlessphoto**, không cần token.
3. Mapillary là nguồn street-level duy nhất đáng đầu tư (CC BY-SA 4.0, radius search 50 m), qua **server-side token proxy**.
4. KartaView chỉ là dự phòng — kiểm tra coverage trước, bỏ nếu thưa.
5. Loại **Street View, ảnh JR press, SNS** khỏi demo thương mại vì license.
6. Mọi ảnh hiển thị phải có **attribution bar** theo chuỗi mẫu §5 (ghi cả ngày chụp).
7. Tách UI thành hai tab: **"tuyến thật (bối cảnh)"** vs **"ảnh kiểm tra (drone)"** + disclaimer cố định.
8. Ảnh defect cho AI review long-term **chỉ từ drone/khách hàng** — ghi thành yêu cầu gửi khách từ demo.

## OPEN QUESTIONS

1. Mắt kiểm Mapillary quanh corridor cho coverage thực tế thế nào (ai làm, khi nào)?
2. Token Mapillary đăng ký bằng tài khoản nào của team (Meta account + developers dashboard)?
3. Pháp chế chốt bảng license (đặc biệt ShareAlike khi crop/overlay bbox AI lên ảnh CC BY-SA)?
4. Overlay bbox AI lên ảnh CC BY-SA rồi phân phối có tính là Adapted Material phải giữ BY-SA không?
5. Tim tuyến MVP dùng OSM hiện có hay chuyển MLIT N02?
6. Khách hàng có cung cấp ảnh drone cận cảnh + ảnh tư liệu JR không, timeline nào?
7. Cache thumbnail Commons trong repo có cần tuân thêm điều khoản nào ngoài license file?
8. KartaView coverage quanh corridor có đủ để viết integration không?
