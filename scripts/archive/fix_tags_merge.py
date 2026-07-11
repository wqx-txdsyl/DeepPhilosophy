"""fix_tags_merge.py — 分裂连接标签 + 合并相近标签 + 重建对应"""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from philosophers_db import PHILOSOPHERS

# === 1. Tag merge map (相近标签 → 统一标签) ===
MERGE_MAP = {
    # 古希腊系
    '前苏格拉底':'古希腊哲学','米利都学派':'古希腊哲学','埃利亚学派':'古希腊哲学',
    '多元论':'古希腊哲学','柏拉图学派':'古希腊哲学','逍遥学派':'古希腊哲学',
    '犬儒学派':'古希腊哲学','伊壁鸠鲁学派':'古希腊哲学','伊壁鸠鲁派':'古希腊哲学',
    '新柏拉图主义':'古希腊哲学','古代哲学':'古希腊哲学','自然哲学':'古希腊哲学',
    '折衷主义':'古希腊哲学','元素论':'古希腊哲学','柏拉图主义':'古希腊哲学',
    '古代怀疑论':'古希腊哲学','古典-希腊化时期':'古希腊哲学','前苏格拉底哲学':'古希腊哲学',
    '希伯来':'希伯来（犹太）',
    # 斯多葛系
    '斯多葛派':'斯多葛学派','斯多葛主义':'斯多葛学派','晚期斯多亚':'斯多葛学派',
    '斯多葛':'斯多葛学派','斯多葛学派（罗马）':'斯多葛学派',
    # 教父/经院
    '希腊教父':'教父哲学','拉丁教父':'教父哲学','希伯来（犹太）教父':'教父哲学',
    '希波教父':'教父哲学','亚历山大里亚教父':'教父哲学','卡帕多西亚教父':'教父哲学',
    '尼撒的格列高利派':'教父哲学',
    '盛期经院哲学':'经院哲学','早期经院哲学':'经院哲学','阿拉伯-亚里士多德派':'经院哲学',
    '后期经院哲学':'经院哲学','古典经院哲学':'经院哲学','经院哲学唯名论':'经院哲学',
    '经院哲学（唯名论与实在论）':'经院哲学','奥古斯丁-方济各派':'经院哲学',
    # 理性/经验
    '欧陆哲学':'理性主义','启蒙思想':'启蒙运动','启蒙哲学':'启蒙运动',
    '苏格兰启蒙':'启蒙运动','人文主义':'启蒙运动','文艺复兴人文主义':'启蒙运动',
    '机械唯物主义':'实在论','常识实在论':'实在论','人本唯物论':'实在论',
    # 德国系
    '批判哲学':'德国古典哲学','德国唯心论':'德国古典哲学','唯意志论':'德国古典哲学',
    '悲观主义哲学':'德国古典哲学','德国观念论':'德国古典哲学','德国观念论-沃尔夫体系':'德国古典哲学',
    '德国唯心主义':'德国古典哲学','绝对唯心主义':'唯心主义',
    # 存在/现象
    '存在主义先驱':'存在主义','存在哲学':'存在主义','文学哲学':'存在主义',
    '身体哲学':'现象学','解释学':'现象学','意向性':'现象学',
    # 分析
    '逻辑原子主义':'分析哲学','逻辑实用主义':'分析哲学','逻辑实证':'分析哲学',
    '逻辑实证主义':'分析哲学','日常语言':'分析哲学','语言哲学':'分析哲学',
    '逻辑原子论':'分析哲学',
    # 马克思主义
    '结构马克思主义':'马克思主义','历史唯物主义':'马克思主义',
    '文化霸权理论':'西方马克思主义','西方马克思主义（文化霸权）':'西方马克思主义',
    '政治经济学':'政治哲学','古典经济学':'政治哲学',
    # 法兰克福
    '交往理论':'法兰克福学派','文化批评':'法兰克福学派',
    '法兰克福学派（批判理论）':'法兰克福学派','文化工业':'法兰克福学派',
    '批判理论（法兰克福学派）':'法兰克福学派',
    # 社会学/心理学
    '形式社会学':'社会学','社会心理学':'社会学','群体心理学':'社会学',
    '社会达尔文':'社会学','宗教社会学':'社会学','理解社会学':'社会学',
    '精神分析':'精神分析学','分析心理学':'精神分析学','心理治疗':'精神分析学',
    # 政治
    '激进平等':'政治哲学','责任伦理':'政治哲学','社会契约论':'政治哲学',
    '现实主义政治哲学':'政治哲学',
    # 后现代
    '解构主义':'后现代主义','后现代哲学':'后现代主义','后结构':'后结构主义',
    '解构':'后结构主义','后女性主义':'女性主义',
    # 实用/实证
    '进步教育':'实用主义','新实用主义':'实用主义',
    '实证':'实证主义','逻辑实证':'实证主义',
    '批判理性主义':'科学哲学','逻辑经验主义':'科学哲学',
    # 结构主义
    '结构语言学':'结构主义','结构主义诗学':'结构主义','结构主义语言学':'结构主义',
    '结构主义符号学':'结构主义','结构马克思主义':'马克思主义',
    # 伦理学
    '德性伦理':'伦理学',
    # 宗教
    '宗教存在主义':'宗教哲学','宗教荒诞':'宗教哲学','宗教改革运动':'宗教哲学',
    '耶路撒冷学派':'宗教哲学',
    # 中国
    '天演论':'中国近代哲学','维新派':'中国近代哲学',
    '旧民主主义':'中国近代政治哲学','新民主主义':'中国近代政治哲学',
    '三民主义':'中国近代政治哲学','毛泽东思想创新':'中国马克思主义',
    '中国马克思主义哲学':'中国马克思主义',
    '马克思主义哲学的中国化与体系化':'中国马克思主义',
    '马克思主义哲学史':'中国马克思主义',
    '马克思主义理论家':'中国马克思主义',
    '马克思主义理论创新':'中国马克思主义',
    '统一战线':'中国马克思主义','继承与发展':'中国马克思主义',
    '习近平新时代中国特色社会主义思想':'中国马克思主义',
    '毛泽东思想':'中国马克思主义',
    '两汉经学':'儒家','魏晋玄学':'道家','隋唐佛学':'佛学',
    '宋明理学':'儒家','明清实学':'儒家','乾嘉朴学':'儒家',
    '综合经学':'儒家','古文经学':'儒家','史学考证':'儒家',
    '现代新儒家':'儒家','理学':'儒家','心学':'儒家','气学':'儒家',
    '前墨家':'墨家','墨家创始人':'墨家',
    '法家创始人':'法家','道家创始人':'道家','儒家创始人':'儒家',
    '兵家创始人':'兵家','名家创始人':'名家',
    '阴阳家创始人':'阴阳家',
    # 荒诞
    '荒诞文学':'荒诞哲学',
    # 浪漫
    '浪漫主义先驱':'浪漫主义','浪漫主义（文学哲学）':'浪漫主义',
    # 其他合并
    '近代哲学之父':'近代哲学','有机体哲学':'过程哲学',
    '元理论':'科学哲学','元伦理学':'伦理学',
    '偏好功利主义':'功利主义',
    '诗性哲学观':'浪漫主义',
    '观念论':'唯心主义',
    '道德哲学':'伦理学',
    '逻辑学':'分析哲学',
    '语言哲学（言语行为理论）':'分析哲学',
    '实用主义（概念实用主义）':'实用主义',
    '文学现代主义':'荒诞哲学',
    '戏剧荒诞':'荒诞哲学',
    '荒诞派戏剧':'荒诞哲学',
    '生活美学':'美学',
    '意识哲学':'心灵哲学',
    '心灵哲学（意向性）':'心灵哲学',
    '现象学（身体现象学）':'现象学',
    '伦理学（女性主义关怀伦理）':'伦理学',
    '社会学（形式社会学）':'社会学',
    '社会理论':'社会学',
    '政治哲学（自由主义）':'政治哲学',
    '政治哲学（现实主义）':'政治哲学',
    '政治哲学（共和主义）':'政治哲学',
    '政治哲学（社会契约）':'政治哲学',
    '政治哲学（激进民主）':'政治哲学',
    '政治哲学（正义论）':'政治哲学',
    '文化哲学（文化符号学）':'文化哲学',
    # Single-char fragments
    '儒':'儒家','道':'道家','墨':'墨家','法':'法家','兵':'兵家',
    '名':'名家','农':'农家','杂':'杂家','小说':'小说家',
    '阴阳':'阴阳家','纵横':'纵横家',
    # More variants
    '儒家创始人':'儒家','道家创始人':'道家','墨家创始人':'墨家',
    '法家创始人':'法家','兵家创始人':'兵家','名家创始人':'名家',
    '阴阳家创始人':'阴阳家',
    '法兰克福学派（批判理论）':'法兰克福学派',
    '后结构':'后结构主义','解构':'后结构主义',
    '逻辑经验主义':'分析哲学',
    '德国观念论-沃尔夫体系':'德国古典哲学',
    '德国观念论':'德国古典哲学',
    '古典-希腊化时期':'古希腊哲学',
    '奥古斯丁-方济各派':'经院哲学',
    '阿拉伯-亚里士多德派':'经院哲学',
    '经院哲学（唯名论与实在论）':'经院哲学',
    '西方马克思主义（文化霸权）':'西方马克思主义',
    '批判理论（法兰克福学派）':'法兰克福学派',
    '语言哲学（言语行为理论）':'分析哲学',
    '实用主义（概念实用主义）':'实用主义',
    '现象学（身体现象学）':'现象学',
    '伦理学（女性主义关怀伦理）':'伦理学',
    '社会学（形式社会学）':'社会学',
    '政治哲学（自由主义）':'政治哲学',
    '政治哲学（现实主义）':'政治哲学',
    '政治哲学（共和主义）':'政治哲学',
    '政治哲学（社会契约）':'政治哲学',
    '技术哲学（媒介）':'技术哲学',
    '苏联马克思主义':'马克思主义',
    '毛泽东思想':'中国马克思主义',
    '中国特色社会主义':'中国马克思主义',
    '文化批判（文化研究）':'文化哲学',
    '文化政治批评':'文化哲学',
    '媒介理论':'技术哲学',
    '技术批判理论':'技术哲学',
    '技术哲学（媒介）':'技术哲学',
}

# === 2. Split concatenated tags (no delimiter) ===
SPLIT_PATTERNS = [
    (r'(.+主义)(.+主义)', r'\1/\2'),
    (r'(.+学派)(.+学派)', r'\1/\2'),
    (r'(.+哲学)(.+哲学)', r'\1/\2'),
    (r'(.+创始人)(.+)', r'\1/\2'),
    (r'(.+)(创始人.+)', r'\1/\2'),
    (r'(.+理论)(.+)', r'\1/\2'),
    (r'(.+运动)(.+)', r'\1/\2'),
]

def fix_school_tag(school_str):
    if not school_str:
        return ''
    # First, try to split concatenations
    for pattern, replacement in SPLIT_PATTERNS:
        if '/' not in school_str and '、' not in school_str:
            school_str = re.sub(pattern, replacement, school_str)
    # Split, merge, rejoin
    tags = [t.strip() for t in re.split(r'[/,、，;；]', school_str) if t.strip()]
    merged = []
    seen = set()
    for tag in tags:
        canonical = MERGE_MAP.get(tag, tag)
        if canonical not in seen:
            merged.append(canonical)
            seen.add(canonical)
    return ' / '.join(merged)

# === 3. Apply to all philosophers ===
changes = 0
for name, info in PHILOSOPHERS.items():
    old_school = info.get('school', '')
    new_school = fix_school_tag(old_school)
    if old_school != new_school:
        PHILOSOPHERS[name]['school'] = new_school
        changes += 1

print(f'Fixed {changes} philosopher school tags')

# === 4. Fix country fields (split concatenations) ===
COUNTRY_MERGE = {
    '苏格兰':'英国','英格兰':'英国','罗马帝国':'古罗马','北非':'古罗马',
    '奥匈帝国（捷克）':'捷克','俄国':'俄罗斯','普鲁士':'德国',
    '奥匈帝国':'奥地利','奥斯曼':'土耳其','波斯':'伊朗',
    '佛兰德斯':'比利时','波希米亚':'捷克','摩拉维亚':'捷克',
}

country_changes = 0
for name, info in PHILOSOPHERS.items():
    old = info.get('country', '')
    if not old: continue
    tags = [t.strip() for t in re.split(r'[/,、，;；]', old) if t.strip()]
    merged = []
    seen = set()
    for tag in tags:
        canonical = COUNTRY_MERGE.get(tag, tag)
        if canonical not in seen:
            merged.append(canonical)
            seen.add(canonical)
    new = ' / '.join(merged)
    if old != new:
        PHILOSOPHERS[name]['country'] = new
        country_changes += 1

print(f'Fixed {country_changes} country fields')

# === 5. Write updated philosophers_db.py ===
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophers_db.py')
with open(db_path, 'r', encoding='utf-8') as f:
    content = f.read()

for name, info in PHILOSOPHERS.items():
    # Update school field
    old_school = info.get('_orig_school', info.get('school', ''))
    new_school = info.get('school', '')
    if old_school != new_school:
        # Find and replace in file
        # Pattern: "school": "old_value"
        old_val = info.get('_orig_school', '')
        if not old_val:
            # Find current value in file
            pattern = rf'"{re.escape(name)}":\s*\{{[^}}]*"school":\s*"([^"]*)"'
            m = re.search(pattern, content)
            if m:
                old_val = m.group(1)
        if old_val and old_val != new_school:
            content = content.replace(f'"school": "{old_val}"', f'"school": "{new_school}"')

    # Update country field
    old_country = info.get('_orig_country', '')
    new_country = info.get('country', '')

# Simpler approach: write the whole PHILOSOPHERS dict as a JSON, then format back
# Actually, let me just build the updated lines directly

import ast
with open(db_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

updated_lines = list(lines)
for name, info in PHILOSOPHERS.items():
    for i, line in enumerate(updated_lines):
        if line.strip().startswith(f'"{name}":'):
            for j in range(i, min(i+15, len(updated_lines))):
                for field in ['school', 'country']:
                    field_key = f'"{field}":'
                    if field_key in updated_lines[j]:
                        indent = len(updated_lines[j]) - len(updated_lines[j].lstrip())
                        new_val = info[field].replace('\\', '\\\\').replace('"', '\\"')
                        updated_lines[j] = ' ' * indent + f'"{field}": "{new_val}",\n'
            break

with open(db_path, 'w', encoding='utf-8') as f:
    f.writelines(updated_lines)

# Verify syntax
ast.parse(''.join(updated_lines))
print('Syntax OK - done!')

# Stats
all_tags_final = set()
for info in PHILOSOPHERS.values():
    for tag in info.get('school','').split(' / '):
        if tag.strip(): all_tags_final.add(tag.strip())
print(f'Final unique school tags: {len(all_tags_final)}')
print(f'Total philosophers: {len(PHILOSOPHERS)}')
for tag in sorted(all_tags_final):
    count = sum(1 for info in PHILOSOPHERS.values() if tag in info.get('school',''))
    print(f'  [{count}] {tag}')
