# Phân tích lỗi – `fashionclip` (split test, đo thật)

## Recall@5 theo kiểu biến đổi (tầng instance)

| Biến đổi | n | Recall@5 | Recall@1 | CTE@5 |
|---|---|---|---|---|
| background | 32 | 0.656 | 0.438 | 0.144 |
| color_jitter | 32 | 1.000 | 1.000 | 0.006 |
| combo | 36 | 0.667 | 0.417 | 0.172 |
| crop_offset | 36 | 1.000 | 1.000 | 0.000 |
| hflip_scale | 32 | 1.000 | 0.938 | 0.013 |
| lowres_jpeg | 36 | 0.500 | 0.194 | 0.094 |
| rotate | 36 | 1.000 | 0.972 | 0.000 |

## Recall@5 theo sub_category (instance)

| sub_category | n | Recall@5 |
|---|---|---|
| bag | 44 | 0.909 |
| belt | 9 | 0.778 |
| bottom | 12 | 0.833 |
| cap | 59 | 0.881 |
| dress | 3 | 1.000 |
| eyewear | 7 | 0.714 |
| heel_flat* | 12 | 0.750 |
| leather_shoe | 6 | 0.500 |
| outerwear | 3 | 1.000 |
| sandal | 15 | 0.667 |
| sneaker | 27 | 0.815 |
| top | 42 | 0.810 |
| unknown | 1 | 1.000 |

## Ví dụ lỗi điển hình

| # | query_id | Nhóm | Biến đổi | SP đúng (title) | Top-1 trả về (title, nhóm) | Hạng SP đúng | Nhận xét |
|---|---|---|---|---|---|---|---|
| 1 | vq_inst_acce_046 | accessory | background(scale=0.74) | Fastrack Women Campus Brown Sunglasses | Pepe Jeans Women Casual Sunglasses (accessory) | 9 | cùng nhóm, khác SP |
| 2 | vq_inst_acce_053 | accessory | background(scale=0.76) | Kiara Women Teal Handbag | Roxy Women Blue Cap (headwear) | >10 | SAI NHÓM |
| 3 | vq_inst_acce_083 | accessory | combo(rotate=6.1,b=1.23,bg_scale=0.82) | Fastrack Men Silver Sunglasses | ADIDAS Men Solid Blue Caps (headwear) | >10 | SAI NHÓM |
| 4 | vq_inst_clot_041 | clothing | combo(rotate=-9.2,b=0.93,bg_scale=0.72) | Tonga Women Black Skirt | Forever New Women's Short Black Skirt (clothing) | 7 | cùng nhóm, khác SP |
| 5 | vq_inst_acce_075 | accessory | lowres_jpeg(f=0.58,q=34) | Flying Machine Men Woven Black Belt | Stoln Women Grey Belt (accessory) | 6 | cùng nhóm, khác SP |
| 6 | vq_inst_acce_082 | accessory | lowres_jpeg(f=0.45,q=20) | Hidekraft Women Leather Black Handbags | Hidekraft Women Black Handbag (accessory) | >10 | cùng nhóm, khác SP |
| 7 | vq_cat_foot_020 | footwear | held-out/LOO | Flats | Rocia Women Bronze Sandal (footwear) | >10 | category: top-5 không cùng articleType+màu |
| 8 | vq_cat_foot_021 | footwear | held-out/LOO | Sandals | ADIDAS Women Receptor Grey Black Sandals (footwear) | >10 | category: top-5 không cùng articleType+màu |
| 9 | vq_cat_foot_031 | footwear | held-out/LOO | Formal Shoes | Numero Uno Men Black Formal Shoes (footwear) | >10 | category: top-5 không cùng articleType+màu |