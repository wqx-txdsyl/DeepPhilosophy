"""
AI 识图验证 — 检查哲人头像是否与本人匹配
使用 Agnes 2.0 Flash 视觉模型
"""
import os, sys, json, requests, time

AGNES_KEY = "sk-tAli2tVgjAi5VG2zBG3oz4hUefyaqrD6UyjDaIpvhH6SKEAD"
AGNES_API = "https://apihub.agnes-ai.com/v1/chat/completions"
BASE_URL = "https://deepphilosophy-7g7m.onrender.com/philosopher"

PHILO_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "public", "philosopher")
LIST_FILE = os.path.join(os.path.dirname(__file__), "_batch_philosophers_full.txt")

def ask_agnes(name, image_filename):
    """Ask Agnes if this image is a portrait of the philosopher"""
    url = BASE_URL + "/" + requests.utils.quote(image_filename)
    prompt = "Look at this image and answer exactly ONE word: YES if this appears to be a portrait, photograph, statue, painting, or artistic depiction of the philosopher \"" + name + "\". Answer NO if it is clearly a DIFFERENT person, a landscape, a building, text, a diagram, a group photo where the philosopher cannot be identified, or any other non-portrait image. Then add a brief reason after YES/NO."

    try:
        r = requests.post(AGNES_API,
            headers={"Authorization": "Bearer " + AGNES_KEY, "Content-Type": "application/json"},
            json={
                "model": "agnes-2.0-flash",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": url}}
                    ]
                }],
                "temperature": 0.1, "max_tokens": 100
            },
            timeout=30)
        result = r.json()["choices"][0]["message"]["content"].strip()
        return result
    except Exception as e:
        return "ERROR: " + str(e)[:80]

def main():
    # Get list
    if not os.path.exists(LIST_FILE):
        print("No philosopher list found!")
        return

    with open(LIST_FILE, "r", encoding="utf-8") as f:
        names = [l.strip() for l in f if l.strip()]

    jpgs = set(f for f in os.listdir(PHILO_DIR) if f.endswith(".jpg"))

    bad = []
    ok = 0
    total = 0

    # First pass: check all images
    for name in names:
        safe = name.replace("/", "-").replace(":", "：") + ".jpg"
        if safe not in jpgs:
            continue

        total += 1
        print("[" + str(total) + "] " + name + "...", end=" ", flush=True)
        result = ask_agnes(name, safe)

        if result.upper().startswith("YES"):
            ok += 1
            print("YES")
        elif result.upper().startswith("NO"):
            bad.append((name, result))
            print("NO — " + result)
        else:
            bad.append((name, result))
            print("? " + result[:60])

        time.sleep(0.3)  # Rate limit

    print("\n" + "=" * 50)
    print("Verified: " + str(total))
    print("OK: " + str(ok))
    print("BAD: " + str(len(bad)))

    if bad:
        report = os.path.join(os.path.dirname(__file__), "_ai_bad_images.txt")
        with open(report, "w", encoding="utf-8") as f:
            f.write("=== AI-VERIFIED BAD IMAGES ===\n\n")
            for name, reason in bad:
                f.write(name + "\n")
                f.write("  " + reason + "\n\n")
        print("\nBad list saved to " + report)
        print("\nRun: python _refetch_noface.py  # to re-fetch these")
        for name, reason in bad:
            print("  " + name + " — " + reason[:80])

if __name__ == "__main__":
    main()
