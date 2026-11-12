# US_16 – Bộ đánh giá Product QA (eval_qa) và bộ định tuyến (eval_router)

| Mục | Nội dung |
|---|---|
| Mã US | US_16 (6 pt, Sprint 2, Owner: Chiến, Support: Tuấn Đạt) |
| Mục tiêu | Đo chất lượng RAG (đặc biệt việc không bịa) và router (7 route) |
| Đầu ra | `eval/eval_qa.jsonl` (280 câu), `eval/eval_router.jsonl` (78 câu), script `src/scripts/build_eval_qa.py`, `src/scripts/build_eval_router.py`, raw Gemini `eval/raw/eval_qa_gemini_raw.jsonl`, câu viết tay `eval/eval_qa_handwritten.jsonl` |
| Tiêu chí nghiệm thu | ≥ 150 cặp; > 15% không có đáp án; ≥ 30% được 2 người kiểm tay; eval_router ≥ 60 câu, ≥ 15 chitchat/ngoài phạm vi, ≥ 30% do 2 người duyệt nhãn |
| Trạng thái | **Khung sẵn – cần người thật duyệt.** Mọi ràng buộc tự động đạt (`--check` không lỗi); **chưa có người thật duyệt** (reviewed_by=[], annotator trống) – **nhóm cần duyệt ≥ 30% bởi 2 người** |

## Tóm tắt 5 dòng
1. eval_qa: 280 câu hỏi tiếng Việt trên 80 SP ViMRHP, 71 câu (25,4 %) không có đáp án; 251 câu Gemini sinh + 29 câu tác nhân viết tay.
2. eval_router: 78 câu gắn 7 nhãn route, 21 câu chitchat/ngoài phạm vi.
3. Chưa có người thật duyệt (cột annotator trống) → chưa đạt tiêu chí ≥ 30 % được 2 người kiểm.
4. 45/280 câu eval_qa và 4/78 câu eval_router hỏi về trang sức/tất – ngoài phạm vi taxonomy: `eval/ngoai_pham_vi_taxonomy_v1.csv`, QUYET_DINH mục B.
5. Loại số liệu: [Chưa người duyệt].
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## 1. eval_qa.jsonl – trên dữ liệu THẬT ViMRHP

Schema mỗi dòng: `id, product_id, question, answer, answerable, evidence_review_ids, type, origin, reviewed_by, split`.

| Thống kê (đo bằng `PYTHONPATH=src python src/scripts/build_eval_qa.py --check`) | Giá trị |
|---|---|
| Số câu | **280** trên **80 SP** (bỏ đồng hồ, bỏ SP không phải thời trang như keo dán giày) |
| answerable=false | **71 (25,4%)** > 15% ✔ (sau khi sửa nhãn qa108) |
| Theo origin | `llm_gemini` 251 (190 có đáp án + 61 không) · `viet_tay_tac_nhan` 29 (19 + 10) |
| Theo type | so_sanh 55 · ngoai_pham_vi 50 · chat_lieu 49 · form 32 · size_giay 27 · giao_hang 26 · size_ao_quan 16 · gia 13 · do_ben 12 |
| Split (theo product_id, không lẫn SP) | test 153 · val 127 |
| Đã 2 người duyệt | **0** (chưa có người thật) |

### Quy trình sinh

1. **Chọn SP** (seed 42): cân đối 5 nhóm con ViMRHP, ≥ 10 review/SP.
2. **Gemini sinh theo lô**: mỗi lời gọi gửi 3–7 SP kèm tối đa 25 review thật/SP (cắt 300 ký tự), đánh số R1..Rn. Yêu cầu mỗi SP 3 câu có đáp án (loại khác nhau, đáp án "Theo đánh giá của khách…", bằng chứng R-mã) + 1 câu không có đáp án (giá chính xác, còn hàng, chính sách, xuất xứ, số đo cm). JSON mode, temperature 0.4.
   - Thực tế lượt này: 6 lô (3 SP/lô) bằng `gemini-3.5-flash` (thinkingBudget=0) trước khi **hết quota free tier 20 request/ngày/model** (HTTP 429, `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, key dùng chung cả nhóm); 7 lô còn lại (7 SP/lô) bằng `gemini-3.5-flash-lite`.
3. **Ánh xạ & kiểm bằng chứng**: R-mã → `comment_id` thật; loại câu có bằng chứng không tồn tại, loại sai type, câu có đáp án mà không có bằng chứng.
4. **Câu viết tay của tác nhân** (29 câu): tập trung vào chỗ Gemini sinh ít – size áo/quần theo chiều cao-cân nặng, size giày (tăng/lùi size), câu tồn kho/chính sách/thành phần vải. Câu có đáp án được viết sau khi đọc review thật (mã review ghi trong evidence); câu không đáp án đã được kiểm bằng regex rằng review của SP không chứa thông tin đó.
5. `--check` kiểm: ≥150 câu, >15% không đáp án, schema, type/origin hợp lệ, evidence thuộc đúng SP, có cả 2 origin.

### Điểm cần người duyệt ưu tiên (phát hiện khi kiểm tự động)

- 7 câu `gia` answerable=false mà review của SP **có nhắc giá lúc mua sale** (qa012, qa072, qa076, qa156, qa176, qa192, qa243). Đáp án "chưa có thông tin về giá bán hiện tại" vẫn đúng vì giá trong review không phải giá hiện tại – nhưng người duyệt nên xác nhận; prompt RAG v1.0 đã có quy tắc riêng.
- Câu Gemini sinh có thể thiên về từ ngữ giống review (dễ cho retrieval từ vựng) ⇒ báo cáo riêng số đo theo `origin`.
- Bằng chứng có thể chưa đầy đủ (Gemini chỉ dẫn 1–3 review) ⇒ Hit@K có thể bị đánh giá thấp.

### Hướng dẫn duyệt cho nhóm (để đạt tiêu chí ≥ 30% bởi 2 người)

1. Lấy ngẫu nhiên ≥ 84 câu (30% của 280), ưu tiên đủ mọi `type` và cả 2 `origin`.
2. Mỗi người độc lập: đọc review trong `evidence_review_ids` (tra trong `shared_data/vimrhp_fashion_products.jsonl`), đánh dấu Đúng / Sửa / Loại cho (câu hỏi, đáp án, answerable, evidence).
3. Ghi tên vào `reviewed_by` (vd `["Chien","Dat"]`), sửa trực tiếp nếu cả hai đồng ý; bất đồng ⇒ người thứ 3 quyết. Báo cáo tỉ lệ đồng thuận (Cohen's κ trên nhãn Đúng/Sai).

## 2. eval_router.jsonl

Schema: `id, text, has_image, route, product_id, note, origin, annotator_1, annotator_2` (thêm `product_id` = SP trong ngữ cảnh phiên, để kiểm luật R14).

| Route | Số câu | Ghi chú |
|---|---|---|
| visual | 11 | có ảnh; 1 câu chỉ ảnh không chữ; có câu ảnh + bộ lọc |
| qa | 15 | tên SP thật ViMRHP; 2 câu dùng đại từ "này" với product_id từ phiên; 1 câu hỏi tồn kho (phải ở QA và trả "chưa có thông tin", không chuyển Gemini) |
| search | 13 | bộ lọc giá/màu/size |
| compare | 9 | 2–3 SP thật cùng nhóm |
| gemini_chitchat | 11 | chào hỏi, cảm xúc, tư vấn phối đồ chung |
| gemini_ood | 10 | kiến thức chung, code, tin tức, nội dung nguy hại |
| clarify | 9 | thiếu SP/ảnh, so sánh khác nhóm (R19) |
| **Tổng** | **78** | chitchat + ood = 21 ≥ 15 ✔ |

Đa dạng ngôn ngữ: có dấu, không dấu (vd "tim ao giong hinh"), teencode/viết tắt (ko, k, v, bn, sz, tks, hnay, sp). Toàn bộ `origin = viet_tay_tac_nhan` (tác nhân AI viết); `annotator_1/2` để trống cho 2 người thật gán nhãn độc lập (≥ 30% = ≥ 24 câu), sau đó tính đồng thuận.

Các câu ranh giới cần nhóm thống nhất quy ước: "trời mưa mặc gì" (chitchat hay search?), "tư vấn mua điện thoại" (ood), "còn size 40 không" có product_id (qa, không phải Gemini).
