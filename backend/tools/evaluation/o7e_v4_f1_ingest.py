# -*- coding: utf-8 -*-
"""O7-E V4-F1 §2: 阿奎那《神学大全》公版文本分章入库。

来源: Project Gutenberg #17611 (Part I) / #17897 (Part I-II)
      Benziger Brothers 版, Fathers of the English Dominican Province 译
      （1911-1936 年出版, 美国公有领域; PG 授权允许自由再利用）
提取: ST I q.48-49（恶/善的缺乏）+ ST I-II q.90-97（律法论）→ 10 章
格式: book_chapters/{bid}/{idx}.json 标准三键（title/content/index）
"""
import json
import os
import re
import hashlib

ROOT = "/Users/sen/DeepPhilosophy"
TMP = os.path.join(ROOT, "backend/tools/_tmp/aquinas")
CH_DIR = os.path.join(ROOT, "backend/data/book_chapters")
BOOK_ID = hashlib.sha256("summa-theologica-selections-evil-law-pg17611-17897".encode()).hexdigest()[:12]

BOOK_META = {
    "id": BOOK_ID,
    "title": "神学大全选编：论恶与论律法（英译公版）",
    "author": "托马斯·阿奎那（Thomas Aquinas）",
    "region": "西方",
    "file_type": "txt",
    "file_size": 0,
    "chapterCount": 10,
    "rank": 47.5,
    "tags": ["中世纪哲学", "托马斯主义", "恶", "自然法", "伦理学"],
    "cover": "",
    "summary": ("《神学大全》选编，收录第一集第48-49题（论恶：恶的本性、恶在善中、"
                "恶的划分与恶因）与第一集之二第90-97题（论法律总论：法的本质、种类、"
                "效果、永恒法、自然法、人法、法律的变动）。英译为英多明我会修士译本"
                "（Benziger Brothers, 1911-1936，公有领域），经 Project Gutenberg 数字化。"),
}


def load(path):
    return open(path, encoding="utf-8").read()


def slice_q(text, q_start, q_end=None):
    i = text.find(f"QUESTION {q_start}")
    if i < 0:
        raise ValueError(f"QUESTION {q_start} not found")
    j = text.find(f"QUESTION {q_end}", i + 10) if q_end else -1
    return text[i:j] if j > i else text[i:]


def clean(t):
    t = re.sub(r"\[trans\. [^\]]*\]", "", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def paragraphs(t):
    t = clean(t)
    paras, buf = [], []
    for line in t.split("\n"):
        if line.strip():
            buf.append(line.strip())
        elif buf:
            paras.append(" ".join(buf)); buf = []
    if buf:
        paras.append(" ".join(buf))
    return paras


def main():
    t1 = load(os.path.join(TMP, "st_part1.txt"))
    t2 = load(os.path.join(TMP, "st_part2_1.txt"))

    chapters = []
    # Part I: q.48-49
    q48 = slice_q(t1, 48, 49)
    q49 = slice_q(t1, 49, 50)
    chapters.append({"title": "第一集 第48题 论受造物的特殊区分：恶与善的关系（共六论）", "text": q48})
    chapters.append({"title": "第一集 第49题 恶的原因（共六论）", "text": q49})
    # Part II-I: q.90-97
    t2titles = {
        90: "第二集之一 第90题 法律的本质（共四论）",
        91: "第二集之一 第91题 各种法律（共四论）",
        92: "第二集之一 第92题 法律的效果（共二论）",
        93: "第二集之一 第93题 永恒法（共六论）",
        94: "第二集之一 第94题 自然法（共六论）",
        95: "第二集之一 第95题 人法（共四论）",
        96: "第二集之一 第96题 人法的权力（共六论）",
        97: "第二集之一 第97题 法律的变动（共四论）",
    }
    for q in range(90, 97):
        a = t2.find(f"QUESTION {q}")
        b = t2.find(f"QUESTION {q+1}", a + 10)
        chapters.append({"title": t2titles[q], "text": t2[a:b]})
    chapters.append({"title": t2titles[97], "text": t2[t2.find("QUESTION 97"):]})

    out_dir = os.path.join(CH_DIR, BOOK_ID)
    os.makedirs(out_dir, exist_ok=True)
    for i, ch in enumerate(chapters, 1):
        paras = paragraphs(ch["text"])
        doc = {"title": ch["title"],
               "content": [{"type": "text", "value": p} for p in paras],
               "index": i}
        json.dump(doc, open(os.path.join(out_dir, f"{i}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    meta = {"book_id": BOOK_ID, "chapterCount": len(chapters)}
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    total_chars = sum(len(c["text"]) for c in chapters)
    BOOK_META["file_size"] = total_chars
    print(f"入库完成: {BOOK_ID} 10 章, 共 {total_chars} 字符")
    print("BOOK_META:", json.dumps(BOOK_META, ensure_ascii=False)[:200])


if __name__ == "__main__":
    main()
