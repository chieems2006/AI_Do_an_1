"""Kiểm US_05: JSON Schema hợp lệ, ví dụ thật hợp lệ, dữ liệu thật validate."""
import glob
import json
import os

import pandas as pd
import pytest
from jsonschema import Draft202012Validator

from msa.data.schema_adapters import fpi_row_to_record, load_schema, validate_records, vimrhp_to_record

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data")


def test_schema_is_valid_draft_2020_12():
    s = load_schema()
    Draft202012Validator.check_schema(s)
    assert s["$schema"].endswith("2020-12/schema")
    assert {"product_type", "sub_category", "size_system", "view_type", "variant_id", "language"} <= set(s["required"])


def test_examples_one_per_type_valid():
    ex = sorted(glob.glob(os.path.join(ROOT, "src", "schema", "examples", "*.json")))
    if not ex:
        pytest.skip("chưa chạy scripts/validate_catalog.py")
    recs = [json.load(open(p, encoding="utf-8")) for p in ex]
    ok, bad, errs = validate_records(recs)
    assert bad == 0, errs
    assert {r["product_type"] for r in recs} == {"footwear", "clothing", "headwear", "accessory"}


def test_bad_record_rejected():
    rec = {"product_id": "fpi_1", "title": "x"}
    ok, bad, _ = validate_records([rec])
    assert bad == 1
    good = json.load(open(sorted(glob.glob(os.path.join(ROOT, "src", "schema", "examples", "fpi_*.json")))[0])) if glob.glob(os.path.join(ROOT, "src", "schema", "examples", "fpi_*.json")) else None
    if good:
        wrong = dict(good, product_type="footwear", sub_category="cap")  # lá không thuộc nhóm
        assert validate_records([wrong])[1] == 1


@pytest.mark.realdata
def test_real_catalog_taxonomy_v1_all_valid():
    p = os.path.join(ROOT, "data", "catalog_fpi_taxonomy_v1.parquet")
    if not os.path.exists(p):
        pytest.skip("thiếu catalog_fpi_taxonomy_v1")
    df = pd.read_parquet(p)
    df = df[df.taxonomy_action != "exclude"]
    ok, bad, errs = validate_records(fpi_row_to_record(r) for r in df.to_dict("records"))
    assert bad == 0, errs[:3]
    assert ok == len(df) and ok > 4500


@pytest.mark.realdata
def test_real_vimrhp_inscope_valid():
    p = os.path.join(SHARED, "vimrhp_fashion_products.jsonl")
    if not os.path.exists(p):
        pytest.skip("thiếu dữ liệu ViMRHP")
    recs = [vimrhp_to_record(json.loads(line)) for line in open(p, encoding="utf-8")]
    recs = [r for r in recs if r["product_type"] != "out_of_scope"]
    ok, bad, errs = validate_records(recs)
    assert bad == 0, errs[:3]
    assert all(r["price"] is None for r in recs)  # không bịa giá
