# repo: src/msa/data/taxonomy.py
"""Taxonomy 2 cấp (US_49): product_type -> sub_category và hàm map nhãn từng nguồn về cây.

Quy ước kết quả map: (product_type, sub_category, action, rule_id)
- action = "keep"    : vào catalog/index với lá hợp lệ.
- action = "unknown" : thuộc 1 trong 4 nhóm nhưng chưa rõ lá -> sub_category="unknown", KHÔNG đưa vào index ảnh.
- action = "exclude" : ngoài phạm vi Đồ án 1 (đồng hồ, trang sức, tất, ví, khăn, đồ lót...) -> product_type="out_of_scope".
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from msa.textnorm import strip_accents

TAXONOMY: dict[str, list[str]] = {
    "footwear": ["sneaker", "leather_shoe", "sandal", "boot", "heel_flat"],
    "clothing": ["top", "bottom", "dress", "outerwear"],
    "headwear": ["cap", "beanie", "bucket", "wide_brim"],
    "accessory": ["bag", "belt", "eyewear"],
}
PRODUCT_TYPES = list(TAXONOMY)
OUT = "out_of_scope"

VI_NAMES = {
    "footwear": "Giày dép", "clothing": "Quần áo", "headwear": "Mũ", "accessory": "Phụ kiện",
    "sneaker": "giày thể thao", "leather_shoe": "giày da/giày tây", "sandal": "sandal/dép", "boot": "boot/bốt",
    "heel_flat": "giày cao gót/búp bê", "top": "áo", "bottom": "quần/chân váy", "dress": "váy liền/đầm/jumpsuit",
    "outerwear": "áo khoác", "cap": "mũ lưỡi trai", "beanie": "mũ len (beanie)", "bucket": "mũ bucket",
    "wide_brim": "mũ rộng vành", "bag": "túi/balo", "belt": "thắt lưng", "eyewear": "kính",
}


@dataclass(frozen=True)
class MapResult:
    product_type: str
    sub_category: str
    action: str
    rule_id: str

    def as_tuple(self) -> tuple[str, str, str, str]:
        return (self.product_type, self.sub_category, self.action, self.rule_id)


def is_valid_leaf(product_type: str, sub_category: str) -> bool:
    """Kiểm tra cặp (product_type, sub_category) có thuộc cây (cho phép lá 'unknown')."""
    return product_type in TAXONOMY and (sub_category in TAXONOMY[product_type] or sub_category == "unknown")


def _keep(pt: str, sub: str, rule: str) -> MapResult:
    return MapResult(pt, sub, "keep", rule)


def _unknown(pt: str, rule: str) -> MapResult:
    return MapResult(pt, "unknown", "unknown", rule)


def _excl(rule: str) -> MapResult:
    return MapResult(OUT, "unknown", "exclude", rule)


# ---------------------------------------------------------------- Fashion Product Images
# articleType -> kết quả; khoá theo articleType vì masterCategory/subCategory gốc có nhiễu
# (vd 'Accessories/Belts/Tshirts', 'Apparel/Topwear/Belts').
FPI_ARTICLE: dict[str, MapResult] = {}
for _a in ["Casual Shoes", "Sports Shoes"]:
    FPI_ARTICLE[_a] = _keep("footwear", "sneaker", "fpi.article")
FPI_ARTICLE["Formal Shoes"] = _keep("footwear", "leather_shoe", "fpi.article")
for _a in ["Heels", "Flats"]:
    FPI_ARTICLE[_a] = _keep("footwear", "heel_flat", "fpi.article")
for _a in ["Sandals", "Sports Sandals", "Flip Flops"]:
    FPI_ARTICLE[_a] = _keep("footwear", "sandal", "fpi.article")
for _a in ["Tshirts", "Shirts", "Tops", "Sweatshirts", "Sweaters", "Kurtas", "Kurtis", "Tunics", "Lounge Tshirts"]:
    FPI_ARTICLE[_a] = _keep("clothing", "top", "fpi.article")
for _a in ["Jackets", "Blazers", "Rain Jacket", "Nehru Jackets", "Waistcoat", "Shrug"]:
    FPI_ARTICLE[_a] = _keep("clothing", "outerwear", "fpi.article")
for _a in ["Jeans", "Shorts", "Trousers", "Track Pants", "Skirts", "Capris", "Leggings", "Jeggings",
           "Churidar", "Patiala", "Salwar", "Tights"]:
    FPI_ARTICLE[_a] = _keep("clothing", "bottom", "fpi.article")
for _a in ["Dresses", "Jumpsuit", "Rompers"]:
    FPI_ARTICLE[_a] = _keep("clothing", "dress", "fpi.article")
for _a in ["Clothing Set", "Kurta Sets", "Tracksuits", "Lehenga Choli", "Salwar and Dupatta"]:
    FPI_ARTICLE[_a] = _unknown("clothing", "fpi.set_nhieu_mon")  # bộ nhiều món: không rõ 1 lá
FPI_ARTICLE["Caps"] = _keep("headwear", "cap", "fpi.article")
FPI_ARTICLE["Hat"] = _keep("headwear", "wide_brim", "fpi.article")  # bị ghi đè bởi luật tiêu đề bên dưới
for _a in ["Handbags", "Backpacks", "Rucksacks", "Clutches", "Duffel Bag", "Laptop Bag", "Messenger Bag",
           "Mobile Pouch", "Waist Pouch", "Trolley Bag"]:
    FPI_ARTICLE[_a] = _keep("accessory", "bag", "fpi.article")
FPI_ARTICLE["Belts"] = _keep("accessory", "belt", "fpi.article")
FPI_ARTICLE["Sunglasses"] = _keep("accessory", "eyewear", "fpi.article")

FPI_EXCLUDE_MASTER = {"Personal Care", "Free Items", "Home", "Sporting Goods"}
FPI_EXCLUDE_REASON = {
    "Watches": "đồng hồ", "Earrings": "trang sức", "Bangle": "trang sức", "Bracelet": "trang sức", "Ring": "trang sức",
    "Pendant": "trang sức", "Necklace and Chains": "trang sức", "Jewellery Set": "trang sức",
    "Socks": "tất/vớ", "Booties": "tất/vớ trẻ em", "Stockings": "tất da", "Wallets": "ví",
    "Scarves": "khăn", "Mufflers": "khăn", "Stoles": "khăn", "Dupatta": "khăn choàng",
    "Ties": "cà vạt", "Ties and Cufflinks": "cà vạt", "Cufflinks": "khuy măng sét", "Gloves": "găng tay",
    "Headband": "băng đô (phụ kiện tóc, không phải mũ)", "Hair Accessory": "phụ kiện tóc",
    "Suspenders": "dây đeo quần", "Umbrellas": "ô/dù", "Water Bottle": "bình nước", "Key chain": "móc khoá",
    "Travel Accessory": "phụ kiện du lịch", "Tablet Sleeve": "túi chống sốc thiết bị", "Accessory Gift Set": "set quà",
    "Shoe Accessories": "phụ kiện giày", "Shoe Laces": "dây giày", "Wristbands": "băng cổ tay",
    "Perfume and Body Mist": "mỹ phẩm", "Swimwear": "đồ bơi", "Sarees": "sari (trang phục truyền thống quấn)",
    "Bra": "đồ lót", "Briefs": "đồ lót", "Boxers": "đồ lót", "Trunk": "đồ lót", "Camisoles": "đồ lót",
    "Innerwear Vests": "đồ lót", "Shapewear": "đồ lót", "Baby Dolls": "đồ ngủ", "Bath Robe": "đồ ngủ",
    "Robe": "đồ ngủ", "Night suits": "đồ ngủ", "Nightdress": "đồ ngủ", "Lounge Pants": "đồ mặc nhà",
    "Lounge Shorts": "đồ mặc nhà",
}

_RE_BOOT = re.compile(r"\bboots?\b", re.I)
_RE_BEANIE = re.compile(r"\b(beanie|skull ?caps?)\b", re.I)
_RE_BUCKET = re.compile(r"\bbucket\b", re.I)


def map_fpi(master: str | None, sub: str | None, article: str | None, title: str | None = "") -> MapResult:
    """Map 1 dòng Fashion Product Images về cây. Luật tiêu đề tinh chỉnh lá (boot, beanie)."""
    title = title or ""
    if master in FPI_EXCLUDE_MASTER and article not in FPI_ARTICLE:
        return _excl(f"fpi.master_excl:{master}")
    if article in FPI_EXCLUDE_REASON:
        return _excl(f"fpi.excl:{FPI_EXCLUDE_REASON[article]}")
    if article in ("Lounge Tshirts",):
        return _excl("fpi.excl:đồ mặc nhà")
    if master == "Apparel" and sub == "Loungewear and Nightwear":
        return _excl("fpi.excl:đồ mặc nhà")
    base = FPI_ARTICLE.get(article or "")
    if base is None:
        return _excl(f"fpi.chua_co_trong_bang:{article}")
    # Tinh chỉnh bằng tiêu đề (chỉ trong cùng product_type)
    if base.product_type == "footwear" and _RE_BOOT.search(title) and not re.search(r"sandals?\s*$", title, re.I):
        # 'Sports Shoes' có chữ Boot giữa tên thường là giày đá bóng (football boot) -> giữ sneaker;
        # chỉ nhận boot khi tên KẾT THÚC bằng Boot(s) (vd 'Nike ... ACG Sports Boot').
        if article != "Sports Shoes" or re.search(r"boots?\s*$", title, re.I):
            return _keep("footwear", "boot", "fpi.title_boot")
    if base.product_type == "headwear":
        if _RE_BEANIE.search(title):
            return _keep("headwear", "beanie", "fpi.title_beanie")
        if _RE_BUCKET.search(title):
            return _keep("headwear", "bucket", "fpi.title_bucket")
    return base


# ---------------------------------------------------------------- ViMRHP (Shopee VN)
# Mỗi mẫu: (regex trên tiêu đề KHÔNG dấu, chữ thường) -> kết quả. Chọn mẫu xuất hiện SỚM NHẤT trong
# tiêu đề (danh từ đầu = loại sản phẩm), hoà thì chọn mẫu dài hơn. Nhờ vậy:
#   "Áo khoác ... có mũ"   -> áo khoác (mũ trùm chỉ là chi tiết)
#   "Khăn lau kính"        -> khăn (ngoài phạm vi), không phải kính
VI_PATTERNS: list[tuple[str, MapResult]] = [
    # --- ngoài phạm vi
    (r"dong ho", _excl("vi.excl:đồng hồ")),
    (r"khuyen tai|bong tai|hoa tai|nhan titan|nhan bac|^nhan\b|vong tay|vong co|day chuyen|lac tay|trang suc", _excl("vi.excl:trang sức")),
    (r"^tat\b|\btat (co|tron|nike|the thao|nam|nu)|^vo\b|\bvo co\b|doi vo\b", _excl("vi.excl:tất/vớ")),
    (r"kep toc|day buoc toc|day cot toc|buoc toc|bang do|scrunchie|mieng dan toc|co dinh toc|phu kien toc", _excl("vi.excl:phụ kiện tóc")),
    (r"khau trang", _excl("vi.excl:khẩu trang")),
    (r"\bdu gap\b|umbrella|\bo che\b", _excl("vi.excl:ô/dù")),
    (r"keo dan giay|lot giay|day giay|xi giay", _excl("vi.excl:phụ kiện giày")),
    (r"\bkhan\b", _excl("vi.excl:khăn")),
    (r"\bvi da\b|\bvi nam\b|\bvi nu\b|\bvi cam tay\b|^vi\b|\bbop\b", _excl("vi.excl:ví")),
    (r"ao nguc|ao lot|quan lot|\bsip\b|do lot|ao bra|\bbra\b", _excl("vi.excl:đồ lót")),
    (r"do ngu|bo ngu|pijama|pyjama|pajama|quan ngu|vay ngu|dam ngu|mac nha", _excl("vi.excl:đồ ngủ/mặc nhà")),
    (r"mu bao hiem|non bao hiem", _excl("vi.excl:mũ bảo hiểm")),
    (r"huy hieu|hinh xam|bam lo tai|ong tay|gang tay|moc khoa", _excl("vi.excl:phụ kiện khác")),
    # --- mũ
    (r"mu luoi trai|non luoi trai|snapback|mu ket|non ket|baseball cap", _keep("headwear", "cap", "vi.cap")),
    (r"mu len|non len|beanie", _keep("headwear", "beanie", "vi.beanie")),
    (r"mu bucket|non bucket|mu tai beo|non tai beo|bucket", _keep("headwear", "bucket", "vi.bucket")),
    (r"mu rong vanh|non rong vanh|mu vanh|non vanh|mu coi|non la|mu chong nang|non chong nang|mu cheo|mu phot", _keep("headwear", "wide_brim", "vi.wide_brim")),
    # --- phụ kiện
    (r"that lung|day lung|\bnit da\b|^nit\b", _keep("accessory", "belt", "vi.belt")),
    (r"kinh mat|kinh ram|kinh can|mat kinh|gong kinh|kinh chong|kinh chan|kinh thoi trang|^kinh\b", _keep("accessory", "eyewear", "vi.eyewear")),
    (r"tui xach|tui deo|tui tote|^tui\b|balo|ba lo|cap sach", _keep("accessory", "bag", "vi.bag")),
    # --- giày dép
    (r"cao got|got nhon|got vuong|got tru|got cao|bup be|\bguoc\b", _keep("footwear", "heel_flat", "vi.heel_flat")),
    (r"\bboots?\b|\bbot\b|giay co cao", _keep("footwear", "boot", "vi.boot")),
    (r"giay the thao|sneaker|giay chay|giay tap|giay bong|giay di bo", _keep("footwear", "sneaker", "vi.sneaker")),
    (r"giay da|giay tay|giay cong so nam|giay luoi|loafer|oxford|derby", _keep("footwear", "leather_shoe", "vi.leather_shoe")),
    (r"sandal|sandan|xang dan|^dep\b|\bdep (nam|nu|quai|ban|di|lao|kep|xop|tam|suc|ca|cao|cheo|nhua|chong|vip|ayoon|nerdy|crocs|dong|nk|yz)|tong lao|tong thai|tong di bien|^tong\b|dep tong|\bsuc\b|crocs|slide|xo ngon|flip ?flops?", _keep("footwear", "sandal", "vi.sandal")),
    # --- quần áo
    (r"ao khoac|khoac ngoai|ao gio|bomber|cardigan|blazer|ao vest|ao chong nang|ao choang|poncho|ao phao|ao mang to|jacket", _keep("clothing", "outerwear", "vi.outerwear")),
    (r"\bset (bo )?(ao|quan|do|the thao)\b|\bbo (quan ao|do|the thao|ao|thun|quan|coc)\b|quan ao", _unknown("clothing", "vi.set_nhieu_mon")),
    (r"vay lien|^dam\b|\bdam (nu|xoe|suong|body|om|cong so|du tiec|maxi)|jumpsuit|^vay\b|\bvay (nu|xoe|suong|body|om|maxi|hai day|2 day|babydoll)", _keep("clothing", "dress", "vi.dress")),
    (r"chan vay|vay ngan|^quan\b|\bquan (jean|short|kaki|au|tay|dai|ong|suong|the thao|nam|nu|legging|jogger|cap|ni|dui|baggy|culottes)|legging|jogger", _keep("clothing", "bottom", "vi.bottom")),
    (r"^ao\b|\bao (thun|phong|so mi|polo|hoodie|ni|len|croptop|baby|yem|hai day|2 day|tanktop|ba lo|co|tay)|hoodie|sweater|polo|so mi|baby ?tee|croptop|tank ?top", _keep("clothing", "top", "vi.top")),
]
# Mẫu "chung chung" chỉ dùng khi KHÔNG có mẫu cụ thể nào khớp.
VI_GENERIC: list[tuple[str, MapResult]] = [
    (r"\bmu\b|\bnon\b", _unknown("headwear", "vi.mu_chung")),
    (r"\bgiay\b", _unknown("footwear", "vi.giay_chung")),
    (r"\bao\b", _keep("clothing", "top", "vi.ao_chung")),
    (r"\bquan\b", _keep("clothing", "bottom", "vi.quan_chung")),
]
_VI_COMPILED = [(re.compile(p), r) for p, r in VI_PATTERNS]
_VI_GENERIC_C = [(re.compile(p), r) for p, r in VI_GENERIC]
_RE_VI_HEEL = re.compile(r"cao got|got nhon|got vuong|got tru|got cao|bup be|\bguoc\b")
_RE_VI_BOOT = re.compile(r"\bboots?\b|\bbot\b|giay co cao")


def _clean_vi_title(title: str) -> str:
    t = strip_accents((title or "").lower())
    t = re.sub(r"\[[^\]]*\]|【[^】]*】|\([^)]*\)", " ", t)  # bỏ [FREESHIP], [Mã ...], (FULL BOX)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    # bỏ tiền tố quảng cáo/thương hiệu hay gặp trước danh từ chính
    t = re.sub(r"^(\s*(gift sticker|hot|sale|sieu sale|gia soc|soc|freeship|co hang san|moi|new|full box|xa kho|re vo dich)\s+)+", " ", t)
    return " ".join(t.split())


def _earliest(t: str, compiled: list[tuple[re.Pattern, MapResult]]) -> MapResult | None:
    best: tuple[tuple[int, int], MapResult] | None = None
    for rx, res in compiled:
        m = rx.search(t)
        if m:
            key = (m.start(), -(m.end() - m.start()))
            if best is None or key < best[0]:
                best = (key, res)
    return best[1] if best else None


def map_vimrhp(subcategory: str | None, title: str | None) -> MapResult:
    """Map 1 sản phẩm ViMRHP: SubCategory chỉ là gợi ý (DongHo -> loại), lá lấy từ tiêu đề tiếng Việt.

    Quy tắc: lấy mẫu cụ thể khớp SỚM NHẤT (danh từ đầu tiêu đề = loại SP); giày dép có 'cao gót/búp bê'
    -> heel_flat, có 'boot/bốt' -> boot; nhóm GiayDep* mà ra quần áo -> unknown để người duyệt.
    """
    if subcategory == "DongHo":
        return _excl("vi.subcat:DongHo")
    t = _clean_vi_title(title or "")
    res = _earliest(t, _VI_COMPILED) or _earliest(t, _VI_GENERIC_C)
    if res is None:
        hint = {"GiayDepNam": "footwear", "GiayDepNu": "footwear", "ThoiTrangNam": "clothing", "ThoiTrangNu": "clothing"}.get(subcategory or "")
        return _unknown(hint, "vi.khong_khop_mau") if hint else _excl("vi.khong_khop_mau")
    if res.product_type == "footwear":
        if _RE_VI_HEEL.search(t):
            return _keep("footwear", "heel_flat", "vi.heel_flat")
        if _RE_VI_BOOT.search(t):
            return _keep("footwear", "boot", "vi.boot")
    if subcategory in ("GiayDepNam", "GiayDepNu") and res.product_type == "clothing":
        return _unknown("footwear", "vi.xung_dot_subcat")
    return res


# ---------------------------------------------------------------- Nguồn chưa có file (map theo tài liệu)
DOC_MAPS: dict[str, dict[str, tuple[str, str, str]]] = {
    # [cần xác minh] nhãn theo tài liệu công khai, chưa đối chiếu file thật
    "clothing_dataset_cc0": {
        "T-Shirt": ("clothing", "top", "keep"), "Longsleeve": ("clothing", "top", "keep"), "Shirt": ("clothing", "top", "keep"),
        "Polo": ("clothing", "top", "keep"), "Top": ("clothing", "top", "keep"), "Blouse": ("clothing", "top", "keep"),
        "Hoodie": ("clothing", "top", "keep"), "Pants": ("clothing", "bottom", "keep"), "Shorts": ("clothing", "bottom", "keep"),
        "Skirt": ("clothing", "bottom", "keep"), "Dress": ("clothing", "dress", "keep"), "Outwear": ("clothing", "outerwear", "keep"),
        "Blazer": ("clothing", "outerwear", "keep"), "Hat": ("headwear", "unknown", "unknown"), "Shoes": ("footwear", "unknown", "unknown"),
        "Undershirt": (OUT, "unknown", "exclude"), "Body": (OUT, "unknown", "exclude"), "Other": (OUT, "unknown", "exclude"),
        "Not sure": (OUT, "unknown", "exclude"), "Skip": (OUT, "unknown", "exclude"),
    },
    "abo_amazon_berkeley_objects": {
        "SHOES": ("footwear", "unknown", "unknown"), "BOOT": ("footwear", "boot", "keep"), "SANDAL": ("footwear", "sandal", "keep"),
        "HAT": ("headwear", "unknown", "unknown"), "HANDBAG": ("accessory", "bag", "keep"), "BACKPACK": ("accessory", "bag", "keep"),
        "SUNGLASSES": ("accessory", "eyewear", "keep"), "SHIRT": ("clothing", "top", "keep"), "PANTS": ("clothing", "bottom", "keep"),
        "DRESS": ("clothing", "dress", "keep"), "COAT": ("clothing", "outerwear", "keep"), "WATCH": (OUT, "unknown", "exclude"),
    },
    "amazon_reviews_2023_clothing_shoes_jewelry": {
        "Shoes > Athletic": ("footwear", "sneaker", "keep"), "Shoes > Fashion Sneakers": ("footwear", "sneaker", "keep"),
        "Shoes > Boots": ("footwear", "boot", "keep"), "Shoes > Sandals": ("footwear", "sandal", "keep"),
        "Shoes > Oxfords": ("footwear", "leather_shoe", "keep"), "Shoes > Loafers & Slip-Ons": ("footwear", "leather_shoe", "keep"),
        "Shoes > Pumps": ("footwear", "heel_flat", "keep"), "Shoes > Flats": ("footwear", "heel_flat", "keep"),
        "Accessories > Hats & Caps > Baseball Caps": ("headwear", "cap", "keep"), "Accessories > Hats & Caps > Skullies & Beanies": ("headwear", "beanie", "keep"),
        "Accessories > Hats & Caps > Bucket Hats": ("headwear", "bucket", "keep"), "Accessories > Hats & Caps > Sun Hats": ("headwear", "wide_brim", "keep"),
        "Accessories > Belts": ("accessory", "belt", "keep"), "Accessories > Sunglasses & Eyewear Accessories": ("accessory", "eyewear", "keep"),
        "Handbags & Wallets > Shoulder Bags": ("accessory", "bag", "keep"), "Clothing > Tops, Tees & Shirts": ("clothing", "top", "keep"),
        "Clothing > Pants": ("clothing", "bottom", "keep"), "Clothing > Dresses": ("clothing", "dress", "keep"),
        "Clothing > Coats, Jackets & Vests": ("clothing", "outerwear", "keep"), "Jewelry": (OUT, "unknown", "exclude"),
        "Watches": (OUT, "unknown", "exclude"),
    },
}
