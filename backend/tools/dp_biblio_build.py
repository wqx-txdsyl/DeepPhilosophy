# -*- coding: utf-8 -*-
"""O7-B Bibliographic Metadata Foundation builder（dp_biblio_build.py）

O7-B RP1（2026-09-06）重写核心:
  - 语义边界抽取: 「译」后必须是行尾/标点/空白, 不得紧跟 文/本/版/丛/书/社
    （kill case: 上海译文出版社 → 上海译 → translator=上海, 已冻结为 R1 回归）
  - 冲突模型: 每字段 candidates[] 全保留; ≥2 个 eligible 异值 → CONFLICT_UNRESOLVED
    → production 字段 null; 禁止 majority-wins
  - 年份语义分类: EDITION_YEAR(第N版) / CIP_BIBLIOGRAPHIC_YEAR(CIP 行尾) /
    PRINTING_YEAR(第N次印刷, 不支持 edition year) / CIP_REGISTRATION(核字, 不支持)
  - 国籍 ≠ 原文语种: author_nationality_hint 仅非模型面向提示;
    work.original_language 只能来自明确语言事实（本库暂无 → null）
  - 实体 identity: work_id / edition_record_id / digital_source_id
  - 可复现: 输出文件含 builder_hash / source_snapshot_hash / pilot_manifest_hash,
    无时间戳, 确定性重建

产出:
  backend/data/book_bibliography.json（RP1 起为 git 跟踪的 production reference data）
  docs/evidence/PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json

用法: .venv/bin/python backend/tools/dp_biblio_build.py
      .venv/bin/python backend/tools/dp_biblio_build.py --out <path>   （重建比对用）
"""
import hashlib
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE)
CHAPTERS = os.path.join(BASE, "data", "book_chapters")
BOOKS_JSON = os.path.join(ROOT, "app", "public", "books.json")
DEFAULT_OUT_DATA = os.path.join(BASE, "data", "book_bibliography.json")
OUT_MANIFEST = os.path.join(ROOT, "docs", "evidence",
                            "PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json")

# ── Pilot 选型（O7-B §11; RP1 §3 全量 39 书重建）──────────────────────
PILOT = [
    ("8c0c6955c793", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（KANT_AB locator）"),
    ("29b3de571c12", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品 + 尼采人格主典"),
    ("08e055841182", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（§ 节号）"),
    ("d9272a80942a", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（篇章结构）"),
    ("dd03ec6572e7", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（尽心下篇）"),
    ("a08a3f332229", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（计篇/作战篇）"),
    ("88b56fb4da52", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品"),
    ("178e7d06d42d", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（Early Modern）"),
    ("d1986c75d6b2", "NIETZSCHE_PRIMARY", "尼采人格主典（persona corpus works/ 收录）"),
    ("5c935000a2a7", "NIETZSCHE_PRIMARY", "尼采人格主典（persona corpus works/ 收录）"),
    ("b5c7fcb371d4", "ANCIENT_GREEK", "柏拉图《理想国》——Stephanus locator 探测样本"),
    ("e574c8e7f515", "ANCIENT_GREEK", "亚里士多德《尼各马可伦理学》——Bekker locator 探测样本"),
    ("ec338ccc63b6", "ANCIENT_ROME", "西塞罗——古典拉丁传统"),
    ("4be7b72cf01d", "ANCIENT_ROME", "西塞罗——古典拉丁传统"),
    ("a44cb4c8f8d9", "ANCIENT_ROME", "西塞罗——古典拉丁传统"),
    ("bcc83fdfca5e", "LATE_ANTIQUITY", "奥古斯丁——教父/晚期古代传统"),
    ("8c3044772b18", "EARLY_MODERN", "笛卡尔《谈谈方法》——Tier1 CIP 完整样本"),
    ("65dbe55d66df", "EARLY_MODERN", "霍布斯《利维坦》——章节/部分结构"),
    ("44a32441dabe", "EARLY_MODERN", "洛克《人类理解论》——卷章结构"),
    ("21a479c4978d", "EARLY_MODERN", "亚当·斯密——苏格兰启蒙"),
    ("6a65e3ef874f", "EARLY_MODERN", "密尔《论自由》——章节结构"),
    ("e23d6fac862d", "EARLY_MODERN", "密尔《功利主义》——章节结构"),
    ("053203b03b6c", "GERMAN_IDEALISM", "黑格尔《精神现象学》——Tier1 CIP 完整样本"),
    ("e2845fe17764", "GERMAN_IDEALISM", "叔本华——卷章结构"),
    ("53d1b4ff90d2", "NINETEENTH_CENTURY", "马克思《资本论》——卷章结构"),
    ("f1e06cece874", "NINETEENTH_CENTURY", "克尔凯郭尔——节选结构"),
    ("2c1a4c7d17a4", "TWENTIETH_CENTURY", "马尔库塞——RP1 kill case（刘继译/上海译文出版社）"),
    ("c5013f33fe01", "TWENTIETH_CENTURY", "海德格尔《存在与时间》——§ 节号结构"),
    ("5d906139d1b2", "TWENTIETH_CENTURY", "维特根斯坦《逻辑哲学论》——命题编号"),
    ("929771a017d6", "TWENTIETH_CENTURY", "罗尔斯《正义论》——节结构"),
    ("17fda3378628", "TWENTIETH_CENTURY", "阿多诺——Tier1 CIP 完整样本"),
    ("5b827532ec8b", "TWENTIETH_CENTURY", "梅洛-庞蒂——章节结构"),
    ("8eb18c6de2bc", "TWENTIETH_CENTURY", "福柯——卷章结构"),
    ("87bfe5b27ca1", "TWENTIETH_CENTURY", "哈贝马斯——章节结构"),
    ("dccd6f4879db", "TWENTIETH_CENTURY", "施特劳斯——章节结构"),
    ("b3219ec260ed", "TWENTIETH_CENTURY", "阿尔都塞《读〈资本论〉》——ISBN 样本"),
    ("5bdec4dbde50", "TWENTIETH_CENTURY", "卢卡奇——章节结构"),
    ("c3c401982587", "CHINESE_PHILOSOPHY", "庄子——Tier1 CIP 完整样本（内篇结构）"),
    ("32093eed6ff1", "CHINESE_PHILOSOPHY", "冯友兰——Tier1 CIP 完整样本（章节结构）"),
]

# ── 机械抽取（Tier1: 版次自身内嵌的版权页/扉页文本, RP1 语义边界版）────
# ISBN: 「ISBN 978-7-208-16251-8」行 —— ISBN_STATEMENT 语义
RE_ISBN = re.compile(r"ISBN[：:\s]*([0-9][0-9\s\-—]{8,16}[\dXx])")
# 出版社名 —— PUBLISHER_STATEMENT 语义
RE_PUBLISHER = re.compile(r"([\u4e00-\u9fa5A-Za-z·]{2,20}(?:出版社|出版公司|出版集团|书馆))")
# 责任者: 「刘继译」「卫茂平 译」「涂又光译」「某某等译」
#   语义边界（RP1 §2）: 「译」后必须是行尾/标点/空白/引号,
#   不得紧跟 文/本/版/丛/书/社（否则命中「上海译文出版社」「修订译本」等）
RE_TRANSLATOR = re.compile(
    r"([\u4e00-\u9fa5]{2,4})\s?(?:等)?[译譯](?![文本版丛书社])(?=$|[\s.,，。;；:：．·—\-、）)”])")
# 原文题名陈述: 「书名原文：Asthetische Theorie」
RE_ORIG_TITLE = re.compile(r"书名原文[：:]\s*(\S.{1,80})")
RE_NATION = re.compile(r"[（(【\[]([a-zA-Z\u4e00-\u9fa5]{1,8})[)）\]】]\s*(?:著|原|编|撰|译|版)?")
NATION_MAP = {"德": "de", "法": "fr", "英": "en", "美": "en", "俄": "ru",
              "古希腊": "grc", "古罗马": "la", "罗马": "la", "荷": "nl",
              "丹麦": "da", "挪": "no", "奥": "de-at", "瑞士": "de-ch"}
# 年份语义分类
RE_EDITION_YEAR = re.compile(r"((?:19|20)\d{2})\s*年[^，。;；]{0,12}第[一二三四五六七八九十0-9]+版")
RE_PRINTING_YEAR = re.compile(r"((?:19|20)\d{2})\s*年[^，。;；]{0,12}第[一二三四五六七八九十百0-9]+次印刷")
RE_CIP_TAIL_YEAR = re.compile(r"[，,]((?:19|20)\d{2})(?=$|[^0-9])")
RE_CIP_REG_YEAR = re.compile(r"核字[（(]((?:19|20)\d{2})[)）]")


def _content(ch):
    c = ch.get("content")
    if isinstance(c, list):
        parts = []
        for x in c:
            if isinstance(x, dict):
                parts.append(str(x.get("value") or x.get("text") or ""))
            else:
                parts.append(str(x))
        c = "\n".join(parts)
    return c or ""


def load_chapters(bid, limit=None):
    d = os.path.join(CHAPTERS, bid)
    if not os.path.isdir(d):
        return []
    idxs = sorted(int(f[:-5]) for f in os.listdir(d) if re.fullmatch(r"\d+\.json", f))
    if limit:
        idxs = idxs[:limit]
    out = []
    for i in idxs:
        try:
            out.append((i, json.load(open(os.path.join(d, f"{i}.json"), encoding="utf-8"))))
        except Exception:
            continue
    return out


def _front_spans(bid):
    """前部「版权页/扉页」类章节的短版式行 → [(chapter_idx, line_no, line)]。"""
    spans = []
    for i, ch in load_chapters(bid, limit=4):
        title = str(ch.get("title") or "")
        if not any(k in title for k in ("版权", "扉页", "出版说明", "版本")):
            continue
        for line_no, line in enumerate(_content(ch).splitlines()):
            line = line.strip()
            if line and len(line) <= 80:
                spans.append((i, line_no, line))
    return spans


def _plausible(v):
    return not re.fullmatch(r"(.)\1+", v or "")


def _mk_field(cands, eligible_values):
    """冲突模型字段（RP1 §5）。

    candidates: 全保留; eligible = ≥2 独立 (chapter,line) 证据行的值。
    ≥2 个互异 eligible 值 → CONFLICT_UNRESOLVED, selected=null, verified=false。
    恰 1 个 eligible → NO_CONFLICT, selected=该值, verified=true。
    无 eligible 但有候选 → NO_CONFLICT, selected=null, verified=false（OCR_CANDIDATE）。
    """
    conflict = False
    if len(eligible_values) >= 2:
        conflict = True
    if conflict:
        return {"candidates": cands, "selected_value": None,
                "resolution_status": "CONFLICT_UNRESOLVED", "resolution_basis": None,
                "verified": False, "conflict": True}
    if eligible_values:
        v = eligible_values[0]
        cand = next(c for c in cands if c["value"] == v)
        return {"candidates": cands, "selected_value": v,
                "resolution_status": "NO_CONFLICT", "resolution_basis": None,
                "verified": True, "conflict": False,
                "confidence": round(min(0.6 + 0.15 * cand["n_spans"], 0.97), 2)}
    return {"candidates": cands, "selected_value": None,
            "resolution_status": "NO_CONFLICT", "resolution_basis": None,
            "verified": False, "conflict": False}


def _collect_rx(spans, rx, semantic_class):
    """按值聚合候选; n_spans = 独立 (chapter,line) 行数（同行多命中算 1）。"""
    found = {}
    for i, ln, line in spans:
        seen_in_line = set()
        for m in rx.finditer(line):
            v = m.group(1).strip().strip(".,，。;；")
            if v and v not in seen_in_line:
                seen_in_line.add(v)
                found.setdefault(v, []).append(
                    {"chapter_idx": i, "line_no": ln, "raw_span": m.group(0),
                     "semantic_source_type": semantic_class})
    return found


def _field_from_found(found, min_spans=2):
    cands = [{"value": v, "evidence": ev,
              "semantic_source_type": ev[0]["semantic_source_type"],
              "n_spans": len({(e["chapter_idx"], e["line_no"]) for e in ev})}
             for v, ev in sorted(found.items(), key=lambda kv: -len({(e['chapter_idx'], e['line_no']) for e in kv[1]}))
             if _plausible(v)]
    eligible = [c["value"] for c in cands if c["n_spans"] >= min_spans]
    return _mk_field(cands, eligible)


def extract_front_matter(bid):
    """Tier1 抽取（RP1 语义版）。verified = NO_CONFLICT 且 selected 非空。"""
    spans = _front_spans(bid)
    fields = {}
    for name, rx, cls in (("isbn", RE_ISBN, "ISBN_STATEMENT"),
                          ("publisher", RE_PUBLISHER, "PUBLISHER_STATEMENT"),
                          ("translator", RE_TRANSLATOR, "RESPONSIBILITY_STATEMENT"),
                          ("original_title", RE_ORIG_TITLE, "ORIGINAL_TITLE_STATEMENT")):
        f = _field_from_found(_collect_rx(spans, rx, cls))
        if f["candidates"]:
            fields[name] = f

    # 出版年: 语义分类, 只有 EDITION_YEAR / CIP_BIBLIOGRAPHIC_YEAR 支持 edition year
    year_cands = {}
    def add_year(v, ev):
        year_cands.setdefault(v, []).append(ev)
    for i, ln, line in spans:
        for m in RE_PRINTING_YEAR.finditer(line):
            add_year(m.group(1), {"chapter_idx": i, "line_no": ln,
                                  "raw_span": m.group(0),
                                  "semantic_source_type": "PRINTING_YEAR"})
        for m in RE_EDITION_YEAR.finditer(line):
            add_year(m.group(1), {"chapter_idx": i, "line_no": ln,
                                  "raw_span": m.group(0),
                                  "semantic_source_type": "EDITION_YEAR"})
        if "图书在版编目" in line or ("出版社" in line and "核字" not in line):
            for m in RE_CIP_TAIL_YEAR.finditer(line):
                add_year(m.group(1), {"chapter_idx": i, "line_no": ln,
                                      "raw_span": m.group(0),
                                      "semantic_source_type": "CIP_BIBLIOGRAPHIC_YEAR"})
        for m in RE_CIP_REG_YEAR.finditer(line):
            add_year(m.group(1), {"chapter_idx": i, "line_no": ln,
                                  "raw_span": m.group(0),
                                  "semantic_source_type": "CIP_REGISTRATION_YEAR"})
    if year_cands:
        cands = []
        for v, ev in sorted(year_cands.items(), key=lambda kv: -len(kv[1])):
            spans_per_v = {}
            for e in ev:
                spans_per_v.setdefault((e["chapter_idx"], e["line_no"]), e)
            cands.append({"value": v,
                          "evidence": list(spans_per_v.values()),
                          "semantic_source_type": "/".join(sorted({e["semantic_source_type"] for e in ev})),
                          "n_spans": len(spans_per_v)})
        # RP1 §6/C5/C6: EDITION_YEAR 与 CIP_BIBLIOGRAPHIC_YEAR 是同一事实
        # （版次出版年）的两种陈述——两类间异值即 CONFLICT_UNRESOLVED（不限 span 数,
        # 防「2020 出现两次就静默赢」）; PRINTING/CIP_REGISTRATION 年不参与。
        elig_classes = ("EDITION_YEAR", "CIP_BIBLIOGRAPHIC_YEAR")
        distinct = sorted({c["value"] for c in cands
                           if any(e["semantic_source_type"] in elig_classes
                                  for e in c["evidence"])})
        if len(distinct) >= 2:
            fields["publication_year"] = _mk_field(cands, distinct)
        else:
            eligible = [c["value"] for c in cands
                        if len({(e["chapter_idx"], e["line_no"]) for e in c["evidence"]
                                if e["semantic_source_type"] in elig_classes}) >= 2]
            fields["publication_year"] = _mk_field(cands, eligible)

    # 作者国籍提示（非模型面向; ≠ work.original_language, RP1 §4）
    nat = {}
    for i, ln, line in spans:
        for m in RE_NATION.finditer(line):
            code = NATION_MAP.get(m.group(1))
            if code:
                nat.setdefault(code, []).append(
                    {"chapter_idx": i, "line_no": ln, "raw_span": m.group(0),
                     "semantic_source_type": "AUTHOR_NATIONALITY_HINT"})
    if nat:
        code = max(nat, key=lambda k: len(nat[k]))
        fields["author_nationality_hint"] = {
            "candidates": [{"value": code, "evidence": nat[code][:4],
                            "semantic_source_type": "AUTHOR_NATIONALITY_HINT",
                            "n_spans": len({(e["chapter_idx"], e["line_no"]) for e in nat[code]})}],
            "selected_value": None, "resolution_status": "NO_CONFLICT",
            "resolution_basis": None, "verified": False, "conflict": False}
    return fields


# ── Locator 机械探测（证据驱动; canonical 按作者门控）──────────────────
LOCATOR_PROBES = [
    ("STEPHANUS", "CANONICAL", re.compile(r"\b(\d{1,3}[a-e])(?:\b|[-–])"), "柏拉图", "柏拉图 Stephanus 页码"),
    ("BEKKER", "CANONICAL", re.compile(r"\b(10\d{2}[a-h]\d{1,2})\b"), "亚里士多德", "亚里士多德 Bekker 页码"),
    ("KANT_AB", "CANONICAL", re.compile(r"\b([AB]\d{1,3}[ab]?)\b"), "康德", "康德第一版 A/第二版 B 页码"),
    ("PROPOSITION", "STRUCTURAL", re.compile(r"^\s*(\d+(?:\.\d+)*)\s*$", re.M), None, "命题编号（逻辑哲学论）"),
    ("APHORISM_SECTION", "STRUCTURAL", re.compile(r"[§§]\s*(\d{1,4})"), None, "§ 节号"),
    ("CHAPTER_PART", "STRUCTURAL", re.compile(r"(第[一二三四五六七八九十百千0-9]+[卷篇章节回])"), None, "卷/篇/章 结构"),
]
CN_SECTIONS = {
    "论语": ["学而", "为政", "八佾", "里仁", "公冶长", "雍也", "述而", "泰伯",
             "子罕", "乡党", "先进", "颜渊", "子路", "宪问", "卫灵公", "季氏",
             "阳货", "微子", "子张", "尧曰"],
    "孟子": ["梁惠王", "公孙丑", "滕文公", "离娄", "万章", "告子", "尽心"],
    "孙子兵法": ["计篇", "作战篇", "谋攻篇", "形篇", "势篇", "虚实篇", "军争篇",
                  "九变篇", "行军篇", "地形篇", "九地篇", "火攻篇", "用间篇"],
    "庄子": ["逍遥游", "齐物论", "养生主", "人间世", "德充符", "大宗师", "应帝王"],
}


def detect_locators(bid, book_title, author=""):
    def _author_matches(gate):
        return gate in (author or "")
    locators = []
    chapters = load_chapters(bid)
    titles = [str(c.get("title") or "") for _, c in chapters]
    title_blob = "\n".join(titles)
    text_blob = "\n".join(_content(c)[:20000] for _, c in chapters[:8])
    for scheme, kind, rx, author_gate, desc in LOCATOR_PROBES:
        if kind == "CANONICAL" and author_gate and not _author_matches(author_gate):
            continue
        hits_t = set(rx.findall(title_blob)[:50]) if scheme != "KANT_AB" else []
        hits_x = rx.findall(text_blob)[:50] if scheme in ("STEPHANUS", "BEKKER", "KANT_AB") else []
        hits = list(dict.fromkeys(list(hits_t) + list(hits_x)))
        if len(hits) >= 3:
            ev_ch = next((i for i, t in enumerate(titles) if rx.search(t or "")), None)
            locators.append({"locator_kind": kind, "locator_scheme": scheme,
                             "availability": "AVAILABLE",
                             "evidence": {"sample_values": [str(h) for h in hits[:6]],
                                          "distinct_hits": len(hits),
                                          "title_chapter_idx": ev_ch},
                             "note": desc})
    for classic, names in CN_SECTIONS.items():
        if classic in book_title:
            hit_names = [n for n in names if n in title_blob or n in text_blob[:60000]]
            if len(hit_names) >= 2:
                locators.append({"locator_kind": "STRUCTURAL",
                                 "locator_scheme": "CHAPTER_PART",
                                 "availability": "AVAILABLE",
                                 "evidence": {"sample_values": hit_names[:8],
                                              "distinct_hits": len(hit_names),
                                              "title_chapter_idx": None},
                                 "note": f"{classic} 传统篇名（{classic}篇目体系）"})
    return locators


def max_granularity(locators):
    kinds = {l["locator_kind"] for l in locators}
    if "CANONICAL" in kinds:
        return "CANONICAL_LOCATOR"
    if any(l["locator_scheme"] in ("APHORISM_SECTION", "PROPOSITION") for l in locators):
        return "SECTION"
    return "CHAPTER"


def source_hash(bid):
    d = os.path.join(CHAPTERS, bid)
    h = hashlib.sha256()
    files = sorted(f for f in os.listdir(d) if re.fullmatch(r"(\d+|meta)\.json", f)) \
        if os.path.isdir(d) else []
    for f in files:
        h.update(f.encode())
        h.update(open(os.path.join(d, f), "rb").read())
    return h.hexdigest() if files else None


def _sel(fields, name):
    """production 值: NO_CONFLICT 且 verified 才有值; 冲突/未验证 → null。"""
    f = fields.get(name)
    if f and f.get("verified") and not f.get("conflict"):
        return f["selected_value"]
    return None


def build(out_data=None):
    out_data = out_data or DEFAULT_OUT_DATA
    books = json.load(open(BOOKS_JSON, encoding="utf-8"))
    by_id = {b["id"]: b for b in books}
    records, traditions = [], set()
    for bid, tradition, reason in PILOT:
        b = by_id.get(bid)
        assert b, f"pilot book missing: {bid}"
        fm = extract_front_matter(bid)
        locators = detect_locators(bid, b["title"], b.get("author", ""))
        author = (b.get("author") or "").strip()
        work_id = "work-" + hashlib.sha256(
            (author + "|" + b["title"]).encode()).hexdigest()[:12]
        has_conflict = any(v.get("conflict") for v in fm.values())
        verified_publisher = _sel(fm, "publisher") is not None
        verified_year = _sel(fm, "publication_year") is not None
        verified_isbn = _sel(fm, "isbn") is not None
        if has_conflict:
            edition_status = "PARTIAL" if fm else "UNKNOWN"
        elif verified_publisher and (verified_year or verified_isbn):
            edition_status = "VERIFIED"
        elif fm:
            edition_status = "PARTIAL"
        else:
            edition_status = "UNKNOWN"
        yr = _sel(fm, "publication_year")
        records.append({
            "book_id": bid,
            "work_id": work_id,                       # 内部实体 identity（RP1 §8）
            "edition_record_id": "ed-" + bid,
            "digital_source_id": "ds-" + bid,
            "work": {
                "author": b.get("author"),
                "canonical_title": b.get("title"),
                "original_title": _sel(fm, "original_title"),
                "original_language": None,   # 国籍≠语种; 本库无明确语言事实 → null
                "original_publication_year": None,
            },
            "edition": {
                "edition_title": None,
                "language": "zh",
                "translator": _sel(fm, "translator"),
                "editor": None,
                "publisher": _sel(fm, "publisher"),
                "publication_place": None,
                "publication_year": int(yr) if yr else None,
                "isbn": (_sel(fm, "isbn") or "").replace(" ", "") or None,
                "edition_identity": edition_status,
            },
            "digital_source": {
                "digital_source_id": "ds-" + bid,
                "source_type": b.get("file_type"),
                "source_file_ref": f"backend/data/book_chapters/{bid}/",
                "source_hash": source_hash(bid),
                "provenance": "dp_pdf_import/dp_epub_ocr 导入管线（章节 JSON 为唯一本地数字源）",
            },
            "locators": locators,
            "citation_capability": {
                "max_verified_granularity": max_granularity(locators),
                "locator_schemes": [l["locator_scheme"] for l in locators],
            },
            "field_provenance": fm,          # 含 candidates[]/resolution_status 全量
            "pilot_selection": {"tradition": tradition, "reason": reason},
        })
        traditions.add(tradition)

    builder_hash = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    corpus_h = hashlib.sha256()
    for r in records:
        corpus_h.update((r["book_id"] + (r["digital_source"]["source_hash"] or "")).encode())
    universe_h = hashlib.sha256(
        json.dumps(books, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    data = {
        "schema_version": "o7b-2",
        "builder_hash": builder_hash,
        "source_snapshot_hash": corpus_h.hexdigest(),
        "book_universe_hash": universe_h,
        "pilot_manifest_hash": None,  # 写 manifest 后回填
        "missingness_policy": "null 表示未验证/不可用; 禁止占位字符串; 禁止模型记忆回填",
        "conflict_policy": "candidates 全保留; ≥2 eligible 异值 → CONFLICT_UNRESOLVED → production null; 禁止 majority-wins",
        "books": {r["book_id"]: r for r in records},
    }
    os.makedirs(os.path.dirname(out_data), exist_ok=True)
    json.dump(data, open(out_data, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 审计 manifest（tracked）
    manifest = {
        "generated_by": "backend/tools/dp_biblio_build.py",
        "schema_version": "o7b-2",
        "builder_hash": builder_hash,
        "pilot": {
            "works": len(records),
            "traditions_or_periods": sorted(traditions),
            "records": [{"book_id": r["book_id"],
                         "work_id": r["work_id"],
                         "edition_record_id": r["edition_record_id"],
                         "digital_source_id": r["digital_source_id"],
                         "work": r["work"]["canonical_title"],
                         "edition_status": r["edition"]["edition_identity"],
                         "populated_verified_fields": [k for k, v in r["field_provenance"].items()
                                                       if v.get("verified") and not v.get("conflict")],
                         "ocr_candidate_fields": [k for k, v in r["field_provenance"].items()
                                                   if not v.get("verified") and k != "author_nationality_hint"],
                         "conflict_fields": [k for k, v in r["field_provenance"].items() if v.get("conflict")],
                         "field_provenance": r["field_provenance"],
                         "locator_schemes": r["citation_capability"]["locator_schemes"],
                         "max_verified_granularity": r["citation_capability"]["max_verified_granularity"],
                         "selection": r["pilot_selection"]} for r in records],
        },
        "tier_counts": {
            "tier1_verified": sum(1 for r in records for v in r["field_provenance"].values()
                                  if v.get("verified") and not v.get("conflict")
                                  and k_tier1(v)),
            "tier1_ocr_candidate": sum(1 for r in records for k, v in r["field_provenance"].items()
                                       if not v.get("verified") and k != "author_nationality_hint"),
        },
        "universe": {"current_book_count": len(books),
                     "book_universe_hash": universe_h,
                     "corpus_snapshot_hash": corpus_h.hexdigest()},
    }
    os.makedirs(os.path.dirname(OUT_MANIFEST), exist_ok=True)
    json.dump(manifest, open(OUT_MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 回填 manifest hash（语义内容: 去掉回填字段本身）
    data["pilot_manifest_hash"] = hashlib.sha256(open(OUT_MANIFEST, "rb").read()).hexdigest()
    json.dump(data, open(out_data, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    vf = sum(1 for r in records for v in r["field_provenance"].values()
             if v.get("verified") and not v.get("conflict"))
    cf = sum(1 for r in records for v in r["field_provenance"].values() if v.get("conflict"))
    ed = {}
    for r in records:
        ed[r["edition"]["edition_identity"]] = ed.get(r["edition"]["edition_identity"], 0) + 1
    print(json.dumps({"pilot_works": len(records), "traditions": sorted(traditions),
                      "edition_identity": ed, "verified_fields": vf,
                      "conflict_fields": cf}, ensure_ascii=False, indent=1))


def k_tier1(v):
    return True


if __name__ == "__main__":
    out = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--out":
        out = sys.argv[2]
    sys.exit(build(out))
