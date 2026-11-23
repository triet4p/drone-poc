# 01 — Nghiên cứu dữ liệu cho kiểm tra đường sắt

## 1. Phạm vi nghiên cứu

Ngày kiểm tra nguồn: 20-11-2026. Mục tiêu là dữ liệu thực cho một cầu bê tông, một cửa hầm và một mái dốc; triển khai nội bộ, GPU tùy chọn. Tài liệu này là kế hoạch thu thập, không khẳng định đã có dữ liệu, đã bay hoặc đã đo hiệu năng. Phân biệt biến trạng (変状), kết quả phát hiện và đánh giá sức khỏe (判定区分); kỹ sư có thẩm quyền xác nhận, mọi thao tác có nhật ký. Con số thiết kế, chi phí và thời gian chưa đo đều ghi [推定]. Phiên bản được kiểm tra theo trang phát hành chính thức, không coi bản nightly là ổn định.

## 2. Findings

### 2.1. Chuẩn Nhật: đường bộ là tham khảo, không phải quy định đường sắt

| Nguồn | Phạm vi và điều cần áp dụng |
|---|---|
| [Danh mục hướng dẫn MLIT](https://www.mlit.go.jp/road/sisaku/yobohozen/yobohozen.html) | Đường bộ: 道路橋定期点検要領 và 道路トンネル定期点検要領, bản 3/2024; tài sản do quốc gia quản lý: 橋梁定期点検要領 7/2024, sửa 14/3/2025; 道路トンネル定期点検要領 9/2024, sửa 14/10/2025. Không tự áp nghĩa vụ đường bộ cho đường sắt. |
| [Báo cáo JTSB, bảng 8–9](https://jtsb.mlit.go.jp/railway/rep-acci/RA2025-4-1.pdf) | Chuẩn đường sắt được báo cáo mô tả A gồm AA, B, C, S cho kiểm tra chung; A1/A2 là phân loại chi tiết qua kiểm tra cá biệt. AA khẩn cấp; A1 cần xử lý sớm; A2 cần xử lý vào thời điểm thích hợp; B theo dõi nguy cơ thành A; C biến trạng nhẹ; S lành mạnh. Cần lấy quy trình và từ điển mã cụ thể của khách hàng. |
| [Hướng dẫn cầu](https://www.mlit.go.jp/road/sisaku/yobohozen/tenken/yobo7_6.pdf), [hầm](https://www.mlit.go.jp/road/sisaku/yobohozen/tenken/yobo7_7.pdf) | Phân loại và biểu mẫu hư hại phụ thuộc cấu kiện và vật liệu: nứt (ひびわれ), bong/vỡ (剥離・剥落), lộ cốt thép (鉄筋露出), gỉ (腐食), thấm/rò nước (漏水・遊離石灰), biến dạng, hư hại khác. Cầu/hầm đường bộ dùng sức khỏe I–IV, không đồng nhất hoặc ánh xạ máy móc sang AA/A1/A2/B/C/S. |

[Danh mục kỹ thuật hỗ trợ kiểm tra (点検支援技術性能カタログ)](https://www.mlit.go.jp/road/sisaku/inspection-support/zenbun.html), bản cầu/hầm 3/2026, gồm đo ảnh (画像計測), kiểm tra không phá hủy (非破壊検査), đo/giám sát (計測・モニタリング), và thu thập/truyền dữ liệu (データ収集・通信). Danh mục có mục tiêu chuẩn, bản mô tả từng kỹ thuật, phiếu kiểm chứng phụ lục 2 và phương pháp thử phụ lục 3. [Chương 1](https://www.mlit.go.jp/road/sisaku/inspection-support/pdf/02.pdf) phân biệt **性能値** là giá trị lý thuyết hoặc thử nghiệm do nhà phát triển công bố trong điều kiện của họ, với **標準試験値** là kết quả thử tái lập dưới điều kiện chung; có thể không có thử chuẩn, không được trình bày như chứng nhận. [Phụ lục 3](https://www.mlit.go.jp/road/sisaku/inspection-support/pdf/27.pdf) nêu các phép thử nứt, bong/lộ thép, vị trí ảnh trực giao, màu và tốc độ; hầm có thêm nứt bị bồ hóng che hoặc lấp.

Quan trọng: chính [chương 1](https://www.mlit.go.jp/road/sisaku/inspection-support/pdf/02.pdf) loại AI tự động chẩn đoán dựa trên đánh giá chủ quan của chuyên gia khỏi phạm vi danh mục; không hứa rằng bộ phân loại 判定区分 sẽ được đăng. Phần đo ảnh và lập báo cáo có thể thuộc phạm vi nếu đáp ứng điều kiện liên quan. Để thuyết phục khách hàng: mô tả cảm biến, phần mềm, phiên bản, khoảng cách, chiếu sáng, đối tượng, giới hạn nhìn thấy, sai số và thời gian; so sánh mẫu chuẩn có kích thước biết trước với đo thực tế, lưu cả trường hợp bỏ sót, sai và dữ liệu gốc; chạy thử hiện trường và báo cáo riêng dữ liệu đường sắt. Cung cấp ma trận điều kiện hoạt động, bằng chứng AI theo lớp/độ rộng, khoảng tin cậy, hiệu chuẩn và xét duyệt kỹ sư. Không tuyên bố tương đương 近接目視 hoặc thay thế gõ/nghe, sờ, đo sâu và kiểm tra nội bộ mà chưa được khách hàng chấp thuận.

### 2.2. Bộ dữ liệu thực và quyền sử dụng

Quyết định “demo” dưới đây bao gồm trình chiếu cho khách hàng thương mại **và** huấn luyện trọng số dùng trong sản phẩm. Quyền truy cập công khai không đồng nghĩa quyền thương mại. Luôn lưu phiên bản, URL, giấy phép, tác giả và checksum khi tải; giấy phép ảnh không tự cấp quyền cho trọng số của bên thứ ba.

| Bộ dữ liệu, nguồn | Kích thước, nhãn | Giấy phép; demo | Chênh lệch miền |
|---|---|---|---|
| [SDNET2018](https://digitalcommons.usu.edu/all_datasets/48/) | Hơn 56.000 crop 256×256 từ 230 ảnh gốc; nhãn nứt/không nứt mức crop. Cầu mặt sàn, tường, mặt đường. | CC BY 4.0; **có**, ghi nguồn; không có mask hay tọa độ cấu kiện. | Mỹ, chủ yếu bề mặt dân dụng/đường; không đại diện cảnh UAV đường sắt ban đêm. |
| [Concrete Crack Images for Classification](https://data.mendeley.com/datasets/5y9wdsg2zt/1) | 40.000 crop 227×227, cân bằng nhị phân, từ 458 ảnh gốc của tòa nhà METU. | CC BY 4.0; **có**, ghi nguồn; chỉ phân loại. | Bê tông tòa nhà, không có ngữ cảnh cầu/hầm hay đo độ rộng. |
| [MCDS bản Bikit](https://github.com/phiyodr/building-inspection-toolkit/blob/master/details/mcds.md) | Bản lọc 2.597 ảnh đa nhãn mức ảnh: nứt, bong vỡ, cốt thép lộ, vết gỉ, muối và khác; số lượng không suy rộng sang bản gốc. | [Bản gốc Zenodo](https://zenodo.org/records/2601506) không ghi rõ quyền toàn bộ ảnh đa nguồn; **không** dùng demo/huấn luyện thương mại nếu chưa được cấp quyền từng nguồn. | Cầu, nhiều nguồn và điều kiện chụp; không đại diện ánh sáng đêm đường sắt. |
| [CODEBRIM](https://github.com/MrtnMndt/meta-learning-CODEBRIM), [thống kê](https://cdn.datasetninja.com/codebrim) | 1.590 ảnh cầu độ phân giải cao; hộp cho nứt, bong, lộ thép, muối, gỉ; có vùng nền và đa nhãn. | [Điều khoản riêng](https://zenodo.org/records/2620293/files/license.md): chỉ nghiên cứu/giáo dục phi thương mại; hạn chế ảnh và dẫn xuất. **Không** demo thương mại hoặc huấn luyện sản phẩm nếu không có cấp phép khác. | Cầu thực nhưng môi trường, góc và ánh sáng khác; hộp không đo bề rộng nứt. |
| [CrackForest CFD](https://github.com/cuilimeng/CrackForest-dataset) | 118 ảnh mặt đường và ground truth; mask nứt. | Chỉ nghiên cứu phi thương mại; **không** demo thương mại nếu chưa có phép. | Nhựa đường đô thị, không phải bê tông hầm/cầu. |
| [DeepCrack](https://github.com/yhlleo/DeepCrack) | 537 ảnh nhiều cảnh, mask nhị phân thủ công; train/test. | Ảnh và bản đồ nhãn chỉ nghiên cứu/giáo dục phi thương mại; **không** demo thương mại. | Vật liệu và chụp nhiều miền; không xác nhận điều kiện đêm đường sắt. |
| [CTCD](https://huggingface.co/datasets/shiweiluo99/tunnel-crack-segmentation-dataset/blob/main/README.md) | 292 crop 256×256, mask pixel, 52 hầm đường bộ Trung Quốc, xe kiểm tra. | Tác giả ghi CC BY 4.0; **có**, ghi nguồn. | Có lớp phủ hầm nhưng không phải đường sắt, UAV hoặc thấm nước. |
| [UAV-Tunnel / TunnelScan](https://www.sciencedirect.com/science/article/pii/S0886779825002688), [kho tác giả](https://github.com/KerouacDlg/TunnelScan) | Bài báo mô tả nứt, rò nước, bong và bu lông; số ảnh và gói ảnh tải được chưa xác minh. | Kho hiện không nêu giấy phép ảnh hay cung cấp rõ tập ảnh; **không** dùng cho tới khi có quyền và dữ liệu. | UAV trong hầm có ích, nhưng không chứng minh đường sắt Nhật/ánh sáng hiện trường. |
| [Landslide4Sense](https://huggingface.co/datasets/ibm-nasa-geospatial/Landslide4sense) | 3.799 patch train, 245 validation, 800 test; mask trượt đất đa phổ vệ tinh, độ phân giải khoảng 10 m. | Quyền cụ thể của bản tải và dữ liệu nguồn chưa xác minh; **không** đưa vào demo thương mại cho tới khi làm rõ. | Mái dốc quy mô vệ tinh; không đại diện nứt/lưới bảo vệ ở khoảng cách UAV. |

Không có bộ nào ở trên chứng minh ảnh điểm rơi nước, rỉ thép, lộ thép hoặc mái dốc **của khách hàng** có quyền thương mại và phù hợp điều kiện đêm. Thu ảnh tự sở hữu hoặc được khách hàng cấp phép bằng văn bản. Hai bộ classification chỉ cho nhãn toàn crop; không biến thành ground truth segmentation. Tách train/validation/test theo cấu trúc/ảnh gốc và chuyến bay, không tách ngẫu nhiên crop cùng ảnh: ví dụ đề xuất [推定] 70/15/15 theo công trình, giữ riêng toàn bộ ảnh đêm hiện trường để đánh giá, không tuyên bố tổng quát từ một cầu.

### 2.3. Cỡ pixel, cự ly và chất lượng ảnh

Với mặt gần vuông góc, GSD = H × p / f = H × S_w / (f × N_w), cùng đơn vị; H là khoảng cách camera–bề mặt, p pitch, f tiêu cự thực, S_w chiều rộng cảm biến và N_w số pixel ngang. Đây là xấp xỉ pinhole, không phải độ chính xác đo [Pix4D](https://support.pix4d.com/hc/en-us/articles/202559809). Với p = 0,004 mm và f = 20 mm: H = 5 m → 1 mm/px; 2 m → 0,4 mm/px; 0,5 m → 0,1 mm/px; 0,2 m → 0,04 mm/px. Đây là ví dụ thiết kế, không phải thông số một drone đã chọn. Nghiêng, méo, độ sâu trường ảnh và crop làm GSD thay đổi theo vị trí.

| Nhiệm vụ | Thiết kế đề nghị [推定] | Hệ quả |
|---|---|---|
| Ảnh từng cấu kiện (部材単位) | Ảnh tĩnh gốc, p=4 µm, f=20 mm, H khoảng 2–5 m → 0,4–1 mm/px; chụp mỗi mặt dầm/trụ/mố, cửa hầm, mái dốc; ảnh vuông góc và xiên, ID bảng tên. | Liên kết cấu kiện và biến trạng lớn; không hứa phát hiện nứt 0,2 mm. |
| Ảnh cận tiếp (近接) | Mục tiêu ≤0,1 mm/px cho sàng lọc nứt 0,2 mm, ≤0,04 mm/px cho thử đo, tương ứng 2 và 5 pixel ngang; cầm tay hoặc ống tele được phép nếu UAV không thể giữ an toàn. Đặt thước nứt cùng mặt phẳng; kiểm tra khoảng lấy nét tối thiểu thực tế. | Hai hay năm pixel chỉ là mục tiêu lấy mẫu, không bảo đảm phát hiện/đo; thử mẫu có vết nứt biết bề rộng, trên ảnh gốc và cả vùng tối [nghiên cứu GSD và biên nứt](https://pmc.ncbi.nlm.nih.gov/articles/PMC6111740/). |
| Video toàn cảnh (全景) / 3D | [推定] H 3–8 m theo khoảng trống an toàn, video gốc 4K kèm ảnh tĩnh gốc; chọn frame đủ nét, ít trùng, bao phủ các mặt và góc; ảnh tĩnh vẫn là dữ liệu 3D ưu tiên. Lập kế hoạch chồng dọc ≥80%, ngang ≥70%, tăng cho bề mặt lặp/ít texture. | Video nén/rolling shutter không thay ảnh cận; thiếu thị sai hoặc mặt bị che sẽ không tái tạo. Không dùng mesh để đo nứt nhỏ. |

[ODM](https://docs.opendronemap.org/map-accuracy/) khuyến nghị tối thiểu 5 GCP (標定点) phân bố cả biên, giữa, cao/thấp; mỗi điểm nhìn thấy ít nhất 3 ảnh, nên 5. Đề nghị [推定] thêm ≥3 điểm kiểm tra độc lập không đưa vào điều chỉnh, đo bằng toàn đạc trong hệ tọa độ khách hàng, mục tiêu bất định khảo sát ≤5 mm nếu hiện trường cho phép. Đây là mục tiêu, không phải chuẩn phổ quát; đo residual từng trục và lưu RMS/max, phân bố điểm và mốc độ cao. Có GCP vẫn không tăng độ phân giải nứt; không có điểm kiểm tra thì ghi sai số chưa xác định.

Nhòe do chuyển động xấp xỉ số pixel = vận tốc tương đối trên mặt × thời gian phơi sáng / GSD. Mục tiêu [推定] ≤0,5 pixel: tại 0,1 mm/px và 1/1000 s, vận tốc mặt ≤0,05 m/s; 0,2 m/s cần ≤1/4000 s. Hover, chụp liên tiếp và chọn ảnh bằng thước mẫu; rung góc, lấy nét và rolling shutter vẫn có thể làm ảnh hỏng. Đèn chiếu đêm cố định, tán quang và một góc xiên bổ sung, tránh lóa bê tông ướt, bóng đổ, nhấp nháy và thay đổi màu; lưu thời gian phơi sáng, ISO, khẩu độ và bố trí đèn. Tăng ISO không thể bù ảnh mất nét. Không bay gần đường ray hoặc tiếp cận 0,2 m nếu chưa được đơn vị vận hành phê duyệt khoảng cách, chiếm dụng đường (線路閉鎖) và an toàn.

### 2.4. Trắc địa ảnh và khả năng kiểm chứng

[ODM](https://docs.opendronemap.org/map-accuracy/) mô tả tương đối 1–3 GSD, GPS thường ngang 2–6 m, có GCP khoảng 2,5 GSD ngang/4 GSD đứng trong điều kiện tài liệu nêu; đây chỉ là kỳ vọng, không phải nghiệm thu cho cầu hẹp, dưới dầm, GNSS kém. Muốn so hai kỳ: dùng cùng hệ tọa độ, cùng điểm mốc ổn định, đăng ký trên vùng không đổi và giữ điểm kiểm tra độc lập. Ước lượng sai số từng kỳ và sai số đăng ký từ residual; nếu độc lập, xấp xỉ sai số chênh lệch là căn tổng bình phương, nếu có tương quan phải báo riêng. Hiển thị dải sai số và “không xác định” khi thiếu dữ liệu; chỉ gắn cờ thay đổi khi vượt ngưỡng đã thống nhất, không gọi nhiễu là hư hỏng. [ODM hỗ trợ căn chỉnh đa thời kỳ](https://docs.opendronemap.org/map-accuracy/) nhưng bản thân căn chỉnh không chứng minh thay đổi thật.

### 2.5. Xe kiểm tra đường ray (検測車) và pháp lý

Chưa có dữ liệu 検測車. Yêu cầu khách hàng cung cấp dữ liệu theo thời gian và キロ程, hướng tuyến, track ID, gauge/cao thấp/mặt bằng theo cột và đơn vị thực tế, mốc đo, lịch hiệu chuẩn, phiên bản định nghĩa, chất lượng, quyền dùng và ít nhất hai kỳ nếu có; không suy diễn cấu trúc từ tên cột. Ghép theo tuyến, hướng và chuỗi mốc do khách hàng xác nhận, không chỉ theo GPS. Nếu không có: ẩn lớp hoặc ghi “データ未提供”, vẫn cho xem cấu kiện/ảnh và chuỗi キロ程 xác nhận thủ công; không sinh số đo giả, không tuyên bố tương quan hạ tầng–đường ray.

[Quốc thổ địa lý GSI](https://www.gsi.go.jp/KOUKYOU/koukyo0032.html) phân biệt đo đạc công cộng theo chủ thể, kinh phí, mục đích và điều kiện luật, không chỉ vì sử dụng drone. Dự án nội bộ không tự động được miễn mọi thủ tục; xác nhận với khách hàng và GSI về 公共測量, việc dùng kết quả đo cơ bản/công cộng, hồ sơ và quyền sao chép. [GSI về dữ liệu địa không gian và thông tin cá nhân](https://www.gsi.go.jp/common/000252137.pdf) và [ủy ban bảo vệ thông tin cá nhân](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/) yêu cầu xét khả năng nhận diện trong ngữ cảnh thực tế; ảnh gần/xiên có thể thấy người, biển số. Được phép bay, bảo đảm an toàn đường sắt và các thủ tục hàng không riêng trước khi bay; không suy ra được phép bay từ giấy phép đo đạc. Theo hợp đồng: mục đích, chủ sở hữu, truy cập, mã hóa tại chỗ, cấm xuất mạng, sao lưu, lưu giữ/xóa, xử lý lộ diện, phương án dùng để huấn luyện và quyền trình chiếu. Chỉ phát hành bản che mặt/biển số đã duyệt; giữ bản gốc hạn chế quyền để kiểm chứng. Đây không thay tư vấn pháp lý.

## 3. Bảng so sánh phương án

| Phương án | Ưu | Nhược | Chi phí/công sức | Rủi ro |
|---|---|---|---|---|
| [ODM 3.6.2](https://github.com/OpenDroneMap/ODM/releases/tag/v3.6.2) | Linux, xử lý CPU; [LAZ/PLY, mesh OBJ và orthophoto GeoTIFF](https://docs.opendronemap.org/sw/outputs/); GCP, căn chỉnh. | Tối ưu bản đồ, mặt đứng/dưới cầu cần thử; GeoTIFF không mặc nhiên là COG. | Miễn phí; AGPL-3.0 [license](https://github.com/OpenDroneMap/ODM/blob/master/LICENSE); [推定] 30–180 phút/100 ảnh CPU. | Tuân thủ AGPL và phụ thuộc; kiểm tra output, tự chuyển GeoTIFF sang COG và kiểm tính hợp lệ. |
| [WebODM](https://github.com/WebODM/WebODM) | UI quản lý ảnh; self-host. | [Thông báo tách dự án/backend](https://webodm.org/blog/announcement/) làm phiên bản/backend cần kiểm tra, không mặc định đồng nhất ODM. | Miễn phí/cài đặt; xem quyền từng thành phần; [推定] 30–180 phút nếu cùng engine, không gồm upload. | Kiểm tra offline, license và backend trước chốt; không khóa kiến trúc theo tên sản phẩm. |
| [Metashape Professional 2.3.2](https://www.agisoft.com/downloads/installer/) | Linux, công cụ quản lý ảnh/GCP và xuất sản phẩm hoàn chỉnh; [manual](https://www.agisoft.com/downloads/user-manuals/). | Độc quyền, phải xác nhận kích hoạt air-gap và tính năng phiên bản mua. | [Giá niêm yết](https://www.agisoft.com/buy/online-store/) Professional 3.499 USD, chưa gồm thuế; [推定] 20–120 phút/100 ảnh. | Kiểm tra xuất LAS/LAZ, orthophoto GeoTIFF theo edition; COG cần kiểm tra/chuyển. |
| [COLMAP 4.2.1](https://github.com/colmap/colmap/releases/tag/4.2.1) | BSD, Linux, tái tạo SfM và MVS; kiểm soát sâu. | Sparse SfM có thể chạy CPU, dense MVS chuẩn cần CUDA; không coi toàn pipeline là CPU-only. PLY/mesh cần pipeline bổ sung cho LAS/LAZ, orthophoto và COG. | Không phí license; [推定] 30–180 phút/100 ảnh với GPU và xử lý bổ sung. | Công sức tích hợp, georeference, chuyển định dạng và kiểm tra tăng. [FAQ](https://colmap.github.io/faq.html). |
| [RealityCapture / RealityScan](https://rshelp.capturingreality.com/en-US/tools/export.htm) | Xuất LAS/PLY; [orthophoto TIFF](https://rshelp.capturingreality.com/en-US/tutorials/orthophoto_export.htm). | Không xác minh hỗ trợ Linux native hoặc kích hoạt hoàn toàn offline; COG/LAZ cần kiểm tra hoặc chuyển. | [Giá/cấp phép được Epic công bố 2024](https://forums.unrealengine.com/t/realitycapture-1-4-is-now-available/1817369): 1.250 USD/user/năm trên ngưỡng doanh thu nêu trong thông báo; phải xin báo giá hiện hành. [推定] 15–90 phút/100 ảnh GPU. | Không chọn cho một máy Linux/offline nếu chưa xác nhận hợp đồng và nền tảng. |
| [CVAT 2.83.0](https://github.com/cvat-ai/cvat/releases/tag/v2.83.0) | Tự host, ảnh/video, polygon/mask; [mã và MIT](https://github.com/cvat-ai/cvat). | Vận hành, sao lưu, cấu hình quyền. | Miễn phí bản cộng đồng; [推定] 2 người gán và 1 kỹ sư phân xử. | Thành phần phụ thuộc có license riêng; chức năng theo edition cần kiểm tra. |
| [Label Studio 1.23.2](https://github.com/HumanSignal/label-studio/releases/tag/1.23.2) | Apache-2.0, tự host, linh hoạt [repo](https://github.com/HumanSignal/label-studio). | [Release notes](https://github.com/HumanSignal/label-studio/releases/tag/1.23.2): chính sách SSRF có thể bỏ ảnh từ địa chỉ mạng nội bộ khi export; phải cấu hình an toàn và kiểm kết quả. | Miễn phí bản mã nguồn mở; công cấu hình nhãn. | Không tắt toàn bộ bảo vệ chỉ để cho export chạy; dùng allowlist phù hợp. |

Thời gian trên chỉ là **[推定] kế hoạch**, không phải benchmark: 100 ảnh 20 MP, overlap tốt, 16 lõi CPU, RAM 64 GB, SSD; hàng GPU giả định thêm RTX 4090 24 GB. Kết quả thực phụ thuộc preset, độ phân giải, mặt đứng, ánh sáng và I/O; cần đo riêng sau khi có dữ liệu, không so sánh như thí nghiệm chuẩn.

## 4. Khuyến nghị

Chọn ODM 3.6.2 chạy CPU trên Linux làm đường dựng 3D mặc định, xử lý trước cuộc họp; GPU là tùy chọn, không bắt buộc. Chọn CVAT Community 2.83.0 cho annotation nội bộ; Label Studio 1.23.2 là phương án dự phòng. Chọn Metashape Professional nếu ODM không tái tạo được mặt dưới cầu sau thử nghiệm thật và điều khoản cấp phép offline được duyệt. Khởi tạo bộ mẫu bằng SDNET2018, Concrete Crack Images và CTCD theo CC BY; dùng ảnh tự chụp/khách hàng có quyền làm dữ liệu chính cho demo. Những bộ hạn chế hoặc quyền không rõ không đi vào bản trình diễn và trọng số thương mại.

[推定] Cấu hình 16 lõi, 64 GB RAM, SSD 2 TB, bản sao lưu mã hóa ngoài máy; dự trù ≥200 GB trống cho ảnh gốc, bản trung gian và nhiều kỳ. Không có dữ liệu thật thì không điền tọa độ, cấp độ hoặc lịch sử giả. Dữ liệu thời tiết/lịch đóng đường phải có nguồn và thời điểm chốt, nếu chưa có thì đánh dấu chưa xác nhận thay vì tự tạo điều kiện vận hành thực.

## 5. Đặc tả MVP

### 5.1. Kế hoạch thu thập và phụ thuộc

Mọi số lượng là **[推定] mức tối thiểu thiết kế**, không phải số lượng hiện có hay đảm bảo đủ thống kê. Mỗi kỳ tối thiểu có tổng quan và cận tiếp, cả ảnh không hư hỏng và hư hỏng thật nếu phát hiện; không cố ý tạo hư hại cho công trình.

| Hạng mục | Nguồn | License/quyền | Công sức [推定] | Chặn tính năng nào |
|---|---|---|---|---|
| Lịch, cửa sổ 線路閉鎖, giới hạn bay, dự báo thời tiết kèm thời điểm | Khách hàng và cơ quan khí tượng được phép | Xác nhận điều khoản và lưu trong mạng | 0,5–1 ngày phối hợp | Màn lập lịch/chụp: không có thì chưa xác nhận lịch. |
| Mã cầu/trụ/dầm/mố, hầm, mái dốc, キロ程, tuyến, sơ đồ | Khách hàng | Cấp phép nội bộ bằng văn bản | 0,5–2 ngày | Dải dọc, ID 部材, report. |
| Ảnh cầu/hầm/dốc | Bay/chụp tại địa điểm tự sở hữu hoặc khách hàng cho phép | Quyền chụp, huấn luyện, demo, lưu trữ và che thông tin | 1–2 ngày/site sau phê duyệt | Màn kế hoạch ảnh, AI, ảnh gốc, báo cáo. |
| Dữ liệu 3D 100–200 ảnh cầu; thêm 50–100 ảnh mỗi hầm/dốc | Tự chụp theo spec, đủ mặt, GCP và ≥3 checkpoint | Quyền tương tự ảnh; đo mốc được phép | 1–2 ngày khảo sát + [推定] 0,5–1 ngày xử lý mỗi site | Màn 3D/vị trí; không có thì hiện ảnh 2D, không giả điểm mây. |
| 50–100 ảnh cận/site, gồm ảnh nền và biến trạng nếu có | Tự chụp hoặc khách hàng | Đồng ý bằng văn bản | 1–2 ngày gán + phân xử [推定] | AI ứng viên, xác nhận, nháp 調書. |
| Hai kỳ ảnh/GCP cùng công trình; hồ sơ bảo trì thật | Khách hàng; kỳ mới tự chụp | Cho phép đối chiếu và hiển thị | Tùy quyền và lịch sử | Màn thay đổi/ưu tiên: nếu chỉ một kỳ thì hiển thị chưa đủ kỳ, không bịa biến đổi. |
| Nhãn đường sắt, biểu mẫu 調書 và hạng | Khách hàng | Nội bộ, bản được duyệt | 0,5–2 ngày đối chiếu | Phân loại, mức ưu tiên và xuất nháp theo quy trình khách hàng. |
| 検測車 | Khách hàng | Nội bộ; xin cả từ điển và hiệu chuẩn | Không xác định | Lớp tương quan đường ray; thiếu thì không có lớp. |
| Ảnh công khai SDNET/CCIC/CTCD | Tác giả [SDNET](https://digitalcommons.usu.edu/all_datasets/48/), [CCIC](https://data.mendeley.com/datasets/5y9wdsg2zt/1), [CTCD](https://huggingface.co/datasets/shiweiluo99/tunnel-crack-segmentation-dataset/blob/main/README.md) | CC BY 4.0, ghi nguồn | 0,5 ngày tải, kiểm checksum, phân nhóm | Thử nhãn/phân loại; không thay ảnh công trình khách hàng. |

Năm nhóm màn hình và bằng chứng: (1) lịch + kế hoạch chụp cần cửa sổ, thời tiết và danh mục ảnh; (2) AI + kỹ sư cần ảnh thật, nhãn, confidence và nhật ký; (3) 3D + dải キロ程 cần ảnh chồng, GCP/checkpoint, bộ phận và tuyến; (4) thay đổi + ưu tiên cần hai kỳ cùng vị trí và sai số hoặc hiện chưa đủ dữ liệu; (5) 調書 nháp cần bản ghi kỹ sư, ảnh, nguồn và mẫu được duyệt. Không hứa đủ điều kiện vận hành chỉ từ bộ ảnh công khai.

### 5.2. Quy trình và bảng nhãn

1. Nhận quyền bằng văn bản; chốt mã tuyến, cấu kiện, CRS, mốc cao độ, điều kiện an toàn và ẩn dữ liệu nhận diện. Đồng bộ đồng hồ camera/telemetry, ghi độ lệch.
2. Khảo sát an toàn; đo GCP và checkpoint; chụp ảnh toàn cấu kiện, ảnh cận có thước, ảnh chồng nhiều góc, video tổng quan. Kiểm tra ngay độ nét, lóa, độ phủ, thông tin phơi sáng và tính nhìn thấy của mốc.
3. Lưu nguyên bản bất biến kèm SHA-256; ghi metadata, đồng bộ telemetry theo timestamp với sai số thời gian; liên kết キロ程 bằng mốc tuyến được khách hàng kiểm. Không gán tọa độ khi không đủ độ tin cậy.
4. Gán nhãn độc lập, phân xử, xuất phiên bản cố định; dựng cloud/orthophoto, đo checkpoint; nhập vào ứng dụng. Kỹ sư kiểm tra từng ứng viên, chỉ sau xác nhận mới đưa vào báo cáo nháp.

| Trường nhãn | Kiểu / giá trị | Quy tắc |
|---|---|---|
| `class` | `crack`, `spalling`, `exposed_rebar`, `rust`, `leakage`, `efflorescence`, `slope_instability`, `other` | Đa nhãn khi cùng vị trí; định nghĩa tiếng Nhật và ví dụ từng lớp phải được kỹ sư ký duyệt. Không phân loại vết ẩm là rò nước chắc chắn khi không đủ bằng chứng. |
| `geometry` | mask/polygon; polyline nứt; box khi chỉ có nhãn thô | Pixel ảnh gốc, kèm kích thước ảnh; lưu hình học độc lập theo phiên bản, không giả mask từ box. |
| `member_id`, `image_id` | ID khóa ngoại | Không biết thì null và đưa vào hàng chờ; một ảnh có thể thấy nhiều 部材. |
| `severity_scheme`, `severity` | `rail_operator_vX`, `AA/A1/A2/B/C/S` hoặc null | Chỉ kỹ sư theo quy định khách hàng; null là chưa đánh giá, không phải S. Có thể lưu A tổng quát theo bước kiểm tra. |
| `occluded`, `uncertain` | boolean + lý do | Vùng bị che hoặc không xác định không được biến thành ảnh âm tính. |
| `width_mm`, `width_uncertainty_mm` | nullable, số và phương pháp | Chỉ ghi khi đã hiệu chuẩn cùng mặt phẳng; ghi GSD cục bộ, thước tham chiếu và bất định. |
| `annotator`, `reviewer`, `time`, `revision` | ID, UTC, phiên bản | Lưu hai annotation độc lập cùng quyết định phân xử; tuyệt đối không ghi đè lịch sử. |
| `confidence`, `model_version`, `source` | nullable, số, version/hash, `human`/`model` | Confidence là điểm mô hình, không phải xác suất đã hiệu chuẩn nếu chưa chứng minh; nhãn người không cần điểm giả. |

QA [推定]: hai người gán độc lập ít nhất 20% ảnh, chọn phân tầng theo cấu kiện, lớp, đêm, khu vực bị che và ảnh âm tính; trường hợp hiếm lấy toàn bộ để phân xử. Ghép đối tượng theo ảnh, lớp, IoU hoặc khoảng cách polyline đã chốt; báo độ đồng thuận lớp bằng Cohen κ, tỉ lệ đồng thuận thô kèm ma trận nhầm lẫn, IoU mask và bỏ sót theo lớp; với nứt mảnh thêm sai số biên theo pixel, không dùng IoU duy nhất. Kỹ sư thứ ba phân xử khác biệt, lưu cả hai bản và lý do; đặt ngưỡng chấp nhận cùng khách hàng trước khi đánh giá, không giả ngưỡng là quy định MLIT. Đo riêng mỗi kỳ và công trình; không dùng ảnh chưa thấy làm âm tính chỉ vì thiếu nhãn.

### 5.3. Sketch lưu trữ cho kiến trúc

Dùng file bất biến trong kho nội bộ, bảng quan hệ giữ ID và metadata. Khóa ngoại nullable khi không biết; mọi tọa độ phải có hệ trục, datum độ cao, đơn vị và phương pháp. Một ảnh có thể chứa nhiều cấu kiện, một khuyết tật có nhiều quan sát; không nhét quan hệ đó vào một chuỗi filename.

| Bảng | Các trường tối thiểu / quan hệ |
|---|---|
| `asset` | `id, type, name, line_id, km_start_m, km_end_m, crs, source, validity` — cầu, cửa hầm, mái dốc. |
| `member` | `id, asset_id, parent_id, type, name, km_m, geometry_ref, coordinate_uncertainty_m`. |
| `survey` | `id, asset_id, epoch, captured_at_utc, operator, possession_ref, weather_ref, crs, vertical_datum, calibration_ref`. |
| `media` | `id, survey_id, uri, sha256, media_type, original_filename, captured_at_utc, timezone_source, time_uncertainty_ms, width_px, height_px, camera_id, lens_focal_mm, pixel_pitch_um, exposure_s, iso, lighting, license_ref`. Video thêm frame timecode/frame index; ảnh gốc giữ EXIF. |
| `pose` | `media_id, x,y,z, crs, yaw,pitch,roll, frame_convention, pose_source, uncertainty, timestamp_offset_ms`; nguồn EXIF/GNSS/gimbal/SfM phân biệt; thiếu thì null. |
| `media_member` | `media_id, member_id, assignment_method, evidence, reviewer, confidence`; gán thủ công hoặc chiếu tia lên mesh, lưu phương pháp và không đồng nhất GPS drone với vị trí nứt. |
| `route_reference` | `line_id, direction, track_id, km_m, x,y,z, crs, source, uncertainty_m, approved_by, version`; nội suy có kiểm chứng giữa mốc và lưu sai số. |
| `control_point` | `survey_id, point_id, role` GCP/checkpoint, `x,y,z, crs, survey_method, uncertainty, observations, residual`; điểm kiểm tra không tham gia fitting. |
| `reconstruction` | `survey_id, software_version, parameters, inputs_hash, cloud_uri, mesh_uri, orthophoto_uri, crs, checkpoint_metrics, coverage, status`. LAZ/GeoTIFF lưu gốc; COG chỉ sau chuyển và kiểm định. |
| `defect` / `observation` | `defect_id, member_id`; `observation_id, defect_id, survey_id, media_id, class, geometry, position_3d, uncertainty, occluded, uncertain, width_mm, confidence, model_hash`. Phép chiếu 2D–3D cần calibration và pose; không có tương ứng đáng tin thì để null. |
| `judgement_event` | `id, observation_id, actor_id, action, prior_state, new_state, rank_scheme, rank, reason, timestamp_utc, input_hash`; append-only, có thể sửa qua sự kiện tiếp theo, không xóa dấu vết. |
| `change_comparison` | `observation_a, observation_b, alignment_method, stable_area, error_a, error_b, registration_error, threshold, conclusion, reviewer`; thiếu bất định thì `indeterminate`. |
| `report_draft` | `id, template_version, source_observation_ids, judgement_event_ids, author, generated_at, status`; chỉ nháp, sau xác nhận bởi kỹ sư. |

## 6. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu / điều kiện dừng |
|---|---|
| Không đủ nét tại 0,2 mm | Dùng ảnh cận an toàn, thước chuẩn và thử hiện trường; không báo số nếu không đủ GSD hoặc sai số chưa biết. |
| Thiếu vùng dưới dầm/hầm tối | Đánh dấu vùng chưa quan sát; điều chỉnh góc, đèn, phương tiện tiếp cận được duyệt; không suy ra không có hư hại. |
| Dataset công khai bị nhầm quyền | Chỉ dùng CC BY đã kiểm và giữ citation; các bộ không rõ/phi thương mại bị cách ly khỏi demo và huấn luyện thương mại. |
| Mẫu quá ít và cùng một công trình | Tách theo kỳ/cấu kiện, báo n và khoảng tin cậy, không tuyên bố độ chính xác tổng quát; tiếp tục kiểm chứng tại địa điểm khác. |
| Sai キロ程 hoặc sai lệch hai kỳ | Dùng route_reference có phiên bản, checkpoint độc lập và dải sai số; không hiển thị thay đổi định lượng khi thiếu căn chỉnh. |
| Áp chuẩn đường bộ lên đường sắt | Hiển thị nguồn/rank scheme; chờ khách hàng phê chuẩn từ điển 判定区分 và mẫu báo cáo. |
| Tài liệu công khai hoặc ảnh khách hàng rời mạng | Không CDN, không cloud; kiểm soát quyền, mã hóa, sao lưu và audit; lọc PII trước xuất. |

## 7. Câu hỏi cho khách hàng

1. Công trình nào được chọn; sơ đồ và danh sách 部材, tuyến, hướng, キロ程, hệ tọa độ và mốc cao độ nào là bản có thẩm quyền?
2. Lịch 線路閉鎖, vùng cấm bay, quy trình xin phép tiếp cận, giới hạn chiếu sáng và an toàn điện là gì?
3. Có ảnh gốc, điểm mây, GCP/checkpoint, bản vẽ và ít nhất hai kỳ hồ sơ được cấp quyền dùng cho demo không?
4. Quy trình phân loại 変状, định nghĩa AA/A1/A2/B/C/S, tiêu chí ưu tiên và mẫu 点検調書 cụ thể là gì? Ai ký quyết định?
5. Có dữ liệu 検測車 và từ điển cột, đơn vị, hướng tuyến, hiệu chuẩn, quyền truy cập và thời gian không?
6. Độ rộng nứt cần phát hiện/đo, sai số vị trí, ngưỡng thay đổi và phạm vi kiểm tra hiện trường nào là đủ chấp nhận?
7. Quyền lưu, gán nhãn, huấn luyện nội bộ, trình chiếu, thời hạn xóa và xử lý khuôn mặt/biển số được cho phép đến đâu?
8. Hạ tầng offline có cho dùng gói AGPL, giấy phép phần mềm thương mại và phần cứng lưu trữ/đo mốc không?

## 8. References & Web Sources

Các liên kết gắn ngay tại từng bảng/khẳng định ở trên là danh mục nguồn đầy đủ; nguồn cốt lõi và bối cảnh truy cập:

- [MLIT — bản hướng dẫn kiểm tra và các sửa đổi](https://www.mlit.go.jp/road/sisaku/yobohozen/yobohozen.html): đối chiếu phiên bản và phạm vi đường bộ.
- [MLIT — danh mục kỹ thuật 3/2026](https://www.mlit.go.jp/road/sisaku/inspection-support/zenbun.html), [chương 1](https://www.mlit.go.jp/road/sisaku/inspection-support/pdf/02.pdf), [phụ lục 3](https://www.mlit.go.jp/road/sisaku/inspection-support/pdf/27.pdf): phạm vi, giá trị và thử chuẩn.
- [JTSB — đánh giá sức khỏe kết cấu đường sắt](https://jtsb.mlit.go.jp/railway/rep-acci/RA2025-4-1.pdf): phân biệt A/AA/A1/A2/B/C/S.
- [SDNET2018](https://digitalcommons.usu.edu/all_datasets/48/), [Concrete Crack Images](https://data.mendeley.com/datasets/5y9wdsg2zt/1), [CTCD](https://huggingface.co/datasets/shiweiluo99/tunnel-crack-segmentation-dataset/blob/main/README.md): kích thước, loại nhãn và CC BY.
- [MCDS gốc](https://zenodo.org/records/2601506), [MCDS bản lọc](https://github.com/phiyodr/building-inspection-toolkit/blob/master/details/mcds.md), [CODEBRIM terms](https://zenodo.org/records/2620293/files/license.md), [CrackForest](https://github.com/cuilimeng/CrackForest-dataset), [DeepCrack](https://github.com/yhlleo/DeepCrack): giới hạn quyền và nguồn.
- [GSD Pix4D](https://support.pix4d.com/hc/en-us/articles/202559809), [nghiên cứu sai số đo nứt](https://pmc.ncbi.nlm.nih.gov/articles/PMC6111740/), [ODM độ chính xác/GCP/đa kỳ](https://docs.opendronemap.org/map-accuracy/): thiết kế chụp, không phải bảo đảm nghiệm thu.
- [GSI về 公共測量](https://www.gsi.go.jp/KOUKYOU/koukyo0032.html), [GSI về dữ liệu cá nhân](https://www.gsi.go.jp/common/000252137.pdf), [PPC hướng dẫn chung](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/): điều kiện pháp lý cần xác nhận.
