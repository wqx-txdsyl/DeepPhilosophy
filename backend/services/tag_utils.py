"""
标签归一化工具 —— 从 JSON 加载配置，提供与原来 main.py 硬编码相同的 API
"""
import json
import os
import re
from typing import Optional


_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TAG_DATA_PATH = os.path.join(_here, "data", "tag_normalization.json")

_tag_data: Optional[dict] = None


def _load_tag_data() -> dict:
    """懒加载标签归一化配置（内存缓存）"""
    global _tag_data
    if _tag_data is not None:
        return _tag_data
    if os.path.exists(_TAG_DATA_PATH):
        with open(_TAG_DATA_PATH, "r", encoding="utf-8") as f:
            _tag_data = json.load(f)
    else:
        _tag_data = {"merge_map": {}, "multi_map": {}, "country_norm": {}, "country_expand": {}}
    return _tag_data


def normalize_tag(tag: str) -> str:
    """归一化标签：合并相似标签到标准分类"""
    data = _load_tag_data()
    tag = tag.strip()
    return data["merge_map"].get(tag, tag)


def norm_country(c: str) -> list[str]:
    """标准化国家名，返回列表"""
    data = _load_tag_data()
    country_norm = data.get("country_norm", {})
    c = c.strip()
    if not c:
        return []
    c = re.sub(r'[（(][^)）]*[)）]', '', c).strip()
    results = []
    for part in re.split(r'[/,、，;；]', c):
        part = part.strip()
        if not part:
            continue
        mapped = country_norm.get(part, part)
        if mapped and mapped not in results:
            results.append(mapped)
    return results if results else [c]


def expand_tags(tag: str) -> list[str]:
    """展开标签用于筛选匹配（拆分组合标签 + 添加父标签）"""
    data = _load_tag_data()
    tag = tag.strip()
    result = [tag]

    # 拆分拼接标签（如 "存在主义女性主义" → ["存在主义", "女性主义"]）
    for kw in ['主义', '哲学', '学派', '理论', '思想']:
        idx = tag.find(kw)
        if 0 < idx < len(tag) - len(kw):
            part1 = tag[:idx + len(kw)]
            part2 = tag[idx + len(kw):]
            if part1 not in result:
                result.append(part1)
            if part2 not in result:
                result.append(part2)

    # 添加合并后的父标签
    display_parent = normalize_tag(tag)
    if display_parent != tag and display_parent not in result:
        result.append(display_parent)

    # 多标签展开
    multi_map = data.get("multi_map", {})
    extras = multi_map.get(tag, [])
    for t in extras:
        if t not in result:
            result.append(t)

    # 国家标签展开
    country_expand = data.get("country_expand", {})
    country_extras = country_expand.get(tag, [])
    for t in country_extras:
        if t not in result:
            result.append(t)

    return result


def era_to_century(era_str: str) -> Optional[str]:
    """将年代字符串转为世纪"""
    if not era_str or era_str in ("-", "未知", ""):
        return None
    m = re.search(r'(?:公元前|约公元前|约前|前)\s*(\d+)', era_str)
    if m:
        year = int(m.group(1))
        return f'公元前{(year + 99) // 100}世纪'
    m = re.search(r'(?<!\d)(\d{3,4})', era_str)
    if m:
        year = int(m.group(1))
        century = (year + 99) // 100 if year < 1000 else (year - 1) // 100 + 1
        return f'{century}世纪'
    return None


def era_to_centuries(era_str: str) -> list[str]:
    """获取哲学家生平覆盖的所有世纪"""
    if not era_str or era_str in ("-", "未知", ""):
        return []
    centuries = set()
    years = []
    # 公元前
    for m in re.finditer(r'(?:公元前|约公元前|约前|前)\s*(\d+)', era_str):
        years.append(-int(m.group(1)))
    # 公元
    for m in re.finditer(r'(?<![前\d])(?<!公元前)(?<!约公元前)(?<!约前)(\d{3,4})(?!\s*世纪)', era_str):
        years.append(int(m.group(1)))

    for y in years:
        if y < 0:
            centuries.add(f'公元前{(-y + 99) // 100}世纪')
        else:
            c = (y + 99) // 100 if y < 1000 else (y - 1) // 100 + 1
            centuries.add(f'{c}世纪')

    if len(years) >= 2:
        ymin, ymax = min(years), max(years)
        if ymin < 0 and ymax < 0:
            bc_start = (abs(ymin) + 99) // 100
            bc_end = (abs(ymax) + 99) // 100
            for c in range(bc_end, bc_start + 1):
                centuries.add(f'公元前{c}世纪')
        elif ymin > 0 and ymax > 0:
            for c in range((ymin + 99) // 100, (ymax + 99) // 100 + 1):
                centuries.add(f'{c}世纪')
        elif ymin < 0 and ymax > 0:
            bc_start = (abs(ymin) + 99) // 100
            for c in range(1, bc_start + 1):
                centuries.add(f'公元前{c}世纪')
            for c in range(1, (ymax + 99) // 100 + 1):
                centuries.add(f'{c}世纪')

    return sorted(centuries, key=lambda x: (
        -int(re.search(r'(\d+)', x).group(1)) if '公元前' in x else 0,
        int(re.search(r'(\d+)', x).group(1)) if '公元前' not in x else 0,
    ))
