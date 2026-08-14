# -*- coding: utf-8 -*-
"""
dp_ocr_watchdog.py — OCR 单分片看门狗（独立 pythonw 进程, 会话无关）
背景: OCR 曾两次整体死亡（会话后台任务被杀 / 系统休眠）——ckpt 页级断点可续, 但需自动拉起
单分片模式（2026-08-05: 4 并行 CPU 过热, 改 1 路慢跑）
检测: ckpt 超过 TIMEOUT 秒未更新（死/卡）→ 杀旧进程 → pythonw 重启（断点续传）
退出: 主 ckpt books >= TOTAL_PDFS（全部完成）
"""
import os, sys, time, json, subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
DATA = os.path.join(BASE, "data")
TOOLS = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.dirname(os.path.dirname(sys.executable)) if sys.executable else r"F:\program\Python\DeepPhilosophy\.venv"
PYW = os.path.join(VENV, "Scripts", "pythonw.exe")
SCRIPT = os.path.join(TOOLS, "dp_pdf_import.py")
SHARDS = 1
TIMEOUT = 600          # 10 分钟无写盘视为死
CHECK_EVERY = 60       # 检查间隔
TOTAL_PDFS = 120       # 全部 pdf（应用合并规则后扫描 120）


def log(msg):
    try:
        with open(os.path.join(DATA, "ocr_watchdog.log"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def ckpt_age(shard):
    ck = os.path.join(DATA, "dp_pdf_import_ckpt.json" if shard == 0 else f"dp_pdf_import_ckpt_s{shard}.json")
    if os.path.exists(ck):
        return time.time() - os.path.getmtime(ck)
    return float("inf")


def shard_pids(shard):
    # PowerShell 命令用 Python 单引号包住（反引号是 PS 转义符, Python 端必须原样传给 PS）
    # 单分片模式: 进程命令行是 dp_pdf_import.py 0 1
    ps = ('(Get-CimInstance Win32_Process -Filter "Name=\'pythonw.exe\'" | '
          f'Where-Object {{ $_.CommandLine -match \'dp_pdf_import\\.py.* {shard} 1\' }} | '
          "ForEach-Object { $_.ProcessId }) -join ','")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return [int(p) for p in out.split(",") if p.strip().isdigit()]
    except Exception:
        return []


def restart(shard):
    for pid in shard_pids(shard):
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=15)
            log(f"  killed old pid {pid}")
        except Exception:
            pass
    time.sleep(2)
    so = open(os.path.join(DATA, f"ocr_s{shard}.log"), "a", encoding="utf-8")
    se = open(os.path.join(DATA, f"ocr_s{shard}_err.log"), "a", encoding="utf-8")
    p = subprocess.Popen([PYW, SCRIPT, str(shard), str(SHARDS)], stdout=so, stderr=se)
    log(f"  restarted pid {p.pid}")


def main():
    log(f"watchdog start: shards={SHARDS}, timeout={TIMEOUT}s, check={CHECK_EVERY}s")
    while True:
        time.sleep(CHECK_EVERY)
        try:
            ck = json.load(open(os.path.join(DATA, "dp_pdf_import_ckpt.json"), encoding="utf-8"))
            done = len(ck.get("books", {}))
        except Exception:
            done = -1
        if done >= TOTAL_PDFS:
            log(f"ALL DONE ({done}/{TOTAL_PDFS}) → exit")
            break
        for s in range(SHARDS):
            age = ckpt_age(s)
            if age > TIMEOUT:
                log(f"shard {s}: ckpt stale {int(age)}s → restart")
                restart(s)
        log(f"check pass (books {done}/{TOTAL_PDFS})")


if __name__ == "__main__":
    main()
