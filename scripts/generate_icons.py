#!/usr/bin/env python3
"""批量调用 Agnes Image API 生成 icon，保存到 ../icons/"""

import os, sys, json, time, io, base64
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def remove_white_bg(img_bytes: bytes) -> bytes:
    """用 PIL 把白色/近白色像素变透明，防止 API 不输出 alpha 通道"""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        data = img.getdata()
        new_data = []
        for r, g, b, a in data:
            # 浅色背景 → 透明（阈值 200，icon 线条是深色 ink 不受影响）
            if r > 180 and g > 180 and b > 180:
                new_data.append((r, g, b, 0))
            else:
                new_data.append((r, g, b, a))
        img.putdata(new_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return img_bytes  # PIL 未安装，原样保存

API_URL  = "https://apihub.agnes-ai.com/v1/images/generations"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import get_agnes_key
API_KEY = get_agnes_key()
if not API_KEY: raise SystemExit("错误: 未设置 AGNES_API_KEY 环境变量")
MODEL    = "agnes-image-2.1-flash"
OUT_DIR  = Path(__file__).parent.parent / "app" / "public" / "icons"
DELAY_S  = 0.8  # 请求间隔，避免限流

# ── 简洁 prompt（英文，图标生成效果好）─────────────────────
ICONS = {
    # 导航栏
    "nav-books":       "minimal line art icon of an open book, ink strokes, ancient manuscript style, monochrome, transparent background, no fill, 24x24 icon",
    "nav-authors":     "minimal line art icon of a quill pen, ink strokes, classical writing, monochrome, transparent background, no fill, 24x24 icon",
    "nav-genealogy":   "minimal line art icon of a branching tree diagram, ink strokes, genealogy, monochrome, transparent background, no fill, 24x24 icon",
    "nav-qa":          "minimal line art icon of a speech bubble, ink strokes, dialogue, monochrome, transparent background, no fill, 24x24 icon",
    "nav-games":       "minimal line art icon of an astrolabe compass, ink strokes, ancient instrument, monochrome, transparent background, no fill, 24x24 icon",
    # 主题
    "theme-light":     "minimal line art icon of a sun with rays, ink strokes, classical engraving, monochrome, transparent background, no fill, 24x24 icon",
    "theme-dark":      "minimal line art icon of a crescent moon, ink strokes, classical engraving, monochrome, transparent background, no fill, 24x24 icon",
    "mode-desktop":    "minimal line art icon of a laptop computer, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "mode-mobile":     "minimal line art icon of a smartphone, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    # 区域
    "region-east":     "minimal line art icon of a yin yang symbol, ink strokes, Taoist, monochrome, transparent background, no fill, 24x24 icon",
    "region-west":     "minimal line art icon of a Greek ionic column, ink strokes, classical, monochrome, transparent background, no fill, 24x24 icon",
    "region-world":    "minimal line art icon of a globe with meridians, antique map style, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "region-east-pagoda":"minimal line art icon of a pagoda silhouette, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    # 高频操作
    "icon-search":     "minimal line art icon of a magnifying glass, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-book-open":  "minimal line art icon of an open book with pages, ink strokes, classical tome, monochrome, transparent background, no fill, 24x24 icon",
    "icon-edit":       "minimal line art icon of a nib pen, ink strokes, calligraphy, monochrome, transparent background, no fill, 24x24 icon",
    "icon-close":      "minimal line art icon of an X mark, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-save":       "minimal line art icon of a bookmark ribbon, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-trash":      "minimal line art icon of a wastebasket, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-link":       "minimal line art icon of a paperclip, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-refresh":    "minimal line art icon of two arrows forming a circle, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-tip":        "minimal line art icon of a candle flame, ink strokes, monastic, monochrome, transparent background, no fill, 24x24 icon",
    "icon-error":      "minimal line art icon of a crossed circle, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-candle":     "minimal line art icon of a candle, ink strokes, monastic study, monochrome, transparent background, no fill, 24x24 icon",
    "icon-sparkles":   "minimal line art icon of three small diamond dots, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-cloud":      "minimal line art icon of a cloud, ink strokes, antique weather engraving, monochrome, transparent background, no fill, 24x24 icon",
    "icon-clipboard":  "minimal line art icon of a scroll with checklist, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-toc":        "minimal line art icon of stacked horizontal lines, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    # 游戏
    "icon-brain":      "minimal line art icon of a human head profile with brain, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-flame":      "minimal line art icon of a single flame torch, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-rocket":     "minimal line art icon of an arrow pointing upward, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-crazy":      "minimal line art icon of a comedy theatrical mask, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-thumbs-up":  "minimal line art icon of a thumbs up hand gesture, simple geometric outline, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-thumbs-down":"minimal line art icon of a thumbs down hand gesture, simple geometric outline, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-question":   "minimal line art icon of a question mark, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-neutral":    "minimal line art icon of a horizontal dash, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-perfect":    "minimal line art icon of a laurel wreath, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    # 用户/系统
    "btn-user":        "minimal line art icon of a Greek philosopher bust silhouette, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "btn-settings":    "minimal line art icon of a gear, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-lock":       "minimal line art icon of a padlock, ink strokes, antique lock, monochrome, transparent background, no fill, 24x24 icon",
    "icon-lock-key":   "minimal line art icon of an antique skeleton key, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-check":      "minimal line art icon of a checkmark, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-bot":        "minimal line art icon of an owl face, ink strokes, wisdom bird, monochrome, transparent background, no fill, 24x24 icon",
    "icon-sun":        "minimal line art icon of a small sun, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-drama":      "minimal line art icon of two theatrical masks, comedy tragedy, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    # PHTI 称号
    "icon-flashlight": "minimal line art icon of a flashlight, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-zombie":     "minimal line art icon of a sleepwalking person silhouette with arms forward, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-coaster":    "minimal line art icon of a roller coaster loop, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-hammer":     "minimal line art icon of a hammer, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-parachute":  "minimal line art icon of a parachute, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-calc":       "minimal line art icon of an abacus, ink strokes, ancient calculator, monochrome, transparent background, no fill, 24x24 icon",
    "icon-car":        "minimal line art icon of a chariot, ink strokes, ancient vehicle, monochrome, transparent background, no fill, 24x24 icon",
    "icon-slot":       "minimal line art icon of a dice, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-lion":       "minimal line art icon of a lion head, ink strokes, heraldic, monochrome, transparent background, no fill, 24x24 icon",
    "icon-bucket":     "minimal line art icon of a wooden bucket, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-cat":        "minimal line art icon of a cat silhouette, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-eye":        "minimal line art icon of an eye, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-leaf":       "minimal line art icon of a leaf, ink strokes, botanical engraving, monochrome, transparent background, no fill, 24x24 icon",
    "icon-zip-mouth":  "minimal line art icon of a face with zippered mouth, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-microscope": "minimal line art icon of a microscope, ink strokes, scientific, monochrome, transparent background, no fill, 24x24 icon",
    "icon-landmark":   "minimal line art icon of a Greek temple facade, ink strokes, landmark, monochrome, transparent background, no fill, 24x24 icon",
    "icon-ice":        "minimal line art icon of an ice cube, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-cog":        "minimal line art icon of a cogwheel, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-target":     "minimal line art icon of a target with arrow, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-mountain":   "minimal line art icon of a mountain peak, ink strokes, engraving, monochrome, transparent background, no fill, 24x24 icon",
    "icon-wine":       "minimal line art icon of a wine goblet, ink strokes, classical, monochrome, transparent background, no fill, 24x24 icon",
    "icon-handshake":  "minimal line art icon of two hands shaking, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-tent":       "minimal line art icon of a circus tent, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-rainbow":    "minimal line art icon of a rainbow arc, ink strokes, weather, monochrome, transparent background, no fill, 24x24 icon",
    "icon-party":      "minimal line art icon of confetti, ink strokes, celebration, monochrome, transparent background, no fill, 24x24 icon",
    "icon-moon-night": "minimal line art icon of a crescent moon with star, ink strokes, night, monochrome, transparent background, no fill, 24x24 icon",
    "icon-butterfly":  "minimal line art icon of a butterfly, ink strokes, nature engraving, monochrome, transparent background, no fill, 24x24 icon",
    "icon-calendar":   "minimal line art icon of a calendar page, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-pin":        "minimal line art icon of a map pin marker, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-writing":    "minimal line art icon of a hand writing with pen, ink strokes, calligraphy, monochrome, transparent background, no fill, 24x24 icon",
    "icon-thinking":   "minimal line art icon of a thinking bubble, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
    "icon-scroll":     "minimal line art icon of an unrolled scroll, ink strokes, antique, monochrome, transparent background, no fill, 24x24 icon",
    "icon-file-size":  "minimal line art icon of a document with weight scale, ink strokes, monochrome, transparent background, no fill, 24x24 icon",
}

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def generate_icon(key: str, prompt: str) -> bool:
    out_path = OUT_DIR / f"{key}.png"
    if out_path.exists():
        print(f"  SKIP {key} (exists)")
        return True

    body = {
        "model": MODEL,
        "prompt": prompt,
        "size": "1024x1024",
        "return_base64": True,
    }

    try:
        r = requests.post(API_URL, headers=HEADERS, json=body, timeout=180)
        if r.status_code != 200:
            print(f"  ✗ {key} HTTP {r.status_code}: {r.text[:200]}")
            return False

        data = r.json()
        item = data.get("data", [{}])[0]
        b64 = item.get("b64_json", "")
        if not b64:
            # fallback: try URL
            url = item.get("url", "")
            if url:
                r2 = requests.get(url, timeout=60)
                r2.raise_for_status()
                img = r2.content
            else:
                print(f"  ✗ {key} no b64_json or url in response")
                return False
        else:
            img = base64.b64decode(b64)
        img = remove_white_bg(img)  # 去白底 → 透明
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(img)
        print(f"  OK {key} saved ({len(img)} bytes)")
        return True

    except Exception as e:
        print(f"  FAIL {key} error: {e}")
        return False


def main():
    keys = list(ICONS.keys())
    # 只生成命令行指定的 key，不指定则全部
    if len(sys.argv) > 1:
        keys = [k for k in keys if k in sys.argv[1:]]
        if not keys:
            print("Usage: python generate_icons.py [key1 key2 ...]")
            return

    total = len(keys)
    ok = fail = 0
    print(f"Generating {total} icons → {OUT_DIR}")
    for i, key in enumerate(keys):
        print(f"[{i+1}/{total}] {key}", end=" ", flush=True)
        if generate_icon(key, ICONS[key]):
            ok += 1
        else:
            fail += 1
        time.sleep(DELAY_S)

    print(f"\nDone. {ok} ok, {fail} failed, {total - ok - fail} skipped")


if __name__ == "__main__":
    main()
