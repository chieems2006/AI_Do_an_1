# 05_Hoang – Python: data pipeline, metrics, API backend, LLM gateway Gemini, cache

Thành viên: **Hoàng** · Lượt làm việc: 04–05/11/2026 · Dữ liệu: `Data v1 (scripts 01/01b/02, seed 42)` ≡ `shared_data v1 (prep_shared_data.py seed 42)` (cùng 4.593 SP FPI) + 428 SP ViMRHP.
Đường dẫn trong repo chung ghi ở dòng đầu mỗi file (`# repo: ...`). Mọi số liệu dưới đây là **đo thật**, kèm file kết quả; chỗ chưa đo ghi `CHƯA ĐO`.

## 0. Đối chiếu yêu cầu kế hoạch (Tác nhân 2 – 05/11/2026)

Hoàng là Owner của **11 US** (Backlog). Kết luận: **Đạt 7 · Một phần 4 · Chưa đạt 0**.

| US | Đầu ra yêu cầu (DOCS) | File đầu ra | Tiêu chí nghiệm thu (TEST) | Kết quả | Bằng chứng / lý do |
|---|---|---|---|---|---|
| US_02 | README, requirements, cấu trúc thư mục | `repo_skeleton/` | Người mới clone chạy script kiểm tra môi trường < 10 phút | **Một phần** | `check_env` chạy 17–32 s (`results/check_env_output.txt`); chưa có GitLab thật, thời gian `pip install` trên máy sạch CHƯA ĐO |
| US_06 | `01_download_public.py`, log nguồn + license | `src/scripts/01_download_public.py`, `data/counts_public_footwear_accessory.json`, `data/sources_log.json` | ≥ 1.700 SP giày + phụ kiện có ảnh + metadata; chạy lại cho cùng kết quả | **Đạt** | 2.335 SP (2.100 có ảnh ≥ 1.700); 2 lần chạy cùng hash |
| US_17 | metrics.py, run_eval.py, unit test | `src/msa/eval/metrics.py`, `run_eval.py`, `tests/test_metrics.py` | Unit test khớp tính tay | **Đạt** | 10 test tính tay; Khoa đối chiếu chéo trong test của Khoa |
| US_23 | Bảng C (kết quả) | `src/scripts/bench_text_embed.py`, `docs/US_23_benchmark_text_embedding.md`, `results/bench_text_embed*.csv/json` | Cùng chunking, cùng top-K, ghi cấu hình | **Đạt** | 5 cấu hình × 3 seed, cấu hình ghi đầy đủ. Bảng C chính thức dùng số của Chiến (có hybrid, đúng kho RAG) – số của Hoàng là kiểm chéo (QUYET_DINH mục G3) |
| US_30 | API /search/image | `src/msa/api/{main,searchers}.py` | Recall@5 đạt ngưỡng; phản hồi < 1,5 s; CTE@5 ≤ 10 % | **Một phần** | Đạt: p95 1.106 ms (97,5 % < 1,5 s), CTE@5 1,5 % (`results/api_eval.json`). Chưa: Recall@5 qua API CHƯA ĐO; API đang dùng **CLIP B/32** (Khoa đo macro R@5 0,721 < 0,80) và **τ_v = 0,25** (không chặn ảnh ngoài phạm vi) → phải nạp index + τ_v từ `config.json` của Khoa (QUYET_DINH mục C, G4) |
| US_32 | module validation ảnh | `src/msa/api/validation.py` | 10 tình huống lỗi trả thông báo đúng, không crash | **Đạt** | 10 + 3 tình huống có test |
| US_37 | API /search/text | `src/msa/api/text_search.py` | Bộ lọc đúng trên 15 truy vấn | **Đạt** | 15/15 truy vấn, 300/300 kết quả thoả lọc; lọc giá/size chỉ kiểm trên dữ liệu tổng hợp (catalog không có giá/size) |
| US_38 | API /compare | `src/msa/api/compare.py` | 100 % thuộc tính khớp dữ liệu gốc trên 20 cặp | **Đạt** | 20 nhóm, 370/370 ô khớp |
| US_39 (stretch) | prompt diễn giải trên bảng | `src/msa/api/recommend.py` | LLM chỉ dùng thông số trong bảng | **Một phần** | Luật + bộ lọc câu bịa có test; chưa chạy với Gemini thật (hết quota) |
| US_48 | `01b_download_clothing_hats.py` + log + bảng đếm | `src/scripts/01b_download_clothing_hats.py`, `data/counts_public_clothing_headwear.json`, `docs/US_06_US_48_du_lieu_public.md` | ≥ 2.300 SP (quần áo ≥ 2.000, mũ ≥ 300) có ảnh + metadata; nếu mũ < 300 phải ghi quyết định | **Một phần** | Quần áo đạt (2.200 SP FPI có ảnh). Mũ **thiếu**: con số 298 của Hoàng gồm 7 băng đô (taxonomy loại) + 5 mũ ViMRHP **không có ảnh** → số chuẩn có ảnh là **285** (QUYET_DINH mục A). Đã ghi quyết định cho mũ đúng như TEST yêu cầu |
| US_50 | llm_gateway.py + .env.example + README Gemini | `src/msa/llm_gateway.py`, `docs/US_50_llm_gateway.md` | 10 request mẫu thành công; 429/timeout có dự phòng, không crash; key không trong repo; đổi model bằng env | **Đạt** | 10/10 request thật (`results/llm_gateway_live.json`); 429 thật → dự phòng (`llm_gateway_live_gemini35_quota429.json`); grep key rỗng |

**Mâu thuẫn liên quan đã xử lý (`00_Chung/QUYET_DINH_CAN_CHOT.md`):**
- **Mục D – `source="fallback"`:** đề xuất của Hoàng được chọn làm phương án đề xuất; đã thêm vào UI của Đạt (nhãn "Thông báo hệ thống"), router của Trung và `openapi_contract.yaml` – chờ Trung chốt.
- **Mục F – token:** "10.460 vào + 6.370 ra /100" của Hoàng là **/100 lời gọi Gemini** với prompt hệ thống ngắn (≈ 105 token vào/lời gọi); quy về 100 lượt hội thoại (fallback 0,273) ≈ 4.599 token – không mâu thuẫn với 6.028 (Trung, /100 lượt hội thoại) hay 74.750 + 4.170 = 78.920 (Chiến, /100 lời gọi, prompt few-shot dài), chỉ khác đơn vị và độ dài prompt.
- **Mục A, G1 – phiên bản dữ liệu:** Data v1 (5.021 SP) giữ băng đô + đếm ViMRHP vào nhóm theo SubCategory; đề xuất Data v1.1 = catalog sạch của Đạt (4.385) + nhãn taxonomy.

## 1. Bảng truy vết US → file → trạng thái → số liệu thật → việc còn lại (bản của thành viên)

| US | File chính | Trạng thái | Số liệu THẬT (file) | Việc còn lại |
|---|---|---|---|---|
| US_02 Repo/môi trường | `repo_skeleton/` (README, requirements ghim bản thật, environment.yml, .env.example, .gitignore, Makefile, run.sh, scripts/check_env.py) | Hoàn thành (khung) | check_env chạy 17–32 s, "MÔI TRƯỜNG SẴN SÀNG" (`results/check_env_output.txt/json`) | Tạo GitLab thật; cài thử máy sạch (N20) – thời gian pip install CHƯA ĐO |
| US_06 Dataset public giày + phụ kiện | `src/scripts/01_download_public.py`, `src/msa/data/{converters,pipeline}.py` | Hoàn thành | 2.335 SP (giày 1.571, phụ kiện 764; 2.100 có ảnh); chạy 2 lần cùng hash catalog + ảnh (`data/counts_public_footwear_accessory.json`) | Xác minh license FPI |
| US_48 Quần áo + mũ | `src/scripts/01b_download_clothing_hats.py`, `src/scripts/02_merge_data_v1.py` | Một phần | quần áo 2.388 ✅, **mũ 298 < 300** ❌; Data v1 5.021 SP, schema hợp lệ 100%; probe Amazon 20.000 dòng → 372 mũ (234 thuộc 4 loại) nhưng ảnh bị chặn (`data/counts_*.json`, `data/amazon_probe.json`) | Nhóm chốt quyết định mũ (docs mục 4); tải ảnh Amazon trên máy thật |
| US_17 Metrics | `src/msa/eval/metrics.py`, `src/msa/eval/run_eval.py` | Hoàn thành | 10 unit test khớp tính tay | Khoa/Chiến/Trung xuất file dự đoán theo định dạng |
| US_23 Benchmark text-embedding | `src/scripts/bench_text_embed.py` | Hoàn thành (bge-m3 bỏ – RAM) | 5 cấu hình × 3 seed; eval_qa Chiến (208 câu): Hit@5 trong SP – tfidf_word 0,875, tfidf_char 0,856, e5-small 0,803, minilm-l12 0,794, vn-sbert 0,775 (`results/bench_text_embed*.csv/json`) | Hybrid TF-IDF + e5; bge-m3 trên máy nhóm; tách theo origin |
| US_50 LLM Gateway | `src/msa/llm_gateway.py` | Hoàn thành | 10/10 request thật thành công (`gemini-3.5-flash-lite` đổi bằng env), token/**100 lời gọi Gemini**: vào 10.460, ra 6.370 (≈ 4.599 token/100 lượt hội thoại – QUYET_DINH mục F); cache lặp lại 10/10 hit, 0 lời gọi, p50 17,9 ms; thinking 3.5-flash: mặc định 458 token vs budget 0 → 0 (`results/llm_gateway_live.json`, `results/llm_gemini35_thinking_probe.json`); quota free tier 5 RPM & 20 RPD/model – 429 thật → dự phòng không crash (`results/llm_gateway_live_gemini35_quota429.json`) | Đơn giá `[cần xác minh]`; đo lại 3 cấu hình thinking × 10 câu khi có quota |
| US_30 /search/image | `src/msa/api/{main,searchers}.py`, `src/scripts/build_visual_index.py` | Phần đo được: đạt | 80 truy vấn: p50 393 ms, p95 1.106 ms (97,5% < 1,5 s), cross-type error@5 = 1,5%, sub-category P@5 = 0,925 (`results/api_eval.json`) | **Recall@5 CHƯA ĐO** (cần eval_visual của Khoa + ảnh ngoài đời) |
| US_32 Validate ảnh | `src/msa/api/validation.py` | Hoàn thành | 10 tình huống lỗi + 3 tình huống bổ sung, đều đúng mã, không crash (test) | – |
| US_37 /search/text + lọc | `src/msa/api/text_search.py` | Hoàn thành | 15/15 truy vấn thật, 300/300 kết quả thoả lọc, p50 20 ms | Lọc giá/size chỉ test trên dữ liệu tổng hợp (catalog thật thiếu giá/size) |
| US_38 /compare | `src/msa/api/compare.py` | Hoàn thành | 20 nhóm thật, **370/370 ô khớp dữ liệu gốc (100%)**, p50 3,4 ms | – |
| US_39 (stretch) gợi ý | `src/msa/api/recommend.py` | Hoàn thành (luật + kiểm không bịa) | test: câu LLM bịa bị loại | Chạy với Gemini thật khi có quota |

Tài liệu: `docs/US_06_US_48_du_lieu_public.md`, `docs/US_17_metrics.md`, `docs/US_23_benchmark_text_embedding.md`, `docs/US_50_llm_gateway.md`, `docs/US_30_32_37_38_39_api.md`.

## 2. Kết quả pytest

```
cd 05_Hoang && python -m pytest -q
→ 78 passed, 1 deselected (test live) – 05/11/2026
```
Test gọi Gemini thật đánh dấu `live`, bỏ qua mặc định (`MSA_ENV_FILE=<.env> python -m pytest -m live`).

## 3. Cách chạy

```bash
cd 05_Hoang
python src/scripts/01_download_public.py --check-repro          # dữ liệu giày + phụ kiện
python src/scripts/01b_download_clothing_hats.py --check-repro --amazon-lines 20000
python src/scripts/02_merge_data_v1.py                         # Data v1 → data/processed/catalog_v1.parquet
python src/scripts/build_visual_index.py                       # CLIP B/32 embedding (~10 phút trên 2 CPU bận)
cd src && uvicorn msa.api.main:app --port 8000                 # API (đường dẫn mặc định tính từ thư mục 05_Hoang)
python src/scripts/eval_api.py                                 # đo thật API → results/api_eval.json
python src/scripts/bench_text_embed.py --models e5-small --eval-qa ../03_Chien/eval/eval_qa.jsonl   # US_23 (1 model/lần)
MSA_LLM_MOCK=0 python src/scripts/llm_gateway_live.py --env-file <.env>                            # US_50 (tốn quota)
```

## 4. Lưu ý quan trọng cho nhóm
1. **Gemini free tier: 5 request/phút và 20 request/ngày cho mỗi project/model** (đọc từ lỗi 429 thật). Key chung cho 5 người → hết quota rất nhanh; luôn dùng cache + `MSA_LLM_MOCK=1` khi phát triển; cân nhắc mỗi người một project hoặc bật billing.
2. Đề xuất bổ sung hợp đồng 5.2: `source="fallback"` cho thông điệp dự phòng (gateway) – cần Trung xác nhận.
3. Ảnh FPI chỉ 60×80 → kết quả visual trên ảnh studio cao (top-1 TB 0,96) nhưng **không phản ánh ảnh người dùng**; τ_v = 0,25 không chặn được gì với CLIP B/32.
4. Catalog thật **không có giá, size, mô tả** → bộ lọc giá/size, so sánh giá, QA về size phụ thuộc crawl VN (US_07).
5. Máy 2 CPU / 7 GB dùng chung: benchmark bị OOM-kill nhiều lần khi nhiều tác nhân chạy cùng lúc → chạy 1 model/tiến trình; latency đo được là cận trên.
6. Ảnh và parquet lớn **không đóng gói** trong bản giao nộp (bản gốc để ở `/home/claude/work/artifacts_05_Hoang/` qua symlink `data/images`, `data/processed`, `results/cache`); sinh lại bằng các lệnh ở mục 3. Đường dẫn dữ liệu đổi bằng biến môi trường `MSA_SHARED_DATA`, `MSA_RAW_DIR` (hoặc tham số `--raw-dir`, `--shared`).
7. Không có key trong folder: `grep -rn "AQ\." 05_Hoang` rỗng.
