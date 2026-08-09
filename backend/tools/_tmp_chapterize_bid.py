# -*- coding: utf-8 -*-
"""按 ckpt 页级断点重建指定书的章节文件（通用, 幂等）:
用法: _tmp_chapterize_bid.py <rel路径> [title] [author]
读 dp_pdf_import_ckpt.json 的 ocr[safe] → 页序文本 → chapterize → 写 0..N.json + meta"""
import json, os, re, sys, shutil, hashlib

CKPT = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend'

REL = sys.argv[1]
TITLE = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(REL))[0]
AUTHOR = sys.argv[3] if len(sys.argv) > 3 else ''

sys.path.insert(0, os.path.join(BASE, 'tools'))
import importlib.util
spec = importlib.util.spec_from_file_location('dpp', os.path.join(BASE, 'tools', 'dp_pdf_import.py'))
dpp = importlib.util.module_from_spec(spec)
_save_argv = sys.argv
sys.argv = ['dp_pdf_import.py']
try:
    spec.loader.exec_module(dpp)
finally:
    sys.argv = _save_argv

bid = hashlib.md5(REL.encode()).hexdigest()[:12]
safe = re.sub(r'[^\w\-.]', '_', REL)
ckpt = json.load(open(CKPT, encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get(safe, {})
done = {int(k): v for k, v in ocr.items() if v and v != '__FAILED__'}
failed = [int(k) for k, v in ocr.items() if v == '__FAILED__']
print('页级断点:', len(done), '页 | FAILED:', failed)
full = '\n\n'.join(done.get(i, '') for i in range(max(done) + 1))
print('总字符:', len(full))

chs = dpp.chapterize(full)
print('章节数:', len(chs))
for i, c in enumerate(chs):
    print('  [%d] %s (%d字符)' % (i, c['title'][:40], len(c['text'])))

D = os.path.join(BASE, 'data/book_chapters', bid)
if os.path.exists(D):
    shutil.rmtree(D)
os.makedirs(D)
toc = []
for idx, c in enumerate(chs):
    ch = {'index': idx, 'title': c['title'], 'content': dpp.to_blocks(c['text'])}
    json.dump(ch, open(os.path.join(D, f'{idx}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    toc.append(c['title'])
meta = {'bookId': bid, 'title': TITLE, 'author': AUTHOR, 'toc': toc,
        'cover': None, 'chapterCount': len(toc), 'chapterTitles': toc}
json.dump(meta, open(os.path.join(D, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('已写入:', bid, '| toc =', toc)
