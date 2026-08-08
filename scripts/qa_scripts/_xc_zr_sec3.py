# -*- coding: utf-8 -*-
"""临时: 万物本性论卷内标题行定位（搜索关键词行）"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

KWS = ["物质的永恒性", "虚空的存在及其性质", "独立存在者", "永恒性再证明", "赫拉克里特", "恩培多克勒", "阿那克萨戈拉",
       "永远快速运动", "向下运动和偏斜", "形状多样", "数量无限", "多种原子组成", "没有颜色", "心理活动",
       "独立于身体", "有死的", "死与我们无关", "视觉，感觉的可靠性", "听觉、味觉", "影像与心灵", "批判目的论",
       "睡眠与梦", "情爱徒劳", "情欲应当", "神圣的和永恒的", "世界的形成", "天象，天体", "昼夜和季节", "大地的幼年",
       "原始人的生活", "语言的出现", "国家法律", "宗教的起源", "金属工具", "打雷和闪电", "霹雳", "海旋", "地震",
       "火山爆发", "磁石", "疾病的原因", "雅典的瘟疫", "序诗A", "序诗B"]
print("===== 关键词行定位 =====")
for k in range(70, 269):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls):
        n = re.sub(r"\s+", "", l)
        for kw in KWS:
            if kw in n and len(n) <= 24 and not l.startswith("自然与快乐"):
                print(f"p{k} 行{i}: {n}")
                break
