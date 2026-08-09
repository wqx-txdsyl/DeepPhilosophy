# -*- coding: utf-8 -*-
import json
ch = json.load(open('_xr_out_aquinas7/22.json', encoding='utf-8'))
v = ch['content'][0]['value']
print('译后记 3318 残留:', '3318' in v)
paras = [p for p in v.split('\n\n') if p.strip()]
print('段数:', len(paras))
for p in paras[-4:]:
    print('末段: %s…' % p[:80].replace('\n', ''))
    print('  …%s' % p[-60:].replace('\n', ''))
