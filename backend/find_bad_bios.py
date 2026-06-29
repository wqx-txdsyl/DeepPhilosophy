"""识别质量差的bio（markdown格式/过短/零散）"""
import json, re

with open('data/philosophers.json', encoding='utf-8') as f:
    data = json.load(f)

bad = []
good = []
for n, v in data.items():
    bio = v.get('bio','')
    issues = []
    if len(bio) < 1000:
        issues.append(f'short({len(bio)})')
    if re.search(r'^#{1,4}\s', bio, re.MULTILINE):
        issues.append('headers')
    if re.search(r'\*\*', bio):
        issues.append('bold')
    if re.search(r'^\s*[-*•]\s', bio, re.MULTILINE):
        issues.append('bullets')
    if re.search(r'^\d+[\.\)]\s', bio, re.MULTILINE):
        issues.append('numbered')
    if issues:
        bad.append((n, issues))
    else:
        good.append(n)

print(f'Good (clean prose): {len(good)}')
print(f'Bad: {len(bad)}')
for n, issues in bad[:10]:
    print(f'  {n}: {issues}')
if len(bad) > 10:
    print(f'  ... +{len(bad)-10} more')

# Save bad list for regeneration
with open('data/bad_bios.json', 'w', encoding='utf-8') as f:
    json.dump([n for n,_ in bad], f, ensure_ascii=False)
print(f'Saved {len(bad)} names to bad_bios.json')
