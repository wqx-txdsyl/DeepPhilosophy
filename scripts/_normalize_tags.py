"""
标签规范化模块 — add_author / _batch_add 入库后自动调用
"""
import re

# 拆分：组合标签 → 独立标签
SPLIT_MAP = {
    "存在主义女性主义": "存在主义/女性主义",
    "马克思主义女性主义": "马克思主义/女性主义",
    "精神分析学女性主义": "精神分析学/女性主义",
    "自由主义女性主义": "自由主义/女性主义",
    "后结构主义女性主义": "后结构主义/女性主义",
    "分析哲学女性主义": "分析哲学/女性主义",
    "实用主义女性主义": "实用主义/女性主义",
    "批判理论女性主义": "批判理论/女性主义",
    "后现代主义女性主义": "后现代主义/女性主义",
    "现象学存在主义": "现象学/存在主义",
    "现象学诠释学": "现象学/哲学诠释学",
    "分析哲学马克思主义": "分析哲学/马克思主义",
    "存在主义现象学": "存在主义/现象学",
    "马克思主义存在主义": "马克思主义/存在主义",
    "结构主义马克思主义": "结构主义/马克思主义",
    "后现代女性主义": "后现代主义/女性主义",
}

# 合并：别名 → 标准流派名
MERGE_MAP = {
    "希腊哲学": "古希腊哲学",
    "德国唯心主义": "德国古典哲学",
    "德意志唯心论": "德国古典哲学",
    "语言分析哲学": "分析哲学",
    "逻辑分析哲学": "分析哲学",
    "存在哲学": "存在主义",
    "存在主义哲学": "存在主义",
    "马克思哲学": "马克思主义",
    "马克思主义哲学": "马克思主义",
    "后结构": "后结构主义",
    "新儒家": "现代新儒家",
    "当代新儒家": "现代新儒家",
    "实用主义哲学": "实用主义",
    "生命学派": "生命哲学",
    "实在论哲学": "实在论",
    "唯心论": "唯心主义",
    "经验论": "经验主义",
    "理性论": "理性主义",
    "现象学派": "现象学",
    "中国马克思主义": "中国马克思主义哲学",
    "语言哲学": "分析哲学",
}

def normalize_school(school_str):
    """规范化流派标签"""
    if not school_str:
        return ""
    s = school_str
    # 先去重
    parts = list(dict.fromkeys(p.strip() for p in re.split(r'[/,，、;；]', s) if p.strip()))
    s = "/".join(parts)

    # 拆分组合标签
    for bad, good in SPLIT_MAP.items():
        if bad in s and good not in s:
            s = s.replace(bad, good)

    # 合并相似标签
    for alias, canonical in MERGE_MAP.items():
        if alias in s and canonical not in s:
            # Split, replace, rejoin
            parts = s.split('/')
            new_parts = [canonical if p == alias else p for p in parts]
            s = '/'.join(new_parts)
            if s == alias:
                s = canonical

    # 重新收集去重
    parts = list(dict.fromkeys(p.strip() for p in re.split(r'[/,，、;；]', s) if p.strip()))
    return "/".join(parts)

def normalize_country(country_str):
    """规范化国家标签 — 去掉括号注释，保留核心国名"""
    if not country_str:
        return ""
    s = country_str
    # 去掉移居/移民/迁居/流亡/入籍等括号注释
    s = re.sub(r'[（(][^)）]*?移居[^)）]*[)）]', '', s)
    s = re.sub(r'[（(][^)）]*?移民[^)）]*[)）]', '', s)
    s = re.sub(r'[（(][^)）]*?迁居[^)）]*[)）]', '', s)
    s = re.sub(r'[（(][^)）]*?流亡[^)）]*[)）]', '', s)
    s = re.sub(r'[（(][^)）]*?入籍[^)）]*[)）]', '', s)
    s = re.sub(r'[（(][^)）]*?归化[^)）]*[)）]', '', s)
    # 统一分隔符
    s = re.sub(r'\s*/\s*', '/', s)
    s = re.sub(r'\s*,\s*', '/', s)
    s = re.sub(r'\s*、\s*', '/', s)
    s = s.strip(' /')
    return s

def normalize_philosopher(info):
    """规范化一位哲学家的所有标签"""
    if "school" in info:
        info["school"] = normalize_school(info["school"])
    if "country" in info:
        info["country"] = normalize_country(info["country"])
    return info

def normalize_all(philosophers_dict):
    """规范化整个哲学家字典"""
    fixed = 0
    for name, info in philosophers_dict.items():
        orig_school = info.get("school", "")
        orig_country = info.get("country", "")
        info = normalize_philosopher(info)
        if info.get("school") != orig_school or info.get("country") != orig_country:
            fixed += 1
    return fixed
