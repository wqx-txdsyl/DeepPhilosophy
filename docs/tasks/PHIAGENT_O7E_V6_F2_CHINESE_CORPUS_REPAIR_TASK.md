# PhiAgent O7-E V6-F2 Chinese Scholarly Corpus Repair Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 签发 V6-F1-R1 PASS / V6-F1 CLOSED + V6-F2 任务书。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Verdict：V6-F1-R1 PASS / V6-F1 CLOSED

这次可以签掉，不再继续补 RCA。

```
V6_MEASUREMENT_UNCHANGED=true
RCA_SCOPE_INTEGRITY=PASS
V6_F1_R1_RCA_REVIEW=PASS
V6_F1_R1_PASS=true
V6_F1_CLOSED=true
QUERY_05_FORMULATION_DEFECT=CONFIRMED
QUERY_FORMULATION_FAILURE=NOT_DEMONSTRATED
CORPUS_COVERAGE_GAP=CONFIRMED
CONTENT_AVAILABILITY_GAP=CONFIRMED
READ_ORCHESTRATION_FAILURE=NOT_DEMONSTRATED
EVIDENCE_PROMOTION_FAILURE=NOT_DEMONSTRATED
MODEL_TOOL_USE_FAILURE=NOT_DEMONSTRATED
PRIMARY_ROOT_CAUSE=CORPUS_COVERAGE_GAP
PRIMARY_ROOT_CAUSE_CONFIDENCE=HIGH
V6_F2_AUTHORIZED=true
V7_AUTHORIZED=false
```

Scope 完全干净（6016321 → aaca107 两段 docs-only）；64 occurrences / 40 unique / 31 readable occurrences / 18 unique readable 固化；27/32 人工粗计撤回；Query #5 Ming dynasty 错配正式承认。Reviewer 还按冻结 DOI 独立恢复了 UNCERTAIN 项 metadata：网络教学、水利工程、孙中山制度正义、密尔功利主义等——均非董仲舒-陈亮-叶适-永嘉/永康事功专题。因果链成立：8 searches → 64 occurrences → 无 topic-relevant + readable secondary source → READ=0（不归责 orchestration）→ CONTENT_EVIDENCE=0 → PRIMARY=CURRENT SCHOLARLY CORPUS COVERAGE GAP（范围限定：当前 local registry + 当前 reachable scholarly-provider universe，不是「中国学界没有相关研究」）。

---

## V6-F2 任务书

**MODEL:** GLM-5.3　**BASE:** `aaca1071b6f602204ea39f2ac382ff2d1417c81c`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

Objective：修复 V6-F1 已确认的 primary root cause：CORPUS_COVERAGE_GAP——当前 scholarly corpus 缺少可读的董仲舒 / 义利之辨 / 陈亮 / 叶适 / 永康永嘉事功思想二手研究。**只修 corpus coverage；不得为 V6-09 特判。**

### §1 Curated scholarly coverage

向正常 scholarly registry/corpus 增补一组真实、可验证、有 provenance 的二手研究，至少覆盖：
- 董仲舒与义/利、正其谊不谋其利
- 陈亮与朱熹思想论辩
- 陈亮 / 永康学派的事功思想
- 叶适 / 永嘉学派
- 事功思想与传统义利观的关系

要求：不得伪造 bibliography / abstract / passages；优先合法公开可访问的 scholarly source；ABSTRACT_AVAILABLE+ 才可计入 readable coverage；metadata-only 可收录但不能作为 content-evidence 修复证明；不得抓取或绕过付费墙；保存 DOI/URL/title/authors/year/source/provenance/access_level/content provenance。

### §2 Normal production-path regression

必须走真实生产链：search_scholarship → get_scholarly_source。不得直接调用 registry 内部函数作为 PASS 证据。

使用与 V6-09 主题等价但不是 holdout answer rerun 的 deterministic probes，例如：
- 陈亮 朱熹 义利 事功
- Chen Liang Zhu Xi utilitarian statecraft
- 叶适 永嘉学派 事功
- Ye Shi Yongjia school
- 董仲舒 义利 正其谊不谋其利

Gate：DIRECT_RELEVANT_SEARCH_HIT >= 1 for each major topic cluster；READABLE_DIRECT_RELEVANT_HIT >= 1 for each major topic cluster；GET_SCHOLARLY_SOURCE_SUCCESS=true；NONEMPTY_CONTENT=true；CONTENT_EVIDENCE_CAPABLE=true。

至少实际 READ：1 条董仲舒/义利相关；1 条陈亮相关；1 条叶适/永嘉相关。

### §3 No special routing

必须证明：NO_V6_09_CASE_ID_ROUTING=true / NO_EXACT_QUERY_HARDCODE=true / NO_ANSWER_HARDCODE=true / NO_MODEL_CHANGE=true / NO_JUDGE_RUBRIC_CHANGE=true / NO_V6_CANONICAL_ARTIFACT_CHANGE=true。通过正常 scholarly retrieval 对同义/中英变体生效。

### §4 Ranking rule

**默认禁止修改 ranking。** 先以 corpus-only 运行 §2。只有新增 direct/readable records 仍被明显离题结果挤出正常结果窗口时，才可提交证据并实施最小 generic ranking correction。若 corpus-only 已通过，RANKING_CHANGED=false。

### §5 Evidence

新增 docs/evidence/V6_F2_CHINESE_SCHOLARLY_CORPUS_REPAIR.json。记录：新增 source inventory + provenance；access/content levels；exact diagnostic queries；returned ranks/source IDs；READ trace；content availability；special-routing negative proofs；production drift；regression/full-test result。不得运行 V6 answer 或 V6 judge。

### Exit

Builder 不得自行宣布 O7-E PASS。最终仅：READY_FOR_V6_F2_REPAIR_REVIEW。STOP.

Milestone：V5-F2=PASS/CLOSED；V6=CONSUMED；V6 DELIVERY=PASS；V6 SCHOLARLY=FAIL；V6-F1=PASS/CLOSED；PRIMARY RCA=CORPUS_COVERAGE_GAP；V6-F2=AUTHORIZED；V7=NOT YET AUTHORIZED。

「F2 做完回来，我会直接审新增文献真实性 + normal search→READ 可达性 + 有没有偷偷做 V6-09 特判；F2 PASS 后才放行 fresh V7。」
