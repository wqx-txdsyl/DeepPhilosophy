# -*- coding: utf-8 -*-
"""O7-B RP1 §10-11 — Clean checkout reproduction gate + deterministic rebuild identity.

在临时 git worktree（从指定 SHA checkout, 不带任何本机 untracked 文件）验证:
  1. backend/data/book_bibliography.json 被 git 跟踪且存在
  2. get_book_detail(pilot) / get_chapter(pilot) 暴露 metadata; 非 pilot 不变
  3. 在 clean tree 上重跑 builder → REBUILT_RUNTIME_DATA_HASH == TRACKED_RUNTIME_DATA_HASH

用法: .venv/bin/python backend/tools/dp_biblio_cleancheck.py <GATE_SHA>
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNTIME = "backend/data/book_bibliography.json"


def sh(*args, cwd=ROOT):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()


def fhash(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(sha):
    tmp = tempfile.mkdtemp(prefix="o7b_clean_")
    try:
        sh("git", "worktree", "add", "--detach", tmp, sha)
        # ① runtime data tracked & exists
        tracked = sh("git", "-C", tmp, "ls-files", RUNTIME)
        assert tracked == RUNTIME, f"runtime data 未被跟踪: {tracked!r}"
        assert os.path.exists(os.path.join(tmp, RUNTIME)), "runtime data 不存在"
        # ② 工具暴露（clean tree 内 import, 无本机 untracked 依赖）
        probe = r'''
import json, sys
sys.path.insert(0, "backend")
from routes import agent_tools_retrieval as RT
data = json.load(open("backend/data/book_bibliography.json", encoding="utf-8"))
pilot = next(iter(data["books"]))
allb = json.load(open("app/public/books.json", encoding="utf-8"))
non_pilot = next(b["id"] for b in allb if b["id"] not in data["books"])
det = RT.TOOLS["get_book_detail"]["execute"]({"book_id": pilot})
ch = RT.TOOLS["get_chapter"]["execute"]({"book_id": pilot, "chapter_idx": 0})
det2 = RT.TOOLS["get_book_detail"]["execute"]({"book_id": non_pilot})
out = {
  "detail_metadata": "bibliographic_metadata" in det,
  "chapter_metadata": "bibliographic_metadata" in ch,
  "citation_label": "citation_label" in ch,
  "non_pilot_untouched": "bibliographic_metadata" not in det2,
}
print(json.dumps(out))
'''
        r = subprocess.run([sys.executable, "-c", probe], cwd=tmp,
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-1500:]
        result = json.loads(r.stdout.strip().splitlines()[-1])
        assert result["detail_metadata"] and result["chapter_metadata"], result
        assert result["citation_label"] and result["non_pilot_untouched"], result
        # ③ deterministic rebuild（写到临时路径, 不污染 tree）
        rebuilt = os.path.join(tmp, "_rebuild_biblio.json")
        r = subprocess.run([sys.executable, "backend/tools/dp_biblio_build.py",
                            "--out", rebuilt], cwd=tmp, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-1500:]
        h_tracked = fhash(os.path.join(tmp, RUNTIME))
        h_rebuilt = fhash(rebuilt)
        assert h_tracked == h_rebuilt, f"重建 hash 不一致: {h_tracked[:12]} != {h_rebuilt[:12]}"
        print(json.dumps({
            "gate_sha": sha,
            "CLEAN_CHECKOUT_METADATA_VISIBLE": True,
            "CLEAN_CHECKOUT_LOCAL_GENERATION_REQUIRED": False,
            "TRACKED_RUNTIME_DATA_HASH": h_tracked,
            "REBUILT_RUNTIME_DATA_HASH": h_rebuilt,
            "DETERMINISTIC_REBUILD_MATCH": True,
        }, indent=1))
        return 0
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", tmp],
                       cwd=ROOT, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "HEAD"))
