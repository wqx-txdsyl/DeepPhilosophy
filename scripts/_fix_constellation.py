"""Fix constellation: remove placeholder thinkers and fix relation name mismatches for Eastern/World schools."""
import re

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# List of all Eastern + World prefixes that might have issues
EASTERN_WORLD = [
    'CONFUCIANISM','TAOISM','MOHISM','LEGALISM','SCHOOL_OF_NAMES',
    'YINYANG_SCHOOL','MILITARY_SCHOOL','HAN_CONFUCIANISM',
    'WEIJIN_METAPHYSICS','SUITANG_BUDDHISM','SONGMING_NEO_CONFUCIANISM',
    'MINGQING_PRACTICAL','QIANJIA_EVIDENTIAL','EVOLUTION_CHINA',
    'REFORMIST','THREE_PRINCIPLES','MAO_ZEDONG_THOUGHT',
    'CHINESE_MARXIST_PHILOSOPHY','NEW_CONFUCIANISM','CHINESE_POSITIVISM',
    'MARXISM_SINICIZATION','XI_JINPING_THOUGHT',
    'INDIAN_PHILOSOPHY','JAPANESE_PHILOSOPHY','ISLAMIC_PHILOSOPHY',
    'AFRICAN_PHILOSOPHY','JEWISH_PHILOSOPHY','PERSIAN_PHILOSOPHY',
    'LATIN_AMERICAN_PHILOSOPHY','SOUTHEAST_ASIAN_PHILOSOPHY',
]

def get_block(c, var):
    m = re.search(rf'const {var}_DATA\s*=\s*\{{', c)
    if not m: return None, None, None
    start = m.start()
    d = 0; end = start
    for i in range(start, len(c)):
        if c[i] == '{': d += 1
        elif c[i] == '}':
            d -= 1
            if d == 0: end = i + 2; break
    return start, end, c[start:end]

def fix_thinkers(thinkers_str):
    """Remove placeholder thinkers and clean up names."""
    # Match individual thinker entries
    entries = re.findall(r'\{(.*?)\}', thinkers_str, re.DOTALL)
    cleaned = []
    for entry in entries:
        # Extract name
        name_m = re.search(r'name:\s*[`"]([^`"]+)[`"]', entry)
        if name_m:
            name = name_m.group(1)
            # Skip placeholder thinkers (name contains "代表人物" or matches common patterns)
            if '代表人物' in name:
                continue
            # Skip entries with empty or generic names
            if len(name) < 2:
                continue
        cleaned.append('{' + entry + '}')
    return '[' + ','.join(cleaned) + ']'

fixes = 0
for var in EASTERN_WORLD:
    start, end, block = get_block(content, var)
    if not block:
        continue

    # Find thinkers section
    t_match = re.search(r'thinkers:\s*(\[.*?\])\s*,', block, re.DOTALL)
    if not t_match:
        continue

    thinkers_str = t_match.group(1)
    # Check for placeholder thinkers
    if '代表人物' in thinkers_str:
        new_thinkers = fix_thinkers(thinkers_str)
        old = t_match.group(0)
        new = old.replace(thinkers_str, new_thinkers)
        content = content[:start] + block.replace(old, new) + content[end:]
        fixes += 1
        print(f'Fixed thinkers: {var}')

    # Check for name mismatches between relations and thinkers
    # Re-extract after potential fix
    _, _, block = get_block(content, var)
    thinkers = re.findall(r'name:\s*[`"]([^`"]+)[`"]', block)
    rel_names = set(re.findall(r'(?:from|to):\s*[`"]([^`"]+)[`"]', block))

    mismatches = [r for r in rel_names if r not in thinkers]
    if mismatches:
        # Remove relations that reference non-existent thinkers
        rel_match = re.search(r'relations:\s*(\[.*?\])\s*,', block, re.DOTALL)
        if rel_match:
            rels_str = rel_match.group(1)
            entries = re.findall(r'\{(.*?)\}', rels_str, re.DOTALL)
            valid = []
            for entry in entries:
                from_m = re.search(r'from:\s*[`"]([^`"]+)[`"]', entry)
                to_m = re.search(r'to:\s*[`"]([^`"]+)[`"]', entry)
                if from_m and to_m:
                    if from_m.group(1) in thinkers and to_m.group(1) in thinkers:
                        valid.append('{' + entry + '}')
            if valid:
                new_rels = 'relations:[' + ','.join(valid) + ']'
                old_rels = rel_match.group(0)
                content = content[:start] + block.replace(old_rels, new_rels) + content[end:]
                fixes += 1
                print(f'Fixed relations: {var} — removed {len(entries) - len(valid)} invalid links')

print(f'\nTotal fixes: {fixes}')
with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Written: {len(content)} bytes')
