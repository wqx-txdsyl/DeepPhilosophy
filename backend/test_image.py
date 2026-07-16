import sys, os, hashlib, traceback, zipfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from build_book_json import is_image, save_as_webp, EXTRACTED_IMG_DIR

filepath = r"F:\philosophy\西方\阿尔贝·加缪\西西弗神话.epub"
rel = os.path.relpath(filepath, r"F:\philosophy").replace("\\", "/")
book_id = hashlib.md5(rel.encode()).hexdigest()[:12]

os.makedirs(EXTRACTED_IMG_DIR, exist_ok=True)
images = {}
count = 0
with zipfile.ZipFile(filepath) as z:
    for name in z.namelist():
        if is_image(name) and '__MACOSX' not in name:
            try:
                data = z.read(name)
                fn = Path(name).name
                img_hash = hashlib.md5(data).hexdigest()[:10]
                out_fn = f"{book_id}_{img_hash}.webp"
                out_path = os.path.join(EXTRACTED_IMG_DIR, out_fn)
                if not os.path.exists(out_path):
                    save_as_webp(data, out_path)
                images[fn] = f"/api/books/{book_id}/image/{out_fn}"
                count += 1
            except Exception:
                traceback.print_exc()
print(f"Images: {count}")
