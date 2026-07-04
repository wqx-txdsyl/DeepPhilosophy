import os

LIST = os.path.join(os.path.dirname(__file__), "_batch_philosophers_full.txt")
IMG  = os.path.join(os.path.dirname(__file__), "..", "app", "public", "philosopher")

with open(LIST, "r", encoding="utf-8") as f:
    names = [l.strip() for l in f if l.strip()]

missing = []
for n in names:
    safe = n.replace("/", "-").replace("\\", "-").replace(":", "：")
    path = os.path.join(IMG, safe + ".jpg")
    if not os.path.exists(path):
        missing.append(n)

print("Total: " + str(len(names)))
print("Missing: " + str(len(missing)))
for n in missing:
    print("  " + n)

# Save to file
out = os.path.join(os.path.dirname(__file__), "_missing_images.txt")
with open(out, "w", encoding="utf-8") as f:
    for n in missing:
        f.write(n + "\n")
print("\nSaved to " + out)
