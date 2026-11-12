# 04_Khoa – ML: embedding ảnh, đánh giá Visual Search, tối ưu

Đồ án 1 – AI Agent trợ lý mua sắm thời trang (MSA). Thành viên: **Khoa** (người cầm "số liệu quyết định" của phần visual).
Dữ liệu: `shared_data v1 (prep_shared_data.py seed 42)` – catalog FPI 4.593 SP (ảnh 60×80), 44.072 dòng FPI gốc, ViMRHP 509 SP/11.009 review. Mọi số dưới đây là **đo thật**, có file kết quả + lệnh tái lập; phần không đo được ghi `CHƯA ĐO`.

## 0. Đối chiếu yêu cầu kế hoạch (Tác nhân 2 – 05/11/2026)

Khoa là Owner của **9 US** (Backlog). Kết luận: **Đạt 6 · Một phần 3 · Chưa đạt 0**. Lưu ý chung: mọi truy vấn visual là **[Thật–tổng hợp]** (ảnh catalog thật bị biến đổi), chưa có ảnh ngoài đời, chưa người duyệt nhãn (`00_Chung/THUAT_NGU.md`).

| US | Đầu ra yêu cầu (DOCS) | File đầu ra | Tiêu chí nghiệm thu (TEST) | Kết quả | Bằng chứng / lý do |
|---|---|---|---|---|---|
| US_09 | notebook EDA + ≥ 6 biểu đồ | `docs/US_09_eda/` (9 PNG, `eda_report.md`, `notebook_eda.ipynb`) | Số liệu cụ thể cho từng nguồn | **Đạt** | 9 biểu đồ; số liệu riêng FPI và ViMRHP (`eda_stats.json`) |
| US_12 | Sheet 2 – Visual Search | `docs/US_12_do_do_visual_search.md` | Mỗi độ đo có công thức, ưu/nhược, chọn/không | **Đạt** | Recall@K, P@K, mAP, MRR, NDCG, CTE, AUROC, latency – đủ 3 cột |
| US_15 | eval_visual.csv + mô tả cách tạo | `eval/eval_visual.csv`, `eval/eval_visual_ood.csv`, `docs/US_15_eval_visual.md` | ≥ 200 query (studio khác góc + **ảnh ngoài đời**); chia val/test; ≥ 30 test/nhóm; ≥ 20 query dễ nhầm; có cột product_type | **Một phần** | Đạt: 600 query (test 360, 90/nhóm), 96 hard_cross_type (53 ở test), có product_type, val/test tách theo product_id. Chưa: **0 ảnh ngoài đời** (chờ US_11); 100 % là biến đổi tổng hợp |
| US_19 | Sheet 3 – Bảng A | `docs/US_19_khao_sat_embedding_anh.md` | ≥ 6 phiên bản, mỗi cái có lý do đưa vào | **Đạt** | 8 model trong registry + lý do |
| US_21 | Sheet 3 – Bảng E | `docs/US_21_he_thong_va_bai_bao_tuong_tu.md` | Mỗi hệ thống/bài báo có "điểm đáng học" + "liên hệ đồ án" | **Đạt** | (trích dẫn cần xác minh lại) |
| US_22 | Bảng A (kết quả) + notebook | `docs/US_22_benchmark_embedding.md`, `results/bench_image_embed.csv`, `results/bench/*.json` | ≥ 5 model, cùng tiền xử lý, cùng FAISS Flat, latency ≥ 3 lần lấy median | **Đạt** | 5 model đo thật; 60 lần đo latency; R@5 theo nhóm, CTE@5, có/không gate. Khác kế hoạch: CLIP B/16 CHƯA ĐO, thay bằng DINOv2-S |
| US_29 | build_index.py + index | `src/scripts/build_index.py`, `docs/US_29_build_index.md` | Build < 30 phút cho ≥ 3.000 SP; truy vấn < 200 ms | **Đạt** | FashionCLIP: 775,8 s (12,9 phút); search 1,9 ms; embed+gate+search median 168,8 ms. Nếu đổi model theo Bảng F (DINOv2-S, embed 790,8 s) vẫn < 30 phút |
| US_44 | baseline_report.md | `docs/US_44_baseline_e2e.md`, `eval/e2e_scenarios.jsonl` | Bảng baseline + top 10 lỗi; bảng route: tỉ lệ Gemini, chi phí/100 lượt | **Một phần** | 60 kịch bản có; chỉ phần visual đo thật (TSR 15/18 = 0,833); TSR toàn hệ thống, tỉ lệ Gemini, chi phí CHƯA ĐO (chờ ghép Agent/API) |
| US_45 | Sheet "Cải tiến T3" có số liệu | `docs/US_45_cai_tien_va_do_truoc_sau.md`, `results/improvements_fashionclip.{csv,json}` | ≥ 4 cải tiến High đo trước/sau; ≥ 1 nhóm Gemini (I15/I16); ≥ 1 I19 | **Một phần** | 4 cải tiến visual đo thật trên truy vấn **[Thật–tổng hợp]** (I3 adapter R@5 0,829 → 0,921 – adapter học trên cùng họ biến đổi tổng hợp với truy vấn test nên **chưa chứng minh cải thiện trên ảnh người dùng**; I2; I1; I19 CTE@5 0,062 → 0,044). Chưa: cải tiến Gemini (I15/I16 – của Hoàng/Chiến); I1 và I19 làm R@5 giảm nhẹ → theo TEST chỉ giữ nếu cải thiện rõ |

**Mâu thuẫn liên quan đã xử lý (`00_Chung/QUYET_DINH_CAN_CHOT.md`):**
- **Mục E – chọn model:** Bảng F chạy thật trên CSV của Khoa xếp **DINOv2-S 4,83 > SigLIP 3,98 > FashionCLIP 3,96**; DINOv2-S hạng 1 ở 12/12 cấu hình độ nhạy. Thêm `results/recall_by_transform.csv` (Tác nhân 2, chỉ đọc kết quả có sẵn): truy vấn đổi nền R@5 – SigLIP 0,906, DINOv2-S 0,812, FashionCLIP 0,656. → Kết luận "chọn FashionCLIP" ở §2 dưới đây **không được Bảng F ủng hộ**; đề xuất DINOv2-S (dự phòng SigLIP), chốt lại khi có ảnh ngoài đời.
- **Mục C – τ_v:** đề xuất của Khoa (τ_v theo model, lưu trong `config.json`) được chấp nhận làm phương án đề xuất; 0,25 trong thiết kế chung bị bỏ.
- **Mục A – mũ:** benchmark chạy trên catalog 4.593 (mũ 293, gồm 7 băng đô ngoài phạm vi); số chuẩn của nhóm là 285 sau làm sạch – benchmark giữ nguyên nhưng index demo nên build trên Data v1.1 (4.385 SP).

## 1. Bảng truy vết US → file → trạng thái (bản của thành viên)

| US | Đầu ra chính | Trạng thái | Số liệu thật (file) | Việc còn lại |
|---|---|---|---|---|
| US_09 EDA | `src/scripts/eda.py`, `docs/US_09_eda/` (9 biểu đồ, `eda_report.md`, `eda_stats.json`, `notebook_eda.ipynb`) | Hoàn thành (2 nguồn hiện có) | 4.593 SP: clothing 2.200 / footwear 1.400 / accessory 700 / headwear 293; 100 % ảnh 60×80; 785 dòng trùng tên; ViMRHP 93,4 % review 5 sao, 57,8 % review theo mẫu Shopee | Thêm nguồn crawl VN / ảnh ngoài đời khi có |
| US_12 Độ đo visual | `docs/US_12_do_do_visual_search.md`, `src/msa/eval/visual_metrics.py` | Hoàn thành | – (đối chiếu khớp `metrics.py` của Hoàng trong test) | Trung chốt ngưỡng ở US_18 |
| US_15 eval_visual | `src/scripts/build_eval_visual.py`, `eval/eval_visual.csv` (600), `eval/eval_visual_ood.csv` (60), `eval/queries/`, `docs/US_15_eval_visual.md` | Hoàn thành phần làm được | 600 truy vấn (val 240 / test 360; 90 test/nhóm), 96 hard_cross_type (53 test) | **80–100 ảnh ngoài đời: CHƯA CÓ** (nhóm tự chụp); 2 người duyệt nhãn |
| US_19 Khảo sát embedding | `docs/US_19_khao_sat_embedding_anh.md`, `src/msa/embed/image_embedders.py` (registry 8 model + DummyEmbedder) | Hoàn thành | dim/tham số đo khi nạp (`results/prefetch_models.json`) | Xác minh các ô `[cần xác minh]` |
| US_21 Hệ thống & bài báo | `docs/US_21_he_thong_va_bai_bao_tuong_tu.md` | Hoàn thành (khảo sát tài liệu) | – | Xác minh trích dẫn; tự trải nghiệm Shopee/Google Lens |
| US_22 Benchmark ≥ 5 model | `src/scripts/bench_image_embed.py`, `results/bench_image_embed.{csv,json}`, `results/bench/*.json`, `docs/US_22_benchmark_embedding.md` | Hoàn thành 5 model: ResNet-50, CLIP B/32, FashionCLIP, DINOv2-S, SigLIP B/16 | Bảng A/A2, gate, τ_v, 10 ví dụ lỗi/model | CLIP B/16, OpenCLIP LAION-2B, Marqo-FashionSigLIP: CHƯA ĐO (thiếu thời gian CPU) – chạy tiếp bằng script (có resume) |
| US_29 Build index | `src/scripts/build_index.py`, `src/msa/search/visual.py`, `indexes/fashionclip/` (+ `indexes/best` → fashionclip), `docs/US_29_build_index.md` | Hoàn thành | FashionCLIP: embed catalog 775,8 s (12,9 phút < 30 phút ✔); search-only 1,9 ms; e2e (embed+gate+search) median 168,8 ms ✔ / p95 674,6 ms | Đo lại latency trên máy demo không tải nền |
| US_44 Baseline e2e | `src/scripts/baseline_e2e.py`, `eval/e2e_scenarios.jsonl` (60), `docs/US_44_baseline_e2e.md` | Khung sẵn – phần visual đo thật | Visual-only: TSR 15/18 = 0,833 (3 lỗi đều do τ_v loại) | TSR toàn hệ thống, tỉ lệ Gemini, chi phí/100 lượt: CHƯA ĐO (chờ ghép Agent/API) |
| US_45 Cải tiến trước/sau | `src/msa/search/improvements.py`, `src/scripts/run_improvements.py`, `results/improvements_fashionclip.{csv,json}`, `docs/US_45_cai_tien_va_do_truoc_sau.md` | Phần visual đo thật | FashionCLIP R@5 test [Thật–tổng hợp]: I3 adapter 0,829→0,921 (chưa kiểm trên ảnh thật); I2 TTA →0,838; I1 crop truy vấn →0,825; I19 gate →0,821 (CTE@5 0,062→0,044) | I15/I16 (Gemini) của Hoàng/Chiến; đo lại trên ảnh ngoài đời; I1 crop cả catalog |

## 2. Số liệu quyết định (split test, đo thật)

Bảng đầy đủ (tự sinh): `results/tables.md`; CSV: `results/bench_image_embed.csv`.

<!-- README_TABLE -->
| Model | Macro R@5 | R@1 | R@10 | MRR@10 | CTE@5 | cat Hit@5 | cat P@5 | Embed truy vấn ms (median) |
|---|---|---|---|---|---|---|---|---|
| dinov2_s | 0.846 | 0.750 | 0.883 | 0.791 | 0.043 | 0.692 | 0.307 | 288.75 |
| siglip_b16 | 0.833 | 0.704 | 0.887 | 0.760 | 0.055 | 0.767 | 0.355 | 189.99 |
| fashionclip | 0.829 | 0.704 | 0.871 | 0.757 | 0.062 | 0.767 | 0.378 | 294.22 |
| clip_b32 | 0.721 | 0.621 | 0.746 | 0.660 | 0.076 | 0.700 | 0.353 | 428.34 |
| resnet50 | 0.704 | 0.604 | 0.738 | 0.644 | 0.138 | 0.667 | 0.332 | 1602.9 |
| clip_b16 | CHƯA ĐO | | | | | | | |
| openclip_b32_laion2b | CHƯA ĐO | | | | | | | |
| marqo_fashionsiglip | CHƯA ĐO | | | | | | | |
<!-- /README_TABLE -->

> **Ghi chú Tác nhân 2:** kết luận dưới đây là của Khoa trước khi có Bảng F; Bảng F (US_25) xếp DINOv2-S hạng 1 – xem mục 0 và `00_Chung/QUYET_DINH_CAN_CHOT.md` mục E.

**Kết luận**: chọn **FashionCLIP** (tạm thời; cao nhất tầng category, có text tower cho type gate; kém DINOv2-S 1,7 và SigLIP 0,4 điểm macro R@5 ở tầng instance – dưới ngưỡng 5 điểm). SigLIP B/16 là phương án thay thế (bền với nền khác 0,906 vs 0,656) – chốt sau khi đo ảnh ngoài đời. **τ_v phải hiệu chỉnh theo model** (0,25 mặc định không loại được ảnh OOD nào; FashionCLIP dùng 0,704).

## 3. Cấu trúc thư mục
```
src/msa/embed/image_embedders.py   # registry model + DummyEmbedder + tiền xử lý chung
src/msa/search/visual.py           # VisualSearcher.search / type_gate / query (τ_v, gate)
src/msa/search/improvements.py     # I1 bbox_crop, I2 TTA, I3 LinearAdapter
src/msa/eval/visual_metrics.py     # Recall/Precision/MRR/NDCG/AP/CTE/AUROC
src/scripts/                       # eda, build_eval_visual, bench_image_embed, build_index, run_improvements,
                                   # baseline_e2e, error_examples, tau_v_analysis, make_tables, fill_docs, prefetch_models
eval/                              # eval_visual.csv, eval_visual_ood.csv, queries/, e2e_scenarios.jsonl
results/                           # số đo thật (json/csv/md/png)
cache/                             # embedding .npy (tái dùng, không commit)
indexes/                           # FAISS index (không commit)
docs/                              # tài liệu theo US
tests/                             # pytest (DummyEmbedder, dữ liệu giả)
```

## 4. Tái lập
```bash
python src/scripts/eda.py
python src/scripts/build_eval_visual.py                      # seed 42
python src/scripts/bench_image_embed.py --model fashionclip  # mỗi model 1 lệnh; --aggregate để gộp
python src/scripts/run_improvements.py --model fashionclip
python src/scripts/build_index.py --model fashionclip --out indexes/fashionclip --reuse-cache --tau-v 0.7039 --gate-tau 0.9
python src/scripts/baseline_e2e.py --agent visual-only --index-dir indexes/best
python src/scripts/tau_v_analysis.py && python src/scripts/make_tables.py && python src/scripts/fill_docs.py
python -m pytest -q
```

## 5. Kiểm thử
`cd 04_Khoa && python -m pytest -q` → **30 passed** (05/11/2026; DummyEmbedder + ảnh giả; có test đối chiếu `metrics.py` của Hoàng và kiểm tra tiêu chí nghiệm thu của `eval_visual.csv`).

## 6. Hạn chế cần nêu trong báo cáo
- Ảnh catalog 60×80, 1 ảnh/SP; truy vấn instance là **biến đổi tổng hợp**, không phải ảnh ngoài đời → số Recall lạc quan.
- Máy 2 CPU/7 GB **dùng chung** với 4 tác nhân, khởi động lại 2 lần trong lúc chạy; latency có nhiễu lớn; vài tiến trình bị OOM-kill và đã chạy lại.
- FashionCLIP/Marqo có nguy cơ đã thấy dữ liệu cùng nguồn Kaggle.
- Tất cả truy vấn/nhãn đánh giá do tác nhân sinh tự động, **chưa có người duyệt**.
