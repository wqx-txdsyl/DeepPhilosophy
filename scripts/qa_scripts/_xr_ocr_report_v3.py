# -*- coding: utf-8 -*-
"""OCR 完整自动汇报 v3（监视器每 5 分钟调用，必须用 DeepPhilosophy/.venv python 跑——需要 fitz）
输出一行完整汇报: 当前书 | 队列位置 | 页进度/总页数/百分比 | 预计剩余时间 | books/checkpoint
- 总页数: fitz 读真实 PDF 页数（缓存 _xr_pdf_pages.json）
- 速率: 快照对比（_xr_ocr_prev.json 存 {safe: [pages, ts]}）→ 秒/页 → 剩余时间
- 停滞检测: checkpoint mtime > 600s 输出告警
"""
import json, os, re, time, hashlib, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
BASE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(BASE, '_xr_ocr_prev.json')
PAGES_CACHE = os.path.join(BASE, '_xr_pdf_pages.json')
BOOKS_DIR = 'F:/philosophy'

def safe_key(rel):
    return re.sub(r'[^\w\-.]', '_', rel)

# ── 扫描 F:/philosophy 全部 pdf（应用引擎同样的合并规则跳过）──
MERGE_RULES = {
    "西方/弗里德里希·恩格斯/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf",
    "西方/弗里德里希·恩格斯/共产党宣言.pdf",
    "西方/弗里德里希·恩格斯/德意志意识形态（节选本）.pdf",
    "西方/波爱修斯/哲学规劝录 哲学的慰藉.pdf",
}
pdf_safe2rel = {}
for region in ['东方', '西方']:
    rp = os.path.join(BOOKS_DIR, region)
    if not os.path.isdir(rp):
        continue
    for author in sorted(os.listdir(rp)):
        ap = os.path.join(rp, author)
        if not os.path.isdir(ap):
            continue
        for fn in sorted(os.listdir(ap)):
            fp = os.path.join(ap, fn)
            if not os.path.isfile(fp):
                continue
            rel = os.path.relpath(fp, BOOKS_DIR).replace('\\', '/')
            if rel in MERGE_RULES:
                continue
            if fn.lower().endswith('.pdf'):
                pdf_safe2rel[safe_key(rel)] = rel

# ── checkpoint ──
ck = json.load(open(CK, encoding='utf-8'))
books = ck.get('books', {})
ocr = ck.get('ocr', {})
done = len(books)
now_pages = {safe: len(p) for safe, p in ocr.items() if isinstance(p, dict) and p}
mtime = os.path.getmtime(CK)
stale = (time.time() - mtime) > 600

# 当前书: 快照对比增长最大（排除已入库书——books 键 rel 的 safe 名）
done_safes = {safe_key(r) for r in books}
prev = json.load(open(PREV, encoding='utf-8')) if os.path.exists(PREV) else {}
prev_pages = {k: (v[0] if isinstance(v, list) else v) for k, v in prev.items()} if prev else {}
prev_ts = {k: (v[1] if isinstance(v, list) else None) for k, v in prev.items()} if prev else {}
now = time.time()
grow = {k: v - prev_pages.get(k, 0) for k, v in now_pages.items() if k not in done_safes and v > prev_pages.get(k, 0)}
if grow:
    cur_safe = max(grow, key=grow.get)
elif prev_pages:
    # 无增长: 模型重载窗口 → 取未入库页数最大
    cand = {k: v for k, v in now_pages.items() if k not in done_safes}
    cur_safe = max(cand, key=cand.get) if cand else None
else:
    cand = {k: v for k, v in now_pages.items() if k not in done_safes}
    cur_safe = max(cand, key=cand.get) if cand else None
# 快照更新（存 [pages, ts]）
json.dump({k: [v, now] for k, v in now_pages.items()}, open(PREV, 'w', encoding='utf-8'), ensure_ascii=False)

# ── 总页数: fitz 读（缓存）──
pages_cache = json.load(open(PAGES_CACHE, encoding='utf-8')) if os.path.exists(PAGES_CACHE) else {}
total = None
if cur_safe and cur_safe in pdf_safe2rel:
    rel = pdf_safe2rel[cur_safe]
    if cur_safe in pages_cache:
        total = pages_cache[cur_safe]
    elif HAS_FITZ:
        try:
            doc = fitz.open(os.path.join(BOOKS_DIR, rel))
            total = doc.page_count
            doc.close()
            pages_cache[cur_safe] = total
            json.dump(pages_cache, open(PAGES_CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
        except Exception:
            total = None

# ── 剩余时间: 速率 = (增长页数)/(时间差) ──
eta = None
if cur_safe and total:
    cur = now_pages.get(cur_safe, 0)
    if cur_safe in prev_pages and prev_ts.get(cur_safe):
        dp = cur - prev_pages[cur_safe]
        dt = now - prev_ts[cur_safe]
        if dp > 0 and dt > 0:
            rate = dt / dp  # 秒/页
            eta = (total - cur) * rate

# ── 输出 ──
out = []
if stale:
    out.append('⚠ 引擎停滞: checkpoint %.0f 秒未写入!' % (time.time() - mtime))
elif cur_safe:
    cur = now_pages.get(cur_safe, 0)
    pct = '%d%%' % round(100 * cur / total) if total else '?%'
    eta_s = '~%d 分钟' % max(1, round(eta / 60)) if eta and eta > 0 else '未知'
    name = cur_safe.replace('_', ' ').replace('.pdf', '')
    # 队列位置: 断点组(4本) / 全新批次(45本)
    in_done = cur_safe in done_safes
    pos = ('[断点组]' if not in_done else '[已完成]')
    out.append('%s %s/%s页 %s 剩%s | books=%d mtime=%s ckpt=%.1fMB%s' % (
        name, cur, total, pct, eta_s, done,
        time.strftime('%H:%M:%S', time.localtime(mtime)), os.path.getsize(CK) / 1048576,
        ' +fitz' if total is not None else ' +无fitz'))
else:
    out.append('当前书: 无页增长（模型加载/空闲） books=%d' % done)
print(' | '.join(out))
