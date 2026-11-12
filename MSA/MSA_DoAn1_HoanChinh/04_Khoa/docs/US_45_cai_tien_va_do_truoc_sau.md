# US_45 – Cải tiến Visual Search & đo trước/sau (phần visual của Sheet `7_Cải tiến T3`)

| Mục | Nội dung |
|---|---|
| Mã US | US_45 (Owner: Khoa, Support: All) – Sprint 3, 8.0 pt |
| Mục tiêu | Cải tiến có số baseline và số sau trên CÙNG bộ test; chỉ giữ khi cải thiện rõ |
| Đầu ra | `src/msa/search/improvements.py` (I1 crop, I2 TTA, I3 adapter), type gate I19 trong `src/msa/search/visual.py`, `src/scripts/run_improvements.py`, `results/improvements_<model>.{csv,json}`, `results/adapters/<model>_linear_adapter.npz`, file này |
| Tiêu chí nghiệm thu | ≥ 4 cải tiến High, trong đó ≥ 1 nhóm Gemini (I15/I16) và ≥ 1 đa domain (I19); mỗi cải tiến có Trước/Sau |
| Trạng thái | **Phần visual (I1, I2, I3, I19) đo THẬT** trên eval_visual split test (mục 2). Cải tiến nhóm Gemini (I15 cache – Hoàng, I16 prompt – Chiến) và TSR end-to-end: **CHƯA ĐO ở đây** – thuộc owner khác / cần hệ thống ghép (US_44). |

## 1. Phương pháp
- Bộ đo: `eval/eval_visual.csv`, **split test** (240 truy vấn instance + 120 category). Siêu tham số (τ của gate, λ của adapter) **chỉ chọn trên split val**.
- **Baseline** = model + FAISS Flat, không cải tiến.
- **I1 crop** (`bbox_crop`): cắt theo bounding box pixel không-trắng (ngưỡng 240) + lề 6 %, fallback center-crop. Không dùng rembg/YOLO ở lượt này (máy 2 CPU dùng chung). Mặc định đo biến thể **chỉ crop truy vấn** (rẻ); biến thể crop cả catalog chạy bằng `--with-crop` (tốn 1 lượt embed lại catalog).
- **I2 TTA**: embedding truy vấn = chuẩn hoá(emb(ảnh) + emb(ảnh lật ngang)). Latency truy vấn ×2.
- **I3 adapter tuyến tính**: \(W=\arg\min\|AW-B\|^2+\lambda\|W-I\|^2\) (nghiệm đóng), A = embedding của 800 ảnh biến đổi (seed 7) từ **800 SP không xuất hiện trong eval_visual**, B = embedding ảnh gốc của chính SP đó. Áp W lên embedding truy vấn. λ ∈ {0,1; 0,3; 1; 3; 10} chọn trên val theo R@5 + cat P@5.
- **I19 type gate**: 3 biến thể dự đoán product_type của ảnh truy vấn – zero-shot prompt văn bản (model có text tower), nearest-centroid, logistic regression trên embedding catalog (loại SP trong eval); nếu xác suất ≥ τ (chọn trên val trong {0; 0,5; 0,7; 0,9}) thì chỉ tìm trong nhóm đó.

## 2. Kết quả (đo thật)

<!-- IMPR_RESULTS -->

**Model: `fashionclip`** – split test

| Biến thể | R@1 | R@5 | MRR@10 | Macro R@5 | CTE@5 | R@5 hard | cat Hit@5 | cat P@5 | ΔR@5 | ΔMacro R@5 | ΔMRR | Δcat P@5 | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.704 | 0.829 | 0.757 | 0.829 | 0.062 | 0.981 | 0.767 | 0.378 | +0.000 | +0.000 | +0.000 | +0.000 |  |
| I2_tta_hflip | 0.696 | 0.838 | 0.754 | 0.838 | 0.060 | 0.981 | 0.758 | 0.370 | +0.008 | +0.008 | -0.002 | -0.008 |  |
| I3_linear_adapter | 0.838 | 0.921 | 0.872 | 0.921 | 0.026 | 0.962 | 0.750 | 0.378 | +0.092 | +0.092 | +0.115 | +0.000 | lambda_chosen_on_val=3.0 |
| I1_bbox_crop_query_only | 0.708 | 0.825 | 0.758 | 0.825 | 0.065 | 0.981 | 0.758 | 0.357 | -0.004 | -0.004 | +0.002 | -0.022 |  |
| I19_type_gate_zeroshot | 0.704 | 0.821 | 0.754 | 0.821 | 0.044 | 0.943 | 0.767 | 0.378 | -0.008 | -0.008 | -0.002 | +0.000 | tau_chosen_on_val=0.9, gate_acc_test=0.9556 |
| I19_type_gate_centroid | 0.704 | 0.821 | 0.753 | 0.821 | 0.058 | 0.943 | 0.767 | 0.378 | -0.008 | -0.008 | -0.003 | +0.000 | tau_chosen_on_val=0.9, gate_acc_test=0.9167 |
| I19_type_gate_logreg | 0.704 | 0.821 | 0.753 | 0.821 | 0.053 | 0.943 | 0.767 | 0.378 | -0.008 | -0.008 | -0.004 | +0.000 | tau_chosen_on_val=0.7, gate_acc_test=0.9611 |
| I2+I3 | 0.838 | 0.917 | 0.872 | 0.917 | 0.026 | 0.962 | 0.758 | 0.372 | +0.087 | +0.087 | +0.115 | -0.007 |  |
<!-- /IMPR_RESULTS -->

## 3. Quyết định

Model áp dụng: **FashionCLIP** (model Khoa chọn tạm ở US_22; Bảng F đề xuất DINOv2-S – cải tiến phải đo lại nếu đổi model, `00_Chung/QUYET_DINH_CAN_CHOT.md` mục E). Mọi số ở đây là **[Thật–tổng hợp]**. Quy tắc: chỉ giữ khi cải thiện rõ (≥ +2 điểm R@5 hoặc giảm rõ CTE@5 mà không làm giảm R@5) trên split test.

| ID | Cải tiến | Trước → Sau (R@5 test) | Tác động khác | Quyết định | Lý do |
|---|---|---|---|---|---|
| I3 | Adapter tuyến tính (λ = 3 chọn trên val) | 0,829 → **0,921** (+0,092) | MRR 0,757 → 0,872; CTE@5 0,062 → 0,026; R@5 mọi nhóm tăng (giày 0,733 → 0,900); cat P@5 giữ 0,378; cat Hit@5 0,767 → 0,750; R@5 hard 0,981 → 0,962 | **GIỮ CÓ ĐIỀU KIỆN** (mặc định TẮT) | Tăng lớn nhất **trên truy vấn biến đổi tổng hợp** – chưa phải bằng chứng cải thiện thật. **Cảnh báo**: adapter học trên CÙNG họ biến đổi tổng hợp với truy vấn test (khác SP, khác seed) nên có thể chỉ học "gỡ" các biến đổi đó; bắt buộc kiểm lại trên ảnh ngoài đời trước khi bật mặc định trong demo |
| I2 | TTA lật ngang | 0,829 → 0,838 (+0,008 ≈ 2/240 truy vấn) | cat P@5 −0,008; latency embed ×2 | **BỎ** | Không cải thiện rõ, tốn gấp đôi thời gian embed |
| I1 | Crop theo nền trắng (chỉ phía truy vấn) | 0,829 → 0,825 (−0,004) | cat P@5 −0,022 | **BỎ** (biến thể này) | Ảnh FPI vốn đã sát nền trắng; truy vấn `background`/`combo` có nền không trắng nên crop theo ngưỡng không tách được. Biến thể crop cả catalog và crop bằng rembg/YOLO: CHƯA ĐO |
| I19 | Type gate lọc cứng (zero-shot, τ = 0,9) | 0,829 → 0,821 (−0,008) | **CTE@5 0,0617 → 0,0442 (−28 % tương đối)**; gate đúng 95,6 % truy vấn test; cat CTE@5 0,002 → 0,000 | **GIỮ dạng mềm** (dạng mềm CHƯA ĐO) | Giảm rõ lỗi sai nhóm nhưng lọc cứng làm R@5 giảm nên **không thoả** quy tắc "giảm CTE mà không giảm R@5"; lọc cứng làm mất vài kết quả đúng khi gate sai → dùng gate để *hỏi lại* ("bạn muốn tìm giày, áo hay mũ?") khi conf thấp và để *ưu tiên* nhóm, không lọc cứng mặc định. Biến thể centroid (91,7 %) và logistic regression (96,1 %) cho R@5 như nhau |
| I2+I3 | TTA + adapter | 0,829 → 0,917 | – | BỎ (giữ I3 riêng) | Không hơn I3 đơn lẻ |

Kết quả tương tự đã thấy ở CLIP B/32 cho I19 (R@5 0,721 → 0,717, CTE@5 0,076 → 0,068) và DINOv2 (gate centroid làm R@5 giảm 0,846 → 0,796) – xem `docs/US_22_benchmark_embedding.md`.

## 4. Việc còn lại
1. Đo lại I1/I2/I3/I19 trên **ảnh ngoài đời** (khi nhóm chụp xong) – đây mới là nơi I1/I19 được kỳ vọng có tác dụng lớn.
2. Ghép số I15 (Hoàng) và I16 (Chiến) vào Sheet 7 để đủ điều kiện "≥ 1 cải tiến nhóm Gemini".
3. Chạy `--with-crop` (crop cả catalog) khi máy rảnh.
