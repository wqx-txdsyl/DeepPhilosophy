"""合并 books.json 中同书名多条目"""
import json, os

BASE = os.path.dirname(__file__)
BOOKS_PATH = os.path.join(BASE, "..", "app", "public", "books.json")
DETAIL_DIR = os.path.join(BASE, "..", "app", "public", "book_detail")

books = json.load(open(BOOKS_PATH, "r", encoding="utf-8"))

# ─── 论自然（7个前苏格拉底残篇）→ 合并为1条合集 ───
LUN_ZIRAN_IDS = {'010add665439','62c6222feb1f','e63edad2d08d',  # 残篇：巴门尼德/赫拉克利特/恩培多克勒
                 '4db93f7bc232','4e99f0f2af9e','51b13df7695f',  # 已佚失：阿那克西曼德/泰勒斯/阿那克西美尼
                 '6624e23ed0ef'}  # 伊壁鸠鲁
LUN_ZIRAN_KEEP = '010add665439'  # 保留巴门尼德那条

# ─── 加缪全集（5卷）→ 删掉无卷号的通版，保留4个分卷 ───
CAMUS_IDS = {'全集': None}  # 需要查具体ID
camus_entries = [b for b in books if '加缪全集' in b['title']]
camus_general = [b for b in camus_entries if b['title'] == '加缪全集']
camus_volumes = [b for b in camus_entries if b['title'] != '加缪全集']

print("加缪全集:")
for b in camus_entries:
    print(f"  {b['id']}  {b['title']}  {b['file_type']}  size={b.get('file_size',0)}")

if camus_general and camus_volumes:
    # 如果通版比各分卷加起来还大 → 保留通版，删分卷
    # 否则 → 删通版，保留分卷
    general_size = camus_general[0].get('file_size', 0)
    vols_size = sum(v.get('file_size', 0) for v in camus_volumes)

    if general_size >= vols_size * 0.9:
        # 通版包含全部内容，保留通版
        CAMUS_REMOVE = [v['id'] for v in camus_volumes]
        CAMUS_KEEP = camus_general[0]['id']
        print(f"  → keep general ({general_size/1024:.0f}KB >= {vols_size/1024:.0f}KB total), remove {len(CAMUS_REMOVE)} volumes")
    else:
        CAMUS_REMOVE = [camus_general[0]['id']]
        CAMUS_KEEP = camus_volumes[0]['id']  # doesn't matter, we keep all volumes
        print(f"  → keep {len(camus_volumes)} volumes, remove general")
else:
    CAMUS_REMOVE = []
    CAMUS_KEEP = None
    print("  → nothing to merge")

# ─── 执行合并 ───
REMOVE_IDS = set(LUN_ZIRAN_IDS) - {LUN_ZIRAN_KEEP}
REMOVE_IDS.update(CAMUS_REMOVE)

new_books = []
lun_ziran_kept = False
for b in books:
    if b['id'] in REMOVE_IDS:
        continue

    # 论自然：更新保留条目
    if b['id'] == LUN_ZIRAN_KEEP:
        b['title'] = '论自然（残篇合集）'
        b['author'] = '前苏格拉底哲学家（合集）'
        b['tags'] = list(set((b.get('tags') or []) + ['前苏格拉底哲学', '古希腊哲学', '本体论', '自然哲学']))
        lun_ziran_kept = True

    # 加缪全集：如果保留通版，删除分卷后无需额外处理
    # 如果保留分卷，通版已在上方被跳过

    new_books.append(b)

json.dump(new_books, open(BOOKS_PATH, "w", encoding="utf-8"), ensure_ascii=False)
print(f"\nbooks.json: {len(books)} → {len(new_books)} (removed {len(books)-len(new_books)})")

# ─── 更新 book_detail ───
if lun_ziran_kept:
    dp = os.path.join(DETAIL_DIR, f"{LUN_ZIRAN_KEEP}.json")
    if os.path.exists(dp):
        d = json.load(open(dp, "r", encoding="utf-8"))
        d['title'] = '论自然（残篇合集）'
        d['author'] = '前苏格拉底哲学家（合集）'
        d['tags'] = list(set((d.get('tags') or []) + ['前苏格拉底哲学', '古希腊哲学', '本体论', '自然哲学']))
        json.dump(d, open(dp, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"detail updated: {LUN_ZIRAN_KEEP}")

print("Done.")
