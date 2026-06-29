"""Rebuild timeline with 3-column layout: timeline | 东方 | 西方 | 世界"""
import re, json

def parse_timeline(content, var_name):
    pattern = var_name + r'\s*=\s*\[(.*?)\];'
    m = re.search(pattern, content, re.DOTALL)
    if not m: return []
    schools = []
    for entry in re.finditer(r"{ century: '([^']+)', schools: \[(.*?)\] }", m.group(1)):
        century = entry.group(1)
        for s in re.findall(r"'([^']+)'", entry.group(2)):
            schools.append((century, s))
    return schools

# Read HomePage
with open('src/pages/HomePage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

western = parse_timeline(content, 'WESTERN_TIMELINE')
eastern = parse_timeline(content, 'EASTERN_TIMELINE')
world = parse_timeline(content, 'WORLD_TIMELINE')

# Read descriptions
def parse_descriptions(content, var_name):
    pattern = var_name + r'\s*=\s*\{([^}]+)\}'
    m = re.search(pattern, content, re.DOTALL)
    if not m: return {}
    descs = {}
    for entry in re.finditer(r"'([^']+)'\s*:\s*'([^']*)'", m.group(1)):
        descs[entry.group(1)] = entry.group(2)
    return descs

western_desc = parse_descriptions(content, 'SCHOOL_DESCRIPTIONS')
eastern_desc = parse_descriptions(content, 'EASTERN_DESCRIPTIONS')
world_desc = parse_descriptions(content, 'WORLD_DESCRIPTIONS')

# Assign numeric sort key
def century_key(century_str):
    bce = '公元前' in century_str
    nums = re.findall(r'\d+', century_str)
    if not nums: return (0, 0)
    n = int(nums[0])
    if bce:
        return (-1, -n)
    else:
        return (1, n)

# Build all schools with sort key
all_schools = []
for century, name in western:
    all_schools.append({'name': name, 'century': century, 'region': '西方', 'key': century_key(century)})
for century, name in eastern:
    all_schools.append({'name': name, 'century': century, 'region': '东方', 'key': century_key(century)})
for century, name in world:
    all_schools.append({'name': name, 'century': century, 'region': '世界', 'key': century_key(century)})

# Sort
all_schools.sort(key=lambda x: x['key'])

# Group by century for timeline
centuries = []
current_century = None
for s in all_schools:
    if s['century'] != current_century:
        current_century = s['century']
        centuries.append({'century': current_century, 'schools': []})
    centuries[-1]['schools'].append(s)

# Also sort Western/Eastern/World overview pages
def extract_school_list(content, var_name):
    pattern = var_name + r'\s*=\s*\[(.*?)\];'
    m = re.search(pattern, content, re.DOTALL)
    if not m: return []
    schools = []
    for entry in re.finditer(r"{ name: '([^']+)'[^}]*}", m.group(1)):
        schools.append(entry.group(1))
    return schools

print(f'Total schools: {len(all_schools)}')
print(f'Century groups: {len(centuries)}')
print(f'Western: {len(western)}, Eastern: {len(eastern)}, World: {len(world)}')

# Output sorted lists for overview pages
for region in ['西方', '东方', '世界']:
    region_schools = [s for s in all_schools if s['region'] == region]
    print(f'\n{region} (sorted):')
    for s in region_schools[:10]:
        print(f'  {s["century"]}: {s["name"]}')
    if len(region_schools) > 10:
        print(f'  ... +{len(region_schools)-10}')
