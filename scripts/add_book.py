#!/usr/bin/env python3
"""
一键新增书籍：扫描本地 → DeepSeek 生成标签+摘要 → 插入后端 → 更新前端计数
用法: python add_book.py "F:/philosophy/西方/尼采/查拉图斯特拉如是说.pdf"
     python add_book.py --scan    # 扫描整个 F:/philosophy，批量处理新书
"""
import sys, os, json, re, requests, shutil, hashlib
from pathlib import Path
from datetime import datetime

# ── 路径 ──
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(ROOT, "backend", "data")
SUMMARIES_FILE = os.path.join(JSON_DIR, "book_summaries.json")
CACHE_FILE = os.path.join(JSON_DIR, "books_cache.json")
PHILOSOPHERS_FILE = os.path.join(JSON_DIR, "philosophers.json")
KNOWLEDGE_DIR = "F:/philosophy"

# ── API ──
_keys_path = os.path.join(os.path.dirname(__file__), "api_keys.json")
with open(_keys_path) as f: _keys = json.load(f)
DEEPSEEK_KEY = _keys["deepseek"]
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"

KNOWN_TAGS = [
    "古希腊哲学","教父哲学","经院哲学","唯名论","理性主义","经验主义","启蒙运动",
    "实在论","唯心主义","自由主义","浪漫主义","德国古典哲学","功利主义","超验主义",
    "实证主义","马克思主义","生命哲学","社会学","实用主义","精神分析学","现象学",
    "存在主义","分析哲学","过程哲学","哲学人类学","西方马克思主义","法兰克福学派",
    "批判理论","科学哲学","荒诞哲学","基督教哲学","结构主义","政治哲学","哲学诠释学",
    "解构主义","后结构主义","后现代主义","伦理学","宗教哲学","女性主义","社群主义",
    "技术哲学","斯多葛学派","怀疑论","儒家","道家","墨家","法家","名家","阴阳家",
    "兵家","两汉经学","魏晋玄学","隋唐佛学","宋明理学","明清实学","乾嘉朴学",
    "天演论","维新派","三民主义","毛泽东思想","现代新儒家","印度哲学","日本哲学",
    "韩国哲学","伊斯兰哲学","阿拉伯哲学","非洲哲学","拉丁美洲哲学"
]

# ══════════ 辅助 ══════════
def load_json(path, default={}):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

# ══════════ 从文件名解析 ══════════
def parse_path(filepath):
    """从 F:/philosophy/西方/尼采/查拉图斯特拉如是说.pdf 解析出 region, author, title, file_type"""
    rel = os.path.relpath(filepath, KNOWLEDGE_DIR).replace("\\", "/")
    parts = rel.split("/")
    region = parts[0] if len(parts) > 0 else "未知"
    author = parts[1] if len(parts) > 1 else "未知"
    author = author.replace("###合集&概述###", "合集&概述")
    title = Path(filepath).stem
    ext = Path(filepath).suffix.lower()
    ft = ext.replace(".", "")
    return region, author, title, ft

# ══════════ DeepSeek 生成标签+摘要 ══════════
def generate_tags_summary(title, author, region):
    """用 DeepSeek 为一本书生成标签和摘要"""
    prompt = f"""你是一个哲学文献专家。请为以下书籍生成标签和摘要：

书名：《{title}》
作者：{author}
所属传统：{region}哲学

要求：
1. 标签：从已知标签列表中选择2-5个最匹配的。已知标签：{', '.join(KNOWN_TAGS)}。如果没有完全匹配的，可以提出新标签建议。
2. 摘要：≥300字，涵盖主题、核心思想、哲学贡献。必须是连贯散文，自然段落，绝对禁止分条列点/编号/加粗。

输出 JSON 格式（不要markdown代码块）：
{{"tags": ["标签1", "标签2"], "summary": "摘要内容", "new_tags": ["新标签（如果有）"]}}"""

    r = requests.post(DEEPSEEK_API,
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.5, "max_tokens": 1500}, timeout=120)
    content = r.json()["choices"][0]["message"]["content"]
    content = re.sub(r'^```json\s*', '', content).replace('```', '')
    return json.loads(content)

# ══════════ 主流程 ══════════
def add_book(filepath):
    region, author, title, ft = parse_path(filepath)
    key = f"{title}||{author}"
    print(f"\n📖 {title} — {author} ({region}, {ft})")

    # 1. 检查是否已存在
    summaries = load_json(SUMMARIES_FILE, {})
    if key in summaries:
        print(f"  - 已存在摘要缓存，跳过")
        return

    # 2. 生成标签+摘要
    print(f"  DeepSeek 生成中...")
    result = generate_tags_summary(title, author, region)
    tags = result.get("tags", [])
    summary = result.get("summary", "")
    new_tags = result.get("new_tags", [])

    # 3. 保存
    summaries[key] = {"summary": summary, "tags": tags}
    save_json(SUMMARIES_FILE, summaries)
    print(f"  ✓ 摘要已保存 ({len(summary)}字)")

    # 4. 书籍缓存
    cache = load_json(CACHE_FILE, {})
    cache[key] = {"tags": tags, "title": title, "author": author, "region": region}
    save_json(CACHE_FILE, cache)

    # 5. 更新哲学家数据
    philosophers = load_json(PHILOSOPHERS_FILE, {})
    if author not in philosophers and "合集" not in author:
        philosophers[author] = {
            "era": "", "country": "", "school": ", ".join(tags[:3]),
            "bio": f"{author}，{region}哲学思想家。",
            "wiki_url": f"https://en.wikipedia.org/wiki/{author.replace(' ', '_')}",
            "books": [title]
        }
    elif author in philosophers:
        if "books" not in philosophers[author]:
            philosophers[author]["books"] = []
        if title not in philosophers[author]["books"]:
            philosophers[author]["books"].append(title)
    save_json(PHILOSOPHERS_FILE, philosophers)

    # 6. 新标签提示
    if new_tags:
        print(f"  ⚠ 新标签建议: {new_tags}")
        print(f"    请手动添加到标签规范化系统（backend/main.py + AuthorsPage.jsx normMap）")

    # 7. 状态
    status = "available" if ft != "txt" else "pending"
    file_id = hashlib.md5(filepath.encode()).hexdigest()[:12]
    print(f"  状态: {status} | ID: {file_id}")
    print(f"  下一步: cd app && npm run build && 同步 backend/app-dist")

def scan_all():
    """扫描 F:/philosophy，处理所有新书"""
    print(f"扫描 {KNOWLEDGE_DIR}...")
    count = 0
    for root, dirs, files in os.walk(KNOWLEDGE_DIR):
        dirs[:] = [d for d in dirs if d.lower() not in ('jpg', 'thumb', 'gene', 'icons')]  # 跳过图片目录
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in ('.pdf', '.epub', '.txt'):
                fp = os.path.join(root, f)
                # 检查是否已处理
                region, author, title, ft = parse_path(fp)
                key = f"{title}||{author}"
                summaries = load_json(SUMMARIES_FILE, {})
                if key not in summaries:
                    try:
                        add_book(fp)
                        count += 1
                    except Exception as e:
                        print(f"  FAIL: {fp} ({e})")
    print(f"\n处理完成: {count} 本新书")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python add_book.py 'F:/philosophy/.../书.pdf'")
        print("      python add_book.py --scan")
        sys.exit(1)
    if sys.argv[1] == "--scan":
        scan_all()
    else:
        add_book(sys.argv[1])
