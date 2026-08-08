# -*- coding: utf-8 -*-
import sys, re, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
opf = z.read("OEBPS/content.opf").decode("utf-8", errors="replace")
i = opf.find("<spine")
j = opf.find("</spine>")
print(opf[i:j+9])
