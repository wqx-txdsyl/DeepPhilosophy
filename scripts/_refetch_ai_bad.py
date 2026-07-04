"""
重爬 AI 识别出的错误图片 — 多源搜索 (Wikipedia → Commons → Wikidata → Britannica)
"""
import os, sys, json, time, urllib.request, urllib.parse
from io import BytesIO
from PIL import Image

# Fix Windows GBK encoding
if sys.platform == 'win32':
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHILO_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")
BAD_LIST = os.path.join(SCRIPT_DIR, "_all_refetch.txt")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DeepPhilosophy/1.0)"}
THUMB_DIR = os.path.join(PHILO_DIR, "thumb")
os.makedirs(THUMB_DIR, exist_ok=True)

# Known good search overrides for problematic philosophers
SEARCH_OVERRIDES = {}

def safe_name(name):
    return name.replace("/", "-").replace(":", "：")

def img_path(name):
    return os.path.join(PHILO_DIR, safe_name(name) + ".jpg")

def delete_images(name):
    for sub in ["", "thumb/"]:
        p = os.path.join(PHILO_DIR, sub, safe_name(name) + ".jpg")
        if os.path.exists(p):
            try: os.remove(p)
            except: pass

def wiki_search(query):
    """Wikipedia API"""
    qs = urllib.request.quote(query)
    u = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch=" + qs + "&srlimit=5"
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=10)
        data = json.loads(r.read())
        pages = data.get("query", {}).get("search", [])
        for p in pages:
            title = p["title"]
            if any(kw in title.lower() for kw in ["disambiguation", "list of"]):
                continue
            u2 = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&titles=" + urllib.request.quote(title) + "&pithumbsize=1200"
            r2 = urllib.request.urlopen(urllib.request.Request(u2, headers=HEADERS), timeout=10)
            d2 = json.loads(r2.read())
            for pid, info in d2.get("query", {}).get("pages", {}).items():
                url = info.get("thumbnail", {}).get("source", "")
                if url:
                    return url, title
    except:
        pass
    return None, None

def commons_search(query):
    """Wikimedia Commons"""
    qs = urllib.request.quote(query)
    u = "https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srsearch=" + qs + "&srnamespace=6&srlimit=10"
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=10)
        data = json.loads(r.read())
        results = data.get("query", {}).get("search", [])
        if not results:
            return None, None

        titles = [item["title"] for item in results[:8]]
        u2 = "https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&titles=" + urllib.request.quote("|".join(titles)) + "&iiprop=url|size|mime&iiurlwidth=800"
        r2 = urllib.request.urlopen(urllib.request.Request(u2, headers=HEADERS), timeout=10)
        d2 = json.loads(r2.read())

        candidates = []
        for pid, info in d2.get("query", {}).get("pages", {}).items():
            ii = info.get("imageinfo", [{}])[0]
            url = ii.get("thumburl") or ii.get("url", "")
            mime = ii.get("mime", "")
            w, h = ii.get("width", 0), ii.get("height", 0)
            raw_title = info.get("title", "").lower()
            if any(kw in raw_title for kw in ["diagram", "map", "flag", "logo", "icon", "graph", "chart", "signature"]):
                continue
            if url and any(t in mime for t in ("jpeg", "png")) and w > 100 and h > 100:
                candidates.append((url, w, h))
        if candidates:
            candidates.sort(key=lambda x: x[1] * x[2], reverse=True)
            return candidates[0][0], "Commons"
    except:
        pass
    return None, None

def wikidata_search(name):
    """Wikidata — get image property"""
    qs = urllib.request.quote(name)
    u = "https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&search=" + qs + "&language=en&limit=3"
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=10)
        data = json.loads(r.read())
        for entity in data.get("search", []):
            qid = entity.get("id", "")
            u2 = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=" + qid + "&props=claims"
            r2 = urllib.request.urlopen(urllib.request.Request(u2, headers=HEADERS), timeout=10)
            d2 = json.loads(r2.read())
            claims = d2.get("entities", {}).get(qid, {}).get("claims", {})
            if "P18" in claims:
                fn = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
                url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.request.quote(fn.replace(" ", "_")) + "?width=800"
                return url, "Wikidata"
    except:
        pass
    return None, None

def download(name, url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30)
        img = Image.open(BytesIO(r.read())).convert("RGB")
        w, h = img.size
        if w < 120 or h < 120:
            return False
        path = img_path(name)
        img.save(path, "JPEG", quality=92)
        thumb = img.copy()
        thumb.thumbnail((200, 280), Image.LANCZOS)
        thumb.save(os.path.join(THUMB_DIR, safe_name(name) + ".jpg"), "JPEG", quality=75)
        return True
    except Exception as e:
        print("    download fail: " + str(e)[:60])
        return False

def main():
    with open(BAD_LIST, "r", encoding="utf-8") as f:
        names = [l.strip() for l in f if l.strip()]

    ok = fail = 0
    for i, name in enumerate(names, 1):
        print("[" + str(i) + "/" + str(len(names)) + "] " + name)
        delete_images(name)

        # Try multiple sources
        url = source = None
        # Get search overrides or generate generic queries
        queries = SEARCH_OVERRIDES.get(name, [name])

        for q in queries:
            url, source = wiki_search(q)
            if url: break
            url, source = commons_search(q)
            if url: break
            time.sleep(0.3)

        if not url:
            url, source = wikidata_search(name)

        if url:
            print("  " + str(source) + ": " + url[:80])
            if download(name, url):
                ok += 1
                print("  OK")
            else:
                fail += 1
                print("  FAIL (download)")
        else:
            fail += 1
            print("  NOT FOUND on any source")

        time.sleep(0.3)

    print("\nDone: " + str(ok) + " OK, " + str(fail) + " FAIL")

if __name__ == "__main__":
    main()
