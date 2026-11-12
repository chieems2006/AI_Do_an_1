# US_01 – Project Charter (1 trang)

| Mục | Nội dung |
|---|---|
| Mã US | US_01 (Owner: Trung, Support: All) |
| Mục tiêu | Cả nhóm hiểu cùng mục tiêu, phạm vi, vai trò, mốc |
| Đầu ra | Charter 1 trang (file này) |
| Tiêu chí nghiệm thu | Mỗi thành viên nói lại được mục tiêu, phạm vi và vai trò của mình trong 2 phút |
| Trạng thái | **Bản nháp hoàn chỉnh** – chờ họp kickoff N1 (05/11) để từng người nói lại (chưa nghiệm thu) |

**Tên dự án:** MSA – AI Agent trợ lý mua sắm thời trang đa phương thức (Đồ án 1). **Thời gian:** 05/11 – 25/11/2026 (21 ngày).

**Mục tiêu sản phẩm:** một khung chat tiếng Việt xử lý 5 luồng: (1) tìm SP bằng ảnh (CLIP + FAISS), (2) hỏi đáp về SP (RAG trên mô tả/review), (3) tìm bằng văn bản có bộ lọc, (4) so sánh 2–3 SP cùng nhóm, (5) trò chuyện/ngoài phạm vi/câu khó → **Gemini fallback** có cache và nhãn nguồn. Nguyên tắc: **không bịa** giá/size/tồn kho; dữ liệu cửa hàng luôn ưu tiên; Gemini chỉ nhận text.

**Điều kiện thành công:** số liệu benchmark thật cho từng quyết định; demo chạy ổn định 5 luồng bằng 1 lệnh; bảng tỉ lệ chuyển Gemini + token/chi phí trên 100 lượt; bảng trước/sau cải tiến.

| Phạm vi LÀM | KHÔNG LÀM (để Đồ án 2/3) |
|---|---|
| 4 nhóm: giày dép, quần áo, mũ, phụ kiện (túi, thắt lưng, kính) – cây taxonomy v1 | Đồng hồ, trang sức, tất, ví, khăn, đồ lót, mỹ phẩm |
| Khảo sát dữ liệu, độ đo, phiên bản model có số liệu (3 yêu cầu của thầy) | Website TMĐT, widget, đăng nhập/giỏ hàng |
| Demo local (Gradio/Streamlit) + FastAPI, log JSON | DWH, dashboard, chống prompt injection nâng cao |
| Gemini mức fallback + cache + nhãn nguồn + hậu kiểm | Fine-tune lớn, GPU |

| Thành viên | Vai trò | Chịu trách nhiệm chính |
|---|---|---|
| Trung | Nhóm trưởng/PM, kiến trúc Agent | Charter, schema, taxonomy, độ đo & ngưỡng, chấm điểm chọn model, báo cáo T1/T2, router/agent, demo |
| Tuấn Đạt | Dữ liệu, LLM benchmark, UI, test | Bảng phương pháp/nguồn, làm sạch, benchmark LLM, UI demo, kiểm thử, báo cáo cuối |
| Chiến | Dữ liệu tiếng Việt, RAG | Review VN, eval_qa, eval_router, RAG, prompt Gemini fallback |
| Khoa | ML ảnh | EDA, eval_visual, benchmark embedding ảnh, type gate, cải tiến visual |
| Hoàng | Python backend | Repo, pipeline, metrics.py, FastAPI, LLM gateway + cache |

| Mốc | Ngày | Bàn giao |
|---|---|---|
| Tuần 1 – Dữ liệu | 05–11/11 | Data v1, báo cáo Tuần 1, schema + taxonomy |
| Tuần 2 – Độ đo & khảo sát | 12–18/11 | eval sets, metrics.py, benchmark, Bảng F, báo cáo + slide Tuần 2, architecture.md |
| Tuần 3 – Demo & cải tiến | 19–25/11 | Router + 4 công cụ, baseline e2e, ≥ 4 cải tiến đo trước/sau, feature freeze N19 17:00, diễn tập, tag v1.0 |

**Rủi ro lớn đã thấy (số thật):** quota Gemini free tier 20 request/ngày/model dùng chung 5 người; ảnh catalog 60×80; mũ 286 < 300; không có giá/size. Cắt scope theo sheet Rủi ro mục C (US_42, US_39 cắt đầu tiên).
