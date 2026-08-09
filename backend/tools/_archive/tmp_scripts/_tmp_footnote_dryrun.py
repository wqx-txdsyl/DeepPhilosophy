# -*- coding: utf-8 -*-
"""干跑模拟（干净版）: 脚注区分离规则统计
规则: 行首①-⑨ 行无条件移入注释段; 其后紧邻行若满足注释特征也移入
注释特征: 含'译者注' | 行首①-⑨ | (以。？！.，,结尾 且 <=120字)
输出: moved 移出 / wounded 疑似误伤(>80字且无注释特征词) / missed 残留①行"""
import json, re, sys, time

LOG = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/tools/_tmp_footnote_dryrun.out.txt'
ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_托马斯_霍布斯_托马斯_霍布斯.pdf', {})

FOOT_RE = re.compile(r'^\d{1,4}$')
NOTE_START = re.compile(r'^[①②③④⑤⑥⑦⑧⑨]')
FEAT = ['Hobbes', 'Ibid', 'Malcolm', 'Aubrey', 'Skinner', 'Ross', 'Thucydides',
        'Namque', 'Philosophia', 'Illius', '译者注', '格劳修斯', '苏亚雷斯', '阿奎拉', '斯金纳']

def is_note_line(ln):
    if '译者注' in ln:
        return True
    if NOTE_START.match(ln):
        return True
    if len(ln) <= 120 and (ln.endswith('。') or ln.endswith('？') or ln.endswith('！')
                           or ln.endswith('.') or ln.endswith(',') or ln.endswith('，')):
        return True
    return False

moved = wounded = missed = pages_with_note = 0
t0 = time.time()
for k in sorted(int(x) for x in ocr):
    v = ocr[str(k)]
    if not v or v == '__FAILED__':
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    body = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if FOOT_RE.match(ln):
            i += 1
            continue
        if NOTE_START.match(ln):
            pages_with_note += 1
            moved += 1
            j = i + 1
            while j < len(lines) and not FOOT_RE.match(lines[j]) and not NOTE_START.match(lines[j]):
                if is_note_line(lines[j]):
                    moved += 1
                    if len(lines[j]) > 80 and not any(f in lines[j] for f in FEAT):
                        wounded += 1
                    j += 1
                else:
                    break
            i = j
            continue
        body.append(ln)
        i += 1
    for ln in body:
        if NOTE_START.match(ln):
            missed += 1

out = open(LOG, 'w', encoding='utf-8')
out.write('含脚注页: %d\n' % pages_with_note)
out.write('移出脚注行(含续行): %d\n' % moved)
out.write('疑似误伤正文行: %d\n' % wounded)
out.write('残留①行(漏): %d\n' % missed)
out.write('耗时 %.1fs\n' % (time.time() - t0))
out.close()

# 续行清单: 重跑一次收集非①行被移出的内容
log2 = open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/tools/_tmp_footnote_continuations.txt', 'w', encoding='utf-8')
for k in sorted(int(x) for x in ocr):
    v = ocr[str(k)]
    if not v or v == '__FAILED__':
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    i = 0
    while i < len(lines):
        ln = lines[i]
        if FOOT_RE.match(ln):
            i += 1
            continue
        if NOTE_START.match(ln):
            j = i + 1
            while j < len(lines) and not FOOT_RE.match(lines[j]) and not NOTE_START.match(lines[j]):
                if is_note_line(lines[j]):
                    log2.write('页%d 续行[%d]: %s\n' % (k, j, lines[j][:90]))
                    j += 1
                else:
                    break
            i = j
            continue
        i += 1
log2.close()
print('续行清单已写')
