# repo: src/msa/api/main.py
"""FastAPI backend cho demo MSA (US_30, US_32, US_37, US_38 + /qa, /chat) – Owner: Hoàng.

Ghép module theo hợp đồng mục 5.3 (00_Chung/00_THIET_KE_CHUNG.md):
- /search/image → `msa.search.visual.VisualSearcher` (Khoa) trên index DINOv2-S, τ_v theo tau_v_analysis.json;
- /qa          → `msa.rag.pipeline.RAGPipeline` (Chiến), LLM = LLMGateway;
- /chat        → `msa.agent.router.Router` + `Agent` (Trung), công cụ nội bộ = 4 luồng trên, nhánh Gemini = LLMGateway;
- Gemini chỉ đi qua `msa.llm_gateway.LLMGateway` (Hoàng): cache, retry, source="gemini"|"cache"|"fallback".

Chạy (từ thư mục gốc đồ án): uvicorn msa.api.main:app --app-dir src --port 8000
Biến môi trường: MSA_SHARED_DATA, MSA_CATALOG, MSA_IMAGES_ROOT, MSA_VISUAL_INDEX, MSA_VISUAL_BACKEND (khoa|clip),
MSA_QA_BACKEND (rag|stub), MSA_RAG_DENSE (1|0), MSA_RUNTIME_DIR, MSA_LOG_DIR, MSA_LLM_MOCK, GEMINI_API_KEY.
Mọi response theo mục 5.2: {route, confidence, source, answer, items, citations, latency_ms, request_id} (+ error khi lỗi).
Mỗi request ghi 1 dòng JSON vào <MSA_LOG_DIR>/requests.jsonl.
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

from msa import paths

TAU_V = float(os.environ.get("MSA_TAU_V", 0.25))  # chỉ dùng khi searcher không mang τ_v riêng (vd. searcher giả trong test)
TAU_R = float(os.environ.get("MSA_TAU_R", 0.35))  # ngưỡng của ReviewQAStub
RAG_TAU_R = 0.0  # τ_r thực tế của RAG (Chiến, QUYET_DINH_CAN_CHOT §5.3 cập nhật): từ chối dựa vào LLM + guard trích dẫn
MAX_SESSIONS = 1000


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


def _load_qa(catalog: pd.DataFrame, llm) -> tuple[QAProto, str]:
    """QA backend theo MSA_QA_BACKEND: 'rag' (mặc định – RAGPipeline của Chiến) | 'stub' (ReviewQAStub, cho test).
    Nếu dựng RAG lỗi (thiếu dữ liệu/model) thì hạ về stub và ghi lý do vào /health – không âm thầm."""
    if os.environ.get("MSA_QA_BACKEND", "rag") == "stub":
        return ReviewQAStub(catalog), "stub"
    try:
        from msa.rag.pipeline import build_default_pipeline
        dense = os.environ.get("MSA_RAG_DENSE", "1") != "0"
        return build_default_pipeline(llm=llm, use_dense=dense, tau_r=RAG_TAU_R), "rag" + ("+dense" if dense else "")
    except Exception as e:  # noqa: BLE001
        return ReviewQAStub(catalog), f"stub (RAG lỗi: {type(e).__name__}: {str(e)[:160]})"


def _default_catalog() -> tuple[Path, Path]:
    """(catalog, images_root): MSA_CATALOG/MSA_IMAGES_ROOT nếu đặt; không thì Data v1 của Hoàng nếu đã build;
    không thì catalog dùng chung shared_data v1 (cùng catalog với index ảnh của Khoa)."""
    if os.environ.get("MSA_CATALOG"):
        return Path(os.environ["MSA_CATALOG"]), paths.env_path("MSA_IMAGES_ROOT", Path(os.environ["MSA_CATALOG"]).parent)
    v1 = paths.HOANG / "data" / "processed" / "catalog_v1.parquet"
    if v1.exists():
        return v1, paths.env_path("MSA_IMAGES_ROOT", paths.HOANG / "data")
    return paths.shared_data() / "catalog_fpi.parquet", paths.env_path("MSA_IMAGES_ROOT", paths.shared_data())


# ---------------- Trạng thái ứng dụng (nạp lười) ----------------
class State:
    def __init__(self, catalog: pd.DataFrame | None = None, visual=None, text=None, qa=None, gateway=None,
                 log_dir: str | None = None, images_root: str | None = None, agent=None):
        self._catalog, self._visual, self._text, self._qa, self._gateway = catalog, visual, text, qa, gateway
        self._agent = agent
        self.log_dir = Path(log_dir or os.environ.get("MSA_LOG_DIR") or paths.runtime_dir() / "logs")
        cat_path, img_root = _default_catalog()
        self.catalog_path = cat_path
        self.images_root = Path(images_root) if images_root else img_root
        self.qa_backend = "injected" if qa is not None else None
        self.visual_error: str | None = None
        self.sessions: dict[str, dict] = {}
        self.lock = threading.RLock()

    @property
    def catalog(self) -> pd.DataFrame:
        if self._catalog is None:
            from msa.data.converters import read_catalog
            self._catalog = read_catalog(self.catalog_path)
        return self._catalog

    @property
    def visual(self):
        with self.lock:
            if self._visual is None:
                from .searchers import get_visual_searcher
                try:
                    self._visual = get_visual_searcher(self.catalog, self.images_root,
                                                       paths.env_path("MSA_CACHE_DIR", paths.runtime_dir() / "cache"))
                except FileNotFoundError as e:
                    self.visual_error = str(e)
                    raise
        return self._visual

    @property
    def visual_tau_v(self) -> float:
        """τ_v của searcher đang dùng; searcher không mang τ_v riêng (searcher giả) thì dùng TAU_V của module."""
        tau = getattr(self.visual, "tau_v", None)
        return TAU_V if tau is None else float(tau)

    @property
    def text(self) -> TextSearcher:
        if self._text is None:
            self._text = TextSearcher(self.catalog)
        return self._text

    @property
    def qa(self) -> QAProto:
        with self.lock:
            if self._qa is None:
                self._qa, self.qa_backend = _load_qa(self.catalog, self.gateway)
        return self._qa

    @property
    def gateway(self):
        with self.lock:
            if self._gateway is None:
                from msa.llm_gateway import LLMGateway
                cache = os.environ.get("MSA_LLM_CACHE_PATH") or str(paths.runtime_dir() / "cache" / "llm_cache.sqlite")
                self._gateway = LLMGateway(cache_path=cache, log_path=str(self.log_dir / "llm_calls.jsonl"))
        return self._gateway

    @property
    def agent(self):
        """Router + Agent của Trung; công cụ nội bộ nạp lười (câu chào không làm nạp model ảnh/RAG)."""
        with self.lock:
            if self._agent is None:
                from msa.agent.router import Agent, Router, Tools
                tools = Tools(visual=self._tool_visual, qa=lambda q, pid=None: self.qa.answer(q, pid),
                              search=self._tool_search, compare=self._tool_compare)
                # τ_v đã áp trong _tool_visual (theo searcher); τ_r của RAG = 0 → Agent không chặn thêm.
                self._agent = Agent(router=Router(), tools=tools, llm=self.gateway, tau_v=0.0, tau_r=RAG_TAU_R)
        return self._agent

    def session(self, session_id: str | None) -> dict:
        """Ngữ cảnh phiên cho Router (current_product_id, last_results, clarify_count); không có id → phiên tạm."""
        if not session_id:
            return {}
        with self.lock:
            if session_id not in self.sessions and len(self.sessions) >= MAX_SESSIONS:
                self.sessions.pop(next(iter(self.sessions)))
            return self.sessions.setdefault(session_id, {})

    # ---- công cụ nội bộ cho Agent (mục 5.3)
    def _tool_visual(self, image, k: int = 10) -> list[dict]:
        img = validate_image(image, "chat.jpg", None).image if isinstance(image, (bytes, bytearray)) else image
        res = self.visual.search(img, k=k)
        return res if res and res[0]["score"] >= self.visual_tau_v else []

    def _tool_search(self, text: str) -> list[dict]:
        return self.text.search(text, k=10, filters=parse_filters_vi(text))

    def _tool_compare(self, product_ids: list[str]) -> dict:
        try:
            table = compare_products(self.catalog, product_ids)
        except CompareError as e:
            return {"answer": e.message, "items": []}
        titles = next(r for r in table["rows"] if r["key"] == "title")["values"]
        return {"answer": f"Bảng so sánh {len(table['columns'])} sản phẩm ({table['product_type']}).",
                "items": [{"product_id": p, "title": titles[p]} for p in table["columns"]], "table": table}


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
    product_id: str | None = None  # SP người dùng đang xem (ngữ cảnh QA cho Router – current_product_id)


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
        out = {"status": "ok", "catalog_loaded": st._catalog is not None, "visual_loaded": st._visual is not None,
               "qa_backend": st.qa_backend, "agent_loaded": st._agent is not None}
        if st._visual is not None:
            out["visual"] = {"backend": type(st._visual).__name__, "tau_v": st.visual_tau_v}
        if st.visual_error:
            out["visual_error"] = st.visual_error
        if st._gateway is not None:
            out["llm"] = {"model": st._gateway.model, "mock": st._gateway.mock}
        return out

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
    async def search_image(file: UploadFile = File(...), k: int = Form(10), product_type: str | None = Form(None),
                           session_id: str | None = Form(None)):
        """session_id (tuỳ chọn): lưu kết quả vào last_results của phiên /chat → 'so sánh đôi vừa tìm với đôi thứ 2'."""
        t0 = time.perf_counter()
        data = await file.read()
        chk = validate_image(data, file.filename, file.content_type)
        if not chk.ok:
            body = _resp("visual", answer=chk.message, error=chk.as_error())
            return finish("/search/image", t0, body, 400, {"bytes": chk.n_bytes})
        k = max(1, min(int(k), 50))
        try:
            searcher, tau_v = st.visual, st.visual_tau_v
        except FileNotFoundError as e:  # chưa build index ảnh
            err = {"code": "visual_unavailable", "message": "Tìm bằng ảnh chưa sẵn sàng (chưa có index)."}
            return finish("/search/image", t0, _resp("visual", answer=err["message"], error=err), 503, {"detail": str(e)[:200]})
        res = searcher.search(chk.image, k=k, product_type=product_type or None)
        top1 = res[0]["score"] if res else 0.0
        if not res or top1 < tau_v:
            body = _resp("visual", confidence=top1, answer=MESSAGES["not_product"],
                         error={"code": "not_product", "message": MESSAGES["not_product"]}, extra={"tau_v": tau_v})
            return finish("/search/image", t0, body, 200)
        cat = st.catalog.set_index("product_id", drop=False)
        items = []
        for r in res:
            if r["product_id"] in cat.index:
                p = cat.loc[r["product_id"]]
                title, sub = p.title, p.sub_category
                price = None if pd.isna(p.price) else p.price
                image = (p.image_paths or [None])[0]
            else:  # index build trên catalog khác catalog API đang nạp → dùng meta của index
                title, sub, price, image = r.get("title"), r.get("sub_category"), None, r.get("image")
            items.append({"product_id": r["product_id"], "title": title, "price": price, "score": round(r["score"], 4),
                          "image": image, "product_type": r["product_type"], "sub_category": sub})
        extra = {"tau_v": tau_v}
        if session_id:
            st.session(session_id)["last_results"] = [i["product_id"] for i in items]
            extra["session_id"] = session_id
        body = _resp("visual", confidence=top1, answer=f"Tìm thấy {len(items)} sản phẩm tương tự.", items=items,
                     extra=extra)
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
        extra = {"refused": r.get("refused", False)}
        if r.get("llm_error"):
            extra["llm_error"] = r["llm_error"]
        body = _resp("qa", confidence=r.get("retrieval_score", 0.0), source=r.get("source", "internal"), answer=r["answer"],
                     citations=r.get("citations"), extra=extra)
        return finish("/qa", t0, body)

    @app.post("/chat")
    def chat(req: ChatIn):
        """Router + Agent của Trung chọn route và gọi công cụ nội bộ; chitchat/ngoài phạm vi đi Gemini qua LLMGateway."""
        t0 = time.perf_counter()
        session = st.session(req.session_id)
        if req.product_id:
            session["current_product_id"] = req.product_id
        r = st.agent.handle(text=req.message, image=None, session=session)
        extra = {k: r[k] for k in ("store_fact_flags", "tokens_in", "tokens_out") if r.get(k) not in (None, [])}
        if r.get("error"):  # lỗi Gemini (chuỗi) – không đè trường `error` {code, message} của hợp đồng 5.2
            extra["llm_error"] = r["error"]
        if req.session_id:
            extra["session_id"] = req.session_id
        body = _resp(r.get("route", "clarify"), confidence=r.get("confidence", 0), source=r.get("source", "internal"),
                     answer=r.get("answer", ""), items=r.get("items"), citations=r.get("citations"), extra=extra)
        return finish("/chat", t0, body)

    return app


app = create_app()
