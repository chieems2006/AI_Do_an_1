# US_47 – Kịch bản demo + diễn tập + video dự phòng + tag release

| Mục | Nội dung |
|---|---|
| Mã US | US_47 (Owner: Trung, Support: All) |
| Mục tiêu | Chạy trọn kịch bản demo 2 lần liên tiếp không lỗi; có video dự phòng; gắn `git tag v1.0` |
| Đầu ra | `demo_script.md` (file này), video, tag |
| Tiêu chí nghiệm thu | Chạy trọn kịch bản 2 lần liên tiếp không lỗi |
| Trạng thái | **Kịch bản sẵn** (dùng SP thật); **CHƯA diễn tập** – cần app hoàn chỉnh (N20–N21) |

## 1. Chuẩn bị (T-30 phút)
1. `cp .env.example .env`, điền `GEMINI_API_KEY` (không chiếu màn hình file .env); `GEMINI_MODEL` đã xác minh còn chạy (R11).
2. **Làm nóng cache Gemini** cho các câu chitchat của kịch bản (I15) – vì free tier chỉ 20 request/ngày/model và latency đo được p50 ≈ 14 s khi dùng chung quota.
3. Chạy `python -m pytest -q`; mở app bằng 1 lệnh; mở sẵn video dự phòng.
4. Kiểm `logs/requests.jsonl` ghi được.

## 2. Năm kịch bản (khoảng 7 phút)
| # | Luồng | Thao tác (câu nhập) | Kỳ vọng hiển thị | Dữ liệu thật dùng |
|---|---|---|---|---|
| 1 | Ảnh | Tải ảnh một đôi slip-on đen | `route=visual`; top-5 giày, có `fpi_21744` Vans Classic Slip-On; nhãn "Từ dữ liệu cửa hàng" | ảnh `fpi_images/21744.jpg` (hoặc ảnh tự chụp) |
| 2 | Tìm + lọc | "tìm mũ lưỡi trai màu đen" | `route=search`; card mũ `cap`; ghi rõ "chưa có giá" | FPI headwear/cap |
| 3 | Đa lượt + so sánh | (sau #1) "so sánh đôi vừa tìm với đôi thứ 2" | `route=compare`; bảng thuộc tính từ DB (loại, màu, giới tính, mục đích) | session `last_results` |
| 4 | Hỏi đáp review VN | Mở SP `shopee_22736671626` "Dép YZ Slide Vân Nhám" → "dép này đi có êm không?" rồi "giá bao nhiêu?" | Câu 1 trả lời có trích review; câu 2 "chưa có thông tin giá" (Gemini không bù) | ViMRHP review |
| 5 | Trò chuyện / ngoài phạm vi / mơ hồ | "chào shop" → "đôi thứ 2" (phiên mới) → "đôi thứ 2" → "đồng hồ casio nào đẹp" | chitchat có nhãn **"Trả lời bởi Gemini"**; mơ hồ → hỏi lại 1 lần rồi Gemini; đồng hồ: không khẳng định cửa hàng có bán (hậu kiểm `danh_muc`) | – |

Kịch bản lỗi (nói nếu bị hỏi): ngắt mạng/429 → câu dự phòng "phần trò chuyện đang bận…", `source=internal`, app không sập.

## 3. Nhật ký diễn tập
| Lần | Ngày | Kịch bản 1 | 2 | 3 | 4 | 5 | Lỗi | Sửa |
|---|---|---|---|---|---|---|---|---|
| 1 | N21 | | | | | | | |
| 2 | N21 | | | | | | | |

## 4. Video dự phòng & release
- Quay màn hình 5 kịch bản (≤ 8 phút), không lộ key/`.env`; lưu Drive nhóm.
- Sau 2 lần chạy liên tiếp không lỗi: `git tag -a v1.0 -m "Đồ án 1 – demo"`; ghi data version + model + τ trong release note.
