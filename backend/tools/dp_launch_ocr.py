# -*- coding: utf-8 -*-
"""dp_launch_ocr.py — 启动 OCR 单分片 + 看门狗（pythonw 独立进程, 会话无关）
单分片模式（2026-08-05 决策: 4 并行 CPU 过热, 改 1 路慢跑, 不抢其他任务）
用 subprocess.Popen 精确启动（绕过 Start-Process 的传参怪癖: 每条会启动 2 个进程）
"""
import os, sys, subprocess

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(TOOLS)
DATA = os.path.join(BASE, "data")
VENV = os.path.dirname(os.path.dirname(sys.executable))
PYW = os.path.join(VENV, "Scripts", "pythonw.exe")
SCRIPT = os.path.join(TOOLS, "dp_pdf_import.py")
WATCHDOG = os.path.join(TOOLS, "dp_ocr_watchdog.py")


def log(msg):
    try:
        with open(os.path.join(DATA, "ocr_launch.log"), "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
    try:
        sys.__stdout__.write(msg + "\n")
        sys.__stdout__.flush()
    except Exception:
        pass


def main():
    started = []
    # --only 书名: 单本试跑（质量验证后再放量）
    only_args = []
    if "--only" in sys.argv:
        only_args = ["--only", sys.argv[sys.argv.index("--only") + 1]]
    # 单分片: dp_pdf_import.py 0 1（主 ckpt 断点续传, CPU 1 路慢跑）
    so = open(os.path.join(DATA, "ocr_s0.log"), "a", encoding="utf-8")
    se = open(os.path.join(DATA, "ocr_s0_err.log"), "a", encoding="utf-8")
    p = subprocess.Popen([PYW, SCRIPT, "0", "1"] + only_args, stdout=so, stderr=se)
    started.append(("shard", 0, p.pid))
    log(f"started shard 0 pid {p.pid} {'--only ' + only_args[1] if only_args else ''}")
    so = open(os.path.join(DATA, "ocr_watchdog.log"), "a", encoding="utf-8")
    se = open(os.path.join(DATA, "ocr_watchdog_err.log"), "a", encoding="utf-8")
    p = subprocess.Popen([PYW, WATCHDOG], stdout=so, stderr=se)
    started.append(("watchdog", "", p.pid))
    log(f"started watchdog pid {p.pid}")
    log(f"total {len(started)} processes")


if __name__ == "__main__":
    main()
