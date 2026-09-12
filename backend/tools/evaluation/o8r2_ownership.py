# -*- coding: utf-8 -*-
"""O8-R2 §9: Interaction / Orphan Ownership Audit（evaluation-only, 静态只读）。

对 6 个 pre-existing untracked 孤儿文件逐个判定:
REFERENCED / RUNTIME_OWNER / BUILD_IMPACT / KEEP|DEPRECATE|DELETE 建议 + RATIONALE。
不删除、不提交这些文件。
产出 backend/tools/_tmp/o8r2_ownership.json。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
# 孤儿文件本体只存在于主工作树（untracked 不入 git; reviewed checkout 无此文件）
MAIN = "/Users/sen/DeepPhilosophy"

ORPHANS = [
    "backend/jwt_verify.py",
    "backend/upstream.py",
    "backend/user_profile_store.py",
    "backend/routes/agent_history.py",
    "backend/routes/auth_proxy.py",
    "agent-app/src/data/conversationSync.js",
]

# 引用检测范围: 生产代码目录（排除自身/测试临时/工具/证据文档）
SCAN_DIRS = ["backend", "agent-app/src", "app/src", "workers"]
SKIP_PARTS = {"_tmp", "node_modules", "__pycache__", "dist", ".zcode"}


def iter_files():
    for d in SCAN_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in SKIP_PARTS]
            for f in filenames:
                if f.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".vue",
                               ".json", ".toml", ".sql", ".md")):
                    yield os.path.join(dirpath, f)


def referenced_by(stem, self_path):
    """在代码面检索模块名/文件名引用（排除孤儿文件自身之间的互相引用）。"""
    pats = [re.compile(rf"[\'\"]{re.escape(stem)}[\'\"]"),
            re.compile(rf"import\s+{re.escape(stem)}\b"),
            re.compile(rf"from\s+[.\w]*{re.escape(stem)}\s+import")]
    hits = []
    for fp in iter_files():
        if os.path.basename(fp) == "o8r2_ownership.py":
            continue  # 审计脚本自身不计引用
        if os.path.samefile(fp, self_path) if os.path.exists(fp) and os.path.exists(self_path) else False:
            continue
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for p in pats:
            m = p.search(txt)
            if m:
                hits.append({"file": os.path.relpath(fp, ROOT),
                             "snippet": txt[max(0, m.start() - 40):m.end() + 60]
                             .replace("\n", " ")[:120]})
                break
    return hits


def group_members(path):
    """后端孤儿路由/模块是一组互相引用的半成品——组内引用不算外部引用。"""
    return {os.path.relpath(os.path.join(ROOT, p), ROOT) for p in ORPHANS}


def audit_one(rel):
    full = os.path.join(MAIN, rel)
    info = {"path": rel, "exists": os.path.exists(full)}
    if not info["exists"]:
        info.update({"REFERENCED": False, "RUNTIME_OWNER": None,
                     "BUILD_IMPACT": None, "VERDICT": "REPORT",
                     "RATIONALE": "文件在主工作树不存在（可能已被用户移走）"})
        return info
    stem = os.path.splitext(os.path.basename(rel))[0]
    size = os.path.getsize(full)
    head = open(full, encoding="utf-8", errors="ignore").read(1500)
    hits = referenced_by(stem, full)
    group = group_members(rel)
    ext_hits = [h for h in hits
                if not any(h["file"].startswith(g.rsplit("/", 1)[0]) and
                           os.path.basename(g) in ("", os.path.basename(h["file"]))
                           for g in group if g != rel)]
    # 更直接: 排除六个孤儿文件本身
    ext_hits = [h for h in ext_hits
                if os.path.join(ROOT, h["file"]) not in
                {os.path.join(ROOT, o) for o in ORPHANS}]
    # 路由挂载检测: main.py 是否 import 该 router
    mounted = False
    main_txt = open(os.path.join(ROOT, "backend/main.py"),
                    encoding="utf-8", errors="ignore").read()
    if rel.startswith("backend/routes/"):
        mounted = bool(re.search(rf"import\s+\w*{stem}|from\s+.*\b{stem}\b", main_txt))
    info.update({
        "size_bytes": size,
        "head_summary": re.sub(r"\s+", " ", head)[:200],
        "external_references": ext_hits[:8],
        "external_ref_count": len(ext_hits),
        "router_mounted_in_main": mounted,
    })
    is_group = rel != "agent-app/src/data/conversationSync.js"
    info.update({
        "REFERENCED": bool(ext_hits) or mounted,
        "RUNTIME_OWNER": ("backend FastAPI main.py（若挂载）" if mounted else
                          "无生产挂载点" if is_group else
                          "agent-app 前端（未入库, 无构建引用链）"),
        "BUILD_IMPACT": ("移除不影响任何构建/运行路径（零引用）" if not ext_hits and not mounted
                         else "被引用, 移除会破坏导入"),
        "VERDICT": "KEEP_CANDIDATE" if (ext_hits or mounted) else "DELETE_CANDIDATE",
        "RATIONALE": "",
    })
    return info


if __name__ == "__main__":
    out = [audit_one(o) for o in ORPHANS]
    # 组内互引说明（已有 RATIONALE 的不覆盖）
    for r in out:
        if r.get("RATIONALE"):
            continue
        if not r.get("REFERENCED"):
            r["RATIONALE"] = ("零外部引用（组内互引不计）; 「零引用」≠「可安全删除」——最终去留属"
                              "用户资产决定, 本轮仅归类（Reviewer C 项裁定: 全部不删除不入库）")
        else:
            r["RATIONALE"] = ("存在外部/挂载引用, 删除会破坏导入; 需先理清功能归属再决定")
    # conversationSync.js 专项: 前端 import 链检测
    cs = next((r for r in out if "conversationSync" in r["path"]), None)
    if cs:
        imp = re.compile(r"conversationSync")
        hits = []
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "agent-app/src")):
            dirnames[:] = [x for x in dirnames if x not in SKIP_PARTS]
            for f in filenames:
                if f.endswith((".js", ".jsx", ".ts", ".tsx")):
                    fp = os.path.join(dirpath, f)
                    try:
                        txt = open(fp, encoding="utf-8", errors="ignore").read()
                    except Exception:
                        continue
                    if imp.search(txt) and not fp.endswith("conversationSync.js"):
                        hits.append(os.path.relpath(fp, ROOT))
        cs["conversationSync_importers"] = hits
        if hits:
            cs["REFERENCED"] = True
            cs["VERDICT"] = "KEEP_CANDIDATE"
            cs["RATIONALE"] = "agent-app 前端存在 import 引用, 删除将破坏构建"
    dst = os.path.join(ROOT, "backend/tools/_tmp/o8r2_ownership.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2600])
