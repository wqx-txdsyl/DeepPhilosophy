"""补全星丛哲学家 school/country/era 信息"""
import re, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import philosophers_db

# Read SchoolDetailPage to extract era/sub info for each thinker
jsx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'app', 'src', 'pages', 'SchoolDetailPage.jsx')
with open(jsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract thinker info: name, sub (school), era
thinker_info = {}
blocks = re.split(r'thinkers:\s*\[', content)
for block in blocks[1:]:
    depth, end = 0, 0
    for i, ch in enumerate(block):
        if ch == '[': depth += 1
        elif ch == ']':
            depth -= 1
            if depth < 0: end = i; break
    thinker_block = block[:end]

    # Parse each thinker object
    for obj_match in re.finditer(r'''\{([^}]+)\}''', thinker_block):
        obj_str = obj_match.group(1)
        name_m = re.search(r'''name:\s*['"]([^'"]+)['"]''', obj_str)
        sub_m = re.search(r'''sub:\s*['"]([^'"]+)['"]''', obj_str)
        era_m = re.search(r'''era:\s*['"]([^'"]+)['"]''', obj_str)
        if name_m:
            name = name_m.group(1).strip()
            sub = sub_m.group(1).strip() if sub_m else ''
            era = era_m.group(1).strip() if era_m else ''
            if name not in thinker_info:
                thinker_info[name] = {'sub': sub, 'era': era}

print(f'从星丛提取到 {len(thinker_info)} 个思想者的 sub/era 信息')

# Now update philosophers_db entries that have empty school/era
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophers_db.py')
with open(db_path, 'r', encoding='utf-8') as f:
    db_lines = f.readlines()

# Find entries with empty fields and update them
updated = 0
alias_map = philosophers_db.NAME_ALIASES

for i, line in enumerate(db_lines):
    # Find philosopher name keys
    m = re.match(r'^\s*"([^"]+)":\s*\{', line)
    if not m:
        continue
    name = m.group(1)
    # Find the thinker info (check aliases too)
    ti = thinker_info.get(name)
    if not ti:
        # Try reversed aliases
        for alias, target in alias_map.items():
            if target == name and alias in thinker_info:
                ti = thinker_info[alias]
                break

    if not ti or not (ti['sub'] or ti['era']):
        continue

    # Find the school and era lines for this entry
    entry_end = None
    for j in range(i, min(i+20, len(db_lines))):
        if db_lines[j].strip().startswith('},'):
            entry_end = j
            break
    if not entry_end:
        continue

    # Update era and school within this entry block
    for j in range(i, entry_end):
        if ti['sub'] and '"school": ""' in db_lines[j]:
            db_lines[j] = db_lines[j].replace('"school": ""', f'"school": "{ti["sub"]}"')
            updated += 1
        if ti['era'] and '"era": ""' in db_lines[j]:
            db_lines[j] = db_lines[j].replace('"era": ""', f'"era": "{ti["era"]}"')
            updated += 1

print(f'更新了 {updated} 个字段')

# Also guess country from school name
school_country_map = {
    '古希腊哲学':'古希腊','米利都学派':'古希腊','埃利亚学派':'古希腊','前苏格拉底':'古希腊',
    '柏拉图学派':'古希腊','逍遥学派':'古希腊','犬儒学派':'古希腊','怀疑论':'古希腊',
    '斯多葛学派':'古希腊','伊壁鸠鲁学派':'古希腊','新柏拉图主义':'古希腊','多元论':'古希腊',
    '儒家':'中国','道家':'中国','墨家':'中国','法家':'中国','名家':'中国',
    '兵家':'中国','阴阳家':'中国','两汉经学':'中国','魏晋玄学':'中国',
    '隋唐佛学':'中国','宋明理学':'中国','明清实学':'中国','乾嘉朴学':'中国',
    '德国古典哲学':'德国','法兰克福学派':'德国','现象学':'德国','存在主义':'德国',
    '分析哲学':'英国','经验主义':'英国','功利主义':'英国',
    '启蒙运动':'法国','理性主义':'法国','结构主义':'法国','后结构主义':'法国',
    '后现代主义':'法国','荒诞哲学':'法国',
    '实用主义':'美国','超验主义':'美国','过程哲学':'美国',
    '马克思主义':'德国','西方马克思主义':'德国',
    '社会学':'法国','精神分析学':'奥地利',
    '自由主义':'英国','科学哲学':'奥地利',
    '哲学诠释学':'德国','技术哲学':'德国',
    '教父哲学':'古罗马','经院哲学':'意大利','唯名论':'法国',
    '浪漫主义':'德国','生命哲学':'法国','实证主义':'法国',
    '哲学人类学':'德国','基督教哲学':'法国',
    '斯多葛派':'古希腊','伊壁鸠鲁派':'古希腊',
    '实在论':'英国','唯心主义':'德国',
    '历史唯物主义':'德国','伦理学':'英国',
    '女性主义':'美国','社群主义':'美国',
    '批判理论':'德国','政治哲学':'英国','宗教哲学':'德国',
    '希伯来':'以色列','希伯来（犹太）':'以色列',
    '阿拉伯哲学':'阿拉伯','伊斯兰哲学':'阿拉伯',
    '日本哲学':'日本','印度哲学':'印度',
    '非洲哲学':'非洲','波斯哲学':'波斯',
    '拉美哲学':'拉丁美洲','东南亚哲学':'东南亚',
    # Chinese sub-schools
    '天演论':'中国','维新派':'中国','三民主义':'中国',
    '旧民主主义':'中国','毛泽东思想':'中国','中国马克思主义哲学':'中国',
    '新民主主义':'中国','现代新儒家':'中国','中国实证哲学':'中国',
    '马克思主义哲学的中国化与体系化':'中国','习近平新时代中国特色社会主义思想':'中国',
    '理学':'中国','心学':'中国','气学':'中国',
}

for i, line in enumerate(db_lines):
    m = re.match(r'^\s*"([^"]+)":\s*\{', line)
    if not m: continue
    name = m.group(1)
    # Find entry block
    entry_end = None
    for j in range(i, min(i+20, len(db_lines))):
        if db_lines[j].strip().startswith('},'):
            entry_end = j
            break
    if not entry_end: continue

    # Check if country is empty
    country_empty = False
    school_val = ''
    for j in range(i, entry_end):
        if '"country": ""' in db_lines[j]:
            country_empty = True
        sm = re.search(r'"school":\s*"([^"]*)"', db_lines[j])
        if sm: school_val = sm.group(1)

    if country_empty and school_val:
        # Try to assign country
        # Check multi-valued school
        for school_part in re.split(r'[/,、，;；]', school_val):
            school_part = school_part.strip()
            if school_part in school_country_map:
                for j in range(i, entry_end):
                    if '"country": ""' in db_lines[j]:
                        db_lines[j] = db_lines[j].replace('"country": ""', f'"country": "{school_country_map[school_part]}"')
                        updated += 1
                        break
                break

print(f'含country赋值共更新 {updated} 个字段')

# Write updated
with open(db_path, 'w', encoding='utf-8') as f:
    f.writelines(db_lines)

# Verify syntax
import ast
ast.parse(''.join(db_lines))
print('Syntax OK - done!')
