"""作者 API 路由 — filters/详情/列表
从 main.py 拆分（2026-08-15），标签/世纪辅助复用 services.tag_utils
"""
import os, re, time, urllib.request, urllib.parse
from typing import Optional
from fastapi import APIRouter, Query
from starlette.responses import JSONResponse as StarletteJSON

from db import PHILOSOPHERS, NAME_ALIASES, get_philosopher_info
from services.book_scanner import scan_books, is_valid_author
from services.summaries import load_summaries_cache
from services.tag_utils import normalize_tag, expand_tags, era_to_centuries

router = APIRouter()

# 作者详情缓存（10 分钟）
_AUTHOR_DETAIL_CACHE = {}
# 作者列表缓存（5 分钟）
_AUTHORS_CACHE = None
_AUTHORS_CACHE_TIME = 0


def scrape_baidu_baike(author_name: str) -> Optional[dict]:
    """从百度百科爬取作者信息"""
    try:
        url = f"https://baike.baidu.com/item/{urllib.parse.quote(author_name)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        desc_match = re.search(
            r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
            html, re.IGNORECASE
        )
        bio = ""
        if desc_match:
            bio = desc_match.group(1).strip()
            bio = bio.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            bio = bio.replace("&quot;", '"').replace("&#039;", "'")

        if bio and len(bio) > 30:
            return {"bio": bio, "source": "baidu_baike", "wiki_url": url}
        return None
    except Exception:
        return None


def _infer_region(country_raw: str, school_raw: str = "") -> str:
    """从国家/流派字符串推断大区域"""
    if "中国" in country_raw:
        return "东方"
    if any(kw in country_raw for kw in ("日本","韩国","朝鲜","越南","蒙古","以色列","伊朗","土耳其","埃及","巴西","阿根廷","墨西哥","泰国","印度尼西亚","巴基斯坦","孟加拉","印度")):
        return "世界"
    if any(kw in school_raw for kw in ("印度哲学","日本哲学","伊斯兰","阿拉伯","非洲","犹太","波斯","拉美","东南亚","韩国")):
        return "世界"
    return "西方"


@router.get("/api/authors/filters")
async def get_author_filters():
    """获取作者多维度筛选选项（按世纪分组）—— 包含所有哲学家"""
    eras = set()
    countries = set()
    schools = set()

    for name, info in PHILOSOPHERS.items():
        if info.get("era"):
            for century in era_to_centuries(info["era"]):
                eras.add(century)
        if info.get("country"):
            for c in re.split(r'[/,、，;；]', info["country"]):
                c = c.strip()
                if c:
                    countries.add(c)
        if info.get("school"):
            for tag in re.split(r'[/,、，;；]', info["school"]):
                tag = tag.strip()
                if tag:
                    schools.add(tag)

    def _century_sort_key(c):
        m_bce = re.match(r'公元前(\d+)世纪', c)
        if m_bce:
            return (-int(m_bce.group(1)), 0)
        m_ce = re.match(r'(\d+)世纪', c)
        if m_ce:
            return (0, int(m_ce.group(1)))
        return (1, 0)

    _school_rank = {
        "古希腊哲学": 1, "启蒙运动": 2, "德国古典哲学": 3, "经验主义": 4,
        "理性主义": 5, "马克思主义": 6, "存在主义": 7, "现象学": 8,
        "分析哲学": 9, "实用主义": 10, "自由主义": 11, "政治哲学": 12,
        "伦理学": 13, "科学哲学": 14, "斯多葛学派": 15, "怀疑论": 16,
        "经院哲学": 17, "浪漫主义": 18, "宗教哲学": 19, "荒诞哲学": 20,
        "结构主义": 21, "后现代主义": 22, "精神分析学": 23, "法兰克福学派": 24,
        "生命哲学": 25, "功利主义": 26, "实证主义": 27, "实在论": 28,
        "唯心主义": 29, "历史唯物主义": 30, "后结构主义": 31, "过程哲学": 32,
        "哲学诠释学": 33, "技术哲学": 34, "社会学": 35, "女性主义": 36,
        "超验主义": 37, "教父哲学": 38, "托马斯主义": 39, "绝对唯心主义": 40,
        "唯名论": 41, "近代哲学": 42, "社群主义": 43, "基督教哲学": 44,
        "悲观主义哲学": 45,
    }
    def _school_sort_key(s):
        return _school_rank.get(s, 100)

    return StarletteJSON({
        "eras": sorted(eras, key=_century_sort_key),
        "countries": sorted(countries),
        "schools": sorted(schools, key=_school_sort_key),
    }, headers={"Cache-Control": "public, max-age=300"})


@router.get("/api/authors/{author_name}")
async def get_author_info(author_name: str):
    """获取作者详细信息（内置库优先，10分钟内存缓存）"""
    # 0. 缓存检查
    if author_name in _AUTHOR_DETAIL_CACHE:
        cached, cache_time = _AUTHOR_DETAIL_CACHE[author_name]
        if time.time() - cache_time < 600:
            return cached

    # 1. 先从内置数据库获取（O(1)，瞬间），同时解析别名
    info = get_philosopher_info(author_name)
    canonical_name = info.get("name", author_name) if info else author_name

    # 2. 书籍列表：用规范名匹配（别名→规范名）
    book_list = []
    book_count = 0
    region = info.get("country", "未知") if info else "未知"
    region = _infer_region(region, info.get("school", "") if info else "")
    if region == "未知":
        region = "西方"

    # 快速获取书籍：用规范名和别名同时匹配
    summaries = load_summaries_cache()
    import hashlib
    for key, entry in summaries.items():
        if "||" in key:
            title, author = key.split("||", 1)
            if author in (canonical_name, author_name):
                book_list.append({"id": hashlib.md5(key.encode()).hexdigest()[:12], "title": title, "file_type": "txt"})
                book_count += 1

    # 如果缓存没有，回退到完整扫描
    if book_count == 0:
        books = scan_books()
        author_books = [b for b in books if b["author"] in (canonical_name, author_name)]
        region = author_books[0]["region"] if author_books else region
        book_list = [{"id": b["id"], "title": b["title"], "file_type": b["file_type"]} for b in author_books]
        book_count = len(book_list)

    def build_response(source, era="", country="", school="", bio="", wiki_url=None):
        return {
            "name": canonical_name,
            "region": region,
            "era": era,
            "country": country,
            "school": school,
            "bio": bio,
            "wiki_url": wiki_url or f"https://en.wikipedia.org/wiki/{author_name}",
            "books": book_list,
            "book_count": book_count,
            "source": source,
        }

    if info:
        resp = build_response(
            "builtin_database",
            era=info.get("era", ""),
            country=info.get("country", ""),
            school=info.get("school", ""),
            bio=info.get("bio", ""),
            wiki_url=info.get("wiki_url"),
        )
    else:
        scraped = scrape_baidu_baike(author_name)
        if scraped:
            resp = build_response("baidu_baike", bio=scraped["bio"], wiki_url=scraped.get("wiki_url"))
        else:
            book_titles = [b["title"] for b in book_list]
            resp = build_response(
                "fallback",
                bio=f"{author_name}是{region}哲学史上的重要思想家。著有{'、'.join(book_titles[:5])}等作品。",
            )

    _AUTHOR_DETAIL_CACHE[author_name] = (resp, time.time())
    return resp


@router.get("/api/authors")
async def list_all_authors(tag: Optional[str] = Query(None)):
    """获取所有作者（带内存缓存，5分钟有效）"""
    global _AUTHORS_CACHE, _AUTHORS_CACHE_TIME
    now = time.time()
    if _AUTHORS_CACHE is not None and (now - _AUTHORS_CACHE_TIME) < 300:
        result = _AUTHORS_CACHE
    else:
        books = scan_books()
        authors_map = {}

        # 预处理别名反向索引（一次性）
        _alias_to_canonical = dict(NAME_ALIASES)

        for b in books:
            author = b["author"]
            if not is_valid_author(author):
                continue
            canonical = _alias_to_canonical.get(author, author)
            if canonical not in authors_map:
                info = get_philosopher_info(canonical)
                authors_map[canonical] = {
                    "name": canonical,
                    "region": b["region"],
                    "books": [],
                    "era": info.get("era", "") if info else "",
                    "country": info.get("country", "") if info else "",
                    "school": info.get("school", "") if info else "",
                }
            if b["title"] not in authors_map[canonical]["books"] and "待收录" not in b["title"]:
                authors_map[canonical]["books"].append(b["title"])

        # 补入哲学家数据库中的人物（无需磁盘扫描——philosophers.json 已全覆盖）
        for ph_name, ph_info in PHILOSOPHERS.items():
            if ph_name in authors_map or ph_name in _alias_to_canonical:
                continue
            country_raw = ph_info.get("country", "")
            school_raw = ph_info.get("school", "")
            region = _infer_region(country_raw, school_raw)
            authors_map[ph_name] = {
                "name": ph_name, "region": region, "books": [],
                "era": ph_info.get("era", ""), "country": country_raw,
                "school": school_raw,
            }
        _AUTHORS_CACHE = authors_map
        _AUTHORS_CACHE_TIME = now
        result = authors_map

    # 筛选 + 序列化
    _alias_to_canonical = dict(NAME_ALIASES)
    output = []
    for name, info in result.items():
        centuries = era_to_centuries(info.get("era", "")) if info.get("era") else []
        entry = {
            "name": name,
            "region": info["region"],
            "book_count": len(info["books"]),
            "books": info["books"][:10],
            "era": info["era"],
            "centuries": centuries,
            "country": re.sub(r'[（(][^)）]*[)）]', '', info.get("country", "")).strip(),
            "school": info["school"],
        }
        # 多标签筛选（逗号分隔，AND逻辑）
        if tag:
            raw_school = info.get("school") or ""
            expanded_schools = [t for s in re.split(r'[/,、，;；]', raw_school) if s.strip() for t in expand_tags(s.strip())]
            raw_country_clean = re.sub(r'[（(][^)）]*[)）]', '', info.get("country") or "")
            norm_countries = set(c.strip() for c in re.split(r'[/,、，;；]', raw_country_clean) if c.strip())
            all_match = True
            for t in tag.split(","):
                t = t.strip()
                if not t:
                    continue
                if t in raw_school or t in expanded_schools:
                    continue
                if t in raw_country_clean or t in norm_countries:
                    continue
                if t == info.get("era", ""):
                    continue
                if centuries and t in centuries:
                    continue
                all_match = False
                break
            if not all_match:
                continue
        output.append(entry)

    def _author_sort_key(author_name: str) -> int:
        """作者排序权重：合集=最前，按出生年份升序"""
        if "合集" in author_name or "概述" in author_name:
            return -99999
        info = get_philosopher_info(author_name)
        if info and info.get("era"):
            m = re.search(r'(\d+)', info["era"])
            if m:
                year = int(m.group(1))
                if "公元前" in info["era"] or "前" in info["era"]:
                    year = -year
                return year
        return 9999

    return StarletteJSON(
        {"authors": sorted(output, key=lambda a: (_author_sort_key(a["name"]), a["region"], a["name"]))},
        headers={"Cache-Control": "public, max-age=300"},
    )
