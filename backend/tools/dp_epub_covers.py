# -*- coding: utf-8 -*-
"""
dp_epub_covers.py — epub 封面补全 + 无 detail 的 epub 建骨架 + 重建 covers.json
功能:
  1. 遍历 F:/philosophy 所有 .epub → bid = md5(rel_path)[:12] 映射
  2. books.json 中 file_type==epub 且无 detail 文件 → 建骨架 detail（内容后面补）
  3. detail 中 epub 无封面 → 从 epub 提取封面图（OPF cover-image → webp）
  4. 统一 detail.cover 为 /covers/ 静态路径
  5. 重建 app/public/covers.json（bid → /covers/xxx.webp）
"""
import sys, io, os, json, hashlib, zipfile, re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_book_json import save_as_webp

PHILO = r"F:/philosophy"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
DDIR = os.path.join(BASE, "data", "book_detail")
COVERS_DIR = os.path.join(BASE, "..", "app", "public", "covers")
COVERS_JSON = os.path.join(BASE, "..", "app", "public", "covers.json")
BOOKS_FILE = os.path.join(BASE, "..", "app", "public", "books.json")
os.makedirs(COVERS_DIR, exist_ok=True)


def bid_of(rel):
    return hashlib.md5(rel.encode("utf-8")).hexdigest()[:12]


def find_epubs():
    found = {}
    for root, dirs, files in os.walk(PHILO):
        dirs[:] = [d for d in dirs if d not in ("jpg", "new")]
        for fn in files:
            if fn.lower().endswith(".epub"):
                rel = os.path.relpath(os.path.join(root, fn), PHILO).replace("\\", "/")
                found[bid_of(rel)] = os.path.join(root, fn)
    return found


def extract_cover(epub_path):
    """从 epub 提取封面图片 bytes；失败返回 None"""
    try:
        with zipfile.ZipFile(epub_path) as z:
            names = z.namelist()
            opf = None
            if "META-INF/container.xml" in names:
                cx = z.read("META-INF/container.xml").decode("utf-8", "ignore")
                m = re.search(r'full-path="([^"]+)"', cx)
                if m:
                    opf = m.group(1)
            if not opf:
                opf = next((n for n in names if n.endswith(".opf")), None)
            if not opf:
                return None
            opf_xml = z.read(opf).decode("utf-8", "ignore")
            m = re.search(r'<meta\s+name="cover"\s+content="([^"]+)"', opf_xml)
            cover_id = m.group(1) if m else None
            target = None
            for m in re.finditer(r"<item\b[^>]*>", opf_xml):
                tag = m.group(0)
                mid = re.search(r'id="([^"]+)"', tag)
                href = re.search(r'href="([^"]+)"', tag)
                props = re.search(r'properties="([^"]*)"', tag)
                mtype = re.search(r'media-type="([^"]+)"', tag)
                if not (mid and href):
                    continue
                if cover_id and mid.group(1) == cover_id:
                    target = href.group(1)
                    break
                if props and "cover" in props.group(1):
                    target = href.group(1)
                    break
                if target is None and mtype and mtype.group(1) in ("image/jpeg", "image/png"):
                    target = href.group(1)
            if not target:
                return None
            img_path = os.path.normpath(os.path.join(os.path.dirname(opf), target)).replace("\\", "/")
            if img_path in names:
                return z.read(img_path)
            base = os.path.basename(target)
            hit = next((n for n in names if n.endswith(base)), None)
            if hit:
                return z.read(hit)
            return None
    except Exception as e:
        print(f"  extract error {epub_path}: {e}", flush=True)
        return None


def main():
    epubs = find_epubs()
    print(f"found {len(epubs)} epub files", flush=True)

    books = json.load(open(BOOKS_FILE, encoding="utf-8"))
    epub_books = [b for b in books if b.get("file_type") == "epub"]
    skeleton = 0
    for b in epub_books:
        bid = b["id"]
        dp = os.path.join(DDIR, f"{bid}.json")
        if not os.path.exists(dp):
            # 无 detail → 建骨架（内容后面补），尽量带封面
            x = {"bookId": bid, "title": b["title"], "author": b.get("author", ""),
                 "cover": None, "toc": [], "chapterCount": 0, "chapterTitles": [],
                 "region": b.get("region", ""), "file_type": "epub"}
            if bid in epubs:
                data = extract_cover(epubs[bid])
                if data:
                    save_as_webp(data, os.path.join(COVERS_DIR, f"{bid}_cover.webp"))
                    x["cover"] = f"/covers/{bid}_cover.webp"
            json.dump(x, open(dp, "w", encoding="utf-8"), ensure_ascii=False)
            skeleton += 1
            print(f"  + skeleton {b['title']}", flush=True)

    # 缺封面的 epub 补封面 + 统一路径
    fixed = 0
    for fn in os.listdir(DDIR):
        dp = os.path.join(DDIR, fn)
        x = json.load(open(dp, encoding="utf-8"))
        if x.get("file_type") != "epub":
            continue
        bid = x.get("bookId") or fn[:-5]
        cur = x.get("cover") or ""
        cur_file = os.path.join(COVERS_DIR, os.path.basename(cur)) if cur else ""
        if not cur or not os.path.exists(cur_file):
            if bid in epubs:
                data = extract_cover(epubs[bid])
                if data:
                    save_as_webp(data, os.path.join(COVERS_DIR, f"{bid}_cover.webp"))
                    x["cover"] = f"/covers/{bid}_cover.webp"
                    json.dump(x, open(dp, "w", encoding="utf-8"), ensure_ascii=False)
                    fixed += 1
                    print(f"  + cover {x['title']}", flush=True)
        elif not cur.startswith("/covers/"):
            x["cover"] = f"/covers/{os.path.basename(cur)}"
            json.dump(x, open(dp, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"skeletons: {skeleton}, covers fixed: {fixed}", flush=True)

    # 重建 covers.json（bid → /covers/xxx.webp）
    manifest = {}
    for fn in sorted(os.listdir(COVERS_DIR)):
        if fn.endswith(".webp"):
            manifest.setdefault(fn.split("_")[0], f"/covers/{fn}")
    json.dump(manifest, open(COVERS_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"covers.json: {len(manifest)} entries", flush=True)


if __name__ == "__main__":
    main()
