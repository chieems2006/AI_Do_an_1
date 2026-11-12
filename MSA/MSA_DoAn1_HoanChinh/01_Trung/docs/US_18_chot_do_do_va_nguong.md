# US_18 – Chốt bộ độ đo + lý do + ngưỡng mục tiêu

| Mục | Nội dung |
|---|---|
| Mã US | US_18 (Owner: Trung, Support: Khoa) |
| Mục tiêu | Chọn độ đo chính/phụ cho từng module và đặt ngưỡng mục tiêu **dựa trên baseline thật**, để mọi cải tiến Tuần 3 đo bằng cùng thước |
| Đầu ra | File này (= cột "Nhóm chọn" + Bảng B của sheet `2_Độ đo`) |
| Tiêu chí nghiệm thu | Mỗi độ đo được chọn có ≥ 1 lý do gắn mục tiêu sản phẩm |
| Trạng thái | **Đạt tiêu chí nghiệm thu** (mỗi độ đo có lý do gắn mục tiêu). Bảng ngưỡng **cập nhật 05/11 bởi Tác nhân 2** theo số mới nhất của Khoa (5 model), Chiến (RAG e2e), Đạt (Bảng D). TSR toàn hệ thống, latency e2e **CHƯA ĐO**. Chốt chính thức ở họp N11 |

## Tóm tắt 5 dòng
1. Mỗi module có 1–3 độ đo **chính**, chọn vì gắn trực tiếp với trải nghiệm người dùng (ví dụ: người dùng chỉ nhìn 5 kết quả đầu → Recall@5).
2. Visual: macro Recall@5 + MRR@10 + CTE@5 + latency; RAG: Hit@5 (tìm) + Faithfulness/Hallucination/Abstention (trả lời); Agent: route accuracy, TSR, unsupported-store-fact.
3. Không chọn ROUGE/BLEU vì không phản ánh đúng/sai nghĩa của câu trả lời tiếng Việt.
4. Ngưỡng mục tiêu đặt **từ baseline thật**: chỉ số nào baseline đã vượt thì nâng (MRR 0,75, macro R@5 0,85); chưa đạt thì giữ (route accuracy 0,90 – hiện 0,878).
5. Loại số liệu: visual [Thật–tổng hợp]; RAG generation [LLM chấm]; mọi bộ eval [Chưa người duyệt] – thuật ngữ ở `00_Chung/THUAT_NGU.md`.

Data version chung: `shared_data v1 (prep_shared_data.py seed 42)`; phần cứng 2 CPU, 7 GB RAM, không GPU.

## 1. Bộ độ đo đã chọn
| Module | Độ đo CHÍNH | Lý do gắn mục tiêu sản phẩm | Độ đo PHỤ |
|---|---|---|---|
| Visual search | macro Recall@5 theo 4 nhóm; MRR@10; Cross-type error@5; Latency P95 | Người dùng chỉ nhìn ~5 kết quả đầu; macro để nhóm mũ/phụ kiện nhỏ không bị nhóm áo che; nhầm áo↔giày là lỗi khó chấp nhận nhất (R17) | Recall@1/10, NDCG@10, cat_P@5 (nhiều đáp án đúng) |
| RAG – retrieval | Hit@5 (lọc theo product_id) | Retrieval sai thì LLM không thể đúng; tách lỗi "không tìm ra" khỏi "nói sai" | MRR@10, AUC tách câu có/không đáp án (để chọn τ_r) |
| RAG – generation | Faithfulness; Hallucination rate; Abstention accuracy | Mục tiêu "không bịa thông số"; QA thiếu dữ kiện phải nói "chưa có thông tin" | F1 token (câu factual ngắn), human eval 50 câu |
| Search & Compare | Attribute extraction F1; Comparison factual correctness | Bộ lọc sai thì kết quả sai từ đầu; bảng so sánh lấy từ DB nên phải ~100% | – |
| Agent | Route accuracy (eval_router ≥ 60 câu); Task Success Rate; Unsupported-store-fact rate nhánh Gemini | Router là "não"; TSR là chỉ số Tuần 3 cần tăng; Gemini không được bịa giá/size/tồn kho/danh mục | Fallback rate, cache hit rate, latency e2e P95, token/100 lượt |
| Không chọn | ROUGE/BLEU | Không phản ánh đúng câu trả lời hội thoại tiếng Việt | – |

## 2. Bảng ngưỡng (Bảng B) – baseline thật → mục tiêu
| Độ đo | Chiều | Baseline đo thật (nguồn) | Mục tiêu sheet ban đầu | **Mục tiêu đề xuất** | Lý do điều chỉnh |
|---|---|---|---|---|---|
| Visual macro Recall@5 (test) | ↑ | **0,846** DINOv2-S / 0,833 SigLIP / 0,829 FashionCLIP / 0,721 CLIP B/32 (CLIP B/32 là baseline cũ) – `04_Khoa/results/bench_image_embed.csv` [Thật–tổng hợp] | 0,80 | **0,85** trên test tổng hợp; **0,70** trên ảnh ngoài đời (CHƯA ĐO) | 3 model đã vượt 0,80 trên truy vấn tổng hợp → nâng; ảnh thật sẽ khó hơn nhiều nên đặt mục tiêu riêng |
| Visual MRR@10 (test) | ↑ | **0,791** DINOv2-S (CLIP B/32 0,660) | 0,60 | **0,75** | Baseline đã vượt 0,70 → nâng để còn ý nghĩa |
| Visual Cross-type error@5 (test) | ↓ | **0,043** DINOv2-S không gate; FashionCLIP 0,062 → 0,044 có gate (CLIP B/32 0,076) | 0,10 | **≤ 0,05** (tập khó ≤ 0,08) | Đã đạt với model chọn; giữ để giám sát khi đổi model/ảnh thật |
| Visual latency P95 nhúng 1 ảnh (ms) | ↓ | DINOv2-S 1.924 / SigLIP 214 / FashionCLIP 390 (p50 289 / 190 / 294; 60 lần đo; CPU 2 luồng **dùng chung**) | 1.000 | **1.000** (giữ) | P95 nhiễu mạnh do máy dùng chung; đo lại trên máy demo. Tiêu chí US_30 (phản hồi API < 1,5 s) đã đạt 97,5 % truy vấn với CLIP B/32 (Hoàng) |
| RAG Hit@5 theo product_id (test) | ↑ | **0,895** Hybrid BM25 + e5-small (n=114; val 0,832); TF-IDF char 0,877 – `03_Chien/results/rag_retrieval_eval.json` [Chưa người duyệt] | 0,85 | **0,90** | Đã đạt 0,85 trên test; val thấp hơn → mục tiêu 0,90 trên test |
| τ_r (ngưỡng retrieval) | – | Với τ_r = 0,35: **60,1% câu có đáp án bị chặn**; AUC tách = 0,724 | 0,35 | **hiệu chỉnh lại** (đề xuất quét trên val, chọn theo Abstention ≥ 0,9 với tỉ lệ chặn câu có đáp án ≤ 20%) | Thang điểm TF-IDF khác thang dense |
| RAG Faithfulness | ↑ | **1,00** (Chiến, 52 câu test, hybrid + flash-lite) – `03_Chien/results/rag_e2e_eval.json`; **0,939** (Đạt, 36 câu, Bảng D) – `02_TuanDat/results/bench_llm_summary.json` [LLM chấm] | 0,85 | 0,85 (giữ) | Giám khảo LLM có thể dễ dãi → cần 50 câu người chấm trước khi coi là đạt |
| RAG Hallucination rate | ↓ | **0,00** (Chiến, 52 câu) / **0,111** (Đạt, 36 câu; lỗi đến từ 1 review spam) [LLM chấm] | 0,10 | 0,10 (giữ) | Hai số khác vì khác bộ câu + khác prompt/giám khảo; lọc review spam trước khi chunk |
| RAG Abstention accuracy | ↑ | **1,00** (15/15, Chiến); false-refusal 0/37 | 0,90 | 0,90 (giữ) | n nhỏ (15 câu) – mở rộng khi eval_qa có người duyệt |
| Router route accuracy | ↑ | **0,878** v1 trên tập held-out Gemini sinh (n=49); v0 0,667 trên bộ Chiến (n=78) – `results/router_eval_v*.json` | 0,90 | **0,90** (giữ) | Chưa đạt trên held-out; v2 + eval người thật |
| Fallback rate (chuyển Gemini) | ↓ | **0,273** (47/172 câu eval) | 0,10–0,25 | **≤ 0,25** trên log demo thật | Bộ eval cố ý nhiều chitchat/ood nên cao hơn lưu lượng thật |
| Unsupported-store-fact rate (Gemini) | ↓ | **2/40 = 0,05** (kiểm tay; giá/size/tồn kho 0/40, khẳng định có bán hàng ngoài danh mục 2/40) – `results/gemini_store_fact_recheck.json` | 0 | **0** sau hậu kiểm | Đã thêm mẫu `danh_muc` vào I18 + đề xuất sửa prompt (I16) |
| Gemini latency P95 1 lời gọi (s) | ↓ | **41,1** (p50 14,4) flash-lite, **gồm chờ retry 429** do free tier dùng chung | 4,0 | **4,0** (giữ, đo lại khi có quota riêng) | Số hiện tại không phản ánh độ trễ thuần |
| Agent latency e2e P95 (s) | ↓ | CHƯA ĐO (chưa nối đủ công cụ) | 8,0 | 8,0 | – |
| Agent Task Success Rate | ↑ | Chỉ có phần visual: **0,833** (15/18 kịch bản, FashionCLIP + τ_v 0,704) – `04_Khoa/results/e2e_visual-only.json`; TSR toàn hệ thống CHƯA ĐO | 0,80 | 0,80 | 3 lỗi visual đều do τ_v loại truy vấn nền lạ |
| Token / 100 lượt hội thoại (Gemini) | – | **≈ 6.028** (prompt ngắn của Trung); **≈ 21.566** nếu dùng prompt few-shot của Chiến (quy đổi cùng fallback rate 0,273); thinking 1024 ≈ 15.092 (prompt Trung) | ghi nhận | ghi nhận + công thức tiền `[cần xác minh đơn giá]` | Giải thích chênh lệch: `00_Chung/QUYET_DINH_CAN_CHOT.md` mục F |

## 3. Quy tắc hiệu chỉnh
1. Chỉnh tham số/ngưỡng trên **val**; test chỉ chạm khi báo cáo (Bước 1, Bảng C sheet Độ đo). Không để cùng product_id ở 2 tập.
2. Mỗi lần chạy ghi 1 dòng `experiments.csv` (ngày, người, model, data version, seed, tham số, kết quả).
3. Một mục tiêu đã đạt ở baseline → nâng lên mức "baseline + biên" (như MRR, CTE@5) để cải tiến còn ý nghĩa; mục tiêu chưa đạt → giữ, ghi khoảng cách.
4. Số đo có điều kiện bất thường (latency gồm chờ quota, nhãn chưa người duyệt) **phải ghi chú cạnh số**, không đưa vào kết luận cuối.
