#!/usr/bin/env python3
"""
流派背景图生成器 — 两阶段：预训练风格 → 按需生成
阶段1: python gen_school_bg.py --train       # 喂所有背景图，总结风格
阶段2: python gen_school_bg.py "萨满哲学"     # 输入流派名，自动生成
"""
import sys, os, json, requests, base64, glob, io
from PIL import Image
from _lib import get_agnes_key

API_KEY = get_agnes_key()
if not API_KEY:
    raise SystemExit("错误: 未设置 AGNES_API_KEY 环境变量。请编辑 backend/.env 或设置环境变量后重试。")
TEXT_API = "https://apihub.agnes-ai.com/v1/chat/completions"
IMG_API  = "https://apihub.agnes-ai.com/v1/images/generations"
TEXT_MODEL = "agnes-2.0-flash"
IMG_MODEL  = "agnes-image-2.1-flash"

_script_dir = os.path.dirname(os.path.abspath(__file__))
STYLE_FILE = os.path.join(_script_dir, "..", "backend", "data", "school_style_master.json")
SCHOOLS_DIR = os.path.join(_script_dir, "..", "app", "public", "schools")

def load_master_style():
    try:
        with open(STYLE_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return None

def save_master_style(data):
    with open(STYLE_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_school_images():
    """获取所有流派背景图 URL"""
    base = "https://deepphilosophy-7g7m.onrender.com/schools"
    images = []
    for f in sorted(os.listdir(SCHOOLS_DIR)):
        if f.endswith(('.jpg', '.png')) and 'school_' not in f and 'thumb' not in f:
            images.append(f"{base}/{f}")
    return images  # 全部，不限制数量

def train():
    """预训练：喂所有背景图给 AI，输出 master style prompt"""
    images = get_school_images()
    if not images:
        print("没有找到学校背景图，使用缓存 URL")
        images = [
            f"https://deepphilosophy-7g7m.onrender.com/schools/{n}.jpg"
            for n in ['caucasus.jpg','shaman.jpg','arctic.jpg','austronesian.jpg','pacific.jpg']
        ]

    print(f"预训练：分析 {len(images)} 张背景图...")
    content = [{"type": "text", "text": """You are analyzing background images from a digital museum of philosophy. These cover schools from 3000 BCE to 21st century — ancient, medieval, modern, and contemporary. Study ALL images and identify the COMMON museum-quality visual DNA.

CRITICAL: The master style must be FLEXIBLE enough to work for ALL eras — not just classical/antiquity. Modern schools should look modern, ancient schools should look ancient. Describe the SHARED qualities (museum curation, elegant composition, scholarly mood, high production value) WITHOUT locking into a single era.

Output a JSON object with:
- "style_master": A 3-4 sentence master style prompt. Focus on MUSEUM QUALITY traits that transcend eras: balanced composition, atmospheric depth, scholarly elegance, curated visual hierarchy, warm-but-adaptable palette. Do NOT mention specific eras like "classical" or "oil painting". This is a PREFIX for generating all school images.
- "color_palette": Dominant colors (e.g. "adaptable warm-cool spectrum")
- "texture": Surface feel (e.g. "refined museum print quality")
- "lighting": Light quality (e.g. "dramatic yet natural, era-flexible")
- "composition": Layout (e.g. "hero focal point with atmospheric depth")

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
    print(f"[OK] 风格已保存到 {STYLE_FILE}")
    print(f"  Master: {style_data.get('style_master','')[:120]}...")
    return style_data

def generate(school_name):
    """使用预训练风格生成指定流派的背景图"""
    style = load_master_style()
    if not style:
        print("未找到预训练风格，先运行 --train")
        return

    master = style.get("style_master", "")
    # 读取流派的 overview 作为上下文
    school_json = os.path.join(os.path.dirname(__file__), "..", "backend", "data", f"school_{school_name}.json")
    context = ""
    if os.path.exists(school_json):
        with open(school_json, "r", encoding="utf-8") as f:
            d = json.load(f)
            context = d.get("overview", "")[:500]

    # 提取年代信息
    timeline = d.get("timeline", []) if 'd' in dir() else []
    era_hint = ""
    if timeline:
        years = [e.get("year","") for e in timeline[:3]]
        era_hint = f"Historical period: {', '.join(years)}. "

    print(f"[1/3] 为「{school_name}」生成内容 prompt...")
    r = requests.post(TEXT_API, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": TEXT_MODEL, "messages": [
            {"role": "user", "content": f"""为哲学流派"{school_name}"的网页背景图写一段英文视觉prompt（2-3句）。

{era_hint}
流派简介：{context}

要求：
1. 必须体现该流派最独特的视觉符号、核心场景和哲学气质
2. 允许出现该流派时代的建筑、服饰、器物、自然景观
3. 如果流派特征与通用风格冲突（如现代流派不应出现古典建筑），以流派特征为准
4. 描述具体生动，避免空泛的形容词堆砌
5. 与该流派的思想内核形成视觉隐喻

Output ONLY the prompt, no other text."""}
        ], "temperature": 0.5, "max_tokens": 300}, timeout=60)
    content_prompt = r.json()["choices"][0]["message"]["content"].strip()
    print(f"  → {content_prompt[:120]}...")

    # 合并 master style + content prompt
    final_prompt = f"{master} {content_prompt}"
    print(f"[2/3] 生成图片...")
    r = requests.post(IMG_API, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": IMG_MODEL, "prompt": final_prompt, "size": "1280x720", "extra_body": {"response_format": "url"}}, timeout=180)
    url = r.json()["data"][0].get("url", "")
    if not url:
        print("[FAIL] 无图片返回")
        return
    print(f"  [OK] {url}")

    # 下载保存（使用 ASCII 文件名，避免 Render 404）
    IMG_MAP = {'萨满哲学':'shaman','北极原住民哲学':'arctic','南岛哲学':'austronesian','高加索哲学':'caucasus','高加索-草原哲学':'caucasus-steppe','太平洋原住民哲学':'pacific'}
    safe = IMG_MAP.get(school_name) or school_name.replace("/", "-").replace("\\", "-")
    print(f"[3/3] 保存为 {safe}.jpg...")
    img_data = requests.get(url, timeout=60).content
    out = os.path.join(SCHOOLS_DIR, f"{safe}.jpg")
    with open(out, "wb") as f: f.write(img_data)
    print(f"[OK] {out} ({len(img_data)} bytes)")

    # 生成缩略图
    thumb_dir = os.path.join(SCHOOLS_DIR, "thumb")
    os.makedirs(thumb_dir, exist_ok=True)
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    img.thumbnail((200, 280), Image.LANCZOS)
    img.save(os.path.join(thumb_dir, f"{safe}.jpg"), "JPEG", quality=75)
    print(f"[OK] 缩略图已生成")

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
