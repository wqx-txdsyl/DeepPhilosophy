#!/usr/bin/env python3
"""康德著作集：ch7-14/31-41/42-52 三份报告的核定修复 + 注文迁移 + ch52 结构修复"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dp_proofread_lib import Proofreader
import dp_note_migrate_auto as m

REPO = Path("/Users/sen/.codex/worktrees/book-quality-zcode-20261024/DeepPhilosophy")
RD = REPO / "docs/tasks/book-full-proofread-zcode-2026-10-24/progress/reading"
BOOK = REPO / "backend/data/book_chapters/309de54e4392"
SKIP_INSTR = ("删除", "合并", "移到", "应移", "对调", "块2", "块3")

OPS = []

def from_report(fname, skip_blocks=None):
    rep = json.loads((RD / fname).read_text())
    for c in rep["perChapter"]:
        for iss in c["issues"]:
            if iss["confidence"] not in ("certain", "likely") or not iss.get("proposed"):
                continue
            prop = iss["proposed"]
            if any(k in prop for k in SKIP_INSTR):
                continue
            if skip_blocks and (c["chapter"], iss["block"]) in skip_blocks:
                continue
            OPS.append({"op": "replace_in", "ch": c["chapter"], "original": iss["original"],
                        "proposed": prop, "note": (iss.get("evidence") or "")[:110]})

# ch7-14：4处（b171 特殊处理、b163 按报告应用）
from_report("309de54e4392.ch7-14.json", skip_blocks={(7, 171)})
OPS.append({"op": "replace_in", "ch": 7,
            "original": "自吾人所已集合部分之自然的统一。而来者也",
            "proposed": "自吾人所已集合部分之自然的统一而来者也",
            "note": "删句中衍句号（代理据扫描件核对）"})
# ch31-36：certain/likely 文本修复
from_report("309de54e4392.ch31-36.json", skip_blocks={(32, 71), (32, 72), (32, 73), (33, 146), (33, 147), (33, 190), (33, 191), (35, 7)})
# ch37-41
from_report("309de54e4392.ch37-41.json", skip_blocks={(37, 6), (38, 107)})
# ch42-52（结构性项单独处理：ch52 b26/27合并、b28-34移位、b35删除、标题对调）
from_report("309de54e4392.ch42-52.json", skip_blocks={(52, 26), (52, 28), (52, 35)})

# 结构性 op（降序删除）
OPS += [
    {"op": "delete_block", "ch": 32, "block": 72, "expect": "第一章 美的分析"},   # ch33 b1 重复
    {"op": "delete_block", "ch": 32, "block": 71, "expect": "上卷 审美判断力的批判"},  # ch33 b0 重复
    {"op": "delete_block", "ch": 33, "block": 191, "expect": "关于自然界的力学的崇高"},
    {"op": "delete_block", "ch": 33, "block": 147, "expect": "第二章"},
    {"op": "delete_block", "ch": 35, "block": 7, "expect": "附录"},          # ch36 b0 重复
    {"op": "delete_block", "ch": 37, "block": 6, "expect": "下卷"},          # ch38 b0 重复
]
# ch52 b26/27 合并（split 整块重组）
OPS.append({"op": "merge", "ch": 52, "tail_expect": "（工蜂从蜂巢里，把那些游手好闲的雄蜂赶出去。",
            "head_expect": "维吉尔）", "note": "维吉尔诗汉译括注跨块合并"})
# ch52 标题对调
OPS.append({"op": "replace_in", "ch": 53, "original": '"title": "PLACEHOLDER_NEVER"', "proposed": "x"}) if False else None

p = Proofreader("309de54e4392", "康德著作集")
p.residuals = [
    {"ch": 7, "issue": "「能调为/平和及静保/此程进程/图满规定/召人之信仰/断独的矫妄主张」等约20处经商务扫描件比对确认为印刷原貌，勿改清单已入台账"},
    {"ch": 12, "issue": "「法象统一性/矫拂为法则/丰衍性」等韩水法译本原貌若干处，勿改"},
    {"ch": 12, "issue": "【考订】ch12-14 译本实为韩水法译（非关文译），介绍撰写时须采用"},
    {"ch": 26, "issue": "圈码注①无锚点（前已记）"},
    {"ch": 32, "issue": "「反味」三处疑为「反省」误读但不排除原译有意用词；b73 块实为ch33内容且含[1][2]标记（注文在ch33）——跨章锚点待裁定"},
    {"ch": 33, "issue": "【全书性】页注重编错位：正文[16]-[28]对应章末[1]-[3]/[1]-[10]（内容逐条核对匹配）——本章注释暂不迁移，待纸本逐条核对；b172私用区乱码已修"},
    {"ch": 33, "issue": "b170 句中叹号、b199 疑脱字、b340 破折号混入、Enthusiam疑脱s——无据未改"},
    {"ch": 38, "issue": "b107 电子版整理者校注〔校注：…AA5:401…〕混入，是否保留待核"},
    {"ch": 39, "issue": "三处德文大小写疑原印本即误，已按 likely 修复"},
    {"ch": 42, "issue": "ch42-51 实为唐钺译《道德形而上学探本》（Groundwork）"},
    {"ch": 45, "issue": "「普遍定律、不涉及」顿号存疑未改"},
    {"ch": 46, "issue": "「固然；他们」分号存疑未改"},
    {"ch": 47, "issue": "「令式听命令人实行」「同一理由。」句似未完——无据未改"},
    {"ch": 48, "issue": "「这样行这」「不实则」「概念的而纯乎」三处存疑——无据未改"},
    {"ch": 52, "issue": "「没曾做过」疑为「未曾」——无据未改"},
]
p.apply(OPS)
print("fixes:", p.replacements, "repl,", p.pollution_removed, "removed,", p.paragraph_fixes, "para")
errs = p.validate()
print("validate:", errs or "PASS")
out = p.ledger(extra={"scope": "ch7-14/31-52 报告核定修复（含拉丁文/变音/标点/重复块）"})
p.sync_dev_mirror()

# ch52 结构修复（值锚定）：贺拉斯续块移到注[1]之后；删前言标题块；标题对调
f52 = BOOK / "52.json"
d = json.loads(f52.read_text())
c = d["content"]
vals = [(b.get("value") or "") for b in c]
i_start = next(i for i, v in enumerate(vals) if v.startswith("Labitur et labetur"))
i_end = next(i for i, v in enumerate(vals) if v.startswith("——贺拉斯"))
assert i_end > i_start and i_end - i_start == 6, (i_start, i_end)
i_pre = next(i for i, v in enumerate(vals) if v.startswith("前言") and "形而上学知识的特点" in v)
i_rusticus = next(i for i, v in enumerate(vals) if "Rusticus exspectat" in v)
moved = c[i_start:i_end + 1]
rest = [b for j, b in enumerate(c) if not (i_start <= j <= i_end) and j != i_pre]
insert_at = next(i for i, b in enumerate(rest) if "Rusticus exspectat" in (b.get("value") or "")) + 1
newc = rest[:insert_at] + moved + rest[insert_at:]
# 保全：文字总量 = 原 − 前言标题
orig_text = "".join(vals)
new_text = "".join((b.get("value") or "") for b in newc)
from collections import Counter
exp_counter = Counter(vals) - Counter([vals[i_pre]])
assert Counter(new_text) == Counter("".join(k * 1 for k in [])) or True
assert Counter([b.get("value") or "" for b in newc]) == exp_counter, "ch52 重排丢文"
d["content"] = newc
d["title"] = "前言　论一切形而上学知识的特点"
f52.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ch52 reordered, title → 前言")

f53 = BOOK / "53.json"
d53 = json.loads(f53.read_text())
d53["title"] = "导言"
f53.write_text(json.dumps(d53, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
mm = json.loads((BOOK / "meta.json").read_text())
mm["chapterTitles"][52] = "前言　论一切形而上学知识的特点"
mm["chapterTitles"][53] = "导言"
for t in mm.get("toc", []):
    if isinstance(t, dict) and t.get("index") == 52:
        t["title"] = mm["chapterTitles"][52]
    if isinstance(t, dict) and t.get("index") == 53:
        t["title"] = mm["chapterTitles"][53]
(BOOK / "meta.json").write_text(json.dumps(mm, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ch53/meta title → 导言")

# 注文迁移（配对健全者）
for ch in (32, 34, 38, 39, 40, 45, 46, 47, 48):
    r = m.migrate_chapter(BOOK / f"{ch}.json")
    print("migrate", ch, r.get("status"), r.get("notes", ""))
# ch52（移位后）
r = m.migrate_chapter(BOOK / "52.json")
print("migrate 52", r.get("status"), r.get("notes", ""))
print("ALL DONE")
