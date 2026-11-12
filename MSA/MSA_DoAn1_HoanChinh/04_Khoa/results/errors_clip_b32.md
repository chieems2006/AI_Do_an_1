# Phân tích lỗi – `clip_b32` (split test, đo thật)

## Recall@5 theo kiểu biến đổi (tầng instance)

| Biến đổi | n | Recall@5 | Recall@1 | CTE@5 |
|---|---|---|---|---|
| background | 32 | 0.344 | 0.219 | 0.112 |
| color_jitter | 32 | 0.969 | 0.875 | 0.019 |
| combo | 36 | 0.389 | 0.194 | 0.217 |
| crop_offset | 36 | 1.000 | 1.000 | 0.017 |
| hflip_scale | 32 | 1.000 | 0.938 | 0.031 |
| lowres_jpeg | 36 | 0.417 | 0.250 | 0.128 |
| rotate | 36 | 0.944 | 0.889 | 0.000 |

## Recall@5 theo sub_category (instance)

| sub_category | n | Recall@5 |
|---|---|---|
| bag | 44 | 0.659 |
| belt | 9 | 0.889 |
| bottom | 12 | 0.833 |
| cap | 59 | 0.695 |
| dress | 3 | 1.000 |
| eyewear | 7 | 0.571 |
| heel_flat* | 12 | 0.833 |
| leather_shoe | 6 | 0.333 |
| outerwear | 3 | 1.000 |
| sandal | 15 | 0.667 |
| sneaker | 27 | 0.704 |
| top | 42 | 0.786 |
| unknown | 1 | 1.000 |

## Ví dụ lỗi điển hình

| # | query_id | Nhóm | Biến đổi | SP đúng (title) | Top-1 trả về (title, nhóm) | Hạng SP đúng | Nhận xét |
|---|---|---|---|---|---|---|---|
| 1 | vq_inst_acce_046 | accessory | background(scale=0.74) | Fastrack Women Campus Brown Sunglasses | Polaroid Unisex Sunglasses (accessory) | >10 | cùng nhóm, khác SP |
| 2 | vq_inst_acce_053 | accessory | background(scale=0.76) | Kiara Women Teal Handbag | Baggit Women Bingri Club Gold Clutch (accessory) | >10 | cùng nhóm, khác SP |
| 3 | vq_inst_head_079 | headwear | color_jitter(b=0.95,c=1.29,s=1.07) | Nike Unisex Grey FCB Cap | Puma Unisex Ferrari Lifestyle Black Cap (headwear) | 8 | cùng nhóm, khác SP |
| 4 | vq_inst_acce_055 | accessory | combo(rotate=-6.4,b=1.22,bg_scale=0.71) | American Tourister Unisex Black Backpack | Basics Men Blue Beret Cap (headwear) | >10 | SAI NHÓM |
| 5 | vq_inst_acce_062 | accessory | combo(rotate=-7.2,b=0.77,bg_scale=0.82) | Be For Bag Women Orange Bag | Spice Art Women Beaded Multi Coloured Clutch (accessory) | >10 | cùng nhóm, khác SP |
| 6 | vq_inst_acce_040 | accessory | lowres_jpeg(f=0.41,q=25) | Baggit Women Hero Brush Black Clutch | Puma Unisex Cat Red Headband (headwear) | >10 | SAI NHÓM |
| 7 | vq_inst_acce_047 | accessory | lowres_jpeg(f=0.42,q=36) | Paridhan Women Red Handbag | Lino Perros Women Red Clutch (accessory) | >10 | cùng nhóm, khác SP |
| 8 | vq_cat_foot_020 | footwear | held-out/LOO | Flats | Rocia Women Bronze Sandal (footwear) | >10 | category: top-5 không cùng articleType+màu |
| 9 | vq_cat_foot_021 | footwear | held-out/LOO | Sandals | Puma Women Navy Blue Sandal (footwear) | >10 | category: top-5 không cùng articleType+màu |
| 10 | vq_cat_foot_033 | footwear | held-out/LOO | Sports Shoes | Spinn Men Cubic Black Sports Shoes (footwear) | 6 | category: top-5 không cùng articleType+màu |