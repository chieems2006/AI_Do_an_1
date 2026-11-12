# Lựa chọn cải tiến Tuần 3 (sheet "Cải tiến T3") – đề xuất của Trung theo lỗi baseline THẬT đã thấy

| Mục | Nội dung |
|---|---|
| Liên quan | US_45 (Owner: Khoa), I12/I17 (Trung) |
| Mục tiêu | Chọn ≥ 4 cải tiến tác động cao/effort thấp dựa trên lỗi đo được, đo trước/sau trên cùng bộ test |
| Trạng thái | **Đề xuất** – chốt ở N18 sau baseline end-to-end; cột "Sau" để trống (CHƯA ĐO) |

## 1. Lỗi baseline đã đo được (bằng chứng)
| Lỗi | Số đo thật | File |
|---|---|---|
| Router nhầm so sánh/khác nhóm, teencode "tui" | v1 held-out 0,878; compare recall 0,57 | `results/router_eval_v1.json` |
| Gemini tự nhận cửa hàng có bán hàng ngoài danh mục | 2/40 câu | `results/gemini_store_fact_recheck.json` |
| Gemini latency cao + 429 dùng chung quota | p50 14,4 s, p95 41,1 s; 12 retry/62 lời gọi; 3.5-flash hết 20 req/ngày | `results/gemini_fallback_live.json` |
| Fallback rate hơi cao | 0,273 | như trên |
| Visual nhóm yếu | R@5 footwear 0,683, accessory 0,683 vs clothing 0,817; CTE@5 0,076 | `04_Khoa/results/bench/clip_b32.json` |
| Visual latency P95 | 2.901 ms (p50 428) | như trên |
| τ_r chặn quá tay | τ_r 0,35 chặn 60,1% câu có đáp án | `03_Chien/results/rag_retrieval_eval.json` |

## 2. Đề xuất ưu tiên
| Ưu tiên | ID | Cải tiến | Vì sao (lỗi ở trên) | Độ đo trước → sau | Owner |
|---|---|---|---|---|---|
| 1 | **I15** | Cache Gemini exact-match + làm nóng câu demo + rate limiter 4 RPM | quota 20/ngày, 429, latency | cache hit 10/10 (p50 0,3 ms) đã đo; Trước: p95 41,1 s → Sau: CHƯA ĐO | Hoàng |
| 2 | **I16 + I18** | Prompt cấm nêu/khẳng định mặt hàng ngoài danh mục + hậu kiểm regex v2 (`danh_muc`, `$` trước số) | 2/40 bịa danh mục; regex v1 bắt nhầm 1, sót 2 | Unsupported-store-fact: 0,05 → mục tiêu 0 (đo trên câu mới) | Chiến / Trung |
| 3 | **I12 + I17** | Router v2 (sửa "tui", "phân vân giữa", "X hay Y hơn") + quét τ_intent trên val | route acc held-out 0,878 < 0,90; clarify rate 0,20 | Route acc, fallback rate, clarify rate | Trung |
| 4 | **I19** | Product-type gate (Khoa đã có `clip_b32__gate_*.csv`) | macro R@5 0,721 < 0,80; CTE@5 0,076 | macro R@5, CTE@5 | Khoa |
| 5 | I17 (τ_r) | Hiệu chỉnh τ_r theo thang điểm retriever thật | 60,1% câu có đáp án bị chặn | Abstention acc + tỉ lệ chặn câu có đáp án | Chiến |
| 6 | I11 | Cache embedding truy vấn / giảm luồng chờ | visual P95 2,9 s | latency P95 | Hoàng/Khoa |

Không ưu tiên: I3 fine-tune (12 giờ, rủi ro overfit), semantic cache (cắt scope thứ tự 1), I13 tóm tắt review (đã có bản của Đạt – chỉ dùng nếu faithfulness tốt).

## 3. Quy tắc giữ/bỏ
Chỉ giữ cải tiến khi cải thiện rõ trên **cùng bộ test** (không phải bộ đã dùng để chỉnh) và không làm xấu độ đo khác quá 2 điểm; ghi `experiments.csv`; feature freeze N19 17:00.
