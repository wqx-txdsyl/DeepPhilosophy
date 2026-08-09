# -*- coding: utf-8 -*-
"""OCR 引擎完整状态报告 v2：从 checkpoint 读页进度（新引擎 stdout 未重定向，日志不可靠）
当前书判定: 上次运行快照对比（_xr_ocr_prev.json 存上次各书页数），页数增长最大 = 当前书
"""
import json, os, time

CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
PREV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_xr_ocr_prev.json')

ck = json.load(open(CK, encoding='utf-8'))
books = ck.get('books', {})
ocr = ck.get('ocr', {})
done = len(books)

# 各书页数（ocr 键 = safe 文件名 → {page: text}）
now_pages = {}
for safe, pages in ocr.items():
    if isinstance(pages, dict):
        now_pages[safe] = len(pages)

# 上次快照对比 → 增长最大 = 当前书（无快照时靠页号上限判当前书）
prev = json.load(open(PREV, encoding='utf-8')) if os.path.exists(PREV) else {}
grow = {k: v - prev.get(k, 0) for k, v in now_pages.items() if v > prev.get(k, 0)}
cur_safe = max(grow, key=grow.get) if grow else None
if cur_safe is None and prev:
    # 无增长但快照存在 → 可能在模型重载窗口；取页数最大且未入库的
    done_safes = {os.path.basename(r).replace('/', '_').replace('\\', '_').replace('.', '_') for r in books}
    cand = {k: v for k, v in now_pages.items()}
    cur_safe = max(cand, key=cand.get) if cand else None
json.dump(now_pages, open(PREV, 'w', encoding='utf-8'), ensure_ascii=False)

print('=== OCR 引擎状态 ===')
print('已完成入库: %d 本' % done)
if cur_safe:
    cur = now_pages[cur_safe]
    # 总页数：从 books 键找这本书？没有。用日志最后一次的 472 或标注
    name = cur_safe.replace('_', ' ').replace('.pdf', '')
    print('当前书: %s' % name)
    print('已 OCR 页数: %d 页' % cur)
    print('（总页数未知——引擎 stdout 未重定向，待引擎日志恢复）')
else:
    print('当前书: 无页增长（可能正在模型加载或空闲）')
# 各书页数列表
print()
print('--- ocr 缓存各书页数（top 10）---')
for k, v in sorted(now_pages.items(), key=lambda x: -x[1])[:10]:
    print('  %4d 页 | %s' % (v, k[:60]))
print()
print('checkpoint 最后写入: %s' % time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(CK))))
print('checkpoint 大小: %.1f MB' % (os.path.getsize(CK) / 1048576))
