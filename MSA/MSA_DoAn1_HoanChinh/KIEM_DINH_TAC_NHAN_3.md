# Nhật ký kiểm định – Tác nhân 3 (kiểm định viên cuối) – 05/11/2026

Phạm vi: kiểm câu từ, logic, tính đúng sai của kết quả sau Tác nhân 2; sửa lỗi; tổng hợp folder hoàn chỉnh. **Không gọi Gemini, không chạy lại benchmark nặng, không bịa số.** `stage1/` không bị sửa. Ưu tiên: (1) đối chiếu số liệu, (2) báo cáo tổng hợp, (3) README gốc, (4) các sửa khác.

## 1. Đối chiếu số liệu (bắt buộc, có script)

- Script: `00_Chung/kiem_dinh/check_numbers.py` (chỉ thư viện chuẩn). Mỗi khẳng định = chuỗi số như viết trong tài liệu + danh sách tài liệu chứa nó + file nguồn + cách đọc giá trị (đọc trực tiếp JSON/CSV/JSONL; một số dòng là phép tính từ file, vd token/100 lượt = 47/172 × 100 × token/lời gọi). Kết quả ghi vào `00_Chung/kiem_dinh/doi_chieu_so_lieu.md`. Script còn **quét câu chữ rủi ro** (adapter 0,921 không ghi "tổng hợp"; token "/100 lượt" nhầm đơn vị; 7.575 ↔ 361; 0,923 gọi là held-out; faithfulness gọi là người chấm).
- Phạm vi: README 5 thành viên, `QUYET_DINH_CAN_CHOT.md`, `THUAT_NGU.md`, US_25, US_27, US_41, US_45, US_49, US_26, `README.md` gốc, `BAO_CAO_TONG_HOP.md`.
- Các mục bắt buộc đã kiểm: bảng 5 model ảnh của Khoa (macro R@5, R@1, MRR@10, CTE@5, cat P@5, latency, RAM – 35 số), Bảng F (5 tổng điểm + tính lại từ điểm thành phần × trọng số + 12/12 cấu hình độ nhạy + kịch bản B), mũ 285/286/293/298, router 0,667/0,878/0,923/0,949/0,846, RAG 15/15 (và 15/16 trước sửa nhãn), Hybrid Hit@5 0,866/0,895, text-embed TF-IDF > neural (5 model của Hoàng), faithfulness/hallucination Bảng D, token/100 lượt (6.028; 15.092; 21.566; 4.599), latency API, số SP, số review, số câu eval, số chunk.
- **Kết quả cuối: 211 khẳng định – KHỚP 211, LỆCH 0, lỗi đọc 0; quét câu chữ: 0 cảnh báo** (sau khi sửa các lỗi ở mục 2).
- Lần chạy đầu phát hiện **1 lệch thật** (review ViMRHP, mục 2 #1) và 1 số cần giải thích nguồn (144 lời gọi 429 = 36 câu trong file `failed/` × 4 lần thử – khớp ghi chú ở US_28 của Đạt).
- Tác nhân 3 chạy lại (trên bản sao tạm, không ghi đè kết quả) 3 script rẻ để kiểm tái lập: `run_scoring_from_khoa.py` → `weighted_scoring.json` **giống hệt**; `eval_router.py` → 0,9231 / 0,8776 **giống**; `recall_by_transform.py` → CSV **giống hệt**; `build_eval_router.py --check` → không lỗi.

## 2. Lỗi phát hiện và cách sửa

| # | Loại | Vị trí | Lỗi | Sửa |
|---|---|---|---|---|
| 1 | Số liệu sai | `00_Chung/QUYET_DINH_CAN_CHOT.md` G2; `01_Trung/docs/US_26…`, `US_49…` | "7.575 review của 361 SP trong phạm vi" – đếm lại từ `vimrhp_taxonomy_v1.csv`: 7.575 là của **349 SP có lá** (keep); 361 SP (gồm 12 unknown) có **7.833** review | Sửa cả 3 file, ghi cả hai số |
| 2 | Đơn vị sai | `03_Chien/README.md` (US_51), `docs/US_14…`, `docs/US_51…`; `05_Hoang/README.md` (US_50) | "74.750 in + 4.170 out token/100 lượt", "token/100 lượt: vào 10.460" – thực ra là **/100 lời gọi Gemini** (trái quyết định F) | Đổi thành "/100 lời gọi Gemini" + số quy đổi /100 lượt hội thoại (21.566; 4.599) |
| 3 | Kết luận vượt số liệu | `04_Khoa/README.md`, `docs/US_45…`, `TONG_HOP_TAC_NHAN_1.md` | Adapter I3 0,829 → 0,921 gọi là "cải thiện rõ nhất" – adapter học trên cùng họ biến đổi tổng hợp với truy vấn test | Ghi rõ **[Thật–tổng hợp]**, "chưa chứng minh cải thiện trên ảnh thật", mặc định tắt |
| 4 | Logic quyết định | `04_Khoa/docs/US_45…` (I19) | "GIỮ dạng mềm" trong khi lọc cứng làm R@5 giảm – không thoả chính quy tắc của tài liệu; dạng mềm chưa đo | Ghi "không thoả quy tắc", "dạng mềm CHƯA ĐO"; sửa −29 % → −28 % (0,0617 → 0,0442) |
| 5 | Held-out | `03_Chien/README.md` US_35, `01_Trung/docs/US_27…` | 15/15 từ chối đúng là **sau khi sửa nhãn qa108 trên chính tập test** (trước 15/16); trình bày như kết quả nghiệm thu đạt | Ghi cả số trước/sau, "không phải held-out"; hạ US_35 Đạt → **Một phần** (mới đo 15/71 câu không đáp án) – Chiến: Đạt 4 · Một phần 5 |
| 6 | LLM chấm | `01_Trung/docs/US_27…` | Faithfulness chỉ ghi [LLM chấm] chung | Ghi rõ giám khảo (Gemini chấm Gemini; `gemini-2.5-flash`) và "không phải đánh giá của người" |
| 7 | Thuật ngữ / công thức | `00_Chung/THUAT_NGU.md` | Recall@K định nghĩa như Hit@K; NDCG mô tả mơ hồ; thiếu mAP, F1 thuộc tính; mẫu số hallucination khác nhau giữa Đạt (mọi câu) và Chiến (câu không từ chối) không được nói; ví dụ token dùng 27,3 % (ra 6.022, không phải 6.028); khoảng cosine OOD ghi 0,6–0,8 (thực tế 0,4–0,8 tuỳ model); held-out chưa nói "sửa nhãn" | Viết lại công thức Recall@K, NDCG (ví dụ hạng 3 → 0,5), thêm AP/mAP (ví dụ 0,833), F1 thuộc tính (ví dụ 0,4); ghi mẫu số; sửa ví dụ; bổ sung định nghĩa held-out |
| 8 | Model / dataset | `01_Trung/docs/US_27…`, `02_TuanDat/docs/US_10…` | ResNet-50 ghi năm 2015 (bài CVPR 2016); mã arXiv/venue ViMRHP chưa được xác minh; ABO đã biết CC BY-NC 4.0 nhưng còn `[cần xác minh]` | ResNet-50 → 2016 (arXiv 2015); thêm `[cần xác minh]` cho arXiv/NLDB của ViMRHP; ABO ghi CC BY-NC 4.0. Giữ `[cần xác minh]` cho license Fashion Product Images. Đã đối chiếu: CLIP 2021 OpenAI · SigLIP 2023 Google · DINOv2 2023 Meta (384 chiều, Apache-2.0) · FashionCLIP 2022 (Chia và cs., Scientific Reports) · ViMRHP CC BY-NC-ND 4.0 – đúng |
| 9 | Đường dẫn trong code | 22 file `.py` | Hard-code `/home/claude/work/shared_data`, `/home/claude/realdata` | Thay bằng `os.environ.get("MSA_SHARED_DATA", …)`, `os.environ.get("MSA_RAW_DIR", …)` (giữ mặc định cũ) – kiểm bằng AST mọi file có `import os` ở top-level |
| 10 | Đường dẫn tới bản gốc | `01_Trung/scripts/eval_router.py`, `04_Khoa/src/scripts/probe_precision.py` | Trỏ `/home/claude/work/stage1/...` | Đổi sang đường dẫn tương đối theo `__file__` (+ biến `MSA_CHIEN_EVAL_ROUTER`); file tạm `/tmp/sp_*.npy` → `$TMPDIR` |
| 11 | Đường dẫn file key | `00_Chung/00_THIET_KE_CHUNG.md` | Ghi đường dẫn tuyệt đối tới file key trong `/tmp/claude-0/...` | Thay bằng hướng dẫn `.env` ngoài repo qua `MSA_ENV_FILE` / `MSA_GEMINI_KEY_FILE` / `GEMINI_API_KEY` |
| 12 | Cấu hình | `05_Hoang/repo_skeleton/.env.example`, `01_Trung/pytest.ini` | `MSA_TAU_V=0.25`, `GEMINI_THINKING_BUDGET=0` không có cảnh báo (0,25 không chặn OOD; flash-lite từ chối budget 0) | Thêm chú thích + biến `MSA_SHARED_DATA`, `MSA_RAW_DIR`; marker `realdata` nói rõ biến môi trường |
| 13 | Tài liệu lỗi thời | `QUYET_DINH_CAN_CHOT.md` dòng 4; `05_Hoang/README.md` mục 4.6 | Trỏ tới folder `A2_chinh_sua/`; nói ảnh/parquet nằm ở symlink không còn trong bản giao nộp | Sửa tham chiếu; ghi "không đóng gói, sinh lại bằng script" |

Các điểm đã kiểm và **đúng**, không cần sửa: công thức Recall/Hit/MRR/mAP@K/NDCG trong `04_Khoa/docs/US_12…` (ví dụ tính tay: MRR 1/3, NDCG 0,5, P@5 0,6, Recall@5 3/31); ví dụ MRR (1 + 0,5 + 0,25)/3 = 0,583, macro R@5 0,829, faithfulness 1/2, hallucination 4/36, CTE 1/5 trong THUAT_NGU; ví dụ min–max tốc độ FashionCLIP 4,71 (US_25); Bảng F tính lại = 4,833; 285 = 293 − 7 băng đô − 1 trùng MD5 (cap 258 + beanie 21 + wide_brim 6); 4.385 = 1.400 + 2.000 + 700 + 285; 10.173 chunk = 428 + 9.317 + 428; Router "0,878 held-out / 0,923 đã chỉnh luật" được ghi đúng nghĩa ở mọi nơi; nhất quán giữa 5 thành viên và `QUYET_DINH_CAN_CHOT.md` về mũ 285, τ_v theo model, `source="fallback"`, DINOv2-S hạng 1.

Định dạng: kiểm tự động mọi bảng markdown (số cột từng dòng = header) – **0 bảng vỡ**.

## 3. Kiểm code

| Kiểm tra | Kết quả |
|---|---|
| `python -m pytest -q` – 01_Trung | **53 passed, 1 skipped, 1 deselected** (skip: thiếu `data/catalog_fpi_taxonomy_v1.parquet`; deselected: test `live` gọi Gemini) |
| 02_TuanDat | **21 passed, 3 skipped** (2 skip thiếu `results/catalog_clean.parquet`, 1 skip test live) |
| 03_Chien | **51 passed, 1 deselected** |
| 04_Khoa | **30 passed** |
| 05_Hoang | **78 passed, 1 deselected** |
| Tổng | **233 passed, 4 skipped**, 0 failed – trước và sau khi sửa đường dẫn kết quả giống nhau |
| `python -m py_compile` toàn bộ 122 file `.py` (gồm `check_numbers.py`) | **OK**, 0 lỗi |
| `grep -rn "AQ\.Ab8" .` | **rỗng** (cả mẫu rộng `AQ\.` cũng rỗng) |
| `grep -rIn "/tmp/claude-0" .` | **rỗng** (trừ nhật ký này mô tả việc đã xoá) |
| `/home/claude/...` trong code | còn là **giá trị mặc định** trong `os.environ.get(...)` hoặc trong docstring ví dụ lệnh; đổi bằng biến môi trường – bảng biến ở `README.md` §2 |
| File rác | đã xoá mọi `__pycache__/`, `.pytest_cache/`; giữ toàn bộ log/kết quả (log là bằng chứng đo) |

Ghi chú lệnh README: `01_Trung/scripts/eval_router.py` mặc định ghi ra `results/router_eval.json` với nhãn `router_v0_rule` dù đang chạy router hiện tại (v1) – không ảnh hưởng số, nhưng khi tái lập nên truyền `--out results/router_eval_v1.json --label router_v1_rule`.

## 4. Tổng hợp folder
- Giữ nguyên 5 folder thành viên + `00_Chung/` (đã sửa như mục 2).
- Thêm ở gốc: `README.md` (cửa vào), `BAO_CAO_TONG_HOP.md` + `BAO_CAO_TONG_HOP.docx` (xuất bằng pandoc 3.1.3, có mục lục; kiểm `zipfile.testzip()` = None và pandoc đọc ngược ra text được), file này.
- Thêm `00_Chung/kiem_dinh/` (`check_numbers.py`, `doi_chieu_so_lieu.md`).
- Giữ `TONG_HOP_TAC_NHAN_1.md`, `CHANGELOG_TAC_NHAN_2.md` làm lịch sử (thêm 1 ghi chú ở đầu bảng của Tác nhân 1).

## 5. Rủi ro còn lại (không sửa được bằng tài liệu)
1. **Không có số nào do người thật duyệt/chấm**: eval_qa, eval_router, eval_visual, kiểm taxonomy, tóm tắt review, faithfulness – đều do LLM hoặc tác nhân AI. Thầy hỏi "ai gán nhãn?" thì câu trả lời hiện là "tác nhân AI".
2. **Visual 100 % là truy vấn tổng hợp trên ảnh 60×80**; thứ hạng DINOv2-S / SigLIP / FashionCLIP chênh ≤ 1,7 điểm, có thể đảo khi có ảnh ngoài đời.
3. **Hệ thống chưa ghép end-to-end**: TSR toàn hệ thống, tỉ lệ chuyển Gemini trên lưu lượng thật, chi phí tiền/100 lượt – CHƯA ĐO; API còn dùng CLIP B/32 + τ_v 0,25.
4. Latency Gemini (14–16 s p50) gồm thời gian chờ quota; quota free tier 20 request/ngày/model không đủ cho demo.
5. Các ô `[cần xác minh]` còn lại: license Fashion Product Images, mã arXiv/venue ViMRHP, đơn giá Gemini, một số trích dẫn ở US_21 – Tác nhân 3 không truy cập mạng để xác minh.
6. Tên model `gemini-3.5-flash(-lite)`, `gemma-4-26b-a4b-it` lấy từ log API thật của lượt chạy; cần kiểm lại tên trước demo (R11).
7. 13 quyết định trong `QUYET_DINH_CAN_CHOT.md` vẫn ở trạng thái **đề xuất**; 3 thay đổi code của Tác nhân 2 cho mục D (`source="fallback"`) cần hoàn tác nếu nhóm chọn phương án khác.
