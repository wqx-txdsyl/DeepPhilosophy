我审完 09b8b1384 → 118e654f2 这一轮了。结论：STOP 是正确的，但我暂时不授权 repair-specific SystemMessage。因为这次 5/8 仍然不是“模型在拿到正确 repair evidence 后仍不服从”的干净实验。

正式裁定：

O7_E_RP2_CALIBRATION_CLOSURE_REVIEW = PATCH_REQUIRED

METRIC_CORRECTION = PASS
BEST_WINDOW_ROLLBACK = PASS
THIRD_NEAR_QUOTE_ESCAPE_ROLLBACK = PASS
SMALL_PACKET_DIRECTION = PASS
MAX_VALIDATION_REPAIRS_2 = ACCEPTED

PRIMARY_TARGET_RESOLUTION_WORK = PARTIAL_PASS
PRIMARY_TRUTH_HELPER = ACCEPTED_AS_FOUNDATION

REAL_QUOTE_EVIDENCE_REF_RESOLUTION = FAIL
PRIMARY_GATE_CANONICAL_INTEGRATION = FAIL
PRIMARY_COVERAGE_PREFLIGHT = FAIL

REPAIR_SPECIFIC_SYSTEM_PROTOCOL_AUTHORIZED = false
STAGE_B_AUTHORIZED = false

O7_E_RP2_CALIBRATION_CLOSURE_2_AUTHORIZED = true

这里有一个很关键的独立审计发现。

你现在新的 resolver 只接受：

Python
Run
m_ev = re.fullmatch(r"ev_(\d+)", ref)

然后自己按 raw tool log 顺序去重建 ev_N → tool result。

但 quote validator 的 evidence_ref 根本不是 ev_N。

quote_bound.evidence_spans() 给实际读取的章节生成的是：

qb_read_<raw_tool_entry_index>

搜索片段是：

qb_snip_...

corpus 是：

qb_corp_...

。

然后 verify_quote() 在 NEAR / EXACT 时把这个 qb_* ID 原样作为 evidence_id 返回。

audit_quotes() 又把它暴露成：

source_evidence_id

。

实际 Stage-B artifact 里也能直接看到：

source_evidence_id = "qb_read_7"

。

而 final_validator 的 quote issue 正是：

Python
Run
ev = e["source_evidence_id"]
ValidationIssue(... evidence_ref=ev)

所以真实链路是：

NEAR_QUOTE_NOT_MARKED
        ↓
evidence_ref = qb_read_7
        ↓
当前 repair packet：
只识别 ev_\d+
        ↓
MISS

这非常重要，因为你本轮剩下最顽固的恰恰就是：

NEAR_QUOTE_NOT_MARKED
UNSUPPORTED_EXACT_QUOTE

所以我不能接受：

canonical mapping 已正确 + small packet 后仍 5/8，因此根因是模型服从性。

quote repair 最需要的 canonical evidence 事实上还没有被 resolver 正确接住。

第二个 blocker 是 Primary Gate。

你确实已经把逻辑从 test 中抽成：

backend/tools/evaluation/o7e_evidence_checks.py

这方向正确。

但当前：

Python
Run
def check_case(case, run):
    ...
    return None

而且注释自己写了：

runner 只存名字——需要 raw log；由 gate 在运行期直接调用 primary_satisfied

。

也就是说：

primary_satisfied()
    ✅ helper 已有

Final Gate canonical path
    ❌ 还没调用

所以：

PRIMARY_TRUTH_CANONICAL_EVALUATOR

现在只能算foundation exists，还不能算 Gate 已闭合。

好消息是没必要保存整段原文。

O7-E runner 已经把：

Python
Run
done.get("evidence")

保存成：

evidence_digest

。

而你们原来的 EvidenceState 已经记录了实际 get_chapter 成功后的：

read_chapters =
book_id#chapter_idx

所以 Primary Gate 可以直接基于这些机械事实，不需要再存 full raw text。

第三个 blocker 就是你自己披露的墨子问题，而且这里我直接裁决，不再悬着。

当前 manifest 明确：

R21:
论语 = RESOLVED
墨子 = UNAVAILABLE_IN_CORPUS

R22:
墨子 = UNAVAILABLE_IN_CORPUS

。

因此原冻结宇宙不是可执行 Gate。

我不选：

R21 ALL → ANY

因为这会把原本的比较题偷偷降级成只验证孔子一侧，属于 Gate weakening。

我也不建议 O7-E 临时扩充《墨子》语料。那会把本阶段从“学术行为最终 Gate”重新扩成 corpus 建设，和现在的收口目标冲突。

所以我裁定：

废弃当前不可满足的 RP2 case universe，仅替换 R21/R22；其他 26 题完全不动，然后冻结 V2 universe。

因为 Stage B 从未运行，这不是 holdout 泄漏，也不是看到结果后换题，而是preflight 发现 case 无法机械满足后的合法修正。

建议精确替换：

R21 comparative

旧：
孔子「仁」与墨子「兼爱」的道德哲学差异？

新：
孔子的「仁」与孟子的「四端」在道德根据上有什么差异？

targets:
论语 d9272a80942a
孟子 dd03ec6572e7
mode = ALL

以及：

R22 chinese

旧：
《墨子·兼爱》的论证为什么诉诸利害而不是道德直觉？

新：
荀子为什么认为「礼义」能够改造人的欲望，
而不只是压制欲望？

target:
荀子 795658cafeab
mode = ANY

原：

670522673bd66e92...

标记：

SUPERSEDED_PRE_STAGE_B_PRIMARY_COVERAGE_FAILURE

然后生成：

O7E_RP2_HOLDOUT_V2_CASE_UNIVERSE_HASH
O7-E RP2 Calibration Closure 2
Quote Evidence Identity + Executable Gate Closure
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 118e654f2

STAGE_B_AUTHORIZED = false
DEDICATED_REPAIR_SYSTEM_PROMPT = false
MAX_VALIDATION_REPAIRS = 2

这一轮只修四件事。

1. evidence_ref 双命名空间 resolver

必须承认现在系统里本来就有两套机械 evidence identity：

Citation evidence:
ev_N

Quote-bound evidence:
qb_read_*
qb_snip_*
qb_corp_*

不要把它们强行当成一种。

实现：

resolve_repair_evidence_ref(ref, raw_tool_log)

if ref starts ev_:
    → EC._extract_candidates(raw_tool_log)
    → exact evidence_id match

if ref starts qb_:
    → QB.evidence_spans(raw_tool_log)
    → exact evidence_id match

禁止重新猜序号。

硬门：

REAL_CITATION_REF = ev_1
REAL_CITATION_REF_RESOLVED = true

REAL_QUOTE_REF = qb_read_<actual index>
REAL_QUOTE_REF_RESOLVED = true
2. Quote packet 必须给“对应 span 中的相关真实上下文”

因为 qb_read_* 已经告诉你是哪一个 source span，不再跨全库找 best window。

在该 span 内，用 Quote Bound 自己已有的 normalization / shingle 口径，机械找到与 offending locator 覆盖最高的 unit。

即：

issue locator
+
resolved qb_read span
↓
只在这个 span.units 内
按 QB 既有 7-shingle overlap
↓
best unit
↓
SOURCE_EXACT_CONTEXT <= 400

这不是旧 R4 那种：

整本/整章所有窗口
→ 自己发明一个 2-gram reranker

而是直接复用 validator 已经认可的 quote matching 语义。

禁止：

new semantic reranker
new LLM
new threshold
3. Primary Gate 真正接上 runner

check_case() 不得再：

Python
Run
return None

。

推荐基于 runner 已保存的：

run.evidence_digest.read_chapters

解析：

book_id#chapter_idx
→ read_book_ids

然后：

primary_satisfied(case, read_book_ids)

输出至少：

primary_required
primary_target_mode
resolved_targets
read_target_ids
primary_satisfied
missing_targets

无需保存 primary 正文。

硬测试：

P1 SECONDARY BOOK READ
→ false

P2 search_books only
→ false

P3 target get_chapter reflected in read_chapters
→ true

P4 ALL one side
→ false

P5 ALL both sides
→ true

P6 Final Gate aggregator actually consumes check_case()
4. Case Universe V2

只改 R21/R22，采用上面两个替代题。

要求：

OLD_CASE_UNIVERSE_HASH =
670522673bd66e92...

OLD_CASE_UNIVERSE_STATUS =
SUPERSEDED_PRE_STAGE_B_PRIMARY_COVERAGE_FAILURE

UNCHANGED_CASE_TEXTS = 26

REPLACED_CASES = 2

然后重新跑 primary preflight：

PRIMARY_REQUIRED_UNRESOLVED_TARGETS = 0

先 freeze V2，再做任何以后可能的 policy 改动。

然后只重新跑一次 8-case calibration。

这次我仍然不授权 SystemMessage。

硬门继续：

REPAIR_TRIGGERED_CASES >= 5
REPAIR_CASE_CONVERGENCE_RATE >= 0.80
EMPTY_FINAL = 0

如果这次在：

ev_N 正确解析
+
qb_* 正确解析
+
quote packet 真正包含对应原文

之后仍低于 0.80，

那我下一轮直接授权：

REPAIR_SPECIFIC_SYSTEM_LEVEL_PROTOCOL

不再继续 packet 微调。

最终回执：

O7_E_RP2_CALIBRATION_CLOSURE_2 =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

CODE_SHA=
CASE_V2_FREEZE_SHA=
HEAD_SHA=
REMOTE_SHA=

OLD_HOLDOUT_CASE_UNIVERSE_HASH=
OLD_UNIVERSE_STATUS=

NEW_HOLDOUT_CASE_UNIVERSE_HASH=
UNCHANGED_CASE_TEXTS=
REPLACED_CASES=

R21_NEW_TARGETS=
R22_NEW_TARGETS=

PRIMARY_REQUIRED_TARGETS=
PRIMARY_REQUIRED_RESOLVED_TARGETS=
PRIMARY_REQUIRED_UNRESOLVED_TARGETS=

PRIMARY_GATE_CHECK_CASE_IMPLEMENTED=
PRIMARY_GATE_AGGREGATOR_INTEGRATED=

REAL_CITATION_EVIDENCE_REF=
REAL_CITATION_REF_RESOLVED=

REAL_QUOTE_EVIDENCE_REF=
REAL_QUOTE_REF_RESOLVED=

QUOTE_REF_NAMESPACE_SUPPORTED=
qb_read/qb_snip/qb_corp

QUOTE_CONTEXT_MATCH_SCOPE=
RESOLVED_SOURCE_SPAN_ONLY

QUOTE_CONTEXT_MATCH_ALGORITHM=
QUOTE_BOUND_EXISTING_SHINGLE_SEMANTICS

REPAIR_PACKET_MAX_CONTEXT_CHARS=400
REPAIR_PACKET_LLM_CALLS=0

DEDICATED_REPAIR_SYSTEM_PROMPT=false
MAX_VALIDATION_REPAIRS=2

REPAIR_CALIBRATION_CASES=8
REPAIR_TRIGGERED_CASES=
REPAIR_CONVERGED_CASES=
REPAIR_CASE_CONVERGENCE_RATE=

REPAIR_TOTAL_INVOCATIONS=
REPAIR_INVOCATION_EFFICIENCY=
MEAN_REPAIR_INVOCATIONS_PER_TRIGGERED_CASE=
REPAIR_EXHAUSTED_CASES=

EMPTY_FINAL=
SYSTEMIC_QUOTE_DELETION=

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false
BUDGET_INCREASED=false
PRODUCTION_MODEL_CHANGED=false
PHILOSOPHER_AGENT_DIFF=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

O7E_RP2_POLICY_SHA=
仅 calibration >=0.80 后填写

STAGE_B_AUTHORIZED=false

PROPOSED_VERDICT=
PASS_TO_POLICY_FREEZE /
PATCH_REQUIRED

STOP

所以这轮最关键的新发现是：

我们以为已经修好了 evidence_ref，但实际上只修好了 citation 的 ev_N 世界；导致最多 repair 失败的 quote validator 活在 qb_read_* 世界。

这会直接影响你现在观察到的 NEAR/UNSUPPORTED 不收敛。

先把这最后一层 evidence identity 对上。如果对上之后 DeepSeek 还是不听，我就不再让 agent 继续折腾 packet，下一轮直接给它 repair 专用 system-level protocol。