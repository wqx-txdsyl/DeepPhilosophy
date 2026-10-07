#!/usr/bin/env python3
"""检查 editorial 包正文/era 是否泄漏编辑流程语言（面向用户的字段不得含内部术语）。

用法：python3 scripts/check_editorial_jargon.py [--fix-hint]
命中即打印清单并以非零退出；CI/晋升前必跑。白名单收录正当学术用语
（如丹尼特「多重草稿模型」、拉康「镜像阶段」、一般「可据此确认」）。
"""
import json, re, sys, os, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ED = os.path.join(BASE, 'app/public/philosopher/editorial')

PAT = re.compile(
    r'\.json|editorial/|eraSource|era=|canonical|站内|本包|本轮|互为镜像|证据记录'
    r'|legacy|旧数据|旧 data|批次\s*\d|同批|提请主编|建议主编|复核统一|复核说明'
    r'|资料包|既有包|逐字镜像|镜像对齐|era 字段|listingKind|sourceRefs|people\[\]'
    r'|端点|镜像留|新条|任务提示|单向记录|该包|type=\w|label=|evidenceKind=|from/to'
)
ERA_PAT = re.compile(r'站内|据此确认|旧数据|本包|批次|legacy|本轮|草稿|复核|证据记录|互为镜像|canonical')
# 正当学术用语豁免（命中 PAT 前先剔除这些短语再判断）
ALLOW = re.compile(r'多重草稿模型|镜像阶段|镜像自我|镜像神经元')

def fields(d):
    p = d.get('profile') or {}
    if isinstance(p.get('question'), str): yield ('question', p, 'question')
    ov = p.get('overview')
    if isinstance(ov, list):
        for i in range(len(ov)):
            if isinstance(ov[i], str): yield ('overview', ov, i)
    for key in ('life', 'concepts', 'people', 'bibliography', 'relations', 'readingRoutes'):
        arr = p.get(key)
        if isinstance(arr, list):
            for x in arr:
                if isinstance(x, dict):
                    for f in ('title', 'body', 'definition', 'era', 'summary', 'description', 'label', 'detail'):
                        if isinstance(x.get(f), str): yield (key, x, f)
    db = p.get('debate')
    if isinstance(db, dict):
        for f in ('title', 'year'):
            if isinstance(db.get(f), str): yield ('debate', db, f)
        paras = db.get('paragraphs')
        if isinstance(paras, list):
            for j in range(len(paras)):
                if isinstance(paras[j], str): yield ('debate', paras, j)

def main():
    hits = []
    for f in sorted(glob.glob(os.path.join(ED, '*.json'))):
        d = json.load(open(f))
        era = (d.get('identity') or {}).get('era', '')
        if ERA_PAT.search(era or ''):
            hits.append((d['name'], 'identity.era', era[:120]))
        for fname, c, k in fields(d):
            v = c[k]
            stripped = ALLOW.sub('', v)
            m = PAT.search(stripped)
            if m:
                hits.append((d['name'], fname, v[max(0, m.start() - 40):m.end() + 40].replace('\n', ' ')))
    if hits:
        print(f'编辑流程语言残留 {len(hits)} 处：')
        seen = set()
        for name, field, ctx in hits:
            key = (name, ctx[:40])
            if key in seen: continue
            seen.add(key)
            print(f'  [{name}|{field}] …{ctx}…')
        sys.exit(1)
    print('editorial 正文检查通过：无编辑流程语言残留')

if __name__ == '__main__':
    main()
