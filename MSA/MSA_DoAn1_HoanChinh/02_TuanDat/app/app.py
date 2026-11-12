# repo: app/app.py
"""US_43 – Giao diện demo Gradio: upload ảnh + chat + card kết quả + bảng so sánh + nhãn nguồn.

Chạy 1 lệnh:   python app/app.py            (MSA_API_URL=http://localhost:8000 mặc định)
Không có API:  MSA_UI_MOCK=1 python app/app.py   (hoặc tự rơi về mock khi API không phản hồi)
Headless test: MSA_UI_SMOKE=1 python app/app.py  (dựng giao diện, khởi động server 3 giây rồi tắt)

UI chỉ gọi API qua HTTP (hợp đồng 5.2): /search/image, /search/text, /compare, /qa, /chat.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from components import CSS, render_response, validate_response  # noqa: E402

API_URL = os.environ.get("MSA_API_URL", "http://localhost:8000").rstrip("/")
IMAGE_ROOT = os.environ.get("MSA_IMAGE_ROOT", "/home/claude/work/shared_data")
FORCE_MOCK = os.environ.get("MSA_UI_MOCK") == "1"
PID_RX = re.compile(r"\b(fpi_\d+|shopee_\d+)\b")


class Backend:
    """Gọi API thật; lỗi kết nối/timeout → dùng MockAPI và ghi chú (để demo không vỡ)."""

    def __init__(self, url: str = API_URL, force_mock: bool = FORCE_MOCK, timeout: float = 30.0):
        self.url, self.force_mock, self.timeout = url, force_mock, timeout
        self._mock = None

    @property
    def mock(self):
        if self._mock is None:
            from mock_api import MockAPI
            self._mock = MockAPI()
        return self._mock

    def _post(self, path: str, **kw) -> dict | None:
        if self.force_mock:
            return None
        try:
            r = httpx.post(f"{self.url}{path}", timeout=self.timeout, **kw)
            if r.status_code == 200:
                return r.json()
            return {"route": "clarify", "confidence": 0.0, "source": "internal", "items": [], "citations": [],
                    "answer": f"Hệ thống báo lỗi {r.status_code}: {r.text[:200]}", "latency_ms": 0, "request_id": ""}
        except httpx.HTTPError:
            return None

    def handle(self, text: str, image_bytes: bytes | None) -> dict:
        """Định tuyến phía UI tối thiểu: có ảnh → /search/image; có ≥2 mã SP → /compare; 1 mã → /qa; còn lại → /chat."""
        text = (text or "").strip()
        pids = PID_RX.findall(text)
        if image_bytes:
            r = self._post("/search/image", files={"image": ("query.jpg", image_bytes, "image/jpeg")},
                           data={"text": text})
            return r or self.mock.search_image(image_bytes)
        if len(pids) >= 2:
            return self._post("/compare", json={"product_ids": pids[:3]}) or self.mock.compare(pids[:3])
        if len(pids) == 1:
            return self._post("/qa", json={"question": text, "product_id": pids[0]}) or self.mock.qa(text, pids[0])
        r = self._post("/chat", json={"text": text})
        if r:
            return r
        if re.search(r"tìm|kiếm|mua|có .* không|giày|dép|áo|quần|mũ|nón|túi|kính|thắt lưng", text.lower()):
            return self.mock.search_text(text)
        return self.mock.chat(text)


def build_ui(backend: Backend | None = None):
    import gradio as gr
    backend = backend or Backend()

    def on_submit(text, image, history):
        img_bytes = None
        if image is not None:
            import io
            buf = io.BytesIO()
            image.convert("RGB").save(buf, format="JPEG")
            img_bytes = buf.getvalue()
        resp = backend.handle(text, img_bytes)
        errs = validate_response(resp)
        chat_md, cards_html, cmp_md = render_response(resp, IMAGE_ROOT)
        if resp.get("mock"):
            chat_md += "\n\n_(Đang dùng dữ liệu giả lập – API chưa chạy)_"
        if errs:
            chat_md += f"\n\n_Cảnh báo schema: {errs}_"
        history = (history or []) + [{"role": "user", "content": text or "(ảnh)"},
                                     {"role": "assistant", "content": chat_md}]
        return history, cards_html, cmp_md, "", None

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
        cards = gr.HTML(label="Kết quả")
        cmp = gr.Markdown()
        send.click(on_submit, [txt, img, chat], [chat, cards, cmp, txt, img])
        txt.submit(on_submit, [txt, img, chat], [chat, cards, cmp, txt, img])
        clear.click(lambda: ([], "", ""), None, [chat, cards, cmp])
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
