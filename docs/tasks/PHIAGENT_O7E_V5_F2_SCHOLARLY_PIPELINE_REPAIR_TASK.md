# PhiAgent O7-E V5-F2 Scholarly Pipeline Repair Task Book（Reviewer 原文存档）

> 存档说明：以下为 GPT-5.6 Sol 于 2026-09-07 给出的 V5_F1_R1_RCA_PASS 终审结论 +
> V5-F2 production repair 任务书，逐字存档。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Final Verdict：V5_F1_R1_RCA_PASS

这次可以正式收口。

```
V5_F1_R1_RCA_PASS=true
V5_F1_RCA_CLOSED=true
V5_MEASUREMENT_UNCHANGED=true
PRIMARY_ROOT_CAUSE=SCHOLARLY_CORPUS_DISCOVERY_CONTENT_GAP
COMPOUNDING_CONDITION=V5_RUN_OBSERVED_PROVIDER_FAILURE
PRIMARY_ROOT_CAUSE_CONFIDENCE=HIGH
READ_ORCHESTRATION_FAILURE=CONFIRMED_SECONDARY
QUERY_FORMULATION_FAILURE=UNRESOLVED
RELEVANCE_RANKING_FAILURE=SECONDARY / GENERIC_WEAKNESS
BIBLIOGRAPHY_GROUNDING_GUARD_GAP=CONFIRMED
EVIDENCE_PROMOTION_FAILURE=NOT_DEMONSTRATED
V5_F2_REPAIR_AUTHORIZED=true
V6_AUTHORIZED=false
```

### 为什么这次 PASS

范围首先完全合规。`bf0b9ff → 8f9376c` 只有一个 commit，实际只增加新的 relevance RCA 与任务书，没有 production 或已消费 V5 canonical artifact 修改。

上一轮最大的统计错误也真正修掉了。118 已降格为 **result occurrences**；按 case 去重后分别只有 5/9/13/7/5/11 个 readable records，而六个 case 的 `DIRECT_UNIQUE_RECORDS` 全部为 0。只有 V5-06 和 V5-11 存在少量 SUPPORTING 级可读材料。

我抽查 frozen records 后同意这个分类。比如 V5-09 本应检索 Nishida/James pure experience，实际出现的是 Kant、Locke、墨家、Wittgenstein 等；这些即使 READ 也不能完成题目要求。V5-11 最好的候选也只是 `Aristotle on Eudaimonia` 和 `Kant on Autonomy and Moral Evil`，可作为背景 SUPPORTING，但不是 Anscombe/Hooker 争论的直接文献。V5-12 更明显，候选是 Leibniz、Wittgenstein、Kant、Hume、王阳明等，与 Mackie/Parfit/Enoch 的目标争论没有直接对应。

冻结 registry 的天花板也确实很低：316 records、282 accepted，但只有 **31 条 abstract evidence，0 passage，0 full-text-read records**。再叠加 V5 run 中 live provider 没有贡献，local registry 就成为唯一 scholarly source，这足以解释为何 secondary-heavy qualification 整体崩掉。

因此我对 Builder 的 root-cause wording 做一个正式规范化：

> **主因是 local scholarly corpus 的 discovery/content coverage gap；V5 评测环境中 live provider 零贡献是使这个 gap 变成致命故障的复合条件。**

这样比把两者都混成一个 root cause 更精确。

另外，READ orchestration 并没有被撤销：工具本来明确要求 LOCATE 后用 `get_scholarly_source` READ，而且 `access_level` 对模型可见。只是我们现在知道，它不是六个 secondary-heavy case 的首要失败原因——**池里本来就没有足够直接文献。**

---

## V5-F2 Production Repair 任务书

**MODEL:** GLM-5.3　**BASE:** `8f9376cdb7ad106e1a952350a3856322acbaa19a`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

下一阶段不再做 RCA，正式修 production，但仍然**不授权 V6**。先把 scholarly pipeline 修到值得重新 qualification 的程度。

目标：修复 V5-F1 已确认的 scholarly corpus/discovery-content gap，并同时关闭 retrieval relevance、LOCATE→READ、bibliography grounding、qualification observability 四个配套缺陷。

V5 永久消费。禁止 V5 rerun/rejudge。禁止修改 judge/rubric/threshold/final-gate。

### A. Scholarly corpus

使用正常、可复现 ingestion/curation pipeline 扩充 secondary corpus。不得 V5 case-id routing，不得在 production 中硬编码题目。

V5 六主题可作为 **dev regression**：
- Searle/Chinese Room；
- Williams/Nagel moral luck；
- Nishida/William James pure experience；
- Averroes/Ibn Rushd philosophy–religion；
- Anscombe *Modern Moral Philosophy* + Hooker 的 rule consequentialism；
- Mackie error theory + Parfit/Enoch realism。

每个 dev topic 至少要求：

```
DIRECT_RECORDS >= 3
CONTENT_READABLE_DIRECT_RECORDS >= 2
```

内容必须是真实 abstract 或合法 OA passage，有完整 provenance。metadata-only 不算 content coverage。

同时建立更广的 generic coverage matrix，覆盖 western ancient/medieval/modern/contemporary、Chinese、Indian/Islamic/Japanese/African 等，不得只塞 V5 六题。

### B. Retrieval relevance

修复当前 OR/BM25 单词碰撞造成的离题结果。

必须 generic：
- 多词覆盖率/短语/人物名匹配优先；
- 语义相关度优先于 access level；
- 仅在相关度相当时优先 `ABSTRACT_AVAILABLE+`。

不得针对 Searle/Averroes 等写 production special-case。

V5 dev queries 的 DIRECT records 必须进入合理 top-k。

### C. LOCATE → READ

强化 generic scholarly contract：

当用户明确要求"学术文献/二手研究/争议/文献依据"时，若 search 结果存在 relevant `ABSTRACT_AVAILABLE+` source，在作出该来源的内容性归因前必须调用 `get_scholarly_source`。

search response 增加机械派生的：`READABLE_RESULT_COUNT` 及可读 source IDs / 清晰提示。

若没有 relevant readable evidence，必须进入诚实 fallback，不得用模型记忆伪装已核验 scholarship。

### D. Bibliography grounding guard

增加机械 guard：终稿中的精确 scholarly bibliographic metadata，例如 DOI、publisher、volume、year、page 等，必须能够追溯到 retrieved bibliographic record 的 verified fields。

无证据时至少产生：`UNGROUNDED_BIBLIOGRAPHIC_DETAIL` 并进入 repair/fail-closed，不得像 V5-12 一样 issue=0 直接发布。

同时保持：`EVIDENCE_PROMOTION_FAILURE` 不做无证据扩张。

### E. Qualification harness

修复 `scholarly_calls_detail`：不得再从无 args 的 `tool_start` 取参数；必须从实际 `type="tool"` event 保存：`tool_call_id` / `name` / `args` / `result/provenance`。

未来 qualification artifact 必须可恢复原始 scholarly query。

不要依赖会被 pytest 覆写的 `scholarly_cache.json` 作为 canonical query log。

### F. Environment

保持 SSRF/security 默认行为不降低。

增加 qualification preflight，明确报告：

```
NETWORK_MODE
CROSSREF_REACHABLE
OPENALEX_REACHABLE
LIVE_PROVIDER_AVAILABLE
OFFLINE_MODE
```

未来 V6 最终 qualification 不允许把 provider blockage 静默当作正常在线运行。

### G. Dev behavioral gate

本阶段允许使用 consumed V5 themes 作为 development probes；它们不属于 V6。

建立 6 个 secondary dev probes，证明 production agent 实际执行：

```
search_scholarship → relevant source selection → get_scholarly_source
→ content_evidence → grounded final answer
```

Acceptance：

```
6/6 search
>=5/6 scholarly READ
>=5/6 content evidence
UNGROUNDED_BIBLIOGRAPHIC_DETAIL=0
FABRICATED precise bibliography=0
SAFE_FALLBACK correct when evidence unavailable
```

允许开发过程中反复运行这些 dev probes；它们永久禁止进入 V6 holdout。

### H. Closure

先提交 implementation/tests/corpus：`CONTENT_HEAD`。运行 full test。

再独立 evidence-only commit：`ARCHIVE_HEAD.parent == CONTENT_HEAD`。

产物：`docs/evidence/V5_F2_SCHOLARLY_PIPELINE_REPAIR.json`

至少记录 corpus before/after、coverage matrix、六个 dev-topic DIRECT/content counts、retrieval regressions、behavioral probe metrics、bibliography guard regressions、harness args roundtrip、provider preflight、FULL_TEST_RESULT、changed-files exact diff。

最终只能报告：

```
BASE_SHA
CONTENT_HEAD
ARCHIVE_HEAD
REMOTE_SHA
CORPUS_COVERAGE
DEV_DIRECT_COVERAGE
DEV_CONTENT_COVERAGE
BEHAVIORAL_SEARCH_READ
BIBLIOGRAPHY_GUARD
HARNESS_QUERY_ARGS
PROVIDER_PREFLIGHT
FULL_TEST
READY_FOR_V5_F2_REVIEW
```

STOP.

**正式状态现在是：`V5-F1 RCA CLOSED → V5-F2 REPAIR AUTHORIZED`。**

F2 通过之后我再决定是否直接开放 V6；不会再拿新的 qualification 去替尚未验证的修复试错。
