# US_21 – Khảo sát hệ thống & bài báo tương tự (Sheet 3 – Bảng E)

| Mục | Nội dung |
|---|---|
| Mã US | US_21 (Owner: Khoa, Support: Chiến) – Sprint 1, 2.0 pt |
| Mục tiêu | Học kiến trúc và bài học từ hệ thống/bài báo đã có thay vì tự mò |
| Đầu ra | Bảng E (file này) |
| Tiêu chí nghiệm thu | Mỗi hệ thống/bài báo có "điểm đáng học" và "liên hệ đồ án" |
| Trạng thái | **Hoàn thành (bản khảo sát tài liệu)** – thông tin tổng hợp từ kiến thức công khai của tác nhân, **chưa mở lại từng nguồn để đối chiếu**; mục nào không chắc gắn `[cần xác minh]`. Nhóm cần mở arXiv/ACM/trang chính thức để xác minh tên, tác giả, năm trước khi đưa vào báo cáo. Trải nghiệm thực tế Shopee/Google Lens: **CHƯA LÀM** (cần người thật dùng app). |

## E1. Sản phẩm / hệ thống

| Tên | Tổ chức / Năm | Điểm đáng học | Liên hệ với đồ án |
|---|---|---|---|
| Google Lens | Google, 2017 | Nhận dạng/khoanh vùng vật thể trước rồi mới tìm; cho người dùng chọn lại vùng quan tâm; kết hợp tìm ảnh với tìm văn bản (multisearch) | Cải tiến I1 (crop vật thể) và gợi ý UI "chọn vùng"; khi τ_v thấp thì gợi ý mô tả bằng chữ (đã cài trong `VisualSearcher.query`) |
| Pinterest Lens / Visual Search | Pinterest, 2015–2017 | Pipeline detect → embed → index; dùng tín hiệu tương tác để huấn luyện embedding; tìm theo "ý tưởng" chứ không chỉ SP trùng | Cấu trúc 3 bước của `build_index.py` / `visual.py`; tầng category trong eval_visual đo "giống loại" |
| Shopee – Tìm kiếm bằng hình ảnh | Shopee (Sea), ~2019 `[cần xác minh năm]` | Có sẵn trên sàn VN; trả về SP cùng loại kèm bộ lọc giá/đánh giá | Mốc trải nghiệm thực tế cho người dùng VN – nhóm cần tự thử 10 ảnh và ghi ưu/nhược (CHƯA LÀM) |
| Amazon StyleSnap | Amazon, 2019 | Tìm thời trang theo ảnh "outfit"; tách từng món trong ảnh người mặc cả bộ | Rủi ro "ảnh người mặc cả bộ" trong I19 – type gate hỏi lại "bạn muốn tìm áo, giày hay mũ?" |
| Amazon Rufus | Amazon, 2024 | Trợ lý hỏi đáp mua sắm dựa trên thông tin SP + review + Q&A cộng đồng | Gần nhất với luồng QA (RAG) + so sánh; bài học: luôn dẫn nguồn và không bịa thông số |
| Alibaba Pailitao (拍立淘) | Alibaba, 2014 | Phân loại danh mục trước khi tìm (category prediction) để thu hẹp không gian; ảnh người dùng khác ảnh studio | Trực tiếp ủng hộ **I19 type gate**; nhấn mạnh phải đo trên ảnh ngoài đời |

## E2. Bài báo

| Bài báo | Tác giả / Nơi công bố | Điểm đáng học | Liên hệ với đồ án |
|---|---|---|---|
| Visual Search at Pinterest | Jing và cộng sự, KDD 2015 | Kiến trúc tìm ảnh quy mô lớn, chia detect – embed – index; dùng đặc trưng CNN | Khung kiến trúc visual search của nhóm |
| Visual Search at eBay | Yang và cộng sự, KDD 2017 | Dự đoán danh mục trước rồi tìm trong danh mục; mã nhị phân để tiết kiệm bộ nhớ | Type gate (I19); FAISS Flat đủ cho < 100K vector nên chưa cần nén |
| Visual Search at Alibaba | Zhang và cộng sự, KDD 2018 | Category prediction + phát hiện vật thể + học embedding từ hành vi người dùng; xử lý ảnh đời thực | I1 + I19; hạn chế của nhóm: không có dữ liệu hành vi |
| Learning Transferable Visual Models From Natural Language Supervision (CLIP) | Radford và cộng sự, ICML 2021 | Học contrastive ảnh–text trên 400M cặp; zero-shot qua prompt văn bản | Cơ sở để vừa tìm bằng ảnh vừa làm type gate zero-shot bằng prompt |
| Reproducible scaling laws for contrastive language-image learning (OpenCLIP) | Cherti và cộng sự, CVPR 2023 | Huấn luyện lại CLIP mở trên LAION-2B; checkpoint công khai | Ứng viên `openclip_b32_laion2b` |
| Sigmoid Loss for Language Image Pre-Training (SigLIP) | Zhai và cộng sự, ICCV 2023 | Thay softmax contrastive bằng sigmoid theo cặp, hiệu quả ở batch nhỏ | Ứng viên `siglip_b16` |
| SigLIP 2 | Tschannen và cộng sự, arXiv 2025 | Đa ngôn ngữ, thêm mục tiêu dày đặc/định vị | Ứng viên tương lai (chưa chạy – xem US_19) |
| Contrastive language and vision learning of general fashion concepts (FashionCLIP) | Chia và cộng sự, Scientific Reports 2022 | Fine-tune CLIP trên catalog thời trang (Farfetch) | Ứng viên chuyên miền `fashionclip` |
| Marqo-FashionCLIP / FashionSigLIP (blog + model card) | Marqo, 2024 | Generalized Contrastive Learning trên dữ liệu thời trang; tác giả báo cáo thắng FashionCLIP 2.0 | Ứng viên `marqo_fashionsiglip`; **lưu ý rò rỉ**: tác giả có dùng bộ "KAGL" (Kaggle Fashion Product Images – cùng nguồn với FPI) trong đánh giá `[cần xác minh có dùng để huấn luyện hay không]` |
| DINOv2: Learning Robust Visual Features without Supervision | Oquab và cộng sự, TMLR 2024 (arXiv 2023) | Self-supervised, đặc trưng thị giác mạnh cho tương đồng hình dáng/kết cấu | Ứng viên thuần ảnh `dinov2_s` |
| Deep Residual Learning for Image Recognition (ResNet) | He và cộng sự, CVPR 2016 | Baseline CNN kinh điển | Baseline `resnet50` |
| Billion-scale similarity search with GPUs (FAISS) | Johnson, Douze, Jégou – IEEE Trans. Big Data 2019 (arXiv 2017) | Thư viện tìm kiếm vector; Flat chính xác, IVF/HNSW xấp xỉ | Chọn `IndexFlatIP` (catalog 4.593 vector – search đo được < 1 ms, xem US_22) |
| Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | Lewis và cộng sự, NeurIPS 2020 | Kết hợp retriever + generator | Nền tảng luồng QA (Chiến) |
| RAGAS | Es và cộng sự, 2023 (EACL 2024 demo) | Độ đo faithfulness/answer relevancy/context precision | Độ đo RAG (US_13) |
| ReAct | Yao và cộng sự, ICLR 2023 | Agent xen kẽ suy luận và gọi công cụ | Router/Agent (Trung) |
| ViMRHP: A Vietnamese Benchmark Dataset for Multimodal Review Helpfulness Prediction | Nguyen và cộng sự, NLDB 2025 `[cần xác minh tên đầy đủ]` | Review TMĐT tiếng Việt thật (Shopee) kèm điểm hữu ích | Nguồn review tiếng Việt của đồ án (shared_data) |
| CAMEO (NTCIR-19) | NTCIR-19, 2025–2026 `[cần xác minh nội dung nhiệm vụ]` | Nhiệm vụ đánh giá chung (shared task) liên quan hội thoại/đa phương thức | Tham khảo cách tổ chức bộ đánh giá; nhóm cần đọc trang chính thức trước khi trích dẫn |

## Bài học rút ra cho đồ án
1. **Phân loại trước, tìm sau** (eBay, Alibaba, Google Lens) → I19 type gate là cải tiến có cơ sở.
2. **Ảnh người dùng ≠ ảnh studio** (Alibaba, StyleSnap) → bộ eval hiện tại chỉ là xấp xỉ; nhóm bắt buộc phải có 80–100 ảnh ngoài đời.
3. **Khi không chắc, hỏi lại hoặc chuyển sang tìm bằng chữ** (Google multisearch) → τ_v + câu gợi ý trong `visual.py`.
4. **Model chuyên miền có thể đã "thấy" dữ liệu đánh giá** (Marqo, FashionCLIP) → số trên FPI có thể lạc quan cho các model này; ưu tiên số trên ảnh ngoài đời khi có.
