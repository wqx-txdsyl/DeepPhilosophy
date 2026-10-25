#!/usr/bin/env python3
"""书5《柏拉图对话集》35279e2e439d ch0-16 批量核定修复（981条issue）"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dp_proofread_lib import Proofreader

RD = Path("/Users/sen/.codex/worktrees/book-quality-zcode-20261024/DeepPhilosophy/docs/tasks/book-full-proofread-zcode-2026-10-24/progress/reading")

OPS = []
merge_n = 0
residual_items = []
skipped_stats = {}

def clean_edge(s, left=True):
    # 去报告省略号省略标记（两端都可能带）
    while s.startswith("…"):
        s = s[1:]
    while s.endswith("…"):
        s = s[:-1]
    return s

for fname in ("35279e2e439d.ch0-8.json", "35279e2e439d.ch9-16.json"):
    rep = json.loads((RD / fname).read_text())
    for c in rep["perChapter"]:
        ch = c["chapter"]
        for iss in c["issues"]:
            t = iss.get("type", "other")
            conf = iss.get("confidence", "uncertain")
            orig = iss.get("original") or ""
            prop = iss.get("proposed")
            if t == "page-split":
                if conf not in ("certain", "likely") or "‖" not in orig:
                    skipped_stats[t] = skipped_stats.get(t, 0) + 1
                    continue
                a, _, b = orig.partition("‖")
                tail = clean_edge(a.strip())
                head = clean_edge(b.strip())
                if not tail or not head:
                    skipped_stats[t] = skipped_stats.get(t, 0) + 1
                    continue
                OPS.append({"op": "merge", "ch": ch, "tail_expect": tail, "head_expect": head,
                            "note": "页缝硬拆合并"})
                merge_n += 1
                continue
            if conf not in ("certain", "likely") or not prop:
                skipped_stats["residual:" + t] = skipped_stats.get("residual:" + t, 0) + 1
                continue
            if not orig.strip():
                skipped_stats["empty-orig"] = skipped_stats.get("empty-orig", 0) + 1
                continue
            if t == "name-inconsistency":
                # 译名统一由专门 replace_all 处理
                skipped_stats["name-unify"] = skipped_stats.get("name-unify", 0) + 1
                continue
            OPS.append({"op": "replace_in", "ch": ch, "original": orig, "proposed": prop,
                        "note": (iss.get("evidence") or "")[:100]})

# 译名统一：欧梯甫戎→欧悌甫戎（王太庆译本用字，报告核定）
OPS.append({"op": "replace_all_in", "ch": 1, "original": "欧梯甫戎", "proposed": "欧悌甫戎",
            "note": "同章两种译名混用，统一为悌（报告核定）"})

print(f"ops: {len(OPS)} (merges {merge_n})")

p = Proofreader("35279e2e439d", "柏拉图对话集（王太庆）")
p.residuals = [
    {"ch": "全书", "issue": "【重大】原书脚注在数字化时整体丢失：ch0-8 的21处①②③标记、ch9-16 的①②③④及被OCR误作?的标记均无对应注文——注文无法复原，标记保留原状，待对照纸本补译"},
    {"ch": "全书", "issue": "不确定项14+条（丹答罗/居狄亚/比格贝/互相爱款/坏间/伊弱果/亚尔柯/诚恐诚等）均无据未改，详见两份报告"},
    {"ch": 0, "issue": "块9 冒号后所引巴门尼德译文整体缺失（疑内容损失）——待原书"},
    {"ch": 7, "issue": "块21/22 之间疑有几何图版脱漏；块19 说话人名'枚农'丢失（已按报告修复与否见changes）"},
    {"ch": 8, "issue": "Stephanus 页码（59A-118A 共44处）为原书边码入文，按原书面貌保留；损坏变体（19%/93.A）按报告修复"},
    {"ch": 5, "issue": "块22 末'（此处译稿有缺失。——编者）'与 ch6 末'（译文到此中断。——编者）'为原书固有状态"},
    {"ch": 13, "issue": "Loeb 边码 18-66 贯穿全章并拆词——边码入文体例，拆词处已按报告修复；希腊语拉丁乱码成片（ἐστί→Eut 等）待专项"},
    {"ch": 15, "issue": "章末截断（'…合在一起，它'无编者按）——原书/数字化边界待核"},
    {"ch": 16, "issue": "块96 封底版权杂质块未删（含定价信息，删除需确认）；俄文乱码（у меня есть книга等）与希腊字母表块88-89 全毁——待专项；严复术语'大择/内瘤/外'疑当作'大演/内籀/外籀'存疑未改"},
    {"ch": 10, "issue": "页眉'4.20 柏拉图对话集'（一处作拍）与 ch14 页眉插断两处、ch16 页码插断——按报告修复；坏间/魅尔魅若/爱若/诚人君子 存疑未改"},
]
p.apply(OPS)
errs = p.validate()
print("validate:", errs or "PASS")
out = p.ledger(extra={"scope": "ch0-16 两报告核定：页缝合并+形近字+标点+译名统一+杂符清理；原书脚注整体丢失与成片希腊/俄文乱码单列专项",
                      "skipped": skipped_stats})
p.sync_dev_mirror()
print(f"OK repl={p.replacements} para={p.paragraph_fixes} removed={p.pollution_removed}")
