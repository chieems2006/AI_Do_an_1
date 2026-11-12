# US_13 – Khảo sát độ đo cho Product QA / RAG (Sheet "2_Độ đo" – phần QA/RAG)

| Mục | Nội dung |
|---|---|
| Mã US | US_13 (3 pt, Sprint 2, Owner: Chiến, Support: Khoa) |
| Mục tiêu | Đánh giá được cả khâu tìm tài liệu (retrieval) lẫn khâu sinh câu trả lời (generation), đặc biệt việc **không bịa** |
| Đầu ra | File này (bổ sung/chỉnh cho sheet `2_Độ đo`), code tính ở `src/scripts/eval_rag.py` (khi ghép repo: chuyển sang `src/msa/eval/metrics.py` của Hoàng) |
| Tiêu chí nghiệm thu | Mỗi độ đo có công thức, ưu/nhược và quyết định chọn/không chọn |
| Trạng thái | **Hoàn thành** (khảo sát) + đã có số đo thật đầu tiên (mục 3) |

## Tóm tắt 5 dòng
1. Khảo sát độ đo cho 2 khâu: tìm tài liệu (Hit@K, MRR, context precision/recall) và sinh câu trả lời (EM/F1, ROUGE, BLEU, BERTScore, faithfulness, relevancy, hallucination, abstention, human eval).
2. Chọn chính: Hit@5, MRR@10 (tìm); Faithfulness, Hallucination rate, Refusal accuracy + False-refusal, Answer relevancy (trả lời); human eval 50 câu.
3. Không chọn ROUGE/BLEU vì đo trùng chữ, không đo đúng/sai nghĩa của câu tiếng Việt.
4. Số đo thật: Hit@5 test 0,895 (hybrid); faithfulness 1,00 trên 52 câu – [LLM chấm], cần người chấm lại.
5. Ví dụ dễ hiểu từng độ đo: `00_Chung/THUAT_NGU.md` mục 2–3.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Ký hiệu: Q = tập câu hỏi; với câu q, G(q) = tập chunk bằng chứng (review trong `evidence_review_ids`), R_K(q) = top-K chunk truy xuất, rank(q) = hạng của chunk đúng đầu tiên.

## 1. Độ đo retrieval

| Độ đo | Công thức | Ý nghĩa | Ưu điểm | Nhược điểm | Quyết định | Lý do |
|---|---|---|---|---|---|---|
| **Hit@K** | (1/\|Q\|) Σ 1[R_K(q) ∩ G(q) ≠ ∅], K=1,5 | Có lấy được ít nhất 1 đoạn chứa đáp án trong K đoạn đưa cho LLM không | Rẻ, khách quan, tách lỗi "không tìm ra" khỏi lỗi "LLM nói sai" | Không phân biệt hạng 1 với hạng 5; cần gán bằng chứng | **CHÍNH** (K=5 = số đoạn đưa vào prompt) | LLM chỉ đúng được khi bằng chứng có trong ngữ cảnh |
| **MRR@10** | (1/\|Q\|) Σ 1/rank(q) (0 nếu không có trong top-10) | Thứ hạng của bằng chứng | Một số duy nhất để so retriever | Chỉ xét bằng chứng đầu tiên | **CHÍNH** (so sánh retriever, Bảng C) | Phân biệt được TF-IDF/BM25/dense/hybrid khi Hit@5 sát nhau |
| Context Precision | (1/K) Σ_{i≤K} 1[c_i liên quan] (bản RAGAS có trọng số theo hạng) | Bao nhiêu % ngữ cảnh đưa vào là liên quan | Đo "nhiễu" trong prompt | Cần nhãn liên quan cho mọi chunk hoặc LLM giám khảo | **PHỤ** | Review Shopee ngắn, nhiều câu khen chung chung → nhiễu ít ảnh hưởng; báo cáo nếu còn quota |
| Context Recall | \|G(q) ∩ R_K(q)\| / \|G(q)\| | Ngữ cảnh có đủ mọi bằng chứng cần không | Quan trọng khi đáp án tổng hợp nhiều review (ý kiến trái chiều) | Phụ thuộc độ đầy đủ của G(q) (Gemini có thể bỏ sót) | **PHỤ** | Tính được miễn phí từ cùng dữ liệu; dùng khi phân tích lỗi |

## 2. Độ đo generation

| Độ đo | Công thức | Ý nghĩa | Ưu điểm | Nhược điểm | Quyết định | Lý do |
|---|---|---|---|---|---|---|
| Exact Match / F1 token | EM = 1[chuẩn hoá(a)=chuẩn hoá(g)]; F1 = 2PR/(P+R) trên token | So câu trả lời với đáp án chuẩn | Khách quan, rẻ | Đáp án tự do tiếng Việt diễn đạt khác ⇒ F1 thấp dù đúng | **PHỤ** (chỉ câu factual ngắn) | ViMRHP không có giá/size cấu trúc nên gần như không có câu factual ngắn |
| ROUGE-L / BLEU | LCS hoặc n-gram precision | Chồng lặp chuỗi | Rẻ, quen thuộc | Không phản ánh đúng/sai nghĩa | **KHÔNG CHỌN** | Như sheet gốc |
| BERTScore | F1 của cosine token-embedding (vd XLM-R) | Tương đồng ngữ nghĩa | Nhạy nghĩa hơn ROUGE | Không biết có bám ngữ cảnh không; tốn CPU | **PHỤ / tham khảo** | Không ưu tiên trên máy 2 CPU |
| **Faithfulness** | (số nhận định được ngữ cảnh hỗ trợ)/(tổng nhận định), trung bình theo câu; câu từ chối = 1 | Có bịa không | Đo trực tiếp mục tiêu "không bịa" | Giám khảo LLM có thể sai/thiên lệch | **CHÍNH** | Hiện chấm bằng Gemini giám khảo + **kiểm trích dẫn** (câu không trích nguồn hợp lệ bị guard chặn); cần người kiểm 50 mẫu |
| **Answer Relevancy** | % câu trả lời đúng trọng tâm (giám khảo) | Không lạc đề | Bắt lỗi "đúng ngữ cảnh nhưng vô ích" | Giám khảo LLM | **CHÍNH** | Cặp với faithfulness |
| **Hallucination rate** | % câu trả lời *không từ chối* có ≥ 1 nhận định không có trong ngữ cảnh | Một con số dễ truyền đạt | Ngưỡng an toàn rõ (mục tiêu ≤ 0.10) | Phụ thuộc quy ước đếm | **CHÍNH** | Quy ước: tính trên câu đã trả lời; câu từ chối không tính |
| **Refusal (abstention) accuracy** | % câu answerable=false được trả "chưa có thông tin" | Biết từ chối | Kiểm trực tiếp US_35 (mục tiêu ≥ 0.90) | Cần ≥ 15% câu không đáp án | **CHÍNH** | eval_qa có 25,4% câu answerable=false |
| False-refusal rate (bổ sung) | % câu answerable bị từ chối | Từ chối quá tay | Cân bằng với refusal accuracy (tránh hệ thống "từ chối hết" vẫn đạt 100%) | – | **CHÍNH (bổ sung)** | Nếu thiếu, có thể đạt refusal 1.0 bằng cách luôn từ chối |
| Citation rate / cited-gold rate (bổ sung) | % câu trả lời có trích [Cx] hợp lệ; % câu trích trúng review bằng chứng | Trích nguồn đúng | Rẻ, không cần giám khảo | Trích đúng chunk chưa chắc nói đúng | **PHỤ** | Bằng chứng cho US_35 "trả lời kèm nguồn" |
| Human eval 1-5 | 2 người chấm đúng/hữu ích/tự nhiên trên 50 câu; báo cáo Cohen's κ | Đáng tin nhất | Hiệu chỉnh giám khảo LLM | Tốn công | **CHÍNH (50 câu)** | **CHƯA LÀM** – cần 2 người thật |

## 3. Số đo thật đã có (05/11/2026, data `shared_data v1`)

Retrieval – `results/rag_retrieval_eval.json` (209 câu answerable của eval_qa, sau khi sửa nhãn qa108, 10.173 chunk / 428 SP, lệnh `PYTHONPATH=src python src/scripts/eval_rag.py retrieval`):

| Retriever | Hit@1 (lọc product_id) | Hit@5 (lọc product_id) | MRR@10 (lọc product_id) | Hit@5 (toàn kho) |
|---|---|---|---|---|
| TF-IDF char 2-4 (bỏ dấu) | 0.249 | 0.833 | 0.500 | 0.120 |
| BM25 âm tiết (bỏ dấu) | 0.244 | 0.837 | 0.496 | 0.163 |
| BM25 + viết lại teencode | 0.249 | 0.818 | 0.496 | 0.163 |
| multilingual-e5-small | 0.263 | 0.794 | 0.490 | 0.120 |
| paraphrase-multilingual-MiniLM-L12-v2 | 0.278 | 0.756 | 0.491 | 0.024 |
| **Hybrid RRF (BM25 + e5-small)** | **0.321** | **0.866** | **0.548** | **0.177** |

End-to-end (faithfulness, hallucination, refusal) – `results/rag_e2e_eval.json`, xem README.

Nhận xét: (1) chế độ "lọc theo product_id" là chế độ đúng cho QA (người dùng đang xem 1 SP; ~22 chunk/SP) – Hit@5 hybrid 0.866 vượt mục tiêu 0.85 nhưng **gold do Gemini sinh, chưa người duyệt**; (2) toàn kho rất thấp (≤ 0.18) vì review nhiều SP giống nhau ("giao hàng nhanh, đóng gói cẩn thận") ⇒ **bắt buộc có product_id** trước khi QA (router hỏi lại nếu thiếu); (3) điểm top-1 tách câu có/không đáp án kém (AUC 0.72–0.77) ⇒ **không dùng τ_r làm cơ chế từ chối chính**; từ chối dựa vào LLM + guard trích dẫn.
