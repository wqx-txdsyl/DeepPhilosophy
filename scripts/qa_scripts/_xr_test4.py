# -*- coding: utf-8 -*-
import re
MID = re.compile(r'(?<=[一-鿿])\d{3,4}[a-z](?=[一-鿿])')
for s in ['这就是440a形体', '有439b物', '所有447b的人']:
    print(repr(s), '->', repr(MID.sub('', s)))
