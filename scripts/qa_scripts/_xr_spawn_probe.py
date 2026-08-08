# -*- coding: utf-8 -*-
"""spawn 实验探针：最小化定位 spawn 源
venv pythonw 跑本脚本，只 import paddleocr，观察是否 spawn 系统 Python 对
输出到同目录 _xr_spawn_probe.log
"""
import sys, os, time

log = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_xr_spawn_probe.log')

def p(msg):
    with open(log, 'a', encoding='utf-8') as f:
        f.write(f'[{time.strftime("%H:%M:%S")}] {msg}\n')

p(f'started executable={sys.executable} pid={os.getpid()}')
p(f'importing paddle...')
import paddle
p('paddle ok')
p('importing paddleocr...')
import paddleocr
p('paddleocr ok')
p('sleeping 25s (watch for spawn)...')
time.sleep(25)
p('done')
