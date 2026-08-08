# -*- coding: utf-8 -*-
"""第四批补丁2b（一次性）：沉思集恢复（接 batch4c 断点）
batch4c 第2步已把沉思2-6 移回 8-12；本脚本继续：
1. 19-21.json（《沉思集》分析/推理顺序/译后记）→ 18-20.json
2. 从 DP git HEAD 恢复原 8-12.json（答辩+4篇导论）→ 13-17.json
3. toc 与文件断言一致，同步 PhiAgent + DP。"""
import json, subprocess, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/88b56fb4da52"
REPO = "f:/program/Python/DeepPhilosophy/DeepPhilosophy"

# 1. 断言当前状态（batch4c 第2步后）
assert load(f"{SRC}/8.json")["title"].startswith("第二个沉思")
assert load(f"{SRC}/12.json")["title"].startswith("第六个沉思")
assert not os.path.exists(f"{SRC}/18.json"), "18.json 应为空位"

# 2. 导论后移：19-21 → 18-20（先移 19 腾位，逐级让位）
for src, dst in [(19, 18), (20, 19), (21, 20)]:
    os.rename(f"{SRC}/{src}.json", f"{SRC}/{dst}.json")
print("✓ 导论后移: 19-21 → 18-20")

# 3. 从 git HEAD 恢复原 8-12 → 13-17
def git_show(f, out):
    p = subprocess.run(["git", "show", f"HEAD:backend/data/book_chapters/88b56fb4da52/{f}"],
                       cwd=REPO, capture_output=True)
    assert p.returncode == 0, f"git show {f} 失败: {p.stderr[:200]}"
    open(out, "wb").write(p.stdout)

for src, dst in [(8, 13), (9, 14), (10, 15), (11, 16), (12, 17)]:
    git_show(f"{src}.json", f"{SRC}/{dst}.json")
d13 = load(f"{SRC}/13.json")
d13["title"] = "对第二组反驳的答辩（节录）"
dump(f"{SRC}/13.json", d13)
print("✓ 从 git HEAD 恢复 13-17（答辩+4篇导论）")

# 4. 校验文件 ↔ toc
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
print("✓ 沉思集恢复完成: 21 章 0-20 连续")

# 5. 同步 DP
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/88b56fb4da52"
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")
