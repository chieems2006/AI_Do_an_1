# Tổng hợp của Tác nhân 1 (chuyên gia thiết kế AI)

Nguồn kế hoạch: `MSA_PLAN_v2.xlsx` (51 user story, 199 point). Tác nhân 1 đã:
1. Trích phần việc từng người (sheet Backlog, Phân công, Lịch theo ngày) → `00_Chung/trich_ke_hoach/`.
2. Ban hành thiết kế chung (schema, định dạng response, tên module, quy tắc Gemini, quy tắc số liệu) → `00_Chung/00_THIET_KE_CHUNG.md`.
3. Chuẩn bị dữ liệu thật dùng chung (Fashion Product Images 4.593 SP + ViMRHP Fashion 509 SP / 11.009 review tiếng Việt) → `00_Chung/prep_shared_data.py`, `00_Chung/stats.json`.
4. Giao việc cho 5 tác nhân thành viên → `00_Chung/giao_viec/`, và gom kết quả thành 5 folder dưới đây.

> Ghi chú Tác nhân 3: bảng dưới là **ảnh chụp lúc Tác nhân 1 gom kết quả** (giữ nguyên để truy vết). Số pytest cuối cùng và số liệu đã kiểm định: `KIEM_DINH_TAC_NHAN_3.md`, `BAO_CAO_TONG_HOP.md`. Adapter 0,921 là trên truy vấn biến đổi tổng hợp; số mũ chuẩn là 285.

| Folder | Thành viên | Vai trò | pytest | Số liệu thật nổi bật (theo báo cáo của thành viên) |
|---|---|---|---|---|
| `01_Trung/` | Trung | Nhóm trưởng, kiến trúc, router, taxonomy | 54 passed | Taxonomy map 168/168 nhãn FPI; schema hợp lệ 4.586/4.586; router 0,878 trên tập độc lập (chưa đạt 0,90); token Gemini/100 lượt ≈ 6.028 (flash-lite) |
| `02_TuanDat/` | Tuấn Đạt | Dữ liệu, benchmark LLM, UI, test | 23 passed | Làm sạch 4.593 → 4.385 SP; benchmark 3 LLM (Flash-Lite, Gemma 4 26B API, Qwen 0.5B); tóm tắt review 428 SP |
| `03_Chien/` | Chiến | Dữ liệu tiếng Việt, RAG, eval QA, prompt Gemini | 51 passed | eval_qa 280 câu, eval_router 78 câu; retrieval hybrid Hit@5 0,866; RAG từ chối đúng 15/15 |
| `04_Khoa/` | Khoa | ML: embedding ảnh, eval visual, cải tiến | 30 passed | Benchmark 5 model ảnh (DINOv2-S, SigLIP, FashionCLIP, CLIP B/32, ResNet-50); adapter R@5 0,829 → 0,921 (cần kiểm trên ảnh thật) |
| `05_Hoang/` | Hoàng | Pipeline, metrics, API, LLM gateway | 78 passed | Data v1 5.021 SP; API /search/image p95 ≈ 1,1 s; compare 370/370 ô khớp; text-embed: TF-IDF thắng neural |

Ghi chú đóng gói: các file nặng tái tạo được (cache embedding `.npy`, FAISS index, ảnh, `.parquet`, cache SQLite) không đưa vào; chạy lại script trong từng folder để sinh lại.
Ràng buộc chung gặp phải: Gemini free tier ~20 request/ngày/model (đã chuyển sang `gemini-3.5-flash-lite`); Tiki chặn IP cloud (dùng ViMRHP); ảnh FPI chỉ 60×80; mũ < 300 SP.
