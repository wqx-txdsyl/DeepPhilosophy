"""
精准修复错误/低质量图片 — 使用精确搜索词避免爬错人
"""
import os, sys, requests, time
from io import BytesIO
from PIL import Image

HEADERS = {"User-Agent": "DeepPhilosophy/1.0 (research; image fix)"}
PD = os.path.join(os.path.dirname(__file__), "..", "app", "public", "philosopher")
TD = os.path.join(PD, "thumb")
os.makedirs(TD, exist_ok=True)

# ── 精确搜索词（避免同名混淆）──
FIX_MAP = {
    # User reports: wrong person
    "智顗":     ["Zhiyi Buddhist monk Tiantai", "Tiantai Zhiyi"],
    "法藏":     ["Fazang Buddhist philosopher Huayan", "Fazang Huayan"],
    "波普":     ["Karl Popper philosopher", "Karl Popper portrait"],
    "温尼科特": ["Donald Winnicott psychoanalyst", "D. W. Winnicott"],
    # TINY images — use full name search
    "冯友兰":   ["Feng Youlan philosopher", "Fung Yu-lan"],
    "卡伦·霍妮": ["Karen Horney psychoanalyst", "Karen Horney"],
    "吉尔伯特·赖尔": ["Gilbert Ryle philosopher", "Gilbert Ryle"],
    "哈茨霍恩": ["Charles Hartshorne philosopher", "Charles Hartshorne"],
    "唐君毅":   ["Tang Junyi philosopher", "Tang Junyi New Confucian"],
    "尼古拉·哈特曼": ["Nicolai Hartmann philosopher", "Nicolai Hartmann"],
    "弗兰克尔": ["Viktor Frankl psychiatrist", "Viktor Frankl logotherapy"],
    "格奥尔格·齐美尔": ["Georg Simmel sociologist", "Georg Simmel philosopher"],
    "洛色林":   ["Roscelin of Compiegne", "Roscelin scholastic"],
    "神秀":     ["Shenxiu Buddhist monk", "Shenxiu Chan"],
    "福柯":     ["Michel Foucault philosopher", "Foucault portrait"],
    "米德":     ["George Herbert Mead philosopher", "George Herbert Mead"],
    "米歇尔·福柯": ["Michel Foucault philosopher", "Foucault portrait"],
    "阿尔弗雷德·艾耶尔": ["A. J. Ayer philosopher", "Alfred Jules Ayer"],
    "阿达莫夫": ["Arthur Adamov playwright", "Arthur Adamov"],
    "雅各布森": ["Roman Jakobson linguist", "Roman Jakobson"],
    "霍妮":     ["Karen Horney psychoanalyst", "Karen Horney"],
    # Modern NOFACE
    "马克斯·霍克海默": ["Max Horkheimer Frankfurt School", "Horkheimer portrait"],
    "迈克尔·沃尔泽": ["Michael Walzer philosopher", "Michael Walzer political theorist"],
    "奥尔特加·伊·加塞特": ["Jose Ortega y Gasset philosopher", "Ortega y Gasset portrait"],
}

def safe_name(name):
    return name.replace("/", "-").replace(":", chr(0xFF1A))

def del_image(name):
    for sub in ["", "thumb/"]:
        p = os.path.join(PD, sub, safe_name(name) + ".jpg")
        if os.path.exists(p):
            os.remove(p)

def search_wiki(query):
    """Search Wikipedia for page image"""
    params = {"action": "query", "format": "json", "list": "search", "srsearch": query, "srlimit": 3}
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=10)
        pages = r.json().get("query", {}).get("search", [])
    except:
        return None
    for p in pages:
        ip = {"action": "query", "format": "json", "prop": "pageimages", "titles": p["title"], "pithumbsize": 1200}
        try:
            r2 = requests.get("https://en.wikipedia.org/w/api.php", params=ip, headers=HEADERS, timeout=10)
            for pid, info in r2.json().get("query", {}).get("pages", {}).items():
                url = info.get("thumbnail", {}).get("source", "")
                title = info.get("title", "")
                if url:
                    return url, title
        except:
            continue
    return None, None

def download(url, name):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        img = Image.open(BytesIO(r.content)).convert("RGB")
        w, h = img.size
        if w < 200 or h < 200:
            return False  # Still too small
        path = os.path.join(PD, safe_name(name) + ".jpg")
        img.save(path, "JPEG", quality=92)
        thumb = img.copy()
        thumb.thumbnail((200, 280), Image.LANCZOS)
        thumb.save(os.path.join(TD, safe_name(name) + ".jpg"), "JPEG", quality=75)
        return True
    except:
        return False

def main():
    total = len(FIX_MAP)
    ok, fail, skip = 0, 0, 0

    for i, (name, queries) in enumerate(FIX_MAP.items(), 1):
        print(f"[{i}/{total}] {name}")
        path = os.path.join(PD, safe_name(name) + ".jpg")

        # Check existing
        if os.path.exists(path):
            try:
                img = Image.open(path)
                w, h = img.size
                size_kb = os.path.getsize(path) // 1024
                if w >= 400 and h >= 400 and size_kb >= 30:
                    print(f"  SKIP (already good: {w}x{h}, {size_kb}KB)")
                    skip += 1
                    continue
                else:
                    print(f"  Replacing (current: {w}x{h}, {size_kb}KB)")
            except:
                pass

        # Delete old
        del_image(name)

        # Try each query
        found = False
        for q in queries:
            print(f"  search: {q}")
            url, title = search_wiki(q)
            if url:
                print(f"  found: {title[:60]}")
                if download(url, name):
                    img = Image.open(path)
                    print(f"  OK: {img.size}, {os.path.getsize(path)//1024}KB")
                    ok += 1
                    found = True
                    break
            time.sleep(0.3)

        if not found:
            print(f"  FAIL")
            fail += 1

        time.sleep(0.5)

    print(f"\nDone: {ok} OK, {fail} FAIL, {skip} SKIP ({total} total)")

if __name__ == "__main__":
    main()
