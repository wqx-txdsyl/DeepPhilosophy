# -*- coding: utf-8 -*-
"""第五批补丁2（一次性）：君主论 2e66606c2854 文件错位修复
batch5 缺陷：dump 1.json(译者序)/2.json(献辞) 覆盖了原第一/二章，
rename 又把译者序→3、献辞→4。修复：
1. 3.json(译者序) → 1.json，4.json(献辞) → 2.json
2. 从源 PDF 文本层提取第一章（页23起）、第二章（页24起）→ 3.json/4.json
3. 校验文件 ↔ toc，同步 PhiAgent + DP。"""
import fitz, json, re, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/2e66606c2854"
PDF = "F:/philosophy/西方/马基雅维利/君主论.pdf"

# 1. 译者序/献辞归位（先移 4→2，再 3→1，避免覆盖）
os.rename(f"{SRC}/4.json", f"{SRC}/2.json")
os.rename(f"{SRC}/3.json", f"{SRC}/1.json")
print("✓ 译者序→1.json, 献辞→2.json")

# 2. 从 PDF 提取第一章/第二章
doc = fitz.open(PDF)
def extract_until(start_pno, stop_marker):
    """从 start_pno 起收集文本，直到出现 stop_marker 标题行"""
    paras = []
    for pno in range(start_pno, len(doc)):
        t = doc[pno].get_text()
        if stop_marker and pno > start_pno and stop_marker in t:
            # 停在标题所在页（该页可能含标题+正文，从标题处截断）
            i = t.find(stop_marker)
            t = t[:i]
            paras.append(t)
            break
        paras.append(t)
    # 按空行拆段
    out = []
    for chunk in paras:
        for para in re.split(r"\n\s*\n", chunk):
            v = " ".join(para.split()).replace(" \u2013 ", " ").strip()
            if v:
                out.append({"type": "text", "value": v})
    return out

ch1 = extract_until(23, "第二章　世袭君主国")
# 第一章标题行在页首，删掉
v0 = ch1[0]["value"]
if "君主国有多少种类" in v0:
    i = v0.find("方法获得的")
    ch1[0]["value"] = v0[i + len("方法获得的"):]
ch2 = extract_until(24, "第三章　混合君主国")
if ch2 and "世袭君主国" in ch2[0]["value"]:
    i = ch2[0]["value"].find("这里，我想撇开共和国")
    ch2[0]["value"] = ch2[0]["value"][i:]

dump(f"{SRC}/3.json", {"title": "第一章　君主国有多少种类？是用什么方法获得的？", "content": [c for c in ch1 if c["value"]]})
dump(f"{SRC}/4.json", {"title": "第二章　世袭君主国", "content": [c for c in ch2 if c["value"]]})
print(f"✓ 第一章 {len([c for c in ch1 if c['value']])} 段, 第二章 {len([c for c in ch2 if c['value']])} 段")
print("  第一章首段:", ch1[0]["value"][:50])
print("  第二章首段:", ch2[0]["value"][:50])

# 3. 校验文件 ↔ toc
m = load(f"{SRC}/meta.json")
files = sorted(int(f[:-5]) for f in os.listdir(SRC) if re.fullmatch(r"\d+\.json", f))
toc_idx = [t["index"] for t in m["toc"]]
print("文件:", files)
print("toc :", toc_idx)
assert files == toc_idx and files == list(range(29)), "文件/索引不一致"
for t in m["toc"]:
    d = load(f"{SRC}/{t['index']}.json")
    if t["index"] not in (3, 4):
        assert d["title"] == t["title"], f"{t['index']} title 不一致: {d['title'][:16]} vs {t['title'][:16]}"
    assert d["content"], f"{t['index']} 空内容"
print("✓ 君主论恢复完成: 29 章 0-28 连续")

# 4. 同步 DP
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/2e66606c2854"
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")
