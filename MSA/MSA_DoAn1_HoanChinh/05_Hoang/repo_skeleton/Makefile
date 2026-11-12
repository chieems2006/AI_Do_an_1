# Chạy từ gốc repo. `make all` = kiểm môi trường → dữ liệu → index → test → API.
PY ?= python
.PHONY: check data index test api eval all
check:  ; $(PY) scripts/check_env.py
data:   ; $(PY) scripts/01_download_public.py --download --check-repro && \
          $(PY) scripts/01b_download_clothing_hats.py --check-repro && $(PY) scripts/02_merge_data_v1.py
index:  ; $(PY) scripts/build_visual_index.py
test:   ; $(PY) -m pytest -q
api:    ; cd src && uvicorn msa.api.main:app --host 0.0.0.0 --port 8000
eval:   ; $(PY) scripts/eval_api.py
all: check data index test api
