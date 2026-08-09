# -*- coding: utf-8 -*-
"""验证清洗效果: 用户指出的会饮篇 296-297 页 + 全章字符量"""
import json

P = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d\9.json'
ch = json.load(open(P, encoding='utf-8'))
blocks = ch['content']
print('会饮篇块数:', len(blocks), '| 总字符:', sum(len(b['value']) for b in blocks if isinstance(b, dict)))
print()
print('== 原296页块(现第2块) 开头 ==')
print(blocks[1]['value'][:120])
print()
print('== 原297页块(现第3块) 开头 ==')
print(blocks[2]['value'][:120])
print()
print('== 原298页块(现第4块) 开头 ==')
print(blocks[3]['value'][:120])
print()
print('== 原296页块 末尾(页脚注释应已删) ==')
print(blocks[1]['value'][-120:])
# 检查是否还有残留页眉/圈号行首
import re
resid = []
for i, b in enumerate(blocks):
    for j, ln in enumerate(str(b.get('value','')).split('\n')):
        if re.match(r'^[①-⑩]', ln.strip()) or re.match(r'^\d{1,3}\n柏拉图对话集', ln):
            resid.append((i, j, ln[:40]))
print()
print('残留圈号行首/页眉:', '无 ✓' if not resid else resid[:10])
