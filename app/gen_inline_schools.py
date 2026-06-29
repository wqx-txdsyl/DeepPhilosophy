"""Convert school JSON to inline JS DATA objects"""
import json, os, re

schools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public', 'schools')
json_files = sorted([f for f in os.listdir(schools_dir) if f.startswith('school_') and f.endswith('.json')])

js_entries = []
school_map_entries = []

for fname in json_files:
    with open(os.path.join(schools_dir, fname), 'r', encoding='utf-8') as f:
        data = json.load(f)

    name = data.get('name', fname.replace('school_','').replace('.json',''))
    # Remove non-alphanumeric chars for variable name
    clean = re.sub(r'[^\w]', '', name)
    var_name = clean.upper() + '_DATA'

    def esc(s):
        if not s: return '""'
        s = str(s)
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '')
        return '"' + s + '"'

    def arr_str(items, fields_fn):
        lines = []
        for item in items:
            parts = []
            for f, default in fields_fn:
                val = item.get(f, default)
                parts.append(f'{f}: {esc(val)}')
            lines.append('    {' + ', '.join(parts) + '},')
        return '[\n' + '\n'.join(lines) + '\n  ]'

    # Build DATA object
    lines = [f'const {var_name} = {{']
    lines.append(f'  name: {esc(name)},')
    lines.append(f'  subtitle: {esc(data.get("subtitle",""))},')
    lines.append(f'  overview: {esc(data.get("overview",""))},')
    lines.append(f'  quote: {esc(data.get("quote",""))},')
    lines.append(f'  quoteAuthor: {esc(data.get("quoteAuthor",""))},')

    # timeline
    tl = data.get('timeline', [])
    lines.append('  timeline: ' + arr_str(tl, [('year',''),('event',''),('detail',''),('type','event')]) + ',')

    # thinkers
    thinkers = data.get('thinkers', [])
    lines.append('  thinkers: ' + arr_str(thinkers, [('name',''),('sub',''),('era',''),('influence',5),('key',''),('works','[]')]) + ',')

    # relations
    rels = data.get('relations', [])
    lines.append('  relations: ' + arr_str(rels, [('from',''),('to',''),('label','')]) + ',')

    # cihai
    ch = data.get('cihai', [])
    lines.append('  cihai: ' + arr_str(ch, [('word',''),('def',''),('source','')]) + ',')

    # quotes
    qs = data.get('quotes', [])
    lines.append('  quotes: ' + arr_str(qs, [('text',''),('author',''),('exp','')]) + ',')

    # works
    ws = data.get('works', [])
    lines.append('  works: ' + arr_str(ws, [('title',''),('author',''),('era',''),('desc','')]) + ',')

    # conclusion + closingQuote
    closing = data.get('closingQuote', data.get('quote', ''))
    lines.append(f'  conclusion: {esc(data.get("conclusion",""))},')
    lines.append(f'  closingQuote: {esc(closing)},')
    lines.append('};')
    lines.append('')

    js_entries.append('\n'.join(lines))

    # SCHOOL_MAP entry
    bg = f"url(/schools/{name}.jpg)"
    school_map_entries.append(f"  '{name}': {{ data:{var_name}, sub:{{}}, ci:[], bg:'{bg}' }},")

# Write output
output = '// === NEW WORLD SCHOOLS (auto-generated from JSON) ===\n\n'
output += '\n'.join(js_entries)
output += '\n// SCHOOL_MAP entries to replace _json versions:\n'
output += '\n'.join(school_map_entries)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'pages', '_new_schools_data.jsx')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)
print(f'Generated {len(json_files)} DATA objects ({len(output)} bytes)')
print(f'Saved to: {out_path}')
