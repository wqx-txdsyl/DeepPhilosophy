"""列出缺图哲学家"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    p = json.load(f)

def safe_fn(name):
    return name.replace('/', '-').replace('\\', '-').replace(':', '-')

missing = [n for n in p if not any(
    os.path.exists(os.path.join(IMG_DIR, safe_fn(n) + e)) for e in ['.jpg', '.png', '.webp']
)]

top = [(n, p[n].get('rank', 0)) for n in missing if isinstance(p.get(n), dict) and p[n].get('rank', 0) >= 40]
top.sort(key=lambda x: x[1], reverse=True)

print(f'缺图: {len(missing)}')
print(f'重点 (rank>=40): {len(top)}')
for n, r in top[:30]:
    print(f'  {n} (rank={r})')
print(f'其他: {len(missing) - len(top)}')
