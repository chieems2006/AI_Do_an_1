# repo: scripts/audit_taxonomy_samples.py
"""US_49 – Kiểm 30 mẫu/nguồn (seed 42) + nhóm ca khó. Kết luận đúng/sai do TÁC NHÂN AI (vai Trung) kiểm
bằng tiêu đề + ảnh 60×80 (FPI) / tiêu đề (ViMRHP, ảnh Shopee không tải được). Nhóm PHẢI kiểm lại bằng 2 người.

Chạy:  PYTHONPATH=src python scripts/audit_taxonomy_samples.py   (sau build_category_map.py)
"""
from __future__ import annotations

import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 42

# Ghi chú của người kiểm cho mẫu không hiển nhiên. Mẫu không có trong dict = "dung" (đúng, không mơ hồ).
NOTES_FPI = {
    "fpi_18405": ("mo_ho", "Skechers giày nâu: ảnh giống giày casual da; nhãn nguồn Casual Shoes -> sneaker theo quy ước"),
    "fpi_10029": ("mo_ho", "Áo nỉ có khoá kéo + mũ trùm: quy ước Sweatshirts/hoodie -> top (không phải outerwear)"),
    "fpi_27079": ("dung", "Nhãn nguồn Heels nhưng tiêu đề/ảnh là Flats; cả hai cùng lá heel_flat nên không sai"),
}
NOTES_VI = {
    "shopee_16686075502": ("mo_ho", "Áo ba lỗ kèm mút đệm ngực: sát ranh giới đồ lót; giữ top"),
    "shopee_18084830443": ("dung", "Hoodie không ghi 'áo khoác' -> top theo quy ước"),
}
# Ca khó chọn có chủ đích (không ngẫu nhiên) để kiểm luật – kết luận của tác nhân
HARD_CASES = [
    ("fpi_53440", "ADIDAS Men Red Pre L Boot Sports Shoes", "footwear/sneaker", "Ảnh là giày đá bóng; luật boot đã sửa để KHÔNG bắt (trước sửa: sai)"),
    ("fpi_5599", "Reebok Men's Trail Surpant Black Orange Shoe (nhãn Sandals)", "footwear/sandal", "Tiêu đề ghi Shoe nhưng ảnh là sandal -> nhãn nguồn đúng, tiêu đề sai"),
    ("fpi_12440", "Timberland Unisex Casual Black Skull Caps (nhãn Hat)", "headwear/beanie", "Nhãn Hat của FPI thực chất là mũ len -> beanie, không phải wide_brim"),
    ("shopee_18390665755", "Áo Khoác Lông 2 lớp ... có mũ tai gấu", "clothing/outerwear", "Áo khoác có mũ trùm: danh từ đầu 'áo khoác' thắng chữ 'mũ'"),
    ("vi:khan lau kinh", "Khăn lau kính Nano ...", "out_of_scope", "Danh từ đầu 'khăn' thắng chữ 'kính'"),
    ("vi:sandal cao got", "GIÀY SANDAL CAO GÓT NỮ ĐẾ NHỌN ...", "footwear/heel_flat", "Quy ước: giày dép có 'cao gót' -> heel_flat kể cả sandal"),
]


def _audit(df: pd.DataFrame, notes: dict, src: str, title_col: str, label_col: str) -> pd.DataFrame:
    s = df.sample(30, random_state=SEED).copy()
    out = pd.DataFrame(dict(
        source=src, product_id=s.product_id.values, source_label=s[label_col].values, title=s[title_col].values,
        mapped=(s.product_type + "/" + s.sub_category).values))
    out["ket_luan"] = [notes.get(pid, ("dung", ""))[0] for pid in out.product_id]
    out["ghi_chu"] = [notes.get(pid, ("dung", ""))[1] for pid in out.product_id]
    out["nguoi_kiem"] = "tac_nhan_AI(vai Trung) – CẦN 2 người kiểm lại"
    out["nguoi_kiem_2"] = ""
    return out


def main() -> None:
    cat = pd.read_parquet(os.path.join(ROOT, "data", "catalog_fpi_taxonomy_v1.parquet"))
    vi = pd.read_csv(os.path.join(ROOT, "data", "vimrhp_taxonomy_v1.csv"))
    a1 = _audit(cat, NOTES_FPI, "fashion_product_images", "title", "category")
    a2 = _audit(vi, NOTES_VI, "vimrhp_shopee", "title", "vimrhp_subcategory")
    a1.to_csv(os.path.join(ROOT, "data", "taxonomy_audit_fpi_30.csv"), index=False)
    a2.to_csv(os.path.join(ROOT, "data", "taxonomy_audit_vimrhp_30.csv"), index=False)
    summary = {}
    for name, a in [("fpi", a1), ("vimrhp", a2)]:
        summary[name] = dict(n=len(a), sai=int((a.ket_luan == "sai").sum()), mo_ho=int((a.ket_luan == "mo_ho").sum()),
                             dung=int((a.ket_luan == "dung").sum()), dat_tieu_chi_sai_le_3=bool((a.ket_luan == "sai").sum() <= 3),
                             phan_bo_mau=a.mapped.value_counts().to_dict())
    summary["hard_cases"] = [dict(id=i, title=t, ket_qua=m, ghi_chu=n) for i, t, m, n in HARD_CASES]
    summary["ghi_chu"] = ("Kiểm bởi tác nhân AI (vai Trung) bằng tiêu đề + ảnh 60×80 cho FPI, chỉ tiêu đề cho ViMRHP; "
                          "seed 42; CHƯA phải 2 người thật – nhóm phải kiểm lại (cột nguoi_kiem_2).")
    json.dump(summary, open(os.path.join(ROOT, "results", "taxonomy_audit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k in ("fpi", "vimrhp")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
