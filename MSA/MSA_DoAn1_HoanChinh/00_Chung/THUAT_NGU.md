# Thuật ngữ dùng chung – giải thích bằng lời và ví dụ (Tác nhân 2 biên soạn)

Mục đích: mọi thành viên và thầy đọc báo cáo hiểu **cùng một nghĩa** cho mỗi con số. Tài liệu của từng thành viên trỏ về file này thay vì định nghĩa lại.
Quy ước viết số: dấu phẩy thập phân trong văn bản tiếng Việt (0,829), dấu chấm trong file CSV/JSON (0.829). Hai cách ghi là **cùng một số**.

## 1. Nhãn nguồn gốc số liệu (bắt buộc ghi cạnh mỗi bảng)

| Nhãn | Nghĩa | Ví dụ trong đồ án |
|---|---|---|
| **[Thật–thật]** | Đo thật, trên dữ liệu thật, nhãn đúng/sai do dữ liệu gốc quyết định | Số SP sau làm sạch 4.385 (`02_TuanDat/results/clean_report.json`) |
| **[Thật–tổng hợp]** | Đo thật nhưng **truy vấn/câu hỏi do máy tạo ra** từ dữ liệu thật | Recall@5 visual: ảnh truy vấn là ảnh catalog bị xoay/cắt/đổi nền (`04_Khoa/eval/eval_visual.csv`, cột `origin`) |
| **[LLM chấm]** | Đúng/sai do một LLM làm giám khảo quyết định | Faithfulness 1,00 của Chiến (giám khảo Gemini), 0,939 của Đạt (giám khảo `gemini-2.5-flash`) |
| **[Tác nhân kiểm]** | Do tác nhân AI kiểm tay, **chưa có người thật** | Kiểm 30 mẫu taxonomy, kiểm 20 tóm tắt review |
| **[Chưa người duyệt]** | Nhãn/đáp án của bộ đánh giá chưa được 2 người thật duyệt | `eval_qa.jsonl`, `eval_router.jsonl` (cột `annotator_1/2` trống) |
| **CHƯA ĐO** | Không có số; không được ước lượng thay | Recall@5 trên ảnh ngoài đời (chưa có ảnh) |

Cấu hình chung khi không ghi khác: data version `shared_data v1 (prep_shared_data.py seed 42)`; seed 42; máy 2 CPU / 7 GB RAM, **dùng chung với 4 tác nhân khác** → số latency là **cận trên, có nhiễu**.

## 2. Độ đo tìm kiếm (visual search và retrieval của RAG)

| Thuật ngữ | Giải thích bằng lời | Ví dụ |
|---|---|---|
| **Recall@K** (R@K) | Mỗi truy vấn: (số SP đúng nằm trong K kết quả đầu) / (tổng số SP đúng); rồi lấy trung bình trên các truy vấn. Ở tầng instance mỗi truy vấn chỉ có **1 SP đúng** nên Recall@K = Hit@K = tỉ lệ truy vấn có SP đúng trong top-K. | 100 ảnh truy vấn, 83 ảnh có SP đúng trong top-5 → R@5 = 0,83 |
| **Hit@K** | Giống Recall@K nhưng chỉ hỏi "có ít nhất 1 kết quả đúng trong K đầu không" (dùng cho RAG: có lấy được ít nhất 1 đoạn review chứa đáp án không). | Hit@5 = 0,866: 86,6% câu hỏi có ≥ 1 review chứa đáp án trong 5 đoạn đưa cho LLM |
| **Macro Recall@5** | Tính R@5 **riêng từng nhóm** (giày, quần áo, mũ, phụ kiện) rồi lấy trung bình cộng 4 số. Tránh để nhóm đông (quần áo) che nhóm ít (mũ). | Giày 0,733, quần áo 0,833, mũ 0,883, phụ kiện 0,867 → macro = 0,829 (FashionCLIP) |
| **MRR@10** | Trung bình của 1/hạng của kết quả đúng đầu tiên (0 nếu ngoài top-10). Thưởng việc đưa SP đúng **lên đầu**. | Đúng ở hạng 1 → 1; hạng 2 → 0,5; hạng 4 → 0,25. Ba truy vấn đó: MRR = (1+0,5+0,25)/3 = 0,583 |
| **NDCG@10** | DCG@10 = Σ_{i=1..10} rel_i / log₂(i+1); NDCG = DCG / DCG lý tưởng (xếp mọi kết quả đúng lên đầu). Tính được khi có nhiều kết quả đúng hoặc độ liên quan nhiều mức. | 1 SP đúng ở hạng 3: NDCG = (1/log₂4)/(1/log₂2) = 0,5 |
| **AP / mAP** | AP của 1 truy vấn = trung bình của Precision@k tại mỗi hạng k có kết quả đúng; mAP = trung bình AP trên mọi truy vấn. Khi chỉ có 1 SP đúng thì AP = 1/hạng (= MRR không cắt). | Đúng ở hạng 1 và 3 (2 SP đúng): AP = (1/1 + 2/3)/2 = 0,833 |
| **Precision@K** (P@K), **cat P@5** | Trong K kết quả, bao nhiêu % là đúng. `cat P@5` = % trong top-5 là SP **cùng loại + cùng màu** (tầng "sản phẩm tương tự"). | Top-5 có 2 áo thun đen giống truy vấn → cat P@5 = 0,4 |
| **Tầng instance / tầng category** | *Instance*: tìm lại **đúng món** (ảnh truy vấn là biến đổi của ảnh catalog). *Category*: tìm **món khác nhưng cùng loại, cùng màu**. | Ảnh đôi Nike trắng xoay 10° → instance; ảnh một đôi sneaker trắng khác → category |
| **CTE@5** (Cross-type error@5) | % kết quả trong top-5 thuộc **nhóm khác** với truy vấn (giày ↔ áo ↔ mũ ↔ phụ kiện). Càng thấp càng tốt. | Tìm giày mà top-5 có 1 cái túi → CTE của truy vấn đó = 1/5 = 0,2 |
| **Type gate** | Bước đoán nhóm của ảnh (giày/áo/mũ/phụ kiện) rồi **chỉ tìm trong nhóm đó** nếu đủ tự tin (≥ τ gate). *Zero-shot* dùng câu mô tả chữ ("a photo of shoes") nên cần model có phần xử lý chữ (text tower); *centroid* dùng vector trung bình mỗi nhóm. | FashionCLIP + gate zero-shot: CTE@5 0,062 → 0,044 |
| **AUROC** | Xác suất một truy vấn "trong phạm vi" có điểm cao hơn một truy vấn "ngoài phạm vi". 1,0 = tách hoàn hảo, 0,5 = đoán mò. | AUROC 1,0: mọi ảnh thời trang có cosine top-1 cao hơn mọi ảnh đồng hồ/mỹ phẩm |
| **Cosine top-1** | Độ giống (−1…1) giữa vector ảnh truy vấn và vector SP xếp hạng 1. | 0,96 = rất giống; ảnh đồng hồ với CLIP B/32 vẫn đạt ~0,80 |
| **FAISS IndexFlatIP** | Chỉ mục tìm kiếm vector **chính xác** (so với mọi vector) bằng tích vô hướng; với vector đã chuẩn hoá L2 thì tích vô hướng = cosine. | 4.593 vector × 512 chiều: tìm < 2 ms |

## 3. Độ đo sinh câu trả lời (RAG, Gemini)

| Thuật ngữ | Giải thích bằng lời | Ví dụ |
|---|---|---|
| **Faithfulness** | Trong câu trả lời, bao nhiêu % **nhận định có trong ngữ cảnh** (review/mô tả) đưa vào. 1,0 = không bịa câu nào. Câu từ chối tính = 1. | Trả lời "vải dày, giao nhanh" mà review chỉ nói "vải dày" → 1/2 = 0,5 |
| **Hallucination rate** | % câu trả lời có **ít nhất 1 nhận định bịa**. Mẫu số phải ghi rõ: Đạt chia cho **mọi câu được chấm** (gồm câu từ chối); Chiến chia cho câu **không** từ chối. | 36 câu được chấm, 4 câu có ý bịa → 4/36 = 0,111 (Đạt) |
| **Refusal (abstention) accuracy** | Với câu **không có đáp án trong dữ liệu**, % được trả "chưa có thông tin" thay vì bịa. | 15 câu không đáp án, từ chối đúng 15 → 15/15 = 1,00 (Chiến, **sau** khi sửa nhãn câu qa108; trước sửa: 15/16 = 0,9375) |
| **False-refusal rate** | % câu **có đáp án** mà hệ thống lại từ chối (từ chối quá tay). Đi cặp với refusal accuracy. | 0/37 = 0,00 |
| **Citation rate / cited-gold** | % câu trả lời có trích nguồn; cited-gold = % trích **đúng** đoạn bằng chứng. | citation 1,00, cited-gold 0,865 |
| **Precision / Recall / F1 thuộc tính** (attribute F1, US_14) | So tập thuộc tính trích được (màu, size, giá…) với nhãn: P = đúng/trích được, R = đúng/nhãn có, F1 = 2PR/(P+R). | Trích {đen, 42} khi nhãn là {đen, 41, da}: P = 1/2, R = 1/3, F1 = 0,4 |
| **Answer relevancy** | % câu trả lời đúng trọng tâm câu hỏi. | Hỏi "có bền không" mà trả lời về màu → không relevant |
| **Unsupported-store-fact rate** | % phản hồi **Gemini** nêu giá/size/tồn kho/"cửa hàng có bán X" mà không có dữ liệu cửa hàng. Mục tiêu 0. | 2/40: Gemini nói cửa hàng có bán đồng hồ (ngoài danh mục) |
| **Giám khảo LLM (LLM-as-judge)** | Dùng một LLM chấm đúng/sai. Rẻ nhưng có thể dễ dãi, nhất là khi cùng họ với model bị chấm → phải có người chấm lại một mẫu. | Gemini chấm Gemini: faithfulness 1,00 → cần 50 câu người chấm |

## 4. Độ đo Agent và chi phí

| Thuật ngữ | Giải thích | Ví dụ |
|---|---|---|
| **Route / route accuracy** | Route = nhánh xử lý agent chọn: `visual, qa, search, compare, gemini_chitchat, gemini_ood, clarify`. Route accuracy = % câu chọn đúng nhánh. | 49 câu, đúng 43 → 0,878 |
| **Held-out** | Tập kiểm tra **không được nhìn** khi chỉnh luật/model/nhãn. Chỉ số trên held-out mới phản ánh khả năng thật. Tập đã **sửa luật hoặc sửa nhãn sau khi xem lỗi** thì không còn là held-out. | Router v1: 0,923 trên bộ đã dùng để sửa luật, nhưng 0,878 trên tập held-out → báo 0,878 |
| **Fallback rate** | % lượt hội thoại được **chuyển sang Gemini**. | 47/172 = 0,273 |
| **Token / 100 lượt** | Tổng token (vào + ra + thinking) cho **100 lượt hội thoại** của người dùng. Phải nói rõ "lượt hội thoại" hay "lời gọi Gemini" (xem `QUYET_DINH_CAN_CHOT.md` mục F). | 100 lượt × (47/172 = 27,33 %) chuyển Gemini × 220,6 token/lời gọi ≈ 6.028 token (Trung) |
| **Thinking token** | Token "suy nghĩ nội bộ" của Gemini 3.5: không hiện ra nhưng **vẫn tính tiền như token ra**. Tắt bằng `thinkingBudget=0` (chỉ `gemini-3.5-flash` nhận; `flash-lite` mặc định không suy nghĩ). | Câu trả lời 20 token nhưng thinking 388 token, chậm 16 s thay vì 1,3 s |
| **TSR (Task Success Rate)** | % kịch bản end-to-end hoàn thành đúng (đúng route + đúng kết quả + không lỗi). | Visual-only 15/18 = 0,833 |
| **p50 / p95 (latency)** | p50 = trung vị (một nửa số lần nhanh hơn); p95 = 95% số lần nhanh hơn mức này – đại diện "lần chậm". | p50 393 ms, p95 1.106 ms |

## 5. Các ngưỡng τ (tau)

| Ngưỡng | Ý nghĩa bằng lời | Ví dụ quyết định |
|---|---|---|
| **τ_v** | Nếu cosine top-1 của visual search **< τ_v** → coi như "không thấy SP giống", không trả kết quả, gợi ý mô tả bằng chữ. | τ_v = 0,25 thì ảnh đồng hồ/mỹ phẩm (cosine top-1 trung vị ~0,4–0,8 tuỳ model) **vẫn lọt** → vô dụng; FashionCLIP cần ~0,70 |
| **τ_r** | Ngưỡng điểm retrieval của RAG; dưới ngưỡng → từ chối trước khi gọi LLM. | Với TF-IDF, τ_r = 0,35 chặn nhầm 60% câu có đáp án → Chiến đặt τ_r = 0 và để LLM + guard từ chối |
| **τ_intent** | Độ tự tin tối thiểu của router; dưới ngưỡng → hỏi lại (`clarify`) hoặc chuyển Gemini. | 0,6 (mặc định thiết kế chung) |
| **τ gate** | Độ tự tin tối thiểu để type gate lọc theo nhóm. | 0,9 (chọn trên val) |

**Quy tắc chọn ngưỡng:** chỉnh trên tập **val**, báo cáo trên tập **test**; mỗi model embedding có thang cosine khác nhau nên **ngưỡng phải đi theo model** (lưu trong `indexes/<model>/config.json`).
