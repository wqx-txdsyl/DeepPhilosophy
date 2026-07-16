#!/usr/bin/env python3
"""本地生成JSON→OSS上传"""
import os, sys, hashlib, hmac, base64, json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from dotenv import load_dotenv; load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))
from build_book_json import process_epub, add_pagination

BOOKS_DIR = "F:/philosophy"
EP = os.getenv("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com")
BK = os.getenv("OSS_BUCKET", "deepphilosophy")
AK = os.getenv("OSS_ACCESS_KEY", "")
SK = os.getenv("OSS_SECRET_KEY", "")

def oss_put(key, data):
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    s = f"PUT\n\napplication/json\n{now}\n/{BK}/{key}"
    sig = base64.b64encode(hmac.new(SK.encode(), s.encode(), hashlib.sha1).digest()).decode()
    req = Request(f"https://{BK}.{EP}/{key}", data=data,
        headers={"Date":now,"Content-Type":"application/json","Authorization":f"OSS {AK}:{sig}"}, method="PUT")
    try: return urlopen(req, timeout=300).status
    except HTTPError as e: return e.code

count = 0
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in sorted(files):
        if not f.lower().endswith(".epub"): continue
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, BOOKS_DIR).replace("\\", "/")
        bid = hashlib.md5(rel.encode()).hexdigest()[:12]
        key = f"book_json/{bid}.json"
        try:
            if urlopen(Request(f"https://{BK}.{EP}/{key}", method="HEAD"), timeout=10).status == 200:
                continue
        except: pass
        print(f"[{count+1}] {f[:50]}...", end=" ", flush=True)
        book = process_epub(fp)
        if not book: print("SKIP"); continue
        book["bookId"] = bid
        book["title"] = book.get("title") or os.path.splitext(f)[0]
        book["author"] = book.get("author") or ""
        book["sourcePath"] = rel
        book = add_pagination(book)
        data = json.dumps(book, ensure_ascii=False).encode("utf-8")
        s = oss_put(key, data)
        if s == 200: print(f"OK {len(data)//1024}KB"); count += 1
        else: print(f"FAIL {s}")
print(f"Done: {count} uploaded")
