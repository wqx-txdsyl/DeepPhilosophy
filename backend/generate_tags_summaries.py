"""
DeepPhilosophy 书籍标签和简介批量生成工具
使用 DeepSeek API 为所有缺少标签/简介的书籍生成内容
运行: KNOWLEDGE_DIR=F:/philosophy python generate_tags_summaries.py
"""
import json
import os
import sys
import time
import traceback
import io
from pathlib import Path

# Fix Windows GBK encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# === 配置 ===
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
SUMMARIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "book_summaries.json")
BOOKS_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "books_cache.json")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def chat(messages, temperature=0.7, max_tokens=512, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3 ** attempt)
            else:
                raise RuntimeError(str(e))
    return ""

def generate_tags_only(author, title, region, existing_summary):
    """从已有摘要中提取标签"""
    prompt = f"""你是一位哲学图书分类专家。请根据以下书籍信息，为该书包生成2-5个标签（短关键词，用于筛选分类）。

作者：{author}
书名：《{title}》
地域：{region}
现有摘要：{existing_summary[:300]}

请只输出标签，用逗号分隔，不要输出其他任何内容。标签示例：存在主义、古希腊哲学、伦理学、政治哲学、德国古典哲学、现象学、实用主义、启蒙运动、分析哲学、斯多葛学派、儒家、道家、马克思主义、后现代主义、精神分析学、科学哲学...
标签应当准确、尽可能使用公认的哲学流派/学派名称。"""

    result = chat([
        {"role": "system", "content": "你是一个专业的哲学图书分类助手。只输出逗号分隔的标签，不输出其他任何内容。"},
        {"role": "user", "content": prompt}
    ], temperature=0.5, max_tokens=100)

    tags = [t.strip() for t in result.replace("，", ",").split(",")]
    tags = [t for t in tags if t and len(t) >= 2]
    return tags[:6]

def generate_summary_and_tags(author, title, region, file_type):
    """为没有摘要的书生成标签和简介"""
    prompt = f"""请为以下哲学著作撰写一段简介（50-150字），并为它打2-5个分类标签。

作者：{author}
书名：《{title}》
地域：{region}哲学
格式：{file_type}

简介要求：
- 不少于50字
- 说明该书的主题、核心思想和哲学贡献
- 语言简明扼要，有学术深度
- 如果该书是佚失/残篇，请说明其历史意义和现存情况

标签要求：用公认的哲学流派/学派名称，如：古希腊哲学、存在主义、德国古典哲学、伦理学、政治哲学、现象学、实用主义、启蒙运动、分析哲学、斯多葛学派、儒家、道家...

请严格按以下格式输出（模板格式，不要改动）：
简介：<这里写简介>
标签：<标签1>, <标签2>, <标签3>"""

    result = chat([
        {"role": "system", "content": "你是一个专业的哲学图书编目专家。请严格按照要求的格式输出，不要输出多余内容。"},
        {"role": "user", "content": prompt}
    ], temperature=0.7, max_tokens=400)

    summary = ""
    tags = []

    for line in result.split("\n"):
        line = line.strip()
        if line.startswith("简介：") or line.startswith("简介:"):
            summary = line.replace("简介：", "").replace("简介:", "").strip()
        elif line.startswith("标签：") or line.startswith("标签:"):
            tag_str = line.replace("标签：", "").replace("标签:", "").strip()
            tags = [t.strip() for t in tag_str.replace("，", ",").split(",")]
            tags = [t for t in tags if t and len(t) >= 2]

    # Fallback: if format not followed, try to extract
    if not summary:
        # Use first meaningful line as summary
        lines = [l.strip() for l in result.split("\n") if l.strip() and not l.startswith("标签")]
        if lines:
            summary = "".join(lines)[:300]
    if not summary:
        summary = f"《{title}》是{author}的哲学著作。"

    return summary[:300], tags[:6]


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_template_summary(s):
    """检测是否为模板生成的假摘要"""
    if not s or s.strip() == "":
        return True
    patterns = [
        "的著作，TXT格式",
        "的著作，PDF格式",
        "的著作，EPUB格式",
        "的导读作品。在希腊哲学与基督教信仰",
        "的书信集。以天理为形上本体",
        "的文集/作品集。以亚里士多德逻辑学",
        "的文集/选集。以宏伟的体系性",
        "的文集/作品集。直面人的被抛",
        "的书信/日记。",  # too vague
    ]
    for p in patterns:
        if p in s:
            return True
    return len(s) < 50

def main():
    print("=" * 60)
    print("  DeepPhilosophy 标签+简介批量生成工具")
    print("=" * 60)

    # Import scan_books from main.py
    from config import KNOWLEDGE_DIR
    print(f"  知识库目录: {KNOWLEDGE_DIR}")

    # Import scan function
    import main as backend_main
    books = backend_main.scan_books()
    print(f"  扫描到 {len(books)} 本书")

    # Load existing data
    summaries = load_json(SUMMARIES_PATH)
    print(f"  已有摘要缓存: {len(summaries)} 条")

    # Classify books
    need_tags_only = []
    need_full = []
    ok = []

    for b in books:
        title = b["title"]
        author = b.get("author", "")
        key = f"{title}||{author}"
        entry = summaries.get(key, {})
        s = entry.get("summary", "")
        t = entry.get("tags", [])

        if is_template_summary(s):
            need_full.append(b)
        elif not t or len(t) == 0:
            need_tags_only.append(b)
        else:
            ok.append(b)

    print(f"  已完成(有标签+真摘要): {len(ok)}")
    print(f"  缺标签(有摘要): {len(need_tags_only)}")
    print(f"  缺标签+摘要(模板/空白): {len(need_full)}")
    print()

    if not need_tags_only and not need_full:
        print("[OK] 所有书籍都已完整！无需处理。")
        return

    total = len(need_tags_only) + len(need_full)
    processed = 0
    errors = 0

    # === Phase 1: Tag-only books (fast) ===
    print(f"[Phase 1] 为 {len(need_tags_only)} 本书补标签...")
    for i, b in enumerate(need_tags_only):
        title = b["title"]
        author = b["author"]
        region = b["region"]
        key = f"{title}||{author}"
        existing_summary = summaries.get(key, {}).get("summary", "")

        try:
            print(f"  [{i+1}/{len(need_tags_only)}] {region} {author} - {title}")
            tags = generate_tags_only(author, title, region, existing_summary)

            if key not in summaries:
                summaries[key] = {}
            summaries[key]["tags"] = tags
            print(f"    [OK] 标签: {', '.join(tags)}")
            processed += 1

            # Save every 10
            if processed % 10 == 0:
                save_json(SUMMARIES_PATH, summaries)
                print(f"  [SAVED] {processed}/{total}")

            time.sleep(0.5)  # Rate limit

        except Exception as e:
            errors += 1
            print(f"    [FAIL] {e}")
            time.sleep(3)

    # === Phase 2: Full generation books (slow) ===
    print(f"\n[Phase 2] 为 {len(need_full)} 本书生成标签+简介...")
    for i, b in enumerate(need_full):
        title = b["title"]
        author = b["author"]
        region = b["region"]
        ftype = b["file_type"]
        status = b["status"]
        key = f"{title}||{author}"

        try:
            label = f"[{i+1}/{len(need_full)}]"
            print(f"  {label} {region} {author} - {title} ({ftype}, {status})")

            summary, tags = generate_summary_and_tags(author, title, region, ftype)

            if key not in summaries:
                summaries[key] = {}
            summaries[key]["summary"] = summary
            summaries[key]["tags"] = tags
            print(f"    [OK] 简介({len(summary)}字): {summary[:80]}...")
            print(f"    [OK] 标签: {', '.join(tags) if tags else '(无)'}")
            processed += 1

            # Save every 5
            if processed % 5 == 0:
                save_json(SUMMARIES_PATH, summaries)
                print(f"  [SAVED] {processed}/{total}")

            time.sleep(0.5)  # Rate limit

        except Exception as e:
            errors += 1
            print(f"    [FAIL] {e}")
            traceback.print_exc()
            time.sleep(3)

    # Final save
    save_json(SUMMARIES_PATH, summaries)
    print()
    print("=" * 60)
    print(f"  [DONE] 处理完成！")
    print(f"  成功: {processed - errors}")
    print(f"  失败: {errors}")
    print(f"  总摘要数: {len(summaries)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
