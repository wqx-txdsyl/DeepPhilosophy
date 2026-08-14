# -*- coding: utf-8 -*-
"""
dp_ocr_check.py — OCR 入库质量核查清单（2026-08-07）
每本 OCR 完成后运行: python dp_ocr_check.py <bid>
按清单依次核对历史出现过的所有问题, 输出 ✓/✗ 报告。

清单（编号对应 OCR_CHECKLIST.md）:
  A1 章节数 > 1（整本 1 章 → 需手动分章）
  A2 每章段落数 ≥ 3（段落压扁检查 — 曾整章 1-2 大段）
  A3 每章字数 > 0（空文本检查 — 曾全新 OCR 书空文本）
  A4 首段不以章标题开头（标题拼进正文 — 曾"亚伯拉罕颂如果一个人…"）
  A5 跋/后记/附录块字数合理（曾跋=全部正文）
  B6 页眉页脚残留（首/尾行为书名/页码 — 跨页重复）
  B7 无 FAILED OCR 页（空页检查）
  B8 繁体书名书已转简体（拟仿物先例）
  C9 三端一致（PhiAgent / DP public / DP backend md5）
  C10 chapterCount 三处一致（books.json / book_detail / meta.json）
  C11 向量已重嵌（index 条目数 = chapterCount）
  C12 toc 类型正确（part 分组须组内有 chapter; 编/卷级应 chapter）
  C13 toc 无重复标题（曾 OCR 错字"间题/向题/同题"切 3 次）
  C16 section 锚点一致（type=section 条目的 sec 指向章内同名 text 块 — 分级标题）
"""
import sys, os, json, re, hashlib

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

PHI_CH = os.path.join(BASE, "data", "book_chapters")
PHI_DET = os.path.join(BASE, "data", "book_detail")
EMB = os.path.join(BASE, "data", "embeddings")
DP_PUBLIC = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")
CKPT = os.path.join(BASE, "data", "dp_pdf_import_ckpt.json")

SENT_END = "。！？；：”』」）】…—-"
# 页眉/页脚残留特征: 全数字页码行 / 书名式行
RE_PAGENUM = re.compile(r"^\d{1,6}$")
BODY_TITLE_WORDS = ("序", "前言", "引言", "导言", "绪论", "结语", "跋", "后记", "附录",
                    "目录", "参考文献", "出版说明", "译者序", "代序", "题记", "致谢",
                    "注释", "译注", "索引", "版本信息", "版权")


def md5dir(bd):
    h = hashlib.md5()
    for fn in sorted(os.listdir(bd)):
        h.update(fn.encode())
        h.update(open(os.path.join(bd, fn), "rb").read())
    return h.hexdigest()


def main(bid):
    report = []
    def check(no, name, ok, detail=""):
        report.append((no, name, ok, detail))
        print(f"  {no} [{('✓' if ok else '✗')}] {name} {detail}", flush=True)

    bd = os.path.join(PHI_CH, bid)
    if not os.path.exists(os.path.join(bd, "meta.json")):
        print(f"✗ book_chapters/{bid} 不存在", flush=True)
        return
    meta = json.load(open(os.path.join(bd, "meta.json"), encoding="utf-8"))
    nch = meta["chapterCount"]
    chs = []
    for i in range(nch):
        fp = os.path.join(bd, f"{i}.json")
        if os.path.exists(fp):
            chs.append(json.load(open(fp, encoding="utf-8")))

    # A1 章节数
    check("A1", "章节数", nch > 1, f"chapterCount={nch}")
    # A2 段落数（正文块 ≥3 段; 短块 <300 字豁免; 目录/版本信息/版权类块是列表性质豁免）
    para_ok = True
    min_para = None
    for ch in chs:
        ts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
        w = sum(len(t) for t in ts)
        is_list = any(kw in (ch["title"] or "") for kw in ("目录", "版本信息", "版权", "版權", "题词", "致谢", "索引", "导言"))
        # 短章白名单(人工确认内容完整): (bid, 章名, 段数, 字数)
        A2_KNOWN = {
            ("f11f1b13c278", "第七章", 2, 1113), ("f11f1b13c278", "第三章", 2, 697),
            ("f11f1b13c278", "第二十章、第二十一章", 2, 524), ("f11f1b13c278", "第二十五章", 2, 376),
            ("f11f1b13c278", "第三章", 2, 700), ("f11f1b13c278", "第二章", 2, 564),
            ("f11f1b13c278", "第七章", 2, 618), ("f11f1b13c278", "第十章", 2, 478),
            # 纯粹理性批判: 题辞=单页培根引文页(2026-08-08 重建后人工确认 2 段正常)
            ("8c0c6955c793", "题辞", 2, 326),
        }
        if w > 300 and len(ts) < 3 and not is_list and (bid, ch["title"], len(ts), w) not in A2_KNOWN:
            para_ok = False
            check("A2", "段落数", False, f"{ch['title'][:20]!r} {w}字 仅 {len(ts)} 段")
        elif min_para is None or len(ts) < min_para:
            min_para = len(ts)
    if para_ok:
        check("A2", "段落数", True, f"min={min_para}")
    # A3 空章节（含"只有标题行"的空块: 总字数 ≤ 标题+5 且 ≤50）
    empty = [ch["title"] for ch in chs
             if not [x for x in ch.get("content", []) if x.get("type") == "text"]]
    for ch in chs:
        ts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
        w = sum(len(x) for x in ts)
        t = ch["title"] or ""
        if ts and w <= len(t) + 5 and w <= 50:
            empty.append(ch["title"])
    check("A3", "无空章节", not empty, f"空章节={empty if empty else '无'}")
    # A4 首段不以章标题开头。注意: 标题独立成段（首段=标题行）是正常结构;
    # 真正的问题是标题与正文粘在同一段（剥离标题后仍有 ≥10 字正文）→ 报
    bad_head = []
    for ch in chs:
        ts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
        t = ch["title"] or ""
        if ts and t and len(t) >= 2:
            h = "".join(ts[0][:len(t) * 2].split())
            hh = "".join(t.split())
            if h.startswith(hh):
                rest = len("".join(ts[0].split())) - len(hh)
                if rest >= 10:
                    bad_head.append(t)
    check("A4", "首段无标题", not bad_head, f"命中={bad_head if bad_head else '无'}")
    # A5 跋/附录字数
    total_words = 0
    for ch in chs:
        ts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
        total_words += sum(len(t) for t in ts)
    tail_ok = True
    for ch in chs:
        if any(w in (ch["title"] or "") for w in ("跋", "后记", "附录", "版权")):
            ts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
            w = sum(len(t) for t in ts)
            if total_words and w > total_words * 0.15 and nch > 1:
                tail_ok = False
                check("A5", "尾块字数", False, f"{ch['title'][:16]!r} {w}字 占{100*w//total_words}%")
    if tail_ok:
        check("A5", "尾块字数", True, f"总量 {total_words} 字")

    # B6 页眉页脚残留
    header_ok = True
    for i, ch in enumerate(chs):
        ts = [x.get("value", "") for x in ch.get("content", []) if x.get("type") == "text"]
        for t in ts[:1]:
            first_line = t.strip().split("\n")[0][:20]
            if RE_PAGENUM.match(first_line.strip()):
                header_ok = False
                check("B6", "页眉页脚", False, f"块{i} 首行是页码 {first_line!r}")
    if header_ok:
        check("B6", "页眉页脚", True, "无页码残留")

    # B7 FAILED 页（只查当前书; 展示前后邻页内容供人工判断空白页 vs 丢内容）
    fails = []
    rel = None
    if os.path.exists(CKPT):
        ck = json.load(open(CKPT, encoding="utf-8"))
        for k, v in (ck.get("books") or {}).items():
            if hashlib.md5(k.encode()).hexdigest()[:12] == bid:
                rel = k
                break
        if rel:
            safe = re.sub(r"[^\w\-.]", "_", rel)
            ocr = (ck.get("ocr") or {}).get(safe, {})
            for k, v in sorted(ocr.items(), key=lambda x: int(x[0])):
                if v == "__FAILED__":
                    i = int(k)
                    # 语义连续性: 前邻页末尾 22 字 + 后邻页开头 22 字（前页末半句/后页首半句 = 丢正文）
                    prev_t = "".join((ocr.get(str(i - 1)) or "").split())[-22:]
                    next_t = "".join((ocr.get(str(i + 1)) or "").split())[:22]
                    fails.append(f"页{k} 前末[{prev_t}] 后首[{next_t}]")
    if fails:
        print("  B7 [⚠] FAILED 页（请人工判断: 前/后邻页有内容且 FAILED 页为篇间页 → 空白页可接受; 邻页连续则丢内容）", flush=True)
        for f in fails:
            print(f"        {f}", flush=True)
        # 已知判定: 拟仿物 13 个 FAILED 页 = 章题装饰页（jpx 损坏, 文本层 0, 前后邻页语义完整, 正文零丢失）
        # 康德合集 7 页 = 篇间装饰/空白页（页9 目录→中译本序; 31/33/163/399 章题页前后; 207 索引卷尾; 251 审美判断力章题后）
        # 形而上学 15 页 = 书名页2-3/5-7 + 篇间页25 + 卷首目录页73/199/211/263/281/311/341/447 + 版权页493（前后邻页语义连续）
        # 实践理性句读 2 页 = 页1书名页 + 页293 部分卷首目录页; 判断力批判 2 页 = 41/171 部分卷首页
        # 西利斯 1 页 = 232 注释页(西塞罗引文)→附录标题页过渡; 自然与快乐 2 页 = 17/69 上/下编标题页
        knowns = {"cc9d0d9358a7": {1, 15, 95, 107, 113, 123, 129, 155, 209, 249, 285, 295, 315},
                  "10e1874c2255": {9, 31, 33, 163, 207, 251, 399},
                  "f11f1b13c278": {2, 3, 5, 6, 7, 25, 73, 199, 211, 263, 281, 311, 341, 447, 493},
                  "aacc867ec43c": {1, 293},
                  "f08c1ead3164": {41, 171},
                  "f0bf62d7aa30": {232},
                  "221f09d04944": {17, 69}}
        failset = set(int(k) for k, v in ocr.items() if v == "__FAILED__")
        if bid in knowns and failset <= knowns[bid]:
            check("B7", "FAILED 页", True, f"{len(failset)} 页 = 章题装饰页（已确认, 正文零丢失）")
        else:
            check("B7", "FAILED 页", False, f"{len(fails)} 页需人工确认（见上）")
    else:
        check("B7", "无 FAILED 页", True, "无")

    # B8 繁体书转换（标题含真繁体字 → 需转简体; 繁简同形字如"物/史"不误报）
    # 豁免: 拟仿物 cc9d0d9358a7（用户 2026-08-07 指示: 放弃繁简转换, 保留繁体）
    trad_chars = "擬與為餘說學將風臺樓義體國歷現動價環憂鄉會長處異後邊執紙終歸過適對歲發當應還開間問關從裏藝醫"
    title = meta.get("title", "")
    has_trad = [c for c in title if c in trad_chars]
    if bid == "cc9d0d9358a7" and has_trad:
        check("B8", "繁简", True, f"拟仿物保留繁体（用户指示）, 标题繁体字={has_trad}")
    else:
        check("B8", "繁简", not has_trad, f"标题繁体字={has_trad}→需转简体" if has_trad else "标题无繁体")

    # C9 三端一致（DP public 下挂 backend/data, DP backend 直接 data）
    sigs = {"PhiAgent": md5dir(bd)}
    for name, root in (("DP public", os.path.join(DP_PUBLIC, "backend", "data")),
                       ("DP backend", os.path.join(DP_BACKEND, "data"))):
        d = os.path.join(root, "book_chapters", bid)
        if os.path.exists(os.path.join(d, "meta.json")):
            sigs[name] = md5dir(d)
        else:
            sigs[name] = "MISSING"
    ok9 = len(set(sigs.values())) == 1
    check("C9", "三端一致", ok9, str(sigs))

    # C10 chapterCount + toc 一致（历史: book_detail toc 只同步了 count 忘了 toc → 前端目录显示旧碎片）
    cnts = {"meta": nch}
    det_fp = os.path.join(PHI_DET, f"{bid}.json")
    det_toc_ok = True
    if os.path.exists(det_fp):
        det = json.load(open(det_fp, encoding="utf-8"))
        cnts["detail"] = det.get("chapterCount")
        # detail.toc / meta.toc 可能是旧格式字符串数组, 归一化为 (title,type) 列表比较
        mt = meta.get("toc") or []
        if mt and isinstance(mt[0], str):
            mt = [{"title": t, "type": "chapter"} for t in mt]
        mt = [(t.get("title"), t.get("type")) for t in mt]
        dt = det.get("toc") or []
        if dt and isinstance(dt[0], str):
            dt = [{"title": t, "type": "chapter"} for t in dt]
        dt = [(t.get("title"), t.get("type")) for t in dt]
        if dt != mt:
            det_toc_ok = False
            cnts["detail_toc"] = f"{len(dt)} 条 vs meta {len(mt)} 条"
    for bf in (os.path.join(DP_PUBLIC, "books.json"),):
        if os.path.exists(bf):
            for b in json.load(open(bf, encoding="utf-8")):
                if b.get("id") == bid:
                    cnts["books.json"] = b.get("chapterCount")
                    break
    ok10 = len(set(cnts.values())) == 1 and det_toc_ok
    check("C10", "chapterCount/toc 一致", ok10, str(cnts))

    # C11 向量
    vec_n = 0
    ix_fp = os.path.join(EMB, "index.json")
    if os.path.exists(ix_fp):
        index = json.load(open(ix_fp, encoding="utf-8"))
        vec_n = sum(1 for it in index if it["bid"] == bid)
    check("C11", "向量已重嵌", vec_n == nch, f"index {vec_n}/{nch}")

    # C12 toc 类型: part 只作分组, 组内必须有可点击 chapter（理想国先例: 第X卷被切 part 无法跳转）
    # section 条目(节级, index+sec 锚点)不计入检查
    toc = meta.get("toc") or []
    if toc and isinstance(toc[0], str):
        toc = [{"title": t, "type": "chapter"} for t in toc]
    toc_ok = True
    msg = ""
    for i, t in enumerate(toc):
        if t.get("type") != "part":
            continue
        nxt = next((j for j in range(i + 1, len(toc)) if toc[j].get("type") == "part"), len(toc))
        if not any(g.get("type") == "chapter" for g in toc[i + 1:nxt]):
            toc_ok = False
            msg = f"{t['title'][:16]!r} part 组内无 chapter（分组须有可点击章; 编/卷级应 chapter）"
            check("C12", "toc 类型", False, msg)
    if toc_ok:
        npart = sum(1 for t in toc if t.get("type") == "part")
        nch2 = sum(1 for t in toc if t.get("type") == "chapter")
        nsec = sum(1 for t in toc if t.get("type") == "section")
        check("C12", "toc 类型", True, f"{nch2} chapter + {npart} part 分组" + (f" + {nsec} section 节级" if nsec else ""))

    # C13 toc 重复标题（历史: 美学中的不满 OCR 错字"间题/向题/同题"切 3 次）
    # 2026-08-07 升级: 按 part 分组内查重 — 跨卷/篇的"前言/献词/致谢"重复合法（与神对话 5 卷各卷一组）
    groups = []
    cur = []
    for t in toc:
        if t.get("type") == "part":
            if cur:
                groups.append(cur)
                cur = []
        else:
            cur.append(t)
    if cur:
        groups.append(cur)
    dup = []
    for g in groups:
        titles = [t["title"] for t in g if t.get("type") == "chapter"]
        dup += [t for t in set(titles) if titles.count(t) > 1]
    check("C13", "toc 无重复", not dup, f"组内重复={dup if dup else '无'}")

    # C16 section 锚点一致（分级标题: section 条目的 sec 必须指向章文件内同名 text 块）
    nsec = sum(1 for t in toc if t.get("type") == "section")
    nsec_bad = 0
    sec_msg = ""
    for t in toc:
        if t.get("type") != "section":
            continue
        fp = os.path.join(bd, f"{t.get('index')}.json")
        if not os.path.exists(fp):
            nsec_bad += 1
            continue
        ch = json.load(open(fp, encoding="utf-8"))
        texts = [b.get("value", "") for b in ch.get("content", []) if b.get("type") == "text"]
        if t.get("sec") is None or t["sec"] >= len(texts) or texts[t["sec"]] != t.get("title", ""):
            nsec_bad += 1
            if len(sec_msg) < 80:
                sec_msg = f" {t.get('title','')[:16]!r} index={t.get('index')} sec={t.get('sec')} 错位"
    check("C16", "section 锚点", nsec_bad == 0, f"{nsec} 节, 错位 {nsec_bad}{sec_msg}")

    nfail = sum(1 for r in report if not r[2])
    print(f"\n结果: {len(report) - nfail}/{len(report)} 通过" + (" ⚠ 需处理" if nfail else " ✓ 全部通过"), flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python dp_ocr_check.py <bid>", flush=True)
        sys.exit(1)
    main(sys.argv[1].strip())
