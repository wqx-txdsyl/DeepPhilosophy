#!/bin/bash
# 引擎心跳监控: 每 5 分钟探查一次, 正常静默, 异常/完成才输出事件
# 覆盖 tail -f 的盲区: 引擎静默崩溃(进程死) / 卡死(日志无写入/进度无推进)
CKPT="F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json"
LOG="F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/ocr_s0.log"
ENGINE_PID=25504
KEY="西方_格奥尔格_威廉_弗里德里希_黑格尔_精神现象学.pdf"
TOTAL_PAGES=553
stall_rounds=0

query_ckpt() {
  python - "$CKPT" "$KEY" <<'PY'
import json, sys
try:
    c = json.load(open(sys.argv[1], encoding='utf-8'))
    books = len(c.get('books', {}))
    p = c.get('ocr', {}).get(sys.argv[2], {})
    pages = len(p)
    failed = sum(1 for v in p.values() if v == '__FAILED__')
    print(f"{books}|{pages}|{failed}")
except Exception as e:
    print("ERR|0|0", flush=True)
PY
}

while true; do
  now=$(date +%s)

  # 1. 引擎进程存活
  alive=1
  powershell -NoProfile -Command "if (Get-Process -Id $ENGINE_PID -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" 2>/dev/null || alive=0

  count=$(query_ckpt)
  books=$(echo "$count" | cut -d'|' -f1)
  pages=$(echo "$count" | cut -d'|' -f2)
  failed=$(echo "$count" | cut -d'|' -f3)

  if [ "$books" = "ERR" ]; then
    echo "ALERT ckpt 读取失败 — 引擎写坏或文件被锁, 需人工检查"
    exit 1
  fi

  # 2. 入库完成 (精神现象学 books 86→87)
  if [ "$books" -ge 87 ]; then
    echo "DONE 精神现象学已入库 books=$books — 重启 vite + verify_book.py"
    exit 0
  fi

  # 3. 进程死且未入库 → 意外
  if [ "$alive" = "0" ]; then
    echo "ALERT 引擎进程 $ENGINE_PID 已死, 但 books=$books 未达 87 (精神现象学页进度 $pages/$TOTAL_PAGES, FAILED $failed)"
    exit 1
  fi

  # 4. 日志新鲜度: 10 分钟无写入 → 卡死
  lmtime=$(stat -c %Y "$LOG" 2>/dev/null || echo 0)
  age=$(( now - lmtime ))
  if [ $age -gt 600 ]; then
    echo "ALERT 日志 $age 秒无写入 — 引擎卡死? (books=$books 精神现象学 $pages/$TOTAL_PAGES)"
    exit 1
  fi

  # 5. 进度推进: 连续 6 轮(30分钟)页数不变 → 卡住 (注: FAILED 重试阶段页数可能不动, 但日志新鲜度兜底)
  if [ "$pages" = "$last_pages" ]; then
    stall_rounds=$((stall_rounds + 1))
    if [ $stall_rounds -ge 6 ]; then
      echo "ALERT 进度 30 分钟未推进 (仍 $pages/$TOTAL_PAGES, FAILED $failed) — 引擎可能死循环"
      exit 1
    fi
  else
    stall_rounds=0
    last_pages="$pages"
  fi

  sleep 300
done
