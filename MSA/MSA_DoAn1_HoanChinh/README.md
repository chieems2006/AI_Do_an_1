# Đồ án 1 – AI Agent trợ lý mua sắm thời trang (MSA) · bản giao nộp đã kiểm định

**Đề tài.** Trợ lý mua sắm thời trang 4 nhóm (giày dép, quần áo, mũ, phụ kiện) gồm 5 luồng: (1) tìm sản phẩm bằng ảnh (embedding ảnh + FAISS), (2) hỏi đáp về sản phẩm bằng tiếng Việt (RAG + LLM, có trích nguồn và từ chối khi thiếu thông tin), (3) tìm kiếm bằng văn bản có bộ lọc, (4) so sánh 2–3 sản phẩm, (5) trò chuyện/câu ngoài phạm vi chuyển sang Gemini API (có cache, có nhãn nguồn trả lời).
**Nhóm:** Trung (nhóm trưởng), Tuấn Đạt, Chiến, Khoa (ML), Hoàng (Python). **Kế hoạch:** 05/11 – 25/11/2026 (21 ngày, 51 user story, 199 point).
**Trạng thái bản này (05/11/2026):** phần nghiên cứu của Tuần 1–2 và một phần Tuần 3 đã làm trước bằng dữ liệu thật; các bước cần người thật (duyệt nhãn, chụp ảnh ngoài đời, họp chốt) **chưa làm**. Phần việc của từng thành viên do tác nhân AI đóng vai thực hiện, sau đó qua 2 vòng rà soát (Tác nhân 2) và kiểm định (Tác nhân 3).

> Đọc theo thứ tự: **`BAO_CAO_TONG_HOP.md`** (báo cáo chi tiết từng thành viên, bản Word: `BAO_CAO_TONG_HOP.docx`) → `00_Chung/QUYET_DINH_CAN_CHOT.md` (việc nhóm phải chốt) → `KIEM_DINH_TAC_NHAN_3.md` (nhật ký kiểm định).

## 1. Cấu trúc folder

```
MSA_DoAn1_HoanChinh/
├── README.md                    # file này
├── BAO_CAO_TONG_HOP.md / .docx  # báo cáo tổng hợp – những gì từng thành viên đã làm
├── KIEM_DINH_TAC_NHAN_3.md      # nhật ký kiểm định cuối (lỗi phát hiện, sửa, kết quả test)
├── TONG_HOP_TAC_NHAN_1.md       # ảnh chụp lúc Tác nhân 1 gom kết quả (lịch sử)
├── CHANGELOG_TAC_NHAN_2.md      # các chỉnh sửa của Tác nhân 2 (lịch sử)
├── src/msa/                     # package chung chạy hệ thống (ghép code 5 thành viên theo dòng "# repo:")
├── tests/integration/           # test tích hợp 5 luồng (Gemini mock) – chạy: python -m pytest -q ở thư mục này
├── 00_Chung/                    # dùng chung
│   ├── 00_THIET_KE_CHUNG.md     # schema, định dạng response, quy tắc Gemini, quy tắc số liệu
│   ├── QUYET_DINH_CAN_CHOT.md   # 6 quyết định A–F + mâu thuẫn G1–G7 chờ nhóm ký
│   ├── THUAT_NGU.md             # định nghĩa độ đo + nhãn loại số liệu, có ví dụ bằng số của đồ án
│   ├── kiem_dinh/               # check_numbers.py + doi_chieu_so_lieu.md (đối chiếu số tự động)
│   ├── giao_viec/, trich_ke_hoach/   # phần việc từng người trích từ kế hoạch
│   ├── prep_shared_data.py, stats.json   # chuẩn bị dữ liệu dùng chung (shared_data v1)
├── 01_Trung/    # nhóm trưởng: charter, schema, taxonomy, độ đo & ngưỡng, Bảng F, kiến trúc, router + nhánh Gemini
├── 02_TuanDat/  # phương pháp thu thập, làm sạch, bảng nguồn, benchmark LLM, UI Gradio, test plan
├── 03_Chien/    # dữ liệu tiếng Việt, eval_qa/eval_router, độ đo QA/Agent, RAG, prompt Gemini fallback
├── 04_Khoa/     # EDA, eval_visual, benchmark 5 model ảnh, index FAISS, baseline e2e, cải tiến visual
└── 05_Hoang/    # repo skeleton, tải dữ liệu public, metrics.py, API FastAPI, LLM gateway
```
Từ 12/11/2026 code chạy hệ thống nằm ở `src/msa/` (một bản duy nhất; Gemini chỉ qua `msa.llm_gateway.LLMGateway`). Tài nguyên (prompt, schema, eval, index, kết quả) vẫn ở folder thành viên, đường dẫn tập trung trong `src/msa/paths.py`. Client Gemini cũ của Trung/Đạt/Chiến (`msa_trung`, `msa_td`, `msa_chien` trong `src/` của từng người) chỉ còn dùng cho các script đo đã sinh số liệu báo cáo.
Mỗi folder thành viên có `README.md` (mục 0: bảng đối chiếu US → đầu ra → kết quả), `docs/` (tài liệu theo US), `src/` hoặc `scripts/`, `tests/`, `results/` (số đo thật dạng JSON/CSV/MD).

## 2. Cài đặt và chạy

Môi trường đã dùng: Python 3.13, 2 CPU, 7 GB RAM, không GPU. Danh sách thư viện có ghim phiên bản: `05_Hoang/repo_skeleton/requirements.txt` (kiểm môi trường: `python 05_Hoang/repo_skeleton/scripts/check_env.py`).

**Kiểm thử (không cần mạng, không gọi Gemini):**
```bash
for d in 01_Trung 02_TuanDat 03_Chien 04_Khoa 05_Hoang; do (cd $d && python -m pytest -q); done
python -m pytest -q                             # test tích hợp 5 luồng của src/msa (tests/integration)
python 00_Chung/kiem_dinh/check_numbers.py      # đối chiếu số trong tài liệu với file kết quả
```
Kết quả lần kiểm định cuối (05/11/2026): Trung **53 passed, 1 skipped**; Tuấn Đạt **21 passed, 3 skipped**; Chiến **51 passed**; Khoa **30 passed**; Hoàng **78 passed** (test gọi Gemini thật gắn nhãn `live`, bỏ qua mặc định; các test *skipped* cần file nặng không đóng gói – xem mục 3).

**Demo giao diện (chế độ API giả lập):** `cd 02_TuanDat && MSA_UI_MOCK=1 python app/app.py` → http://localhost:7860.
**API thật:** `uvicorn msa.api.main:app --app-dir src --port 8000` (chạy ở thư mục này; cần dữ liệu và index sinh ở mục 3). /search/image dùng VisualSearcher của Khoa trên index DINOv2-S (`04_Khoa/indexes/dinov2_s`, đề xuất mục E), τ_v đọc từ `04_Khoa/results/tau_v_analysis.json` (mục C); /qa dùng RAGPipeline của Chiến; /chat dùng Router + Agent của Trung; mọi lời gọi Gemini qua LLMGateway của Hoàng. Trạng thái các backend: `GET /health`.
**Gemini:** key **không** có trong folder (`grep -rn "AQ\.Ab8" .` rỗng). Đặt `GEMINI_API_KEY` hoặc trỏ `MSA_ENV_FILE` / `MSA_GEMINI_KEY_FILE` tới file `.env` riêng ngoài repo (mẫu: `05_Hoang/repo_skeleton/.env.example`). Free tier đo được: 5 request/phút, 20 request/ngày/model.

**Biến môi trường đường dẫn** (thay cho đường dẫn tuyệt đối trong code; mặc định là đường dẫn của máy đã chạy):

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `MSA_SHARED_DATA` | thư mục dữ liệu dùng chung (`catalog_fpi.parquet`, `fpi_images/`, `vimrhp_fashion_products.jsonl`) | `/home/claude/work/shared_data` |
| `MSA_RAW_DIR` | dữ liệu thô tải về (`fpi/data/*.parquet`, `vimrhp/Annotation/Fashion-*.json`) | `/home/claude/realdata` |
| `MSA_CHIEN_EVAL_ROUTER` | eval_router dùng cho `01_Trung/scripts/eval_router.py` | `../03_Chien/eval/eval_router.jsonl` |
| `MSA_IMAGE_ROOT` | gốc ảnh cho UI của Đạt | như `MSA_SHARED_DATA` |
| `MSA_VISUAL_INDEX` | index ảnh cho /search/image (`MSA_VISUAL_BACKEND=clip` để dùng CLIP B/32 cũ) | `04_Khoa/indexes/dinov2_s` |
| `MSA_QA_BACKEND`, `MSA_RAG_DENSE` | `rag` (RAG của Chiến) hoặc `stub`; `0` = chỉ BM25, không tải e5 | `rag`, `1` |
| `MSA_CATALOG`, `MSA_IMAGES_ROOT` | catalog + gốc ảnh cho API | Data v1 của Hoàng nếu đã build, không thì `shared_data` |
| `MSA_RUNTIME_DIR` | log request + cache LLM khi chạy API (không commit) | `runtime/` |
| `GEMINI_API_KEY`, `MSA_ENV_FILE`, `MSA_GEMINI_KEY_FILE` | key Gemini (không commit) | – |

## 3. Dữ liệu đã dùng – nguồn, license, cách tái tạo file nặng

| Nguồn | Dùng cho | Quy mô thực tế | License / ràng buộc |
|---|---|---|---|
| Fashion Product Images (small) – mirror HF `ashraq/fashion-product-images-small` (gốc Kaggle `paramaggarwal/fashion-product-images-dataset`, dữ liệu Myntra) | catalog + ảnh cho visual search, tìm, so sánh | 44.072 dòng gốc → chọn 4.593 SP 4 nhóm → **4.385 SP sau làm sạch** (giày 1.400, quần áo 2.000, phụ kiện 700, **mũ 285**); ảnh 60×80 px; không có giá/size/mô tả | `[cần xác minh]` – chưa đọc được Data Card gốc; chỉ dùng học thuật, không phát hành lại ảnh |
| ViMRHP (HF `trucmtnguyen/ViMRHP`), mục Fashion | review tiếng Việt cho RAG, eval_qa | 509 SP / 11.009 review; bỏ 81 đồng hồ → 428 SP / 9.403 review → 9.317 review sau khử trùng; 361 SP thuộc 4 nhóm | **CC BY-NC-ND 4.0** – phi thương mại, không phát hành bản chỉnh sửa |
| Bộ đánh giá tự tạo | eval_visual (600 truy vấn + 60 OOD), eval_qa (280 câu), eval_router (78 + 45 + 49 câu), 60 kịch bản e2e | xem `BAO_CAO_TONG_HOP.md` §2 | sinh tự động bằng biến đổi ảnh / Gemini / tác nhân viết; **chưa có người duyệt** |
| Dự phòng chưa dùng | Amazon Reviews 2023, ABO (CC BY-NC 4.0), Clothing Dataset (CC0), DeepFashion | – | xem `02_TuanDat/docs/US_10_bang_nguon_va_tinh_chinh_thong.md` |

**File nặng không đóng gói** (tái tạo được, ~150 MB): ảnh, `.parquet`, cache embedding `.npy`, FAISS index, cache SQLite.
```bash
python 00_Chung/prep_shared_data.py                                   # shared_data v1 (cần MSA_RAW_DIR)
cd 01_Trung && PYTHONPATH=src python scripts/build_category_map.py     # data/catalog_fpi_taxonomy_v1.parquet
cd 02_TuanDat && python src/scripts/03_clean.py                         # results/catalog_clean.parquet (4.385 SP)
cd 03_Chien && HF_HUB_OFFLINE=1 PYTHONPATH=src python src/scripts/eval_rag.py retrieval   # cache e5 + số retrieval
cd 04_Khoa && python src/scripts/bench_image_embed.py --model dinov2_s  # cache embedding (≈ 13 phút/model trên 2 CPU)
cd 04_Khoa && python src/scripts/build_index.py --model fashionclip --out indexes/fashionclip --reuse-cache --tau-v 0.7039 --gate-tau 0.9
cd 05_Hoang && python src/scripts/01_download_public.py && python src/scripts/01b_download_clothing_hats.py && python src/scripts/02_merge_data_v1.py
```

## 4. Ba yêu cầu của thầy → file trả lời

| Yêu cầu | Nội dung | Trả lời tổng hợp | Chi tiết theo thành viên |
|---|---|---|---|
| **1. Thu thập dữ liệu** | Phương pháp nào, vì sao chọn/không chọn, kết quả (nguồn, tính chính thống, phân loại, đặc điểm) | `BAO_CAO_TONG_HOP.md` §8.1; `01_Trung/docs/US_27_bao_cao_tuan2_khung.md` (Yêu cầu 1) | `02_TuanDat/docs/US_04_phuong_phap_thu_thap.md`, `US_08_quy_trinh_lam_sach.md`, `US_10_bang_nguon_va_tinh_chinh_thong.md`; `04_Khoa/docs/US_09_eda/eda_report.md`; `05_Hoang/docs/US_06_US_48_du_lieu_public.md`; `03_Chien/docs/US_07_kiem_tra_robots_tos.md`; `01_Trung/docs/US_49_taxonomy.md` |
| **2. Độ đo** | Có những độ đo nào; chọn độ đo nào, vì sao | `BAO_CAO_TONG_HOP.md` §8.2; `00_Chung/THUAT_NGU.md` | `04_Khoa/docs/US_12_do_do_visual_search.md`; `03_Chien/docs/US_13_do_do_qa_rag.md`, `US_14_do_do_search_compare_agent.md`; `01_Trung/docs/US_18_chot_do_do_va_nguong.md`; `05_Hoang/docs/US_17_metrics.md` |
| **3. Khảo sát phiên bản** | So sánh các phiên bản/mô hình tương tự bằng số liệu | `BAO_CAO_TONG_HOP.md` §8.3 | `04_Khoa/docs/US_19_khao_sat_embedding_anh.md`, `US_22_benchmark_embedding.md`, `US_21_he_thong_va_bai_bao_tuong_tu.md`; `01_Trung/docs/US_25_bang_cham_diem_co_trong_so.md`; `03_Chien/docs/US_20_khao_sat_text_embedding_llm.md`; `05_Hoang/docs/US_23_benchmark_text_embedding.md`; `02_TuanDat/docs/US_24_benchmark_llm.md` |

## 5. Quy ước số liệu
Mỗi bảng ghi loại số liệu theo `00_Chung/THUAT_NGU.md`: **[Thật–thật]**, **[Thật–tổng hợp]** (truy vấn/câu hỏi do máy tạo), **[LLM chấm]** (không phải người chấm), **[Tác nhân kiểm]**, **[Chưa người duyệt]**, **CHƯA ĐO**. Dấu phẩy thập phân trong văn bản (0,846) = dấu chấm trong JSON/CSV (0.846). Mọi số trong `BAO_CAO_TONG_HOP.md` và các README đã được đối chiếu tự động với file kết quả (`00_Chung/kiem_dinh/doi_chieu_so_lieu.md`).
