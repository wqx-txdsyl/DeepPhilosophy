#!/usr/bin/env python3
"""任务A 页面验收工具：按页校验星云有效节点/辞海独立词条门槛与结构完整性。
用法: python3 validate_school.py app/public/schools/data/school_X.json [more.json ...]
退出码: 0=全部达标 1=有页面未达标
"""
import json, re, sys, os, hashlib

WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
RETIRED = set(json.load(open(os.path.join(os.path.dirname(__file__), 'retired-a.json')))) if os.path.exists(os.path.join(os.path.dirname(__file__), 'retired-a.json')) else set()

AUDIT_TONE = re.compile(r'门禁|本轮|核得|未核|冻结|编译产物|镜像|1301|source-backed|partial-text|字段路径|游标|验收|coverage|已读回执|实读|待领取|review|context字段|开发')

def word_key(w):
    w = re.sub(r'[（(].*?[)）]', '', str(w or '')).strip()
    return re.sub(r'[\s·•—–-]', '', w).lower()

def normalize_like_frontend(raw):
    """模拟 schoolContent.normalizeSchool 的过滤（含退役作者过滤）。"""
    def objs(v):
        if not isinstance(v, list): return []
        out = []
        for x in v:
            if isinstance(x, dict): out.append(x)
        return out
    thinkers = [t for t in objs(raw.get('thinkers')) if str(t.get('name','')).strip() and str(t.get('name','')).strip() not in RETIRED]
    relations = [r for r in objs(raw.get('relations')) if str(r.get('from','')).strip() and str(r.get('to','')).strip()
                 and str(r.get('from','')).strip() not in RETIRED and str(r.get('to','')).strip() not in RETIRED]
    cihai = [c for c in objs(raw.get('cihai')) if str(c.get('word','')).strip() and str(c.get('def','')).strip()]
    timeline = [t for t in objs(raw.get('timeline')) if str(t.get('event','')).strip()]
    quotes = [q for q in objs(raw.get('quotes')) if str(q.get('text','')).strip()]
    works = [w for w in objs(raw.get('works')) if str(w.get('title','')).strip()]
    sub = raw.get('subSchools')
    if not isinstance(sub, list): sub = list(sub.values()) if isinstance(sub, dict) else []
    subschools = [s for s in sub if isinstance(s, dict) and str(s.get('name','')).strip()]
    return thinkers, relations, cihai, timeline, quotes, works, subschools

def check(path, min_nodes=30, min_cihai=30):
    d = json.load(open(path))
    name = d.get('name', os.path.basename(path))
    thinkers, relations, cihai, timeline, quotes, works, subs = normalize_like_frontend(d)
    # 星云有效节点 = thinkers ∪ relations 端点（前端 constellationNodes 口径，先经退役过滤）
    nodes = {}
    for t in thinkers: nodes.setdefault(t['name'], 'thinker')
    for r in relations:
        for end in (r['from'], r['to']): nodes.setdefault(end, 'related')
    problems = []
    if len(nodes) < min_nodes: problems.append(f"节点{len(nodes)}<{min_nodes}")
    if len(relations) < min_nodes // 2: problems.append(f"关系边{len(relations)}过少(<{min_nodes//2})")
    # 孤立节点检查（除必要类别节点外，节点应有至少一条关系）
    linked = set()
    for r in relations: linked.add(r['from']); linked.add(r['to'])
    orphans = [n for n in nodes if n not in linked]
    if orphans: problems.append(f"孤立节点{len(orphans)}: {','.join(orphans[:6])}")
    # 辞海：去重后独立词条且必须有 def
    groups = {}
    for c in cihai:
        k = word_key(c['word'])
        if k not in groups: groups[k] = c
    if len(groups) < min_cihai: problems.append(f"辞海独立词条{len(groups)}<{min_cihai}")
    empty_defs = [c['word'] for c in cihai if len(str(c.get('def','')).strip()) < 40]
    if empty_defs: problems.append(f"释义过短{len(empty_defs)}条: {','.join(empty_defs[:5])}")
    # 关系端点必须在节点集中（有效边）
    invalid = [f"{r['from']}→{r['to']}" for r in relations if r['from'] not in nodes or r['to'] not in nodes]
    if invalid: problems.append(f"无效边{len(invalid)}: {','.join(invalid[:5])}")
    # 格式化关系检查：label 缺失、过短或与 type 完全相同（模板边无效信息）
    generic = []
    for r in relations:
        lb, tp = str(r.get('label','')).strip(), str(r.get('type','')).strip()
        if not lb or len(lb) < 10:
            generic.append(f"{r['from']}→{r['to']}[label过短:{lb}]")
        elif tp and lb == tp:
            generic.append(f"{r['from']}→{r['to']}[label复述type:{lb}]")
    if generic: problems.append(f"格式化关系边{len(generic)}: " + '; '.join(generic[:5]))
    # 正文完整性
    if len(str(d.get('overview','')).strip()) < 400: problems.append("overview过短(<400字)")
    if len(str(d.get('conclusion','')).strip()) < 150: problems.append("conclusion过短(<150字)")
    # 审计口吻扫描（公开正文字段）
    tone_hits = []
    for field, val in [('overview', d.get('overview')), ('conclusion', d.get('conclusion')), ('subtitle', d.get('subtitle')), ('quote', d.get('quote'))]:
        m = AUDIT_TONE.search(str(val or ''))
        if m: tone_hits.append(f"{field}:{m.group(0)}")
    for i, t in enumerate(timeline):
        m = AUDIT_TONE.search(str(t.get('detail','')))
        if m: tone_hits.append(f"timeline[{i}]:{m.group(0)}")
    if tone_hits: problems.append("疑似审计口吻: " + '; '.join(tone_hits[:6]))
    ok = not problems
    print(f"{'PASS' if ok else 'FAIL'} {name} | 节点{len(nodes)} 边{len(relations)} 辞海{len(groups)}(共{len(cihai)}) 时间轴{len(timeline)} 金句{len(quotes)} 典籍{len(works)} 子流派{len(subs)}"
          + ('' if ok else ' | ' + ' ; '.join(problems)))
    return ok, {'nodes': len(nodes), 'relations': len(relations), 'cihai': len(groups), 'timeline': len(timeline)}

if __name__ == '__main__':
    files = sys.argv[1:]
    if not files: print(__doc__); sys.exit(2)
    all_ok = True
    for f in files:
        ok, _ = check(f)
        all_ok = all_ok and ok
    sys.exit(0 if all_ok else 1)
