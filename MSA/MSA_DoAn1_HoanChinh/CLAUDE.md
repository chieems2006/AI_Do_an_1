# CLAUDE.md – Đồ án 1: AI Agent trợ lý mua sắm thời trang (MSA)

Nhóm 5 người, kế hoạch 05/11 – 25/11/2026. Tài liệu viết **tiếng Việt có dấu**; thuật ngữ chuyên môn giữ tiếng Anh (Recall@K, FAISS…).
Đọc trước khi sửa gì: `README.md` → `BAO_CAO_TONG_HOP.md` → `00_Chung/00_THIET_KE_CHUNG.md` (hợp đồng chung) → `00_Chung/QUYET_DINH_CAN_CHOT.md` (quyết định A–F, G1–G7 **chưa ký**).

## Kiến trúc
Code chạy hệ thống nằm trong **một package duy nhất `src/msa/`** (ghép 12/11/2026 theo dòng `# repo:` đầu mỗi file).
Agent có 5 luồng; một router (`src/msa/agent/router.py`) chọn `route` trong 7 giá trị: `visual|qa|search|compare|gemini_chitchat|gemini_ood|clarify`.
1. **visual**: `msa.search.visual.VisualSearcher` (Khoa) + FAISS. API nạp index DINOv2-S (`04_Khoa/indexes/dinov2_s`, đề xuất mục E – chưa ký), τ_v từ `04_Khoa/results/tau_v_analysis.json` (quy tắc mục C).
2. **qa**: `msa.rag.pipeline.RAGPipeline` (Chiến) trên review ViMRHP, hybrid BM25 + e5-small (RRF), τ_r = 0. Phải có trích nguồn và phải từ chối khi thiếu dữ kiện.
3. **search**: tìm bằng văn bản, có lọc metadata.
4. **compare**: so sánh 2–3 SP. Bảng thuộc tính lấy từ dữ liệu, LLM chỉ diễn giải.
5. **gemini_chitchat / gemini_ood**: `Agent` (Trung) gọi Gemini qua `msa.llm_gateway.LLMGateway` (Hoàng) – cache SQLite, xử lý 429, chế độ `MSA_LLM_MOCK=1`.

Ghép nối ở `src/msa/api/main.py` (`State`): /search/image → VisualSearcher, /qa → RAGPipeline, /chat → Router + Agent (công cụ = 4 luồng nội bộ, bộ nhớ phiên theo `session_id`). Đường dẫn tới tài nguyên của thành viên tập trung ở `src/msa/paths.py`.

Mọi response theo cùng một schema (`00_THIET_KE_CHUNG.md` §5.2):
`{route, confidence, source, answer, items[], citations[], latency_ms, request_id}`, trong đó `source ∈ internal|gemini|cache|fallback`.
Schema sản phẩm (§5.1) và tên hàm gọi chéo (§5.3) là **hợp đồng** giữa 5 người: không đổi tên trường hay chữ ký hàm nếu chưa cập nhật tài liệu đó.

| Folder | Chủ | Nội dung chính |
|---|---|---|
| `src/msa/` | chung | package chạy hệ thống: `agent/` (Trung), `rag/` (Chiến), `search/`, `embed/` (Khoa), `api/`, `llm_gateway.py`, `data/`, `eval/` |
| `tests/integration/` | chung | test tích hợp 5 luồng, Gemini mock; `test_realdata.py` cần index + shared_data thật |
| `00_Chung/` | chung | thiết kế chung, thuật ngữ, quyết định cần chốt, `kiem_dinh/check_numbers.py`, `prep_shared_data.py` |
| `01_Trung/` | nhóm trưởng | schema, taxonomy (`msa.data.taxonomy`), router + nhánh Gemini, Bảng F chấm điểm |
| `02_TuanDat/` | Tuấn Đạt | làm sạch (`src/scripts/03_clean.py`), benchmark LLM, UI Gradio (`app/app.py`) |
| `03_Chien/` | Chiến | dữ liệu tiếng Việt, `eval/eval_qa.jsonl`, `eval/eval_router.jsonl`, RAG, `prompts/gemini_fallback.md` |
| `04_Khoa/` | Khoa | EDA, `eval/eval_visual.csv`, benchmark 5 model ảnh, `build_index.py`, cải tiến visual |
| `05_Hoang/` | Hoàng | `repo_skeleton/` (requirements, check_env), `metrics.py`, API FastAPI, `llm_gateway.py` |

Mỗi folder thành viên gồm `README.md` (bảng truy vết US → file → trạng thái), `docs/`, `scripts/` hoặc `src/scripts/`, `tests/`, `results/` (chứa số đo thật). Test và script của thành viên import `msa` từ `../src` (`pytest.ini` có `pythonpath = ... ../src`); luôn chạy pytest từ bên trong folder đó. `src/` của thành viên chỉ còn client Gemini cũ (`msa_trung`, `msa_td`, `msa_chien`) dành cho các script đo đã sinh số liệu báo cáo – **code hệ thống mới không được dùng chúng**.

## Môi trường (máy Windows này)
- Venv: `.venv/` (Python 3.11.9) ở thư mục này, chạy bằng `.venv/Scripts/python.exe`.
- Torch `2.15.0+cu132` chạy được trên RTX 4060 Laptop (`torch.cuda.is_available()` = True). Các script được viết cho CPU (`torch.set_num_threads(2)`); muốn dùng GPU thì phải chỉ định rõ.
- Khác với `requirements.txt` (bản ghim gốc trên Python 3.13):
  - `numpy==2.4.6` thay cho `2.5.3`, vì 2.5.x cần Python ≥ 3.12.
  - Cài thêm `jsonschema`, `requests`, `psutil`: code có import nhưng requirements chưa liệt kê.
- **Encoding trên Windows:** mọi chỗ đọc/ghi file text trong code đã có `encoding="utf-8"` (sửa ngày 12/11/2026), nên pytest và `check_env.py` chạy được mà không cần `PYTHONUTF8`. Một số script vẫn `print` tiếng Việt, và sẽ lỗi `UnicodeEncodeError` nếu chuyển hướng stdout ra file (`> logs/x.log`); khi đó cần đặt `PYTHONUTF8=1`.
- **Quy ước khi viết code mới:** luôn truyền `encoding="utf-8"` cho `open()`, `read_text()` và `write_text()` ở chế độ text.
- Dữ liệu nặng (ảnh, `.parquet`, `.npy`, FAISS, SQLite) **không có trong repo** (đã `.gitignore`). Trên máy này đã tái tạo (12/11/2026): `MSA_RAW_DIR=D:/DoAn1/data/raw`, `MSA_SHARED_DATA=D:/DoAn1/data/shared_data` (khai trong `.env`), index ở `04_Khoa/indexes/{dinov2_s,clip_b32}`; số đo build ở `04_Khoa/results/rebuild_2026-11-12_win/` (không ghi đè số gốc của Khoa).
- `.env` có cú pháp không hợp lệ với bash (giá trị trong `<...>`): **không `source .env`** (sẽ in key ra lỗi); chỉ đọc đúng biến cần bằng `sed`, ví dụ `export MSA_SHARED_DATA=$(tr -d '' < .env | sed -nE 's/^\s*MSA_SHARED_DATA\s*=\s*(.*\S)\s*$//p')`.
- `build_index.py` của Khoa ghi đè `04_Khoa/results/build_index_<model>.json`: khi build lại, chuyển file mới sang thư mục riêng và `git checkout` lại file gốc.

## Lệnh thường dùng
```bash
PY=$(pwd)/.venv/Scripts/python.exe

$PY 05_Hoang/repo_skeleton/scripts/check_env.py                    # kiểm môi trường
for d in 01_Trung 02_TuanDat 03_Chien 04_Khoa 05_Hoang; do (cd $d && $PY -m pytest -q); done
$PY -m pytest -q                                                    # test tích hợp 5 luồng (tests/integration)
$PY 00_Chung/kiem_dinh/check_numbers.py --strict                    # đối chiếu số trong tài liệu với file kết quả (12/11: 224/224 KHỚP); ghi đè doi_chieu_so_lieu.md
(cd 03_Chien && $PY -m pytest -q -m live)                           # test gọi Gemini thật – tốn quota, chỉ chạy khi được yêu cầu
(cd 02_TuanDat && MSA_UI_MOCK=1 $PY app/app.py)                     # UI giả lập → http://localhost:7860
$PY -m uvicorn msa.api.main:app --app-dir src --port 8000           # API thật (cần MSA_SHARED_DATA + index); GET /health xem backend
```
Kết quả pytest trên máy này (12/11/2026, sau khi hợp nhất `src/msa`, có `MSA_SHARED_DATA`; không đặt thì Trung/Chiến/tích hợp skip thêm test cần dữ liệu):

| Folder | Kết quả |
|---|---|
| Tích hợp (`tests/`) | 28 passed |
| Trung | 53 passed, 1 skipped |
| Tuấn Đạt | 21 passed, 3 skipped |
| Chiến | 51 passed |
| Khoa | 32 passed |
| Hoàng | 78 passed |

Mọi test bị skip đều do thiếu file dữ liệu nặng hoặc là test `live`.

## Quy ước BẮT BUỘC
- **Không commit `.env`** hay bất kỳ key nào. Key Gemini đặt qua `GEMINI_API_KEY` hoặc `MSA_ENV_FILE`/`MSA_GEMINI_KEY_FILE`. Không in key ra màn hình, không ghi key vào log, kết quả, README hay test.
- **Không bịa số liệu.** Số nào chưa đo thì ghi `CHƯA ĐO`, kèm lệnh/script sẽ sinh ra số đó. Thông tin công khai mà không chắc chắn (giá API, license, tên model) thì gắn nhãn `[cần xác minh]`.
- **Mọi số đo phải có file kết quả** (JSON/CSV/MD trong `results/`), kèm lệnh tái lập và cấu hình (model, seed, phiên bản dữ liệu). Mỗi bảng phải ghi nhãn loại số liệu theo `00_Chung/THUAT_NGU.md`: [Thật–thật], [Thật–tổng hợp], [LLM chấm], [Tác nhân kiểm], [Chưa người duyệt], CHƯA ĐO. Không ghi "người duyệt" khi chưa có người thật duyệt.
- Không sửa file eval gốc (`eval_qa.jsonl`, `eval_router.jsonl`, `eval_visual.csv`), vì số đã báo cáo được tính trên các file đó. Muốn thay đổi thì tạo bản mới (v1.1).
- Không hard-code ngưỡng: `τ_v` đi theo model – API đọc từ `04_Khoa/results/tau_v_analysis.json` (quy tắc `b_max_ood_val+0.01`), dự phòng `indexes/<model>/config.json`.
- **Một client Gemini duy nhất**: code trong `src/msa` chỉ gọi Gemini qua `LLMGateway` (`tests/integration/test_package.py` kiểm điều này). Module mới đặt đúng vị trí ghi ở dòng `# repo:` đầu file.
- Gemini: chỉ gửi text, không gửi ảnh; không nêu giá/size/tồn kho nếu DB không có; câu trả lời từ Gemini phải mang `source="gemini"` để UI hiện nhãn. Test gọi Gemini thật phải gắn `@pytest.mark.live`. Free tier chỉ có 5 request/phút và 20 request/ngày/model.
- Văn bản dùng dấu phẩy thập phân (0,846), còn JSON/CSV dùng dấu chấm (0.846).
