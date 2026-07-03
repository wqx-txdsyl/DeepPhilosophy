"""严格仿照现有流派格式，从 JSON 生成 inline DATA 并插入 SchoolDetailPage"""
import json, re, os

JSON_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data')
SD_FILE  = os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'pages', 'SchoolDetailPage.jsx')

SCHOOLS = ['萨满哲学','北极原住民哲学','南岛哲学','高加索哲学','高加索-草原哲学','太平洋原住民哲学']
VAR_MAP = {n: n.replace('-','') for n in SCHOOLS}

def gen_const(name, d):
    """Generate JS const DATA block, matching existing format exactly"""
    vn = VAR_MAP[name] + '_DATA'
    j = lambda x: json.dumps(x, ensure_ascii=False)
    ja = lambda arr: '[' + ', '.join(j(x) for x in arr) + ']' if arr else '[]'

    parts = [f'const {vn} = {{']
    parts.append(f'  name: {j(d.get("name",name))},')
    parts.append(f'  subtitle: {j(d.get("subtitle",""))},')
    parts.append(f'  overview: {j(d.get("overview",""))},')
    parts.append(f'  quote: {j(d.get("quote",""))},')
    parts.append(f'  quoteAuthor: {j(d.get("quoteAuthor",""))},')

    # timeline
    parts.append('  timeline: [')
    for e in d.get('timeline',[]):
        parts.append(f'    {{year: {j(e.get("year",""))}, event: {j(e.get("event",""))}, detail: {j(e.get("detail",""))}, type: {j(e.get("type","event"))}}},')
    parts.append('  ],')

    # thinkers
    parts.append('  thinkers: [')
    for t in d.get('thinkers',[]):
        w = t.get('works',[])
        if isinstance(w, str):
            try: w = json.loads(w.replace("'",'"'))
            except: w = [w]
        if w and isinstance(w[0], dict):
            w = [x.get('title','') for x in w]
        parts.append(f'    {{name: {j(t.get("name",""))}, sub: {j(t.get("sub",""))}, era: {j(t.get("era",""))}, influence: {t.get("influence",5) or 5}, key: {j(t.get("key",""))}, works: {ja(w)}}},')
    parts.append('  ],')

    # relations
    parts.append('  relations: [')
    for r in d.get('relations',[]):
        parts.append(f'    {{from: {j(r.get("from",""))}, to: {j(r.get("to",""))}, label: {j(r.get("label",""))}}},')
    parts.append('  ],')

    # cihai
    parts.append('  cihai: [')
    for c in d.get('cihai',[]):
        parts.append(f'    {{word: {j(c.get("word",""))}, def: {j(c.get("def",""))}, source: {j(c.get("source",""))}}},')
    parts.append('  ],')

    # quotes
    parts.append('  quotes: [')
    for q in d.get('quotes',[]):
        parts.append(f'    {{text: {j(q.get("text",""))}, author: {j(q.get("author",""))}, exp: {j(q.get("exp",""))}}},')
    parts.append('  ],')

    # works (school)
    parts.append('  works: [')
    for w in d.get('works',[]):
        if isinstance(w, dict):
            parts.append(f'    {{title: {j(w.get("title",""))}, author: {j(w.get("author",""))}, era: {j(w.get("era",""))}, desc: {j(w.get("desc",""))}}},')
        else:
            parts.append(f'    {j(str(w))},')
    parts.append('  ],')

    # conclusion
    parts.append(f'  conclusion: {j(d.get("conclusion",""))},')
    parts.append(f'  closingQuote: {j(d.get("closingQuote","") or d.get("quote",""))},')

    # meta
    meta = d.get('meta',{})
    if meta:
        parts.append('  meta: {')
        for mk, mv in meta.items():
            parts.append(f'    {j(mk)}: {j(mv)},')
        parts.append('  },')

    parts.append(f'  region: {j(d.get("region","世界"))},')
    parts.append(f'  bg: {j(d.get("bg", f"url(/schools/{name}.jpg)"))},')

    # sub_schools
    ss = d.get('sub_schools',{})
    if ss:
        parts.append('  sub_schools: {')
        for sk, sv in ss.items():
            parts.append(f'    {j(sk)}: {{name: {j(sv.get("name",sk))}, desc: {j(sv.get("desc",""))}}},')
        parts.append('  },')

    parts.append('};')
    return '\n'.join(parts)

# === MAIN ===
print('Generating DATA blocks...')
data_blocks = []
for name in SCHOOLS:
    jp = os.path.join(JSON_DIR, f'school_{name}.json')
    with open(jp, 'r', encoding='utf-8') as f:
        d = json.load(f)
    block = gen_const(name, d)
    data_blocks.append(block)
    print(f'  {VAR_MAP[name]}_DATA: {len(block)} chars')

# Read SD
with open(SD_FILE, 'r', encoding='utf-8') as f:
    sd = f.read()

# Insert DATA blocks AFTER the last existing inline DATA and BEFORE the SCHOOL_MAP
# Find 'const 黑人哲学_DATA' and insert after it
marker = 'const 黑人哲学_DATA'
pos = sd.find(marker)
assert pos > 0, 'Cannot find marker'
# Find the };\n ending
depth = 0
start_brace = sd.index('{', pos)
for i in range(start_brace, len(sd)):
    if sd[i] == '{': depth += 1
    elif sd[i] == '}':
        depth -= 1
        if depth == 0:
            pos = i + 2  # after };
            break

insert_text = '\n\n// === 6 NEW WORLD SCHOOLS ===\n' + '\n\n'.join(data_blocks) + '\n'
sd = sd[:pos] + insert_text + sd[pos:]

# Build SCHOOL_MAP entries (use ASCII bg filenames)
BG_ASCII = {'萨满哲学':'shaman','北极原住民哲学':'arctic','南岛哲学':'austronesian','高加索哲学':'caucasus','高加索-草原哲学':'caucasus-steppe','太平洋原住民哲学':'pacific'}
map_entries = []
for name in SCHOOLS:
    vn = VAR_MAP[name] + '_DATA'
    bg_name = BG_ASCII[name]
    map_entries.append(f"  '{name}': {{ data:{vn}, sub:{{}}, ci:[], bg:'url(/schools/{bg_name}.jpg)' }},")

# Insert SCHOOL_MAP entries after '黑人哲学'
black_marker = "  '黑人哲学': { data:黑人哲学_DATA, sub:{}, ci:[], bg:'url(/schools/黑人哲学.jpg)' },\n"
bpos = sd.find(black_marker)
assert bpos > 0, 'Cannot find black philosophy entry'
sd = sd[:bpos + len(black_marker)] + '\n'.join(map_entries) + '\n' + sd[bpos + len(black_marker):]

# Also add ENG_NAMES
eng_marker = "  '黑人哲学': 'BLACK PHILOSOPHY',\n"
epos = sd.find(eng_marker)
assert epos > 0, 'Cannot find ENG_NAMES'
eng_entries = []
eng_names = {
    '萨满哲学': 'SHAMANIC PHILOSOPHY',
    '北极原住民哲学': 'ARCTIC INDIGENOUS PHILOSOPHY',
    '南岛哲学': 'AUSTRONESIAN PHILOSOPHY',
    '高加索哲学': 'CAUCASIAN PHILOSOPHY',
    '高加索-草原哲学': 'CAUCASIAN-STEPPE PHILOSOPHY',
    '太平洋原住民哲学': 'PACIFIC INDIGENOUS PHILOSOPHY',
}
for name in SCHOOLS:
    eng_entries.append(f"  '{name}': '{eng_names[name]}',\n")
sd = sd[:epos + len(eng_marker)] + ''.join(eng_entries) + sd[epos + len(eng_marker):]

with open(SD_FILE, 'w', encoding='utf-8') as f:
    f.write(sd)

print(f'\nDone! Injected {len(data_blocks)} DATA blocks + SCHOOL_MAP + ENG_NAMES')
