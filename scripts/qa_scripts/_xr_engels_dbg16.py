# -*- coding: utf-8 -*-
"""调试 16.json 两处未合并断段"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _xr_engels_fix import (CONT, PUNCT_HEAD, FN_STANDALONE, FN_TITLE, SHORT_EXCLUDE,
                            NAME_COLON, NOTE_END, is_sentence_end)

c = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/aa21ac425e87/16.json', encoding='utf-8'))
vals = [b.get('value', '').strip() for b in c['content']
        if isinstance(b, dict) and isinstance(b.get('value', ''), str) and b['value'].strip()]
for i, v in enumerate(vals):
    if 'mv' in v or '静止是运动的特殊情况' in v:
        prev_t = vals[i - 1].rstrip() if i > 0 else '(首段)'
        cur = v
        checks = {
            'is_sentence_end(prev)': is_sentence_end(prev_t),
            'FN_STANDALONE': bool(FN_STANDALONE.match(cur)),
            'FN_TITLE': bool(FN_TITLE.match(cur)),
            'SHORT_EXCLUDE': bool(SHORT_EXCLUDE.match(cur)),
            'NAME_COLON': bool(NAME_COLON.match(cur)),
            'startswith［（(——': cur.startswith(('［', '（', '(', '——')),
            'num_list': bool(re.match(r'^\d+[．.]', cur)),
            'NOTE_END(prev)': bool(NOTE_END.search(prev_t)),
            'prev endswith）': prev_t.endswith('）'),
            'prev is alpha': bool(re.fullmatch(r'[A-Za-z]+', prev_t)),
            'short_title_excl': (len(prev_t) < 15 and len(cur) >= 15 and not prev_t.startswith('（')),
            'CONT.match(cur)': bool(CONT.match(cur)),
        }
        print(f'--- i={i} prev尾={prev_t[-20:]!r} cur头={cur[:18]!r}')
        for k, vv in checks.items():
            if vv:
                print(f'    {k}: {vv}')
        if not checks['is_sentence_end(prev)'] and not checks['FN_STANDALONE'] and not checks['FN_TITLE'] \
                and not checks['SHORT_EXCLUDE'] and not checks['NAME_COLON'] and not checks['startswith［（(——'] \
                and not checks['num_list'] and not checks['NOTE_END(prev)'] and not checks['prev endswith）'] \
                and not checks['prev is alpha'] and not checks['short_title_excl']:
            print('    → 所有排除未触发，应合并！')
