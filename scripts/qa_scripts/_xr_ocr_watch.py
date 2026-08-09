# -*- coding: utf-8 -*-
"""OCR 引擎盯梢②：checkpoint 顶层结构 + 进程命令行 + 日志文件 + 处理中书的证据"""
import json, os, time, subprocess

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
CK = os.path.join(DP, 'backend/data/dp_pdf_import_ckpt.json')

ck = json.load(open(CK, encoding='utf-8'))
print('checkpoint 顶层键:', list(ck.keys()))
for k, v in ck.items():
    if isinstance(v, dict) and len(v) < 8:
        print('  %s: %s' % (k, json.dumps(v, ensure_ascii=False)[:200]))
    elif isinstance(v, dict):
        sample = list(v.items())[:2]
        print('  %s: dict(%d) 样例: %s' % (k, len(v), json.dumps(sample, ensure_ascii=False)[:200]))

print()
# 进程命令行：谁在跑 dp_pdf_import
print('=== python/pythonw 进程命令行 ===')
r = subprocess.run(['wmic', 'process', 'where', "name like 'python%'", 'get', 'ProcessId,CommandLine', '/format:list'],
                   capture_output=True, text=True, errors='ignore')
for line in r.stdout.splitlines():
    line = line.strip()
    if line and ('dp_pdf' in line or 'pdf_import' in line or line.startswith('CommandLine=') or line.startswith('ProcessId=')):
        print(' ', line[:160])
