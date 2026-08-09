# -*- coding: utf-8 -*-
import json, os
base = os.path.dirname(os.path.abspath(__file__))
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))
def show(od, fn, n_head=120, n_tail=200):
    ch = json.load(open(os.path.join(base, od, fn), encoding='utf-8'))
    v = ch['content'][0]['value']
    print('[%s/%s] %s | 开头: %s…' % (od, fn, ch['title'], v[:n_head].replace('\n', '⏎')))
    print('  …结尾: …%s' % v[-n_tail:].replace('\n', '⏎'))
    print()
show('_xr_out_aquinas6', '1.json')       # 问题76 首尾
show('_xr_out_aquinas6', '14.json')      # 问题89 首尾（中段）
show('_xr_out_aquinas7', '17.json')      # 附录一 首尾
show('_xr_out_aquinas7', '22.json', n_tail=300)  # 译后记尾
show('_xr_out_bacon', '1.json')          # 第一卷首尾
show('_xr_out_bacon', '2.json', n_tail=300)       # 第二卷尾（全书尾）
# 第7卷 0.json 末段完整 + 页 27 原文
ch = json.load(open(os.path.join(base, '_xr_out_aquinas7', '0.json'), encoding='utf-8'))
paras = [p for p in ch['content'][0]['value'].split('\n\n') if p.strip()]
print('===== 问题103 章末段完整 =====')
print(repr(paras[-1]))
print()
print('===== checkpoint 页27 原文（问题103 最后一页） =====')
print(ck['ocr']['西方_托马斯_阿奎那_神学大全_第一集_第7卷.pdf'].get('27', '缺失')[-800:])
