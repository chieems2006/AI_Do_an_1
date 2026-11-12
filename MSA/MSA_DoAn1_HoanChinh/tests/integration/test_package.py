"""Kiểm cấu trúc package msa chung: một client Gemini duy nhất, module đặt đúng vị trí "# repo:", tài nguyên tồn tại."""
from __future__ import annotations

import importlib
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "msa"


def test_only_llm_gateway_talks_to_gemini():
    """Không để mỗi người một client Gemini: chỉ llm_gateway.py gọi REST Gemini."""
    hits = sorted(str(p.relative_to(SRC)) for p in SRC.rglob("*.py")
                  if re.search(r"generativelanguage\.googleapis\.com|x-goog-api-key", p.read_text(encoding="utf-8")))
    assert hits == ["llm_gateway.py"], hits


def test_repo_headers_match_location():
    """Mỗi module mang dòng '# repo: src/msa/...' đúng với vị trí thật của nó trong package."""
    wrong = []
    for p in SRC.rglob("*.py"):
        if p.name == "__init__.py":
            continue
        first = p.read_text(encoding="utf-8").splitlines()[0]
        want = "src/msa/" + p.relative_to(SRC).as_posix()
        if not first.startswith(f"# repo: {want}"):
            wrong.append((want, first[:60]))
    assert not wrong, wrong


def test_all_modules_import():
    """Mọi module của package import được (không còn phụ thuộc đường dẫn cũ trong folder thành viên)."""
    mods = ["msa." + ".".join(p.relative_to(SRC).with_suffix("").parts) for p in sorted(SRC.rglob("*.py"))
            if p.name != "__init__.py"]
    for mod in mods:
        importlib.import_module(mod)
    assert {"msa.api.main", "msa.agent.router", "msa.rag.pipeline", "msa.search.visual", "msa.llm_gateway"} <= set(mods)


def test_resources_owned_by_members_exist():
    from msa import paths
    for f in (paths.SCHEMA_PATH, paths.ROUTER_PROTOS, paths.RAG_PROMPT, paths.FALLBACK_PROMPT,
              paths.HALLUCINATION_CHECKER, paths.TAU_V_ANALYSIS):
        assert f.exists(), f


def test_tau_v_rule_matches_decision_c():
    """τ_v lấy theo quy tắc 'max OOD val + 0,01' (QUYET_DINH_CAN_CHOT mục C) – khớp số đã báo cáo."""
    from msa.api.searchers import tau_v_from_analysis
    assert tau_v_from_analysis("dinov2_s") == 0.5923
    assert tau_v_from_analysis("fashionclip") == 0.7039
    assert tau_v_from_analysis("khong_co_model") is None


def test_default_visual_index_is_dinov2_s(monkeypatch):
    from msa import paths
    monkeypatch.delenv("MSA_VISUAL_INDEX", raising=False)
    assert paths.visual_index_dir() == paths.KHOA / "indexes" / "dinov2_s"
