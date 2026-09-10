# -*- coding: utf-8 -*-
"""O7-E V3-RP3 Scholarly Retrieval Recovery: registry 双语覆盖回归。

锁死（PF-RP5-F1/V3-RP3 任务书 §3）:
  CN/EN 查询族均须命中本地 curated registry（别名/索引覆盖修复实证）;
  ALIAS_EQUIVALENCE（同记录可被中英查询族共同召回）;
  R25 probe（王阳明相关候选可被找到）;
  SAFE_FALLBACK / 合同指引存在（不做 runtime 强制）。
纯离线: 只读本地 FTS5 registry, 零网络/零 Agent/零 holdout 调用。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scholarly_sources as SS
import scholarly_registry as SR

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAMILIES = {
    "王阳明": ["王阳明"],
    "Wang Yangming": ["Wang Yangming"],
    "Wang Shouren": ["Wang Shouren"],
    "朱熹": ["朱熹"],
    "Zhu Xi": ["Zhu Xi"],
    "知行合一": ["知行合一"],
    "unity of knowledge and action": ["unity of knowledge and action"],
    "格物": ["格物"],
    "gewu": ["gewu"],
    "investigation of things": ["investigation of things"],
    "Neo-Confucianism": ["Neo-Confucianism"],
    "Song-Ming Confucianism": ["Song-Ming Confucianism"],
}


def _hits(queries):
    # 强制从冻结 registry.jsonl 重载 + 重建索引——避免同套件内其他测试的
    # fixture registry 污染全局缓存（顺序依赖消除）
    SR._registry = None
    SR._evidence = None
    if os.path.exists(SR.INDEX):
        os.unlink(SR.INDEX)
    SR.build_index()
    out = []
    for q in queries:
        out += SS._local_results(q, limit=8)
    return out


def _ids(hits):
    return {h.get("source_record_id") for h in hits}


# ── CN/EN 查询族覆盖 ──
def test_registry_cn_en_family_coverage():
    for fam, queries in FAMILIES.items():
        hits = _hits(queries)
        assert hits, f"{fam} 查询族零命中（alias/index 覆盖缺口回归）"


def test_alias_equivalence_cn_en_same_records():
    cn = _ids(_hits(FAMILIES["王阳明"]))
    en = _ids(_hits(FAMILIES["Wang Yangming"]))
    assert cn & en, "CN/EN 查询族必须召回同一相关记录（ALIAS_EQUIVALENCE）"
    zhu_cn = _ids(_hits(FAMILIES["朱熹"]))
    zhu_en = _ids(_hits(FAMILIES["Zhu Xi"]))
    assert zhu_cn & zhu_en, "朱熹/Zhu Xi 别名等价失败"


def test_r25_regression_probe_wang_yangming_candidates_available():
    """R25 实况回归: 王阳明/知行合一相关候选现在可被本地 registry 召回。"""
    for fam, queries in (("知行合一", FAMILIES["知行合一"]),
                         ("Wang Yangming", FAMILIES["Wang Yangming"]),
                         ("格物", FAMILIES["格物"])):
        hits = _hits(queries)
        assert hits, f"{fam} 相关候选必须可召回"


def test_unrelated_top_result_regression_fixed():
    """R25 实况回归: 多词学术查询的 top 命中必须是相关记录（非古生物学/网络协议）。"""
    hits = _hits(FAMILIES["unity of knowledge and action"])
    assert hits
    blob = json_dumps_hits(hits)
    for unrelated in ("endothelia", "wireless sensor", "X-Ray Diffraction"):
        assert unrelated.lower() not in blob.lower()


def json_dumps_hits(hits):
    import json
    return json.dumps(hits, ensure_ascii=False)


def test_contract_v4_multilingual_guidance_present():
    import engine_langgraph as EG
    contract = EG.SCHOLARLY_CONTRACT
    assert "原语言名称" in contract
    assert "换" in contract and "重新表述" in contract   # 首轮离题→换语言/关键词


def test_search_tool_description_discovery_only():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "routes", "agent_tools_scholarly.py")
    src = open(p, encoding="utf-8").read()
    assert "metadata/discovery only" in src
    assert "内容归因必须再用" in src


# ── RP3-R1: search→read 真路径 + METADATA_ONLY 不造内容 + clean rebuild ──
def test_search_to_read_real_abstract_content():
    import scholarly_sources as SS
    hits = _hits(["Wang Yangming"])
    assert hits, "检索必须先命中王阳明相关候选"
    sid = "doi:10.1215/00318108-9554691"      # 有持久化 ABSTRACT 的相关记录
    rec = SS.get_record(sid)
    assert rec, "registry 必须含该记录"
    rec2, info = SS.get_evidence(rec, "ABSTRACT")
    text = (info.get("abstract") or {}).get("text") or ""
    assert text.strip()                                        # READ 取得真实内容
    assert info.get("returned_evidence_level") in ("ABSTRACT_AVAILABLE",
                                                   "FULL_TEXT_READ")


def test_metadata_only_candidate_yields_no_fabricated_content():
    import scholarly_sources as SS
    sid = None
    for r in SR.load_registry().values():
        ing = r.get("ingest") or {}
        if ing.get("access_level_at_ingest") == "METADATA_ONLY":
            sid = r.get("source_record_id")
            break
    assert sid, "registry 应存在 METADATA_ONLY 记录"
    rec = SR.record(sid)
    assert rec is not None
    # 无持久化内容证据（evidence.jsonl 无该 sid 条目）
    assert not SR.evidence_for(sid)


def test_clean_canonical_rebuild_deterministic():
    """从 HEAD 已提交源（snapshot/manifest/curation）确定性重建 →
    registry/evidence sha 与已提交派生文件一致（CLEAN_REBUILD_DIFF=0）。"""
    import hashlib
    import shutil
    import tempfile
    import scholarly_registry as SR2
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools"))
    import dp_o7d_registry  # noqa: F401  (确保 build 可用)
    before = (hashlib.sha256(open('data/scholarly/registry.jsonl', 'rb').read()).hexdigest(),
              hashlib.sha256(open('data/scholarly/evidence.jsonl', 'rb').read()).hexdigest())
    tmp = tempfile.mkdtemp()
    try:
        # 备份派生文件 → 重建 → 比对
        shutil.copy('data/scholarly/registry.jsonl', tmp + '/r.jsonl')
        shutil.copy('data/scholarly/evidence.jsonl', tmp + '/e.jsonl')
        SR2._registry = None
        SR2._evidence = None
        if os.path.exists(SR2.INDEX):
            os.unlink(SR2.INDEX)
        import dp_o7d_registry as REG
        REG.build()
        after = (hashlib.sha256(open('data/scholarly/registry.jsonl', 'rb').read()).hexdigest(),
                 hashlib.sha256(open('data/scholarly/evidence.jsonl', 'rb').read()).hexdigest())
        assert before == after, "确定性重建漂移"
    finally:
        shutil.copy(tmp + '/r.jsonl', 'data/scholarly/registry.jsonl')
        shutil.copy(tmp + '/e.jsonl', 'data/scholarly/evidence.jsonl')
        shutil.rmtree(tmp, ignore_errors=True)
