"""
重爬无人脸/缺图的哲学家 — 多源搜索
"""
import os, sys, json, re, time, requests
from io import BytesIO
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHILO_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")
HEADERS = {"User-Agent": "DeepPhilosophy/1.0 (research bot; philosophical image retrieval)"}

# ── 目标名单 ──
MODERN_NOFACE = [
    "加塔里", "哈茨霍恩", "哲罗姆", "埃马纽埃尔·列维纳斯",
    "奥尔特加·伊·加塞特", "杨献珍", "热奈特", "皮埃尔·阿多",
    "迈克尔·沃尔泽", "露西·伊利格瑞", "马克斯·霍克海默",
]
MISSING_IMAGES = ["司马穰苴", "尉缭", "慎到", "邓析", "邹奭", "邹衍", "黄枬森"]
ALL_TARGETS = MODERN_NOFACE + MISSING_IMAGES

# ── 多语言搜索词 ──
SEARCH_TERMS = {
    "加塔里":       ["Felix Guattari", "Pierre-Felix Guattari"],
    "哈茨霍恩":     ["Charles Hartshorne", "Charles Hartshorne philosopher"],
    "哲罗姆":       ["Jerome philosopher", "Saint Jerome", "Jerome of Stridon"],
    "埃马纽埃尔·列维纳斯": ["Emmanuel Levinas", "Emmanuel Levinas philosopher"],
    "奥尔特加·伊·加塞特": ["Jose Ortega y Gasset", "Ortega y Gasset philosopher"],
    "杨献珍":       ["Yang Xianzhen", "Yang Hsien-chen", "杨献珍", "Yang Xianzhen philosopher"],
    "热奈特":       ["Gerard Genette", "Genette narratology"],
    "皮埃尔·阿多":  ["Pierre Hadot", "Pierre Hadot philosopher"],
    "迈克尔·沃尔泽": ["Michael Walzer", "Michael Walzer philosopher"],
    "露西·伊利格瑞": ["Luce Irigaray", "Irigaray philosopher", "Luce Irigaray philosopher"],
    "马克斯·霍克海默": ["Max Horkheimer", "Horkheimer philosopher", "Max Horkheimer Frankfurt School"],
    "司马穰苴":     ["Sima Rangju", "Sima Rangju general", "司马穰苴"],
    "尉缭":         ["Wei Liao", "Wei Liaozi", "尉缭子"],
    "慎到":         ["Shen Dao philosopher", "Shen Dao Legalist", "慎到"],
    "邓析":         ["Deng Xi philosopher", "Deng Xi Chinese", "邓析"],
    "邹奭":         ["Zou Shi philosopher Yin Yang", "Zou Shi Chinese"],
    "邹衍":         ["Zou Yan philosopher", "Tsou Yen", "Zou Yan Yin Yang"],
    "黄枬森":       ["Huang Nansen", "Huang Nan-sen philosopher", "黄枬森", "黄楠森 哲学家"],
}

def safe_name(name):
    return name.replace("/", "-").replace("\\", "-").replace(":", "：")

def img_path(name):
    return os.path.join(PHILO_DIR, safe_name(name) + ".jpg")

def try_wikipedia(query):
    """Wikipedia search for page image"""
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": query, "srlimit": 3,
    }
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=10)
        pages = r.json().get("query", {}).get("search", [])
    except:
        return None
    for p in pages:
        ip = {"action": "query", "format": "json", "prop": "pageimages", "titles": p["title"], "pithumbsize": 800}
        try:
            r2 = requests.get("https://en.wikipedia.org/w/api.php", params=ip, headers=HEADERS, timeout=10)
            for pid, info in r2.json().get("query", {}).get("pages", {}).items():
                url = info.get("thumbnail", {}).get("source", "")
                if url: return url
        except:
            continue
    return None

def try_commons(query):
    """Wikimedia Commons search for portrait images"""
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": query,
        "srnamespace": 6, "srlimit": 5, "srsort": "relevance",
    }
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers=HEADERS, timeout=10)
        results = r.json().get("query", {}).get("search", [])
    except:
        return None

    titles = [item["title"] for item in results[:5]]
    if not titles:
        return None

    ip = {"action": "query", "format": "json", "prop": "imageinfo", "titles": "|".join(titles),
          "iiprop": "url|size|mime|canonicaltitle", "iiurlwidth": 800}
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php", params=ip, headers=HEADERS, timeout=10)
        pages = r.json().get("query", {}).get("pages", {})
    except:
        return None

    candidates = []
    for pid, info in pages.items():
        ii = info.get("imageinfo", [{}])[0]
        url = ii.get("thumburl") or ii.get("url", "")
        mime = ii.get("mime", "")
        w, h = ii.get("width", 0), ii.get("height", 0)
        title_lower = info.get("title", "").lower()
        # Skip diagrams, maps, flags, logos
        skip_words = ["diagram", "map", "flag", "logo", "icon", "coat of arms", "graph", "chart"]
        if any(w in title_lower for w in skip_words):
            continue
        if url and any(t in mime for t in ("jpeg", "png")) and w > 100 and h > 100:
            # Prefer portrait orientation
            score = h - w if h > w else 0
            candidates.append((url, score, w * h))
    if candidates:
        # Sort by portrait preference then size
        candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return candidates[0][0]
    return None

def try_wikidata(name):
    """Wikidata entity image"""
    # First search for the Wikidata entity
    params = {
        "action": "wbsearchentities", "format": "json",
        "search": name, "language": "en", "limit": 3,
    }
    try:
        r = requests.get("https://www.wikidata.org/w/api.php", params=params, headers=HEADERS, timeout=10)
        results = r.json().get("search", [])
    except:
        return None

    for entity in results:
        qid = entity.get("id", "")
        if not qid:
            continue
        # Get the image property (P18)
        ip = {"action": "wbgetentities", "format": "json", "ids": qid, "props": "claims", "languages": "en"}
        try:
            r = requests.get("https://www.wikidata.org/w/api.php", params=ip, headers=HEADERS, timeout=10)
            claims = r.json().get("entities", {}).get(qid, {}).get("claims", {})
            if "P18" in claims:
                filename = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
                # Build Commons URL
                encoded = filename.replace(" ", "_")
                md5 = encoded  # simplified — actually need MD5 of filename, use API instead
                url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width=800"
                return url
        except:
            continue
    return None

def download_and_save(url, name):
    """Download image and save"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        img = Image.open(BytesIO(r.content)).convert("RGB")
        out = img_path(name)
        img.save(out, "JPEG", quality=92)
        thumb = img.copy()
        thumb.thumbnail((200, 280), Image.LANCZOS)
        thumb_dir = os.path.join(PHILO_DIR, "thumb")
        os.makedirs(thumb_dir, exist_ok=True)
        thumb.save(os.path.join(thumb_dir, safe_name(name) + ".jpg"), "JPEG", quality=75)
        return True
    except Exception as e:
        print(f"    download error: {e}")
        return False

def main():
    total = len(ALL_TARGETS)
    ok, fail = 0, 0

    for i, name in enumerate(ALL_TARGETS, 1):
        path = img_path(name)
        print(f"\n[{i}/{total}] {name}")

        # Skip if already has a face-verified image
        if os.path.exists(path):
            # Check if it already has a face (quick re-check)
            import cv2, numpy
            try:
                pil_img = Image.open(path).convert("RGB")
                cv_img = cv2.cvtColor(numpy.array(pil_img), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                fc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = fc.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
                if len(faces) > 0:
                    print("  SKIP: already has face-detected image")
                    continue
                else:
                    print("  No face in current image, re-fetching...")
                    os.remove(path)  # Remove bad image
                    thumb_path = os.path.join(PHILO_DIR, "thumb", safe_name(name) + ".jpg")
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)
            except:
                pass

        # Try multiple search strategies
        queries = SEARCH_TERMS.get(name, [name])
        url = None
        source = ""

        for q in queries:
            # Strategy 1: Wikipedia
            url = try_wikipedia(q)
            if url:
                source = "Wikipedia: " + q
                break
            # Strategy 2: Commons
            url = try_commons(q)
            if url:
                source = "Commons: " + q
                break
            time.sleep(0.5)

        # Strategy 3: Wikidata (if still no image)
        if not url:
            url = try_wikidata(name)
            if url:
                source = "Wikidata"

        if url:
            print(f"  {source}")
            if download_and_save(url, name):
                ok += 1
                print(f"  OK")
            else:
                fail += 1
                print(f"  FAIL (download)")
        else:
            fail += 1
            print(f"  NO IMAGE FOUND on any platform")

        time.sleep(0.5)  # Be polite to APIs

    print(f"\n{'='*50}")
    print(f"Done: {ok} OK, {fail} FAIL ({total} total)")

if __name__ == "__main__":
    main()
