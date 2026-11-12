# repo: src/scripts/recall_by_transform.py
"""Tách Recall@5 (split test, tầng instance) theo HỌ biến đổi ảnh truy vấn – chỉ đọc file có sẵn, không chạy lại model.
Đầu vào: eval/eval_visual.csv (cột transform) + results/per_query/<model>.csv (kết quả benchmark US_22 đã đo).
Đầu ra:  results/recall_by_transform.csv
Chạy:    python src/scripts/recall_by_transform.py   (từ thư mục 04_Khoa)
Thêm bởi Tác nhân 2 để trả lời câu hỏi "model nào bền với ảnh giống ảnh người dùng (nền lạ, ảnh mờ)?"."""
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS = ["dinov2_s", "siglip_b16", "fashionclip", "clip_b32", "resnet50"]


def main() -> None:
    e = pd.read_csv(os.path.join(ROOT, "eval", "eval_visual.csv"))
    e["ho_bien_doi"] = e["transform"].astype(str).str.split("(").str[0]
    out, n = {}, None
    for m in MODELS:
        d = pd.read_csv(os.path.join(ROOT, "results", "per_query", f"{m}.csv")).merge(e[["query_id", "ho_bien_doi"]], on="query_id")
        d = d[(d["split"] == "test") & (d["tier"] == "instance")]
        out[m] = d.groupby("ho_bien_doi")["R@5"].mean().round(3)
        n = d.groupby("ho_bien_doi").size()
    df = pd.DataFrame(out)
    df["n_truy_van"] = n
    df.to_csv(os.path.join(ROOT, "results", "recall_by_transform.csv"))
    print(df.to_string())


if __name__ == "__main__":
    main()
