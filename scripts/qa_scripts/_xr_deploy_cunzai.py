# -*- coding: utf-8 -*-
"""论存在者与本质 部署：重建产物 → PA backend 章节 + PA detail → _xr_sync_bids 四层 → 五步验证"""
import json, os, shutil, subprocess, sys

bid = 'e1fabd8e802c'
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_xr_out_cunzai')
PA_CH = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
PA_DETAIL = 'f:/program/Python/PhiAgent/backend/data/book_detail'
QA = os.path.dirname(os.path.abspath(__file__))

dst = os.path.join(PA_CH, bid)
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(SRC, dst)
print('① PA 章节 %s 个文件 ✓' % len(os.listdir(dst)))

m = json.load(open(os.path.join(dst, 'meta.json'), encoding='utf-8'))
df = os.path.join(PA_DETAIL, bid + '.json')
d = json.load(open(df, encoding='utf-8'))
d['toc'] = m['toc']
d['chapterCount'] = m['chapterCount']
d['chapterTitles'] = m['chapterTitles']
json.dump(d, open(df, 'w', encoding='utf-8'), ensure_ascii=False)
print('② PA detail: cc=%d toc对象格式 ✓' % d['chapterCount'])

r = subprocess.run([sys.executable, os.path.join(QA, '_xr_sync_bids.py'), bid],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

r = subprocess.run([sys.executable, os.path.join(QA, '_xr_verify_generic.py'), bid],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)
print('部署完成 ✓')
