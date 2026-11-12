# Phần việc của Chiến (trích tự động từ MSA_PLAN_v2.xlsx)

## Vai trò (sheet Phân công)

- **Thành viên**: Chiến
- **Vai trò chính**: Dữ liệu tiếng Việt & RAG
- **Tuần 1**: Crawl sàn TMĐT Việt Nam (tuân thủ robots/ToS); khảo sát text-embedding & LLM; khảo sát hệ thống tương tự (hỗ trợ).
- **Tuần 2**: Độ đo RAG + độ đo Tìm/So sánh/Agent; eval_qa (150 câu); hỗ trợ benchmark text-embedding.
- **Tuần 3**: Kho tri thức + RAG pipeline; trích nguồn & từ chối khi thiếu info; cải tiến RAG (hybrid, rewriting). Prompt + nhánh Gemini US_51.
- **Đầu ra bắt buộc**: Dữ liệu crawl, eval_qa, RAG, số liệu Faithfulness/hallucination
- **Lưu ý**: Rủi ro lớn nhất là crawl bị chặn: có kế hoạch B trong sheet 'Rủi ro & Quy ước'.

## User story mà Chiến là Owner

### US_07 – Crawl bổ sung dữ liệu sàn TMĐT Việt Nam (quy mô nhỏ) (5.0 pt, Sprint 1, ưu tiên Medium)
- Muốn: crawl 300-500 sản phẩm (tên, giá, mô tả, size, ảnh, review tiếng Việt), tuân thủ robots.txt và có delay
- Để: có dữ liệu tiếng Việt thực tế cho phần hỏi đáp
- Support: Hoàng
- DOCS (đầu ra): script 02_crawl_vn.py, file raw, ghi chú robots.txt/ToS đã kiểm tra
- TEST (nghiệm thu): Có ít nhất 300 sản phẩm và 1.000 review tiếng Việt; không bị block; có bằng chứng đã kiểm tra robots/ToS

### US_13 – Khảo sát độ đo cho Product QA / RAG (3.0 pt, Sprint 2, ưu tiên High)
- Muốn: liệt kê độ đo retrieval (Hit@K, MRR, context precision/recall) và generation (EM/F1, ROUGE, BERTScore, faithfulness, answer relevancy, hallucination rate, human eval)
- Để: đánh giá được cả khâu tìm tài liệu lẫn khâu sinh câu trả lời
- Support: Khoa
- DOCS (đầu ra): Sheet '2_Độ đo' - phần Product QA/RAG
- TEST (nghiệm thu): Mỗi độ đo có công thức, ưu/nhược và quyết định chọn/không chọn

### US_14 – Khảo sát độ đo cho Tìm/So sánh & Agent (2.0 pt, Sprint 2, ưu tiên Medium)
- Muốn: liệt kê intent accuracy, tool-call accuracy, attribute F1, task success rate, latency end-to-end, chi phí/lượt
- Để: đo được chất lượng của cả agent chứ không chỉ từng module
- Support: Trung
- DOCS (đầu ra): Sheet '2_Độ đo' - phần Search/Compare & Agent
- TEST (nghiệm thu): Mỗi độ đo có công thức, ưu/nhược và quyết định

### US_16 – Xây bộ đánh giá Product QA (câu hỏi - đáp án - nguồn) (6.0 pt, Sprint 2, ưu tiên High)
- Muốn: tạo ít nhất 150 cặp Q&A tiếng Việt (size, chất liệu, độ bền, giá, so sánh, câu hỏi ngoài phạm vi) gồm cả câu LLM sinh và câu viết tay; gồm cả size giày + size áo/quần S-XL, chất liệu, form; thêm eval_router.jsonl ≥ 60 câu gắn nhãn route {visual, qa, search, compare, gemini_chitchat, gemini_ood, clarify}
- Để: đo được chất lượng RAG, đặc biệt là việc không bịa
- Support: Tuấn Đạt
- DOCS (đầu ra): eval_qa.jsonl, eval_router.jsonl
- TEST (nghiệm thu): Ít nhất 150 cặp; trên 15% là câu hỏi không có đáp án; ít nhất 30% được 2 người kiểm tay; eval_router có ≥ 15 câu chitchat/ngoài phạm vi; ≥ 30% do 2 người duyệt nhãn

### US_20 – Khảo sát text-embedding & LLM cho RAG tiếng Việt (3.0 pt, Sprint 1, ưu tiên High)
- Muốn: liệt kê các mô hình embedding đa ngôn ngữ và LLM (API và open-source) phù hợp tiếng Việt
- Để: chọn được ứng viên cho Product QA
- Support: Trung
- DOCS (đầu ra): Sheet '3_Khảo sát phiên bản' - Bảng C và D
- TEST (nghiệm thu): Có ít nhất 4 text-embedding và 5 LLM, ghi rõ ưu/nhược cho tiếng Việt

### US_33 – Xây kho tri thức (chunk mô tả, specs, review) & vector store (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: chunk dữ liệu theo từng sản phẩm/trường, gắn metadata product_id và nguồn
- Để: truy xuất đúng tài liệu cho câu hỏi về một sản phẩm cụ thể
- Support: Tuấn Đạt
- DOCS (đầu ra): ingest script + vector store
- TEST (nghiệm thu): Mỗi chunk truy ngược được product_id và nguồn

### US_34 – Hỏi đáp về sản phẩm bằng tiếng Việt (8.0 pt, Sprint 3, ưu tiên High)
- Muốn: hỏi 'đôi này có bền không?', 'còn size 40 không?', 'áo này mặc size M có rộng không?' và nhận câu trả lời dựa trên mô tả và đánh giá
- Để: quyết định mua nhanh hơn
- Support: Trung
- DOCS (đầu ra): API /qa
- TEST (nghiệm thu): Hit@5 và Faithfulness đạt ngưỡng mục tiêu trên eval_qa

### US_35 – Trả lời có trích nguồn và biết từ chối khi thiếu thông tin (3.0 pt, Sprint 3, ưu tiên High)
- Muốn: thấy câu trả lời kèm nguồn và được báo 'chưa có thông tin' khi dữ liệu không có
- Để: tin tưởng trợ lý và không bị thông tin sai
- Support: Tuấn Đạt
- DOCS (đầu ra): prompt grounding + guard
- TEST (nghiệm thu): Từ 90% câu hỏi ngoài phạm vi trong eval_qa được từ chối đúng thay vì bịa

### US_51 – Trò chuyện tự nhiên: Gemini xử lý chitchat, ngoài phạm vi, câu khó & fallback khi nội bộ không tự tin (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: hỏi chuyện ngoài mua sắm (chào hỏi, 'trời mưa mặc gì cho hợp?') hoặc câu hệ thống nội bộ không chắc và nhận câu trả lời tự nhiên có nhãn nguồn
- Để: hội thoại không bị cụt ('xin lỗi tôi không hiểu') nhưng vẫn không bịa thông tin cửa hàng
- Support: Hoàng
- DOCS (đầu ra): prompts/gemini_fallback.md (system prompt + few-shot, có version) + nhánh Gemini trong router + ngưỡng τ
- TEST (nghiệm thu): Route accuracy ≥ 90% trên eval_router; 0/60 phản hồi Gemini bịa giá/size/tồn kho; UI có nhãn nguồn; 429/timeout trả thông điệp dự phòng; câu in-domain có product_id không bị đẩy sang Gemini trừ khi retrieval rỗng


## User story mà Chiến là Support

- US_01 – Kickoff & chốt phạm vi (Owner: Trung)
- US_03 – Họp daily 15' + review cuối tuần (Owner: Trung)
- US_04 – Liệt kê & so sánh các phương pháp thu thập dữ liệu (Owner: Tuấn Đạt)
- US_11 – Tạo tập ảnh truy vấn 'ngoài đời' (Owner: Tuấn Đạt)
- US_15 – Xây bộ đánh giá Visual Search (query + ground truth) (Owner: Khoa)
- US_21 – Khảo sát hệ thống & bài báo tương tự (Owner: Khoa)
- US_23 – Benchmark text-embedding cho RAG (ít nhất 3 model) (Owner: Hoàng)
- US_24 – Benchmark LLM trả lời (1 API + 1-2 open-source) (Owner: Tuấn Đạt)
- US_27 – Báo cáo + slide mốc 2 tuần (dữ liệu, độ đo, khảo sát) (Owner: Trung)
- US_36 – Tóm tắt đánh giá khách hàng theo sản phẩm (ưu/nhược) (Owner: Tuấn Đạt)
- US_39 – Gợi ý 'nên chọn cái nào' theo nhu cầu (stretch) (Owner: Hoàng)
- US_42 – Hội thoại nhiều lượt có nhớ ngữ cảnh (stretch) (Owner: Trung)
- US_44 – Đo baseline hệ thống end-to-end (Owner: Khoa)
- US_45 – Thực hiện ít nhất 4 cải tiến ưu tiên cao & đo trước/sau (Owner: Khoa)
- US_46 – Kiểm thử 15-20 kịch bản & sửa lỗi (Owner: Tuấn Đạt)
- US_47 – Diễn tập demo + video dự phòng + gắn tag release (Owner: Trung)

## Lịch theo ngày của Chiến

- N1 (05/11): US_07: Chọn 1-2 sàn TMĐT VN, đọc robots.txt và điều khoản, xem cấu trúc trang sản phẩm.
- N2 (06/11): US_07: Viết crawler thử cho 1 sàn: 1 trang sản phẩm -> JSON; chạy thử 20 sản phẩm.
- N3 (07/11): US_07: Chạy crawl 300-500 sản phẩm + review tiếng Việt; lưu raw + log.
- N4 (08/11): US_07: Hoàn tất crawl; kiểm tra 50 mẫu ngẫu nhiên xem ảnh/giá/review có đúng không.
- N5 (09/11): Gộp dữ liệu crawl vào schema. US_20: bắt đầu khảo sát text-embedding & LLM tiếng Việt.
- N6 (10/11): US_20: Hoàn tất bảng text-embedding & LLM (Sheet 3, Bảng C và D).
- N7 (11/11): Nghỉ (hoặc bù việc trễ).
- N8 (12/11): US_13: Khảo sát độ đo cho Product QA/RAG. US_14: Khảo sát độ đo cho Tìm/So sánh & Agent.
- N9 (13/11): US_16: Dùng LLM sinh Q&A từ mô tả/review + tự viết câu hỏi tay (kể cả câu hỏi ngoài phạm vi). Thêm eval_router ≥ 60 câu (Gemini sinh nháp chitchat/ngoài phạm vi, kiểm tay).
- N10 (14/11): US_16: Hoàn tất eval_qa (kiểm tay 30%, 2 người). Hỗ trợ US_23.
- N11 (15/11): Tổng hợp kết quả text-embedding + LLM thành bảng; hỗ trợ viết phần độ đo RAG.
- N12 (16/11): Điền Sheet 3 Bảng C; viết phần độ đo RAG và phân tích lỗi retrieval.
- N13 (17/11): Slide phần độ đo.
- N14 (18/11): Tập phần độ đo.
- N15 (19/11): US_33: Chunk mô tả/specs/review, nạp vào vector store, gắn product_id.
- N16 (20/11): US_34: RAG pipeline v0: retrieve + LLM + prompt có trích nguồn. US_51: prompt fallback v1 (dùng chung file prompt với US_34).
- N17 (21/11): US_35: Trích nguồn + từ chối khi thiếu thông tin. US_34: hoàn tất /qa.
- N18 (22/11): US_45: Cải tiến RAG: hybrid BM25 + dense, query rewriting tiếng Việt, prompt grounding. I16: prompt v2.
- N19 (23/11): Sửa bug RAG; đo lại Faithfulness, hallucination rate.
- N20 (24/11): Chuẩn bị dữ liệu demo (5 kịch bản đẹp, đã kiểm chứng chạy ổn).
- N21 (25/11): Diễn tập phần hỏi đáp/RAG.