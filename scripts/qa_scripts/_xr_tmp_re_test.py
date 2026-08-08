# -*- coding: utf-8 -*-
import re
v = "第4章 论主体的第一类客体，以及在这类客体中起支配作用的充足根据律的形式（下）"
pat = r'^第\d+章.*（上|下）$'
print("1:", bool(re.match(pat, v)))
print("2:", bool(re.match(pat, "第4章（下）")))
print("3:", bool(re.match(r'.*（下）$', v)))
print("4:", bool(re.match(r'^第\d+章.*（下）$', v)))
print("5:", bool(re.match(r'^第\d+章.*下）$', v)))
print("6:", bool(re.match(r'^第\d+章.*\)$', v)))
