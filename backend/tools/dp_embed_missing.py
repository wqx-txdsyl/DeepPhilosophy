# -*- coding: utf-8 -*-
"""
dp_embed_missing.py — 增量补嵌入（2026-08-07, 2026-08-10 增强）
扫描 book_chapters 中 index.json 里缺失的书 → 只为缺失书生成向量 → 追加到现有向量库
不重跑已有向量（区别于 build_embeddings.py 全量重建）

2026-08-10 增强:
- 排除 _old_bad 归档垃圾目录（旧版错误章节, 绝不嵌入）
- 条目带 text_hash（章节文本 md5）; --check-hash 时比对全文库,
  内容变过（章节数没变但文本变了）的章节自动重嵌 —— 根治"重建书向量过期"
- 用法: python dp_embed_missing.py [--check-hash] [--force BID...]
"""
import json, os, sys, time, hashlib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS = os.path.join(BASE, "data", "book_chapters")
OUT = os.path.join(BASE, "data", "embeddings")

for line in open(os.path.join(os.path.dirname(BASE), ".env"), encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
KEY = os.environ.get("ZHIPU_API_KEY", "")
if not KEY:
    print("缺少 ZHIPU_API_KEY")
    sys.exit(1)

from openai import OpenAI
_emb_client = OpenAI(api_key=KEY, base_url="https://open.bigmodel.cn/api/paas/v4/", timeout=60)


def embed_batch(texts):
    for attempt, wait in enumerate([5, 10, 15]):
        try:
            resp = _emb_client.embeddings.create(model="embedding-2", input=texts)
            return [d.embedding for d in resp.data]
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(wait)


def chapter_text(bid, i):
    """读章节文本（与嵌入时一致: 文本块拼接, 前 1500 字）"""
    cp = os.path.join(CHAPTERS, bid, f"{i}.json")
    if not os.path.exists(cp):
        return None, None
    ch = json.load(open(cp, encoding="utf-8"))
    texts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
    text = " ".join(texts)[:1500]
    return ch.get("title", ""), text


def main():
    check_hash = "--check-hash" in sys.argv
    force = [a for a in sys.argv[1:] if not a.startswith("--")]
    if force:
        print(f"强制重嵌: {force}")

    # 现有索引
    ix_fp = os.path.join(OUT, "index.json")
    vec_fp = os.path.join(OUT, "vectors.npy")
    index = json.load(open(ix_fp, encoding="utf-8"))
    import numpy as np
    vectors = np.load(vec_fp).tolist() if os.path.exists(vec_fp) else []
    assert len(index) == len(vectors), f"index/vectors 数量不一致: {len(index)} vs {len(vectors)}"
    have = set(it["bid"] for it in index)
    print(f"现有向量库: {len(vectors)} 条, 覆盖 {len(have)} 本书")

    # 每书已有 (idx → hash)（旧条目无 hash 视为未知, 不触发重嵌）
    have_idx = {}
    for it in index:
        have_idx.setdefault(it["bid"], {})[it["idx"]] = it.get("hash")

    missing = []      # (bid, idx, title, text, old_has_hash)
    for bid in sorted(os.listdir(CHAPTERS)):
        if "_old_bad" in bid:
            continue  # 归档垃圾目录（旧版错误章节），绝不嵌入
        mp = os.path.join(CHAPTERS, bid, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp, encoding="utf-8"))
        n = meta.get("chapterCount", 0)
        for i in range(n):
            cp = os.path.join(CHAPTERS, bid, f"{i}.json")
            if not os.path.exists(cp):
                continue
            title, text = chapter_text(bid, i)
            if not text or len(text) < 20:
                continue
            h = hashlib.md5(text.encode()).hexdigest()
            old = (have_idx.get(bid) or {}).get(i)
            if bid in force:
                pass  # 强制重嵌（下面会删旧条目）
            elif old is not None:
                if check_hash and old and old != h:
                    print(f"  [hash 变化] {bid} idx={i} 重嵌")
                else:
                    continue  # 已有且内容未变
            missing.append((bid, i, title, text, old is not None))
    print(f"需嵌入章节: {len(missing)}（覆盖 {len(set(b for b, *_ in missing))} 本）")

    if not missing:
        print("无缺向量, 退出")
        return

    # 删除被替换的旧条目（force / hash 变化）
    drop = set()
    for b, i, *_ in missing:
        if (have_idx.get(b) or {}).get(i) is not None:
            drop.add((b, i))
    if drop:
        keep = [k for k, it in enumerate(index) if (it["bid"], it["idx"]) not in drop]
        print(f"替换旧条目 {len(index) - len(keep)} 条")
        index = [index[k] for k in keep]
        vectors = [vectors[k] for k in keep]

    items = [{"bid": b, "idx": i, "title": t, "text": tx} for b, i, t, tx, _ in missing]
    new_index, new_vecs = [], []
    BATCH = 8
    for pos in range(0, len(items), BATCH):
        batch = items[pos:pos + BATCH]
        try:
            vecs = embed_batch([it["text"] for it in batch])
        except Exception as e:
            print(f"批 {pos} 失败: {e}")
            continue
        for it, v in zip(batch, vecs):
            new_vecs.append(v)
            new_index.append({"bid": it["bid"], "idx": it["idx"], "title": it["title"],
                              "hash": hashlib.md5(it["text"].encode()).hexdigest()})
        if pos % 200 == 0 or pos + BATCH >= len(items):
            print(f"进度: {pos + BATCH}/{len(items)}")
        time.sleep(0.3)

    if not new_index:
        print("无新向量, 退出")
        return
    # 追加保存
    json.dump(index + new_index, open(ix_fp, "w", encoding="utf-8"), ensure_ascii=False)
    np.save(vec_fp, np.array(vectors + new_vecs, dtype="float32"))
    print(f"完成: 新增 {len(new_index)} 条 → 共 {len(index) + len(new_index)} 条向量")


if __name__ == "__main__":
    main()
