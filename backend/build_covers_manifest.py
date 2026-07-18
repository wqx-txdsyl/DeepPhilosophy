"""将封面图片复制到 public/covers/ 作为静态文件 + 生成 covers.json 清单

问题：封面图片通过 /api/books/{id}/image/{name} API 提供，无 CDN 缓存，每次都重新下载
解决：复制到 public/covers/ → 作为静态文件被 Vite/Nginx/CDN 直接服务 → 浏览器强缓存
"""
import os, json, shutil

BASE = os.path.dirname(__file__)
DETAIL_DIR = os.path.join(BASE, "..", "app", "public", "book_detail")
IMG_SRC_DIR = os.path.join(BASE, "data", "book_images")
COVERS_OUT_DIR = os.path.join(BASE, "..", "app", "public", "covers")
MANIFEST_OUT = os.path.join(BASE, "..", "app", "public", "covers.json")

os.makedirs(COVERS_OUT_DIR, exist_ok=True)

covers = {}
copied = 0
total = 0

for fn in sorted(os.listdir(DETAIL_DIR)):
    if not fn.endswith('.json'): continue
    total += 1
    try:
        with open(os.path.join(DETAIL_DIR, fn), 'r', encoding='utf-8') as f:
            d = json.load(f)
        bid = d.get('bookId', fn.replace('.json', ''))
        cover_url = d.get('cover')
        if not cover_url: continue
        # URL 格式: /api/books/{bid}/image/{img_name}.webp
        img_name = cover_url.rsplit('/', 1)[-1]  # 提取 xx.webp
        src = os.path.join(IMG_SRC_DIR, img_name)
        dst = os.path.join(COVERS_OUT_DIR, img_name)
        if os.path.exists(src):
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
                shutil.copy2(src, dst)
                copied += 1
            covers[bid] = f"/covers/{img_name}"
        else:
            # 源图不存在，保留原 API URL
            covers[bid] = cover_url
    except Exception as e:
        print(f"  skip {fn}: {e}")

with open(MANIFEST_OUT, 'w', encoding='utf-8') as f:
    json.dump(covers, f, ensure_ascii=False)

# 统计
covers_size = sum(os.path.getsize(os.path.join(COVERS_OUT_DIR, f))
                  for f in os.listdir(COVERS_OUT_DIR) if f.endswith('.webp'))
print(f"covers.json: {len(covers)}/{total} books have covers")
print(f"copied: {copied} images, total size: {covers_size/1024:.0f} KB")
print(f"static path: /covers/xxx.webp (browser caches natively)")
