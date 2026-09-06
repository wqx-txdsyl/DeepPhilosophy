# -*- coding: utf-8 -*-
"""O6-Q1 failure corpus audit dump（临时脚本，随用随删）
Dump every failure in prerp1_data (cases + conversations) + run1_polluted for
manual root-cause classification (Q1-Q12 + three-way class)."""
import json, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.abspath(__file__))
GB = os.path.join(BASE, "o6_gate", "gate_b")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def fmt_issue(i):
    loc = (i.get("locator") or "").replace("\n", " ")[:70]
    det = (i.get("detail") or "").replace("\n", " ")[:110]
    ev = i.get("evidence_ref") or "-"
    return f"    {i.get('code')} @ {loc} | ev={ev} | {det}"


def dump_turn(tid, t, hist=None):
    out = []
    val = t.get("validation") or {}
    res = (val.get("result") or {})
    issues = res.get("issues") or []
    vfp = t.get("validation_failed_payload") or {}
    v_issues = vfp.get("issues") or issues
    published = t.get("published")
    failed = not published
    # repair exhaustion indicator
    repairs = val.get("repairs_used")
    exhausted = failed and (vfp.get("repairs_used") is not None)
    qb = t.get("quote_bound") or {}
    qsum = qb.get("summary") or {}
    budget = t.get("budget") or {}
    out.append(f"## {tid} agent={t.get('agent')} published={published} "
               f"repairs={repairs} tools={t.get('tool_count')} "
               f"(S={t.get('search_calls')}/R={t.get('read_calls')}) hard={budget.get('hard')}")
    if hist:
        out.append(f"  HISTORY: {hist}")
    out.append(f"  Q: {t.get('question')}")
    ans = (t.get("answer") or "").strip()
    out.append(f"  A({t.get('answer_chars')}): {ans[:180].replace(chr(10), ' | ')}")
    seq = t.get("tool_seq") or []
    seqs = []
    for s in seq:
        nm = s.get("name")
        mark = "*RE" if s.get("reused") else ""
        err = "ERR" if s.get("err") else ""
        a = s.get("args") or {}
        q = (a.get("query") or a.get("concept") or a.get("philosopher") or "")
        arg = f"({q[:20]})" if q else ""
        seqs.append(f"{nm}{arg}{mark}{err}")
    out.append("  SEQ: " + " → ".join(seqs))
    out.append(f"  QBOUND: {json.dumps(qsum, ensure_ascii=False)}")
    if v_issues:
        out.append("  ISSUES:")
        for i in v_issues:
            out.append(fmt_issue(i))
    cites = t.get("citations") or []
    if cites and failed:
        out.append(f"  CITATIONS(panel): {[ (c.get('book'), c.get('chapter')) for c in cites ][:6]}")
    cs = t.get("citation_sanitize") or {}
    if cs.get("unverified_before") and failed:
        out.append(f"  UNVERIFIED_CITES: {cs.get('unverified_before')[:4]}")
    return out, failed, exhausted


def main():
    lines = []
    n_fail = n_exhaust = 0
    # ── single-turn cases ──
    cdir = os.path.join(GB, "prerp1_data", "cases")
    for fn in sorted(os.listdir(cdir)):
        d = load(os.path.join(cdir, fn))
        r = d.get("result", d)
        cid = r.get("id", fn)
        ls, failed, exhausted = dump_turn(cid, r)
        if failed:
            n_fail += 1
            if exhausted:
                n_exhaust += 1
            lines += ls
    # ── conversations ──
    convdir = os.path.join(GB, "prerp1_data", "conversations")
    for fn in sorted(os.listdir(convdir)):
        d = load(os.path.join(convdir, fn))
        hist = []
        for t in d.get("turns", []):
            histq = t.get("question", "")
            ls, failed, exhausted = dump_turn(t.get("id", "?"), t,
                                              hist=" || ".join(hist[-2:]) if hist else None)
            if failed:
                n_fail += 1
                if exhausted:
                    n_exhaust += 1
                lines += ls
            hist.append(f"{t.get('id','?')}[pub={t.get('published')}]: {histq[:60]}")
    # ── run1_polluted ──
    rp = os.path.join(GB, "run1_polluted")
    for sub in ("cases", "conversations"):
        p = os.path.join(rp, sub)
        if not os.path.isdir(p):
            continue
        for fn in sorted(os.listdir(p)):
            try:
                d = load(os.path.join(p, fn))
            except Exception as e:
                lines.append(f"## POLLUTED {fn}: load error {e}")
                continue
            if sub == "cases":
                r = d.get("result", d)
                ls, failed, exhausted = dump_turn("POLL-" + r.get("id", fn), r)
                if failed:
                    n_fail += 1
                    lines += ls
            else:
                for t in d.get("turns", []):
                    ls, failed, exhausted = dump_turn("POLL-" + t.get("id", "?"), t)
                    if failed:
                        n_fail += 1
                        lines += ls
    print(f"=== TOTAL FAILURES: {n_fail} (exhausted={n_exhaust}) ===")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
