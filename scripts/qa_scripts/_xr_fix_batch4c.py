# -*- coding: utf-8 -*-
"""第四批补丁2（一次性）：沉思集 88b56fb4da52 文件错位/覆盖恢复
batch4 bug 链：dump 六沉思覆盖了原 8-12.json（答辩+4篇导论），rename 又把沉思移到 14-18。
恢复方案：
1. 当前 14-18.json（沉思2-6）→ 移回 8-12.json
2. 当前 19-21.json（《沉思集》分析/推理顺序/译后记）→ 移到 18-20.json，删 21.json
3. 从 DP git HEAD 恢复原 8-12.json（答辩+导论）→ 13-17.json（答辩标题更新）
4. toc 与文件断言一致，同步 PhiAgent + DP。"""
import json, subprocess, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/88b56fb4da52"
REPO = "f:/program/Python/DeepPhilosophy/DeepPhilosophy"

# 1. 断言当前 14-18 是沉思 2-6
expect = {14: "第二个沉思", 15: "第三个沉思", 16: "第四个沉思", 17: "第五个沉思", 18: "第六个沉思"}
for idx, prefix in expect.items():
    d = load(f"{SRC}/{idx}.json")
    assert d["title"].startswith(prefix), f"{idx}.json 应为 {prefix}, 实为 {d['title']}"
# 断言当前 19-21 是导论/译后记
assert load(f"{SRC}/19.json")["title"].startswith("《沉思集》中的分析")
assert load(f"{SRC}/20.json")["title"].startswith("推理顺序")
assert load(f"{SRC}/21.json")["title"].startswith("译后记")

# 2. 移回沉思：14-18 → 8-12（目标空位，无覆盖）
for src, dst in [(18, 12), (17, 11), (16, 10), (15, 9), (14, 8)]:
    os.rename(f"{SRC}/{src}.json", f"{SRC}/{dst}.json")
# 3. 导论后移：19-21 → 18-20（先移 19→18 腾出 19，再 20→19，最后 21→20）
for src, dst in [(19, 18), (20, 19), (21, 20)]:
    os.rename(f"{SRC}/{src}.json", f"{SRC}/{dst}.json")

# 4. 从 git HEAD 恢复原 8-12 → 13-17
def git_show(f, out):
    p = subprocess.run(["git", "show", f"HEAD:backend/data/book_chapters/88b56fb4da52/{f}"],
                       cwd=REPO, capture_output=True)
    assert p.returncode == 0, f"git show {f} 失败: {p.stderr[:200]}"
    open(out, "wb").write(p.stdout)

for src, dst in [(8, 13), (9, 14), (10, 15), (11, 16), (12, 17)]:
    git_show(f"{src}.json", f"{SRC}/{dst}.json")
# 答辩标题更新（新 toc 已改"对第二组反驳的答辩"）
d13 = load(f"{SRC}/13.json")
d13["title"] = "对第二组反驳的答辩（节录）"
dump(f"{SRC}/13.json", d13)

# 5. 校验文件 ↔ toc
m = load(f"{SRC}/meta.json")
files = sorted(int(f[:-5]) for f in os.listdir(SRC) if f[:-5].isdigit())
toc_idx = [t["index"] for t in m["toc"]]
print("文件:", files)
print("toc :", toc_idx)
assert files == toc_idx, "文件/索引不一致"
assert files == list(range(21)), "应为 0-20 连续 21 个"
for t in m["toc"]:
    d = load(f"{SRC}/{t['index']}.json")
    if t.get("index") != 13:
        assert d["title"] == t["title"], f"{t['index']} title 不一致: {d['title']} vs {t['title']}"
print("✓ 沉思集恢复完成: 21 章 0-20 连续, 六沉思+答辩+6导论+译后记")

# 6. 同步 DP
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/88b56fb4da52"
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")
