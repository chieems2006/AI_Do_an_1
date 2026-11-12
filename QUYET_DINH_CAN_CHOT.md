# Quyết định cần chốt – mâu thuẫn giữa các thành viên (Tác nhân 2 đề xuất)

Mỗi mục: **Vấn đề → Bằng chứng (file) → Phương án → Đề xuất → Người chốt → Hạn**. Trạng thái tất cả: `ĐỀ XUẤT – chờ người chốt ký` (ghi ngày + tên vào cột cuối khi chốt).
Mọi số trong file này truy được về file trong folder này (Tác nhân 3 đã đối chiếu tự động: `00_Chung/kiem_dinh/doi_chieu_so_lieu.md`); thuật ngữ: `00_Chung/THUAT_NGU.md`.

## Tóm tắt 5 dòng
1. **Mũ: con số chuẩn là 285 SP có ảnh** (thiếu 15 so với quota 300) – 293/286/298 là cùng một nguồn ở các bước khác nhau (mục A).
2. **Trang sức/tất là ngoài phạm vi**: 4 câu eval_router + 45/280 câu eval_qa + 67 SP trong kho RAG của Chiến cần gắn cờ (danh sách: `03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv`) (mục B).
3. **τ_v = 0,25 bị bỏ**: ngưỡng đi theo model, đọc từ `indexes/<model>/config.json` (mục C).
4. **Thêm `source="fallback"`** cho thông điệp hệ thống khi Gemini lỗi – đã sửa UI của Đạt và router của Trung để không hiện nhầm "Từ dữ liệu cửa hàng" (mục D).
5. **Bảng F chạy thật trên 5 model: DINOv2-S hạng 1 (4,83/5), FashionCLIP hạng 3 (3,96)** → lựa chọn FashionCLIP của Khoa không được Bảng F ủng hộ; đề xuất đổi model chính (mục E). Số token Gemini lệch nhau chủ yếu vì **khác đơn vị và khác độ dài prompt** (mục F).

---

## A. Số sản phẩm nhóm mũ: 293 / 286 / 285 / 298

**Vấn đề.** Bốn tài liệu ghi bốn con số khác nhau cho nhóm mũ, người đọc không biết số nào đúng.

**Bằng chứng – cả bốn số đều đúng, nhưng đo ở các bước khác nhau của cùng một nguồn FPI:**

| Số | Ai ghi | Bước | Thành phần | File |
|---|---|---|---|---|
| **293** | Tác nhân 1 (`shared_data`), Khoa (EDA, benchmark) | Nhãn gốc FPI, **chưa** áp taxonomy | Caps 283 + Hat 3 + **Headband 7** | `00_Chung/stats.json`, `04_Khoa/docs/US_09_eda/eda_stats.json` |
| **286** | Trung (US_49) | Áp taxonomy v1: Headband (băng đô) → `out_of_scope` | 293 − 7 = 286 (cap 266, beanie 20) | `01_Trung/results/taxonomy_coverage.json` |
| **285** | Đạt (US_08) | Bỏ Headband **và** khử 1 ảnh trùng MD5 thuộc nhóm mũ | 293 − 7 − 1 = 285 (cap 258, beanie 21, wide_brim 6) | `02_TuanDat/results/clean_report.json` (`removed_unknown_labels`, `before_cap.by_type`) |
| **298** | Hoàng (US_48, Data v1) | **Giữ** Headband (ghi `unknown`) + thêm 5 mũ ViMRHP | 293 + 5 = 298 (cap 286, unknown 9, wide_brim* 3) | `05_Hoang/data/counts_data_v1.json` |

Ngoài số tổng, **nhãn lá** cũng lệch: Tác nhân 2 đối chiếu `catalog_clean.parquet` (Đạt) với `catalog_fpi_taxonomy_v1.parquet` (Trung) – 4.375/4.385 SP trùng nhãn, **10 SP lệch** và đã xem ảnh từng SP:

| product_id | Tiêu đề | Đạt | Trung | Ảnh thực tế (Tác nhân 2 xem) | Nhãn đúng |
|---|---|---|---|---|---|
| fpi_34793…34797 (5 SP) | Flying Machine Men … Hat | wide_brim | cap | mũ phớt (fedora) có vành | **wide_brim** (Đạt đúng) |
| fpi_39495 | Wildcraft Unisex Beige Hat | wide_brim | cap | mũ tai bèo vành rộng (boonie) | **wide_brim** (Đạt đúng; mơ hồ với bucket) |
| fpi_19436 | Quiksilver … Beanies Cap | beanie | cap | mũ len trùm đầu | **beanie** (Đạt đúng) |
| fpi_15488, fpi_13360, fpi_22731 | … Boots / Sports Boot | heel_flat / sneaker | boot | bốt cổ cao | **boot** (Trung đúng) |

**Phương án.** (1) Lấy 293 (số nguồn) · (2) 286 (theo taxonomy) · (3) **285 (taxonomy + làm sạch)** · (4) 298 (cộng ViMRHP).

**Đề xuất: số chuẩn = 285 SP mũ có ảnh** (cap 258 / beanie 21 / wide_brim 6; bucket 0), vì:
- Tiêu chí US_48 tính "SP **có ảnh + metadata**" → 5 mũ ViMRHP không có ảnh, không tính vào quota visual (vẫn dùng cho QA) → loại phương án (4).
- Headband đã được taxonomy (US_49, người có thẩm quyền về nhãn) xếp `out_of_scope` → loại (1).
- Ảnh trùng MD5 phải bỏ theo US_08 → (3) là con số **sau cùng** của pipeline.
- Nhãn lá: dùng taxonomy v1 làm gốc, **sửa 7 SP mũ theo bảng trên** (luật tiêu đề "Hat" → wide_brim, "Beanie(s)" → beanie) và **giữ 3 boot** của taxonomy (luật làm sạch của Đạt thiếu luật "Boot").
- Mũ 285 < 300 → áp sheet Rủi ro mục C, thứ tự cắt 3: **"nhóm mũ chỉ giữ mức demo"**; báo cáo nêu rõ thiếu 15 SP, không có bucket.

**Việc kéo theo:** Trung thêm 2 luật tiêu đề vào `msa.data.taxonomy.map_fpi`; Đạt dùng `map_fpi` thay luật riêng; Hoàng loại Headband khỏi Data v1 (headwear 298 → 291 nếu giữ ViMRHP, 286 nếu chỉ tính FPI trước khử trùng). Mọi báo cáo ghi: *"Mũ: 285 SP có ảnh (FPI, sau taxonomy v1 + làm sạch); +5 SP ViMRHP chỉ có review"*.
**Người chốt:** Trung (taxonomy) + Đạt (làm sạch) · Hoàng, Khoa xác nhận. **Hạn:** họp N5.

## B. Trang sức / tất: eval của Chiến coi là hàng trong cửa hàng, taxonomy coi là ngoài phạm vi

**Vấn đề.** Taxonomy v1 (US_49 mục "ngoài phạm vi") loại tất/vớ, trang sức, phụ kiện tóc…; nhưng bộ đánh giá và kho RAG của Chiến lấy cả nhóm `PhuKienNu` của ViMRHP.

**Bằng chứng (đếm lại bằng `01_Trung/data/vimrhp_taxonomy_v1.csv`):**
- Kho tri thức RAG `03_Chien/data/kb/chunks.jsonl`: 428 SP, trong đó **67 SP ngoài phạm vi** (dây chuyền, khuyên tai, vòng tay, dây buộc tóc, bộ ngủ…). ViMRHP thực sự trong phạm vi: **361 SP** (349 có lá + 12 `unknown`).
- `eval_qa.jsonl`: **45/280 câu** hỏi về 12 SP ngoài phạm vi (44 câu PhuKienNu + 1 bộ ngủ).
- `eval_router.jsonl`: **4/78 câu** – r019 (dây chuyền, `qa`), r020 (tất, `qa`), r038 (khuyên tai, `search`), r047 (dây chuyền vs vòng cổ, `compare`).
- Danh sách đầy đủ từng câu + đề xuất: `03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv` (Tác nhân 2 tạo, **không sửa** file eval gốc để không làm lệch số đã báo cáo).

**Phương án.** (1) Mở rộng phạm vi thêm trang sức/tất · (2) **Giữ 4 nhóm, gắn cờ và đổi nhãn** · (3) Xoá các câu đó.

**Đề xuất: (2).** Phạm vi 4 nhóm là quyết định ở US_01/Tổng quan; mở rộng làm loãng dữ liệu (R16).
- eval_router v1.1: đổi 4 câu trên sang `gemini_ood` – đây chính là ca kiểm "Gemini không được nhận cửa hàng có bán trang sức" (lỗi 2/40 Trung đã gặp). Vẫn ≥ 60 câu, ≥ 15 câu chitchat/ngoài phạm vi (21 → 25).
- eval_qa v1.1: thêm trường `in_scope` (false cho 45 câu); **số báo cáo chính tính trên 235 câu in_scope**, số trên 280 câu để phụ lục. Tỉ lệ câu không đáp án phải kiểm lại sau khi tách (yêu cầu > 15%).
- Kho RAG: lọc 67 SP hoặc gắn `in_scope=false` để agent trả "cửa hàng chưa kinh doanh mặt hàng này".
- Sau khi đổi: Trung chạy lại `scripts/eval_router.py` (không tốn Gemini); Chiến/Hoàng chạy lại retrieval (TF-IDF/BM25 không tốn GPU; dense dùng cache).
**Người chốt:** Chiến (eval) + Trung (phạm vi). **Hạn:** N6.

## C. Ngưỡng τ_v: 0,25 (thiết kế chung) vs 0,704 (Khoa)

**Vấn đề.** Thiết kế chung §5.3 đặt `τ_v = 0.25`; US_40 (Trung) vẽ sơ đồ với 0,25; API của Hoàng dùng 0,25; Khoa đề xuất 0,704 cho FashionCLIP.

**Bằng chứng** (`04_Khoa/results/tau_v_analysis.json`, test split, OOD = 60 ảnh FPI đồng hồ/mỹ phẩm):

| Model | τ_v = 0,25: loại OOD | τ_v chọn trên val (max OOD val + 0,01) | Loại OOD (test) | Giữ truy vấn category | Giữ truy vấn instance |
|---|---|---|---|---|---|
| fashionclip | **0 %** | 0,7039 | 100 % | 100 % | 84,2 % |
| dinov2_s | 0 % | 0,5923 | 97,2 % | 100 % | 94,2 % |
| siglip_b16 | 0 % | 0,7531 | 100 % | 100 % | 96,3 % |
| clip_b32 | 0 % | 0,8887 | 100 % | 94,2 % | 67,1 % |

Hoàng cũng đo độc lập: với CLIP B/32 không truy vấn nào dưới 0,25 (top-1 trung bình 0,96 – `05_Hoang/results/api_eval.json`). Lý do: mỗi model có **thang cosine riêng** (ảnh đồng hồ vẫn giống ảnh thời trang ở mức 0,4–0,8).

**Đề xuất.** Bỏ giá trị cố định 0,25. `τ_v` **đi theo model**, chọn trên val bằng quy tắc "max cosine top-1 của OOD val + 0,01", lưu trong `indexes/<model>/config.json`; API (Hoàng) và Agent (Trung) **đọc từ config**, không hard-code. Giá trị cho demo phụ thuộc mục E (DINOv2-S → 0,5923; FashionCLIP → 0,7039).
Cảnh báo cần ghi trong báo cáo: tập OOD hiện chỉ là ảnh studio FPI; phải hiệu chỉnh lại khi có ảnh ngoài đời (US_11) và ảnh "không phải thời trang" thật (mèo, đồ ăn – kịch bản T05 của Đạt). Với FashionCLIP, ngưỡng 0,704 làm 3/18 kịch bản visual của US_44 thất bại (truy vấn nền lạ bị loại).
**Người chốt:** Khoa (giá trị) + Trung (sửa US_40) + Hoàng (API đọc config). **Hạn:** N11 (chốt ngưỡng).

## D. `source="fallback"` (Hoàng) vs hợp đồng §5.2 (`internal|gemini|cache`)

**Vấn đề.** Khi Gemini lỗi 429/timeout, LLMGateway của Hoàng trả thông điệp dự phòng với `source="fallback"` – giá trị không có trong hợp đồng. Kiểm chéo cho thấy hậu quả thật:
- UI của Đạt (`02_TuanDat/app/components.py`) coi mọi `source` lạ là **"Từ dữ liệu cửa hàng"** và `validate_response` báo lỗi.
- Router của Trung (`01_Trung/src/msa/agent/router.py`) gắn `source="internal"` cho câu "phần trò chuyện đang bận" → UI cũng hiện "Từ dữ liệu cửa hàng". Cả hai đều **gắn nhãn sai nguồn**, trái quy tắc §5.4.

**Phương án.** (1) Ép về `gemini` (sai: Gemini không trả lời) · (2) Ép về `internal` (sai: không phải dữ liệu cửa hàng) · (3) **Thêm giá trị `fallback`** · (4) Giữ 3 giá trị + trường phụ `degraded=true`.

**Đề xuất: (3)** – rõ nghĩa nhất, UI hiện nhãn "Thông báo hệ thống". Đồng thời khuyến nghị: câu Gemini lấy từ cache nên dùng `source="gemini"` + `cached=true` (giá trị `cache` giữ lại để tương thích, UI đã xử lý).
**Đã làm (thay đổi nhỏ, tương thích ngược, pytest vẫn pass):** thêm `fallback` vào `SOURCES` + nhãn `LABEL_SYSTEM` + 1 assert test (Đạt); router Trung dùng `source="fallback"` cho 2 thông điệp hệ thống + sửa 1 assert; enum trong `01_Trung/docs/openapi_contract.yaml`. Nếu nhóm chọn phương án khác thì hoàn tác 3 chỗ này.
**Người chốt:** Trung (chủ hợp đồng US_40) + Hoàng + Đạt. **Hạn:** N14.

## E. Model embedding ảnh: Khoa chọn FashionCLIP – Bảng F (Trung) chưa có số liệu

**Vấn đề.** US_25 yêu cầu chọn model bằng bảng chấm điểm có trọng số; bản cũ chỉ có 1 ứng viên nên "chưa xếp hạng được", trong khi Khoa đã chọn FashionCLIP bằng lập luận định tính.

**Đã chạy (Tác nhân 2):** `cd 01_Trung && PYTHONPATH=src python scripts/run_scoring_from_khoa.py` trên `04_Khoa/results/bench_image_embed.csv` (5 model, split test). Script đã sửa để đọc đúng cột CSV của Khoa (ánh xạ cột ghi ở docstring) và sửa khoá `dinov2_small` → `dinov2_s` trong bảng điểm định tính.

| Hạng | Model | Độ chính xác (0,35) | Tốc độ (0,15) | Tài nguyên (0,15) | Phù hợp miền (0,15) | License (0,10) | Tích hợp (0,10) | **Tổng /5** |
|---|---|---|---|---|---|---|---|---|
| 1 | dinov2_s | 5,00 | 4,72 | 4,83 | 5,00 | 5,00 | 4,00 | **4,83** |
| 2 | siglip_b16 | 4,47 | 5,00 | 1,00 | 4,08 | 5,00 | 4,00 | **3,98** |
| 3 | fashionclip | 4,33 | 4,71 | 3,13 | 3,15 | 4,00 | 4,00 | **3,96** |
| 4 | clip_b32 | 1,89 | 4,33 | 2,33 | 2,23 | 5,00 | 5,00 | 2,99 |
| 5 | resnet50 | 1,00 | 1,00 | 4,98 | 1,00 | 5,00 | 5,00 | 2,40 |

Nguồn: `01_Trung/results/weighted_scoring.md/.json`. **Độ nhạy:** đổi từng trọng số ±0,05 (12 cấu hình) → DINOv2-S hạng 1 ở **12/12**; FashionCLIP và SigLIP đổi chỗ hạng 2–3 (`weighted_scoring_sensitivity.json`). **Kịch bản B** (thêm tiêu chí "tầng category" 0,10 – lợi thế của FashionCLIP): DINOv2-S 4,48 > FashionCLIP 4,03 > SigLIP 3,96 (`weighted_scoring_scenario_B.json`).

Bổ sung bằng chứng độ bền (Tác nhân 2 tách từ kết quả có sẵn, không chạy lại model – `04_Khoa/results/recall_by_transform.csv`, R@5 test instance):

| Họ biến đổi (gần ảnh người dùng nhất in đậm) | n | DINOv2-S | SigLIP B/16 | FashionCLIP |
|---|---|---|---|---|
| **background** (đổi nền) | 32 | 0,812 | **0,906** | 0,656 |
| **combo** (nhiều biến đổi) | 36 | **0,750** | **0,750** | 0,667 |
| **lowres_jpeg** (mờ, nén) | 36 | 0,417 | 0,278 | **0,500** |

Lập luận của Khoa cho FashionCLIP (cat P@5 cao nhất 0,378; có text tower cho type gate zero-shot) có thật nhưng **không đủ bù**: DINOv2-S không cần gate vẫn có CTE@5 0,043 – thấp hơn FashionCLIP **có** gate (0,044); FashionCLIP yếu nhất ở "đổi nền" – loại biến đổi gần ảnh người dùng nhất.

**Phương án.**
1. **Đổi model chính sang DINOv2-S** (đúng Bảng F; build index ≈ 13 phút – embed catalog đo 790,8 s; τ_v 0,5923; không dùng gate vì gate centroid làm R@5 giảm 0,846 → 0,796). Nhược: chưa có text tower; cải tiến I1/I2/I3 của Khoa phải đo lại cho DINOv2-S.
2. Giữ FashionCLIP cho demo (index + cải tiến đã xong) nhưng báo cáo phải nói rõ **chọn trái Bảng F** và lý do – dễ bị thầy hỏi vặn.
3. Chọn SigLIP B/16 (hạng 2, có text tower, bền nền lạ nhất) – tốn RAM nhất (đỉnh 2,4 GB).

**Đề xuất: phương án 1** cho báo cáo Tuần 2 và demo; giữ SigLIP B/16 làm ứng viên dự phòng. **Chốt lại sau khi có ≥ 80 ảnh ngoài đời (US_11)**: chạy lại 3 model DINOv2-S / SigLIP / FashionCLIP; nếu chênh macro R@5 < 5 điểm thì giữ DINOv2-S. Lưu ý trung thực: mọi truy vấn instance hiện là biến đổi tổng hợp – DINOv2 được huấn luyện để bất biến với biến đổi kiểu này nên có thể được lợi; đây là lý do bắt buộc phải có ảnh thật.
**Người chốt:** Trung (US_25) + Khoa (US_22). **Hạn:** N12 (buổi chấm điểm).

## F. Số token Gemini / 100 lượt lệch nhau giữa Trung, Chiến, Hoàng (và Đạt)

**Vấn đề.** Bốn người báo "token/100 lượt" từ ~6 nghìn đến ~79 nghìn.

**Bằng chứng – cùng model `gemini-3.5-flash-lite` (vì `gemini-3.5-flash` hết quota free tier 20 request/ngày), khác ở 4 điểm:**

| Người (file) | Vai trò đo | Prompt hệ thống | n | Token vào / lời gọi | Ra | Thinking | Số gốc báo cáo | **Đơn vị của số gốc** |
|---|---|---|---|---|---|---|---|---|
| Trung (`01_Trung/results/gemini_fallback_live.json`, cấu hình A) | chitchat/ood qua router | ngắn (`GEMINI_SYSTEM_PROMPT` trong router.py) | 40 | 165,1 | 55,5 | 0 | ≈ 6.028 | **100 lượt hội thoại** (đã nhân fallback rate 0,273) |
| Trung (cấu hình B, thinking 1024) | như trên | như trên | 10 | 164,7 | 37,3 | 350,3 | ≈ 15.092 | 100 lượt hội thoại |
| Chiến (`03_Chien/results/gemini_fallback_check.json`) | nhánh fallback US_51 | **dài: system + few-shot** (`prompts/gemini_fallback.md` v1.0) | 22 | 747,5 | 41,7 | 0 | 74.750 vào + 4.170 ra | **100 lời gọi Gemini** |
| Hoàng (`05_Hoang/results/llm_gateway_live.json`, pass default) | kiểm gateway, 10 câu mẫu | ngắn (3 câu) | 10 | 104,6 | 63,7 | 0 | 10.460 vào + 6.370 ra | **100 lời gọi Gemini** |
| Đạt (`02_TuanDat/results/bench_llm_summary.json`, qa) | **RAG trả lời có ngữ cảnh review** | prompt QA + context | 36 | 606,2 | 36,3 | 0 | 60.619 vào + 3.631 ra | 100 câu QA (mỗi câu 1 lời gọi) |
| Đạt (router) | Gemini làm router | prompt phân loại | 14 | 315,8 | 32,7 | 0 | 31.579 vào + 3.271 ra | 100 câu định tuyến |

**Giải thích chênh lệch:**
1. **Đơn vị khác nhau** (nguyên nhân lớn nhất): Trung chia cho *lượt hội thoại* (chỉ 27,3% lượt gọi Gemini); Chiến, Hoàng tính trên *lời gọi Gemini* (100% lượt gọi). Khác nhau ~3,7 lần chỉ vì đơn vị.
2. **Độ dài prompt hệ thống**: prompt có few-shot của Chiến ≈ 750 token vào/lời gọi, gấp ~4,5 lần prompt ngắn của Trung, ~7 lần của Hoàng.
3. **Vai trò khác**: số của Đạt là RAG có ngữ cảnh review (≈ 600 token vào) và router – không so trực tiếp với nhánh chitchat.
4. **Thinking**: bật thinking 1024 trên flash-lite thêm ~350 token/lời gọi (tính giá như token ra); với `gemini-3.5-flash` mặc định thinking 388–458 token cho 1 câu ngắn, `thinkingBudget=0` → 0 (`03_Chien/results/gemini_thinking_probe.json`, `05_Hoang/results/llm_gemini35_thinking_probe.json`, n=1 – chỉ là thăm dò).
5. Tập câu khác nhau, n nhỏ (10–40) → độ dài câu trả lời dao động.

**Quy đổi về cùng đơn vị** "token / 100 lượt hội thoại" với fallback rate 47/172 = 0,2733 (Tác nhân 2 tính: tổng token/lời gọi × 100 × 0,2733): Trung ≈ 6.028 · **Chiến ≈ 21.566** · Hoàng ≈ 4.599.

**Đề xuất.**
- Đơn vị báo cáo chính thức (US_44, Bảng D2): **token / 100 lượt hội thoại** = fallback_rate × 100 × (vào + ra + thinking trung bình mỗi lời gọi); kèm số "/100 lời gọi Gemini" ở phụ lục.
- Prompt dùng cho demo là bản của Chiến (US_51 owner) vì 0/20 vi phạm giá/size/tồn kho, trong khi prompt ngắn của Trung có 2/40 câu nhận bán hàng ngoài danh mục. Chi phí ước tính ≈ 21,6 nghìn token/100 lượt; nếu cần giảm, rút few-shot (I16) rồi đo lại.
- Cấu hình chuẩn: `gemini-3.5-flash-lite`, không thinking, temperature ghi rõ; nếu có quota `gemini-3.5-flash` thì đặt `thinkingBudget=0`.
**Người chốt:** Chiến (prompt) + Trung (router, US_44 bảng route) + Hoàng (gateway log token). **Hạn:** N11.

---

## G. Các mâu thuẫn khác Tác nhân 2 tự phát hiện

| # | Vấn đề | Bằng chứng | Đề xuất | Người chốt |
|---|---|---|---|---|
| G1 | **Mỗi người dùng một phiên bản catalog**: Khoa benchmark trên 4.593 SP (`shared_data`), Đạt làm sạch ra 4.385, Trung 4.586, Hoàng Data v1 5.021 (index ảnh 4.593) | các README + file đếm ở mục A | Đặt tên **Data v1.1** = `catalog_clean.parquet` (4.385) + nhãn taxonomy v1 + 7 sửa mũ (mục A). Index demo build trên v1.1; số benchmark Bảng A trên 4.593 vẫn giữ (ghi rõ phiên bản) | Trung + Đạt + Hoàng |
| G2 | **ViMRHP "trong phạm vi" 428 hay 361 SP?** Đạt/Chiến/Hoàng ghi 428 (chỉ bỏ đồng hồ), taxonomy ghi 361 | `01_Trung/data/vimrhp_taxonomy_v1.csv` | Ghi: "ViMRHP 509 → bỏ 81 đồng hồ = 428 SP nạp vào kho; trong đó 361 thuộc 4 nhóm". Số review: 9.403 (thô của 428 SP) → 9.317 (khử 86 trùng `comment_id`, Chiến) → 7.833 (thô, của 361 SP trong phạm vi = 349 có lá + 12 `unknown`); riêng 349 SP có lá: 7.575 (số Trung ghi ở US_49) – *Tác nhân 3 sửa: bản trước gán 7.575 cho 361 SP* | Chiến + Trung |
| G3 | **Bảng C text-embedding: "TF-IDF thắng" (Hoàng) vs "Hybrid thắng" (Chiến)** | Hoàng: kho 9.403 chunk chỉ review, 208 câu, 3 seed, chưa thử hybrid (`05_Hoang/results/bench_text_embed.csv`); Chiến: kho 10.173 chunk (title + review + detail_rating), 209 câu sau sửa nhãn qa108, có hybrid (`03_Chien/results/rag_retrieval_eval.json`) | Không mâu thuẫn về kết luận: cả hai thấy từ vựng ≥ dense; hybrid chỉ Chiến đo. **Bảng C dùng số của Chiến** (đúng kho RAG sẽ chạy) – chọn Hybrid RRF BM25 + e5-small, Hit@5 0,866; số của Hoàng là kiểm chéo độc lập | Chiến + Hoàng |
| G4 | **API /search/image (Hoàng) dùng CLIP B/32**, không phải model được chọn | `05_Hoang/docs/US_30_32_37_38_39_api.md` | API nạp index theo `indexes/best` của Khoa (model + τ_v từ config) – sau mục E | Hoàng + Khoa |
| G5 | **Baseline trong US_18 / US_27 của Trung đã cũ** (chỉ CLIP B/32, RAG faithfulness "CHƯA ĐO") | so với Khoa (5 model), Chiến (e2e RAG), Đạt (Bảng D) | Tác nhân 2 đã cập nhật US_18, US_27 theo số mới nhất | Trung |
| G6 | **Số pytest trong README khác khi chạy trên bản A2** (Trung 54 passed → 53 passed + 1 skipped; Đạt 23 passed + 1 skipped → 21 passed + 3 skipped) | test bỏ qua vì file nặng `catalog_fpi_taxonomy_v1.parquet`, `catalog_clean.parquet` không đóng gói | Ghi rõ trong README: chạy lại script sinh file thì test đó chạy | – |
| G7 | **Router: 0,878 (Trung, luật) vs 0,857 (Đạt, Gemini làm router)** dễ bị đọc như mâu thuẫn | n khác (49 vs 14), tập khác | Đây là 2 phương án router khác nhau, không phải 2 lần đo cùng hệ thống; Bảng D2 ghi cả hai, kết luận chưa đạt 0,90 | Trung |
