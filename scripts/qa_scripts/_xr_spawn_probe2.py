# -*- coding: utf-8 -*-
"""spawn 探针 B2：import paddleocr + PaddleOCR() 实例化（加载模型），观察 spawn
venv pythonw 跑，日志到同目录 _xr_spawn_probe2.log
"""
import sys, os, time

log = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_xr_spawn_probe2.log')

def p(msg):
    with open(log, 'a', encoding='utf-8') as f:
        f.write(f'[{time.strftime("%H:%M:%S")}] {msg}\n')

p(f'started pid={os.getpid()} exe={sys.executable}')
p('importing paddleocr...')
from paddleocr import PaddleOCR
p('imported, instantiating PaddleOCR()...')
ocr = PaddleOCR()  # 加载 det/rec 模型（约 5-20 秒）
p('PaddleOCR instantiated ok')
p('sleeping 30s (watch for spawn)...')
time.sleep(30)
p('done')
