# -*- coding: utf-8 -*-
"""临时: 打印指定 PDF 页的首几行（锚点验证用）"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

targets = {
    324: "辩证论·第一卷纯粹理性的概念?",
    342: "辩证论·第二卷纯粹理性的辩证推论?",
    561: "先验辩证论附录?",
    663: "法规·第一节?",
    667: "法规·第二节?",
    751: "索引区?",
    753: "索引区?",
    755: "索引区?",
}
for pdf, note in targets.items():
    print(f"===== PDF{pdf} ({note}) =====")
    ls = [l.strip() for l in pages[str(pdf)].split("\n") if l.strip()]
    for l in ls[:8]:
        print(" ", l[:56])
