#!/usr/bin/env python3
"""
人脸检测 + 自动重爬
用法: python check_faces.py          # 仅检测，输出报告
      python check_faces.py --fix    # 检测并自动重爬非人脸图片
"""
import sys, os, json, time, subprocess
import cv2
import numpy
import requests
from io import BytesIO
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHILO_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")
FETCH_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_philosopher_img.py")
HEADERS = {"User-Agent": "DeepPhilosophy/1.0 (philosophical image research)"}

# 加载 OpenCV 预训练的 Haar 级联分类器
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
PROFILE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

def has_face(image_path):
    """检测图片是否包含人脸（正脸或侧脸）"""
    # Use PIL to read (handles Unicode paths on Windows), convert to OpenCV format
    try:
        pil_img = Image.open(image_path).convert("RGB")
        img = cv2.cvtColor(numpy.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        return False, f"无法读取: {e}"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 多尺度检测 + 不同参数组合
    faces_frontal = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    faces_profile = PROFILE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    total = len(faces_frontal) + len(faces_profile)
    if total > 0:
        return True, f"人脸×{total} (正{len(faces_frontal)}+侧{len(faces_profile)})"
    else:
        # 放宽参数再试一次（模糊/远景人脸）
        faces_loose = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40))
        if len(faces_loose) > 0:
            return True, f"人脸×{len(faces_loose)} (宽松)"
        return False, "未检测到人脸"

def refetch_with_portrait_search(name):
    """用更精确的肖像搜索重新爬取"""
    safe = name.replace("/", "-").replace("\\", "-").replace(":", "：")
    out_path = os.path.join(PHILO_DIR, f"{safe}.jpg")

    # 先删掉旧文件
    for f in [out_path, os.path.join(PHILO_DIR, "thumb", f"{safe}.jpg")]:
        if os.path.exists(f):
            os.remove(f)

    # 尝试多种搜索策略
    strategies = [
        # 策略1: Wikipedia 英文 + portrait
        lambda: _search_wiki_portrait(name),
        # 策略2: Wikimedia Commons 精确肖像搜索
        lambda: _search_commons_portrait(name),
        # 策略3: 原始脚本（中文 Wikipedia）
        lambda: _run_fetch_script(name),
    ]

    for i, strategy in enumerate(strategies):
        try:
            url = strategy()
            if url:
                return _download(url, name)
        except Exception as e:
            continue

    return None

def _search_wiki_portrait(name):
    """Wikipedia 英文站 + 'portrait' 搜索"""
    print(f"    策略1: Wikipedia EN '{name} portrait'...")
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": f"{name} portrait", "srlimit": 3,
    }
    r = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=15)
    pages = r.json().get("query", {}).get("search", [])

    for p in pages:
        img_params = {
            "action": "query", "format": "json",
            "prop": "pageimages", "titles": p["title"],
            "pithumbsize": 800, "pilimit": 1,
        }
        r = requests.get("https://en.wikipedia.org/w/api.php", params=img_params, headers=HEADERS, timeout=15)
        for pid, info in r.json().get("query", {}).get("pages", {}).items():
            url = info.get("thumbnail", {}).get("source", "")
            if url:
                return url
    return None

def _search_commons_portrait(name):
    """Commons 精确肖像搜索"""
    print(f"    策略2: Commons '{name} portrait photograph'...")
    params = {
        "action": "query", "format": "json",
        "list": "search", "srsearch": f'"{name}" portrait',
        "srnamespace": 6, "srlimit": 5,
    }
    r = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers=HEADERS, timeout=15)
    results = r.json().get("query", {}).get("search", [])

    candidates = []
    for item in results:
        img_params = {
            "action": "query", "format": "json",
            "prop": "imageinfo", "titles": item["title"],
            "iiprop": "url|size|mime", "iiurlwidth": 800,
        }
        r = requests.get("https://commons.wikimedia.org/w/api.php", params=img_params, headers=HEADERS, timeout=15)
        for pid, info in r.json().get("query", {}).get("pages", {}).items():
            ii = info.get("imageinfo", [{}])[0]
            url = ii.get("thumburl") or ii.get("url", "")
            w = ii.get("width", 0)
            h = ii.get("height", 0)
            # 偏好竖版肖像
            if url and h > w and h > 200:
                candidates.append((url, h))

    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    return None

def _run_fetch_script(name):
    """回退到原始脚本"""
    print(f"    策略3: 原始 fetch_philosopher_img.py...")
    result = subprocess.run(
        [sys.executable, FETCH_SCRIPT, name],
        cwd=SCRIPT_DIR, timeout=120,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    safe = name.replace("/", "-").replace("\\", "-").replace(":", "：")
    out = os.path.join(PHILO_DIR, f"{safe}.jpg")
    return out if os.path.exists(out) else None

def _download(url, name):
    """下载并保存"""
    safe = name.replace("/", "-").replace("\\", "-").replace(":", "：")
    out = os.path.join(PHILO_DIR, f"{safe}.jpg")
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        img = Image.open(BytesIO(r.content)).convert("RGB")
        img.save(out, "JPEG", quality=92)
        thumb = img.copy()
        thumb.thumbnail((200, 280), Image.LANCZOS)
        os.makedirs(os.path.join(PHILO_DIR, "thumb"), exist_ok=True)
        thumb.save(os.path.join(PHILO_DIR, "thumb", f"{safe}.jpg"), "JPEG", quality=75)
        return out
    except Exception as e:
        print(f"    下载失败: {e}")
        return None

def main():
    fix_mode = "--fix" in sys.argv

    jpgs = sorted([f for f in os.listdir(PHILO_DIR) if f.endswith('.jpg')])
    total = len(jpgs)
    ok, bad = 0, 0
    bad_list = []

    print(f"{'='*60}")
    print(f"人脸检测: {total} 张图片  {'(自动修复模式)' if fix_mode else '(仅检测)'}")
    print(f"{'='*60}\n")

    for i, f in enumerate(jpgs, 1):
        name = f.replace('.jpg', '')
        path = os.path.join(PHILO_DIR, f)
        face_ok, detail = has_face(path)

        if face_ok:
            ok += 1
            if i % 20 == 0:
                print(f"  [{i}/{total}] OK {name} ({detail})  |  通过:{ok} 失败:{bad}")
        else:
            bad += 1
            bad_list.append(name)
            print(f"  [{i}/{total}] NOFACE {name} - {detail}")

            if fix_mode:
                print(f"    → 重爬...")
                result = refetch_with_portrait_search(name)
                if result and has_face(result)[0]:
                    print(f"    -> FIXED")
                    bad -= 1
                    ok += 1
                    bad_list.remove(name)
                else:
                    print(f"    -> STILL NO FACE, keeping original")
                time.sleep(1)

    print(f"\n{'='*60}")
    print(f"结果: {ok} 张有人脸, {bad} 张无人脸 ({total} 总计)")
    if bad_list:
        print(f"\n无人脸列表 ({len(bad_list)}):")
        for n in bad_list:
            print(f"  - {n}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
