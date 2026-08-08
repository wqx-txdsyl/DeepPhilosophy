# -*- coding: utf-8 -*-
import sys, os, json, hashlib, datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOOLS = r"f:/program/Python/PhiAgent/backend/tools"
BASE = os.path.dirname(TOOLS)
CH = os.path.join(BASE, "data", "book_chapters")
CKPT = json.load(open(os.path.join(BASE, "data", "dp_pdf_import_ckpt.json"), encoding="utf-8"))
A2_DEFAULT = ("00fadd7de47c 0ed8c0c49e2f 1085686cbd33 17c85f942c78 17fda3378628 "
              "21d51965ccbb 221f09d04944 2321fab7e032 2cbf90eb6f69 2e66606c2854 "
              "302d32b2975c 309de54e4392 324c13db486e 343df8697039 3e85310c7179 "
              "4be7b72cf01d 536c2b9338e5 53d1b4ff90d2 60eed962806b 64056c6623ee "
              "6bcbc6a5904f 7729ccdecb0f 8ae083851bd8 a04933b82f3c a26240ee8f45 "
              "a3e1832a509d a44cb4c8f8d9 a6d6def88c3b a9955bc4ee64 aa21ac425e87 "
              "aa614e2cf92d aacc867ec43c ad61ed0fd976 add6c213fde8 b43aeb7ccc57 "
              "bbac1be0bb4b bcc83fdfca5e bedc9c78dfdf c13b139d1db3 d0c5ade4fcbd "
              "d54046539e0d d54981640212 d8bcc10d42ff dd03ec6572e7 e3a52553c303 "
              "e574c8e7f515 ef76ae88994f f08c1ead3164 f11f1b13c278 f9549bd811f6").split()
books = CKPT.get("books") or {}
rel_by_bid = {}
for k in books:
    rel_by_bid[hashlib.md5(k.encode()).hexdigest()[:12]] = k
today = datetime.date.today().isoformat()
print(f"{'bid':12s} {'章节':>4s} {'修改日期':10s} 标题")
for bid in A2_DEFAULT:
    mfp = os.path.join(CH, bid, "meta.json")
    if not os.path.exists(mfp):
        print(f"{bid}  无 meta")
        continue
    meta = json.load(open(mfp, encoding="utf-8"))
    mt = datetime.date.fromtimestamp(os.path.getmtime(mfp)).isoformat()
    rel = rel_by_bid.get(bid, "?")
    flag = "" if mt == today else "  ←旧"
    print(f"{bid} {meta.get('chapterCount',0):>4d} {mt} {meta.get('title','?')[:20]}{flag}  {rel[:60]}")
