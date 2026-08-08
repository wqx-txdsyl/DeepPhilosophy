# -*- coding: utf-8 -*-
"""临时: 在页范围中搜索标题行"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

def find(pdf_from, pdf_to, pats):
    for pdf in range(pdf_from, pdf_to + 1):
        for line in pages[str(pdf)].split("\n"):
            n = re.sub(r"\s+", "", line)
            for pat in pats:
                if n and re.search(pat, n):
                    print(f"PDF{pdf}: {line.strip()[:60]}")
                    break

print("== 辩证推论标题 (330-360) ==")
find(330, 360, [r"第二卷纯粹理性的辩证推论"])
print("== 法规节标题 (662-683) ==")
find(662, 683, [r"第一节我们理性的纯粹运用的最终目的", r"第一节[^。]{2,12}最终目的",
                 r"第二节至善", r"第二节[^。]{2,12}根据", r"意见、知识和信念"])
print("== 附录标题 (555-565) ==")
find(555, 565, [r"先验辩证论附录", r"纯粹理性诸理念的调节性运用", r"人类理性的自然辩证论的终极意图"])
print("== 索引区 (743-756) ==")
find(743, 756, [r"汉德术语对照表", r"人名索引", r"德汉术语索引", r"版本说明"])
