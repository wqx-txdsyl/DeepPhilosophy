"""
书籍摘要缓存 —— 从 main.py 提取的摘要加载/生成逻辑
"""
import os
import json
import time
from pathlib import Path
from loguru import logger


_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CACHE_PATH = os.path.join(_HERE, "data", "book_summaries.json")

_SUMMARIES_MEM_CACHE = None
_SUMMARIES_MEM_TIME = 0


def load_summaries_cache() -> dict:
    """加载书籍摘要缓存（内存缓存，10分钟有效）"""
    global _SUMMARIES_MEM_CACHE, _SUMMARIES_MEM_TIME
    now = time.time()
    if _SUMMARIES_MEM_CACHE is not None and (now - _SUMMARIES_MEM_TIME) < 600:
        return _SUMMARIES_MEM_CACHE
    if not os.path.exists(_CACHE_PATH):
        return {}
    try:
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            _SUMMARIES_MEM_CACHE = json.load(f)
        _SUMMARIES_MEM_TIME = now
        logger.debug(f"Loaded {len(_SUMMARIES_MEM_CACHE)} book summaries from cache")
        return _SUMMARIES_MEM_CACHE
    except Exception:
        return {}


def generate_summary(book: dict) -> str:
    """生成书籍摘要（纯缓存，瞬间返回）"""
    cache = load_summaries_cache()
    title = book.get("title", "")
    author = book.get("author", "")
    key = f"{title}||{author}"
    if key in cache and cache[key].get("summary"):
        return cache[key]["summary"]
    if title in cache and cache[title].get("summary"):
        return cache[title]["summary"]
    return f"《{title}》是{author}的著作，{book.get('file_type', 'N/A').upper()}格式，约{(book.get('file_size', 0) / 1024 / 1024):.1f}MB。"


def classify_book(title: str, author: str, region: str) -> list[str]:
    """根据书名和作者自动生成分类标签"""
    tags = []
    title_lower = title.lower()

    school_keywords = {
        "存在主义": ["存在", "existential"],
        "现象学": ["现象", "phenomenolog"],
        "形而上学": ["形而上学", "metaphysic"],
        "伦理学": ["伦理", "道德", "ethic", "moral"],
        "政治哲学": ["政治", "politic", "政府", "国家", "社会契约"],
        "美学": ["美学", "aesthetic", "艺术"],
        "认识论": ["认识", "知识", "理解", "epistemolog"],
        "逻辑学": ["逻辑", "logic", "推理"],
        "心灵哲学": ["心灵", "意识", "mind", "consciousness"],
        "语言哲学": ["语言", "language", "linguistic"],
        "科学哲学": ["科学", "science", "scientif"],
        "宗教哲学": ["宗教", "信仰", "神", "religion", "god"],
        "历史哲学": ["历史", "history"],
    }
    for school, kws in school_keywords.items():
        for kw in kws:
            if kw in title_lower:
                tags.append(school)
                break

    if any(kw in title for kw in ["全集", "文集", "选集", "著作", "作品"]):
        tags.append("全集/选集")
    elif any(kw in title for kw in ["批判", "论", "原理", "导论", "概论"]):
        tags.append("专著")
    elif any(kw in title for kw in ["对话", "篇", "录"]):
        tags.append("对话/语录")

    if region == "东方":
        if "儒家" in author or any(kw in title for kw in ["论语", "孟子", "大学", "中庸"]):
            tags.append("儒家")
        elif "道家" in author or any(kw in title for kw in ["道", "庄子", "老子"]):
            tags.append("道家")
        elif any(kw in title for kw in ["佛", "禅", "心经"]):
            tags.append("佛学")
    else:
        if any(kw in author for kw in ["柏拉图", "亚里士多德", "苏格拉底"]):
            tags.append("古希腊哲学")
        elif any(kw in author for kw in ["康德", "黑格尔", "尼采", "叔本华", "海德格尔"]):
            tags.append("德国哲学")
        elif any(kw in author for kw in ["笛卡尔", "萨特", "福柯", "德里达", "卢梭"]):
            tags.append("法国哲学")
        elif any(kw in author for kw in ["休谟", "洛克", "罗素", "维特根斯坦"]):
            tags.append("英国哲学")

    return tags[:4]


def book_sort_key(book: dict) -> int:
    """计算排序权重：合集最先，然后按哲学家出生年份升序"""
    author = book.get("author", "")
    if "合集" in author or "概述" in author:
        return -99999
    from db import get_philosopher_info
    info = get_philosopher_info(author)
    if info and info.get("era"):
        import re
        m = re.search(r'(\d+)', info["era"])
        if m:
            year = int(m.group(1))
            if "公元前" in info["era"] or "前" in info["era"]:
                year = -year
            return year
    return 9999
