import os, re

PHILO = os.path.join(os.path.dirname(__file__), "..", "app", "public", "philosopher")
BAD_FILE = os.path.join(os.path.dirname(__file__), "_ai_bad_images.txt")

with open(BAD_FILE, "r", encoding="utf-8") as f:
    content = f.read()

names = set()
for line in content.split("\n"):
    m = re.search(r"\]\s+(\S+?)\.{3}", line)
    if m:
        names.add(m.group(1))

print("Bad images: " + str(len(names)))
deleted = 0
for name in names:
    safe = name.replace("/", "-").replace(":", chr(0xFF1A))
    for sub in ["", "thumb/"]:
        path = os.path.join(PHILO, sub, safe + ".jpg")
        if os.path.exists(path):
            os.remove(path)
            deleted += 1

for static_dir in ["backend/static/philosopher", "backend/app-dist/philosopher"]:
    sp = os.path.join(os.path.dirname(__file__), "..", static_dir)
    if os.path.isdir(sp):
        for name in names:
            safe = name.replace("/", "-").replace(":", chr(0xFF1A))
            for sub in ["", "thumb/"]:
                path = os.path.join(sp, sub, safe + ".jpg")
                if os.path.exists(path):
                    os.remove(path)

remaining = len([f for f in os.listdir(PHILO) if f.endswith(".jpg")])
print("Deleted: " + str(deleted) + " files")
print("Remaining: " + str(remaining))
