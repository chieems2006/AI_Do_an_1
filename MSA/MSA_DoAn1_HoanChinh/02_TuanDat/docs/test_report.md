# Test report – US_46 (MẪU – điền khi chạy N19, 23/11/2026)

| Mục | Nội dung |
|---|---|
| Mã US | US_46 |
| Phiên bản hệ thống | `git rev-parse --short HEAD` = ……… ; model ảnh: ……… ; LLM RAG: ……… ; Gemini model: ……… |
| Người chạy | ……… |
| Trạng thái | **Chưa chạy** (chờ hệ thống tích hợp) – chỉ có kết quả test tự động bên dưới |

## 1. Kết quả theo kịch bản (`docs/US_46_test_plan.md`)

| ID | Ngày giờ | Route thực tế | Source | Latency (ms) | Kết quả (Pass/Fail) | Bug ID | Ghi chú |
|---|---|---|---|---|---|---|---|
| T01 | | | | | | | |
| T02 | | | | | | | |
| … | | | | | | | |
| T20 | | | | | | | |

## 2. Danh sách bug

| Bug ID | Kịch bản | Mức | Mô tả | Cách tái hiện | Người sửa | Trạng thái | Commit sửa |
|---|---|---|---|---|---|---|---|
| B01 | | | | | | Mở | |

## 3. Tổng hợp
| Mức | Số bug mở | Số bug đã sửa |
|---|---|---|
| Nghiêm trọng | | |
| Cao | | |
| TB | | |
| Thấp | | |

Kết luận feature freeze: ……… (đạt khi Nghiêm trọng = 0).

## 4. Kết quả test tự động hiện có (đo thật 05/11/2026, folder 02_TuanDat)
| Kịch bản | Test | Kết quả |
|---|---|---|
| T15 Gemini 429 | `tests/test_bench_reviews_vq.py::test_gemini_client_429_circuit` | Pass – 3 lần 429 thì ngắt mạch, lần 4–5 không gọi mạng |
| T16 Gemini timeout | `::test_gemini_client_timeout` | Pass – trả `error=network:Timeout`, không ném ngoại lệ |
| T17 nhãn cache | `tests/test_components_app.py::test_labels` | Pass |
| T20 API sập | `::test_backend_falls_back_when_api_down` | Pass – UI tự chuyển mock |
| 4 luồng UI (mock) | `::test_four_flows_mock_backend` | Pass – ảnh / tìm / so sánh / hỏi đáp + chat |
| UI khởi động | `MSA_UI_SMOKE=1 MSA_UI_MOCK=1 python app/app.py` | HTTP 200 (Gradio 6.31.0) |
