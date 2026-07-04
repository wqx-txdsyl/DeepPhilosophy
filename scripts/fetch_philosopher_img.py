#!/usr/bin/env python3
"""
哲学家头像爬取 —— Wikipedia / Wikimedia Commons 无水印照片
用法: python fetch_philosopher_img.py "哲学家名"
"""
import sys, os, json, re, requests, io
from PIL import Image
from urllib.parse import quote, urljoin

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")
HEADERS = {"User-Agent": "DeepPhilosophy/1.0 (https://github.com/wqx-txdsyl/DeepPhilosophy; philosophical image research)"}
WIKI_API = "https://zh.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

def step(msg):
    print(f"  {msg}")

# ═══════════════════════════════════════════════
# Step 1: Wikipedia 搜图（首选：信息框图片）
# ═══════════════════════════════════════════════
def search_wikipedia(name):
    """通过 Wikipedia API 获取哲学家页面信息框中的主图"""
    step(f"Wikipedia 搜索: {name}")

    # 先搜页面
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": name, "srlimit": 3,
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
        pages = r.json().get("query", {}).get("search", [])
    except Exception as e:
        print(f"  [WARN] Wikipedia 搜索失败: {e}")
        return None

    if not pages:
        print("  [WARN] Wikipedia 未找到匹配页面")
        return None

    # 逐个尝试获取页面主图
    for p in pages:
        title = p["title"]
        step(f"  检查页面: {title}")
        img_params = {
            "action": "query", "format": "json",
            "prop": "pageimages", "titles": title,
            "pithumbsize": 800, "pilimit": 1,
        }
        try:
            r = requests.get(WIKI_API, params=img_params, headers=HEADERS, timeout=15)
            pages_data = r.json().get("query", {}).get("pages", {})
        except Exception:
            continue

        for pid, info in pages_data.items():
            thumb = info.get("thumbnail", {})
            if thumb:
                url = thumb.get("source", "")
                if url:
                    print(f"  [OK] 找到图片: {url[:80]}...")
                    return url

    print("  [WARN] 未在页面中找到信息框图片，尝试 Wikimedia Commons...")
    return None

# ═══════════════════════════════════════════════
# Step 2: Wikimedia Commons 搜图（备用）
# ═══════════════════════════════════════════════
def search_commons(name):
    """在 Wikimedia Commons 搜索高分辨率无水印照片"""
    step(f"Wikimedia Commons 搜索: {name}")

    # 尝试英文名搜索（更全）
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": f"{name} portrait",
        "srnamespace": 6,  # File namespace
        "srlimit": 5,
        "srsort": "relevance",
    }
    try:
        r = requests.get(COMMONS_API, params=params, headers=HEADERS, timeout=15)
        results = r.json().get("query", {}).get("search", [])
    except Exception as e:
        print(f"  [WARN] Commons 搜索失败: {e}")
        return None

    if not results:
        print("  [WARN] Commons 未找到匹配文件")
        return None

    # 获取文件信息，筛选 JPG/PNG
    titles = [item["title"] for item in results[:5]]
    img_params = {
        "action": "query", "format": "json",
        "prop": "imageinfo", "titles": "|".join(titles),
        "iiprop": "url|size|mime", "iiurlwidth": 800,
    }
    try:
        r = requests.get(COMMONS_API, params=img_params, headers=HEADERS, timeout=15)
        pages = r.json().get("query", {}).get("pages", {})
    except Exception:
        return None

    candidates = []
    for pid, info in pages.items():
        ii = info.get("imageinfo", [{}])[0]
        url = ii.get("thumburl") or ii.get("url", "")
        mime = ii.get("mime", "")
        size = ii.get("size", 0)
        # 优先 JPG/PNG，>50KB（太小可能是图标），<10MB
        if url and any(t in mime for t in ("jpeg", "png")) and 50000 < size < 10_000_000:
            # 偏好人像构图（竖版）— 从 URL 可推测缩略图宽高
            candidates.append((url, size))

    if candidates:
        # 选最大的
        candidates.sort(key=lambda x: x[1], reverse=True)
        url = candidates[0][0]
        print(f"  [OK] Commons 找到: {url[:80]}... ({candidates[0][1]} bytes)")
        return url

    print("  [WARN] Commons 无合适的 JPG/PNG 文件")
    return None

# ═══════════════════════════════════════════════
# Step 3: 下载 & 保存
# ═══════════════════════════════════════════════
def download_and_save(url, name):
    """下载图片并保存为 JPG"""
    step(f"下载: {url[:80]}...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
    except Exception as e:
        print(f"  [FAIL] 下载失败: {e}")
        return False

    img = Image.open(io.BytesIO(r.content)).convert("RGB")

    # 保存原图
    os.makedirs(OUT_DIR, exist_ok=True)
    safe_name = name.replace("/", "-").replace("\\", "-").replace(":", "：")
    out_path = os.path.join(OUT_DIR, f"{safe_name}.jpg")
    img.save(out_path, "JPEG", quality=92)
    print(f"  [OK] 已保存: {out_path} ({img.size[0]}×{img.size[1]})")

    # 生成缩略图（200×280）
    thumb_dir = os.path.join(OUT_DIR, "thumb")
    os.makedirs(thumb_dir, exist_ok=True)
    thumb = img.copy()
    thumb.thumbnail((200, 280), Image.LANCZOS)
    thumb.save(os.path.join(thumb_dir, f"{safe_name}.jpg"), "JPEG", quality=75)
    print(f"  [OK] 缩略图已生成")

    return out_path

# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("用法: python fetch_philosopher_img.py '哲学家名'")
        print("示例: python fetch_philosopher_img.py '孔子'")
        print("      python fetch_philosopher_img.py 'Immanuel Kant'")
        sys.exit(1)

    name = sys.argv[1]
    print(f"\n{'='*50}")
    print(f"  爬取哲学家图片: {name}")
    print(f"{'='*50}")

    # 检查是否已存在
    safe_name = name.replace("/", "-").replace("\\", "-").replace(":", "：")
    existing = os.path.join(OUT_DIR, f"{safe_name}.jpg")
    if os.path.exists(existing):
        print(f"  [SKIP] 图片已存在: {existing}")
        return

    # 依次尝试 Wikipedia → Wikimedia Commons
    url = search_wikipedia(name) or search_commons(name)

    if not url:
        print(f"\n[FAIL] 未找到 {name} 的无水印照片")
        print("  建议：手动从以下来源获取：")
        print("    - https://commons.wikimedia.org/")
        print("    - https://zh.wikipedia.org/")
        print(f"  并保存到: {existing}")
        sys.exit(1)

    path = download_and_save(url, name)
    if path:
        print(f"\n[SUCCESS] {name} → {path}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
