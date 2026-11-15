"""Trình chạy dự án cho CHAY_DU_AN.bat (Windows) – dùng được cả trên Linux/macOS.

    python scripts/chay_du_an.py check    # kiểm tra trước khi chạy (venv, .env, dữ liệu, index, cổng trống)
    python scripts/chay_du_an.py api      # API FastAPI  → http://127.0.0.1:8000 (Swagger: /docs)
    python scripts/chay_du_an.py wait     # chờ API sẵn sàng + nạp sẵn ảnh/RAG/router (KHÔNG gọi Gemini)
    python scripts/chay_du_an.py ui       # giao diện Gradio → http://127.0.0.1:7860
    python scripts/chay_du_an.py wait-ui  # chờ giao diện mở
    python scripts/chay_du_an.py stop     # tắt API + giao diện đang chiếm cổng 8000/7860 (và cửa sổ của chúng)

Biến môi trường đọc từ `.env` ở thư mục dự án (không in giá trị, bỏ cặp <...> bao ngoài giá trị).
MSA_LLM_MOCK=1 → Gemini giả lập (không tốn quota). Cổng: MSA_API_PORT (8000), MSA_UI_PORT (7860).
"""
from __future__ import annotations

import os
import socket
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_PORT = int(os.environ.get("MSA_API_PORT", 8000))
UI_PORT = int(os.environ.get("MSA_UI_PORT", 7860))
API_URL = f"http://127.0.0.1:{API_PORT}"
UI_URL = f"http://127.0.0.1:{UI_PORT}"


def load_env() -> list[str]:
    """Nạp .env (biến đã đặt sẵn trong môi trường được giữ nguyên) và bỏ <...> bao ngoài giá trị."""
    from msa.llm_gateway import load_env_file

    loaded = load_env_file(PROJECT / ".env")
    for k in loaded:
        v = os.environ[k].strip()
        if v.startswith("<") and v.endswith(">"):
            os.environ[k] = v[1:-1].strip()
    return loaded


class _Tee:
    """Ghi output vừa ra cửa sổ vừa vào runtime/logs/chay_<tên>.log (cửa sổ đóng rồi vẫn xem được lỗi)."""

    def __init__(self, stream, log):
        self.stream, self.log = stream, log

    def write(self, s):
        for out in (self.stream, self.log):
            try:
                out.write(s); out.flush()
            except Exception:  # cửa sổ đã đóng / mã hoá lạ – không làm chết tiến trình
                pass
        return len(s)

    def flush(self):
        for out in (self.stream, self.log):
            try:
                out.flush()
            except Exception:
                pass

    def __getattr__(self, name):
        return getattr(self.stream, name)


def tee_to_log(name: str) -> Path:
    log_dir = PROJECT / "runtime" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"chay_{name}.log"
    f = open(path, "w", encoding="utf-8")
    sys.stdout, sys.stderr = _Tee(sys.stdout, f), _Tee(sys.stderr, f)
    return path


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def check() -> int:
    loaded = load_env()
    errs, warns = [], []
    mock = os.environ.get("MSA_LLM_MOCK") == "1"
    if not (PROJECT / ".env").exists():
        warns.append("không có file .env – Gemini sẽ báo thiếu key (chạy CHAY_DU_AN.bat mock để dùng Gemini giả lập)")
    elif not mock and not os.environ.get("GEMINI_API_KEY"):
        warns.append(".env chưa có GEMINI_API_KEY – câu chào hỏi/ngoài phạm vi sẽ nhận câu trả lời dự phòng")
    shared = os.environ.get("MSA_SHARED_DATA")
    if not shared or not (Path(shared) / "catalog_fpi.parquet").exists():
        errs.append("chưa có dữ liệu: đặt MSA_SHARED_DATA trong .env và chạy 00_Chung/prep_shared_data.py")
    from msa import paths

    if not (paths.visual_index_dir() / "config.json").exists():
        errs.append(f"chưa build index ảnh ở {paths.visual_index_dir()} "
                    "(cd 04_Khoa && python src/scripts/build_index.py --model dinov2_s --out indexes/dinov2_s --tau-v 0.5923)")
    for port, name in ((API_PORT, "API"), (UI_PORT, "giao diện")):
        if port_busy(port):
            errs.append(f"cổng {port} ({name}) đang bận – có thể dự án đang chạy rồi; chạy DUNG_DU_AN.bat rồi thử lại")
    print("Biến đọc từ .env:", ", ".join(sorted(loaded)) or "(không có)",
          "| Gemini:", "GIẢ LẬP (MSA_LLM_MOCK=1)" if mock else os.environ.get("GEMINI_MODEL", "mặc định"))
    for w in warns:
        print("  [cảnh báo]", w)
    for e in errs:
        print("  [LỖI]", e)
    return 1 if errs else 0


def run_api() -> None:
    log = tee_to_log("api")
    load_env()
    import uvicorn

    print(f"API: {API_URL}  (Swagger: {API_URL}/docs) – đóng cửa sổ này để dừng API | log: {log}", flush=True)
    from msa.api import main as M

    if os.environ.get("MSA_PRELOAD", "1") != "0":
        preload(M.app.state.msa)
    uvicorn.run(M.app, host="127.0.0.1", port=API_PORT, log_level="info")


def preload(st) -> None:
    """Nạp torch, model ảnh, RAG và router NGAY trong luồng chính trước khi mở cổng.
    Lý do: (1) nạp lười trong luồng phụ của server lần đầu `import torch` có lúc làm tiến trình chết không để lại
    traceback trên Windows; (2) câu hỏi đầu tiên của người dùng không phải chờ. Không gọi Gemini."""
    def step(name, fn):
        t = time.time()
        try:
            fn()
            print(f"  nạp sẵn {name}: {time.time() - t:.1f} s", flush=True)
        except Exception as e:  # thiếu dữ liệu/index → API vẫn chạy, endpoint đó báo lỗi rõ ràng như cũ
            print(f"  [cảnh báo] chưa nạp được {name}: {type(e).__name__}: {str(e)[:150]}", flush=True)

    print("Đang nạp sẵn (lần đầu có thể mất vài phút)...", flush=True)
    step("torch", lambda: __import__("torch"))
    step("catalog", lambda: st.catalog)

    def visual():
        st.visual
        shared = Path(os.environ.get("MSA_SHARED_DATA", ""))
        img = next((shared / "fpi_images").glob("*.jpg"), None) if (shared / "fpi_images").is_dir() else None
        if img:
            st._tool_visual(img.read_bytes(), k=1)  # nạp trọng số model ảnh + FAISS

    step("model ảnh + index", visual)
    step("RAG (BM25 + e5)", lambda: st.qa.answer("khởi động", "__warmup__"))  # SP không tồn tại → không gọi Gemini
    step("router + agent", lambda: st.agent.handle(text="đôi thứ 2", image=None, session={}))  # → clarify


def run_ui() -> None:
    log = tee_to_log("ui")
    load_env()
    os.environ.setdefault("MSA_API_URL", API_URL)
    os.environ["PORT"] = str(UI_PORT)
    if os.environ.get("MSA_SHARED_DATA"):
        os.environ.setdefault("MSA_IMAGE_ROOT", os.environ["MSA_SHARED_DATA"])
    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    app_dir = PROJECT / "02_TuanDat"
    os.chdir(app_dir)
    sys.argv = [str(app_dir / "app" / "app.py")]
    print(f"Giao diện: {UI_URL} – đóng cửa sổ này để dừng giao diện | log: {log}", flush=True)
    import runpy
    import traceback

    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except BaseException:
        traceback.print_exc()
        raise


def _wait(url: str, timeout_s: float) -> bool:
    import httpx

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            if httpx.get(url, timeout=3).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(1)
    return False


def wait_api() -> int:
    """Chờ /health rồi nạp sẵn 3 phần nạp lười, để câu hỏi đầu tiên của người dùng không phải chờ.
    Cả 3 lời gọi đều không tới Gemini: /qa với mã SP không tồn tại (RAG nạp xong, từ chối vì không có dữ liệu),
    /search/image với 1 ảnh catalog, /chat câu mơ hồ trong phiên mới (router trả clarify)."""
    import httpx

    load_env()
    print("Đang chờ API khởi động...", flush=True)
    t_start = time.time()
    if not _wait(f"{API_URL}/health", 600):
        print("  [LỖI] API không phản hồi sau 600 s – xem cửa sổ 'MSA API' hoặc runtime/logs/chay_api.log")
        return 1
    print(f"  API đã nhận yêu cầu sau {time.time() - t_start:.0f} s", flush=True)
    print("Đang nạp sẵn model ảnh, RAG và router (lần đầu có thể mất vài phút)...", flush=True)
    t0 = time.time()
    try:
        httpx.post(f"{API_URL}/qa", json={"question": "khởi động", "product_id": "__warmup__"}, timeout=900)
        shared = Path(os.environ.get("MSA_SHARED_DATA", ""))
        img = next((shared / "fpi_images").glob("*.jpg"), None) if (shared / "fpi_images").is_dir() else None
        if img:
            httpx.post(f"{API_URL}/search/image", files={"file": (img.name, img.read_bytes(), "image/jpeg")}, timeout=900)
        httpx.post(f"{API_URL}/chat", json={"message": "đôi thứ 2", "session_id": f"warmup-{time.time_ns()}"}, timeout=900)
    except httpx.HTTPError as e:
        print("  [cảnh báo] nạp sẵn chưa xong:", type(e).__name__, "– câu hỏi đầu tiên sẽ chậm hơn")
    try:
        h = httpx.get(f"{API_URL}/health", timeout=10).json()
    except httpx.HTTPError:
        print("  [LỖI] API đã dừng trong lúc nạp – xem cửa sổ 'MSA API' hoặc runtime/logs/chay_api.log")
        return 1
    print(f"API sẵn sàng sau nạp sẵn {time.time() - t0:.0f} s | ảnh: {h.get('visual')} | hỏi đáp: {h.get('qa_backend')} "
          f"| Gemini: {h.get('llm')}", flush=True)
    return 0


def wait_ui() -> int:
    t0 = time.time()
    ok = _wait(UI_URL, 300)
    print(f"Giao diện sẵn sàng sau {time.time() - t0:.0f} s." if ok else
          "  [LỖI] giao diện không mở sau 300 s – xem cửa sổ 'MSA UI' hoặc runtime/logs/chay_ui.log")
    return 0 if ok else 1


def stop() -> int:
    """Tắt tiến trình đang nghe cổng API/UI. Nếu nó được mở từ cửa sổ cmd của CHAY_DU_AN.bat thì đóng luôn cửa sổ đó
    (tắt theo tiêu đề cửa sổ không dùng được với Windows Terminal nên tìm theo cổng)."""
    import psutil

    victims = {}
    for c in psutil.net_connections(kind="tcp"):
        if c.status == psutil.CONN_LISTEN and c.laddr and c.laddr.port in (API_PORT, UI_PORT) and c.pid:
            try:
                proc = psutil.Process(c.pid)
            except psutil.NoSuchProcess:
                continue
            top = proc
            for parent in proc.parents():  # đi lên tới cửa sổ cmd của chay_du_an (venv python → python gốc)
                if parent.name().lower() in ("python.exe", "python", "cmd.exe") and                         "chay_du_an" in " ".join(parent.cmdline()):
                    top = parent
                else:
                    break
            victims[top.pid] = (c.laddr.port, top)
    if not victims:
        print("Không có API/giao diện MSA nào đang chạy trên cổng", API_PORT, "hoặc", UI_PORT)
        return 0
    for port, top in victims.values():
        procs = top.children(recursive=True) + [top]
        for pr in procs:
            try:
                pr.kill()
            except psutil.Error:
                pass
        print(f"Đã tắt cổng {port} (pid {top.pid}, {len(procs)} tiến trình)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    actions = {"check": check, "api": run_api, "ui": run_ui, "wait": wait_api, "wait-ui": wait_ui, "stop": stop}
    if cmd not in actions:
        sys.exit(f"Lệnh không hợp lệ: {cmd}. Dùng: {', '.join(actions)}")
    sys.exit(actions[cmd]() or 0)
