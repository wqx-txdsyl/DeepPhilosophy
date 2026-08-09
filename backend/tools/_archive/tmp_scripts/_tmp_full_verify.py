# -*- coding: utf-8 -*-
"""全量逐本验证 (任务 8): books.json 全部非 txt 书逐本跑 verify_book.py
结果写入 _full_verify_result.txt (utf-8), 打印汇总
用法: python _tmp_full_verify.py [--vite-check] (默认本地检查)
"""
import json, os, subprocess, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
TOOL = os.path.join(BASE, 'backend', 'tools', 'verify_book.py')
VITE = '--vite-check' in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_full_verify_result.txt')

bj = json.load(open(os.path.join(BASE, 'app/public/books.json'), encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
targets = [it for it in items if it.get('file_type') != 'txt']
print('待验证 %d 本 (共 %d 条目, 排除 %d txt)' % (len(targets), len(items), len(items) - len(targets)))

ok, fail = [], []
lines = []
for i, it in enumerate(targets):
    bid = it['id']
    cmd = [sys.executable, TOOL, bid] + (['--vite-check'] if VITE else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    title = (it.get('title') or '')[:24]
    if r.returncode == 0:
        ok.append(bid)
        line = '[%3d/%d] OK  %s %s' % (i + 1, len(targets), title, bid)
    else:
        fail.append((bid, title, r.stdout[-500:]))
        line = '[%3d/%d] FAIL %s %s' % (i + 1, len(targets), title, bid)
    print(line, flush=True)
    lines.append(line)
    if r.returncode != 0:
        for l in r.stdout.strip().split('\n')[-6:]:
            lines.append('      ' + l)

lines.append('')
lines.append('===== 汇总 =====')
lines.append('通过: %d  失败: %d' % (len(ok), len(fail)))
if fail:
    lines.append('失败清单:')
    for bid, title, _ in fail:
        lines.append('  %s %s' % (bid, title))
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('结果已写入 %s' % OUT)
print('===== 汇总 =====')
print('通过: %d  失败: %d' % (len(ok), len(fail)))
if fail:
    print('失败清单:')
    for bid, title, _ in fail:
        print('  %s %s' % (bid, title))
