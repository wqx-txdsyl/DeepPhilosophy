#!/usr/bin/env python3
"""在 Render 服务器上运行：生成 EPUB JSON + 上传到 OSS
用法（在 Render Shell 中）:
  cd backend && python upload_book_json_to_oss.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from build_book_json import process_epub, add_pagination
import hashlib, hmac, base64, json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from dotenv import load_dotenv
load_dotenv()

import config
BOOKS_DIR = config.KNOWLEDGE_DIR  # /app/data/books on Render

ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com")
BUCKET = os.getenv("OSS_BUCKET", "deepphilosophy")
AK = os.getenv("OSS_ACCESS_KEY", "")
SK = os.getenv("OSS_SECRET_KEY", "")
FORCE = "--force" in sys.argv

if not AK or not SK:
    print("错误: 请设置 OSS_ACCESS_KEY 和 OSS_SECRET_KEY")
    sys.exit(1)

def oss_put(key_path, data):
    now = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    string_to_sign = f"PUT\n\napplication/json\n{now}\n/{BUCKET}/{key_path}"
    sig = base64.b64encode(hmac.new(SK.encode(), string_to_sign.encode(), hashlib.sha1).digest()).decode()
    url = f"https://{BUCKET}.{ENDPOINT}/{key_path}"
    req = Request(url, data=data, headers={
        'Date': now, 'Content-Type': 'application/json',
        'Authorization': f'OSS {AK}:{sig}',
    }, method='PUT')
    try: return urlopen(req, timeout=120).status
    except HTTPError as e: return e.code

def main():
    count = 0
    for root, dirs, files in os.walk(BOOKS_DIR):
        for f in files:
            if not f.lower().endswith('.epub'): continue
            filepath = os.path.join(root, f)
            rel = os.path.relpath(filepath, BOOKS_DIR).replace('\\', '/')
            book_id = hashlib.md5(rel.encode()).hexdigest()[:12]
            key = f"book_json/{book_id}.json"

            # 检查 OSS 是否已存在（除非 --force）
            if not FORCE:
                try:
                    url = f"https://{BUCKET}.{ENDPOINT}/{key}"
                    req = Request(url, method='HEAD')
                    if urlopen(req, timeout=10).status == 200:
                        continue  # 跳过
                except: pass

            print(f"[{count+1}] {f}...", end=' ', flush=True)
            book = process_epub(filepath)
            if not book:
                print("SKIP")
                continue
            book["bookId"] = book_id
            book["title"] = book.get("title") or os.path.splitext(f)[0]
            book["author"] = book.get("author") or ""
            book["sourcePath"] = rel
            book = add_pagination(book)
            data = json.dumps(book, ensure_ascii=False).encode('utf-8')
            status = oss_put(key, data)
            if status == 200:
                size_kb = len(data)/1024
                print(f"OK ({size_kb:.0f}KB)")
                count += 1
            else:
                print(f"FAIL {status}")
    print(f"\nDone: {count} uploaded → oss://{BUCKET}/book_json/")

if __name__ == '__main__':
    main()

