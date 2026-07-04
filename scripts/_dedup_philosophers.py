"""
AI 去重：检测347哲人中的重复项，自动合并
用法: python _dedup_philosophers.py         # 检测，输出报告
     python _dedup_philosophers.py --apply # 执行合并
"""
import json, os, re, sys
from _lib import PHILOSOPHERS_FILE, ALIASES_FILE, get_deepseek_key, ask_deepseek, load_json, save_json

philo = load_json(PHILOSOPHERS_FILE)
aliases = load_json(ALIASES_FILE)

# 1. Find substring candidates
names = sorted(philo.keys())
pairs = []
for i, a in enumerate(names):
    for j, b in enumerate(names):
        if i >= j: continue
        if len(a) < len(b) and a in b:
            parts = b.replace('·', ' ').split()
            a_parts = a.replace('·', ' ').split()
            if any(ap in parts for ap in a_parts):
                pairs.append((a, b))
        elif len(b) < len(a) and b in a:
            parts = a.replace('·', ' ').split()
            b_parts = b.replace('·', ' ').split()
            if any(bp in parts for bp in b_parts):
                pairs.append((b, a))

pairs = sorted(set(pairs))
print(f"Found {len(pairs)} potential duplicate pairs")

# 2. Use AI to verify each pair
def ai_verify(short_name, long_name):
    """Ask AI if two names refer to the same person"""
    prompt = f"""判断这两个名字是否指代同一位哲学家：
- 短名: {short_name}
- 全名: {long_name}

请只回答 YES 或 NO。YES = 同一人（如"尼采"和"弗里德里希·尼采"），NO = 不同人（如"墨子"和"墨子的弟子"）。
如果短名是全名的简称/姓氏/常用译名，回答 YES。"""
    try:
        resp = ask_deepseek(prompt, max_tokens=10, temperature=0.1)
        return resp.strip().upper().startswith("YES")
    except:
        # Fallback heuristic: if short name is a complete word in long name
        short_parts = set(short_name.replace('·',' ').split())
        long_parts = set(long_name.replace('·',' ').split())
        return short_parts.issubset(long_parts)

confirmed = []
rejected = []
for short_name, long_name in pairs:
    print(f"  Checking: {short_name} <-> {long_name}...", end=" ", flush=True)
    if ai_verify(short_name, long_name):
        confirmed.append((short_name, long_name))
        print("YES")
    else:
        rejected.append((short_name, long_name))
        print("NO")

print(f"\nConfirmed duplicates: {len(confirmed)}")
print(f"Rejected: {len(rejected)}")

# 3. Merge confirmed duplicates
if "--apply" in sys.argv:
    for short_name, long_name in confirmed:
        # Merge: keep long_name, alias short_name to long_name
        if short_name in philo and long_name in philo:
            # Both exist — remove short_name, add alias
            del philo[short_name]
            aliases[short_name] = long_name
            print(f"  Merged: {short_name} -> {long_name}")
        elif short_name in philo:
            # Only short exists — rename to long
            philo[long_name] = philo.pop(short_name)
            aliases[short_name] = long_name
            print(f"  Renamed: {short_name} -> {long_name}")

    save_json(PHILOSOPHERS_FILE, philo)
    save_json(ALIASES_FILE, aliases)
    print(f"\nPhilosophers: {len(philo)}")
    print(f"Aliases: {len(aliases)}")
    print("Merged!")
else:
    print("\nRun with --apply to merge duplicates")

# Save report
with open(os.path.join(os.path.dirname(__file__), "_dedup_report.txt"), "w", encoding="utf-8") as f:
    f.write(f"Confirmed duplicates ({len(confirmed)}):\n")
    for s, l in confirmed: f.write(f"  {s} -> {l}\n")
    f.write(f"\nRejected ({len(rejected)}):\n")
    for s, l in rejected: f.write(f"  {s} <-> {l}\n")
print("Report: _dedup_report.txt")
