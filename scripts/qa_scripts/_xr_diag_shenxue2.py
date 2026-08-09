# -*- coding: utf-8 -*-
"""实测 scan_books + _generate_summary 对神学大全两卷的返回"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend')
import os
os.chdir('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend')

import main

books = main.scan_books(force=True)
for b in books:
    if b['id'] in ('f52ed83b99d9', '9ed36aca09c5'):
        print('id:', b['id'], '| title:', repr(b['title']), '| author:', repr(b['author']), '| file_type:', b['file_type'])
        s = main._generate_summary(b)
        print('  summary 返回:', repr(s[:120]))
        print('  summary 长度:', len(s))
        print()
