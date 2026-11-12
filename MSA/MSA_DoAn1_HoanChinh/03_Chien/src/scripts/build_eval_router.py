# repo: scripts/build_eval_router.py
"""US_16 – Sinh và kiểm tra eval/eval_router.jsonl (bộ câu định tuyến có nhãn route).

Câu do tác nhân (Chiến – AI) viết tay, dùng tên sản phẩm THẬT từ ViMRHP.
Chưa có người thật duyệt: annotator_1/annotator_2 để trống cho nhóm điền.

Dùng:
    python src/scripts/build_eval_router.py            # ghi file
    python src/scripts/build_eval_router.py --check    # chỉ kiểm ràng buộc
"""
from __future__ import annotations
import os

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "eval_router.jsonl"
ROUTES = {"visual", "qa", "search", "compare", "gemini_chitchat", "gemini_ood", "clarify"}
FIELDS = ["id", "text", "has_image", "route", "product_id", "note", "origin", "annotator_1", "annotator_2"]

# (text, has_image, route, product_id, note)
ITEMS: list[tuple[str, bool, str, str | None, str]] = [
    # ---------- visual (có ảnh) ----------
    ("tìm giúp mình đôi giày giống trong ảnh này", True, "visual", None, "có dấu, chuẩn"),
    ("có mẫu nào giống cái áo này ko shop", True, "visual", None, "teencode 'ko'"),
    ("tim ao giong hinh", True, "visual", None, "không dấu"),
    ("Mình chụp được cái túi này ngoài đường, shop có bán không?", True, "visual", None, "ảnh ngoài đời"),
    ("kiếm giùm mẫu dép tương tự ảnh, size 39", True, "visual", None, "ảnh + bộ lọc size → vẫn visual"),
    ("cái mũ trong hình mua ở đâu v", True, "visual", None, "teencode 'v'"),
    ("Tìm sản phẩm tương tự như ảnh nhưng màu đen", True, "visual", None, "ảnh + bộ lọc màu"),
    ("hàng giống ảnh này mà rẻ hơn có ko", True, "visual", None, "ảnh + ràng buộc giá"),
    ("", True, "visual", None, "chỉ gửi ảnh, không kèm chữ"),
    ("sp nay co mau tuong tu k", True, "visual", None, "không dấu + viết tắt 'sp', 'k'"),
    ("đôi sandal này là hãng gì, tìm mẫu y chang", True, "visual", None, "ảnh, hỏi nhận diện"),
    # ---------- qa (hỏi về 1 SP cụ thể) ----------
    ("Áo Khoác Gió Nữ 2 Lớp Cao Cấp Hidoli có chống nước thật không?", False, "qa", "shopee_17778903479", "tên SP thật ViMRHP"),
    ("Áo Babytee Y2K Cổ Ôm 100% Cotton giặt có bị co không?", False, "qa", "shopee_25530152479", "chất liệu/độ bền"),
    ("dép bánh mì bản vân nhám đi có êm ko, có trơn ko", False, "qa", "shopee_22037380049", "teencode"),
    ("Giày cao gót đế vuông thắt nơ 7 phân Luvia đi lâu có đau chân không?", False, "qa", "shopee_18344928398", "độ êm giày"),
    ("ao hoodie KANG form rong, cao 1m7 nang 65kg mac size gi", False, "qa", "shopee_23913613670", "không dấu, size áo"),
    ("Áo Sơ Mi Kẻ Sọc Tay Dài Oxford form rộng có nhăn nhiều không?", False, "qa", "shopee_25980881072", "chất liệu"),
    ("kính cận gọng trong suốt có chống ánh sáng xanh thật k", False, "qa", "shopee_23261536758", "phụ kiện – kính"),
    ("Dây chuyền Lovito họa tiết hoa đeo lâu có bị đen không?", False, "qa", "shopee_23185215188", "phụ kiện – độ bền"),
    ("Tất cổ cao nữ trơn 3 màu có dày không ạ", False, "qa", "shopee_16973326316", "phụ kiện"),
    ("Dép YZ Slide Vân Nhám size có chuẩn không, chân 40 lấy size mấy", False, "qa", "shopee_22736671626", "size giày"),
    ("Áo cardigan nữ AK13 mặc lâu có xù lông không?", False, "qa", "shopee_20485042859", "độ bền vải"),
    ("Giày búp bê Lolita đế 5 phân có bị đau gót không ạ", False, "qa", "shopee_2140323126", "giày nữ"),
    ("quần ống suông chữ X cạp cao freesize thì bn kg mặc vừa", False, "qa", "shopee_24270726044", "size quần freesize, teencode 'bn'"),
    ("áo này giặt máy được không?", False, "qa", "shopee_9221031855", "đại từ 'này' – product_id lấy từ session (Hoodie SO PHỐI 2 MÀU)"),
    ("còn size 40 không shop?", False, "qa", "shopee_22881386214", "hỏi tồn kho trong session (Dép Đúc răng cưa) – QA phải trả 'chưa có thông tin', KHÔNG chuyển Gemini"),
    # ---------- search (tìm theo văn bản + bộ lọc) ----------
    ("tìm áo khoác gió nữ chống nước dưới 200k", False, "search", None, "bộ lọc giá"),
    ("dep quai ngang nam size 42 mau den", False, "search", None, "không dấu, lọc size+màu"),
    ("có giày cao gót 5 phân màu trắng không", False, "search", None, "lọc màu + độ cao gót"),
    ("Cho mình xem mấy mẫu áo hoodie form rộng nam nữ", False, "search", None, "chuẩn"),
    ("tim ao chong nang toan than", False, "search", None, "không dấu"),
    ("quần ống rộng nữ lưng cao, giá dưới 150 nghìn", False, "search", None, "lọc giá"),
    ("kính cận gọng trong suốt có sẵn độ", False, "search", None, "phụ kiện"),
    ("giày sandal nữ mũi vuông đế 7cm", False, "search", None, "giày nữ"),
    ("áo thun cotton cổ tròn unisex size L", False, "search", None, "size alpha"),
    ("shop có bán túi đeo chéo nữ ko", False, "search", None, "teencode"),
    ("dép xỏ ngón nam rẻ rẻ thui", False, "search", None, "teencode 'thui'"),
    ("khuyên tai nam châm không cần bấm lỗ", False, "search", None, "phụ kiện"),
    ("mũ lưỡi trai đen đi phượt", False, "search", None, "mũ"),
    # ---------- compare (2-3 SP cùng nhóm) ----------
    ("so sánh Áo Khoác Gió PEABOO BST01 với BST02 giúp mình", False, "compare", None, "2 SP thật cùng nhóm"),
    ("Dép bánh mì vân nhám và Dép YZ Slide vân nhám cái nào bền hơn", False, "compare", None, "2 dép"),
    ("áo hoodie KANG vs áo hoodie MISTERHIZII, cái nào dày hơn", False, "compare", None, "'vs'"),
    ("so sanh 2 doi cao got Luvia 75CG va G0060", False, "compare", None, "không dấu"),
    ("giữa áo chống nắng UMI dáng dài và áo khoác chống nắng UPF 50+ nên lấy cái nào", False, "compare", None, "dạng 'nên lấy cái nào'"),
    ("Hai mẫu áo thun AM BE và AM 1 khác nhau chỗ nào?", False, "compare", None, "2 áo thun"),
    ("so sánh 3 đôi dép này giúp em: bánh mì vân nhám, YZ slide, xỏ ngón Latoma", False, "compare", None, "3 SP"),
    ("dây chuyền Lovito với vòng cổ MAYEBE, cái nào ít bị đen hơn", False, "compare", None, "phụ kiện"),
    ("cardigan AK13 hay hoodie zip DERROR ấm hơn", False, "compare", None, "2 áo khoác"),
    # ---------- gemini_chitchat ----------
    ("chào shop", False, "gemini_chitchat", None, "chào hỏi"),
    ("hello bot, bạn tên gì", False, "gemini_chitchat", None, "chào + hỏi danh tính"),
    ("cảm ơn nha, bạn dễ thương ghê", False, "gemini_chitchat", None, "cảm ơn"),
    ("hnay mình buồn quá", False, "gemini_chitchat", None, "teencode 'hnay', cảm xúc"),
    ("bạn là người hay máy vậy?", False, "gemini_chitchat", None, "hỏi danh tính"),
    ("kể chuyện cười đi", False, "gemini_chitchat", None, "giải trí"),
    ("chúc shop buổi tối vui vẻ", False, "gemini_chitchat", None, "xã giao"),
    ("ok tks nhé", False, "gemini_chitchat", None, "viết tắt 'tks'"),
    ("trời mưa thế này mặc gì cho hợp nhỉ?", False, "gemini_chitchat", None, "tư vấn chung (ví dụ trong US_51) – không nêu SP/giá"),
    ("đi đám cưới bạn thân nên phối đồ thế nào cho lịch sự", False, "gemini_chitchat", None, "tư vấn phối đồ chung"),
    ("mai đi Đà Lạt nên mang áo gì", False, "gemini_chitchat", None, "tư vấn chung"),
    # ---------- gemini_ood ----------
    ("thủ đô của Úc là gì", False, "gemini_ood", None, "kiến thức chung"),
    ("viết giùm tôi đoạn code python sắp xếp mảng", False, "gemini_ood", None, "lập trình"),
    ("giá vàng hôm nay bao nhiêu", False, "gemini_ood", None, "có chữ 'giá' nhưng ngoài phạm vi"),
    ("kết quả bóng đá tối qua thế nào", False, "gemini_ood", None, "tin tức"),
    ("giải phương trình x^2 - 5x + 6 = 0", False, "gemini_ood", None, "toán"),
    ("làm sao để nấu phở bò ngon", False, "gemini_ood", None, "nấu ăn"),
    ("chỉ mình cách hack facebook người khác", False, "gemini_ood", None, "nội dung nguy hại – Gemini phải từ chối"),
    ("tư vấn mua điện thoại dưới 5 triệu", False, "gemini_ood", None, "mua sắm nhưng ngoài domain thời trang"),
    ("đặt vé máy bay đi HCM giúp mình", False, "gemini_ood", None, "hành động ngoài khả năng"),
    ("thoi tiet ha noi ngay mai the nao", False, "gemini_ood", None, "không dấu; không có công cụ thời tiết"),
    # ---------- clarify ----------
    ("cái này còn không", False, "clarify", None, "không có SP/ảnh trong ngữ cảnh"),
    ("so sánh giúp mình", False, "clarify", None, "thiếu SP để so sánh"),
    ("tư vấn đi", False, "clarify", None, "quá mơ hồ"),
    ("size nào vừa?", False, "clarify", None, "không có SP trong ngữ cảnh"),
    ("có rẻ hơn không", False, "clarify", None, "không có tham chiếu"),
    ("so sánh cái áo này với đôi giày kia", False, "clarify", None, "khác product_type (R19) – hỏi lại chọn cùng nhóm"),
    ("tìm cái giống vậy", False, "clarify", None, "nói 'giống vậy' nhưng không gửi ảnh"),
    ("có màu khác k", False, "clarify", None, "không có SP trong ngữ cảnh"),
    ("mua", False, "clarify", None, "1 từ"),
]


def build() -> list[dict]:
    """Tạo danh sách bản ghi theo đúng schema."""
    rows = []
    for i, (text, img, route, pid, note) in enumerate(ITEMS, 1):
        rows.append({
            "id": f"r{i:03d}", "text": text, "has_image": img, "route": route,
            "product_id": pid, "note": note, "origin": "viet_tay_tac_nhan",
            "annotator_1": "", "annotator_2": "",
        })
    return rows


def check(rows: list[dict], valid_pids: set[str] | None = None) -> list[str]:
    """Kiểm ràng buộc US_16; trả về danh sách lỗi (rỗng = đạt)."""
    errs = []
    if len(rows) < 60:
        errs.append(f"chỉ có {len(rows)} < 60 câu")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        errs.append("trùng id")
    for r in rows:
        if set(r) != set(FIELDS):
            errs.append(f"{r.get('id')}: sai trường {sorted(set(r) ^ set(FIELDS))}")
        if r["route"] not in ROUTES:
            errs.append(f"{r['id']}: route lạ {r['route']}")
        if r["route"] == "visual" and not r["has_image"]:
            errs.append(f"{r['id']}: visual nhưng không có ảnh")
        if not r["has_image"] and not r["text"].strip():
            errs.append(f"{r['id']}: không ảnh, không chữ")
        if valid_pids is not None and r["product_id"] and r["product_id"] not in valid_pids:
            errs.append(f"{r['id']}: product_id không có trong ViMRHP")
    c = collections.Counter(r["route"] for r in rows)
    if c["gemini_chitchat"] + c["gemini_ood"] < 15:
        errs.append("< 15 câu chitchat/ngoài phạm vi")
    missing = ROUTES - set(c)
    if missing:
        errs.append(f"thiếu route {missing}")
    return errs


def load_vimrhp_ids() -> set[str] | None:
    p = Path((os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/vimrhp_fashion_products.jsonl"))
    if not p.exists():
        return None
    return {json.loads(l)["product_id"] for l in p.open(encoding="utf-8")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        rows = [json.loads(l) for l in OUT.open(encoding="utf-8")]
    else:
        rows = build()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    errs = check(rows, load_vimrhp_ids())
    print(json.dumps({"n": len(rows), "by_route": collections.Counter(r["route"] for r in rows),
                      "has_image": sum(r["has_image"] for r in rows), "errors": errs},
                     ensure_ascii=False, indent=1))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
