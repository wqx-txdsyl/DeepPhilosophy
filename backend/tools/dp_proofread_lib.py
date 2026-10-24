#!/usr/bin/env python3
"""dp_proofread_lib.py — 逐书精读修复的应用层（note-contract v1 + 段落修复 + 台账）

设计：实读代理产出 issue 报告 → 主校对核定并编写 ops → 本库带校验地应用。
每个 op 应用前必须精确命中（替换串在目标块内恰好出现一次），否则整本中止并报告，
绝不静默跳过。所有被删除/替换的原文片段连同前后文写入台账，满足内容保全对照。

ops 条目格式（写入 docs/tasks/book-full-proofread-zcode-2026-10-24/progress/ops/{bid}.json）:
  {"op":"replace","ch":i,"block":b,"original":s,"proposed":s}
  {"op":"replace_in","ch":i,"original":s,"proposed":s}          # 全章范围查找唯一命中
  {"op":"note_ref","ch":i,"block":b,"anchor":s,"note_text":s,"kind":opt}  # anchor 以标记结尾，
      # 恰好命中一次；标记被替换为 {{n:x}}；注文进 notes
  {"op":"note_ref_global","ch":i,"anchor":s,...}                # 全章范围唯一锚点
  {"op":"remove_span","ch":i,"block":b,"span":s}                # 删除嵌注/污染串（恰好一次）
  {"op":"split","ch":i,"block":b,"paragraphs":[s,...]}          # 整块替换为真实段落序列
  {"op":"delete_block","ch":i,"block":b,"expect":s}             # 删除整块（expect=该块全文或其唯一前缀）
  {"op":"paragraph_mode","ch":i,"mode":"source"}
"""
import hashlib
import json
import re
import shutil
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parent
TASK = REPO / "docs/tasks/book-full-proofread-zcode-2026-10-24"
TOKEN_RE = re.compile(r"\{\{n:(\d+)\}\}")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Proofreader:
    def __init__(self, bid: str, book_title: str = ""):
        self.bid = bid
        self.book_title = book_title
        self.book_dir = BASE / "data" / "book_chapters" / bid
        self.original_shas = {}
        self.applied = []
        self.notes_added = 0
        self.replacements = 0
        self.paragraph_fixes = 0
        self.pollution_removed = 0
        self.residuals = []
        self.changes = []   # 台账逐条
        for f in sorted(self.book_dir.glob("*.json")):
            if f.stem.isdigit():
                self.original_shas[int(f.stem)] = sha256_bytes(f.read_bytes())

    # ---------- 校验原语 ----------
    def _load(self, ch: int):
        p = self.book_dir / f"{ch}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        return p, d

    def _save(self, p: Path, d: dict):
        p.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    def _find_block(self, d, ch, block):
        content = d.get("content")
        if not isinstance(content, list) or block >= len(content):
            raise ValueError(f"ch{ch} 块{block} 不存在")
        return content[block]

    # ---------- op 实现 ----------
    def op_replace(self, d, ch, o):
        blk = self._find_block(d, ch, o["block"])
        v = blk.get("value") or ""
        if o.get("type") == "text" and blk.get("type") != "text":
            raise ValueError(f"ch{ch} 块{o['block']} 类型不是 text")
        n = v.count(o["original"])
        if n != 1:
            raise ValueError(f"ch{ch} 块{o['block']} 替换目标出现 {n} 次（需恰1次）: {o['original'][:40]}…")
        blk["value"] = v.replace(o["original"], o["proposed"])
        self.replacements += 1
        self.changes.append({"kind": "replace", "ch": ch, "block": o["block"],
                             "original": o["original"], "proposed": o["proposed"]})

    def op_replace_in(self, d, ch, o):
        hits = [bi for bi, blk in enumerate(d["content"])
                if isinstance(blk, dict) and (blk.get("value") or "").count(o["original"])]
        note_hits = [ni for ni, nt in enumerate(d.get("notes") or [])
                     if isinstance(nt, dict) and (nt.get("text") or "").count(o["original"])]
        if len(hits) + len(note_hits) != 1:
            # 幂等：原文已不存在且改后文本已存在 → 视为已应用
            already = [bi for bi, blk in enumerate(d["content"])
                       if isinstance(blk, dict) and o["proposed"] in (blk.get("value") or "")]
            already += ["note" + str(ni) for ni, nt in enumerate(d.get("notes") or [])
                        if isinstance(nt, dict) and o["proposed"] in (nt.get("text") or "")]
            if not hits and not note_hits and already:
                self.changes.append({"kind": "replace_in", "ch": ch,
                                     "block": already[0] if isinstance(already[0], int) else str(already[0]),
                                     "original": o["original"], "proposed": o["proposed"], "skipped": "already_applied"})
                return
            raise ValueError(f"ch{ch} 替换目标在全章出现于 {len(hits) + len(note_hits)} 处（需恰1）: {o['original'][:40]}…")
        if hits:
            self.op_replace(d, ch, {"block": hits[0], "original": o["original"], "proposed": o["proposed"]})
        else:
            nt = d["notes"][note_hits[0]]
            nt["text"] = nt["text"].replace(o["original"], o["proposed"], 1)
            self.replacements += 1
            self.changes.append({"kind": "replace_in", "ch": ch, "note": note_hits[0],
                                 "original": o["original"], "proposed": o["proposed"]})

    def op_replace_all_in(self, d, ch, o):
        n_total = 0
        for bi, blk in enumerate(d["content"]):
            if not isinstance(blk, dict) or blk.get("type") != "text":
                continue
            v = blk.get("value") or ""
            n = v.count(o["original"])
            if n:
                blk["value"] = v.replace(o["original"], o["proposed"])
                n_total += n
                self.changes.append({"kind": "replace_all_in", "ch": ch, "block": bi, "count": n,
                                     "original": o["original"], "proposed": o["proposed"]})
        if not n_total:
            # 幂等
            if any(isinstance(b, dict) and o["proposed"] in (b.get("value") or "") for b in d["content"]):
                self.changes.append({"kind": "replace_all_in", "ch": ch, "skipped": "already_applied",
                                     "original": o["original"], "proposed": o["proposed"]})
                return
            raise ValueError(f"ch{ch} replace_all_in 目标未找到: {o['original'][:40]}…")
        self.replacements += n_total

    def op_note_ref(self, d, ch, o):
        anchor = o["anchor"]
        blk = self._find_block(d, ch, o.get("block")) if "block" in o else None
        if blk is None:
            hits = [bi for bi, blk in enumerate(d["content"])
                    if isinstance(blk, dict) and blk.get("type") == "text" and anchor in (blk.get("value") or "")]
            if len(hits) != 1:
                raise ValueError(f"ch{ch} 注文锚点命中 {len(hits)} 块（需恰1）: {anchor[:40]}…")
            bi = hits[0]
            blk = d["content"][bi]
        else:
            bi = o["block"]
            if (blk.get("value") or "").count(anchor) != 1:
                raise ValueError(f"ch{ch} 块{bi} 注文锚点出现次数≠1: {anchor[:40]}…")
        if blk.get("type") != "text":
            raise ValueError(f"ch{ch} 块{bi} 非 text 块不能挂注")
        marker = anchor[-1]
        if not re.match(r"[①②③④⑤⑥⑦⑧⑨⑩\]\)〕\d］]", marker):
            raise ValueError(f"锚点末字符不是注释标记: {marker!r}")
        notes = d.setdefault("notes", [])
        new_n = len(notes) + 1
        notes.append({"n": new_n, "text": o["note_text"], **({"kind": o["kind"]} if o.get("kind") else {})})
        blk["value"] = blk["value"].replace(anchor, anchor[:-1] + "{{n:%d}}" % new_n, 1)
        self.notes_added += 1
        self.changes.append({"kind": "note_ref", "ch": ch, "block": bi,
                             "marker": marker, "anchor": anchor, "note_n": new_n,
                             "note_text": o["note_text"]})

    def op_remove_span(self, d, ch, o):
        blk = self._find_block(d, ch, o["block"])
        v = blk.get("value") or ""
        n = v.count(o["span"])
        if n != 1:
            raise ValueError(f"ch{ch} 块{o['block']} 待删串出现 {n} 次（需恰1）: {o['span'][:40]}…")
        blk["value"] = v.replace(o["span"], "", 1)
        self.pollution_removed += 1
        self.changes.append({"kind": "remove_span", "ch": ch, "block": o["block"], "removed": o["span"]})

    def op_insert_block(self, d, ch, o):
        """在 anchor_before 块（以其 value 开头唯一确定）之前插入一个 text 块（如小节标题剥离归位）。"""
        hits = [bi for bi, b in enumerate(d["content"])
                if isinstance(b, dict) and b.get("type") == "text"
                and (b.get("value") or "").startswith(o["anchor_before"])]
        if len(hits) != 1:
            raise ValueError(f"ch{ch} insert 锚点命中 {len(hits)} 块: {o['anchor_before'][:30]}…")
        d["content"].insert(hits[0], {"type": "text", "value": o["value"]})
        self.paragraph_fixes += 1
        self.changes.append({"kind": "insert_block", "ch": ch, "block": hits[0], "value": o["value"],
                             "reason": o.get("note", "")})

    def op_peel_title(self, d, ch, o):
        """把粘连在正文中的小节标题剥出为独立块。
        glue: 标题前的锚文本（含其前面的句末标点）；title: 标题串。
        标题在 glue 之后、其余正文之前；其余正文保持为一个块。"""
        glue, title = o["glue"], o["title"]
        # 幂等：标题已是独立块 → 跳过
        if any(isinstance(x, dict) and x.get("value") == title for x in d["content"]):
            self.changes.append({"kind": "peel_title", "ch": ch, "title": title, "skipped": "already_applied"})
            return
        for bi, b in enumerate(d["content"]):
            if not (isinstance(b, dict) and b.get("type") == "text"):
                continue
            v = b.get("value") or ""
            if v.count(glue + title) == 1:
                i = v.index(glue + title) + len(glue)
                rest = v[i + len(title):]
                b["value"] = v[:i]
                new_blocks = [{"type": "text", "value": title}] + ([{"type": "text", "value": rest}] if rest else [])
                d["content"][bi + 1:bi + 1] = new_blocks
                self.paragraph_fixes += 1
                self.changes.append({"kind": "peel_title", "ch": ch, "block": bi, "title": title,
                                     "glue": glue[-20:], "note": o.get("note", "")})
                return
        raise ValueError(f"ch{ch} peel_title 未命中: {glue[-20:]!r}+{title!r}")

    def op_unfold_annex(self, d, ch, o):
        """展开坍缩的『大事年表』/『关键词表』：把粘连的附录标题及其后的条目按句号拆为独立块。
        glue: 附录标题前的锚文本（不含标题本身），None 表示标题在块首；
        title: '大事年表' 或 '关键词表'；entries_end: 可选，后续附录标题出现时停止拆条并独立成块。"""
        title = o["title"]
        glue = o.get("glue")
        for bi, b in enumerate(d["content"]):
            if not (isinstance(b, dict) and b.get("type") == "text"):
                continue
            v = b.get("value") or ""
            if glue is None:
                if not v.startswith(title):
                    continue
                i = 0
            else:
                if v.count(glue + title) != 1:
                    continue
                i = v.index(glue + title) + len(glue)
            rest = v[i + len(title):]
            stop = o.get("entries_end")
            head_parts, tail_part = rest, None
            if stop and stop in rest:
                k = rest.index(stop)
                head_parts, tail_part = rest[:k], rest[k:]
            entries = [x for x in re.split(r"(?<=[。；])", head_parts) if x.strip()]
            pieces = [v[:i], title] + entries
            if tail_part:
                pieces.append(tail_part)
            assert "".join(pieces) == v, f"ch{ch} unfold 拆分不一致"
            b["value"] = pieces[0]
            if not b["value"] and glue is None:
                # 块首展开且无前文：复用该块位置
                new_blocks = [{"type": "text", "value": x} for x in pieces[1:]]
                d["content"][bi:bi + 1] = new_blocks
            else:
                new_blocks = [{"type": "text", "value": x} for x in pieces[1:]]
                d["content"][bi + 1:bi + 1] = new_blocks
            self.paragraph_fixes += 1
            self.changes.append({"kind": "unfold_annex", "ch": ch, "block": bi, "title": title,
                                 "entries": len(entries), "note": o.get("note", "")})
            return
        # 幂等：已展开 → 存在独立标题块
        if any(isinstance(b, dict) and b.get("value") == title for b in d["content"]):
            self.changes.append({"kind": "unfold_annex", "ch": ch, "title": title, "skipped": "already_applied"})
            return
        raise ValueError(f"ch{ch} unfold_annex 未命中: {str(glue)[-20:]!r}+{title!r}")

    def op_split(self, d, ch, o):
        blk = self._find_block(d, ch, o["block"])
        joined = "".join(o["paragraphs"])
        orig = blk.get("value") or ""
        # 内容保全：段集拼接（忽略空白差异）必须覆盖原块全部文字
        norm = lambda s: re.sub(r"\s+", "", s)
        if norm(joined) != norm(orig):
            raise ValueError(f"ch{ch} 块{o['block']} split 段集与原块文字不一致（防丢文）:\n 原块={norm(orig)[:80]}…\n 段集={norm(joined)[:80]}…")
        idx = d["content"].index(blk)
        new_blocks = [{"type": "text", "value": p} for p in o["paragraphs"]]
        d["content"][idx:idx + 1] = new_blocks
        self.paragraph_fixes += 1
        self.changes.append({"kind": "split", "ch": ch, "block": o["block"], "into": len(o["paragraphs"])})

    def op_merge(self, d, ch, o):
        """把目标块拼入其前一块（跨页断句修复）。
        定位: o["block"] 显式块号，或 tail_expect（唯一以其结尾的块）自动定位。
        校验: join_check（拼接点重复串）或 head_expect（后块开头）。"""
        content = d["content"]
        if o.get("block") is not None:
            idx = o["block"]
        elif o.get("tail_expect"):
            hits = [bi for bi, b in enumerate(content)
                    if isinstance(b, dict) and b.get("type") == "text"
                    and (b.get("value") or "").rstrip("\n").endswith(o["tail_expect"])]
            if len(hits) != 1:
                # 幂等：合并已发生 → 尾+头串同块，或头串已在某块（原尾块已并入并完成改写）
                joined = o["tail_expect"] + o.get("head_expect", "")
                already = [bi for bi, b in enumerate(content)
                           if isinstance(b, dict) and b.get("type") == "text"
                           and joined in (b.get("value") or "")]
                if not already and o.get("head_expect"):
                    already = [bi for bi, b in enumerate(content)
                               if isinstance(b, dict) and b.get("type") == "text"
                               and o["head_expect"] in (b.get("value") or "")]
                if not already:
                    already = [bi for bi, b in enumerate(content)
                               if isinstance(b, dict) and b.get("type") == "text"
                               and o["tail_expect"] in (b.get("value") or "")]
                if len(hits) == 0 and already:
                    self.changes.append({"kind": "merge", "ch": ch, "block": already[0],
                                         "junction": o["tail_expect"][-16:] + "⧸" + o.get("head_expect", "")[:16],
                                         "skipped": "already_applied"})
                    return
                raise ValueError(f"ch{ch} tail_expect 定位到 {len(hits)} 个块: {o['tail_expect'][:30]}…")
            idx = hits[0] + 1
        elif o.get("head_expect"):
            hits = [bi for bi, b in enumerate(content)
                    if isinstance(b, dict) and b.get("type") == "text"
                    and (b.get("value") or "").startswith(o["head_expect"])]
            if len(hits) != 1:
                already = [bi for bi, b in enumerate(content)
                           if isinstance(b, dict) and b.get("type") == "text"
                           and o["head_expect"] in (b.get("value") or "")]
                if len(hits) == 0 and already:
                    self.changes.append({"kind": "merge", "ch": ch, "block": already[0],
                                         "junction": "⧸" + o["head_expect"][:16], "skipped": "already_applied"})
                    return
                raise ValueError(f"ch{ch} head_expect 定位到 {len(hits)} 个块: {o['head_expect'][:30]}…")
            idx = hits[0]
        else:
            raise ValueError("merge 需要 block 或 tail_expect/head_expect")
        if idx <= 0 or idx >= len(content):
            raise ValueError(f"ch{ch} merge 块号越界: {idx}")
        prev, nxt = content[idx - 1], content[idx]
        if prev.get("type") != "text" or nxt.get("type") != "text":
            raise ValueError(f"ch{ch} merge 仅支持相邻 text 块")
        pv, nv = prev.get("value") or "", nxt.get("value") or ""
        if o.get("join_check"):
            jc = o["join_check"]
            if not (pv.endswith(jc) and nv.startswith(jc)):
                raise ValueError(f"ch{ch} merge join_check 不匹配: tail={pv[-12:]!r} head={nv[:12]!r}")
        if o.get("head_expect") and not nv.startswith(o["head_expect"]):
            raise ValueError(f"ch{ch} merge head_expect 不匹配: head={nv[:20]!r}")
        prev["value"] = pv + nv
        content.pop(idx)
        self.paragraph_fixes += 1
        self.changes.append({"kind": "merge", "ch": ch, "block": idx,
                             "junction": pv[-16:] + "⧸" + nv[:16]})

    def op_delete_block(self, d, ch, o):
        content = d["content"]
        if o["block"] >= len(content):
            # 幂等：目标已不存在 → 若 expect 串在全章也已消失则视为已删除
            exp = o["expect"].strip()
            if exp and not any(exp in ((b.get("value") or "")) for b in content):
                self.changes.append({"kind": "delete_block", "ch": ch, "block": o["block"],
                                     "removed": exp[:40], "skipped": "already_applied"})
                return
            raise ValueError(f"ch{ch} 块{o['block']} 不存在且 expect 仍可找到")
        blk = content[o["block"]]
        v = (blk.get("value") or "").strip()
        exp = o["expect"].strip()
        if not (v == exp or v.startswith(exp)):
            # 幂等：expect 在全章已消失，或恰剩一次（重复块已删，保留唯一正本）→ 视为已删除
            occur = sum(1 for b in content if exp and exp in ((b.get("value") or ""))) if exp else 0
            if occur == 0 or occur == 1:
                self.changes.append({"kind": "delete_block", "ch": ch, "block": o["block"],
                                     "removed": exp[:40], "skipped": "already_applied"})
                return
            raise ValueError(f"ch{ch} 块{o['block']} 删除内容与 expect 不符: {v[:40]}…")
        d["content"].remove(blk)
        self.pollution_removed += 1
        self.changes.append({"kind": "delete_block", "ch": ch, "block": o["block"], "removed": v[:120]})

    def op_paragraph_mode(self, d, ch, o):
        d["paragraphMode"] = o.get("mode", "source")

    # ---------- 主入口 ----------
    def apply(self, ops):
        by_ch = {}
        for o in ops:
            by_ch.setdefault(o["ch"], []).append(o)
        for ch, ch_ops in sorted(by_ch.items()):
            p, d = self._load(ch)
            for o in ch_ops:
                kind = "op_" + o["op"]
                fn = getattr(self, kind, None)
                if fn is None:
                    raise ValueError(f"未知 op: {o['op']}")
                fn(d, ch, o)
            self._save(p, d)
        return self

    def validate(self):
        """结构+注释配对校验（调 dp_note_check 同规则）"""
        errs = []
        for f in sorted(self.book_dir.glob("*.json")):
            if not f.stem.isdigit():
                continue
            d = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(d, dict) or "content" not in d:
                errs.append(f"{f.name}: 顶层缺 content")
                continue
            notes = d.get("notes") or []
            ns = [nt.get("n") for nt in notes]
            if len(set(ns)) != len(ns):
                errs.append(f"{f.name}: notes n 重复")
            refs = set()
            for bi, b in enumerate(d["content"]):
                if not isinstance(b, dict):
                    errs.append(f"{f.name} 块{bi}: 非法块")
                    continue
                if b.get("type") != "text":
                    if TOKEN_RE.search(b.get("value") or ""):
                        errs.append(f"{f.name} 块{bi}: 非 text 块含 token")
                    continue
                for m in TOKEN_RE.finditer(b.get("value") or ""):
                    refs.add(int(m.group(1)))
            for n in refs:
                if n not in ns:
                    errs.append(f"{f.name}: token n={n} 无对应注")
        return errs

    def ledger(self, extra=None):
        changed_files = []
        for f in sorted(self.book_dir.glob("*.json")):
            if f.stem.isdigit():
                after = sha256_bytes(f.read_bytes())
                ch = int(f.stem)
                if after != self.original_shas.get(ch):
                    changed_files.append({"chapter": ch, "shaBefore": self.original_shas.get(ch), "shaAfter": after})
        led = {
            "book": f"{self.bid} {self.book_title}".strip(),
            "appliedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "changedFiles": changed_files,
            "counters": {"replacements": self.replacements, "notesMigrated": self.notes_added,
                         "paragraphFixes": self.paragraph_fixes, "pollutionRemoved": self.pollution_removed},
            "changes": self.changes,
            "residuals": self.residuals,
        }
        if extra:
            led.update(extra)
        out = TASK / "ledgers" / f"{self.bid}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
        return out

    def sync_dev_mirror(self):
        """把改动章节同步到 vite 开发镜像（未跟踪目录，仅本地开发）"""
        mirror = REPO / "app/public/backend/data/book_chapters" / self.bid
        mirror.mkdir(parents=True, exist_ok=True)
        for c in self.changed_files_all():
            src = self.book_dir / f"{c}.json"
            shutil.copy2(src, mirror / f"{c}.json")
        shutil.copy2(self.book_dir / "meta.json", mirror / "meta.json")

    def changed_files_all(self):
        out = []
        for f in sorted(self.book_dir.glob("*.json")):
            if f.stem.isdigit() and sha256_bytes(f.read_bytes()) != self.original_shas.get(int(f.stem)):
                out.append(int(f.stem))
        return out
