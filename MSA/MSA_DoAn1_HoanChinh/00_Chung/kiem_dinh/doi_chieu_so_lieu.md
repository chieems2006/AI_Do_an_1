# Đối chiếu số liệu – tài liệu ↔ file kết quả (sinh tự động)

Sinh bởi `python 00_Chung/kiem_dinh/check_numbers.py` (Tác nhân 3). **Không sửa tay** – sửa tài liệu rồi chạy lại.
Cột *Số trong tài liệu* là chuỗi tìm thấy trong các tài liệu ở cột kế; *Giá trị trong file* đọc trực tiếp từ file nguồn
(một số dòng là phép tính từ file, ghi trong mô tả). KHỚP = chênh ≤ dung sai làm tròn của số đã viết.

**Tổng: 224 khẳng định · KHỚP 224 · LỆCH 0 · lỗi đọc 0 · khớp nhưng thiếu chuỗi ở ≥ 1 tài liệu 0.**

| Mã | Nội dung | Số trong tài liệu | Tài liệu chứa số | File nguồn | Giá trị trong file | Kết quả |
|---|---|---|---|---|---|---|
| A-dinov2_s-macroR5 | dinov2_s macro R@5 (test) | 0.846 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.8458 | KHỚP |
| A-dinov2_s-R1 | dinov2_s R@1 | 0.750 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.75 | KHỚP |
| A-dinov2_s-MRR | dinov2_s MRR@10 | 0.791 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.7909 | KHỚP |
| A-dinov2_s-CTE | dinov2_s CTE@5 | 0.043 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.0425 | KHỚP |
| A-dinov2_s-catP5 | dinov2_s cat P@5 | 0.307 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.3067 | KHỚP |
| A-dinov2_s-emb | dinov2_s embed truy vấn median (ms) | 288.75 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 288.75 | KHỚP |
| A-dinov2_s-peak | dinov2_s RAM đỉnh (MB) | 1.446 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 04_Khoa/results/bench_image_embed.csv | 1445.9 | KHỚP |
| A-siglip_b16-macroR5 | siglip_b16 macro R@5 (test) | 0.833 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.8333 | KHỚP |
| A-siglip_b16-R1 | siglip_b16 R@1 | 0.704 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.7042 | KHỚP |
| A-siglip_b16-MRR | siglip_b16 MRR@10 | 0.760 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.7602 | KHỚP |
| A-siglip_b16-CTE | siglip_b16 CTE@5 | 0.055 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.055 | KHỚP |
| A-siglip_b16-catP5 | siglip_b16 cat P@5 | 0.355 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.355 | KHỚP |
| A-siglip_b16-emb | siglip_b16 embed truy vấn median (ms) | 189.99 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 189.99 | KHỚP |
| A-siglip_b16-peak | siglip_b16 RAM đỉnh (MB) | 2.431 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 04_Khoa/results/bench_image_embed.csv | 2431.4 | KHỚP |
| A-fashionclip-macroR5 | fashionclip macro R@5 (test) | 0.829 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.8292 | KHỚP |
| A-fashionclip-R1 | fashionclip R@1 | 0.704 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.7042 | KHỚP |
| A-fashionclip-MRR | fashionclip MRR@10 | 0.757 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.7566 | KHỚP |
| A-fashionclip-CTE | fashionclip CTE@5 | 0.062 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.0617 | KHỚP |
| A-fashionclip-catP5 | fashionclip cat P@5 | 0.378 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.3783 | KHỚP |
| A-fashionclip-emb | fashionclip embed truy vấn median (ms) | 294.22 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 294.22 | KHỚP |
| A-fashionclip-peak | fashionclip RAM đỉnh (MB) | 1.597 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 04_Khoa/results/bench_image_embed.csv | 1596.6 | KHỚP |
| A-clip_b32-macroR5 | clip_b32 macro R@5 (test) | 0.721 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.7208 | KHỚP |
| A-clip_b32-R1 | clip_b32 R@1 | 0.621 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.6208 | KHỚP |
| A-clip_b32-MRR | clip_b32 MRR@10 | 0.660 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.6599 | KHỚP |
| A-clip_b32-CTE | clip_b32 CTE@5 | 0.076 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.0758 | KHỚP |
| A-clip_b32-catP5 | clip_b32 cat P@5 | 0.353 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.3533 | KHỚP |
| A-clip_b32-emb | clip_b32 embed truy vấn median (ms) | 428.34 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 428.34 | KHỚP |
| A-clip_b32-peak | clip_b32 RAM đỉnh (MB) | 2.024 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 04_Khoa/results/bench_image_embed.csv | 2023.9 | KHỚP |
| A-resnet50-macroR5 | resnet50 macro R@5 (test) | 0.704 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.7042 | KHỚP |
| A-resnet50-R1 | resnet50 R@1 | 0.604 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.6042 | KHỚP |
| A-resnet50-MRR | resnet50 MRR@10 | 0.644 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.6437 | KHỚP |
| A-resnet50-CTE | resnet50 CTE@5 | 0.138 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.1383 | KHỚP |
| A-resnet50-catP5 | resnet50 cat P@5 | 0.332 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.3317 | KHỚP |
| A-resnet50-emb | resnet50 embed truy vấn median (ms) | 1602.9 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 1602.9 | KHỚP |
| A-resnet50-peak | resnet50 RAM đỉnh (MB) | 1.357 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 04_Khoa/results/bench_image_embed.csv | 1357.2 | KHỚP |
| A-macro-vn | macro R@5 DINOv2-S (dạng VN) | 0,846 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 04_Khoa/results/bench_image_embed.csv | 0.8458 | KHỚP |
| A-macro-fc-vn | macro R@5 FashionCLIP (dạng VN) | 0,829 | 00_Chung/THUAT_NGU.md, BAO_CAO_TONG_HOP.md | 04_Khoa/results/bench_image_embed.csv | 0.8292 | KHỚP |
| A-fc-footwear | FashionCLIP R@5 footwear (ví dụ macro trong THUAT_NGU) | 0,733 | 00_Chung/THUAT_NGU.md | 04_Khoa/results/bench_image_embed.csv | 0.7333 | KHỚP |
| A-fc-clothing | FashionCLIP R@5 clothing (ví dụ macro trong THUAT_NGU) | 0,833 | 00_Chung/THUAT_NGU.md | 04_Khoa/results/bench_image_embed.csv | 0.8333 | KHỚP |
| A-fc-headwear | FashionCLIP R@5 headwear (ví dụ macro trong THUAT_NGU) | 0,883 | 00_Chung/THUAT_NGU.md | 04_Khoa/results/bench_image_embed.csv | 0.8833 | KHỚP |
| A-fc-accessory | FashionCLIP R@5 accessory (ví dụ macro trong THUAT_NGU) | 0,867 | 00_Chung/THUAT_NGU.md | 04_Khoa/results/bench_image_embed.csv | 0.8667 | KHỚP |
| A-dino-embed-s | DINOv2-S embed catalog (s) | 790,8 | 04_Khoa/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/bench_image_embed.csv | 790.8 | KHỚP |
| A-fc-embed-s | FashionCLIP embed catalog (s) | 775,8 | 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 775.8 | KHỚP |
| A-dino-gate | DINOv2-S gate centroid R@5 sau | 0,796 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/bench_image_embed.csv | 0.7958 | KHỚP |
| A-fc-gateCTE | FashionCLIP gate zero-shot CTE@5 | 0,044 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 00_Chung/THUAT_NGU.md, 04_Khoa/README.md | 04_Khoa/results/bench_image_embed.csv | 0.0442 | KHỚP |
| F-dinov2_s | Bảng F tổng điểm dinov2_s | 4,83 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/weighted_scoring.json | 4.833 | KHỚP |
| F-siglip_b16 | Bảng F tổng điểm siglip_b16 | 3,98 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/weighted_scoring.json | 3.976 | KHỚP |
| F-fashionclip | Bảng F tổng điểm fashionclip | 3,96 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/weighted_scoring.json | 3.962 | KHỚP |
| F-clip_b32 | Bảng F tổng điểm clip_b32 | 2,99 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/weighted_scoring.json | 2.994 | KHỚP |
| F-resnet50 | Bảng F tổng điểm resnet50 | 2,40 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/weighted_scoring.json | 2.398 | KHỚP |
| FB-dinov2_s | Bảng F kịch bản B dinov2_s | 4,48 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/weighted_scoring_scenario_B.json | 4.483 | KHỚP |
| FB-fashionclip | Bảng F kịch bản B fashionclip | 4,03 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/weighted_scoring_scenario_B.json | 4.029 | KHỚP |
| FB-siglip_b16 | Bảng F kịch bản B siglip_b16 | 3,96 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/weighted_scoring_scenario_B.json | 3.964 | KHỚP |
| F-recompute-dino | Bảng F DINOv2-S tính lại từ điểm thành phần × trọng số | 4,83 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/weighted_scoring.json | 4.8331 | KHỚP |
| F-sens | DINOv2-S hạng 1 ở bao nhiêu/12 cấu hình độ nhạy | 12/12 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 04_Khoa/README.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/weighted_scoring_sensitivity.json | 12 | KHỚP |
| T-background-siglip_b16 | R@5 background siglip_b16 | 0,906 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/recall_by_transform.csv | 0.906 | KHỚP |
| T-background-dinov2_s | R@5 background dinov2_s | 0,812 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/recall_by_transform.csv | 0.812 | KHỚP |
| T-background-fashionclip | R@5 background fashionclip | 0,656 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/recall_by_transform.csv | 0.656 | KHỚP |
| T-combo-dinov2_s | R@5 combo dinov2_s | 0,750 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/recall_by_transform.csv | 0.75 | KHỚP |
| T-combo-fashionclip | R@5 combo fashionclip | 0,667 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/recall_by_transform.csv | 0.667 | KHỚP |
| T-lowres_jpeg-siglip_b16 | R@5 lowres_jpeg siglip_b16 | 0,278 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/recall_by_transform.csv | 0.278 | KHỚP |
| T-lowres_jpeg-fashionclip | R@5 lowres_jpeg fashionclip | 0,500 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/recall_by_transform.csv | 0.5 | KHỚP |
| TAU-fashionclip | τ_v fashionclip (max OOD val + 0,01) | 0,7039 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 0.7039 | KHỚP |
| TAU-dinov2_s | τ_v dinov2_s (max OOD val + 0,01) | 0,5923 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 0.5923 | KHỚP |
| TAU-siglip_b16 | τ_v siglip_b16 (max OOD val + 0,01) | 0,7531 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 0.7531 | KHỚP |
| TAU-clip_b32 | τ_v clip_b32 (max OOD val + 0,01) | 0,8887 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 0.8887 | KHỚP |
| TAUk-fashionclip | % giữ truy vấn instance tại τ_v của fashionclip | 84,2 % | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 84.17 | KHỚP |
| TAUk-dinov2_s | % giữ truy vấn instance tại τ_v của dinov2_s | 94,2 % | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 94.17 | KHỚP |
| TAUk-siglip_b16 | % giữ truy vấn instance tại τ_v của siglip_b16 | 96,3 % | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 96.25 | KHỚP |
| TAUk-clip_b32 | % giữ truy vấn instance tại τ_v của clip_b32 | 67,1 % | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 67.08 | KHỚP |
| TAU-025 | τ_v = 0,25 loại được bao nhiêu % OOD (FashionCLIP) | 0 % | 00_Chung/QUYET_DINH_CAN_CHOT.md | 04_Khoa/results/tau_v_analysis.json | 0 | KHỚP |
| I-baseline-R@5 | Cải tiến baseline R@5 | 0,829 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.8292 | KHỚP |
| I-I3_linear_adapter-R@5 | Cải tiến I3_linear_adapter R@5 | 0,921 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.9208 | KHỚP |
| I-I2_tta_hflip-R@5 | Cải tiến I2_tta_hflip R@5 | 0,838 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.8375 | KHỚP |
| I-I1_bbox_crop_query_only-R@5 | Cải tiến I1_bbox_crop_query_only R@5 | 0,825 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.825 | KHỚP |
| I-I19_type_gate_zeroshot-R@5 | Cải tiến I19_type_gate_zeroshot R@5 | 0,821 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.8208 | KHỚP |
| I-I19_type_gate_zeroshot-CTE@5 | Cải tiến I19_type_gate_zeroshot CTE@5 | 0,044 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.0442 | KHỚP |
| I-I3_linear_adapter-MRR@10 | Cải tiến I3_linear_adapter MRR@10 | 0,872 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.8719 | KHỚP |
| I-I3_linear_adapter-CTE@5 | Cải tiến I3_linear_adapter CTE@5 | 0,026 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 0.0258 | KHỚP |
| I-adapter-n | Số ảnh huấn luyện adapter (biến đổi tổng hợp) | 800 | 04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md | 04_Khoa/results/improvements_fashionclip.json | 800 | KHỚP |
| BI-search | FashionCLIP search-only median (ms) | 1,9 ms | 04_Khoa/README.md | 04_Khoa/results/build_index_fashionclip.json | 1.885 | KHỚP |
| BI-e2e | FashionCLIP embed+gate+search median (ms) | 168,8 | 04_Khoa/README.md | 04_Khoa/results/build_index_fashionclip.json | 168.84 | KHỚP |
| E2E-tsr | TSR visual-only | 15/18 = 0,833 | 04_Khoa/README.md, BAO_CAO_TONG_HOP.md | 04_Khoa/results/e2e_visual-only.json | 0.8333 | KHỚP |
| E2H-tsr | TSR e2e hệ thống ghép (60 kịch bản) | 39/60 = 0,650 | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 0.65 | KHỚP |
| E2H-n | Số kịch bản e2e hệ thống ghép | 39/60 | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md | 04_Khoa/results/e2e_http.json | 60 | KHỚP |
| E2H-route | Route accuracy e2e | 40/60 = 0,667 | BAO_CAO_TONG_HOP.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 0.6667 | KHỚP |
| E2H-p50 | Latency e2e p50 (ms) | 29,1 | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 29.12 | KHỚP |
| E2H-p95 | Latency e2e p95 (ms) | 12.759,5 | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 12759.5 | KHỚP |
| E2H-gem | Tỉ lệ chuyển Gemini e2e | 18,3 % | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 0.1833 | KHỚP |
| E2H-tin | Token vào/100 lượt e2e | 3.023,3 | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 3023.3 | KHỚP |
| E2H-tout | Token ra/100 lượt e2e | 980,0 | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 980 | KHỚP |
| E2H-calls | Lời gọi Gemini thành công trong lượt e2e | 11 (+2 lần thử lại) | BAO_CAO_TONG_HOP.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 11 | KHỚP |
| E2H-retry | Lần thử lại Gemini trong lượt e2e | +2 lần thử lại | BAO_CAO_TONG_HOP.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 2 | KHỚP |
| E2H-vis | TSR visual trong e2e hệ thống ghép (DINOv2-S) | 16/18 = 0,889 | BAO_CAO_TONG_HOP.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 0.8889 | KHỚP |
| E2H-vp95 | Latency p95 truy vấn ảnh e2e (ms) | 215,0 | BAO_CAO_TONG_HOP.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 214.97 | KHỚP |
| E2H-tp95 | Latency p95 truy vấn văn bản e2e (ms) | 13.266,5 | BAO_CAO_TONG_HOP.md, 04_Khoa/docs/US_44_baseline_e2e.md | 04_Khoa/results/e2e_http.json | 13266.5 | KHỚP |
| EV-n | Số truy vấn eval_visual | 600 | 04_Khoa/README.md | 04_Khoa/eval/eval_visual_stats.json | 600 | KHỚP |
| EV-hard | hard_cross_type (test) | 96 hard_cross_type (53 | 04_Khoa/README.md | 04_Khoa/eval/eval_visual_stats.json | 53 | KHỚP |
| R-v0 | Router v0 trên bộ Chiến (n=78) | 0,667 | 01_Trung/README.md, 01_Trung/docs/US_41_router_agent_va_gemini.md | 01_Trung/results/router_eval_v0.json | 0.6667 | KHỚP |
| R-v1-chien | Router v1 trên bộ Chiến (ĐÃ chỉnh theo lỗi – không phải held-out) | 0,923 | 01_Trung/README.md, 00_Chung/THUAT_NGU.md, 01_Trung/docs/US_41_router_agent_va_gemini.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/router_eval_v1.json | 0.9231 | KHỚP |
| R-v1-merged | Router v1 bộ Chiến gộp 2 nhãn gemini | 0,949 | 01_Trung/README.md | 01_Trung/results/router_eval_v1.json | 0.9487 | KHỚP |
| R-v1-held | Router v1 trên tập Gemini sinh (n=49, held-out) | 0,878 | 01_Trung/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, 00_Chung/THUAT_NGU.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/router_eval_v1.json | 0.8776 | KHỚP |
| R-v1-held-n | n tập held-out router | n=49 | 01_Trung/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 01_Trung/results/router_eval_v1.json | 49 | KHỚP |
| R-emb | Router + e5-small trên bộ Chiến | 0,846 (bộ Chiến) | 01_Trung/README.md | 01_Trung/results/router_eval_v1_emb.json | 0.8462 | KHỚP |
| G-fb | Fallback rate (47/172) | 0,273 | 01_Trung/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, 00_Chung/THUAT_NGU.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_fallback_live.json | 0.2733 | KHỚP |
| G-p50 | Gemini latency p50 (s, gồm chờ 429) | 14,4 s | 01_Trung/README.md | 01_Trung/results/gemini_fallback_live.json | 14.3638 | KHỚP |
| G-p95 | Gemini latency p95 (s) | 41,1 s | 01_Trung/README.md | 01_Trung/results/gemini_fallback_live.json | 41.0678 | KHỚP |
| G-tin | Token vào TB/lời gọi (A) | 165,1 | 01_Trung/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/gemini_fallback_live.json | 165.1 | KHỚP |
| G-tout | Token ra TB/lời gọi (A) | 55,5 | 01_Trung/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/gemini_fallback_live.json | 55.5 | KHỚP |
| G-think | Thinking TB/lời gọi (B, budget 1024) | 350,3 | 01_Trung/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/gemini_fallback_live.json | 350.3 | KHỚP |
| G-t100 | Token/100 lượt hội thoại (Trung, A) = fallback × 100 × total/lời gọi | 6.028 | 01_Trung/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_fallback_live.json | 6028.0 | KHỚP |
| G-t100B | Token/100 lượt (Trung, B thinking) | 15.092 | 01_Trung/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/gemini_fallback_live.json | 15091.9 | KHỚP |
| G-t100-chien | Token/100 lượt quy đổi (Chiến, prompt few-shot) | 21.566 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/gemini_fallback_check.json | 21565.3 | KHỚP |
| G-t100-hoang | Token/100 lượt quy đổi (Hoàng, prompt ngắn) | 4.599 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 05_Hoang/README.md, BAO_CAO_TONG_HOP.md | 05_Hoang/results/llm_gateway_live.json | 4598.9 | KHỚP |
| G-sf | Gemini khẳng định có bán hàng ngoài danh mục (n=40) | 2/40 | 01_Trung/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, 00_Chung/THUAT_NGU.md, BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_store_fact_recheck.json | 2 | KHỚP |
| G-cache | Cache trúng (Trung) | 10/10 | 01_Trung/README.md | 01_Trung/results/gemini_fallback_live.json | 10 | KHỚP |
| S-tax | Schema hợp lệ catalog taxonomy v1 | 4.586/4.586 | 01_Trung/README.md | 01_Trung/results/schema_validation.json | 4586 | KHỚP |
| S-vi | Schema hợp lệ ViMRHP trong phạm vi | 361/361 | 01_Trung/README.md | 01_Trung/results/schema_validation.json | 361 | KHỚP |
| TX-168 | Số nhãn FPI map được | 168/168 | 01_Trung/README.md | 01_Trung/results/taxonomy_coverage.json | 168 | KHỚP |
| TX-286 | Mũ sau taxonomy v1 (trước làm sạch) | 286 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/results/taxonomy_coverage.json | 286 | KHỚP |
| D-4385 | Số SP sau làm sạch | 4.385 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md, README.md | 02_TuanDat/results/clean_report.json | 4385 | KHỚP |
| D-285 | Mũ chuẩn sau làm sạch | 285 | 02_TuanDat/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md, README.md | 02_TuanDat/results/clean_report.json | 285 | KHỚP |
| D-293 | Mũ trước làm sạch (nhãn gốc FPI) | 293 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 00_Chung/stats.json | 293 | KHỚP |
| D-md5 | Số nhóm trùng MD5 / SP xoá | xoá 21 | 02_TuanDat/README.md | 02_TuanDat/results/clean_report.json | 21 | KHỚP |
| D-phash | Cặp pHash ≤ 4 | 3.937 | 02_TuanDat/README.md | 02_TuanDat/results/clean_report.json | 3937 | KHỚP |
| D-review | Cặp pHash cần người xem | 122 | 02_TuanDat/README.md | 02_TuanDat/results/clean_report.json | 122 | KHỚP |
| D-title27 | Nhãn mũ sửa theo tiêu đề | 27 nhãn | 02_TuanDat/README.md | 02_TuanDat/results/clean_report.json | 27 | KHỚP |
| L-gemini35flashlite-faithfulness | Bảng D gemini35flashlite faithfulness [LLM chấm] | 0,939 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 0.939 | KHỚP |
| L-gemini35flashlite-hallucination_rate | Bảng D gemini35flashlite hallucination_rate [LLM chấm] | 0,111 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 0.111 | KHỚP |
| L-gemma4_26b_api-faithfulness | Bảng D gemma4_26b_api faithfulness [LLM chấm] | 0,992 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 0.992 | KHỚP |
| L-gemma4_26b_api-hallucination_rate | Bảng D gemma4_26b_api hallucination_rate [LLM chấm] | 0,031 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 0.031 | KHỚP |
| L-qwen25_05b-faithfulness | Bảng D qwen25_05b faithfulness [LLM chấm] | 0,255 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 0.255 | KHỚP |
| L-qwen25_05b-hallucination_rate | Bảng D qwen25_05b hallucination_rate [LLM chấm] | 0,333 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 0.333 | KHỚP |
| L-gemini35flashlite-tokens_in_per_100 | Bảng D gemini35flashlite tokens_in_per_100 | 60.619 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 60619 | KHỚP |
| L-gemini35flashlite-tokens_out_incl_thinking_per_100 | Bảng D gemini35flashlite tokens_out_incl_thinking_per_100 | 3.631 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 3631 | KHỚP |
| L-gemma4_26b_api-tokens_out_incl_thinking_per_100 | Bảng D gemma4_26b_api tokens_out_incl_thinking_per_100 | 63.112 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 63112 | KHỚP |
| L-qwen25_05b-tokens_in_per_100 | Bảng D qwen25_05b tokens_in_per_100 | 68.994 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 02_TuanDat/results/bench_llm_summary.json | 68994 | KHỚP |
| L-router | Gemini Flash-Lite làm router (n=14) | 0,857 | 02_TuanDat/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 02_TuanDat/results/bench_llm_summary.json | 0.857 | KHỚP |
| L-budget | Lời gọi Gemini Đạt đã dùng | 250/250 | 02_TuanDat/README.md | 02_TuanDat/results/gemini_budget.json | 250 | KHỚP |
| L-429 | Lời gọi bị 429 = số câu trong file failed × 4 lần thử (1 + 3 retry) | 144 lời gọi bị 429 | 02_TuanDat/README.md | 02_TuanDat/results/failed/bench_llm_qa_gemini35flash_t0_ALL_429.jsonl | 144 · 36 dòng × 4 | KHỚP |
| L-us36 | Ý tóm tắt LLM không có trong review | 3/93 | 02_TuanDat/README.md | 02_TuanDat/results/us36_kiem_tay_20sp.csv | 3 | KHỚP |
| L-us36n | Tổng số ý đã kiểm (US_36) | 3/93 | 02_TuanDat/README.md | 02_TuanDat/results/us36_kiem_tay_20sp.csv | 93 | KHỚP |
| Q-280 | Số câu eval_qa | 280 câu | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/eval/eval_qa.jsonl | 280 | KHỚP |
| Q-71 | Câu không có đáp án | 71 câu answerable=false | 03_Chien/README.md | 03_Chien/eval/eval_qa.jsonl | 71 | KHỚP |
| Q-254 | Tỉ lệ câu không đáp án (%) | 25,4 % | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/eval/eval_qa.jsonl | 25.3571 | KHỚP |
| Q-llm | Câu eval_qa do LLM sinh | 251 | 03_Chien/README.md | 03_Chien/eval/eval_qa.jsonl | 251 | KHỚP |
| Q-r78 | Số câu eval_router | 78 câu | 03_Chien/README.md | 03_Chien/eval/eval_router.jsonl | 78 | KHỚP |
| Q-r21 | Câu chitchat/ood eval_router | 21 chitchat/ood | 03_Chien/README.md | 03_Chien/eval/eval_router.jsonl | 21 | KHỚP |
| Q-chunks | Số chunk kho RAG | 10.173 | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/data/kb/chunks.jsonl | 10173 | KHỚP |
| Q-kbsp | Số SP trong kho RAG | 428 | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/data/kb/chunks.jsonl | 428 | KHỚP |
| Q-oos-qa | Câu eval_qa ngoài phạm vi taxonomy | 45/280 | 03_Chien/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv | 45 | KHỚP |
| Q-oos-r | Câu eval_router ngoài phạm vi | 4/78 | 03_Chien/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv | 4 | KHỚP |
| V-rev-all | Review ViMRHP toàn bộ 509 SP | 11.009 | 04_Khoa/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 00_Chung/stats.json | 11009 | KHỚP |
| V-rev-428 | Review của 428 SP (bỏ đồng hồ) | 9.403 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 01_Trung/data/vimrhp_taxonomy_v1.csv | 9403 | KHỚP |
| V-rev-349 | Review của 349 SP có lá taxonomy (keep) | 7.575 | 00_Chung/QUYET_DINH_CAN_CHOT.md, 01_Trung/docs/US_49_taxonomy.md | 01_Trung/data/vimrhp_taxonomy_v1.csv | 7575 | KHỚP |
| V-rev-361 | Review của 361 SP trong phạm vi (349 keep + 12 unknown) | 7.833 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 01_Trung/data/vimrhp_taxonomy_v1.csv | 7833 | KHỚP |
| H-866 | Hybrid Hit@5 (toàn 209 câu) | 0.866 | 03_Chien/README.md | 03_Chien/results/rag_retrieval_eval.json | 0.866 | KHỚP |
| H-895 | Hybrid Hit@5 split test (n=114) | 0,895 | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.8947 | KHỚP |
| H-377 | Hybrid Hit@1 test | 0,377 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/results/rag_retrieval_eval.json | 0.3772 | KHỚP |
| H-599 | Hybrid MRR@10 test | 0,599 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/results/rag_retrieval_eval.json | 0.5987 | KHỚP |
| H-tfidf | TF-IDF char Hit@5 test | 0,877 | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/results/rag_retrieval_eval.json | 0.8772 | KHỚP |
| H-bm25 | BM25 Hit@5 test | 0,868 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/results/rag_retrieval_eval.json | 0.8684 | KHỚP |
| E-ref | Refusal accuracy RAG (sau sửa nhãn qa108) | 15/15 | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, 00_Chung/THUAT_NGU.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_e2e_eval.json | 15 | KHỚP |
| E-ref-before | Refusal accuracy RAG TRƯỚC sửa nhãn (15/16) | 15/16 | BAO_CAO_TONG_HOP.md, 03_Chien/docs/US_33_34_35_rag.md | 03_Chien/results/rag_e2e_eval.json | 0.9375 | KHỚP |
| E-cg | Cited-gold | 0.865 | 03_Chien/README.md | 03_Chien/results/rag_e2e_eval.json | 0.8649 | KHỚP |
| E-faith | Faithfulness RAG Chiến [LLM chấm] | 1.00 | 03_Chien/README.md | 03_Chien/results/rag_e2e_eval.json | 1 | KHỚP |
| E-n | Số câu e2e RAG | 52 câu | 03_Chien/README.md | 03_Chien/results/rag_e2e_eval.json | 52 | KHỚP |
| E-tok | Token vào/câu RAG | 378,9 | 03_Chien/README.md | 03_Chien/results/rag_e2e_eval.json | 378.9 | KHỚP |
| F-viol | Vi phạm giá/size/tồn kho nhánh Gemini (Chiến) | 0/20 | 03_Chien/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md | 03_Chien/results/gemini_fallback_check.json | 0 | KHỚP |
| F-ok | Phản hồi hợp lệ nhánh Gemini (Chiến) | 22/60 | 03_Chien/README.md | 03_Chien/results/gemini_fallback_check.json | 22 | KHỚP |
| F-tin | Token vào TB nhánh fallback Chiến | 747,5 | 00_Chung/QUYET_DINH_CAN_CHOT.md | 03_Chien/results/gemini_fallback_check.json | 747.5 | KHỚP |
| F-p50 | Latency nhánh Gemini Chiến p50 (s) | 16,0 s | 03_Chien/README.md | 03_Chien/results/gemini_fallback_check.json | 15.9831 | KHỚP |
| F-p95 | Latency nhánh Gemini Chiến p95 (s) | 27,8 s | 03_Chien/README.md | 03_Chien/results/gemini_fallback_check.json | 27.7721 | KHỚP |
| F-74750 | Token vào /100 LỜI GỌI Gemini (Chiến) | 74.750 | 03_Chien/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 03_Chien/results/gemini_fallback_check.json | 74750 | KHỚP |
| API-p50 | API /search/image p50 (ms) | p50 393 ms | 05_Hoang/README.md, 00_Chung/THUAT_NGU.md | 05_Hoang/results/api_eval.json | 393.4814 | KHỚP |
| API-p95 | API /search/image p95 (ms) | 1.106 ms | 05_Hoang/README.md, 00_Chung/THUAT_NGU.md, BAO_CAO_TONG_HOP.md | 05_Hoang/results/api_eval.json | 1106.4 | KHỚP |
| API-1500 | % truy vấn < 1,5 s | 97,5 % | 05_Hoang/README.md | 05_Hoang/results/api_eval.json | 97.5 | KHỚP |
| API-cte | CTE@5 qua API (CLIP B/32 + gate) | 1,5 % | 05_Hoang/README.md | 05_Hoang/results/api_eval.json | 1.5 | KHỚP |
| API-subp | Sub-category P@5 qua API | 0,925 | 05_Hoang/README.md | 05_Hoang/results/api_eval.json | 0.925 | KHỚP |
| API-top1 | Top-1 cosine trung bình CLIP B/32 | 0,96 | 05_Hoang/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 05_Hoang/results/api_eval.json | 0.9586 | KHỚP |
| API-cmp | Ô so sánh khớp | 370/370 | 05_Hoang/README.md, BAO_CAO_TONG_HOP.md | 05_Hoang/results/api_eval.json | 370 | KHỚP |
| API-txt | Kết quả /search/text thoả lọc | 300/300 | 05_Hoang/README.md | 05_Hoang/results/api_eval.json | 300 | KHỚP |
| TE-tfidf_word | Text-embed Hit@5 trong SP tfidf_word (Hoàng) | 0,875 | 05_Hoang/README.md | 05_Hoang/results/bench_text_embed_summary.csv | 0.875 | KHỚP |
| TE-tfidf_char | Text-embed Hit@5 trong SP tfidf_char (Hoàng) | 0,856 | 05_Hoang/README.md | 05_Hoang/results/bench_text_embed_summary.csv | 0.8558 | KHỚP |
| TE-e5-small | Text-embed Hit@5 trong SP e5-small (Hoàng) | 0,803 | 05_Hoang/README.md | 05_Hoang/results/bench_text_embed_summary.csv | 0.8029 | KHỚP |
| TE-minilm-l12 | Text-embed Hit@5 trong SP minilm-l12 (Hoàng) | 0,794 | 05_Hoang/README.md | 05_Hoang/results/bench_text_embed_summary.csv | 0.7943 | KHỚP |
| TE-vn-sbert | Text-embed Hit@5 trong SP vn-sbert (Hoàng) | 0,775 | 05_Hoang/README.md | 05_Hoang/results/bench_text_embed_summary.csv | 0.7751 | KHỚP |
| TE-n | n câu Bảng C của Hoàng (tfidf/e5) | 208 câu | 05_Hoang/README.md | 05_Hoang/results/bench_text_embed_summary.csv | 208 · minilm-l12 và vn-sbert chạy trên 209 câu – xem doi_chieu ghi chú | KHỚP |
| GW-10 | Gateway request thành công | 10/10 | 05_Hoang/README.md | 05_Hoang/results/llm_gateway_live.json | 10 | KHỚP |
| GW-tin | Token vào /100 LỜI GỌI (Hoàng) | 10.460 | 05_Hoang/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 05_Hoang/results/llm_gateway_live.json | 10460 | KHỚP |
| GW-tout | Token ra /100 LỜI GỌI (Hoàng) | 6.370 | 05_Hoang/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 05_Hoang/results/llm_gateway_live.json | 6370 | KHỚP |
| GW-cache | Cache p50 (ms) gateway | 17,9 ms | 05_Hoang/README.md | 05_Hoang/results/llm_gateway_live.json | 17.8581 | KHỚP |
| DV1-n | Data v1 tổng SP | 5.021 | 05_Hoang/README.md | 05_Hoang/data/counts_data_v1.json | 5021 | KHỚP |
| DV1-298 | Data v1 mũ (gồm băng đô + ViMRHP) | 298 | 05_Hoang/README.md, 00_Chung/QUYET_DINH_CAN_CHOT.md | 05_Hoang/data/counts_data_v1.json | 298 | KHỚP |
| DV1-cl | Data v1 quần áo (gồm ViMRHP) | 2.388 | 05_Hoang/README.md | 05_Hoang/data/counts_data_v1.json | 2388 | KHỚP |
| SH-4593 | Catalog FPI shared_data | 4.593 | 04_Khoa/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, README.md | 00_Chung/stats.json | 4593 | KHỚP |
| SH-509 | ViMRHP số SP | 509 | 04_Khoa/README.md, 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, README.md | 00_Chung/stats.json | 509 | KHỚP |
| H-e5-small-hit@5 | dense:intfloat/multilingual-e5-small hit@5 test | 0,807 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.807 | KHỚP |
| H-M-L12-v2-hit@5 | dense:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 hit@5 test | 0,763 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.7632 | KHỚP |
| H-e5-small-hit@1 | dense:intfloat/multilingual-e5-small hit@1 test | 0,298 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.2982 | KHỚP |
| H-M-L12-v2-hit@1 | dense:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 hit@1 test | 0,316 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.3158 | KHỚP |
| H-e5-small-mrr@10 | dense:intfloat/multilingual-e5-small mrr@10 test | 0,525 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.5252 | KHỚP |
| H-M-L12-v2-mrr@10 | dense:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 mrr@10 test | 0,511 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.5112 | KHỚP |
| H-idf_char-hit@1 | tfidf_char hit@1 test | 0,289 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.2895 | KHỚP |
| H-bm25-hit@1 | bm25 hit@1 test | 0,272 | 01_Trung/docs/US_27_bao_cao_tuan2_khung.md, BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_retrieval_eval.json | 0.2719 | KHỚP |
| H209-idf_char | tfidf_char Hit@5 trên 209 câu | 0,833 | BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_eval.json | 0.8325 | KHỚP |
| H209-bm25 | bm25 Hit@5 trên 209 câu | 0,837 | BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_eval.json | 0.8373 | KHỚP |
| H209-e5-small | dense:intfloat/multilingual-e5-small Hit@5 trên 209 câu | 0,794 | BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_eval.json | 0.7943 | KHỚP |
| H209-M-L12-v2 | dense:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 Hit@5 trên 209 câu | 0,756 | BAO_CAO_TONG_HOP.md | 03_Chien/results/rag_eval.json | 0.756 | KHỚP |
| FR-seed_trung | Số câu chuyển Gemini – seed_trung | \| 45 \| 13 \| | BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_fallback_live.json | 13 | KHỚP |
| FR-chien_eval_router | Số câu chuyển Gemini – chien_eval_router | \| 78 \| 21 \| | BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_fallback_live.json | 21 | KHỚP |
| FR-gemini_gen_heldout | Số câu chuyển Gemini – gemini_gen_heldout | \| 49 \| 13 \| | BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_fallback_live.json | 13 | KHỚP |
| FR-47 | Tổng câu chuyển Gemini / 172 | **47** | BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_fallback_live.json | 47 | KHỚP |
| T100-trung-call | Token/100 lời gọi (Trung A) | 22.060 | BAO_CAO_TONG_HOP.md | 01_Trung/results/gemini_fallback_live.json | 22060.0 | KHỚP |
| T100-chien-call | Token/100 lời gọi (Chiến) | 78.920 | BAO_CAO_TONG_HOP.md, 05_Hoang/README.md | 03_Chien/results/gemini_fallback_check.json | 78920.0 | KHỚP |
| T100-hoang-call | Token/100 lời gọi (Hoàng) | 16.830 | BAO_CAO_TONG_HOP.md | 05_Hoang/results/llm_gateway_live.json | 16830.0 | KHỚP |
| T100-dat-qa | Token/100 câu QA (Đạt, vào + ra) | 64.250 | BAO_CAO_TONG_HOP.md | 02_TuanDat/results/bench_llm_summary.json | 64250 | KHỚP |
| D-brand | Dòng chuẩn hoá thương hiệu | 1.304 dòng | BAO_CAO_TONG_HOP.md | 02_TuanDat/results/clean_report.json | 1304 | KHỚP |
| TX-keep | Nhãn FPI giữ / unknown / loại | 61 giữ, 5 unknown, 102 loại | BAO_CAO_TONG_HOP.md | 01_Trung/results/taxonomy_coverage.json | 61 | KHỚP |
| TX-vi | ViMRHP giữ / unknown / loại | giữ 349, unknown 12, loại 148 | BAO_CAO_TONG_HOP.md | 01_Trung/results/taxonomy_coverage.json | 349 | KHỚP |
| EDA-37 | Số articleType trong catalog | 37 `articleType` | BAO_CAO_TONG_HOP.md | 04_Khoa/docs/US_09_eda/eda_stats.json | 37 | KHỚP |
| EDA-785 | Dòng trùng tên | 785 dòng trùng tên | BAO_CAO_TONG_HOP.md, 04_Khoa/README.md | 04_Khoa/docs/US_09_eda/eda_stats.json | 785 | KHỚP |
| PYT-sum | Tổng test pass 5 folder (53+21+51+30+78) | 233 passed | BAO_CAO_TONG_HOP.md | KIEM_DINH_TAC_NHAN_3.md (chạy pytest) | 233 · số từng folder lấy từ lần chạy pytest cuối, ghi trong KIEM_DINH | KHỚP |
| US-sum | Tổng US Đạt (3+3+4+6+7) | **23** | BAO_CAO_TONG_HOP.md | README mục 0 của 5 thành viên | 23 | KHỚP |

## Quét câu chữ rủi ro: 0 cảnh báo

Mẫu: adapter 0,921 không ghi tổng hợp; token /100 lượt nhầm đơn vị; 7.575 ↔ 361; 0,923 gọi là held-out; faithfulness gọi là người chấm.

Không có cảnh báo.
