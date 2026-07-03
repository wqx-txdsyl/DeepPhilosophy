#!/usr/bin/env python3
"""
流派背景图生成器 — 两阶段：预训练风格 → 按需生成
阶段1: python gen_school_bg.py --train       # 喂所有背景图，总结风格
阶段2: python gen_school_bg.py "萨满哲学"     # 输入流派名，自动生成
"""
import sys, os, json, requests, base64, glob, io
from PIL import Image

API_KEY = "sk-tAli2tVgjAi5VG2zBG3oz4hUefyaqrD6UyjDaIpvhH6SKEAD"
TEXT_API = "https://apihub.agnes-ai.com/v1/chat/completions"
IMG_API  = "https://apihub.agnes-ai.com/v1/images/generations"
TEXT_MODEL = "agnes-2.0-flash"
IMG_MODEL  = "agnes-image-2.1-flash"

STYLE_FILE = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "school_style_master.json")
SCHOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "public", "schools")

def load_master_style():
    try:
        with open(STYLE_FILE, "r") as f: return json.load(f)
    except: return None

def save_master_style(data):
    with open(STYLE_FILE, "w") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_school_images(limit=15):
    """获取所有流派背景图 URL"""
    base = "https://deepphilosophy-7g7m.onrender.com/schools"
    images = []
    for f in sorted(os.listdir(SCHOOLS_DIR)):
        if f.endswith(('.jpg', '.png')) and 'school_' not in f and 'thumb' not in f:
            images.append(f"{base}/{f}")
    return images[:limit]

def train():
    """预训练：喂所有背景图给 AI，输出 master style prompt"""
    images = get_school_images(15)
    if not images:
        print("没有找到学校背景图，使用缓存 URL")
        images = [
            f"https://deepphilosophy-7g7m.onrender.com/schools/{n}.jpg"
            for n in ['caucasus.jpg','shaman.jpg','arctic.jpg','austronesian.jpg','pacific.jpg']
        ]

    print(f"预训练：分析 {len(images)} 张背景图...")
    content = [{"type": "text", "text": """You are analyzing background images from a digital museum of philosophy. Study ALL these images together and identify the COMMON visual style.

Output a JSON object with:
- "style_master": A 3-4 sentence master style prompt describing the SHARED visual DNA across all images: color palette warmth/temperature range, texture type (paper/parchment/canvas), lighting quality, composition approach (hero image/symbolic/architectural), mood (ancient/elegant/timeless/museum). This will be used as a PREFIX for ALL generated images.
- "color_palette": Dominant colors observed (e.g. "warm ochre, bone white, deep ink")
- "texture": The surface feel (e.g. "aged parchment with subtle grain")
- "lighting": Light quality (e.g. "soft diffused natural light, chiaroscuro edges")
- "composition": Layout approach (e.g. "central symbolic element, atmospheric background, negative space for text overlay")

Output ONLY the JSON object, no other text."""}]
    for url in images:
        content.append({"type": "image_url", "image_url": {"url": url}})

    r = requests.post(TEXT_API, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": TEXT_MODEL, "messages": [{"role": "user", "content": content}], "temperature": 0.2, "max_tokens": 800}, timeout=180)
    result = r.json()["choices"][0]["message"]["content"].strip()
    # Extract JSON
    import re
    m = re.search(r'\{.*\}', result, re.DOTALL)
    if m:
        style_data = json.loads(m.group())
    else:
        style_data = {"style_master": result, "color_palette": "", "texture": "", "lighting": "", "composition": ""}
    save_master_style(style_data)
    print(f"✓ 风格已保存到 {STYLE_FILE}")
    print(f"  Master: {style_data.get('style_master','')[:120]}...")
    return style_data

def generate(school_name):
    """使用预训练风格生成指定流派的背景图"""
    style = load_master_style()
    if not style:
        print("未找到预训练风格，先运行 --train")
        return

    master = style.get("style_master", "")
    print(f"[1/3] 为「{school_name}」生成内容 prompt...")
    # 文字AI生成该流派的细节描述
    r = requests.post(TEXT_API, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": TEXT_MODEL, "messages": [
            {"role": "user", "content": f"""You are a museum curator designing a hero background image for the philosophy school "{school_name}".
Based on what you know about this school's historical period, geographic origin, key symbols, and philosophical themes, write a 2-3 sentence visual prompt describing what should appear in the image.
Include: key symbolic elements, appropriate architecture or landscape, era-appropriate visual cues, and mood.
Output ONLY the prompt, no other text."""}
        ], "temperature": 0.5, "max_tokens": 300}, timeout=60)
    content_prompt = r.json()["choices"][0]["message"]["content"].strip()
    print(f"  → {content_prompt[:120]}...")

    # 合并 master style + content prompt
    final_prompt = f"{master} {content_prompt}"
    print(f"[2/3] 生成图片...")
    r = requests.post(IMG_API, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": IMG_MODEL, "prompt": final_prompt, "size": "1024x768", "extra_body": {"response_format": "url"}}, timeout=180)
    url = r.json()["data"][0].get("url", "")
    if not url:
        print("✗ 无图片返回")
        return
    print(f"  ✓ {url}")

    # 下载保存
    print(f"[3/3] 保存...")
    img_data = requests.get(url, timeout=60).content
    safe = school_name.replace("/", "-").replace("\\", "-")
    out = os.path.join(SCHOOLS_DIR, f"{safe}.jpg")
    with open(out, "wb") as f: f.write(img_data)
    print(f"✓ {out} ({len(img_data)} bytes)")

    # 生成缩略图
    thumb_dir = os.path.join(SCHOOLS_DIR, "thumb")
    os.makedirs(thumb_dir, exist_ok=True)
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    img.thumbnail((200, 280), Image.LANCZOS)
    img.save(os.path.join(thumb_dir, f"{safe}.jpg"), "JPEG", quality=75)
    print(f"✓ 缩略图已生成")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python gen_school_bg.py --train          # 预训练风格")
        print("  python gen_school_bg.py '流派名'          # 生成背景图")
        sys.exit(1)
    if sys.argv[1] == "--train":
        train()
    else:
        school = sys.argv[1]
        generate(school)
