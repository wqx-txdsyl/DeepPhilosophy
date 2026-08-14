# -*- coding: utf-8 -*-
"""
dp_gen_txt_covers.py — txt 占位书生成文字封面（书名/作者排版图）
背景: txt 91 本是佚失占位（无实体文件, 无真实封面）——用文字封面补齐
  1. books.json 中 file_type==txt 且无 cover
  2. PIL 绘制 600x900: 区域色背景 + 书名（自动换行自适应字号）+ 作者 + 细边框
  3. 输出 app/public/covers/{bid}_cover.webp（covers.json 由 dp_epub_covers 统一重建）
字体: 微软雅黑（msyh.ttc）→ 黑体（simhei.ttf）→ 宋体（simsun.ttc）兜底
"""
import sys, io, os, json

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dp_gen_txt_covers.log")
def _log(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    try:
        sys.__stdout__.write(msg + "\n"); sys.__stdout__.flush()
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
BOOKS_FILE = os.path.join(BASE, "..", "app", "public", "books.json")
COVERS_DIR = os.path.join(BASE, "..", "app", "public", "covers")
os.makedirs(COVERS_DIR, exist_ok=True)

FONT_CANDIDATES = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
                   r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]
FONT = next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
REGION_COLOR = {"东方": (58, 47, 40), "西方": (38, 50, 74)}  # 暖棕 / 冷蓝灰


def wrap_text(draw, text, font, max_w):
    """按像素宽度换行"""
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def gen_cover(title, author, region, out_path):
    W, H = 600, 900
    img = Image.new("RGB", (W, H), REGION_COLOR.get(region, (50, 50, 50)))
    d = ImageDraw.Draw(img)
    # 细边框装饰
    d.rectangle([18, 18, W - 18, H - 18], outline=(200, 180, 140), width=2)
    # 书名: 字号按长度自适应, 自动换行
    max_w = W - 120
    for size in (64, 52, 44, 36, 30, 26, 22):
        font = ImageFont.truetype(FONT, size)
        lines = wrap_text(d, title, font, max_w)
        if len(lines) <= 5:
            break
    line_h = size + 14
    total_h = line_h * len(lines)
    y = (H - total_h) // 2 - 60
    for line in lines:
        tw = d.textlength(line, font=font)
        d.text(((W - tw) / 2, y), line, font=font, fill=(240, 238, 230))
        y += line_h
    # 作者
    if author:
        af = ImageFont.truetype(FONT, 30)
        tw = d.textlength(author, font=af)
        d.text(((W - tw) / 2, y + 10), author, font=af, fill=(170, 160, 145))
    # 底部标记
    bf = ImageFont.truetype(FONT, 20)
    d.text((W - 140, H - 55), "DEEPPHILOSOPHY", font=bf, fill=(120, 115, 105))
    img.save(out_path, "WEBP", quality=85)
    return out_path


def main():
    if not FONT:
        _log("!! 无可用中文字体")
        return
    books = json.load(open(BOOKS_FILE, encoding="utf-8"))
    todo = [b for b in books if b.get("file_type") == "txt" and not b.get("cover")]
    _log(f"txt 无封面: {len(todo)}")
    done, fail = 0, 0
    for b in todo:
        try:
            op = os.path.join(COVERS_DIR, f"{b['id']}_cover.webp")
            gen_cover(b["title"], b.get("author", ""), b.get("region", ""), op)
            _log(f"  ✓ {b['title']}")
            done += 1
        except Exception as e:
            _log(f"  ✗ {b['title']}: {e}")
            fail += 1
    _log(f"done: {done} ok, {fail} fail（covers.json 由 dp_epub_covers.py 重建）")


if __name__ == "__main__":
    main()
