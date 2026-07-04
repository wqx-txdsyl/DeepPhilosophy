"""
修复哲学家标签：合并相似流派，拆分错误组合，清理国家标签括号，修复时代标签
"""
import json, re, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHILO_PATH = os.path.join(ROOT, "backend", "data", "philosophers.json")
ALIASES_PATH = os.path.join(ROOT, "backend", "data", "name_aliases.json")
OUTPUT = os.path.join(os.path.dirname(__file__), "_tag_fix_report.txt")

with open(PHILO_PATH, "r", encoding="utf-8") as f:
    philo = json.load(f)

report = []
fixes = 0

# ============================================================
# 1. Split combined school tags like "存在主义女性主义"
# ============================================================
split_rules = {
    "存在主义女性主义": ["存在主义", "女性主义"],
    "现象学存在主义": ["现象学", "存在主义"],
    "马克思主义女性主义": ["马克思主义", "女性主义"],
    "分析哲学女性主义": ["分析哲学", "女性主义"],
    "后结构主义女性主义": ["后结构主义", "女性主义"],
    "实用主义女性主义": ["实用主义", "女性主义"],
    "精神分析学女性主义": ["精神分析学", "女性主义"],
    "批判理论女性主义": ["批判理论", "女性主义"],
    "后现代主义女性主义": ["后现代主义", "女性主义"],
    "自由主义女性主义": ["自由主义", "女性主义"],
    "现象学诠释学": ["现象学", "哲学诠释学"],
    "分析哲学马克思主义": ["分析哲学", "马克思主义"],
}

# ============================================================
# 2. Merge similar school tags (canonical_name: [aliases])
# ============================================================
merge_rules = {
    "古希腊哲学": ["希腊哲学", "古希腊"],
    "德国古典哲学": ["德国唯心主义", "德意志唯心论"],
    "分析哲学": ["语言分析哲学", "逻辑分析哲学"],
    "现象学": ["现象学派"],
    "存在主义": ["存在哲学", "存在主义哲学"],
    "马克思主义": ["马克思哲学", "马克思主义哲学"],
    "后结构主义": ["后结构"],
    "现代新儒家": ["新儒家", "当代新儒家"],
    "中国马克思主义哲学": ["中国马克思主义"],
    "实用主义": ["实用主义哲学"],
    "生命哲学": ["生命学派"],
    "实在论": ["实在论哲学"],
    "唯心主义": ["唯心论"],
    "经验主义": ["经验论"],
    "理性主义": ["理性论"],
}

# ============================================================
# 3. Country tag normalization
# ============================================================
def clean_country(country_str):
    """Remove parenthetical notes like (后移居y国) from country string"""
    # Remove parenthetical notes but keep the country names
    cleaned = re.sub(r'[（(][^)）]*?移居[^)）]*[)）]', '', country_str)
    cleaned = re.sub(r'[（(][^)）]*?移民[^)）]*[)）]', '', cleaned)
    cleaned = re.sub(r'[（(][^)）]*?迁居[^)）]*[)）]', '', cleaned)
    cleaned = re.sub(r'[（(][^)）]*?流亡[^)）]*[)）]', '', cleaned)
    cleaned = re.sub(r'[（(][^)）]*?入籍[^)）]*[)）]', '', cleaned)
    # Clean up extra spaces and separators
    cleaned = re.sub(r'\s*/\s*', '/', cleaned)
    cleaned = re.sub(r'\s*,\s*', '/', cleaned)
    cleaned = cleaned.strip(' /')
    return cleaned

# ============================================================
# Apply fixes
# ============================================================
for name, info in philo.items():
    school = info.get("school", "")
    country = info.get("country", "")
    era = info.get("era", "")
    changed = False

    # Split combined tags
    original_school = school
    for combined, parts in split_rules.items():
        if combined in school:
            school = school.replace(combined, "/".join(parts))
            changed = True

    # Merge similar tags
    for canonical, aliases in merge_rules.items():
        for alias in aliases:
            if alias in school and canonical not in school:
                school = school.replace(alias, canonical)
                changed = True

    # Clean country
    original_country = country
    country = clean_country(country)
    if country != original_country:
        changed = True

    if changed:
        fixes += 1
        info["school"] = school
        info["country"] = country
        report.append(f"{name}: school={original_school} -> {school}")
        if country != original_country:
            report.append(f"{name}: country={original_country} -> {country}")

# Save
with open(PHILO_PATH, "w", encoding="utf-8") as f:
    json.dump(philo, f, ensure_ascii=False, indent=2)

# Report
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(f"Tag fixes applied: {fixes}\n\n")
    f.write("\n".join(report))
    f.write("\n\n=== Tag Statistics ===\n")
    schools = Counter()
    countries = Counter()
    for info in philo.values():
        for t in re.split(r'[/,、，;；]', info.get("school", "")):
            t = t.strip()
            if t: schools[t] += 1
        for t in re.split(r'[/,、，;；]', clean_country(info.get("country", ""))):
            t = t.strip()
            if t: countries[t] += 1
    f.write(f"\nSchools ({len(schools)}):\n")
    for s, n in schools.most_common():
        f.write(f"  {s}: {n}\n")
    f.write(f"\nCountries ({len(countries)}):\n")
    for c, n in countries.most_common():
        f.write(f"  {c}: {n}\n")

print(f"Fixes applied: {fixes}")
print(f"Report: {OUTPUT}")
