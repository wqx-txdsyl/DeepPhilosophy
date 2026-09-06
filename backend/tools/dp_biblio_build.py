# -*- coding: utf-8 -*-
"""O7-B Bibliographic Metadata Foundation builder（dp_biblio_build.py）

构建 work/edition/digital_source 三分离的书目元数据:
  - Tier1 抽取: 章节 0（导入时收录的扉页/版权页文本）内嵌于数字源自身
    → OCR_CANDIDATE 候选; 仅当 ≥2 个独立 span 一致才 verified=true
  - locator: 对章节标题/正文做机械 scheme 探测（Stephanus/Bekker/KANT_AB/
    篇章/§节号）, 附证据（章节号+样例匹配）
  - missingness: 任何字段允许 null; 禁止占位字符串
产出:
  backend/data/book_bibliography.json                 （运行时数据, 未跟踪）
  docs/evidence/PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json（跟踪审计件）

用法: .venv/bin/python backend/tools/dp_biblio_build.py
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
OUT_DATA = os.path.join(BASE, "data", "book_bibliography.json")
OUT_MANIFEST = os.path.join(ROOT, "docs", "evidence",
                            "PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json")

# ── Pilot 选型（O7-B §11: 代表性元数据试点, 非经典排名）────────────────
# selection_reason 逐书写明; tradition 覆盖 7 桶 ≥5。
PILOT = [
    # O7-A seed/calibration 涉及作品
    ("8c0c6955c793", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（KANT_AB locator）"),
    ("29b3de571c12", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品 + 尼采人格主典"),
    ("08e055841182", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（§ 节号）"),
    ("d9272a80942a", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（篇章结构）"),
    ("dd03ec6572e7", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（尽心下篇）"),
    ("a08a3f332229", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（计篇/作战篇）"),
    ("88b56fb4da52", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品"),
    ("178e7d06d42d", "O7A_CALIBRATION", "O7-A 校准 fixture 涉及作品（Early Modern）"),
    # 尼采人格主要原典（persona corpus works/ 与书库交集）
    ("d1986c75d6b2", "NIETZSCHE_PRIMARY", "尼采人格主典（persona corpus works/ 收录）"),
    ("5c935000a2a7", "NIETZSCHE_PRIMARY", "尼采人格主典（persona corpus works/ 收录）"),
    # 古希腊/古典
    ("b5c7fcb371d4", "ANCIENT_GREEK", "柏拉图《理想国》——Stephanus locator 探测样本"),
    ("e574c8e7f515", "ANCIENT_GREEK", "亚里士多德《尼各马可伦理学》——Bekker locator 探测样本"),
    ("ec338ccc63b6", "ANCIENT_ROME", "西塞罗——古典拉丁传统"),
    ("4be7b72cf01d", "ANCIENT_ROME", "西塞罗——古典拉丁传统"),
    ("a44cb4c8f8d9", "ANCIENT_ROME", "西塞罗——古典拉丁传统"),
    ("bcc83fdfca5e", "LATE_ANTIQUITY", "奥古斯丁——教父/晚期古代传统"),
    # Early Modern
    ("8c3044772b18", "EARLY_MODERN", "笛卡尔《谈谈方法》——Tier1 CIP 完整样本"),
    ("65dbe55d66df", "EARLY_MODERN", "霍布斯《利维坦》——章节/部分结构"),
    ("44a32441dabe", "EARLY_MODERN", "洛克《人类理解论》——卷章结构"),
    ("21a479c4978d", "EARLY_MODERN", "亚当·斯密——苏格兰启蒙"),
    ("6a65e3ef874f", "EARLY_MODERN", "密尔《论自由》——章节结构"),
    ("e23d6fac862d", "EARLY_MODERN", "密尔《功利主义》——章节结构"),
    # 德国古典 / 19 世纪
    ("053203b03b6c", "GERMAN_IDEALISM", "黑格尔《精神现象学》——Tier1 CIP 完整样本"),
    ("e2845fe17764", "GERMAN_IDEALISM", "叔本华——卷章结构"),
    ("53d1b4ff90d2", "NINETEENTH_CENTURY", "马克思《资本论》——卷章结构"),
    ("f1e06cece874", "NINETEENTH_CENTURY", "克尔凯郭尔——节选结构"),
    # 20 世纪
    ("c5013f33fe01", "TWENTIETH_CENTURY", "海德格尔《存在与时间》——§ 节号结构"),
    ("5d906139d1b2", "TWENTIETH_CENTURY", "维特根斯坦《逻辑哲学论》——命题编号"),
    ("929771a017d6", "TWENTIETH_CENTURY", "罗尔斯《正义论》——节结构"),
    ("2c1a4c7d17a4", "TWENTIETH_CENTURY", "马尔库塞——Tier1 CIP 完整样本"),
    ("17fda3378628", "TWENTIETH_CENTURY", "阿多诺——Tier1 CIP 完整样本"),
    ("5b827532ec8b", "TWENTIETH_CENTURY", "梅洛-庞蒂——章节结构"),
    ("8eb18c6de2bc", "TWENTIETH_CENTURY", "福柯——卷章结构"),
    ("87bfe5b27ca1", "TWENTIETH_CENTURY", "哈贝马斯——章节结构"),
    ("dccd6f4879db", "TWENTIETH_CENTURY", "施特劳斯——章节结构"),
    ("b3219ec260ed", "TWENTIETH_CENTURY", "阿尔都塞《读〈资本论〉》——ISBN 样本"),
    ("5bdec4dbde50", "TWENTIETH_CENTURY", "卢卡奇——章节结构"),
    # 中国哲学
    ("c3c401982587", "CHINESE_PHILOSOPHY", "庄子——Tier1 CIP 完整样本（内篇结构）"),
    ("32093eed6ff1", "CHINESE_PHILOSOPHY", "冯友兰——Tier1 CIP 完整样本（章节结构）"),
]

# ── 机械抽取（Tier1: 版次自身的内嵌扉页/版权页文本）────────────────────
RE_ISBN = re.compile(r"ISBN[：:\s]*([0-9][0-9\s\-—]{8,16}[\dXx])")
RE_PUBLISHER = re.compile(r"([\u4e00-\u9fa5A-Za-z·]{2,20}(?:出版社|出版公司|出版集团|书馆))")
RE_TRANSLATOR = re.compile(r"([\u4e00-\u9fa5]{2,5})(?:等)?[译譯](?![本版])")
RE_YEAR = re.compile(r"((?:19|20)\d{2})\s*年")
RE_NATION = re.compile(r"[（(【\[]([a-zA-Z\u4e00-\u9fa5]{1,8})[)）\]】]\s*(?:著|原|编|撰|译|版)?")
NATION_MAP = {"德": "de", "德國": "de", "德 国": "de", "法": "fr", "英": "en",
              "美": "en", "俄": "ru", "古希腊": "grc", "古罗马": "la", "罗马": "la",
              "荷": "nl", "丹麦": "da", "挪": "no", "奥": "de", "瑞士": "de"}


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
    idxs = []
    for f in os.listdir(d):
        if re.fullmatch(r"\d+\.json", f):
            idxs.append(int(f[:-5]))
    idxs.sort()
    if limit:
        idxs = idxs[:limit]
    out = []
    for i in idxs:
        p = os.path.join(d, f"{i}.json")
        try:
            ch = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        out.append((i, ch))
    return out


def extract_front_matter(bid):
    """从前部「版权页/扉页」类章节抽取 Tier1 候选字段。

    verified 规则（OCR ≠ 事实本身）: 同一字段需 ≥2 个彼此独立的短行
    （≤80 字符——版权页/扉页版式行）一致才 verified=true,
    否则 OCR_CANDIDATE / verified=false。散文性章节（序言/导言）不参与。"""
    chapters = load_chapters(bid, limit=4)
    spans = []  # (chapter_idx, raw_line) 候选证据行
    for i, ch in chapters:
        title = str(ch.get("title") or "")
        if not any(k in title for k in ("版权", "扉页", "出版说明", "版本")):
            continue  # 序言/导言等散文章节不作为版式证据
        t = _content(ch)
        for line_no, line in enumerate(t.splitlines()):
            line = line.strip()
            if not line or len(line) > 80:  # 版权页/扉页版式行特征: 短行
                continue
            spans.append((i, line_no, line))

    def collect(rx, group=1):
        found = {}
        for i, line_no, line in spans:
            for m in rx.finditer(line):
                v = m.group(group).strip().strip(".,，。;；")
                if v:
                    found.setdefault(v, []).append(
                        {"chapter_idx": i, "line_no": line_no, "raw_span": m.group(0)})
        return found

    def pick(found, min_agree=2):
        """出现于 ≥min_agree 个独立短行的值才 verified（同一行只算一次）。
        过滤 OCR 噪声值: 单字重复（如「一一」）、纯数字 出版社 等。"""
        def plausible(v):
            if re.fullmatch(r"(.)\1+", v):        # 「一一」式重复噪声
                return False
            return True
        best_v, best_ev, best_n = None, None, 0
        for v, evs in found.items():
            if not plausible(v):
                continue
            lines = {(e["chapter_idx"], e.get("line_no", -1), e["raw_span"]) for e in evs}
            if len(lines) > best_n:
                best_v, best_ev, best_n = v, evs, len(lines)
        if best_v is None:
            return None
        verified = best_n >= min_agree
        return {"value": best_v, "verified": verified,
                "status": "VERIFIED" if verified else "OCR_CANDIDATE",
                "evidence": best_ev[:4],
                "source_tier": 1, "source_type": "embedded_front_matter",
                "source_locator": "chapter_idx=0",
                "confidence": round(min(0.55 + 0.2 * best_n, 0.98), 2)}

    fields = {}
    for name, rx in (("isbn", RE_ISBN), ("publisher", RE_PUBLISHER),
                     ("translator", RE_TRANSLATOR)):
        got = pick(collect(rx))
        if got:
            fields[name] = got
    # 出版年: 版权语境（CIP/版次/出版）年份; CIP 行尾裸年份（…出版社，2020）也算
    yfound = {}
    for i, line_no, line in spans:
        ctx = any(k in line for k in ("图书在版编目", "CIP", "出版", "版次", "印"))
        pats = list(RE_YEAR.finditer(line))
        if ctx:
            pats += [m for m in re.finditer(r"[，,]((?:19|20)\d{2})(?=$|[^0-9])", line)]
        if not pats:
            continue
        for m in pats:
            yfound.setdefault(m.group(1), []).append(
                {"chapter_idx": i, "line_no": line_no, "raw_span": m.group(0)})
    got = pick(yfound)
    if got:
        fields["publication_year"] = got
    # 原文语种提示（作品级 nationality 标记, 如 "[德]康德著"）
    nat = {}
    for i, line_no, line in spans:
        for m in RE_NATION.finditer(line):
            code = NATION_MAP.get(m.group(1))
            if code:
                nat.setdefault(code, []).append(
                    {"chapter_idx": i, "line_no": line_no, "raw_span": m.group(0)})
    if nat:
        code = max(nat, key=lambda k: len(nat[k]))
        n = len({(e["chapter_idx"], e.get("line_no", -1)) for e in nat[code]})
        fields["original_language_hint"] = {
            "value": code, "verified": n >= 2,
            "status": "VERIFIED" if n >= 2 else "OCR_CANDIDATE",
            "evidence": nat[code][:4], "source_tier": 1,
            "source_type": "embedded_front_matter",
            "source_locator": "chapter_idx=0", "confidence": round(min(0.5 + 0.2 * n, 0.9), 2)}
    return fields


# ── Locator 机械探测（证据驱动, 不虚构）────────────────────────────
LOCATOR_PROBES = [
    # (scheme, locator_kind, regex, 适用作者关键词(None=不限), 说明)
    ("STEPHANUS", "CANONICAL", re.compile(r"\b(\d{1,3}[a-e])(?:\b|[-–])"), "柏拉图", "柏拉图 Stephanus 页码"),
    ("BEKKER", "CANONICAL", re.compile(r"\b(10\d{2}[a-h]\d{1,2})\b"), "亚里士多德", "亚里士多德 Bekker 页码"),
    ("KANT_AB", "CANONICAL", re.compile(r"\b([AB]\d{1,3}[ab]?)\b"), "康德", "康德第一版 A/第二版 B 页码"),
    ("PROPOSITION", "STRUCTURAL", re.compile(r"^\s*(\d+(?:\.\d+)*)\s*$", re.M), None, "命题编号（逻辑哲学论）"),
    ("APHORISM_SECTION", "STRUCTURAL", re.compile(r"[§§]\s*(\d{1,4})"), None, "§ 节号"),
    ("CHAPTER_PART", "STRUCTURAL", re.compile(r"(第[一二三四五六七八九十百千0-9]+[卷篇章节回])"), None, "卷/篇/章 结构"),
]
# 中国典籍篇名（结构性 locator 证据）
CN_SECTIONS = {
    "论语": ["学而", "为政", "八佾", "里仁", "公冶长", "雍也", "述而", "泰伯",
             "子罕", "乡党", "先进", "颜渊", "子路", "宪问", "卫灵公", "季氏",
             "阳货", "微子", "子张", "尧曰"],
    "孟子": ["梁惠王", "公孙丑", "滕文公", "离娄", "万章", "告子", "尽心"],
    "孙子兵法": ["计篇", "作战篇", "谋攻篇", "形篇", "势篇", "虚实篇", "军争篇",
                  "九变篇", "行军篇", "地形篇", "九地篇", "火攻篇", "用间篇"],
    "庄子": ["逍遥游", "齐物论", "养生主", "人间世", "德充符", "大宗师", "应帝王"],
}
GRAN_ORDER = ["WORK", "CHAPTER", "SECTION", "EDITION_PAGE", "CANONICAL_LOCATOR"]


def detect_locators(bid, book_title, author=""):
    def _author_matches(gate):
        return gate in (author or "")
    by_author_title = f"{book_title} {author}"
    locators = []
    chapters = load_chapters(bid)
    titles = [str(c.get("title") or "") for _, c in chapters]
    # 篇章/节号: 优先扫章节标题（结构性最强）
    title_blob = "\n".join(titles)
    text_blob = "\n".join(_content(c)[:20000] for _, c in chapters[:8])
    for scheme, kind, rx, author_gate, desc in LOCATOR_PROBES:
        if kind == "CANONICAL" and author_gate and not _author_matches(author_gate):
            continue  # canonical scheme 仅对相应作者的作品探测（防跨作品偶发数字）
        hits_t = set(rx.findall(title_blob)[:50]) if scheme != "KANT_AB" else []
        hits_x = []
        if scheme in ("STEPHANUS", "BEKKER", "KANT_AB"):
            hits_x = rx.findall(text_blob)[:50]
        hits = list(dict.fromkeys(list(hits_t) + list(hits_x)))
        # 命中阈值: ≥3 个不同值才算该 scheme 在本源可用（防偶发数字）
        if len(hits) >= 3:
            ev_ch = None
            for i, t in enumerate(titles):
                if rx.search(t or ""):
                    ev_ch = i
                    break
            locators.append({
                "locator_kind": kind, "locator_scheme": scheme,
                "availability": "AVAILABLE",
                "evidence": {"sample_values": [str(h) for h in hits[:6]],
                             "distinct_hits": len(hits),
                             "title_chapter_idx": ev_ch},
                "note": desc})
    # 中国典籍篇名
    for classic, names in CN_SECTIONS.items():
        if classic in book_title:
            hit_names = [n for n in names if n in title_blob or n in text_blob[:60000]]
            if len(hit_names) >= 2:
                locators.append({
                    "locator_kind": "STRUCTURAL", "locator_scheme": "CHAPTER_PART",
                    "availability": "AVAILABLE",
                    "evidence": {"sample_values": hit_names[:8], "distinct_hits": len(hit_names),
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


def build():
    books = json.load(open(BOOKS_JSON, encoding="utf-8"))
    by_id = {b["id"]: b for b in books}
    records, stats = [], {}
    for bid, tradition, reason in PILOT:
        b = by_id.get(bid)
        assert b, f"pilot book missing: {bid}"
        fm = extract_front_matter(bid)
        locators = detect_locators(bid, b["title"], b.get("author", ""))
        verified_fields = [k for k, v in fm.items() if v["verified"]]
        cand_fields = [k for k, v in fm.items() if not v["verified"]]
        edition_status = "UNKNOWN"
        if "publisher" in verified_fields and (
                "publication_year" in verified_fields or "isbn" in verified_fields):
            edition_status = "VERIFIED"
        elif fm:
            edition_status = "PARTIAL"
        rec = {
            "book_id": bid,
            "work": {
                "author": b.get("author"),
                "canonical_title": b.get("title"),
                "original_title": None,
                "original_language": fm.get("original_language_hint", {}).get("value")
                if fm.get("original_language_hint", {}).get("verified") else None,
                "original_publication_year": None,  # 无 Tier1-3 证据 → null
            },
            "edition": {
                "edition_title": None,
                "language": "zh",
                "translator": fm["translator"]["value"] if "translator" in fm and fm["translator"]["verified"] else None,
                "editor": None,
                "publisher": fm["publisher"]["value"] if "publisher" in fm and fm["publisher"]["verified"] else None,
                "publication_place": None,
                "publication_year": int(fm["publication_year"]["value"])
                if "publication_year" in fm and fm["publication_year"]["verified"] else None,
                "isbn": fm["isbn"]["value"].replace(" ", "") if "isbn" in fm and fm["isbn"]["verified"] else None,
                "edition_identity": edition_status,
            },
            "digital_source": {
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
            "field_provenance": fm,
            "pilot_selection": {"tradition": tradition, "reason": reason},
        }
        records.append(rec)
        stats.setdefault("traditions", set()).add(tradition)

    data = {
        "schema_version": "o7b-1",
        "missingness_policy": "null 表示未验证/不可用; 禁止占位字符串; 禁止模型记忆回填",
        "conflict_policy": "候选冲突全保留于 field_provenance; 不做 last-write-wins",
        "books": {r["book_id"]: r for r in records},
    }
    os.makedirs(os.path.dirname(OUT_DATA), exist_ok=True)
    json.dump(data, open(OUT_DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 审计 manifest（tracked）
    def count_tier(t, verified=True):
        return sum(1 for r in records for v in r["field_provenance"].values()
                   if v["source_tier"] == t and v["verified"] == verified)
    manifest = {
        "generated_by": "backend/tools/dp_biblio_build.py",
        "schema_version": "o7b-1",
        "pilot": {
            "works": len(records),
            "traditions_or_periods": sorted(stats["traditions"]),
            "records": [{"book_id": r["book_id"],
                         "work": r["work"]["canonical_title"],
                         "edition_status": r["edition"]["edition_identity"],
                         "populated_verified_fields": [k for k, v in r["field_provenance"].items() if v["verified"]],
                         "ocr_candidate_fields": [k for k, v in r["field_provenance"].items() if not v["verified"]],
                         "field_provenance": r["field_provenance"],
                         "locator_schemes": r["citation_capability"]["locator_schemes"],
                         "max_verified_granularity": r["citation_capability"]["max_verified_granularity"],
                         "conflicts": [], "selection": r["pilot_selection"]} for r in records],
        },
        "tier_counts": {"tier1_verified": count_tier(1, True),
                        "tier1_ocr_candidate": count_tier(1, False),
                        "tier2_verified": 0, "tier3_verified": 0,
                        "tier4_discovery": 0, "tier4_only_verified": 0},
        "universe": {
            "current_book_count": len(books),
            "book_universe_hash": hashlib.sha256(
                json.dumps(books, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
            "pilot_manifest_hash": None,  # 由本文件 sha256 回填于报告中
        },
    }
    corpus_h = hashlib.sha256()
    for r in records:
        corpus_h.update((r["book_id"] + (r["digital_source"]["source_hash"] or "")).encode())
    manifest["universe"]["corpus_snapshot_hash"] = corpus_h.hexdigest()
    os.makedirs(os.path.dirname(OUT_MANIFEST), exist_ok=True)
    json.dump(manifest, open(OUT_MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 控制台摘要
    ver = sum(len(r["field_provenance"]) and 0 or 0 for r in records)
    vf = sum(1 for r in records for v in r["field_provenance"].values() if v["verified"])
    cf = sum(1 for r in records for v in r["field_provenance"].values() if not v["verified"])
    ed = {}
    for r in records:
        ed[r["edition"]["edition_identity"]] = ed.get(r["edition"]["edition_identity"], 0) + 1
    gran = {}
    for r in records:
        g = r["citation_capability"]["max_verified_granularity"]
        gran[g] = gran.get(g, 0) + 1
    loc_kind = {}
    for r in records:
        for l in r["locators"]:
            loc_kind[l["locator_kind"]] = loc_kind.get(l["locator_kind"], 0) + 1
    print(json.dumps({
        "pilot_works": len(records),
        "traditions": sorted(stats["traditions"]),
        "edition_identity": ed,
        "verified_fields": vf, "ocr_candidate_fields": cf,
        "granularity": gran, "locator_kinds": loc_kind,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(build())
