"""泛洪清理所有 icon 的背景"""
from PIL import Image
import glob, os
from collections import deque

ICON_DIR = os.path.join(os.path.dirname(__file__), '..', 'icons')

def flood_clean(img):
    """从边缘种子泛洪填充，去除连通的浅色背景"""
    w, h = img.size
    pixels = img.load()
    visited = set()
    q = deque()
    seeds = [(0,0),(w-1,0),(0,h-1),(w-1,h-1),
             (w//2,0),(w//2,h-1),(0,h//2),(w-1,h//2)]
    for sx, sy in seeds:
        q.append((sx, sy))
    while q:
        x, y = q.popleft()
        if (x,y) in visited or x < 0 or x >= w or y < 0 or y >= h:
            continue
        visited.add((x,y))
        r, g, b, a = pixels[x,y]
        if a > 0 and r + g + b > 300:
            pixels[x,y] = (r, g, b, 0)
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                q.append((x+dx, y+dy))
    return img

for f in sorted(glob.glob(os.path.join(ICON_DIR, '*.png'))):
    img = Image.open(f).convert('RGBA')
    before = sum(1 for r,g,b,a in img.getdata() if a > 0)
    img = flood_clean(img)
    # 第二遍：泛洪被深色线条挡住的光色区域（阈值 r+g+b > 350）
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 0 and r + g + b > 350:
                pixels[x, y] = (r, g, b, 0)
    after = sum(1 for r,g,b,a in img.getdata() if a > 0)
    img.save(f, 'PNG')
    name = os.path.basename(f)
    print(f'{name:35s} removed={before-after:6d}px  corner_alpha={img.getpixel((3,3))[3]}')
