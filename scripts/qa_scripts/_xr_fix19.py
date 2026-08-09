# -*- coding: utf-8 -*-
"""19 本批次统一修复：8 本书
1. 哲学书简   5f838ef64e5e  章0-25 删"注N"注标（章26 注释章保留）
2. 维特根斯坦 c0e78ea6f80a  全书删"注N"（2439处）+ toc[3] 去 ISBN"16463-4"
3. 瓦尔登湖   5135fe68ee4a  删数字上标注标
4. 认识世界   c97cb4e6161a  正文删【N】(529处) + toc 标题删【N】(18条)
5. 与神对话   7657ef4a2cd3  toc 删 8 条卷页条目
6. 现象学     ef76ae88994f  删[0]目录章 + 合并[13-16]课堂讨论 → 37→34章
7. 黑格尔     bbac1be0bb4b  删 8 封面章 + 7 商务序章（留41）→ 460→445章; [0]去空格标题
8. 尼采       4cc9d23c7dbf  toc 10 条补章标题（源目录）
"""
import json, os, re, glob, shutil

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
CHANGED_CC = {}  # bid -> (新章数, 旧章数)

def load_meta(bid):
    return json.load(open(os.path.join(DP, bid, 'meta.json'), encoding='utf-8'))

def save_meta(bid, m):
    json.dump(m, open(os.path.join(DP, bid, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def load_ch(bid, n):
    return json.load(open(os.path.join(DP, bid, f'{n}.json'), encoding='utf-8'))

def save_ch(bid, n, c):
    json.dump(c, open(os.path.join(DP, bid, f'{n}.json'), 'w', encoding='utf-8'), ensure_ascii=False)

def del_ch(bid, n):
    os.remove(os.path.join(DP, bid, f'{n}.json'))

def chap_count(bid):
    return len([f for f in os.listdir(os.path.join(DP, bid)) if f.endswith('.json') and f != 'meta.json'])

def log(msg):
    print(msg)

# ---------- 1) 哲学书简：删正文"注N"，章26保留 ----------
bid = '5f838ef64e5e'
m = load_meta(bid)
tot = 0
for t in m['toc']:
    n = t.get('index')
    if n >= 26:   # 章26 注释章保留
        continue
    c = load_ch(bid, n)
    cnt = 0
    for b in c['content']:
        if isinstance(b, dict) and isinstance(b.get('value'), str):
            v = b['value']
            nv = re.sub(r'注\d+', '', v)
            if nv != v:
                cnt += v.count('注')  # 粗统计
                b['value'] = nv
    if cnt:
        save_ch(bid, n, c)
        tot += cnt
log(f'[1] 哲学书简: 章0-25 删除注标段 {tot} 段')

# ---------- 2) 维特根斯坦：全书删"注N" + toc[3] 去 ISBN ----------
bid = 'c0e78ea6f80a'
m = load_meta(bid)
tot = 0
for t in m['toc']:
    n = t.get('index')
    c = load_ch(bid, n)
    cnt = 0
    for b in c['content']:
        if isinstance(b, dict) and isinstance(b.get('value'), str):
            v = b['value']
            nv = re.sub(r'注\d+', '', v)
            nv = re.sub(r'\s+([，。；、：！？])', r'\1', nv)  # 清理注标残留空格
            nv = re.sub(r'\x20{2,}', ' ', nv)
            if nv != v:
                cnt += 1
                b['value'] = nv
    if cnt:
        save_ch(bid, n, c)
        tot += cnt
# toc[3] 去 ISBN
for t in m['toc']:
    if t.get('index') == 3:
        old = t['title']
        t['title'] = re.sub(r'16463-4', '', t['title'])
        t['title'] = re.sub(r'哲学研究(\D)', '哲学研究：\\1', t['title'])
        t['title'] = t['title'].rstrip()
        log(f'[2] 维特根斯坦 toc[3]: {old} -> {t["title"]}')
save_meta(bid, m)
log(f'[2] 维特根斯坦: 删除注标 {tot} 段（章级）')

# ---------- 3) 瓦尔登湖：删数字上标注标 ----------
bid = '5135fe68ee4a'
files = sorted(glob.glob(os.path.join(DP, bid, '[0-9]*.json')),
               key=lambda p: int(re.search(r'(\d+)\.json', p).group(1)))
pat = re.compile(r'([\u4e00-\u9fff])\s+(\d{1,4})\s+((?![年日月时点分秒章节页码里米斤元])[\u4e00-\u9fff，。；、：！？）】」』])')
tot = 0
for f in files:
    n = int(re.search(r'(\d+)\.json', f).group(1))
    c = json.load(open(f, encoding='utf-8'))
    cnt = 0
    for b in c['content']:
        if isinstance(b, dict) and isinstance(b.get('value'), str):
            v = b['value']
            nv = pat.sub(r'\1\3', v)
            nv = re.sub(r'\x20{2,}', ' ', nv)
            if nv != v:
                cnt += 1
                b['value'] = nv
    if cnt:
        save_ch(bid, n, c)
        tot += cnt
log(f'[3] 瓦尔登湖: 删除数字上标 {tot} 段')

# ---------- 4) 认识世界：正文删【N】 + toc 删【N】 ----------
bid = 'c97cb4e6161a'
files = sorted(glob.glob(os.path.join(DP, bid, '[0-9]*.json')),
               key=lambda p: int(re.search(r'(\d+)\.json', p).group(1)))
pat = re.compile(r'【\d+】')
tot = 0
for f in files:
    n = int(re.search(r'(\d+)\.json', f).group(1))
    c = json.load(open(f, encoding='utf-8'))
    cnt = 0
    for b in c['content']:
        if isinstance(b, dict) and isinstance(b.get('value'), str):
            v = b['value']
            nv = pat.sub('', v)
            nv = re.sub(r'\s*\*\s*$', '', nv)  # 段尾 * 分隔符
            if nv != v:
                cnt += len(pat.findall(v))
                b['value'] = nv
    if cnt:
        save_ch(bid, n, c)
        tot += cnt
m = load_meta(bid)
for t in m['toc']:
    if pat.search(t.get('title', '')):
        t['title'] = pat.sub('', t['title'])
save_meta(bid, m)
log(f'[4] 认识世界: 正文删【N】 {tot} 处, toc 标题已清')

# ---------- 5) 与神对话：toc 删 8 条卷页 ----------
bid = '7657ef4a2cd3'
m = load_meta(bid)
DROP = ['第一卷 与神对话1', '第二卷 与神对话2', '第三卷 与神对话3', '第四卷 与神为友',
        '第五卷 与神合一', '第一部分 人类的十大幻觉', '第二部分 掌握幻觉', '第三部分 与内在造物主相遇']
before = len(m['toc'])
m['toc'] = [t for t in m['toc'] if t.get('title') not in DROP]
after = len(m['toc'])
save_meta(bid, m)
log(f'[5] 与神对话: toc {before} -> {after} 条')

# ---------- 6) 现象学：删[0]目录章 + 合并[13-16] ----------
bid = 'ef76ae88994f'
m = load_meta(bid)
# 6a 合并 13-16
c13 = load_ch(bid, 13)
for n in (14, 15, 16):
    cn = load_ch(bid, n)
    c13['content'].extend(cn['content'])
save_ch(bid, 13, c13)
for n in (14, 15, 16):
    del_ch(bid, n)
# 6b toc: 删 0 和 14/15/16
m['toc'] = [t for t in m['toc'] if t.get('index') not in (0, 14, 15, 16)]
save_meta(bid, m)
# 6c 删文件 0
if os.path.exists(os.path.join(DP, bid, '0.json')):
    del_ch(bid, 0)
log(f'[6] 现象学: 删目录章0 + 合并13-16, toc={len(m["toc"])}, 文件={chap_count(bid)}')

# ---------- 7) 黑格尔：删 8 封面章 + 7 商务序章（留41）+ [0]标题 ----------
bid = 'bbac1be0bb4b'
m = load_meta(bid)
DROP_FILES = [40, 99, 138, 164, 399, 419, 428, 449,       # 封面/目录章
              100, 139, 165, 400, 420, 429, 450]           # 商务序重复（留41）
for n in DROP_FILES:
    if os.path.exists(os.path.join(DP, bid, f'{n}.json')):
        del_ch(bid, n)
before = len(m['toc'])
m['toc'] = [t for t in m['toc'] if t.get('index') not in set(DROP_FILES)]
# [0] 第 一 章 -> 第一章
for t in m['toc']:
    if t.get('index') == 0:
        t['title'] = re.sub(r'第\s+一\s+章', '第一章', t['title'])
        log(f'[7] 黑格尔 toc[0]: -> {t["title"]}')
save_meta(bid, m)
log(f'[7] 黑格尔: 删 {len(before)-len(m["toc"])} 章, toc={len(m["toc"])}, 文件={chap_count(bid)}')

# ---------- 8) 尼采：toc 补 10 处章标题 ----------
bid = '4cc9d23c7dbf'
m = load_meta(bid)
NEW_TITLES = {
    6: '第二章 瓦格纳与现代性',
    9: '第三章 苏格拉底与科学乐观主义',
    12: '第四章 被钉十字架的上帝',
    21: '第二章 非道德论者的道德观',
    26: '第三章 快乐的与不快乐的科学',
    30: '第四章 尼采与启蒙二重性',
    41: '第二章 谁是尼采的查拉图斯特拉形象',
    46: '第三章 权力意志',
    50: '第四章 相同者的永恒轮回',
    54: '结语 未来哲学序曲',
}
for t in m['toc']:
    n = t.get('index')
    if n in NEW_TITLES:
        log(f'[8] 尼采 toc[{n}]: {t["title"]} -> {NEW_TITLES[n]}')
        t['title'] = NEW_TITLES[n]
save_meta(bid, m)
log(f'[8] 尼采: 补 {len(NEW_TITLES)} 处章标题')

log('=== 全部完成 ===')
