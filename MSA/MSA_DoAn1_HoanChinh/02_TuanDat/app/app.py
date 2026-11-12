# repo: app/app.py
"""US_43 – Giao diện demo Gradio: upload ảnh + chat + card kết quả + bảng so sánh + nhãn nguồn.

Chạy 1 lệnh:   python app/app.py            (MSA_API_URL=http://localhost:8000 mặc định)
Không có API:  MSA_UI_MOCK=1 python app/app.py   (hoặc tự rơi về mock khi API không phản hồi)
Headless test: MSA_UI_SMOKE=1 python app/app.py  (dựng giao diện, khởi động server 3 giây rồi tắt)

UI chỉ gọi API qua HTTP (hợp đồng 5.2, khớp src/msa/api/main.py):
  ảnh       → POST /search/image  multipart: file, session_id
  ≥ 2 mã SP → POST /compare       {product_ids}
  1 mã SP   → POST /qa            {question, product_id}  (đồng thời ghi nhớ làm "SP đang xem" của phiên)
  còn lại   → POST /chat          {message, session_id, product_id?}  – Router + Agent chọn luồng
Mỗi cuộc hội thoại trên UI có một session_id riêng (đổi khi bấm "Xoá hội thoại") để Agent nhớ kết quả vừa tìm
("so sánh đôi vừa tìm với đôi thứ 2") và SP đang xem ("giá bao nhiêu?").
"""
from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from components import CSS, ROUTES, render_response, validate_response  # noqa: E402

API_URL = os.environ.get("MSA_API_URL", "http://localhost:8000").rstrip("/")
IMAGE_ROOT = os.environ.get("MSA_IMAGE_ROOT") or os.environ.get("MSA_SHARED_DATA") or "/home/claude/work/shared_data"
FORCE_MOCK = os.environ.get("MSA_UI_MOCK") == "1"
TIMEOUT_S = float(os.environ.get("MSA_UI_TIMEOUT", 120))  # Gemini có lúc > 30 s (thử lại sau timeout)
PID_RX = re.compile(r"\b(fpi_\d+|shopee_\d+)\b")


def new_session() -> dict:
    """Trạng thái hội thoại phía UI: session_id gửi kèm mọi lời gọi + SP đang xem."""
    return {"session_id": f"ui-{uuid.uuid4().hex[:12]}", "product_id": None}


def system_message(text: str, code: str) -> dict:
    """Thông báo hệ thống (lỗi/quá hạn) – source="fallback" để UI gắn nhãn "Thông báo hệ thống", không phải "Từ dữ liệu cửa hàng"."""
    return {"route": "clarify", "confidence": 0.0, "source": "fallback", "items": [], "citations": [], "answer": text,
            "latency_ms": 0, "request_id": "", "error": {"code": code, "message": text}}


class Backend:
    """Gọi API thật. Không kết nối được → MockAPI kèm ghi chú (để demo không vỡ); API chậm/báo lỗi → thông báo hệ thống."""

    def __init__(self, url: str = API_URL, force_mock: bool = FORCE_MOCK, timeout: float = TIMEOUT_S):
        self.url, self.force_mock, self.timeout = url, force_mock, timeout
        self._mock = None

    @property
    def mock(self):
        if self._mock is None:
            from mock_api import MockAPI
            self._mock = MockAPI()
        return self._mock

    def _post(self, path: str, **kw) -> dict | None:
        """200 → body; lỗi HTTP → thông báo hệ thống (giữ câu giải thích của API); quá hạn → thông báo hệ thống;
        không kết nối được → None (gọi mock)."""
        if self.force_mock:
            return None
        try:
            r = httpx.post(f"{self.url}{path}", timeout=self.timeout, **kw)
        except (httpx.ConnectError, httpx.ConnectTimeout):  # API không chạy (Windows: cổng đóng → ConnectTimeout)
            return None
        except httpx.TimeoutException:  # đã kết nối nhưng API trả lời quá chậm
            return system_message(f"Hệ thống phản hồi quá {self.timeout:.0f} giây. Bạn thử lại sau ít phút nhé.", "timeout")
        except httpx.HTTPError:
            return None
        try:
            body = r.json()
        except ValueError:
            body = {}
        if r.status_code == 200 and isinstance(body, dict):
            return body
        msg = body.get("answer") if isinstance(body, dict) else None
        out = system_message(f"Hệ thống báo lỗi {r.status_code}: {msg or r.text[:200]}", f"http_{r.status_code}")
        if isinstance(body, dict) and body.get("route") in ROUTES:
            out["route"] = body["route"]
        return out

    def handle(self, text: str, image_bytes: bytes | None, session: dict | None = None) -> dict:
        """Định tuyến phía UI tối thiểu (xem docstring module). `session` (từ new_session()) được cập nhật tại chỗ."""
        text = (text or "").strip()
        pids = list(dict.fromkeys(PID_RX.findall(text)))
        sid = (session or {}).get("session_id")
        if image_bytes:
            data = {"session_id": sid} if sid else {}
            r = self._post("/search/image", files={"file": ("query.jpg", image_bytes, "image/jpeg")}, data=data)
            return r or self.mock.search_image(image_bytes)
        if len(pids) >= 2:
            return self._post("/compare", json={"product_ids": pids[:3]}) or self.mock.compare(pids[:3])
        if len(pids) == 1:
            if session is not None:
                session["product_id"] = pids[0]
            return self._post("/qa", json={"question": text, "product_id": pids[0]}) or self.mock.qa(text, pids[0])
        payload = {"message": text}
        if sid:
            payload["session_id"] = sid
        if session and session.get("product_id"):
            payload["product_id"] = session["product_id"]
        r = self._post("/chat", json=payload)
        if r:
            return r
        if re.search(r"tìm|kiếm|mua|có .* không|giày|dép|áo|quần|mũ|nón|túi|kính|thắt lưng", text.lower()):
            return self.mock.search_text(text)
        return self.mock.chat(text)


def build_ui(backend: Backend | None = None):
    import gradio as gr
    backend = backend or Backend()

    def on_submit(text, image, history, session):
        session = session or new_session()
        if not (text or "").strip() and image is None:
            return history, gr.update(), gr.update(), "", None, session
        img_bytes = None
        if image is not None:
            import io
            buf = io.BytesIO()
            image.convert("RGB").save(buf, format="JPEG")
            img_bytes = buf.getvalue()
        resp = backend.handle(text, img_bytes, session)
        errs = validate_response(resp)
        chat_md, cards_html, cmp_md = render_response(resp, IMAGE_ROOT)
        if resp.get("mock"):
            chat_md += "\n\n_(Đang dùng dữ liệu giả lập – API chưa chạy)_"
        if errs:
            chat_md += f"\n\n_Cảnh báo schema: {errs}_"
        history = (history or []) + [{"role": "user", "content": text or "(ảnh)"},
                                     {"role": "assistant", "content": chat_md}]
        return history, cards_html, cmp_md, "", None, session

    major = int(gr.__version__.split(".")[0])
    blocks_kw = {"title": "MSA – Trợ lý mua sắm thời trang"} | ({} if major >= 6 else {"css": CSS})
    with gr.Blocks(**blocks_kw) as demo:
        gr.Markdown("## Trợ lý mua sắm thời trang (Đồ án 1)\nTải ảnh để tìm sản phẩm giống, hoặc hỏi bằng tiếng Việt. "
                    "Nhãn **Từ dữ liệu cửa hàng** = trả lời từ catalog/review; **Trả lời bởi Gemini** = mô hình ngoài.")
        with gr.Row():
            with gr.Column(scale=3):
                chat = (gr.Chatbot(height=420, label="Hội thoại") if int(gr.__version__.split(".")[0]) >= 6
                        else gr.Chatbot(type="messages", height=420, label="Hội thoại"))
                txt = gr.Textbox(placeholder="VD: tìm giày sneaker trắng nam | so sánh fpi_1163 fpi_1164 | "
                                             "shopee_25814055660 quần có co giãn không?", label="Tin nhắn")
                with gr.Row():
                    send = gr.Button("Gửi", variant="primary")
                    clear = gr.Button("Xoá hội thoại")
            with gr.Column(scale=2):
                img = gr.Image(type="pil", label="Ảnh truy vấn (jpg/png/webp)")
        session = gr.State(None)  # mỗi cuộc hội thoại một session_id (tạo ở lượt đầu, xoá khi bấm "Xoá hội thoại")
        cards = gr.HTML(label="Kết quả")
        cmp = gr.Markdown()
        send.click(on_submit, [txt, img, chat, session], [chat, cards, cmp, txt, img, session])
        txt.submit(on_submit, [txt, img, chat, session], [chat, cards, cmp, txt, img, session])
        clear.click(lambda: ([], "", "", None), None, [chat, cards, cmp, session])
    demo._msa_launch_kw = {"css": CSS} if major >= 6 else {}  # Gradio 6 nhận css ở launch()
    return demo


if __name__ == "__main__":
    ui = build_ui()
    if os.environ.get("MSA_UI_SMOKE") == "1":
        import time
        ui.launch(server_name="127.0.0.1", server_port=int(os.environ.get("PORT", 7861)), prevent_thread_lock=True,
                  **getattr(ui, "_msa_launch_kw", {}))
        time.sleep(3)
        r = httpx.get(f"http://127.0.0.1:{os.environ.get('PORT', 7861)}/", timeout=10)
        print("SMOKE_HTTP_STATUS", r.status_code)
        ui.close()
    else:
        ui.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)), **getattr(ui, "_msa_launch_kw", {}))
