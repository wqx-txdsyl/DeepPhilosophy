#!/usr/bin/env python3
"""
AI 生成哲学家肖像 — 用于 Wikipedia 无画像的古代哲人
用法: python gen_portrait.py              # 批量生成所有缺图哲人
     python gen_portrait.py "慎到"        # 生成指定哲人
"""
import sys, os, json, requests, time
from PIL import Image
from io import BytesIO

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load API key — try api_keys.json first, then gen_school_bg.py fallback
API_KEY = ""
_keys_path = os.path.join(SCRIPT_DIR, "api_keys.json")
if os.path.exists(_keys_path):
    with open(_keys_path, "r", encoding="utf-8") as f:
        try:
            _keys = json.load(f)
            API_KEY = _keys.get("agnes", _keys.get("deepseek", ""))
        except:
            pass
if not API_KEY:
    # Fallback: extract from gen_school_bg.py
    import re
    _bg_path = os.path.join(SCRIPT_DIR, "gen_school_bg.py")
    if os.path.exists(_bg_path):
        with open(_bg_path, "r", encoding="utf-8") as f:
            m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
            if m: API_KEY = m.group(1)
IMG_API = "https://apihub.agnes-ai.com/v1/images/generations"
TEXT_API = "https://apihub.agnes-ai.com/v1/chat/completions"
TEXT_MODEL = "agnes-2.0-flash"
IMG_MODEL = "agnes-image-2.1-flash"

PHILO_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")
THUMB_DIR = os.path.join(PHILO_DIR, "thumb")
ROOT = os.path.dirname(SCRIPT_DIR)

os.makedirs(PHILO_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

# Load philosophers.json for context info
PHILOSOPHERS_DB = {}
_philo_path = os.path.join(ROOT, "backend", "data", "philosophers.json")
if os.path.exists(_philo_path):
    with open(_philo_path, "r", encoding="utf-8") as f:
        PHILOSOPHERS_DB = json.load(f)

# 已知缺图哲人的详细信息（优先于 philosophers.json 的简短描述）
KNOWN_MISSING = {
    "司马穰苴": {"era": "春秋", "school": "兵家", "desc": "春秋末期齐国军事家，著有《司马法》"},
    "尉缭": {"era": "战国", "school": "兵家", "desc": "战国末期军事家，著有《尉缭子》"},
    "慎到": {"era": "战国", "school": "法家", "desc": "战国法家思想家，强调'势'治天下"},
    "邓析": {"era": "春秋", "school": "名家", "desc": "春秋郑国大夫，中国最早的名家思想家"},
    "邹奭": {"era": "战国", "school": "阴阳家", "desc": "战国阴阳家学者，继承五德终始理论"},
    "邹衍": {"era": "战国", "school": "阴阳家", "desc": "战国阴阳家代表，创五德终始说和大九州说"},
    "相里氏之墨": {"era": "战国", "school": "墨家", "desc": "战国墨家学者，相里氏一派代表"},
}

STYLE_PROMPT = (
    "classical Chinese ink painting style, elegant scholarly portrait, "
    "historical figure, dignified expression, traditional Chinese attire, "
    "soft brushstrokes, rice paper texture, subtle ink wash, "
    "museum quality, ancient Chinese philosophy aesthetic, "
    "no modern elements, no text, no watermark"
)

def generate_prompt(philosopher, info):
    """为哲人生成图片 prompt"""
    if info:
        return (
            f"A dignified classical Chinese portrait of {philosopher}, "
            f"{info.get('era', 'ancient')} period {info.get('school', 'philosophy')} philosopher. "
            f"{info.get('desc', 'An influential thinker in Chinese philosophy')}. "
            f"{STYLE_PROMPT}"
        )
    else:
        # Generic prompt for unknown philosophers
        return (
            f"A dignified classical Chinese ink painting portrait of the philosopher {philosopher}, "
            f"scholarly appearance, traditional Chinese attire, elegant brushwork, "
            f"{STYLE_PROMPT}"
        )

def generate_image(prompt):
    """调用 Agnes Image API 生成图片"""
    r = requests.post(
        IMG_API,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": IMG_MODEL,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
        },
        timeout=60,
    )
    data = r.json()
    if "data" in data and len(data["data"]) > 0:
        # Response may have URL or base64
        img_data = data["data"][0]
        if "url" in img_data:
            resp = requests.get(img_data["url"], timeout=30)
            return Image.open(BytesIO(resp.content))
        elif "b64_json" in img_data:
            import base64
            return Image.open(BytesIO(base64.b64decode(img_data["b64_json"])))
    print(f"  API response: {json.dumps(data, ensure_ascii=False)[:300]}")
    return None

def save_portrait(name, img):
    """保存肖像 + 缩略图"""
    safe = name.replace("/", "-").replace(":", "：")
    path = os.path.join(PHILO_DIR, f"{safe}.jpg")
    img = img.convert("RGB")
    img.save(path, "JPEG", quality=92)
    print(f"  Saved: {safe}.jpg ({img.size[0]}x{img.size[1]})")

    # Thumbnail
    thumb = img.copy()
    thumb.thumbnail((200, 200), Image.LANCZOS)
    thumb_path = os.path.join(THUMB_DIR, f"{safe}.jpg")
    thumb.save(thumb_path, "JPEG", quality=75)

def get_philosopher_info(name):
    """Get philosopher context from known dict or philosophers.json"""
    if name in KNOWN_MISSING:
        return KNOWN_MISSING[name]
    if name in PHILOSOPHERS_DB:
        p = PHILOSOPHERS_DB[name]
        return {
            "era": p.get("era", ""),
            "school": p.get("school", ""),
            "desc": p.get("bio", "")[:100] if p.get("bio") else "",
        }
    return {}

def main():
    if len(sys.argv) > 1:
        names = [sys.argv[1]]
    else:
        # Batch: any philosopher missing image or with image < 20KB
        names = []
        for name in PHILOSOPHERS_DB:
            safe = name.replace("/", "-").replace(":", "：")
            path = os.path.join(PHILO_DIR, f"{safe}.jpg")
            if not os.path.exists(path) or os.path.getsize(path) < 20000:
                names.append(name)

    if not names:
        print("All philosophers have good images!")
        return

    print(f"Generating portraits for {len(names)} philosophers:\n")

    for i, name in enumerate(names, 1):
        info = get_philosopher_info(name)
        print(f"[{i}/{len(names)}] {name} ({info.get('era', '?')} {info.get('school', '?')})")

        prompt = generate_prompt(name, info)
        print(f"  Prompt: {prompt[:120]}...")

        try:
            img = generate_image(prompt)
            if img:
                save_portrait(name, img)
                print(f"  DONE")
            else:
                print(f"  FAILED - no image in response")
        except Exception as e:
            print(f"  ERROR: {e}")

        time.sleep(1.5)

    # Final count
    missing = sum(1 for n in PHILOSOPHERS_DB
                  if not os.path.exists(os.path.join(PHILO_DIR, n.replace("/", "-").replace(":", "：") + ".jpg")))
    print(f"\nRemaining without images: {missing}/{len(PHILOSOPHERS_DB)}")

if __name__ == "__main__":
    main()
