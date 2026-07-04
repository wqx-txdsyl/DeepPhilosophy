"""
应用审计结果：去重、剔除流派、保持列表清洁
"""
import os, sys, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(SCRIPT_DIR, "_batch_philosophers_full.txt")
PHILO_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")

with open(LIST_FILE, "r", encoding="utf-8") as f:
    names = sorted(set(l.strip() for l in f if l.strip()))

before = len(names)

# ═══════════════════════════════════════
# 1. 移除流派/非人物
# ═══════════════════════════════════════
remove_schools = [
    "今文经学",
]
names = [n for n in names if n not in remove_schools]
print("Removed schools: " + str(remove_schools))

# ═══════════════════════════════════════
# 2. 去重：同名异译/简写，保留全名
#    格式: "短名": "全名"
#    ⚠️ 已排除假阳性（如 马克思≠马克思·舍勒）
# ═══════════════════════════════════════
dupe_map = {
    # 短名 → 全名（短名会被移除）
    "卡夫卡":   "弗朗茨·卡夫卡",
    "叔本华":   "阿图尔·叔本华",
    "德里达":   "雅克·德里达",
    "怀特海":   "阿尔弗雷德·诺思·怀特海",
    "本雅明":   "瓦尔特·本雅明",
    "波伏娃":   "西蒙娜·德·波伏娃",
    "皮尔士":   "查尔斯·桑德斯·皮尔士",
    "笛卡尔":   "勒内·笛卡尔",
    "胡塞尔":   "埃德蒙德·胡塞尔",
    "蒂利希":   "保罗·蒂利希",
    "贝克莱":   "乔治·贝克莱",
    "阿伦特":   "汉娜·阿伦特",
    "阿奎那":   "托马斯·阿奎那",
    "霍布斯":   "托马斯·霍布斯",
    "黑格尔":   "格奥尔格·威廉·弗里德里希·黑格尔",
    "伊利格瑞": "露西·伊利格瑞",
    "伽达默尔": "汉斯-格奥尔格·伽达默尔",
    "哈贝马斯": "尤尔根·哈贝马斯",
    "帕斯卡尔": "布莱兹·帕斯卡尔",
    "弗洛伊德": "西格蒙德·弗洛伊德",
    "斯宾诺莎": "巴鲁赫·斯宾诺莎",
    "海德格尔": "马丁·海德格尔",
    "莱布尼茨": "戈特弗里德·威廉·莱布尼茨",
    "克尔凯郭尔": "索伦·克尔凯郭尔",
    "梅洛-庞蒂": "莫里斯·梅洛-庞蒂",
    "维特根斯坦": "路德维希·维特根斯坦",
    "陀思妥耶夫斯基": "费奥多尔·陀思妥耶夫斯基",
    "卢森堡":   "罗莎·卢森堡",
    # "马克思" → "卡尔·马克思" is CORRECT (Karl Marx)
    # BUT "马克思" ≠ "马克思·舍勒" (Max Scheler is DIFFERENT)
    # Keep BOTH: 卡尔·马克思 and 马克思·舍勒
    # Only remove bare "马克思" (refers to Karl Marx)
    "马克思":   "卡尔·马克思",
}

# Ensure target names exist before removing short names
for short, full in dupe_map.items():
    if short in names and full in names:
        names.remove(short)
        print("Dedup: '" + short + "' -> '" + full + "'")
    elif short in names and full not in names:
        # Target doesn't exist — keep short name but flag
        print("WARN: '" + full + "' not in list, keeping '" + short + "'")
    else:
        print("SKIP: '" + short + "' already removed or not found")

# ═══════════════════════════════════════
# 3. 拆分（目前无需拆分，二程已处理）
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# 4. 排序 & 保存
# ═══════════════════════════════════════
names = sorted(set(names))
after = len(names)

# Delete images for removed names
all_removed = set(remove_schools) | {k for k, v in dupe_map.items() if k not in names}
for name in all_removed:
    safe = name.replace("/", "-").replace("\\", "-").replace(":", "：")
    for sub in ["", "thumb/"]:
        path = os.path.join(PHILO_DIR, sub, safe + ".jpg")
        if os.path.exists(path):
            os.remove(path)
            print("Deleted image: " + path)

with open(LIST_FILE, "w", encoding="utf-8") as f:
    for n in names:
        f.write(n + "\n")

print("\n" + "=" * 50)
print("AUDIT COMPLETE")
print("Before: " + str(before))
print("After:  " + str(after))
print("Removed: " + str(before - after))
print("=" * 50)
