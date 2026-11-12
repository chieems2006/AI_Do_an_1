# repo: eval/build_bench_qa.py
"""US_24 – Bộ 36 câu hỏi tiếng Việt cho benchmark LLM, viết tay từ review THẬT của ViMRHP.

- Ngữ cảnh: eval/bench_contexts.jsonl (make_bench_contexts.py, seed 42) – 6 review/SP.
- origin = "tac_nhan_AI_viet_tay_tu_review_that": câu hỏi + đáp án tham chiếu do tác nhân AI (vai Tuấn Đạt) viết
  sau khi đọc ngữ cảnh; CHƯA có người thật duyệt (reviewed_by_human=False) – nhóm cần kiểm lại.
- 7/36 câu (19,4%) KHÔNG có đáp án trong ngữ cảnh (answerable=False) → mô hình phải từ chối.

    python eval/build_bench_qa.py    # ghi eval/bench_qa.jsonl
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFUSAL = "Xin lỗi, hiện chưa có thông tin về điều này trong dữ liệu sản phẩm."

# (product_id, question, answerable, reference_answer, evidence_rids)
ITEMS: list[tuple[str, str, bool, str, list[str]]] = [
    ("shopee_18190349666", "Đế dép này cao khoảng bao nhiêu?", True,
     "Khoảng 3,6–4 cm theo một khách tự đo (R1); một khách khác nói cao tầm 5 phân (R6).", ["R1", "R6"]),
    ("shopee_21930029026", "Dép này đi mưa có bị trơn không?", True,
     "Ý kiến trái chiều: R3 nói đi mưa trơn, đế không chống trơn; R6 nói chống trơn trượt tốt.", ["R3", "R6"]),
    ("shopee_22279268972", "Mình nên chọn size dép thế nào?", True,
     "Một khách khuyên tăng 1 size so với size chân bình thường (R5).", ["R5"]),
    ("shopee_22467937435", "Đôi xăng đan này có size 41 không?", False, REFUSAL, []),
    ("shopee_24154620578", "Đường chỉ trên dép là may thật hay chỉ giả?", True,
     "Đường chỉ là chỉ may giả, không phải may thật (R5).", ["R5"]),
    ("shopee_25855122425", "Form dép có nhỏ không, nên chọn size thế nào?", True,
     "Form dép nhỏ, nên lấy cỡ to hơn chân (R6).", ["R6"]),
    ("shopee_6158316169", "Dép làm bằng chất liệu gì, đi có êm không?", True,
     "Khách mô tả là cao su/nhựa dẻo, xốp; đi nhẹ, êm chân (R2, R4, R5, R6).", ["R2", "R4", "R5", "R6"]),
    ("shopee_18990946912", "Đá trên quai được gắn bằng gì, có chắc không?", True,
     "Đá được dính bằng keo nhựa nhưng khách thấy chắc chắn (R6).", ["R6"]),
    ("shopee_21750128753", "Quai giày có vấn đề gì không?", True,
     "Quai cài khá lỏng/rộng, dễ tuột; shop không đục thêm lỗ nên có khách phải tự đục lỗ để chỉnh (R2, R3, R6).",
     ["R2", "R3", "R6"]),
    ("shopee_21912926225", "Đế giày làm bằng chất liệu gì?", False, REFUSAL, []),
    ("shopee_22420953658", "Người cổ chân to có đi vừa quai ngọc không?", True,
     "Một khách cổ chân hơi to không vừa quai ngọc, phải sửa lại mới đi được (R4).", ["R4"]),
    ("shopee_22542160769", "Giày có đúng size không, mình nên chọn size nào?", True,
     "Ý kiến khác nhau: R1 và R2 lùi 1 size (R2 lùi rồi vẫn hơi rộng); R4 nói đúng form, đi size nào đặt size đó.",
     ["R1", "R2", "R4"]),
    ("shopee_24479327396", "Gót giày cao bao nhiêu và da có mềm không?", True,
     "Cao 5 phân (R5); da mềm, êm chân (R1, R2, R4, R5).", ["R1", "R2", "R4", "R5"]),
    ("shopee_3954542804", "Đế giày làm bằng chất liệu gì?", True,
     "Theo một khách, đế làm bằng nhựa nên bền (R2).", ["R2"]),
    ("shopee_15693430346", "Áo có dày không, mặc có ấm không?", True,
     "Nỉ bông dày, mặc khá ấm (R2); một khách khác thấy không quá mỏng không quá dày, hợp trời se lạnh (R3).",
     ["R2", "R3"]),
    ("shopee_16683003980", "Áo này mặc mùa đông được không?", True,
     "Không hợp trời quá lạnh: vải mỏng, chỉ vừa đủ ấm, hợp mùa thu/hè hơn (R1, R3, R4, R5).",
     ["R1", "R3", "R4", "R5"]),
    ("shopee_17169016608", "Đường may của áo có tốt không?", True,
     "Trái chiều: R3 khen đường may đẹp, không chỉ thừa; R6 chê rách phần nách, nhiều chỉ thừa.", ["R3", "R6"]),
    ("shopee_23913613670", "Áo có giặt máy được không?", False, REFUSAL, []),
    ("shopee_23977815120", "Chữ in trên áo có dễ bong tróc không?", True,
     "Một khách thấy chữ in sắc nét, dày nên đoán còn lâu mới tróc (R3) – chỉ là nhận định ban đầu.", ["R3"]),
    ("shopee_24776979244", "Số đo của áo là bao nhiêu?", True,
     "Một khách ghi số đo: ngang 52, dài 65, tay 18, vai 47 (R3), không nói rõ size.", ["R3"]),
    ("shopee_25503405313", "Áo hoodie này có những màu nào?", False, REFUSAL, []),
    ("shopee_11287789278", "Chất vải bộ này mặc có mát không?", True,
     "Có, nhiều khách nói vải mát (R3, R5, R6); R5 ghi chất cotton, R2 nói vải mỏng.", ["R2", "R3", "R5", "R6"]),
    ("shopee_16997723323", "Size áo có chuẩn không?", True,
     "Nhiều khách thấy size 38 nhỏ/chật (R1 quá bé, R3 hơi chật, nên nhích size); R5 thấy ôm vừa vặn.",
     ["R1", "R3", "R5"]),
    ("shopee_19206582404", "Áo chống nắng này có chỉ số chống UV (UPF) bao nhiêu?", False, REFUSAL, []),
    ("shopee_22681195724", "Vải áo có mỏng không?", True,
     "R3 nói vải khá mỏng, thoáng mát; R4 nói vải không quá mỏng, mềm mịn.", ["R3", "R4"]),
    ("shopee_25814055660", "Quần có co giãn không?", True,
     "Có, chất umi co giãn tốt (R1, R2, R3, R6).", ["R1", "R2", "R3", "R6"]),
    ("shopee_28200605609", "Người bắp tay to nên chọn size thế nào?", True,
     "Nên tăng size; size XL cũng không lo rộng (R3).", ["R3"]),
    ("shopee_7889166708", "Bộ đồ này làm bằng chất liệu gì?", True,
     "Cotton/thun, vải mát, mỏng (R2, R4, R6).", ["R2", "R4", "R6"]),
    ("shopee_18780511843", "Mũ có điều chỉnh được vòng đầu không?", False, REFUSAL, []),
    ("shopee_18888927612", "Vành mũ có che tầm nhìn không?", True,
     "Vành trước khá rộng nhưng hơi ngắn; nếu đội đúng thì hơi che tầm nhìn (R1).", ["R1"]),
    ("shopee_19092023455", "Khăn lau có bị ướt quá không?", True,
     "Một khách thấy khăn khá ướt nhưng chấp nhận được với tầm giá (R6).", ["R6"]),
    ("shopee_23164140187", "Có ai nhận kính bị vỡ không?", True,
     "Có: R2 nhận kính bị vỡ; R5 nghi bị gãy 1 cái do vận chuyển.", ["R2", "R5"]),
    ("shopee_23261536758", "Gọng kính làm bằng titan hay nhựa?", False, REFUSAL, []),
    ("shopee_24010484186", "Thắt lưng có cần đục lỗ không, dùng thế nào?", True,
     "Không cần đục lỗ: đẩy dây chặt vào khóa, khi mở thì gạt cần rồi rút ra (R1).", ["R1"]),
    ("shopee_24265142280", "Dây thắt lưng có phải da thật không?", True,
     "Theo R1, dây là chất liệu nhựa, da không đúng mô tả; R2 nói dây bị xước, móp.", ["R1", "R2"]),
    ("shopee_25703385119", "Mũ có chỉnh được kích cỡ không?", True,
     "Có, mũ có phần điều chỉnh kích thước (R1, R4).", ["R1", "R4"]),
]


def build() -> list[dict]:
    ctx = {json.loads(l)["product_id"]: json.loads(l) for l in (HERE / "bench_contexts.jsonl").open(encoding="utf-8")}
    out = []
    for i, (pid, q, ans, ref, ev) in enumerate(ITEMS, 1):
        assert pid in ctx, pid
        valid = {c["rid"] for c in ctx[pid]["context"]}
        assert set(ev) <= valid, (pid, ev)
        out.append(dict(qid=f"q{i:03d}", product_id=pid, vimrhp_subcategory=ctx[pid]["vimrhp_subcategory"],
                        question=q, answerable=ans, reference_answer=ref, evidence_rids=ev,
                        origin="tac_nhan_AI_viet_tay_tu_review_that", reviewed_by_human=False))
    return out


if __name__ == "__main__":
    rows = build()
    with (HERE / "bench_qa.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} câu ({sum(not r['answerable'] for r in rows)} không có đáp án) -> eval/bench_qa.jsonl")
