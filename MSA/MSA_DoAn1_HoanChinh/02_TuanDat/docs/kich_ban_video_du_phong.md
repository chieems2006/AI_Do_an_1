# Kịch bản video demo dự phòng (US_28 / US_47) – demo_script

| Mục | Nội dung |
|---|---|
| Mã US | US_28 (demo_script.md), hỗ trợ US_47 (video dự phòng) |
| Mục tiêu | Video 4–5 phút chạy đủ 5 luồng, dùng khi demo trực tiếp lỗi mạng/quota |
| Đầu ra | Kịch bản này + video `.mp4` (quay N20, 24/11) |
| Tiêu chí | Mỗi luồng hiện rõ nhãn nguồn; mọi con số nói trong video có trong báo cáo cuối |
| Trạng thái | **Khung sẵn** – quay khi hệ thống tích hợp xong |

Chuẩn bị: chạy API + `python app/app.py`; trình duyệt 1280×720, zoom 110%; tắt thông báo; đổ sẵn cache Gemini cho câu C1, C2
(vì free tier chỉ 20 request/ngày/model – đo thật); ghi màn hình bằng OBS 30 fps.

| # | Thời lượng | Màn hình / thao tác | Lời thoại (gợi ý) |
|---|---|---|---|
| 0 | 0:00–0:20 | Slide tiêu đề + sơ đồ kiến trúc (Trung) | "Trợ lý mua sắm thời trang: tìm bằng ảnh, hỏi đáp tiếng Việt, tìm – so sánh, trò chuyện có Gemini dự phòng." |
| 1 | 0:20–1:10 | Kéo ảnh studio một đôi sneaker từ catalog → 6 card | "Ảnh studio: top-1 đúng sản phẩm. Card có ảnh, tên, giá (catalog FPI chưa có giá nên ghi 'Chưa có giá'), độ tương đồng, link nguồn." |
| 2 | 1:10–1:50 | Kéo ảnh tự chụp (US_11) | "Ảnh ngoài đời khó hơn – Recall@5 ngoài đời là … (Bảng A2)." – chỉ nói số khi đã đo |
| 3 | 1:50–2:30 | Gõ "tìm giày sneaker trắng nam" | "Tìm bằng chữ có bộ lọc màu/giới tính." |
| 4 | 2:30–3:10 | Gõ "so sánh fpi_… fpi_… fpi_…" → bảng | "So sánh 3 sản phẩm; ô thiếu dữ liệu ghi rõ 'Chưa có thông tin', không bịa." |
| 5 | 3:10–3:50 | Gõ "shopee_25814055660 quần có co giãn không?" | "Trả lời từ review thật, có trích nguồn, nhãn 'Từ dữ liệu cửa hàng'." |
| 6 | 3:50–4:10 | Gõ câu không có dữ kiện: "shopee_23261536758 gọng kính titan hay nhựa?" | "Thiếu dữ kiện thì từ chối – Gemini không bù." |
| 7 | 4:10–4:40 | C1 "chào shop" → C2 "mai trời có mưa không?" | "Chitchat và câu ngoài phạm vi chuyển Gemini – nhãn 'Trả lời bởi Gemini'." |
| 8 | 4:40–5:00 | Slide bảng chi phí/100 lượt + tỉ lệ chuyển Gemini | Đọc số từ `results/bench_llm_summary.json` |

Kế hoạch B khi quay: nếu Gemini 429 → dùng câu đã cache (nhãn "bộ nhớ đệm"); nếu API sập → UI tự chuyển mock (có dòng chú thích) – **không** cắt ghép che lỗi, nói rõ trong video.
