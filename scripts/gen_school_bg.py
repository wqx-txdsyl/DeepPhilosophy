#!/usr/bin/env python3
"""
流派背景图生成器 — 学习现有风格后自动生成
用法: python gen_school_bg.py "萨满哲学" [参考图路径]
"""
import sys, os, base64, json, requests

API_KEY = "sk-tAli2tVgjAi5VG2zBG3oz4hUefyaqrD6UyjDaIpvhH6SKEAD"
TEXT_API = "https://apihub.agnes-ai.com/v1/chat/completions"
IMG_API  = "https://apihub.agnes-ai.com/v1/images/generations"
TEXT_MODEL = "agnes-2.0-flash"
IMG_MODEL  = "agnes-image-2.1-flash"

# 已分析的现有风格（缓存，避免重复调用）
STYLE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "school_style_cache.json")

def load_style_cache():
    try:
        with open(STYLE_CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_style_cache(cache):
    with open(STYLE_CACHE_FILE, "w") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def analyze_style(image_urls):
    """用 AI 分析现有流派背景图的风格特征"""
    cache = load_style_cache()
    if "style_prompt" in cache:
        print(f"  ✓ 使用缓存的风格描述")
        return cache["style_prompt"]

    print(f"  分析 {len(image_urls)} 张参考图...")
    messages = [{"role": "user", "content": [
        {"type": "text", "text": "You are analyzing a set of philosophy school background images from a digital museum website. Describe the COMMON artistic style across these images in detail: color palette (warm/cool, dominant colors), texture (paper, parchment, canvas), lighting (soft, dramatic, natural), composition (hero image, architectural, symbolic), mood (ancient, elegant, timeless, museum-quality). Write a concise style description (3-4 sentences) that could be used as a prompt prefix for generating more images in this exact same style. Focus on visual style, not content."},
    ]}]
    for url in image_urls[:3]:  # 最多分析3张
        messages[0]["content"].append({"type": "image_url", "image_url": {"url": url}})

    r = requests.post(TEXT_API, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"
    }, json={"model": TEXT_MODEL, "messages": messages, "temperature": 0.3, "max_tokens": 500}, timeout=120)
    style = r.json()["choices"][0]["message"]["content"].strip()
    cache["style_prompt"] = style
    save_style_cache(cache)
    print(f"  → Style: {style[:100]}...")
    return style

def gen_bg(school_name, style_prefix, description=None):
    """生成流派背景图"""
    print(f"[1/2] 生成 prompt...")
    desc = description or f"A digital museum hero background image for the philosophy school '{school_name}'"
    prompt = f"{style_prefix}. {desc}. High quality, museum exhibition style, elegant composition."

    r = requests.post(TEXT_API, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"
    }, json={"model": TEXT_MODEL, "messages": [
        {"role": "user", "content": f"Write a one-paragraph visual description for a museum-hero background image about the philosophy school: {school_name}. Include: symbolic imagery, color suggestions from the existing style, composition ideas. Output ONLY the description, in English, 2-3 sentences."}
    ], "temperature": 0.5, "max_tokens": 300}, timeout=60)
    visual_desc = r.json()["choices"][0]["message"]["content"].strip()
    final_prompt = f"{style_prefix}. {visual_desc}"
    print(f"  → Prompt: {final_prompt[:150]}...")

    print(f"[2/2] 生成图片...")
    r = requests.post(IMG_API, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"
    }, json={
        "model": IMG_MODEL, "prompt": final_prompt,
        "size": "1024x768", "extra_body": {"response_format": "url"},
    }, timeout=180)
    data = r.json()
    url = data["data"][0].get("url", "")
    if not url:
        print("  ✗ No image URL in response")
        return None
    print(f"  ✓ Generated: {url}")

    # 下载保存
    img_data = requests.get(url, timeout=60).content
    out_dir = os.path.join(os.path.dirname(__file__), "..", "app", "public", "schools")
    os.makedirs(out_dir, exist_ok=True)
    safe_name = school_name.replace("/", "-").replace("\\", "-")
    out_path = os.path.join(out_dir, f"{safe_name}.jpg")
    with open(out_path, "wb") as f:
        f.write(img_data)
    print(f"  ✓ Saved: {out_path} ({len(img_data)} bytes)")
    return out_path

def main():
    if len(sys.argv) < 2:
        print("用法: python gen_school_bg.py '流派名' [图片URL1] [图片URL2] ...")
        print("示例: python gen_school_bg.py '萨满哲学'")
        print("      python gen_school_bg.py '萨满哲学' https://.../schools/caucasus.jpg")
        sys.exit(1)

    school_name = sys.argv[1]
    ref_urls = sys.argv[2:] if len(sys.argv) > 2 else [
        "https://deepphilosophy-7g7m.onrender.com/schools/caucasus.jpg",
        "https://deepphilosophy-7g7m.onrender.com/schools/shaman.jpg",
    ]

    print(f"生成流派背景图: {school_name}")
    style = analyze_style(ref_urls)
    result = gen_bg(school_name, style)
    if result:
        print(f"\n完成! 背景图: {result}")
        print(f"需手动运行 build 脚本内联到 SchoolDetailPage")

if __name__ == "__main__":
    main()
