# Phân tích lỗi – `siglip_b16` (split test, đo thật)

## Recall@5 theo kiểu biến đổi (tầng instance)

| Biến đổi | n | Recall@5 | Recall@1 | CTE@5 |
|---|---|---|---|---|
| background | 32 | 0.906 | 0.688 | 0.062 |
| color_jitter | 32 | 1.000 | 0.906 | 0.013 |
| combo | 36 | 0.750 | 0.472 | 0.078 |
| crop_offset | 36 | 1.000 | 0.944 | 0.006 |
| hflip_scale | 32 | 0.938 | 0.906 | 0.013 |
| lowres_jpeg | 36 | 0.278 | 0.139 | 0.206 |
| rotate | 36 | 1.000 | 0.917 | 0.000 |

## Recall@5 theo sub_category (instance)

| sub_category | n | Recall@5 |
|---|---|---|
| bag | 44 | 0.909 |
| belt | 9 | 0.778 |
| bottom | 12 | 1.000 |
| cap | 59 | 0.780 |
| dress | 3 | 1.000 |
| eyewear | 7 | 0.571 |
| heel_flat* | 12 | 0.833 |
| leather_shoe | 6 | 0.833 |
| outerwear | 3 | 1.000 |
| sandal | 15 | 0.867 |
| sneaker | 27 | 0.815 |
| top | 42 | 0.810 |
| unknown | 1 | 1.000 |

## Ví dụ lỗi điển hình

| # | query_id | Nhóm | Biến đổi | SP đúng (title) | Top-1 trả về (title, nhóm) | Hạng SP đúng | Nhận xét |
|---|---|---|---|---|---|---|---|
| 1 | vq_inst_acce_046 | accessory | background(scale=0.74) | Fastrack Women Campus Brown Sunglasses | Ray-Ban Men Wayfarer Sunglasses (accessory) | >10 | cùng nhóm, khác SP |
| 2 | vq_inst_clot_095 | clothing | background(scale=0.76) | Lee Men Checks Parker Blue Shirt | Highlander Men Black Check Shirt (clothing) | >10 | cùng nhóm, khác SP |
| 3 | vq_inst_acce_076 | accessory | combo(rotate=-9.2,b=0.87,bg_scale=0.81) | Ray-Ban Men Aviator Sunglasses | Basics Men Aviator Sunglasses (accessory) | >10 | cùng nhóm, khác SP |
| 4 | vq_inst_acce_083 | accessory | combo(rotate=6.1,b=1.23,bg_scale=0.82) | Fastrack Men Silver Sunglasses | Tantra Kid's Unisex Caution Blue Kidswear (clothing) | >10 | SAI NHÓM |
| 5 | vq_inst_head_052 | headwear | hflip_scale(s=0.76) | ADIDAS Kids-Unisex Mumbai Indians Team Blue Cap | ADIDAS Blue Cap (headwear) | >10 | cùng nhóm, khác SP |
| 6 | vq_inst_head_080 | headwear | hflip_scale(s=0.77) | ADIDAS Unisex Navy Blue Cap | Stoln Women Black Belt (accessory) | 9 | SAI NHÓM |
| 7 | vq_inst_acce_047 | accessory | lowres_jpeg(f=0.42,q=36) | Paridhan Women Red Handbag | Gini and Jony Girl's Glinda Red Kidswear (clothing) | >10 | SAI NHÓM |
| 8 | vq_cat_foot_020 | footwear | held-out/LOO | Flats | Rocia Women Bronze Sandal (footwear) | >10 | category: top-5 không cùng articleType+màu |
| 9 | vq_cat_foot_021 | footwear | held-out/LOO | Sandals | ADIDAS Men Grey and Navy Blue Sandal (footwear) | >10 | category: top-5 không cùng articleType+màu |
| 10 | vq_cat_foot_038 | footwear | held-out/LOO | Heels | Portia Women Gold Flats (footwear) | >10 | category: top-5 không cùng articleType+màu |