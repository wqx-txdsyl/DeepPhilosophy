#!/usr/bin/env python3
"""
输入 emoji → 文字模型生成 prompt → 生图模型生成 icon → 去背景
用法: python gen_icon_from_emoji.py "🔥" [output_name]
"""
import sys, os, base64, json, time, io
import requests
from PIL import Image
from collections import deque

# ── API 配置 ──
API_KEY = "sk-tAli2tVgjAi5VG2zBG3oz4hUefyaqrD6UyjDaIpvhH6SKEAD"
TEXT_API = "https://apihub.agnes-ai.com/v1/chat/completions"
IMG_API  = "https://apihub.agnes-ai.com/v1/images/generations"
TEXT_MODEL = "agnes-2.0-flash"
IMG_MODEL  = "agnes-image-2.1-flash"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")

# ── 去背景 ──
def remove_bg(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    w, h = img.size
    pixels = img.load()
    q = deque()
    for sx, sy in [(0,0),(w-1,0),(0,h-1),(w-1,h-1),(w//2,0),(w//2,h-1),(0,h//2),(w-1,h//2)]:
        q.append((sx, sy))
    visited = set()
    while q:
        x, y = q.popleft()
        if (x,y) in visited or x<0 or x>=w or y<0 or y>=h: continue
        visited.add((x,y))
        r, g, b, a = pixels[x,y]
        if a > 0 and r+g+b > 300:
            pixels[x,y] = (r,g,b,0)
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]: q.append((x+dx, y+dy))
    # 二遍：封闭区域内的浅色也清掉
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x,y]
            if a > 0 and r+g+b > 350: pixels[x,y] = (r,g,b,0)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def gen(emoji, out_name=None):
    # ── Step 1: emoji → prompt ──
    print(f"[1/3] 分析 emoji: {emoji}")
    r = requests.post(TEXT_API, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"
    }, json={
        "model": TEXT_MODEL,
        "messages": [{"role": "user", "content": f'Describe what this emoji represents: {emoji}. Then write a one-line prompt (in English) for generating a minimal line-art icon (ink strokes, transparent background, monochrome, 24x24 style) of this concept. Output ONLY the prompt, nothing else.'}],
        "temperature": 0.3, "max_tokens": 200,
    }, timeout=60)
    prompt = r.json()["choices"][0]["message"]["content"].strip()
    print(f"  → Prompt: {prompt}")

    # ── Step 2: generate image ──
    print(f"[2/3] 生成 icon...")
    r = requests.post(IMG_API, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"
    }, json={
        "model": IMG_MODEL, "prompt": prompt + ", transparent background, no fill, simple line art",
        "size": "1024x1024", "return_base64": True,
    }, timeout=180)
    data = r.json()
    b64 = data["data"][0].get("b64_json", "")
    if not b64:
        url = data["data"][0].get("url", "")
        if url:
            r2 = requests.get(url, timeout=60)
            img_bytes = r2.content
        else:
            print("  ✗ No image in response")
            return
    else:
        img_bytes = base64.b64decode(b64)

    # ── Step 3: remove background ──
    print(f"[3/3] 去背景...")
    img_bytes = remove_bg(img_bytes)
    os.makedirs(OUT_DIR, exist_ok=True)
    name = out_name or f"icon-{emoji[0]}.png"
    out_path = os.path.join(OUT_DIR, name)
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    print(f"  ✓ Saved: {out_path} ({len(img_bytes)} bytes)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gen_icon_from_emoji.py '🔥' [output_name]")
        sys.exit(1)
    emoji = sys.argv[1]
    out_name = sys.argv[2] if len(sys.argv) > 2 else None
    gen(emoji, out_name)
