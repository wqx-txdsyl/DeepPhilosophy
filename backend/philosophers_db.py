"""
哲学家信息库 —— 从 JSON 加载，避免 Python 转义问题
"""
import json, os
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_here, 'data', 'philosophers.json'), 'r', encoding='utf-8') as f:
    PHILOSOPHERS = json.load(f)

with open(os.path.join(_here, 'data', 'name_aliases.json'), 'r', encoding='utf-8') as f:
    NAME_ALIASES = json.load(f)

EMPTY_DIR_AUTHORS = [
    "乔尔丹诺·布鲁诺", "亨利·柏格森", "以赛亚·伯林", "克里斯蒂安·沃尔夫",
    "加斯东·巴什拉", "南希·卡特赖特", "威廉·狄尔泰", "尼古拉·哈特曼",
    "弗里德里希·H.雅可比", "托马斯·里德", "拉卡托斯·伊姆雷", "朱迪斯·巴特勒",
    "皮埃尔·迪昂", "皮埃尔·阿多", "约翰·邓斯·司各脱", "马克思·舍勒",
]

def get_philosopher_info(name: str) -> Optional[dict]:
    if not name:
        return None
    resolved_name = NAME_ALIASES.get(name, name)
    if resolved_name in PHILOSOPHERS:
        return PHILOSOPHERS[resolved_name]
    for key in PHILOSOPHERS:
        if key in resolved_name or resolved_name in key:
            return PHILOSOPHERS[key]
    return None
