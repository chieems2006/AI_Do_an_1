# ĐỒ ÁN 1: TRỢ LÝ MUA SẮM ĐA PHƯƠNG THỨC
## Visual Search và Product QA

> **Ghi chú về nguồn:** Không tìm thấy file có tên chính xác `Bao_cao_day_du_thu_thap_du_lieu_Visual_Search_Product_QA.docx` trong workspace. Hiện có hai bản `BAO_CAO_TONG_HOP.docx` ở thư mục gốc và thư mục dự án; chúng có nội dung giống hệt nhau. Báo cáo này tổng hợp từ `MSA/MSA_DoAn1_HoanChinh/BAO_CAO_TONG_HOP.md` và các tài liệu chuyên đề của dự án. Những chỗ được ghi **“đề xuất bổ sung”** là phân tích để hoàn thiện báo cáo, không phải ngưỡng đã được nhóm đo hoặc chốt.
>
> Các số liệu của dự án chủ yếu được ghi nhận ngày 05/11/2026. Bộ đánh giá và nhãn chưa được người thật duyệt; vì vậy, cần phân biệt số đo trên dữ liệu thật, truy vấn tổng hợp và kết quả do LLM chấm.

### Mục lục

1. [Phần 1: Phương pháp thu thập dữ liệu](#phần-1-phương-pháp-thu-thập-dữ-liệu)
2. [Phần 2: Hệ thống độ đo](#phần-2-hệ-thống-độ-đo-metrics)
3. [Phần 3: Ứng dụng và bài báo tương tự](#phần-3-khảo-sát-ứng-dụng-và-bài-báo-tương-tự)
4. [Căn cứ trong workspace](#căn-cứ-trong-workspace)

---

# PHẦN 1: PHƯƠNG PHÁP THU THẬP DỮ LIỆU

## 1.1. Các phương pháp thường gặp

Bảng dưới đây tổng hợp các phương pháp đã được khảo sát trong dự án và bổ sung phân tích về managed scraping, AI crawlers, synthetic data để bao quát yêu cầu. Mức độ pháp lý cần được kiểm tra theo nguồn, điều khoản dịch vụ và mục đích sử dụng cụ thể.

| Phương pháp | Mô tả | Ưu điểm | Hạn chế, chi phí | Pháp lý và đạo đức |
|---|---|---|---|---|
| **Public API / API chính thức** | Lấy dữ liệu qua API công khai, API affiliate hoặc API đối tác của sàn. | Dữ liệu có cấu trúc; cập nhật tốt; dễ tự động hóa; thường có giới hạn và quyền truy cập được mô tả rõ. | Có thể cần đăng ký, được duyệt tư cách seller/affiliate hoặc trả phí. API dành cho seller có thể chỉ trả về sản phẩm của shop đó; thời gian duyệt khó kiểm soát. | Thường an toàn hơn scraping nếu tuân điều khoản, quota và chính sách lưu trữ. Không mặc định rằng dữ liệu API có thể phát hành lại. |
| **In-house scraping** | Nhóm tự viết chương trình thu thập trang sản phẩm công khai, review, giá và thông tin liên quan. | Có thể lấy dữ liệu tiếng Việt và trường dữ liệu sát nhu cầu như giá, size, mô tả. Nhóm chủ động được phạm vi và schema. | Tốn công phát triển, sửa khi cấu trúc trang đổi; có thể bị chặn, dữ liệu thiếu hoặc không ổn định. Chi phí nhân lực và thời gian cao. | Cần đọc ToS, robots.txt, quy định bảo vệ dữ liệu và giới hạn truy cập. Không nên né biện pháp chặn hoặc dùng proxy/giả lập trình duyệt để vượt kiểm soát. |
| **Managed scraping / dịch vụ scraping thuê ngoài** | Thuê nhà cung cấp thu thập, làm sạch hoặc cung cấp dữ liệu. | Có thể mở rộng nhanh, giảm công vận hành, thường có cơ chế xử lý website thay đổi. | Có phí; khó kiểm soát chính xác nguồn gốc, độ mới và chất lượng; phụ thuộc nhà cung cấp. | Cần thẩm định quyền thu thập, quyền chuyển giao, nguồn dữ liệu, dữ liệu cá nhân và điều khoản tái phân phối. Thuê bên thứ ba không tự động làm cho việc thu thập hợp pháp. |
| **Public dataset** | Tải bộ dữ liệu đã công bố trên kho học thuật hoặc nền tảng như Hugging Face, Kaggle, Zenodo. | Nhanh; thường có schema, nhãn, tài liệu và cách tái lập; phù hợp nghiên cứu và benchmark. | Có thể không khớp miền ứng dụng; thiếu thuộc tính cần thiết; chất lượng và license khác nhau; bản mirror có thể không xác nhận license gốc. | Phải kiểm tra license của cả bản gốc và bản mirror; lưu ý điều kiện phi thương mại, không tạo tác phẩm phái sinh và không phát hành dữ liệu. |
| **AI crawler / browser agent** | Agent dùng trình duyệt, mô hình thị giác-ngôn ngữ hoặc LLM để tìm trang, trích xuất thông tin và chuẩn hóa dữ liệu. | Linh hoạt với trang không đồng nhất; có thể trích xuất trường bán cấu trúc; giảm công viết parser riêng. | Khó bảo đảm tính ổn định và chính xác; có thể trích nhầm, bỏ sót hoặc “điền” dữ liệu không tồn tại. Chi phí mô hình và kiểm tra đầu ra tăng theo quy mô. | Vẫn chịu cùng yêu cầu ToS, robots.txt, bản quyền và quyền riêng tư như thu thập tự động khác. LLM trích xuất không phải bằng chứng rằng dữ liệu là đúng hoặc được phép sử dụng. |
| **Thủ công / crowdsourcing / tự chụp** | Nhóm hoặc người tham gia chụp ảnh thật, gán nhãn sản phẩm và xác nhận ground truth. | Phù hợp để tạo tập kiểm thử gần ảnh người dùng; kiểm soát được hướng dẫn và nhãn; có thể phát hiện domain gap giữa ảnh studio và ảnh đời thực. | Tốn công chụp, gán nhãn và phân xử bất đồng; quy mô nhỏ; có nguy cơ thiên lệch người chụp hoặc vùng miền. | Cần xin phép người chụp/người xuất hiện trong ảnh; che mặt hoặc thông tin cá nhân khi cần; quy định rõ mục đích sử dụng và lưu trữ. |
| **Synthetic data / dữ liệu tổng hợp bằng LLM** | Tạo câu hỏi, câu định tuyến, truy vấn khó hoặc biến đổi ảnh từ dữ liệu có sẵn. | Tạo nhanh nhiều trường hợp; bổ sung câu ngoài phạm vi, câu mơ hồ và tình huống từ chối; hữu ích khi dữ liệu thật ít. | Có thể tạo câu “quá sạch”, phi tự nhiên, sai nhãn hoặc lặp lại; LLM có thể tự tạo thông tin không có trong dữ liệu. Không thay thế được dữ liệu thực tế của người dùng. | Phải ghi rõ nguồn gốc (`origin`), cách tạo và trạng thái kiểm duyệt. Không được coi câu do LLM sinh là ground truth đã được xác nhận. |
| **Mua dataset thương mại** | Mua quyền truy cập dataset từ nhà cung cấp. | Có thể có schema, chất lượng và hỗ trợ tốt; đôi khi dữ liệu sát miền ứng dụng. | Chi phí cao; thời gian lựa chọn nhà cung cấp; có thể bị giới hạn số người dùng, lưu trữ hoặc thời hạn. | Đọc kỹ quyền sử dụng, xử lý dữ liệu cá nhân, quyền phái sinh và quyền phát hành kết quả. |
| **Hợp tác doanh nghiệp** | Xin catalog, review hoặc log từ cửa hàng/đối tác. | Gần dữ liệu triển khai thật; có thể có giá, size, tồn kho và liên kết sản phẩm chính xác. | Đàm phán và tích hợp lâu; phụ thuộc đối tác; nguy cơ dữ liệu bị giới hạn hoặc không đồng nhất. | Cần thỏa thuận quyền sử dụng, bảo mật, xử lý dữ liệu khách hàng và xóa dữ liệu theo yêu cầu. |
| **Crawl công cụ tìm kiếm ảnh** | Lấy ảnh theo từ khóa từ Google/Bing Images hoặc nguồn tương tự. | Có thể nhanh chóng thu được nhiều ảnh đa dạng. | Thiếu metadata đáng tin cậy, giá và review; nhiễu cao; khó tạo ground truth cho ảnh nào ứng với sản phẩm nào. | Bản quyền và quyền tái sử dụng ảnh thường không rõ; không phù hợp nếu không thể xác minh quyền sử dụng. |
| **Dataset cuộc thi / đăng ký** | Đăng ký truy cập dataset hoặc tham gia shared task, ví dụ dataset cần xin quyền. | Có thể có dữ liệu chuyên ngành và giao thức đánh giá chuẩn. | Thời gian duyệt hoặc ký thỏa thuận không kiểm soát được; dữ liệu có thể chỉ dùng trong cuộc thi. | Tuân thủ điều khoản đăng ký và giới hạn nghiên cứu/phát hành. |

## 1.2. Chiến lược lựa chọn của dự án

Dự án có các ràng buộc chính:

- Thời gian thực hiện khoảng **3 tuần**.
- Nhóm có **5 người**, không có thành viên chuyên trách scraping.
- **Không có ngân sách** mua dataset hoặc dịch vụ thu thập dữ liệu.
- Cần ảnh/catalog cho Visual Search và review tiếng Việt cho Product QA.
- Máy thực nghiệm khoảng **2 CPU, 7 GB RAM, không GPU**.
- Cần có khả năng tái lập kết quả và ghi rõ license.

### Chiến lược được chọn

1. **Dùng public dataset làm nguồn chính** cho catalog và ảnh Visual Search.
2. **Dùng dataset review tiếng Việt học thuật** để xây kho tri thức Product QA thay cho crawl sàn.
3. **Dùng ảnh tự chụp làm tập kiểm thử ảnh đời thực**, không thay dữ liệu huấn luyện/catalog.
4. **Dùng câu hỏi viết tay hoặc LLM sinh làm dữ liệu đánh giá bổ sung**, có ghi `origin` và cần kiểm duyệt.
5. Không dùng LLM hoặc AI crawler để tự “bịa” metadata sản phẩm; câu trả lời của hệ thống phải được ràng buộc bởi bằng chứng trong catalog/review.

### Vì sao không chọn các phương pháp khác?

| Phương pháp không được chọn ở lượt này | Lý do theo dự án |
|---|---|
| Crawl sàn TMĐT Việt Nam | Thử nghiệm ghi nhận Tiki trả **HTTP 403** từ IP cloud; Shopee không kết nối được và URL ảnh bị chặn. Không dùng proxy xoay vòng hoặc giả lập trình duyệt để vượt chặn do rủi ro ToS. |
| API chính thức của sàn | Có thể cần tư cách seller/đối tác và thời gian duyệt; API seller có thể giới hạn ở shop sở hữu. Không phù hợp tiến độ 3 tuần. |
| Managed scraping | Không có ngân sách và cần thẩm định quyền thu thập/chuyển giao; không giải quyết được nhanh vấn đề license và độ đúng của nhãn. Đây là phân tích phù hợp với ràng buộc dự án, không phải kết quả thử nghiệm dịch vụ. |
| AI crawler | Không được dùng trong bộ dữ liệu đã báo cáo. Trong điều kiện dữ liệu ít và license chưa rõ, rủi ro trích sai hoặc vi phạm điều khoản cao hơn lợi ích tự động hóa. |
| Mua dataset | Không phù hợp ràng buộc không ngân sách. |
| Hợp tác doanh nghiệp | Thời gian đàm phán và rủi ro dữ liệu khách hàng vượt phạm vi đồ án. |
| Google/Bing Images | Không bảo đảm bản quyền, liên kết ảnh–metadata và ground truth; không phù hợp làm benchmark đáng tin cậy. |
| Dataset cần đăng ký hoặc xin quyền | Thời gian cấp quyền không kiểm soát được; ghi nhận làm nguồn tiềm năng cho giai đoạn sau. |
| Dữ liệu tổng hợp làm catalog sản phẩm thật | Không được chọn làm dữ liệu sự thật của cửa hàng: giá/size/tồn kho do LLM sinh có thể sai. Synthetic data chỉ dùng bổ trợ tập đánh giá. |

## 1.3. Nguồn dữ liệu và mức độ chính thống

Dự án sử dụng thang đánh giá nguồn 5 mức:

| Mức | Diễn giải |
|---|---|
| **1 – Học thuật/chính thức** | Có tổ chức, paper hoặc công bố chính thức và license/điều khoản tương đối rõ. |
| **2 – Cộng đồng có kiểm duyệt** | Dataset trên nền tảng cộng đồng; cần truy lại nguồn gốc gốc và xác minh license. |
| **3 – Dữ liệu công khai từ sàn** | Dữ liệu thật nhưng chịu giới hạn ToS, robots.txt và chính sách nền tảng. |
| **4 – Nhóm tự tạo** | Nhóm kiểm soát quy trình; cần ghi người tạo, cách tạo và nguồn kế thừa. |
| **5 – Không rõ nguồn** | Không xác định được nguồn hoặc license; không nên dùng. |

### Nguồn đã dùng

| Nguồn | Mức | Loại dữ liệu và quy mô | License/điều khoản và lưu ý |
|---|---:|---|---|
| **Fashion Product Images (small)** – bản mirror Hugging Face `ashraq/fashion-product-images-small`; nguồn gốc Kaggle `paramaggarwal/fashion-product-images-dataset` | 2 | Dataset gốc có **44.072 dòng**; dự án chọn **4.593 sản phẩm** thuộc 4 nhóm, còn **4.385 sản phẩm sau làm sạch**; 1 ảnh/sản phẩm. Dùng làm catalog và dữ liệu Visual Search. | License/Data Card gốc **cần xác minh**; bản mirror không ghi license rõ theo báo cáo. Chỉ dùng học thuật; không phát hành lại ảnh khi chưa xác nhận quyền. Nguồn gốc dữ liệu gắn với catalog Myntra. |
| **ViMRHP – Vietnamese Multimodal Review Helpfulness Prediction** – Hugging Face `trucmtnguyen/ViMRHP` | 1 | **509 sản phẩm, 11.009 review** ban đầu. Sau bỏ 81 sản phẩm đồng hồ còn **428 sản phẩm, 9.403 review**; khử 86 review trùng còn **9.317 review**. Trong 428 sản phẩm, **361 sản phẩm** thuộc phạm vi 4 nhóm của dự án. Dùng cho Product QA, tóm tắt review và benchmark LLM. | **CC BY-NC-ND 4.0** theo thông tin dataset/paper; phi thương mại, không phát hành bản phái sinh. Báo cáo yêu cầu xác minh lại license tại nguồn chính thức trước khi nộp. |
| **Bộ đánh giá tự tạo** | 4 | 600 truy vấn Visual Search, 60 truy vấn OOD, 280 câu QA, 78 câu router và 60 kịch bản end-to-end. | Là dữ liệu nhóm tạo từ dữ liệu nguồn hoặc bằng tác nhân/LLM. Nhãn hiện chưa được người thật duyệt đầy đủ; phải ghi rõ nguồn gốc. |

### Nguồn dự phòng hoặc chưa dùng

| Nguồn | Trạng thái | Lý do / điều kiện |
|---|---|---|
| Amazon Reviews 2023 | Chưa dùng | Có thể hữu ích để bổ sung metadata, review và sản phẩm mũ; điều khoản nghiên cứu cần xác minh. |
| Amazon Berkeley Objects (ABO) | Chưa dùng | Nguồn học thuật; license được ghi là CC BY-NC 4.0 trong tài liệu, nhưng tải từ môi trường bị chặn và cần kiểm tra lại trang gốc. |
| Clothing Dataset của Alexey Grigorev | Chưa dùng | Tài liệu ghi CC0 nhưng yêu cầu xác minh lại; có ảnh và lớp sản phẩm, không có giá/review. |
| DeepFashion | Chưa dùng | Cần xin quyền/thỏa thuận; phạm vi chủ yếu là thời trang/quần áo. |
| CAMEO / ViEcom-Rec (NTCIR-19) | Chưa dùng | Có thể tham khảo cho giai đoạn sau; cần đăng ký và xác minh trang/điều khoản chính thức. |
| Tiki/Shopee crawl | Không dùng trong lượt này | Thử nghiệm truy cập bị chặn hoặc không kết nối; không vượt cơ chế chặn. |
| Ảnh tự chụp | Chưa có | Mục tiêu 80–100 ảnh đời thực; số đã có tại thời điểm báo cáo là **0**. |

## 1.4. Phân loại dữ liệu trong hệ thống

| Loại dữ liệu | Nguồn/hiện trạng | Vai trò trong hệ thống |
|---|---|---|
| **Ảnh sản phẩm** | 4.593 ảnh catalog FPI; mỗi sản phẩm một ảnh, kích thước 60×80 px. | Vector hóa bằng image embedding, lưu index và tìm kiếm top-K. |
| **Metadata sản phẩm** | Tên, nhóm/nhãn taxonomy và một số trường catalog. Catalog thiếu giá, size, mô tả và tồn kho. | Hiển thị sản phẩm, lọc/tìm kiếm, so sánh thuộc tính và liên kết truy vấn với sản phẩm. |
| **Review** | ViMRHP có review tiếng Việt Shopee; 9.317 review sau làm sạch trùng, trước các bước lọc spam tiếp theo. | Tạo knowledge base/chunks cho RAG, trả lời về cảm nhận/chất liệu/giao hàng trong phạm vi review. |
| **Q&A** | Không có bộ Q&A sản phẩm đầy đủ, được xác nhận như dữ liệu gốc trong nguồn chính. | Câu hỏi đánh giá được xây từ review/sản phẩm; không được xem là Q&A thật từ cửa hàng. |
| **Nhãn đánh giá Visual Search** | 600 truy vấn tổng hợp: ảnh catalog được biến đổi; có phân chia instance/category. | Ground truth để so sánh model trên truy vấn mô phỏng. |
| **Nhãn đánh giá QA/router** | 280 câu QA, 78 câu router và các tập held-out; nhiều câu do LLM/tác nhân tạo. | Đo retrieval, trả lời, route và từ chối; cần người thật duyệt để tăng độ tin cậy. |
| **Ảnh đời thực / nhãn người dùng** | Chưa có tại thời điểm báo cáo. | Cần để đánh giá domain gap và khả năng dùng thực tế của Visual Search. |

## 1.5. Cấu trúc dữ liệu và thách thức chất lượng

Dữ liệu của đồ án là **đa phương thức**, gồm ảnh, metadata có cấu trúc, review tiếng Việt dạng văn bản và nhãn đánh giá. Các loại dữ liệu này chưa được liên kết hoàn hảo: ảnh có thể không truy cập được, review không chứa mọi thuộc tính sản phẩm, và bộ đánh giá có thể được tạo từ chính các nguồn dữ liệu đang dùng.

| Thách thức | Bằng chứng trong dự án | Ảnh hưởng |
|---|---|---|
| **Độ phân giải và miền ảnh** | 100% ảnh FPI có kích thước 60×80 px; ảnh nền studio; 1 ảnh/sản phẩm. | Truy vấn được tạo bằng biến đổi ảnh catalog có thể cho kết quả lạc quan hơn ảnh chụp thực tế. |
| **Ảnh đời thực chưa có** | 0/80 ảnh mục tiêu. | Chưa đo được mức tổng quát hóa từ ảnh studio sang ảnh người dùng, góc chụp và nền phức tạp. |
| **Thiếu metadata quan trọng** | FPI và ViMRHP thiếu giá, size, tồn kho; ViMRHP không cung cấp ảnh truy cập được trong môi trường. | Hệ thống không thể trả lời hoặc lọc chính xác các thông tin này nếu không có nguồn bổ sung. |
| **Nhiễu và trùng lặp** | FPI có 20 cặp ảnh trùng MD5; 21 sản phẩm bị loại trong bước làm sạch; pHash có nhiều cặp trông gần nhau nhưng là sản phẩm khác. ViMRHP có 86 review trùng `comment_id`. | Nếu xử lý trùng sai có thể làm sai số lượng và ground truth. |
| **Lỗi taxonomy** | Nhãn “Caps” lẫn beanie; “Hat” có thể là beanie/fedora; một số nhãn mũ và boot cần điều chỉnh. | Sai nhóm làm giảm chất lượng filter, type gate và đánh giá theo nhóm. |
| **Thiếu nhóm dữ liệu** | Sau làm sạch có 285 sản phẩm mũ, thấp hơn quota 300; thiếu một số loại như bucket hat. | Kết quả nhóm nhỏ có độ bất định cao và độ phủ không đều. |
| **Review lệch và spam** | 93,4% review ViMRHP là 5 sao; 262 review spam/quảng cáo được lọc theo luật. | RAG có thể phản ánh thiên lệch tích cực và bị nhiễu bởi review chung chung hoặc spam. |
| **Ngôn ngữ không chuẩn** | Review có teencode, viết không dấu, ngắn; độ dài trung bình khoảng 146 ký tự và trung vị 132 ký tự. | Ảnh hưởng tokenization và retrieval; cần so sánh phương pháp từ vựng và embedding đa ngôn ngữ. |
| **Thiếu liên kết và phạm vi** | 45/280 câu QA và 4/78 câu router liên quan sản phẩm ngoài taxonomy; trong kho RAG có sản phẩm ngoài phạm vi. | Có thể khiến hệ thống trả lời về danh mục không được hỗ trợ hoặc khiến số đo không nhất quán. |
| **Dữ liệu lỗi thời / giá trị thay đổi theo thời gian** | Giá, size, tồn kho không có hoặc không được cập nhật theo thời gian trong catalog hiện tại. | Các câu trả lời về thông tin biến động không thể được coi là đúng nếu không có nguồn thời gian thực. |
| **Nhãn tổng hợp chưa được duyệt** | Bộ eval QA/router và truy vấn visual chưa được hai người thật duyệt; 0% câu eval QA/router có người duyệt theo báo cáo. | Số đo phản ánh benchmark hiện có, chưa phải bằng chứng đầy đủ về chất lượng người dùng thực. |

### Tóm tắt quy mô bộ đánh giá

| Bộ đánh giá | Quy mô | Cách tạo / giới hạn |
|---|---:|---|
| Visual Search | 600 truy vấn (240 validation, 360 test; 90 test mỗi nhóm), thêm 60 truy vấn OOD | Ảnh catalog biến đổi và ảnh sản phẩm cùng loại/màu; chưa có ảnh đời thực. |
| Product QA | 280 câu trên 80 sản phẩm; 71 câu không có đáp án (25,4%) | 251 câu LLM sinh, 29 câu tác nhân viết tay; chưa được người thật duyệt. |
| Router | 78 câu; 21 câu chitchat/OOD | Tập do tác nhân tạo, chưa có người thật duyệt. |
| End-to-end | 60 kịch bản | Chưa được người thật chấm lại; một số kịch bản QA/compare thiếu product ID nên chưa đánh giá tốt luồng thực tế. |
| Visual query đời thực | Mục tiêu 80–100 ảnh | Chưa thu thập tại thời điểm báo cáo. |

---

# PHẦN 2: HỆ THỐNG ĐỘ ĐO (METRICS)

Các ký hiệu:

- \(Q\): tập truy vấn.
- \(L_q[1..K]\): danh sách K kết quả đầu cho truy vấn \(q\).
- \(R_q\): tập sản phẩm đúng của truy vấn.
- \(G(q)\): tập chunk bằng chứng chứa thông tin cần thiết cho câu hỏi.
- \(N\): số câu hỏi hoặc kịch bản được đánh giá.

## 2.1. Visual Search

| Độ đo | Công thức / ý nghĩa | Ưu điểm | Nhược điểm | Vai trò trong dự án |
|---|---|---|---|---|
| **Recall@K** | \(\frac{1}{|Q|}\sum_q \frac{|R_q \cap L_q[1..K]|}{|R_q|}\). Tỷ lệ sản phẩm đúng được tìm thấy trong K kết quả đầu. Với truy vấn instance chỉ có một sản phẩm đúng, tương đương tỷ lệ truy vấn có sản phẩm đó trong top-K. | Gắn trực tiếp với câu hỏi “người dùng có thấy món mình muốn trong vài kết quả đầu không?”; dễ giải thích. | Không phân biệt sản phẩm đúng ở hạng 1 hay hạng K. Phụ thuộc định nghĩa sản phẩm “đúng”. | **Chính:** macro Recall@5 theo 4 nhóm, dùng để chọn model. |
| **Precision@K** | \(\frac{1}{|Q|}\sum_q \frac{|R_q \cap L_q[1..K]|}{K}\). Tỷ lệ kết quả top-K được xem là đúng. | Đo độ “sạch” của danh sách tìm kiếm. | Ở tầng instance chỉ có một sản phẩm đúng nên P@5 tối đa 0,2; không phù hợp để đánh giá việc tìm lại đúng sản phẩm. | **Phụ:** dùng cho tầng category, ví dụ sản phẩm cùng loại và màu. |
| **mAP@K** | AP của truy vấn là trung bình Precision@i ở các vị trí i có kết quả đúng; mAP là trung bình AP qua các truy vấn. | Hữu ích khi mỗi truy vấn có nhiều đáp án đúng và có ground truth đầy đủ. | Khó giải thích với người dùng; cần nhãn đầy đủ. Ở tầng instance một đáp án, AP gần như trùng với reciprocal rank. Ở tầng category, nhãn “cùng loại và màu” chỉ là xấp xỉ mức tương tự. | **Không chọn làm chỉ số chính.** Có thể báo cáo tham khảo khi nhãn category đủ đáng tin cậy. |
| **NDCG@K** | DCG@K \(=\sum_{i=1}^{K}\frac{rel_i}{\log_2(i+1)}\); NDCG = DCG chia cho DCG lý tưởng. Đánh giá thứ tự xếp hạng, có thể dùng nhiều mức liên quan. | Ưu tiên kết quả liên quan ở vị trí cao; biểu diễn được mức độ liên quan. | Cần nhãn relevance nhiều mức; nhãn hiện tại chủ yếu nhị phân và chưa được người thật duyệt. | **Phụ**, dùng khi phân tích xếp hạng. |
| **MRR@10** | \(\frac{1}{|Q|}\sum_q \frac{1}{rank_q}\), bằng 0 nếu sản phẩm đúng nằm ngoài top-10. | Thưởng cho việc đưa kết quả đúng lên đầu; bổ sung thông tin cho Recall@5. | Chỉ xét kết quả đúng đầu tiên, không đánh giá độ chính xác của cả danh sách. | **Chính**, bổ sung cho Recall@5. |
| **Latency p50/p95** | Thời gian xử lý truy vấn; p50 là trung vị, p95 là phân vị 95. Với Visual Search nên đo thời gian nhúng ảnh truy vấn và tìm index, ghi rõ có/không gồm khởi động model. | Đo trực tiếp độ mượt khi demo/triển khai. | Phụ thuộc phần cứng, tải nền, model đã warm-up hay chưa; cần lặp nhiều lần. | **Chính về vận hành**, theo dõi p95. |
| **Macro Recall@5** | Tính Recall@5 riêng cho giày, quần áo, mũ, phụ kiện rồi lấy trung bình cộng. | Ngăn nhóm lớn như quần áo che khuất hiệu năng nhóm nhỏ như mũ. | Nhóm ít truy vấn có phương sai cao; cần báo số truy vấn từng nhóm. | **Chỉ số chính để chọn model.** |
| **CTE@5 (Cross-type error)** | \(\frac{1}{|Q|}\sum_q \frac{\#\{\text{sản phẩm top-5 sai nhóm}\}}{5}\). | Phát hiện lỗi nghiêm trọng như tìm giày nhưng trả áo hoặc phụ kiện. | Không đo độ giống về kiểu dáng, màu sắc hay chất lượng ảnh trong cùng nhóm. | **Chính**, càng thấp càng tốt. |

**Lý do lựa chọn:** trải nghiệm hướng đến việc người dùng xem một số kết quả đầu; macro theo nhóm bảo đảm nhóm nhỏ không bị nhóm lớn lấn át; nhầm khác nhóm là lỗi hiển thị dễ nhận thấy.

## 2.2. Product QA / RAG

| Độ đo | Công thức / ý nghĩa | Ưu điểm | Nhược điểm | Vai trò trong dự án |
|---|---|---|---|---|
| **Hit Rate / Hit@K** | \(\frac{1}{|Q|}\sum_q \mathbb{1}[R_K(q)\cap G(q)\ne\emptyset]\). Tỷ lệ câu hỏi mà top-K retrieval có ít nhất một đoạn bằng chứng. | Tách lỗi “không tìm thấy bằng chứng” khỏi lỗi “LLM trả lời sai”; dễ tính và giải thích. | Không đo thứ hạng chính xác hoặc độ nhiễu của toàn bộ ngữ cảnh; cần gán bằng chứng đúng. | **Chính:** Hit@5, vì hệ thống đưa tối đa 5 đoạn vào prompt. |
| **MRR@K** | Trung bình \(1/rank(q)\) của chunk bằng chứng đúng đầu tiên trong top-K. | Cho biết bằng chứng có được xếp cao để LLM dễ sử dụng không. | Chỉ xét bằng chứng đúng đầu tiên. | **Chính cho so sánh retriever**, bổ sung Hit@5. |
| **Context Precision** | Tỷ lệ chunk trong ngữ cảnh truy xuất được xem là liên quan; dạng đơn giản: \(\frac{\#\text{chunk liên quan}}{K}\). Một số biến thể RAGAS gán trọng số cao hơn cho chunk ở hạng đầu. | Đo mức nhiễu trong ngữ cảnh đưa vào LLM. | Cần nhãn relevance cho từng chunk hoặc LLM-as-judge; có thể tốn công và thiên lệch. | **Phụ**, dùng để chẩn đoán chất lượng retrieval. |
| **Faithfulness / Groundedness** | \(\frac{\#\text{nhận định được bằng chứng hỗ trợ}}{\#\text{nhận định trong câu trả lời}}\). Đánh giá câu trả lời có bám vào review/context hay không. | Đo trực tiếp rủi ro bịa thông tin; phù hợp mục tiêu an toàn của Product QA. | LLM-as-judge có thể chấm sai hoặc dễ dãi; cần kiểm tra trích dẫn và người chấm. | **Chính.** |
| **Hallucination Rate** | Tỷ lệ câu trả lời có ít nhất một nhận định không được hỗ trợ bởi ngữ cảnh. Mẫu số phải được quy định rõ, thường là các câu không bị từ chối. | Dễ diễn giải thành tỷ lệ câu có lỗi bịa. | Phụ thuộc cách định nghĩa “nhận định” và mẫu số; hai báo cáo dùng mẫu số khác nhau thì không so sánh trực tiếp. | **Chính**, mục tiêu càng thấp càng tốt. |
| **Answer Relevance / Answer Relevancy** | Tỷ lệ hoặc điểm đánh giá câu trả lời có đúng trọng tâm câu hỏi hay không. | Phát hiện câu trả lời có căn cứ nhưng lạc đề hoặc không hữu ích. | Thường cần người hoặc LLM chấm; điểm không bảo đảm sự thật nếu đánh giá riêng. | **Chính về chất lượng câu trả lời**, cần đọc cùng Faithfulness. |
| **Abstention / Refusal Accuracy** | \(\frac{\#\text{câu không có đáp án được từ chối đúng}}{\#\text{câu không có đáp án}}\). | Kiểm tra trực tiếp khả năng nói “chưa có thông tin” thay vì đoán. | Hệ thống từ chối tất cả có thể đạt điểm cao nếu không tính false-refusal. | **Chính**, phải đánh giá cùng false-refusal. |
| **False-refusal Rate** | \(\frac{\#\text{câu có đáp án bị từ chối}}{\#\text{câu có đáp án}}\). | Ngăn hệ thống từ chối quá mức. | Phụ thuộc nhãn answerable đúng; cần đủ số câu có đáp án. | **Chính bổ sung** cho refusal accuracy. |
| **Citation Rate / Cited-gold** | Citation rate: tỷ lệ câu trả lời có trích dẫn hợp lệ. Cited-gold: tỷ lệ trích dẫn trỏ đúng bằng chứng. | Kiểm tra khả năng truy vết nguồn; hữu ích trong QA review. | Trích dẫn đúng chunk không tự động bảo đảm câu trả lời đúng. | **Phụ**, nhưng là kiểm soát quan trọng khi triển khai. |
| **EM / token F1** | EM kiểm tra chuỗi sau chuẩn hóa có trùng đáp án; F1 đo precision/recall token giữa câu trả lời và đáp án mẫu. | Khách quan, rẻ cho câu factual ngắn. | Câu tiếng Việt tự do có nhiều cách diễn đạt đúng; có thể phạt câu đúng về nghĩa nhưng khác chữ. | **Phụ**, chỉ cho câu hỏi có đáp án chuẩn ngắn. |
| **ROUGE / BLEU** | Đo trùng lặp n-gram hoặc chuỗi giữa câu trả lời và tham chiếu. | Tính rẻ, quen thuộc trong đánh giá sinh văn bản. | Không đo trực tiếp sự thật hoặc ý nghĩa; kém phù hợp với câu trả lời hội thoại tiếng Việt. | **Không chọn làm chỉ số chất lượng chính.** |
| **BERTScore** | So độ tương đồng embedding giữa token của câu trả lời và câu tham chiếu. | Nhạy ngữ nghĩa hơn so khớp chuỗi. | Không xác nhận câu trả lời có được bằng chứng hỗ trợ; thêm chi phí tính toán. | **Phụ/tham khảo.** |
| **Human evaluation** | Hai người chấm đúng, hữu ích, tự nhiên; có thể báo cáo mức đồng thuận như Cohen’s \(\kappa\). | Có thể phát hiện lỗi mà metric hoặc LLM-as-judge bỏ sót. | Tốn công, cần hướng dẫn chấm và giải quyết bất đồng. | **Cần thiết để kiểm chứng**, dự án đề xuất chấm 50 câu nhưng chưa hoàn thành. |

**Điều kiện quan trọng:** với bộ dữ liệu này, retrieval toàn kho thấp hơn retrieval giới hạn theo `product_id`, do nhiều sản phẩm có review chung chung tương tự. Nếu người dùng đang hỏi về một sản phẩm cụ thể, hệ thống nên nhận diện hoặc hỏi lại sản phẩm trước khi chạy Product QA.

## 2.3. Agent và đánh giá end-to-end

| Độ đo | Công thức / ý nghĩa | Ưu điểm | Nhược điểm | Vai trò trong dự án |
|---|---|---|---|---|
| **Intent Accuracy / Route Accuracy** | \(\frac{\#\text{câu chọn đúng route}}{N}\). Route có thể là visual, QA, search, compare, chitchat/OOD hoặc clarify. | Đánh giá khả năng chọn đúng luồng xử lý; dễ tổng hợp và so sánh. | Không đo mức nghiêm trọng của từng loại lỗi; accuracy tổng có thể che lấp route ít mẫu. | **Chính**, kèm macro theo route và confusion matrix. |
| **Tool-call Accuracy** | Tỷ lệ lượt chọn đúng công cụ và cung cấp đúng tham số bắt buộc, như `product_id`, `product_type` hoặc ảnh. | Phát hiện trường hợp route đúng nhưng công cụ/đầu vào sai. | Cần nhãn tool call và tham số đúng cho từng kịch bản. | **Chính trong bộ kiểm thử công cụ**, theo US_14. |
| **Task Success Rate (TSR)** | \(\frac{\#\text{kịch bản hoàn thành đúng từ đầu đến cuối}}{\#\text{kịch bản}}\). Thành công phải được định nghĩa rõ cho từng kịch bản. | Phản ánh chất lượng hệ thống như người dùng trải nghiệm, thay vì chấm từng module riêng. | Tốn công định nghĩa và chấm; phụ thuộc tính đại diện của kịch bản. | **Chính**, mục tiêu dự án ≥ 0,80. |
| **Hallucination / Unsupported-store-fact Rate** | Tỷ lệ phản hồi có thông tin không có trong dữ liệu cửa hàng, ví dụ tự khẳng định giá, size, tồn kho hoặc cửa hàng có bán sản phẩm ngoài danh mục. | Gắn trực tiếp với rủi ro gây hiểu nhầm trong mua sắm. | Regex có thể bỏ sót cách diễn đạt; cần người kiểm tra mẫu. Unsupported-store-fact là phạm vi hẹp hơn hallucination nói chung. | **Chính về an toàn thông tin**, đặc biệt trên nhánh Gemini. |
| **Fallback Rate** | \(\frac{\#\text{lượt chuyển sang Gemini/fallback}}{\#\text{tổng lượt}}\). | Đo mức phụ thuộc vào LLM ngoài, chi phí/quota và khả năng router xử lý nội bộ. | Phụ thuộc thành phần của bộ test; tập cố tình nhiều OOD có thể làm tỷ lệ cao hơn lưu lượng thực. | **Phụ / chỉ số vận hành**, cần theo dõi cùng chất lượng và chi phí. |
| **Latency end-to-end p95** | Phân vị 95 thời gian từ đầu vào đến phản hồi hoàn chỉnh, gồm retrieval, LLM và công cụ. | Đo độ trễ thực tế người dùng trải nghiệm. | Nhạy với mạng, quota, retry, tải hệ thống và provider. | **Chính về vận hành.** |
| **Token / chi phí** | Tổng token vào/ra/thinking theo 100 lượt; tiền được tính theo biểu giá tương ứng. | Cho biết khả năng vận hành và quy mô chi phí. | Đơn giá và quota thay đổi; phải nói rõ token trên 100 lượt hội thoại hay 100 lời gọi LLM. | **Phụ/vận hành**, bắt buộc ghi rõ đơn vị. |

## 2.4. Độ đo chính, phụ và không chọn

| Thành phần | Độ đo chính | Độ đo phụ | Không chọn làm chỉ số chính |
|---|---|---|---|
| **Visual Search** | Macro Recall@5, MRR@10, CTE@5, latency p95 | Recall@1/10, category Hit@5, category P@5, NDCG@10, AUROC cho chọn ngưỡng OOD, RAM/index size | mAP vì cần ground truth đầy đủ và khó diễn giải trong cấu hình hiện tại; Precision@5 không phù hợp cho truy vấn instance có một đáp án đúng. |
| **Product QA – retrieval** | Hit@5 theo `product_id`; MRR@10 để so sánh thứ hạng retriever | Context Precision, Context Recall, AUC tách câu answerable/unanswerable | Không dùng một ngưỡng retrieval đơn lẻ làm cơ chế từ chối chính nếu làm mất nhiều câu có đáp án. |
| **Product QA – generation** | Faithfulness, Hallucination Rate, Abstention Accuracy, False-refusal Rate, Answer Relevance | Citation/Cited-gold, F1 cho câu factual ngắn, BERTScore, human evaluation | ROUGE/BLEU không phản ánh đúng/sai ngữ nghĩa; không xem điểm LLM-as-judge là bằng chứng cuối cùng. |
| **Agent** | Route/Intent Accuracy, Tool-call Accuracy, TSR, Unsupported-store-fact Rate | Fallback Rate, latency p95, token/100 lượt, cache hit, lỗi 429/timeout | Không đánh giá Agent chỉ bằng độ chính xác route; cần kết quả end-to-end và kiểm tra an toàn thông tin. |

## 2.5. Ngưỡng mục tiêu đề xuất

Bảng dưới đây giữ nguyên ngưỡng đã ghi trong tài liệu US_18. Với những độ đo chính chưa có ngưỡng bằng số trong tài liệu, cột ghi chú đánh dấu rõ đây là **đề xuất bổ sung**, không phải số đo hoặc ngưỡng chính thức của nhóm.

| Thành phần / metric | Mục tiêu | Baseline trong báo cáo | Nhận xét |
|---|---:|---:|---|
| Visual macro Recall@5 trên truy vấn tổng hợp | **≥ 0,85** | 0,846 DINOv2-S | Gần ngưỡng; số đo trên truy vấn tổng hợp, chưa chứng minh chất lượng trên ảnh đời thực. |
| Visual macro Recall@5 trên ảnh đời thực | **≥ 0,70** | Chưa đo | Mục tiêu đề xuất riêng cho ảnh người dùng; cần thu thập tập ảnh thật trước khi kết luận. |
| Visual MRR@10 | **≥ 0,75** | 0,791 DINOv2-S | Baseline vượt ngưỡng đề xuất. |
| Visual CTE@5 | **≤ 0,05**; tập khó **≤ 0,08** | 0,043 DINOv2-S | Đạt trên benchmark hiện tại; tiếp tục theo dõi khi thay model hoặc dữ liệu. |
| Visual latency nhúng một ảnh, p95 | **≤ 1.000 ms** | DINOv2-S 1.924 ms; SigLIP 214 ms; FashionCLIP 390 ms | DINOv2-S chưa đạt trong phép đo này. Latency chịu nhiễu do máy dùng chung và cần đo lại trên máy demo. |
| Product QA Hit@5 theo `product_id` | **≥ 0,90** | 0,895 trên test, n=114 | Gần ngưỡng; bộ câu hỏi chưa được người thật duyệt. |
| Product QA MRR@10 | Chưa chốt bằng số trong tài liệu; **đề xuất ≥ 0,55** | Hybrid 0,548 trên 209 câu answerable | Đề xuất bổ sung gần baseline đã đo; phải xác nhận trên cùng split và protocol trước khi coi là ngưỡng nghiệm thu. |
| Context Precision | Chưa chốt bằng số | Chưa có số đáng tin cậy được báo cáo | Dùng chẩn đoán độ nhiễu; nên chốt sau khi có nhãn relevance cho từng chunk. |
| Faithfulness | **≥ 0,85** | 1,00 (Chiến, 52 câu) và 0,939 (Đạt, 36 câu), đều LLM chấm | Chưa thể xem là đạt cuối cùng nếu chưa có người chấm; kết quả có thể lệch do judge. |
| Hallucination Rate | **≤ 0,10** | 0,00 (Chiến) và 0,111 (Đạt), LLM chấm | Hai lần đo có bộ câu và quy ước mẫu số khác nhau; cần thống nhất cách tính trước khi so sánh. |
| Abstention Accuracy | **≥ 0,90** | 15/15 = 1,00 sau khi sửa nhãn | Mẫu còn nhỏ; báo cáo ghi rõ số đo sau sửa nhãn. |
| False-refusal Rate | **Đề xuất ≤ 0,10** | 0/37 = 0,00 trong phép đo đã báo cáo | Ngưỡng ≤0,10 là đề xuất bổ sung để cân bằng khả năng từ chối đúng; cần thêm câu hỏi answerable được duyệt. |
| Answer Relevance | **Đề xuất ≥ 0,85** | Có lần đo 1,00 trên 52 câu bằng LLM judge | Mức 0,85 là đề xuất bổ sung; cần hiệu chỉnh với người chấm. |
| Route / Intent Accuracy | **≥ 0,90** | 0,878 trên tập held-out n=49 | Chưa đạt. Điểm 0,923 trên tập đã dùng để chỉnh luật không được coi là kết quả held-out. |
| Tool-call Accuracy | Cần đặt theo bộ US_46; **đề xuất ≥ 0,90** | Chưa có số tổng hợp đáng tin cậy trong bảng ngưỡng | Ngưỡng ≥0,90 là đề xuất bổ sung; cần bộ nhãn tool và tham số được duyệt. |
| TSR end-to-end | **≥ 0,80** | 0,650 (39/60) trong hệ thống ghép | Chưa đạt; báo cáo lưu ý một số kịch bản QA/compare thiếu product ID, làm kết quả chưa đại diện tốt cho cấu hình hợp lệ. |
| Unsupported-store-fact Rate | **0** sau hậu kiểm; đặc biệt giá/size/tồn kho phải không bịa | Giá/size/tồn kho 0/40; có 2/40 câu khẳng định cửa hàng bán hàng ngoài danh mục trong một phép kiểm | Chưa đạt mục tiêu nghiêm ngặt 0; cần sửa prompt/guard và kiểm tra lại. |
| Fallback Rate | **≤ 0,25** trên log demo thật | 0,273 trên bộ eval | Bộ eval có nhiều OOD/chitchat nên không đại diện trực tiếp cho lưu lượng thật. |
| Agent end-to-end latency p95 | **≤ 8 giây** | Chưa đo ổn định toàn hệ thống | Ngưỡng có trong tài liệu, cần đo sau khi ghép đủ công cụ. |
| Gemini latency p95 | **≤ 4 giây** | Có phép đo đến 41,1 giây khi gồm retry/quota | Chưa đạt trong điều kiện đo đó; cần đo lại khi không bị quota/429 và ghi tách latency mạng, retry, model. |

### Quy tắc diễn giải kết quả

- Visual Recall hiện tại là **[Thật–tổng hợp]**: model được đo trên ảnh catalog và truy vấn mô phỏng, không phải ảnh đời thực.
- QA Faithfulness/Hallucination hiện có là **[LLM chấm]**; cần người thật chấm mẫu tối thiểu 50 câu để kiểm tra độ tin cậy.
- Bộ đánh giá QA/router còn **[Chưa người duyệt]**; không nên trình bày các con số như kết quả nghiệm thu cuối cùng.
- Mọi ngưỡng nên được chọn trên validation và báo cáo trên test độc lập.
- Cần thống nhất mẫu số Hallucination Rate: tỷ lệ tính trên mọi phản hồi hay chỉ các câu trả lời không từ chối.
- Với mục tiêu “không bịa”, không nên gộp điểm Faithfulness thành kết luận duy nhất; cần xem thêm unsupported-store-fact, cited-gold, refusal accuracy và false-refusal.

---

# PHẦN 3: KHẢO SÁT ỨNG DỤNG VÀ BÀI BÁO TƯƠNG TỰ

## 3.1. Ứng dụng tương tự

Các điểm dưới đây là tổng hợp khảo sát tài liệu trong US_21, không phải kết quả kiểm thử thực nghiệm của nhóm. Báo cáo lưu ý trải nghiệm trực tiếp Google Lens/Shopee chưa thực hiện; năm ra mắt hoặc chi tiết sản phẩm cần xác minh lại từ nguồn chính thức.

| Ứng dụng | Điểm mạnh được ghi nhận | Điểm đáng học hỏi | Bài học áp dụng vào đồ án |
|---|---|---|---|
| **Google Lens** | Nhận diện hoặc khoanh vùng vật thể trong ảnh; hỗ trợ tìm kiếm bằng hình ảnh kết hợp văn bản. | Cho người dùng chọn vùng ảnh cần tìm thay vì luôn dùng toàn ảnh; kết hợp truy vấn ảnh và mô tả chữ. | Tích hợp crop vùng quan tâm; nếu độ tin cậy visual thấp, gợi ý người dùng mô tả bằng văn bản hoặc chọn loại sản phẩm. |
| **Pinterest Lens** | Tìm kiếm hình ảnh phục vụ khám phá ý tưởng/sản phẩm; mô hình có thể học từ tín hiệu tương tác. | Tổ chức pipeline thành phát hiện/vùng quan tâm → embedding → index; tìm sản phẩm “cùng ý tưởng” chứ không chỉ trùng ảnh. | Kiến trúc `detect/embed/index`; đánh giá riêng truy vấn tìm lại đúng sản phẩm và truy vấn tìm sản phẩm cùng loại/màu. |
| **Shopee Image Search** | Gần hành vi mua sắm tại Việt Nam; kết quả gắn với listing và có thể đi kèm bộ lọc thương mại như giá/đánh giá. | Đưa bộ lọc và ngữ cảnh mua sắm vào sau bước tìm ảnh; kết quả cần hữu dụng như danh sách sản phẩm, không chỉ điểm giống ảnh. | Tạo luồng Visual Search hướng sản phẩm, nối với metadata và filter. Cần tự thử ứng dụng với bộ ảnh thật trước khi kết luận UX. |
| **Amazon StyleSnap** | Tìm thời trang từ ảnh người mặc hoặc outfit; có thể liên quan đến phát hiện từng món trong cả bộ đồ. | Tách nhiều món trong ảnh và cho biết hệ thống đang tìm loại nào. | Với ảnh chứa nhiều đối tượng, hỏi lại “bạn muốn tìm áo, giày hay mũ?” hoặc cho phép chọn vùng; tránh trả kết quả sai nhóm. |
| **Amazon Rufus** | Trợ lý mua sắm hỏi đáp dựa trên thông tin sản phẩm, review và Q&A cộng đồng. | Trả lời theo ngữ cảnh sản phẩm và tổng hợp thông tin từ nhiều nguồn. | Kết hợp Product QA với RAG, nhưng cần trích dẫn nguồn, phân biệt review với thông số cửa hàng và từ chối khi nguồn không đủ. |

## 3.2. Bài báo và phương pháp nền tảng

| Công trình | Ý nghĩa chính | Cách áp dụng vào hệ thống |
|---|---|---|
| **CLIP (2021)** – *Learning Transferable Visual Models From Natural Language Supervision* | Học biểu diễn ảnh và văn bản trong cùng không gian từ cặp ảnh–mô tả; hỗ trợ chuyển giao và phân loại zero-shot bằng prompt văn bản. | Là nền tảng cho image embedding và thử nghiệm phân loại nhóm bằng text prompt/type gate. Cần lưu ý kết quả phụ thuộc domain và chất lượng prompt. |
| **FashionCLIP** – *Contrastive language and vision learning of general fashion concepts* | Tinh chỉnh CLIP theo miền thời trang để biểu diễn khái niệm thời trang tốt hơn mô hình tổng quát. | Là ứng viên embedding chuyên miền để so sánh với DINOv2-S, SigLIP và CLIP. Kết quả trên catalog cùng nguồn huấn luyện có nguy cơ lạc quan, nên cần ảnh đời thực. |
| **SigLIP (2023)** – *Sigmoid Loss for Language Image Pre-Training* | Dùng loss sigmoid theo từng cặp ảnh–văn bản thay cho cách chuẩn hóa softmax theo batch; công trình nhấn mạnh khả năng huấn luyện tương phản hiệu quả. | Là ứng viên image-text model và có thể dùng cho phân loại nhóm bằng văn bản; dự án đã benchmark SigLIP B/16. |
| **RAG (Lewis et al., 2020)** – *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* | Kết hợp retriever với mô hình sinh để câu trả lời dựa trên kho tri thức truy xuất, thay vì chỉ dựa vào tham số mô hình. | Product QA dùng retrieval trên review, lấy context rồi mới sinh câu trả lời. Kết quả retrieval phải được đo riêng với độ grounded của câu trả lời. |
| **RAGAS** | Bộ khung đánh giá RAG, gồm các chỉ số như Faithfulness, Answer Relevancy, Context Precision và Context Recall. | Dùng làm khung tổ chức metric cho retrieval/generation. Điểm do LLM chấm cần được kiểm định bằng người thật, đặc biệt khi judge và model trả lời cùng họ. |
| **ReAct (2023)** – *Reasoning and Acting* | Mô hình hóa agent theo chu trình suy luận và hành động/gọi công cụ, quan sát kết quả rồi tiếp tục xử lý. | Là cơ sở khái niệm cho router/tool-calling: chọn Visual Search, Product QA, search, compare hoặc hỏi lại. Cần chấm cả chọn route lẫn tham số công cụ và TSR end-to-end. |

### Bài học tổng hợp cho thiết kế hệ thống

1. **Phân loại trước, tìm sau:** type gate có thể giảm nhầm lẫn giữa giày, áo, mũ và phụ kiện; nhưng cần đo lỗi khi gate lọc nhầm.
2. **Ảnh người dùng khác ảnh catalog:** benchmark ảnh studio không thay thế được tập ảnh ngoài đời.
3. **Cho phép hỏi lại hoặc tìm bằng chữ:** khi ảnh mơ hồ hoặc nhiều món, không nên ép hệ thống đoán.
4. **RAG cần trích dẫn và cơ chế từ chối:** retriever tìm được đoạn phù hợp không đồng nghĩa câu trả lời đã chính xác.
5. **Không dùng điểm tự động làm bằng chứng duy nhất:** nhãn eval, LLM judge và trích dẫn cần được kiểm tra thủ công.
6. **Xác minh nguồn trước khi trích dẫn học thuật:** tài liệu dự án tự đánh dấu một số thông tin về năm, license và trích dẫn ứng dụng/bài báo là cần kiểm tra lại ở nguồn chính thức.

---

# CĂN CỨ TRONG WORKSPACE

- `MSA/MSA_DoAn1_HoanChinh/BAO_CAO_TONG_HOP.md`
- `MSA/MSA_DoAn1_HoanChinh/02_TuanDat/docs/US_04_phuong_phap_thu_thap.md`
- `MSA/MSA_DoAn1_HoanChinh/02_TuanDat/docs/US_10_bang_nguon_va_tinh_chinh_thong.md`
- `MSA/MSA_DoAn1_HoanChinh/04_Khoa/docs/US_12_do_do_visual_search.md`
- `MSA/MSA_DoAn1_HoanChinh/03_Chien/docs/US_13_do_do_qa_rag.md`
- `MSA/MSA_DoAn1_HoanChinh/03_Chien/docs/US_14_do_do_search_compare_agent.md`
- `MSA/MSA_DoAn1_HoanChinh/01_Trung/docs/US_18_chot_do_do_va_nguong.md`
- `MSA/MSA_DoAn1_HoanChinh/04_Khoa/docs/US_21_he_thong_va_bai_bao_tuong_tu.md`
- `MSA/MSA_DoAn1_HoanChinh/00_Chung/THUAT_NGU.md`
