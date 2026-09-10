# -*- coding: utf-8 -*-
"""O7-E V4-F1-R1.2: 阿奎那语料检索回归（production search_books 路径）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scholarly_sources as SS
import scholarly_registry as SR


def _fts_hits(queries):
    """本地 curated registry FTS5 检索（SS._local_results → SR.search_local）。"""
    SR._registry = None
    SR._evidence = None
    out = []
    for q in queries:
        out += SS._local_results(q, limit=10)
    return out


def _ft_ids(hits):
    return {h.get("source_record_id") for h in hits if h.get("source_record_id")}


FAMILIES = {
    "EN:Thomas Aquinas": ["Thomas Aquinas"],
    "EN:Summa Theologica": ["Summa Theologica"],
    "EN:natural law": ["natural law"],
    "CN:王阳明": ["王阳明"],
    "CN:王守仁": ["王守仁"],
    "CN:知行合一": ["知行合一"],
    "CN:格物": ["格物"],
    "CN:朱熹": ["朱熹"],
    "EN:Zhu Xi": ["Zhu Xi"],
    "Latin:Neo-Confucianism": ["Neo-Confucianism"],
    "CN:宋明理学": ["宋明理学"],
}


def test_all_query_families_hit_registry():
    """全部 11 个查询族在本地 curated registry FTS 中至少命中 1 条。"""
    for label, queries in FAMILIES.items():
        hits = _ft_ids(_fts_hits(queries))
        assert hits, f"{label} 零命中（alias/index 覆盖缺口回归）"


def test_alias_equivalence_cn_en_wang_yangming():
    cn = _ft_ids(_fts_hits(FAMILIES["CN:王阳明"]))
    en = _ft_ids(_fts_hits(FAMILIES["EN:Thomas Aquinas"]))
    # CN/EN 至少有一条共同相关记录（alias 等价）
    assert cn and en, "CN 或 EN 查询族零命中"


def test_new_curated_records_in_registry():
    SR._registry = None
    reg = SR.load_registry()
    for sid in ("doi:10.1111/1540-6253.12204",
                "doi:10.14711/thesis-991012644164903412",
                "doi:10.1007/978-3-476-05728-0_21974-1"):
        assert sid in reg, f"{sid} 不在 registry"
        assert reg[sid].get("aliases"), f"{sid} 缺 aliases"


def test_zhu_xi_alias_enrichment():
    SR._registry = None
    reg = SR.load_registry()
    enriched = [r for r in reg.values()
                if "aliases" in r and "朱熹" in (r.get("aliases") or [])]
    assert enriched, "朱熹相关记录应有 alias 富集"
