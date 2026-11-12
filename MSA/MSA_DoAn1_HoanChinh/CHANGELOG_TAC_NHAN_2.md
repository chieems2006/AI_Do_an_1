# CHANGELOG – Tác nhân 2 (chuyên gia AI/ML, giảng viên hướng dẫn) – 05/11/2026

Phạm vi: rà soát kết quả Tác nhân 1, đối chiếu Backlog (DOCS/TEST), làm rõ tài liệu, xử lý mâu thuẫn chéo. **Không gọi Gemini, không benchmark lại model**; mọi số thêm vào đều đọc từ file có sẵn trong folder. `stage1/` không bị sửa.

## Kết quả kiểm tra sau chỉnh sửa
| Folder | `python -m pytest -q` | Ghi chú |
|---|---|---|
| 01_Trung | 53 passed, 1 skipped, 1 deselected | skip: thiếu file nặng `catalog_fpi_taxonomy_v1.parquet` (không đóng gói) |
| 02_TuanDat | 21 passed, 3 skipped | 2 skip: thiếu `catalog_clean.parquet`; 1 skip: test live Gemini |
| 03_Chien | 51 passed, 1 deselected | |
| 04_Khoa | 30 passed | |
| 05_Hoang | 78 passed, 1 deselected | |
`grep -rn "AQ\.Ab8" A2_chinh_sua` → rỗng.

## 00_Chung (dùng chung)
| File | Thay đổi | Lý do |
|---|---|---|
| `QUYET_DINH_CAN_CHOT.md` (mới) | 6 quyết định A–F + 7 mâu thuẫn tự phát hiện G1–G7; mỗi mục: vấn đề, bằng chứng (file), phương án, đề xuất, người chốt, hạn | Yêu cầu mục 3 |
| `THUAT_NGU.md` (mới) | Giải thích Recall@K, Hit@K, macro R@5, MRR, CTE@5, type gate, AUROC, faithfulness, hallucination, abstention, route accuracy, held-out, fallback rate, token/100 lượt, thinking token, τ_v/τ_r/τ_intent – mỗi thuật ngữ có ví dụ bằng số của đồ án; định nghĩa 6 nhãn loại số liệu ([Thật–thật], [Thật–tổng hợp], [LLM chấm], [Tác nhân kiểm], [Chưa người duyệt], CHƯA ĐO) | Người đọc hiểu cùng một nghĩa; tránh định nghĩa lặp ở từng tài liệu |
| `00_THIET_KE_CHUNG.md` | Ghi chú dưới dòng ngưỡng mặc định (τ_v 0,25 bị bỏ, τ_r thực tế 0,0, đề xuất `source="fallback"`); thêm §8 trỏ tới các file mới | τ_v 0,25 đo thật không loại được ảnh ngoài phạm vi nào |

## 01_Trung
| File | Thay đổi | Lý do |
|---|---|---|
| `README.md` | Thêm §0 bảng đối chiếu 12 US (Đạt 3 / Một phần 6 / Chưa đạt 3) với bằng chứng; sửa số pytest bản A2; cập nhật dòng US_25 và ghi chú mũ | Yêu cầu mục 1 |
| `scripts/run_scoring_from_khoa.py` | Viết lại: đọc `../04_Khoa/results/bench_image_embed.csv` (đường dẫn tương đối, `--csv`), ánh xạ cột (ghi trong docstring), sửa khoá `dinov2_small`→`dinov2_s`, thêm kiểm tra độ nhạy ±0,05 và kịch bản B (tiêu chí tầng category) | Yêu cầu mục 3e: chạy Bảng F trên số thật của Khoa |
| `results/weighted_scoring.{md,json}`, `weighted_scoring_sensitivity.json`, `weighted_scoring_scenario_B.json`, `bench_image_embed_from_khoa.csv` | Sinh lại / mới: **DINOv2-S 4,83 > SigLIP 3,98 > FashionCLIP 3,96 > CLIP B/32 2,99 > ResNet-50 2,40**; hạng 1 giữ ở 12/12 cấu hình | Bảng xếp hạng thật |
| `docs/US_25_bang_cham_diem_co_trong_so.md` | Viết lại: tóm tắt 5 dòng, ví dụ tính min-max, bảng đầu vào 5 model, Bảng F thật, độ nhạy, bằng chứng độ bền, kết luận; trạng thái → Đạt | Trước đây "chưa xếp hạng được" |
| `docs/US_27_bao_cao_tuan2_khung.md` | Viết lại thành nội dung báo cáo trả lời đủ 3 yêu cầu của thầy, mỗi kết luận có bảng số + file nguồn + nhãn loại số liệu | Bản cũ chỉ là dàn ý, số đã cũ |
| `docs/US_18_chot_do_do_va_nguong.md` | Thêm tóm tắt 5 dòng; cập nhật 10 dòng bảng ngưỡng theo số mới nhất (5 model visual, Hybrid RAG test 0,895, faithfulness/hallucination/abstention của Chiến và Đạt, TSR visual 0,833, token/100 lượt 2 prompt) | Baseline cũ chỉ có CLIP B/32 và ghi "CHƯA ĐO" cho số đã đo |
| `docs/US_26_bao_cao_tuan1_khung.md` | Mũ 286 → 285 (số chuẩn) + giải thích; ghi chú catalog sau làm sạch 4.385 | Mâu thuẫn A |
| `docs/US_40_architecture.md` | Sơ đồ: τ_v theo model, τ_r 0,0; luật Gemini lỗi → `source=fallback`; bảng ngưỡng; mũ 285 | Mâu thuẫn C, D |
| `docs/openapi_contract.yaml` | Enum `source` thêm `fallback` (kèm mô tả, chờ Trung chốt) | Mâu thuẫn D |
| `docs/US_49_taxonomy.md` | Tóm tắt 5 dòng (gồm 7 nhãn mũ sai Tác nhân 2 phát hiện) | Yêu cầu mục 2 |
| `src/msa/agent/router.py`, `tests/test_router.py` | 2 thông điệp hệ thống đổi `source="internal"` → `"fallback"`; sửa 1 assert | UI đang hiện nhầm "Từ dữ liệu cửa hàng" cho thông báo lỗi |

## 02_TuanDat
| File | Thay đổi | Lý do |
|---|---|---|
| `README.md` | §0 bảng đối chiếu 10 US (Đạt 3 / Một phần 5 / Chưa đạt 2); ghi số pytest bản A2 và lý do skip | Yêu cầu mục 1 |
| `app/components.py`, `tests/test_components_app.py` | Nhận `source="fallback"`, nhãn mới "Thông báo hệ thống"; thêm 1 assert | Mâu thuẫn D – trước đây gateway của Hoàng trả `fallback` thì UI báo không hợp lệ và gắn nhãn cửa hàng |
| `docs/US_04`, `US_08`, `US_10`, `US_24` | Thêm "Tóm tắt 5 dòng" (nêu rõ loại số liệu, số chuẩn mũ 285, 3 boot gán sai) | Yêu cầu mục 2 |

## 03_Chien
| File | Thay đổi | Lý do |
|---|---|---|
| `README.md` | §0 bảng đối chiếu 9 US (Đạt 5 / Một phần 4); thêm số split test (n=114) cạnh bảng retrieval; đường dẫn tương đối | Yêu cầu mục 1 |
| `eval/ngoai_pham_vi_taxonomy_v1.csv` (mới) | 45 câu eval_qa + 4 câu eval_router thuộc SP ngoài phạm vi, kèm đề xuất xử lý; **không sửa file eval gốc** | Mâu thuẫn B |
| `docs/US_13`, `US_14`, `US_16`, `US_20`, `US_51` | Thêm "Tóm tắt 5 dòng" | Yêu cầu mục 2 |

## 04_Khoa
| File | Thay đổi | Lý do |
|---|---|---|
| `README.md` | §0 bảng đối chiếu 9 US (Đạt 6 / Một phần 3); ghi chú kết luận FashionCLIP trái Bảng F; đường dẫn tương đối | Yêu cầu mục 1, mâu thuẫn E |
| `src/scripts/recall_by_transform.py`, `results/recall_by_transform.csv` (mới) | Tách R@5 test theo họ biến đổi từ `results/per_query/*.csv` có sẵn (không chạy model) | Bằng chứng độ bền cho quyết định E (đổi nền: SigLIP 0,906 / DINOv2-S 0,812 / FashionCLIP 0,656) |
| `docs/US_09_eda/eda_report.md`, `US_12`, `US_15`, `US_19`, `US_22` | Thêm "Tóm tắt 5 dòng" | Yêu cầu mục 2 |

## 05_Hoang
| File | Thay đổi | Lý do |
|---|---|---|
| `README.md` | §0 bảng đối chiếu 11 US (Đạt 7 / Một phần 4); nêu API dùng CLIP B/32 + τ_v 0,25 cần đổi; đường dẫn tương đối | Yêu cầu mục 1, mâu thuẫn C, G4 |
| `docs/US_06_US_48_du_lieu_public.md`, `US_23`, `US_50` | Thêm "Tóm tắt 5 dòng" (giải thích mũ 298, token/100 lời gọi vs /100 lượt) | Yêu cầu mục 2, mâu thuẫn A, F |

## Việc còn tồn (cần người thật / nhóm chốt)
1. Ký chốt các mục A–G trong `00_Chung/QUYET_DINH_CAN_CHOT.md` (đặc biệt E – đổi model chính, cần build lại index DINOv2-S và đo lại cải tiến).
2. Áp quyết định A vào code: thêm 2 luật tiêu đề mũ vào `msa.data.taxonomy.map_fpi`, chạy lại `build_category_map.py` / `03_clean.py` (chưa làm vì sinh file nặng).
3. Áp quyết định B: eval_router/eval_qa v1.1, chạy lại `eval_router.py` và retrieval.
4. 2 người duyệt ≥ 30 % eval_qa/eval_router; người chấm 50 câu RAG; 80–100 ảnh ngoài đời (US_11).
5. Xuất `report_week1/2.docx` + slide từ US_26/US_27.
6. Các tài liệu phụ chưa thêm "Tóm tắt 5 dòng" (biên bản, test plan, kịch bản demo, API, schema, kiến trúc) – không thuộc 3 yêu cầu của thầy.
