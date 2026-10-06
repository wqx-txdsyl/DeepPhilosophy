# -*- coding: utf-8 -*-
"""构建 PhiAgent 前端并同步到 backend/static（8011 同源托管，agent.deepphilosophy.top 经隧道访问）

用法: python scripts/build_phiagent_static.py
流程:
  1. cd agent-app && npm run build          → agent-app/dist/
  2. 拷贝必要产物到 backend/static/          → 8011 根路径提供 SPA + /api 同源

backend/static 已被 gitignore（本地构建产物，不入库）；重新部署只需重跑本脚本。
"""
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_APP = os.path.join(BASE, "agent-app")
DIST = os.path.join(AGENT_APP, "dist")
STATIC = os.path.join(BASE, "backend", "static")

# 仅拷贝 phiagent 实际引用的路径（assets/icons/covers.json/covers）; 其余为平台数据副本, 不入静态目录
ESSENTIALS = ["assets", "icons", "covers.json", "covers", "index.html"]


def main():
    print(f"[1/2] building agent-app ...")
    r = subprocess.run(["npm", "run", "build"], cwd=AGENT_APP, shell=(os.name == "nt"))
    if r.returncode != 0:
        print("build failed", file=sys.stderr)
        sys.exit(1)

    os.makedirs(STATIC, exist_ok=True)
    print(f"[2/2] syncing to {STATIC}")
    for name in ESSENTIALS:
        src = os.path.join(DIST, name)
        dst = os.path.join(STATIC, name)
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f"  {name} ✓")
    print("done. backend 8011 now serves PhiAgent at /")


if __name__ == "__main__":
    main()
