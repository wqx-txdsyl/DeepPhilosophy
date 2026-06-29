"""Remove _json entries, add inline DATA entries to SCHOOL_MAP"""
import re

with open('src/pages/SchoolDetailPage.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_schools = ['韩国哲学','西藏哲学','北欧哲学','玛雅哲学','阿兹特克哲学',
               '澳洲原住民哲学','蒙古中亚哲学','东欧斯拉夫哲学','北美哲学','美索不达米亚哲学']

# Step 1: Remove lines with _json for new schools
out = []
for line in lines:
    skip = False
    for name in new_schools:
        pat = "'" + name + "':"
        if pat in line and '_json' in line:
            skip = True
            break
    if not skip:
        out.append(line)

# Step 2: Insert new entries before the closing };
# Find SCHOOL_MAP closing
new_entries = []
for name in new_schools:
    var_name = re.sub(r'[^\w]', '', name).upper() + '_DATA'
    entry = "  '" + name + "': { data:" + var_name + ", sub:{}, ci:[], bg:'url(/schools/" + name + ".jpg)' },\n"
    new_entries.append(entry)

# Find the }; that closes SCHOOL_MAP (right before 'const m = SCHOOL_MAP')
final = []
for i, line in enumerate(out):
    if line.strip() == '};' and i+1 < len(out) and 'const m = SCHOOL_MAP' in out[i+1]:
        final.extend(new_entries)
        final.append(line)
    else:
        final.append(line)

with open('src/pages/SchoolDetailPage.jsx', 'w', encoding='utf-8') as f:
    f.writelines(final)

# Verify
with open('src/pages/SchoolDetailPage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

for name in new_schools:
    var_name = re.sub(r'[^\w]', '', name).upper() + '_DATA'
    count = content.count("'" + name + "':")
    has_data = ("data:" + var_name) in content
    has_json = False
    idx = content.find("'" + name + "':")
    if idx >= 0:
        segment = content[idx:idx+200]
        has_json = '_json' in segment
    print(name + ': entries=' + str(count) + ' has_DATA=' + str(has_data) + ' has_json=' + str(has_json))

print('Done')
