"""
最终图片质量审查 — 检测问题并分类
"""
import os, cv2, numpy, json
from PIL import Image

PD = os.path.join(os.path.dirname(__file__), "..", "app", "public", "philosopher")
fc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
pc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")

jpgs = sorted([f for f in os.listdir(PD) if f.endswith(".jpg")])

# Categories
tiny = []       # < 20KB — likely bad download
many_faces = [] # > 5 faces — group photo or false positive
no_face = []    # 0 faces — statue/painting or bad image
small_img = []  # < 200px either dimension
good = []

for f in jpgs:
    name = f.replace(".jpg", "")
    path = os.path.join(PD, f)
    size_kb = os.path.getsize(path) // 1024
    try:
        pil = Image.open(path).convert("RGB")
        w, h = pil.size
        img = cv2.cvtColor(numpy.array(pil), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ff = fc.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        fp = pc.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        fl = fc.detectMultiScale(gray, 1.05, 3, minSize=(40, 40))
        face_n = max(len(ff) + len(fp), len(fl))

        issues = []
        if size_kb < 20:
            issues.append("TINY_" + str(size_kb) + "KB")
            tiny.append((name, w, h, size_kb, face_n))
        if w < 200 or h < 200:
            issues.append("SMALL_" + str(w) + "x" + str(h))
            small_img.append((name, w, h, size_kb, face_n))
        if face_n > 5:
            issues.append("MANY_FACES_" + str(face_n))
            many_faces.append((name, w, h, size_kb, face_n))
        if face_n == 0:
            no_face.append((name, w, h, size_kb))
        if not issues:
            good.append(name)
    except Exception as e:
        tiny.append((name, 0, 0, size_kb, 0))

# Write report
report = os.path.join(os.path.dirname(__file__), "_image_audit_report.txt")
with open(report, "w", encoding="utf-8") as f:
    f.write("=== IMAGE AUDIT REPORT ===\n")
    f.write("Total: " + str(len(jpgs)) + "\n")
    f.write("Good: " + str(len(good)) + "\n\n")

    f.write("=== TINY (< 20KB, likely bad download) === " + str(len(tiny)) + "\n")
    for n, w, h, kb, fc_n in sorted(tiny):
        f.write("  " + n + "  " + str(w) + "x" + str(h) + "  " + str(kb) + "KB  faces:" + str(fc_n) + "\n")

    f.write("\n=== SMALL IMAGE (< 200px) === " + str(len(small_img)) + "\n")
    for n, w, h, kb, fc_n in sorted(small_img):
        f.write("  " + n + "  " + str(w) + "x" + str(h) + "  " + str(kb) + "KB  faces:" + str(fc_n) + "\n")

    f.write("\n=== MANY FACES (> 5, possible group photo) === " + str(len(many_faces)) + "\n")
    for n, w, h, kb, fc_n in sorted(many_faces):
        f.write("  " + n + "  " + str(w) + "x" + str(h) + "  " + str(kb) + "KB  faces:" + str(fc_n) + "\n")

    f.write("\n=== NO FACE === " + str(len(no_face)) + "\n")
    for n, w, h, kb in sorted(no_face):
        f.write("  " + n + "  " + str(w) + "x" + str(h) + "  " + str(kb) + "KB\n")

print("Report saved to " + report)
print("Good: " + str(len(good)) + ", Tiny: " + str(len(tiny)) + ", Small: " + str(len(small_img)))
print("ManyFaces: " + str(len(many_faces)) + ", NoFace: " + str(len(no_face)))
