# repo: scripts/merge_rag_eval.py
"""Gộp results/rag_retrieval_eval.json + results/rag_e2e_eval.json → results/rag_eval.json (tóm tắt)."""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2] / "results"
ret = json.loads((R / "rag_retrieval_eval.json").read_text(encoding="utf-8"))
e2e = json.loads((R / "rag_e2e_eval.json").read_text(encoding="utf-8"))
out = {
    "data_version": ret["data_version"],
    "retrieval": {"n_answerable": ret["n_answerable"], "ghi_chu_nhan": ret.get("ghi_chu_nhan"),
                  "theo_product_id": {k: {m: v["theo_product_id"][m] for m in ("hit@1", "hit@5", "mrr@10", "latency_ms_p50")}
                                      for k, v in ret["results"].items()},
                  "toan_kho": {k: {m: v["toan_kho"][m] for m in ("hit@1", "hit@5", "mrr@10")} for k, v in ret["results"].items()},
                  "top1_score_auc": {k: v["top1_score_theo_product_id"]["auc_tach_answerable"]
                                     for k, v in ret["results"].items() if "top1_score_theo_product_id" in v},
                  "file": "results/rag_retrieval_eval.json"},
    "e2e": {"retriever": e2e["retriever"], "llm": e2e["llm_models_used"], "batch_size": e2e["batch_size"],
            "summary": e2e["summary"], "summary_truoc_sua_nhan": e2e.get("summary_truoc_sua_nhan"),
            "sua_nhan": e2e.get("sua_nhan"), "token_answer_tren_moi_cau": e2e["token_answer_tren_moi_cau"],
            "luu_y": e2e["luu_y"], "file": "results/rag_e2e_eval.json"},
}
(R / "rag_eval.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok")
