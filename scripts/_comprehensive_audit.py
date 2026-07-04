"""
全量审计：信息完整性 + 标签清洗 + 非人条目 + 数量统一
"""
import json, re, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHILO = os.path.join(ROOT, "backend", "data", "philosophers.json")
ALIASES = os.path.join(ROOT, "backend", "data", "name_aliases.json")
IMG_DIR = os.path.join(ROOT, "app", "public", "philosopher")
OUT = os.path.join(os.path.dirname(__file__), "_comprehensive_report.txt")

with open(PHILO, "r", encoding="utf-8") as f: philo = json.load(f)
with open(ALIASES, "r", encoding="utf-8") as f: aliases = json.load(f)
existing_imgs = set(os.path.splitext(f)[0] for f in os.listdir(IMG_DIR) if f.endswith('.jpg'))

report = []
fixes = 0
all_issues = []

# ============================================================
# 1. INFO COMPLETENESS CHECK
# ============================================================
report.append("=== 1. INFO COMPLETENESS ===")
missing_era = []
missing_country = []
missing_school = []
missing_bio_short = []  # bio < 500 chars
missing_wiki = []
missing_img = []
non_person = []

for name, info in philo.items():
    if not info.get('era'): missing_era.append(name)
    if not info.get('country'): missing_country.append(name)
    if not info.get('school'): missing_school.append(name)
    if len(info.get('bio', '')) < 500: missing_bio_short.append(name)
    if not info.get('wiki_url'): missing_wiki.append(name)

    safe = name.replace('/','-').replace(':','：')
    if safe not in existing_imgs:
        missing_img.append(name)

    # Non-person check
    if len(name) <= 4 and any(name.endswith(kw) for kw in ['主义','学派','理论','哲学','佛教','儒教']):
        non_person.append(name)

report.append(f"Missing era: {len(missing_era)}")
report.append(f"Missing country: {len(missing_country)}")
report.append(f"Missing school: {len(missing_school)}")
report.append(f"Short bio (<500): {len(missing_bio_short)}")
report.append(f"Missing wiki_url: {len(missing_wiki)}")
report.append(f"Missing image: {len(missing_img)}")
report.append(f"Likely non-person: {len(non_person)}")
for n in non_person: report.append(f"  NON-PERSON: {n}")
for n in missing_img: report.append(f"  NO_IMG: {n}")

# ============================================================
# 2. TAG FIXES
# ============================================================
report.append("\n=== 2. TAG FIXES ===")

# Split combined school tags
SPLIT_MAP = {
    "存在主义女性主义": "存在主义/女性主义",
    "马克思主义女性主义": "马克思主义/女性主义",
    "精神分析学女性主义": "精神分析学/女性主义",
    "自由主义女性主义": "自由主义/女性主义",
    "后结构主义女性主义": "后结构主义/女性主义",
    "分析哲学女性主义": "分析哲学/女性主义",
    "实用主义女性主义": "实用主义/女性主义",
    "批判理论女性主义": "批判理论/女性主义",
    "后现代主义女性主义": "后现代主义/女性主义",
    "现象学存在主义": "现象学/存在主义",
    "现象学诠释学": "现象学/哲学诠释学",
    "分析哲学马克思主义": "分析哲学/马克思主义",
}

# Merge similar tags
MERGE_MAP = {
    "希腊哲学": "古希腊哲学",
    "德国唯心主义": "德国古典哲学",
    "语言分析哲学": "分析哲学",
    "存在哲学": "存在主义",
    "马克思哲学": "马克思主义",
    "后结构": "后结构主义",
    "新儒家": "现代新儒家",
    "当代新儒家": "现代新儒家",
    "实用主义哲学": "实用主义",
    "生命学派": "生命哲学",
    "实在论哲学": "实在论",
    "唯心论": "唯心主义",
    "经验论": "经验主义",
    "理性论": "理性主义",
    "现象学派": "现象学",
    "存在主义哲学": "存在主义",
    "中国马克思主义": "中国马克思主义哲学",
    "马克思主义哲学": "马克思主义",
    "语言哲学": "分析哲学",
    "法哲学": "法家",  # 中文语境
}

tag_fixes = 0
for name, info in philo.items():
    school = info.get("school", "")
    country = info.get("country", "")
    changed = False

    # Split combined
    for bad, good in SPLIT_MAP.items():
        if bad in school and good not in school:
            school = school.replace(bad, good)
            changed = True

    # Merge similar
    for alias, canonical in MERGE_MAP.items():
        if alias in school and canonical not in school:
            school = re.sub(rf'\b{re.escape(alias)}\b', canonical, school)
            changed = True

    # Clean country parentheses
    orig_country = country
    country = re.sub(r'[（(][^)）]*?移居[^)）]*[)）]', '', country)
    country = re.sub(r'[（(][^)）]*?移民[^)）]*[)）]', '', country)
    country = re.sub(r'[（(][^)）]*?迁居[^)）]*[)）]', '', country)
    country = country.strip(' /')
    if country != orig_country: changed = True

    if changed:
        tag_fixes += 1
        info["school"] = school
        info["country"] = country

report.append(f"Tag fixes applied: {tag_fixes}")

# Count unique values after fixes
schools = Counter()
countries = Counter()
for info in philo.values():
    for t in re.split(r'[/,，、]', info.get("school", "")):
        t = t.strip()
        if t: schools[t] += 1
    for t in re.split(r'[/,，、]', re.sub(r'[（(][^)）]*[)）]', '', info.get("country", ""))):
        t = t.strip()
        if t: countries[t] += 1

report.append(f"\nSchools ({len(schools)}):")
for s, n in schools.most_common(40):
    report.append(f"  {s}: {n}")
report.append(f"\nCountries ({len(countries)}):")
for c, n in countries.most_common(40):
    report.append(f"  {c}: {n}")

# ============================================================
# 3. COUNT CHECK (pages consistency)
# ============================================================
report.append(f"\n=== 3. COUNT CHECK ===")
report.append(f"philosophers.json: {len(philo)}")
report.append(f"name_aliases.json: {len(aliases)}")
report.append(f"Images on disk: {len(existing_imgs)}")

# Check AuthorsPage count
authors_page_path = os.path.join(ROOT, "app", "src", "pages", "AuthorsPage.jsx")
with open(authors_page_path, "r", encoding="utf-8") as f:
    ap_content = f.read()
# Find hardcoded count
count_match = re.search(r'(\d+)\s*位哲人', ap_content)
if count_match:
    report.append(f"AuthorsPage hardcoded count: {count_match.group(1)} (should be {len(philo)})")

# ============================================================
# SAVE
# ============================================================
with open(PHILO, "w", encoding="utf-8") as f:
    json.dump(philo, f, ensure_ascii=False, indent=2)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print(f"Report: {OUT}")
print(f"Philosophers: {len(philo)}")
print(f"Tag fixes: {tag_fixes}")
print(f"Missing era: {len(missing_era)}, country: {len(missing_country)}, school: {len(missing_school)}")
print(f"Short bio: {len(missing_bio_short)}, missing wiki: {len(missing_wiki)}")
print(f"Missing images: {len(missing_img)}")
print(f"Non-person: {len(non_person)}")
