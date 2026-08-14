# -*- coding: utf-8 -*-
"""build_embeddings.py — PhiAgent 章节向量索引构建（智谱 embedding-2）
遍历有章节的书 → 每章文本（前 1500 字）→ embedding → numpy 存盘
输出: backend/data/embeddings/vectors.npy + index.json
"""
import json, os, sys, time, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(os.path.dirname(BASE), "app", "public")
BOOKS_FILE = os.path.join(PUBLIC, "books.json")
CHAPTERS = os.path.join(BASE, "data", "book_chapters")
OUT = os.path.join(BASE, "data", "embeddings")
os.makedirs(OUT, exist_ok=True)

# .env
for line in open(os.path.join(os.path.dirname(BASE), ".env"), encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
KEY = os.environ.get("ZHIPU_API_KEY", "")
MODEL = "embedding-2"  # 硬编码（.env 的 ZHIPU_MODEL 是 chat 模型, 非 embedding）
if not KEY:
    print("缺少 ZHIPU_API_KEY")
    sys.exit(1)

from openai import OpenAI
_emb_client = OpenAI(api_key=KEY, base_url="https://open.bigmodel.cn/api/paas/v4/", timeout=60)

def embed_batch(texts):
    """智谱 embedding（openai SDK, AIAuthor 验证过的稳路径）"""
    for attempt, wait in enumerate([5, 10, 15]):
        try:
            resp = _emb_client.embeddings.create(model=MODEL, input=texts)
            return [d.embedding for d in resp.data]
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(wait)

def main():
    books = json.load(open(BOOKS_FILE, encoding="utf-8"))
    # 收集章节（有内容且非占位）
    items = []  # {bid, idx, title, text}
    for b in books:
        bid = b["id"]
        mp = os.path.join(CHAPTERS, bid, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp, encoding="utf-8"))
        n = meta.get("chapterCount", 0)
        if n <= 1 and not b.get("chapterCount"):
            continue
        for i in range(n):
            cp = os.path.join(CHAPTERS, bid, f"{i}.json")
            if not os.path.exists(cp):
                continue
            ch = json.load(open(cp, encoding="utf-8"))
            texts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
            text = " ".join(texts)[:1500]
            if len(text) < 20:
                continue
            items.append({"bid": bid, "idx": i, "title": ch.get("title", ""), "text": text})
    print(f"章节总数: {len(items)}")
    # 断点
    ckpt = os.path.join(OUT, "ckpt.json")
    done = json.load(open(ckpt, encoding="utf-8")) if os.path.exists(ckpt) else {"n": 0}
    start = done.get("n", 0)
    vectors, index = [], []
    BATCH = 8
    for pos in range(start, len(items), BATCH):
        batch = items[pos:pos + BATCH]
        try:
            vecs = embed_batch([it["text"] for it in batch])
        except Exception as e:
            print(f"批 {pos} 失败: {e} — 重试一次")
            time.sleep(5)
            try:
                vecs = embed_batch([it["text"] for it in batch])
            except Exception as e2:
                print(f"  重试失败, 跳过批: {e2}")
                continue
        for it, v in zip(batch, vecs):
            vectors.append(v)
            index.append({"bid": it["bid"], "idx": it["idx"], "title": it["title"]})
        if pos % 200 == 0 or pos + BATCH >= len(items):
            import numpy as np
            np.save(os.path.join(OUT, "vectors.npy"), np.array(vectors, dtype="float32"))
            json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False)
            json.dump({"n": pos + BATCH}, open(ckpt, "w", encoding="utf-8"))
            print(f"进度: {pos + BATCH}/{len(items)} ({len(vectors)} 向量)")
        time.sleep(0.3)
    import numpy as np
    np.save(os.path.join(OUT, "vectors.npy"), np.array(vectors, dtype="float32"))
    json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False)
    os.remove(ckpt) if os.path.exists(ckpt) else None
    print(f"完成: {len(vectors)} 向量")

if __name__ == "__main__":
    main()
