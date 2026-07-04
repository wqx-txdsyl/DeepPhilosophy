import urllib.request, json, os
from PIL import Image
from io import BytesIO

HD = {"User-Agent": "DP/1.0"}
PD = "app/public/philosopher"
TD = os.path.join(PD, "thumb")
os.makedirs(TD, exist_ok=True)

targets = {
    "露西·伊利格瑞": ["Luce Irigaray", "Irigaray feminist philosopher"],
    "马克斯·霍克海默": ["Max Horkheimer", "Horkheimer Frankfurt School philosopher"],
}

for name, queries in targets.items():
    safe = name.replace("/", "-").replace(":", "：")
    out = os.path.join(PD, safe + ".jpg")
    if os.path.exists(out):
        # check if already OK
        try:
            import cv2, numpy
            pil = Image.open(out).convert("RGB")
            cvimg = cv2.cvtColor(numpy.array(pil), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cvimg, cv2.COLOR_BGR2GRAY)
            fc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            if len(fc.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))) > 0:
                print(name + ": already has face, skip")
                continue
        except:
            pass

    for q in queries:
        print(name + ": " + q)
        try:
            qs = urllib.request.quote(q)
            u = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch=" + qs + "&srlimit=3"
            r = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=10)
            pages = json.loads(r.read()).get("query", {}).get("search", [])

            for p in pages:
                u2 = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&titles=" + urllib.request.quote(p["title"]) + "&pithumbsize=800"
                r2 = urllib.request.urlopen(urllib.request.Request(u2, headers=HD), timeout=10)
                for pid, info in json.loads(r2.read()).get("query", {}).get("pages", {}).items():
                    url = info.get("thumbnail", {}).get("source", "")
                    if url:
                        img_r = urllib.request.urlopen(urllib.request.Request(url, headers=HD), timeout=30)
                        img = Image.open(BytesIO(img_r.read())).convert("RGB")
                        img.save(out, "JPEG", quality=92)
                        t = img.copy()
                        t.thumbnail((200, 280), Image.LANCZOS)
                        t.save(os.path.join(TD, safe + ".jpg"), "JPEG", quality=75)
                        print("  OK: " + str(img.size))
                        raise Exception("found")
        except Exception as e:
            if str(e) == "found":
                break
            print("  err: " + str(e)[:60])
            continue
    else:
        print("  STILL MISSING")

print("done")
