# MSA – AI Agent trợ lý mua sắm thời trang (Đồ án 1)

**US_02 – Dựng repo, môi trường, quy ước code** · Owner: Hoàng · Support: Trung · Trạng thái: `Hoàn thành` (khung repo) – còn việc: tạo repo GitLab thật và đẩy code.

- **Mục tiêu**: mọi thành viên chạy code giống nhau trên máy mình.
- **Đầu ra**: `README.md`, `requirements.txt` (ghim phiên bản thật), `environment.yml`, `.env.example`, `.gitignore`, `Makefile`, `run.sh`, `scripts/check_env.py`, cấu trúc thư mục.
- **Tiêu chí nghiệm thu**: người mới clone chạy được `scripts/check_env.py` trong < 10 phút. Lần chạy thật (05/11/2026, máy 2 CPU/7,8 GB): **17–32 s**, kết quả “MÔI TRƯỜNG SẴN SÀNG” (`results/check_env_output.txt`). Thời gian `pip install` trên máy sạch: **CHƯA ĐO** (N20 cài thử trên máy sạch).

## 1. Cài đặt nhanh (≈ 10 phút)

```bash
git clone <url-gitlab>/msa.git && cd msa
python -m venv .venv && source .venv/bin/activate        # hoặc: conda env create -f environment.yml
pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env    # điền GEMINI_API_KEY (không commit), hoặc đặt MSA_LLM_MOCK=1
python scripts/check_env.py
```

Chạy toàn bộ: `make all` hoặc `./run.sh` (tạo dữ liệu + index nếu thiếu rồi bật API ở cổng 8000).

## 2. Cấu trúc thư mục

| Thư mục | Nội dung | Ai ghi |
|---|---|---|
| `data/raw/` | Dữ liệu gốc tải về (không commit) | scripts 01/01b |
| `data/processed/` | `catalog_v1.parquet` theo schema 5.1 | scripts 01/01b/02, Tuấn Đạt (03_clean) |
| `data/images/<product_id>/<n>.jpg` | Ảnh sản phẩm | scripts 01/01b |
| `src/msa/` | Package chính: `llm_gateway.py`, `eval/`, `api/`, `data/`, `search/`, `embed/`, `rag/`, `agent/` | theo bảng 5.3 |
| `scripts/` | Script đánh số chạy theo thứ tự (`01_…`, `01b_…`, `02_…`, `build_index.py`, `bench_*.py`) | |
| `eval/` | Bộ đánh giá `eval_visual`, `eval_qa.jsonl`, `eval_router.jsonl` | Khoa, Chiến, Trung |
| `app/` | UI Gradio gọi API qua HTTP | Tuấn Đạt |
| `notebooks/` | EDA, phân tích (không chứa logic dùng chung) | |
| `prompts/` | Prompt Gemini (`gemini_fallback.md`…) | Chiến |
| `logs/` | `requests.jsonl`, `llm_calls.jsonl` (không commit) | API, gateway |
| `tests/` | pytest – mặc định chạy mock, `-m live` mới gọi Gemini thật | mọi người |

## 3. Quy ước

- **Branch**: `main` (luôn chạy được) ← `dev` ← `feature/US_xx-mo-ta-ngan` (vd. `feature/US_37-search-text`). Sửa lỗi: `fix/US_xx-...`.
- **Commit**: `US_xx: <động từ> <nội dung>` (vd. `US_50: thêm retry 429 cho LLMGateway`). Một commit = một thay đổi logic.
- **Merge Request**: ≥ 1 người review chéo (theo sheet Phân công); pytest phải pass; không commit dữ liệu/ảnh/key.
- **Code**: Python ≥ 3.10, type hint, docstring tiếng Việt ngắn; tên hàm/module theo hợp đồng mục 5.3 – đổi schema/API phải báo cả nhóm.
- **Bí mật**: key chỉ nằm trong `.env`/biến môi trường; `grep -r "AQ\." .` phải rỗng trước khi push.
- **Tag dữ liệu**: `data-v1` (N5), `data-v2`; release demo `v1.0-demo` (N21).

## 4. Gemini (US_50)

Mọi nhánh gọi Gemini qua `msa.llm_gateway.LLMGateway` (đọc `GEMINI_API_KEY`, `GEMINI_MODEL`; timeout, retry/backoff 429, cache SQLite, mock `MSA_LLM_MOCK=1`). Đổi model **chỉ bằng biến môi trường**: `GEMINI_MODEL=gemini-3.5-flash-lite`. Chi tiết: `docs/US_50_llm_gateway.md`.
