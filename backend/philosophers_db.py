"""
哲学家信息库 —— 从 JSON 加载，O(1) 查找（含预建索引）
"""
import json, os
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_here, 'data', 'philosophers.json'), 'r', encoding='utf-8') as f:
    PHILOSOPHERS = json.load(f)
PHILOSOPHER_COUNT = len(PHILOSOPHERS)

with open(os.path.join(_here, 'data', 'name_aliases.json'), 'r', encoding='utf-8') as f:
    NAME_ALIASES = json.load(f)

EMPTY_DIR_AUTHORS = [
    "乔尔丹诺·布鲁诺", "亨利·柏格森", "以赛亚·伯林", "克里斯蒂安·沃尔夫",
    "加斯东·巴什拉", "南希·卡特赖特", "威廉·狄尔泰", "尼古拉·哈特曼",
    "弗里德里希·H.雅可比", "托马斯·里德", "拉卡托斯·伊姆雷", "朱迪斯·巴特勒",
    "皮埃尔·迪昂", "皮埃尔·阿多", "约翰·邓斯·司各脱", "马克思·舍勒",
]

# ——— 预建 O(1) 查找索引 ———
# 1. 合并别名映射（别名 → 标准名）
_ALIAS_TO_KEY = dict(NAME_ALIASES)
# 2. 对每个标准名，也映射其自身
for k in PHILOSOPHERS:
    _ALIAS_TO_KEY.setdefault(k, k)
# 3. 对不含姓氏的单名（如"柏拉图"、"康德"），建短名→全名映射
_SHORT_NAME_INDEX = {}
for k in PHILOSOPHERS:
    # 去掉姓氏试试（如"伊曼努尔·康德" → "康德"）
    parts = k.replace('·', ' ').split()
    for p in parts:
        if len(p) >= 2:
            _SHORT_NAME_INDEX.setdefault(p, []).append(k)
# 4. 对短名列表去重（只保留唯一匹配的）
_SHORT_NAME_UNIQUE = {k: v[0] for k, v in _SHORT_NAME_INDEX.items() if len(v) == 1}


def get_philosopher_info(name: str) -> Optional[dict]:
    """O(1) 查找哲学家信息"""
    if not name:
        return None

    # Step 1: 别名/标准名精确匹配 O(1)
    if name in _ALIAS_TO_KEY:
        return PHILOSOPHERS.get(_ALIAS_TO_KEY[name])

    # Step 2: 短名单名匹配 O(1)
    if name in _SHORT_NAME_UNIQUE:
        return PHILOSOPHERS.get(_SHORT_NAME_UNIQUE[name])

    # Step 3: 包含匹配（模糊搜索，仅当以上都失败时，O(n)）
    # 优先完全包含关系
    for key in PHILOSOPHERS:
        if name in key or key in name:
            return PHILOSOPHERS[key]

    return None
