# CLAUDE.md – Đồ án 1: AI Agent trợ lý mua sắm thời trang (MSA)

Nhóm 5 người, kế hoạch 05/11 – 25/11/2026. Tài liệu viết **tiếng Việt có dấu**; thuật ngữ chuyên môn giữ tiếng Anh (Recall@K, FAISS…).
Đọc trước khi sửa gì: `README.md` → `BAO_CAO_TONG_HOP.md` → `00_Chung/00_THIET_KE_CHUNG.md` (hợp đồng chung) → `00_Chung/QUYET_DINH_CAN_CHOT.md` (quyết định A–F, G1–G7 **chưa ký**).

## Kiến trúc
Agent có 5 luồng; một router (`01_Trung/src/msa/agent/router.py`) chọn `route` trong 7 giá trị: `visual|qa|search|compare|gemini_chitchat|gemini_ood|clarify`.
1. **visual**: embedding ảnh + FAISS. Model chính chưa chốt: DINOv2-S hay FashionCLIP (QUYET_DINH mục E).
2. **qa**: RAG trên review ViMRHP, hybrid BM25 + e5-small (RRF). Phải có trích nguồn và phải từ chối khi thiếu dữ kiện.
3. **search**: tìm bằng văn bản, có lọc metadata.
4. **compare**: so sánh 2–3 SP. Bảng thuộc tính lấy từ dữ liệu, LLM chỉ diễn giải.
5. **gemini_chitchat / gemini_ood**: gọi Gemini qua `LLMGateway` (cache SQLite, xử lý 429, chế độ `MSA_LLM_MOCK=1`).

Mọi response theo cùng một schema (`00_THIET_KE_CHUNG.md` §5.2):
`{route, confidence, source, answer, items[], citations[], latency_ms, request_id}`, trong đó `source ∈ internal|gemini|cache|fallback`.
Schema sản phẩm (§5.1) và tên hàm gọi chéo (§5.3) là **hợp đồng** giữa 5 người: không đổi tên trường hay chữ ký hàm nếu chưa cập nhật tài liệu đó.

| Folder | Chủ | Nội dung chính |
|---|---|---|
| `00_Chung/` | chung | thiết kế chung, thuật ngữ, quyết định cần chốt, `kiem_dinh/check_numbers.py`, `prep_shared_data.py` |
| `01_Trung/` | nhóm trưởng | schema, taxonomy (`msa.data.taxonomy`), router + nhánh Gemini, Bảng F chấm điểm |
| `02_TuanDat/` | Tuấn Đạt | làm sạch (`src/scripts/03_clean.py`), benchmark LLM, UI Gradio (`app/app.py`) |
| `03_Chien/` | Chiến | dữ liệu tiếng Việt, `eval/eval_qa.jsonl`, `eval/eval_router.jsonl`, RAG, `prompts/gemini_fallback.md` |
| `04_Khoa/` | Khoa | EDA, `eval/eval_visual.csv`, benchmark 5 model ảnh, `build_index.py`, cải tiến visual |
| `05_Hoang/` | Hoàng | `repo_skeleton/` (requirements, check_env), `metrics.py`, API FastAPI, `llm_gateway.py` |

Mỗi folder thành viên gồm `README.md` (bảng truy vết US → file → trạng thái), `docs/`, `src/` hoặc `scripts/`, `tests/`, `results/` (chứa số đo thật). Mỗi folder là một gói Python **độc lập** có `pytest.ini` riêng, nên luôn chạy pytest từ bên trong folder đó.

## Môi trường (máy Windows này)
- Venv: `.venv/` (Python 3.11.9) ở thư mục này, chạy bằng `.venv/Scripts/python.exe`.
- Torch `2.15.0+cu132` chạy được trên RTX 4060 Laptop (`torch.cuda.is_available()` = True). Các script được viết cho CPU (`torch.set_num_threads(2)`); muốn dùng GPU thì phải chỉ định rõ.
- Khác với `requirements.txt` (bản ghim gốc trên Python 3.13):
  - `numpy==2.4.6` thay cho `2.5.3`, vì 2.5.x cần Python ≥ 3.12.
  - Cài thêm `jsonschema`, `requests`, `psutil`: code có import nhưng requirements chưa liệt kê.
- **Encoding trên Windows:** mọi chỗ đọc/ghi file text trong code đã có `encoding="utf-8"` (sửa ngày 12/11/2026), nên pytest và `check_env.py` chạy được mà không cần `PYTHONUTF8`. Một số script vẫn `print` tiếng Việt, và sẽ lỗi `UnicodeEncodeError` nếu chuyển hướng stdout ra file (`> logs/x.log`); khi đó cần đặt `PYTHONUTF8=1`.
- **Quy ước khi viết code mới:** luôn truyền `encoding="utf-8"` cho `open()`, `read_text()` và `write_text()` ở chế độ text.
- `00_Chung/kiem_dinh/check_numbers.py` cần **Python ≥ 3.12** (f-string có `\`), nên chạy trên 3.11 sẽ báo `SyntaxError`.
- Dữ liệu nặng (ảnh, `.parquet`, `.npy`, FAISS, SQLite) **không có trong repo**. Muốn sinh lại thì đặt `MSA_SHARED_DATA` và `MSA_RAW_DIR` (mặc định là đường dẫn Linux `/home/claude/...`), rồi chạy các script ở README §3.

## Lệnh thường dùng
```bash
PY=$(pwd)/.venv/Scripts/python.exe

$PY 05_Hoang/repo_skeleton/scripts/check_env.py                    # kiểm môi trường
for d in 01_Trung 02_TuanDat 03_Chien 04_Khoa 05_Hoang; do (cd $d && $PY -m pytest -q); done
(cd 03_Chien && $PY -m pytest -q -m live)                           # test gọi Gemini thật – tốn quota, chỉ chạy khi được yêu cầu
(cd 02_TuanDat && MSA_UI_MOCK=1 $PY app/app.py)                     # UI giả lập → http://localhost:7860
(cd 05_Hoang/src && $PY -m uvicorn msa.api.main:app --port 8000)    # API thật, cần index + dữ liệu
```
Kết quả pytest trên máy này (12/11/2026, sau khi sửa encoding, không cần `PYTHONUTF8`):

| Folder | Kết quả |
|---|---|
| Trung | 52 passed, 2 skipped |
| Tuấn Đạt | 21 passed, 3 skipped |
| Chiến | 49 passed, 2 skipped |
| Khoa | 30 passed |
| Hoàng | 78 passed |

Mọi test bị skip đều do thiếu file dữ liệu nặng hoặc là test `live`.

## Quy ước BẮT BUỘC
- **Không commit `.env`** hay bất kỳ key nào. Key Gemini đặt qua `GEMINI_API_KEY` hoặc `MSA_ENV_FILE`/`MSA_GEMINI_KEY_FILE`. Không in key ra màn hình, không ghi key vào log, kết quả, README hay test.
- **Không bịa số liệu.** Số nào chưa đo thì ghi `CHƯA ĐO`, kèm lệnh/script sẽ sinh ra số đó. Thông tin công khai mà không chắc chắn (giá API, license, tên model) thì gắn nhãn `[cần xác minh]`.
- **Mọi số đo phải có file kết quả** (JSON/CSV/MD trong `results/`), kèm lệnh tái lập và cấu hình (model, seed, phiên bản dữ liệu). Mỗi bảng phải ghi nhãn loại số liệu theo `00_Chung/THUAT_NGU.md`: [Thật–thật], [Thật–tổng hợp], [LLM chấm], [Tác nhân kiểm], [Chưa người duyệt], CHƯA ĐO. Không ghi "người duyệt" khi chưa có người thật duyệt.
- Không sửa file eval gốc (`eval_qa.jsonl`, `eval_router.jsonl`, `eval_visual.csv`), vì số đã báo cáo được tính trên các file đó. Muốn thay đổi thì tạo bản mới (v1.1).
- Không hard-code ngưỡng: `τ_v` đi theo model, đọc từ `indexes/<model>/config.json`.
- Gemini: chỉ gửi text, không gửi ảnh; không nêu giá/size/tồn kho nếu DB không có; câu trả lời từ Gemini phải mang `source="gemini"` để UI hiện nhãn. Test gọi Gemini thật phải gắn `@pytest.mark.live`. Free tier chỉ có 5 request/phút và 20 request/ngày/model.
- Văn bản dùng dấu phẩy thập phân (0,846), còn JSON/CSV dùng dấu chấm (0.846).
