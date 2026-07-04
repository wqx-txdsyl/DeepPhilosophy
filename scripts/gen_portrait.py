#!/usr/bin/env python3
"""
AI 生成哲学家肖像 — 用于 Wikipedia 无画像的古代哲人
用法: python gen_portrait.py              # 批量生成所有缺图哲人
     python gen_portrait.py "慎到"        # 生成指定哲人
"""
import sys, os, json, requests, time
from PIL import Image
from io import BytesIO

# Load API key from api_keys.json
_keys_path = os.path.join(SCRIPT_DIR, "api_keys.json")
API_KEY = ""
if os.path.exists(_keys_path):
    with open(_keys_path, "r", encoding="utf-8") as f:
        _keys = json.load(f)
    API_KEY = _keys.get("agnes", _keys.get("deepseek", ""))
IMG_API = "https://apihub.agnes-ai.com/v1/images/generations"
TEXT_API = "https://apihub.agnes-ai.com/v1/chat/completions"
TEXT_MODEL = "agnes-2.0-flash"
IMG_MODEL = "agnes-image-2.1-flash"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHILO_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")
THUMB_DIR = os.path.join(PHILO_DIR, "thumb")

os.makedirs(PHILO_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

# 缺图哲人及其时代/流派信息
MISSING_PHILOSOPHERS = {
    "司马穰苴": {"era": "春秋", "school": "兵家", "desc": "春秋末期齐国军事家，著有《司马法》，被誉为'兵家之祖'之一"},
    "尉缭": {"era": "战国", "school": "兵家", "desc": "战国末期军事家，著有《尉缭子》，主张以法治军"},
    "慎到": {"era": "战国", "school": "法家", "desc": "战国时期法家思想家，强调'势'的重要性，认为君主应以势治天下"},
    "邓析": {"era": "春秋", "school": "名家", "desc": "春秋末期郑国大夫，中国最早的名家思想家，擅长辩论和刑名之学"},
    "邹奭": {"era": "战国", "school": "阴阳家", "desc": "战国末期阴阳家学者，邹衍的后学，继承发展了五德终始理论"},
    "邹衍": {"era": "战国", "school": "阴阳家", "desc": "战国末期阴阳家代表人物，创立五德终始说和大九州说，影响深远"},
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
    return (
        f"A dignified classical Chinese portrait of {philosopher}, "
        f"{info['era']} period {info['school']} philosopher. "
        f"{info['desc']}. "
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

def main():
    if len(sys.argv) > 1:
        names = [sys.argv[1]]
    else:
        # Only generate for those missing images
        names = []
        for n in MISSING_PHILOSOPHERS:
            safe = n.replace("/", "-").replace(":", "：")
            if not os.path.exists(os.path.join(PHILO_DIR, f"{safe}.jpg")):
                names.append(n)

    if not names:
        print("All philosophers already have images!")
        return

    print(f"Generating portraits for {len(names)} philosophers:\n")

    for i, name in enumerate(names, 1):
        info = MISSING_PHILOSOPHERS.get(name, {})
        print(f"[{i}/{len(names)}] {name} ({info.get('era', '')} {info.get('school', '')})")

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

        time.sleep(1.5)  # Rate limit

    # Final count
    remaining = 0
    for name in MISSING_PHILOSOPHERS:
        safe = name.replace("/", "-").replace(":", "：")
        if not os.path.exists(os.path.join(PHILO_DIR, f"{safe}.jpg")):
            remaining += 1
    print(f"\nRemaining without images: {remaining}")

if __name__ == "__main__":
    main()
