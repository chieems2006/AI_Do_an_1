# repo: src/msa/api/main.py
"""FastAPI backend cho demo MSA (US_30, US_32, US_37, US_38 + /qa, /chat qua interface) – Owner: Hoàng.

Chạy: MSA_CATALOG=data/processed/catalog_v1.parquet uvicorn msa.api.main:app --port 8000   (từ thư mục src/)
Mọi response theo mục 5.2: {route, confidence, source, answer, items, citations, latency_ms, request_id} (+ error khi lỗi).
Mỗi request ghi 1 dòng JSON vào logs/requests.jsonl (MSA_LOG_DIR).
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Protocol

import pandas as pd
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .compare import CompareError, compare_products
from .recommend import recommend
from .text_search import Filters, TextSearcher, parse_filters_vi
from .validation import MESSAGES, validate_image

ROOT = Path(__file__).resolve().parents[3]
TAU_V = float(os.environ.get("MSA_TAU_V", 0.25))
TAU_R = float(os.environ.get("MSA_TAU_R", 0.35))


# ---------------- Interface cho module của thành viên khác ----------------
class QAProto(Protocol):
    def answer(self, question: str, product_id: str | None) -> dict: ...  # {answer, citations, retrieval_score, refused}


class ReviewQAStub:
    """Stub /qa khi chưa ghép RAGPipeline của Chiến: TF-IDF trên review của sản phẩm, trả đoạn review liên quan nhất.
    retrieval_score < τ_r → refused ("chưa có thông tin"). KHÔNG dùng Gemini bù dữ kiện sản phẩm (quy tắc 5.4)."""

    def __init__(self, catalog: pd.DataFrame, tau_r: float = TAU_R):
        self.cat = catalog.set_index("product_id", drop=False)
        self.tau_r = tau_r

    def answer(self, question: str, product_id: str | None) -> dict:
        from sklearn.feature_extraction.text import TfidfVectorizer
        if not product_id or product_id not in self.cat.index:
            return {"answer": "Bạn muốn hỏi về sản phẩm nào? Hãy chọn một sản phẩm trước.", "citations": [],
                    "retrieval_score": 0.0, "refused": True}
        revs = [r for r in (self.cat.loc[product_id].reviews or []) if r.get("text")]
        if not revs:
            return {"answer": "Sản phẩm này chưa có thông tin đánh giá/mô tả để trả lời.", "citations": [],
                    "retrieval_score": 0.0, "refused": True}
        texts = [r["text"] for r in revs]
        v = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True).fit(texts + [question])
        s = (v.transform(texts) @ v.transform([question]).T).toarray().ravel()
        i = int(s.argmax())
        if s[i] < self.tau_r:
            return {"answer": "Chưa có thông tin về điều bạn hỏi trong dữ liệu của sản phẩm này.", "citations": [],
                    "retrieval_score": float(s[i]), "refused": True}
        return {"answer": f"Theo đánh giá của khách: \"{texts[i][:300]}\"", "retrieval_score": float(s[i]), "refused": False,
                "citations": [{"product_id": product_id, "field": "review", "chunk_id": str(revs[i].get("review_id"))}]}


def _load_qa(catalog: pd.DataFrame) -> QAProto:
    try:  # module của Chiến (mục 5.3)
        from msa.rag.pipeline import RAGPipeline  # type: ignore
        return RAGPipeline()
    except Exception:
        return ReviewQAStub(catalog)


def _load_agent():
    try:  # module của Trung (mục 5.3)
        from msa.agent.router import Agent  # type: ignore
        return Agent()
    except Exception:
        return None


# ---------------- Trạng thái ứng dụng (nạp lười) ----------------
class State:
    def __init__(self, catalog: pd.DataFrame | None = None, visual=None, text=None, qa=None, gateway=None,
                 log_dir: str | None = None, images_root: str | None = None):
        self._catalog, self._visual, self._text, self._qa, self._gateway = catalog, visual, text, qa, gateway
        self.log_dir = Path(log_dir or os.environ.get("MSA_LOG_DIR", ROOT / "logs"))
        self.images_root = Path(images_root or os.environ.get("MSA_IMAGES_ROOT", ROOT / "data"))
        self.lock = threading.Lock()

    @property
    def catalog(self) -> pd.DataFrame:
        if self._catalog is None:
            from msa.data.converters import read_catalog
            self._catalog = read_catalog(os.environ.get("MSA_CATALOG", ROOT / "data" / "processed" / "catalog_v1.parquet"))
        return self._catalog

    @property
    def visual(self):
        with self.lock:
            if self._visual is None:
                from .searchers import get_visual_searcher
                self._visual = get_visual_searcher(self.catalog, self.images_root,
                                                   os.environ.get("MSA_CACHE_DIR", ROOT / "results" / "cache"))
        return self._visual

    @property
    def text(self) -> TextSearcher:
        if self._text is None:
            self._text = TextSearcher(self.catalog)
        return self._text

    @property
    def qa(self) -> QAProto:
        if self._qa is None:
            self._qa = _load_qa(self.catalog)
        return self._qa

    @property
    def gateway(self):
        if self._gateway is None:
            from msa.llm_gateway import LLMGateway
            self._gateway = LLMGateway()
        return self._gateway


# ---------------- Schema request ----------------
class FiltersIn(BaseModel):
    product_type: str | None = None
    sub_category: str | None = None
    colors: list[str] = Field(default_factory=list)
    gender: str | None = None
    include_unisex: bool = True
    price_min: float | None = None
    price_max: float | None = None
    size: str | None = None


class TextSearchIn(BaseModel):
    query: str = ""
    k: int = Field(10, ge=1, le=50)
    filters: FiltersIn = Field(default_factory=FiltersIn)
    auto_filters: bool = False


class CompareIn(BaseModel):
    product_ids: list[str]
    needs: str | None = None  # US_39: nhu cầu để gợi ý (tuỳ chọn)
    use_llm: bool = False


class QAIn(BaseModel):
    question: str
    product_id: str | None = None


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None


def _resp(route: str, *, confidence: float = 0.0, source: str = "internal", answer: str = "", items=None, citations=None,
          error: dict | None = None, extra: dict | None = None) -> dict:
    d = {"route": route, "confidence": round(float(confidence), 4), "source": source, "answer": answer,
         "items": items or [], "citations": citations or [], "latency_ms": 0, "request_id": str(uuid.uuid4())}
    if error:
        d["error"] = error
    if extra:
        d.update(extra)
    return d


def create_app(state: State | None = None) -> FastAPI:
    st = state or State()
    app = FastAPI(title="MSA – AI Agent trợ lý mua sắm thời trang", version="0.1.0")
    app.state.msa = st

    def log(endpoint: str, body: dict, status: int, extra: dict | None = None) -> None:
        try:
            st.log_dir.mkdir(parents=True, exist_ok=True)
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "endpoint": endpoint, "status": status,
                   "request_id": body.get("request_id"), "route": body.get("route"), "source": body.get("source"),
                   "confidence": body.get("confidence"), "latency_ms": body.get("latency_ms"),
                   "n_items": len(body.get("items") or []), "error": (body.get("error") or {}).get("code"), **(extra or {})}
            with open(st.log_dir / "requests.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def finish(endpoint: str, t0: float, body: dict, status: int = 200, extra: dict | None = None) -> JSONResponse:
        body["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        log(endpoint, body, status, extra)
        return JSONResponse(body, status_code=status)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        path = request.url.path
        missing_file = path.endswith("/search/image") and any("file" in [str(x) for x in e.get("loc", [])] for e in exc.errors())
        err = {"code": "missing_file", "message": MESSAGES["missing_file"]} if missing_file else \
              {"code": "bad_request", "message": "Yêu cầu không hợp lệ: " + "; ".join(
                  f"{'.'.join(str(x) for x in e.get('loc', []))}: {e.get('msg')}" for e in exc.errors())[:300]}
        body = _resp(path.strip("/").replace("/", "_") or "unknown", error=err, answer=err["message"])
        return finish(path, time.perf_counter(), body, 422)

    @app.get("/health")
    def health():
        return {"status": "ok", "catalog_loaded": st._catalog is not None, "visual_loaded": st._visual is not None}

    @app.get("/products/{product_id}")
    def product(product_id: str):
        c = st.catalog
        r = c[c.product_id == product_id]
        if r.empty:
            return JSONResponse({"error": {"code": "not_found", "message": "Không tìm thấy sản phẩm."}}, 404)
        rec = r.iloc[0].to_dict()
        rec["reviews"] = (rec.get("reviews") or [])[:5]
        return JSONResponse(json.loads(json.dumps(rec, ensure_ascii=False, default=str)))

    @app.post("/search/image")
    async def search_image(file: UploadFile = File(...), k: int = Form(10), product_type: str | None = Form(None)):
        t0 = time.perf_counter()
        data = await file.read()
        chk = validate_image(data, file.filename, file.content_type)
        if not chk.ok:
            body = _resp("visual", answer=chk.message, error=chk.as_error())
            return finish("/search/image", t0, body, 400, {"bytes": chk.n_bytes})
        k = max(1, min(int(k), 50))
        res = st.visual.search(chk.image, k=k, product_type=product_type or None)
        top1 = res[0]["score"] if res else 0.0
        if not res or top1 < TAU_V:
            body = _resp("visual", confidence=top1, answer=MESSAGES["not_product"],
                         error={"code": "not_product", "message": MESSAGES["not_product"]})
            return finish("/search/image", t0, body, 200)
        cat = st.catalog.set_index("product_id", drop=False)
        items = []
        for r in res:
            p = cat.loc[r["product_id"]]
            items.append({"product_id": r["product_id"], "title": p.title, "price": None if pd.isna(p.price) else p.price,
                          "score": round(r["score"], 4), "image": (p.image_paths or [None])[0],
                          "product_type": r["product_type"], "sub_category": p.sub_category})
        body = _resp("visual", confidence=top1, answer=f"Tìm thấy {len(items)} sản phẩm tương tự.", items=items)
        return finish("/search/image", t0, body, 200, {"image_wh": [chk.width, chk.height]})

    @app.post("/search/text")
    def search_text(req: TextSearchIn):
        t0 = time.perf_counter()
        f = Filters(**req.filters.model_dump())
        if req.auto_filters:
            pf = parse_filters_vi(req.query)
            for k_, v in pf.__dict__.items():
                if getattr(f, k_) in (None, []) and v not in (None, []):
                    setattr(f, k_, v)
        items = st.text.search(req.query, k=req.k, filters=f)
        note = ""
        if not items and (f.price_min is not None or f.price_max is not None) and st.catalog.price.isna().all():
            note = " (Catalog hiện chưa có dữ liệu giá nên bộ lọc giá không trả được kết quả.)"
        ans = f"Tìm thấy {len(items)} sản phẩm phù hợp." if items else "Không có sản phẩm nào khớp bộ lọc." + note
        body = _resp("search", confidence=items[0]["score"] if items else 0.0, answer=ans, items=items,
                     extra={"applied_filters": f.active()})
        return finish("/search/text", t0, body)

    @app.post("/compare")
    def compare(req: CompareIn):
        t0 = time.perf_counter()
        try:
            table = compare_products(st.catalog, req.product_ids)
        except CompareError as e:
            return finish("/compare", t0, _resp("compare", answer=e.message, error={"code": e.code, "message": e.message}), 400)
        extra = {"table": table}
        ans = f"Bảng so sánh {len(table['columns'])} sản phẩm ({table['product_type']})."
        source = "internal"
        if req.needs:
            rec = recommend(table, req.needs, gateway=st.gateway if req.use_llm else None)
            extra["recommendation"] = {k: v for k, v in rec.items() if k != "rule"}
            ans += " " + rec["answer"]
            source = rec["source"]
        items = [{"product_id": p, "title": next(r for r in table["rows"] if r["key"] == "title")["values"][p]}
                 for p in table["columns"]]
        return finish("/compare", t0, _resp("compare", confidence=1.0, source=source, answer=ans, items=items, extra=extra))

    @app.post("/qa")
    def qa(req: QAIn):
        t0 = time.perf_counter()
        r = st.qa.answer(req.question, req.product_id)
        body = _resp("qa", confidence=r.get("retrieval_score", 0.0), answer=r["answer"], citations=r.get("citations"),
                     extra={"refused": r.get("refused", False)})
        return finish("/qa", t0, body)

    @app.post("/chat")
    def chat(req: ChatIn):
        t0 = time.perf_counter()
        agent = _load_agent()
        if agent is not None:  # Agent của Trung quyết định route và gọi công cụ
            r = agent.handle(text=req.message, image=None, session={"session_id": req.session_id})
            body = _resp(r.get("route", "clarify"), confidence=r.get("confidence", 0), source=r.get("source", "internal"),
                         answer=r.get("answer", ""), items=r.get("items"), citations=r.get("citations"))
            return finish("/chat", t0, body)
        g = st.gateway.generate(req.message, system=CHAT_SYSTEM)
        body = _resp("gemini_chitchat", confidence=0.0, source=g["source"], answer=g["answer"],
                     extra={"llm": {k: g.get(k) for k in ("cached", "tokens_in", "tokens_out", "tokens_thinking", "error", "model")}})
        return finish("/chat", t0, body)

    return app


CHAT_SYSTEM = ("Bạn là trợ lý mua sắm thời trang của cửa hàng (giày dép, quần áo, mũ, phụ kiện). Trả lời tiếng Việt, ngắn gọn. "
               "KHÔNG nêu giá, size, tồn kho hay thông số sản phẩm cụ thể; nếu được hỏi, mời khách dùng chức năng tìm kiếm/so sánh.")

app = create_app()
