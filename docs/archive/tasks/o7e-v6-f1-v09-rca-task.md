# PhiAgent O7-E V6-F1 V6-09 Secondary Evidence RCA Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 给出的 V6 裁定 + V6-F1 窄域 RCA 任务书。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer 结论：V6 测量有效，但 Scholarly FAIL

```
V6_MEASUREMENT_VALID=true
V6_CONSUMED=true
DELIVERY_GATE=PASS
SCHOLARLY_GATE=FAIL
O7-E_FINAL_PASS=false
V6_FINAL_VERDICT=V6_SCHOLARLY_GATE_NOT_MET
V6_RERUN=NOT_AUTHORIZED
V6_REJUDGE=NOT_AUTHORIZED
V7_AUTHORIZED=false
```

1. Qualification integrity：PASS（freeze integrity / no reuse / production drift=0 / measurement contamination=false）。
2. 首次 402 不导致 V6 作废：PRERECHARGE_402_ATTEMPT=NON_CONSUMING_INFRASTRUCTURE_FAILURE（零 token、零工具调用、零 adaptive signal; production/manifest 未变）——重跑裁定成立，属很窄的例外。
3. 回执数字勘误（receipt-only）：REPAIR_TRIGGERED=9 CONVERGED=9（非 8/8）；QUALIFICATION_IMPACT=NONE。其余 mechanical/provenance 数字核验吻合。
4. Canonical judge 只有一个 gate 没过：REQUIRED_DIMENSION_MEDIAN_LT_2=1；六项 fatal 全零；五维均值全部过线。FAIL 必须保留，不得手动 override。
5. 唯一 tail 是 V6-09（SEARCH=8 READ=0 CONTENT_EVIDENCE=0，LO 三票全 1）：不是回答胡编——系统明确披露未取得可读专门研究；evidence boundary 做得对（无 bibliography fabrication、无 access overclaim）。分类：V6_09_LO_FAILURE=CONFIRMED SECONDARY_CONTENT_EVIDENCE_GAP=CONFIRMED SAFE_FALLBACK_FAILURE=false；其余 8 类根因 UNRESOLVED。

不接受回执中「该主题二手语料不在 F2 corpus 扩充范围」作为已证明根因——证据只证明了 8 search→0 READ→0 content evidence，究竟是搜不到/搜偏/只有 metadata/可读未读/provider 问题，必须从 original-call snapshot 查清。

---

## V6-F1 RCA 任务书

**MODEL:** GLM-5.3　**BASE:** `e6fa2ccaea300f027be997204666eb92661cbbf1`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

Objective：仅定位 V6-09 的 8 SEARCH → 0 READ → 0 CONTENT_EVIDENCE 真实根因。**RCA ONLY，不得实施修复。**

Freeze：V6 已永久消费。禁止 V6 agent rerun、judge rerun/rejudge、修改任何 V6 canonical artifact、修改 production、修改 corpus/registry/aliases、修改 scholarly retrieval/ranking/LOCATE→READ、修改 bibliography guard/provenance、修改 judge/rubric/threshold/final gate。

允许：离线分析冻结的 V6-09 original-call trace；必要时以已消费的原 query 做 deterministic tool-level diagnostic probe；READ 已存在 scholarly record 以确认 access/content 状态。不得生成新的 V6 answer 或 judge。

Required audit：对 V6-09 全部 8 次 search 逐次建立 tool_call_id → exact query → returned_source_record_ids → title/relevance → retrieval_origin → access_level → provider_errors/offline_mode → content actually available? → READ attempted? → if not, why? → potential content_evidence。

必须回答：
- 8 个 exact query 分别是什么？
- 是否返回过与董仲舒、陈亮、叶适、永康/永嘉事功思想、王霸义利之辨直接相关的记录？
- 如有相关记录，是 METADATA_ONLY 还是具有 ABSTRACT/PASSAGE/FULL_TEXT 可读内容？
- 是否存在 relevant + readable candidate 却未触发 READ？
- 若全是 metadata/no hit，缺口在 registry/corpus、provider access、query formulation 还是 ranking？
- 是否有 provider error / offline / access-depth 阻断？
- 现有 registry 中是否其实存在可通过更合理 alias/query 找到的可读材料？
- 能否以证据充分确认 CORPUS_COVERAGE_GAP？不能则不得写 confirmed。

最小 repair surface 是什么？

逐项裁定（仅允许 CONFIRMED / CONTRIBUTING / NOT_DEMONSTRATED / NOT_APPLICABLE，不得猜测）：QUERY_FORMULATION_FAILURE / RELEVANCE_RANKING_FAILURE / CORPUS_COVERAGE_GAP / CONTENT_AVAILABILITY_GAP / ACCESS_DEPTH_GAP / READ_ORCHESTRATION_FAILURE / EVIDENCE_PROMOTION_FAILURE / MODEL_TOOL_USE_FAILURE

Artifact：docs/evidence/V6_F1_V6_09_SECONDARY_EVIDENCE_RCA.json，至少包含 V6_MEASUREMENT_UNCHANGED=true、V6_09_SEARCH_CALLS=8、V6_09_READ_CALLS=0、V6_09_CONTENT_EVIDENCE=0、完整 8-call audit、failure classifications、PRIMARY_ROOT_CAUSE、SECONDARY_ROOT_CAUSES[]、MINIMUM_REPAIR_SURFACE[]。

不得实施 repair。最终仅：READY_FOR_V6_F1_RCA_REVIEW。STOP.

里程碑：V5-F2=PASS/CLOSED；V6=CONSUMED；V6_MEASUREMENT=VALID；V6_DELIVERY=PASS；V6_SCHOLARLY=FAIL；V6-F1=RCA AUTHORIZED；V7=NOT YET AUTHORIZED。

「这次其实已经非常接近 O7-E 终门了：不是继续调 judge，而是把唯一剩下的 V6-09 secondary-evidence tail 查明并修掉。」
