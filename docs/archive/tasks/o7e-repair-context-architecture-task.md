我审完 b90d87644 → b14646b15。这次我正式签发架构瓶颈结论，但要先纠正回执和实验 harness 里的两个统计问题。

O7_E_REPAIR_DEPTH_ABLATION_REVIEW = PASS_FOR_DIAGNOSIS

FULL_CONTEXT_FULL_REWRITE_REPAIR_ARCHITECTURE_BOTTLENECK =
CONFIRMED

THIRD_REPAIR_PRODUCT_VALUE =
NOT_DEMONSTRATED

MAX_VALIDATION_REPAIRS_3 =
REJECTED

MAX_VALIDATION_REPAIRS =
RETAIN_2

FOURTH_REPAIR =
NOT_AUTHORIZED

MODEL_POOL_EXPANSION =
NOT_AUTHORIZED

REPAIR_CONTEXT_ARCHITECTURE =
AUTHORIZED

V3_STAGE_B_AUTHORIZED =
false
先纠正实验数字

o7e_repair3.py 对 AT_2 的计算有一个 bug：

Python
Run
if len(hist) >= 3:
    at2_ok = bool(hist[2].get("ok"))

这会把“初检即 PASS”和“第 1 次 repair 后 PASS”的 case 的 VALID_AFTER_2 留成 None，随后又被：

Python
Run
published_at_2 = bool(at2_ok)

错误计成 false。

完整 artifact 里：

S7  [0]     初检即 PASS
H03 [1,0]   repair1 后 PASS
S9  [3,4,0] repair2 后 PASS
H07 [2,1,0] repair2 后 PASS

因此真正的“两轮上限结果”是：

PUBLICATIONS_AT_2 = 4/8
REPAIR_CONVERGED_AT_2 = 3/7
REPAIR_CONVERGENCE_AT_2 = 0.429

不是 receipt 的 3/8，也不是 tracked summary 中的 2/8 / 0.286。

而第三轮之后仍然是：

PUBLICATIONS_AT_3 = 4/8
REPAIR_CONVERGED_AT_3 = 3/7
REPAIR_CONVERGENCE_AT_3 = 0.429

所以真正的实验结论反而比回执更强：

2 repairs → 4/8
3 repairs → 4/8

incremental publications = 0
incremental converged cases = 0

第三轮没有带来任何收益。

四个真正进入第三轮资格的 case 是 H04、H13、S4、H02，其中 REPAIR3_RESCUED_CASES=0 这个核心结论是成立的。

不过还有一个观测细节：H04、H13、H02 都有完整的 initial → r1 → r2 → r3 四个 validation 状态，并在第三轮继续 plateau；S4 虽然 repairs_used=3，history 却只有 [6,3,3] 三个 validation 状态，所以不能严谨地声称“S4 的 r3 后仍为 3”，这里只能标为 third-repair terminal observation incomplete。

这个不影响“0 rescue”的裁定，但下阶段会一起把 telemetry 修掉。

另外，client-path 代码现在确实已经建立了统一的 build_candidate_langchain_client()，repair-depth 实验的 normal / repair 两边都从这个 builder 构建。 但你回执中的“LangChain Stage-A 13/16”没有覆盖进 tracked evidence；当前 HEAD 的 o7e_ablation_A_RP-B_summary.json 仍是旧的 16/16。 这是 provenance 小缺口，下阶段开头补掉即可，不影响这次结构性诊断。

为什么现在可以正式判“架构瓶颈”

目前我们已经逐层排除了：

evidence_ref 命名空间错误
→ 修了

repair evidence 没到模型
→ E2E 证明到了

repair system protocol 优先级不足
→ system-level 注入

temperature 随机性
→ repair temp=0

thinking 对 repair 的干扰
→ V4-Pro RP-B thinking=disabled

output budget
→ 8000

client/config drift
→ matched configuration

第二轮不够
→ 第三轮实验

模型选择
→ 两代 DeepSeek + 多代 GLM 已广泛试过

而最终残留模式仍然是：

完整长答案
   ↓
validator 找到 1~N 个局部 quote/citation issue
   ↓
Main Agent 被要求重新生成完整答案
   ↓
部分 issue 修掉
   ↓
剩余局部 NEAR issue
   ↓
再次完整生成
   ↓
同类 issue plateau

当前 ValidationIssue 本来就已经提供 code / locator / evidence_ref / detail，也就是说 validator 知道问题是局部的。

但 engine 的修复方式依然是：

旧完整 candidate
+
validator feedback
+
packet
→ Main Agent
→ 重新输出完整 replacement final candidate

。

这就是下一阶段真正该动的地方。

不是“上下文太长”这么简单。

更准确的诊断是：

局部、机械、可定位的证据错误，被映射成了高编辑面（high edit surface）的整篇重写任务。

O7-E RP2 RCA-1
Localized Repair Context Architecture
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
b14646b15

TARGET_AGENT =
general

EVALUATION_MODEL =
deepseek-v4-pro

EVALUATION_CONFIG =
RP-B

MAX_VALIDATION_REPAIRS =
2

PRODUCTION_LOCAL_PATCH_ENABLED =
false

V3_HOLDOUT_RUN =
false

这一阶段不再研究第 3 次、第 4 次 repair。

目标只有一个：

FULL-CANDIDATE REWRITE
        ↓
LOCALIZED MAIN-AGENT PATCH

同时继续满足：

COGNITIVE_POLICY_OWNER = 1
FINAL_WRITER = MAIN_AGENT
REPAIR_AGENT_COUNT = 0
0. 先关 repair-depth artifact bookkeeping

先修：

VALID_AT_2
PUBLICATIONS_AT_2
REPAIR_CONVERGENCE_AT_2

早期 PASS 必须计入。

正确算法语义：

state_at_cap(N) =
在 initial + 最多 N 次 repair 内达到的最终 validation state

不是要求 history 长度必须达到 N+1。

重新生成：

o7e_repair3_RP-B_summary.json

正确值必须是：

PUBLICATIONS_AT_2=4
PUBLICATIONS_AT_3=4

REPAIR_CONVERGED_AT_2=3
REPAIR_CONVERGED_AT_3=3

REPAIR3_RESCUED_CASES=0

同时把 LangChain parity 的真实 Stage-A result 单独归档，不覆盖旧的 16/16 历史 artifact。

第三轮 telemetry 增加：

repair_invoked
post_repair_validation_observed

于是 S4 这种：

repairs_used=3
history only initial+r1+r2

必须显式标：

POST_REPAIR3_VALIDATION_OBSERVED=false

不能伪装成 plateau。

1. 新建 Repair Issue Bundle

建议新增：

backend/repair_context.py

它只做机械上下文构造。

每个 validator issue 变成：

JSON
{
  "issue_id": "vi_1",
  "code": "NEAR_QUOTE_NOT_MARKED",

  "anchor": {
    "start": 1234,
    "end": 1312,
    "surface_sha256": "...",
    "surface_preview": "..."
  },

  "evidence_ref": "qb_read_7",

  "source": {
    "book": "...",
    "chapter": "...",
    "exact_context": "..."
  }
}

关键变化：

以前：
“答案里有这么一句有问题”

现在：
“candidate SHA=X 的字符 [1234:1312]
 就是 vi_1 的修改对象”
2. Anchor 必须是 exact candidate-local anchor

不能继续只靠：

locator preview

让模型自己在几千字答案里找。

要求：

candidate_sha256
span_start
span_end
span_sha256

全部机械生成。

formal citation 可以直接用现有 citation regex 定位。

quote issue 应复用 Quote Bound 的 quote extraction 语义；允许给 extract_quotes() 增加：

char_start
char_end

这种 metadata。

禁止修改：

EXACT / NEAR / MEMORY_ONLY 判定语义
NEAR_THRESHOLD
quote eligibility

即：

QUOTE_BOUND_MATCHING_SEMANTICS_CHANGED=false
3. Evidence packet 从“全局最多 3 条”改为 issue-complete

当前 builder 的：

Python
Run
max_evidence=3

是整个 repair packet 的总 ceiling。

这意味着 4 个 issue 时，理论上至少一个 issue 可以拿不到自己的 linked evidence。

新合同：

MAX_EVIDENCE_PER_ISSUE = 2
MAX_CONTEXT_PER_EVIDENCE = 400
MAX_TOTAL_REPAIR_CONTEXT_CHARS = 6000

最重要的 hard invariant：

如果 issue.evidence_ref 可解析
→ 该 issue 的 bundle 必须包含对应 evidence

即：

LINKED_EVIDENCE_STARVATION = 0

不是简单把全局 3 → 8。

4. Main Agent 不再重写整篇答案

对于局部 validator issue：

UNVERIFIED_CITATION
UNSUPPORTED_EXACT_QUOTE
NEAR_QUOTE_NOT_MARKED
STITCHED_QUOTE

进入：

LOCAL_PATCH

模式。

EMPTY_FINAL 等无法局部锚定的问题仍然走现有：

FULL_REWRITE

这个分流只看 deterministic validator issue code：

SEMANTIC_REPAIR_ROUTER = 0
5. Local Patch 输出合同

同一个 Main Agent 最终输出严格结构：

JSON
{
  "candidate_sha256": "...",
  "patches": [
    {
      "issue_id": "vi_1",
      "anchor_sha256": "...",
      "action": "REPLACE_TEXT",
      "replacement_text": "..."
    }
  ]
}

再额外允许一种 action：

COPY_EVIDENCE_SLICE

形式：

JSON
{
  "issue_id": "vi_2",
  "anchor_sha256": "...",
  "action": "COPY_EVIDENCE_SLICE",
  "evidence_ref": "qb_read_7",
  "source_start": 42,
  "source_end": 91
}

这非常重要。

对于逐字引文，不再要求模型：

“看着原文，再自己重新敲一遍原文。”

而是：

Main Agent 决定使用哪个 evidence slice，runtime 只机械复制那个 slice。

这仍然符合 one-brain：

语义选择 = Main Agent
文字来源 = retrieved evidence
复制动作 = runtime mechanical apply

Runtime 没有自行决定该引用什么。

6. Mechanical Patch Applier

新增纯机械：

apply_main_agent_patches()

只能做：

验证 candidate SHA
验证 anchor SHA
验证 issue_id
验证 patch 非重叠
验证 evidence slice 确实属于指定 evidence
按 start 倒序替换

禁止：

自动改写句子
自动选证据
自动删引文
自动补引用
自动 paraphrase

即：

RUNTIME_GENERATED_PROSE_CHARS = 0
7. 非目标正文必须 byte-preserved

这是这套架构最核心的优势之一。

Hard invariant：

NON_TARGET_TEXT_CHANGED_CHARS = 0

除 patch anchor 范围外，旧 candidate 原样保存。

这样：

修第 12 段一句引文

就不会重新生成：

前 11 段 + 后 5 段

也就大幅减少修 A 又重新破坏 B 的机会。

8. Patch 必须覆盖 validator issue，而不是整个答案

每轮：

candidate
↓
validator
↓
RepairIssueBundle
↓
same Main Agent patch
↓
mechanical apply
↓
full validator

如果仍 FAIL：

重新针对新的 candidate 建新的 anchors
↓
repair2

仍然最多两轮。

9. Patch JSON 错误也算一次 repair attempt

例如：

candidate_sha mismatch
anchor stale
overlap
bad evidence slice
missing required issue patch
invalid JSON

都产生纯机械：

PATCH_PROTOCOL_ERROR

反馈给同一个 Main Agent。

禁止 runtime 默默猜修。

10. 工具权力不变

如果 repair 时仍有预算：

Main Agent 仍可调用 tools

tool loop 完成后最终非-tool turn 必须输出 patch JSON。

如果 hard budget reached：

no_tools=true

保持 RP1 已验收语义。

所以：

MAIN_AGENT_TOOL_AUTHORITY = unchanged
11. 不能用 patch 架构玩“删引文保平安”

加入 hard anti-gaming：

PREEXISTING_VERIFIED_EXACT_QUOTES_LOST = 0

PREEXISTING_VALID_CITATIONS_LOST_OUTSIDE_PATCH = 0

SYSTEMIC_QUOTE_DELETION = 0

已通过 Quote Bound 的原文，只要不是当前 issue anchor，就必须 byte-preserved。

12. Telemetry

只记录：

candidate_sha
issue_ids
issue_codes

anchor sha/start/end

patch action
replacement length
evidence_ref
evidence slice offsets

non_target_changed_chars

post_patch_validation issues

禁止：

raw CoT
reasoning_content
完整 hidden repair prompt
13. Production 先不切

这一轮必须：

LOCAL_PATCH_REPAIR_IMPLEMENTED=true
LOCAL_PATCH_REPAIR_PRODUCTION_ENABLED=false

评价 harness 才允许打开。

线上现有行为仍然：

full rewrite
MAX_REPAIRS=2

直到我 review。

14. Evaluation

使用：

deepseek-v4-pro
RP-B

仍然是之前那 8 个 calibration cases。

Run 1：

8 cases

要求：

COMPLETED=8
PUBLISHED>=7

EMPTY_FINAL=0

if REPAIR_TRIGGERED>=3:
  REPAIR_CASE_CONVERGENCE>=0.80

ANCHOR_RESOLUTION_RATE=1.0

LINKED_EVIDENCE_STARVATION=0
NON_TARGET_TEXT_CHANGED_CHARS=0

PATCH_PROTOCOL_FATAL_ERRORS=0

PREEXISTING_VERIFIED_EXACT_QUOTES_LOST=0

如果 Run 1 不过：

STOP

不要调 prompt。

15. Run 1 过了才跑 Run 2

相同：

model
config
policy
packet
patch protocol

再完整跑一次。

正式 architecture qualification：

RUN1 >= 7/8
RUN2 >= 7/8

两轮 repair convergence 均 >=0.80
EMPTY=0

用来防止我们再次被单轮幸运值骗过去。

16. 如果 Local Patch PASS

我下一步会授权：

LOCAL_PATCH_REPAIR_PRODUCTION_ENABLED=true

然后冻结：

repair architecture
V4-Pro RP-B config
policy
runner
evaluator

再跑 academic calibration。

双轴通过后才碰：

V3 28-case untouched Holdout
17. 如果 Local Patch 仍失败

那下一步才审：

anchor quality
issue grouping
COPY_EVIDENCE_SLICE semantics
evidence completeness

而不是：

repair 3→4
换第 9 个模型
降低 Gate
必测回归
A1 citation issue exact anchor
A2 quote issue exact anchor
A3 duplicate preview cannot silently choose wrong span

A4 stale candidate SHA rejected
A5 stale anchor SHA rejected
A6 overlapping patches rejected

A7 COPY_EVIDENCE_SLICE copies exact source substring
A8 invalid slice rejected

A9 REPLACE_TEXT uses only Main-Agent text
A10 runtime prose generation = 0

A11 4 issues each receive linked evidence
A12 global evidence starvation impossible

A13 applying one patch changes zero bytes outside target
A14 two non-overlapping patches apply atomically

A15 successful patch → whole candidate revalidated
A16 failed patch → repair2 gets fresh anchors

A17 EMPTY_FINAL stays full-rewrite
A18 local quote/citation issues use LOCAL_PATCH

A19 tools remain available when budget remains
A20 no_tools semantics unchanged

A21 philosopher agent diff = 0
A22 production patch mode default = false
最终回执
O7_E_RP2_RCA1 =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

BOOKKEEPING_FIX_SHA=
RCA_CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

CORRECTED_PUBLICATIONS_AT_2=
CORRECTED_PUBLICATIONS_AT_3=
CORRECTED_REPAIR_CONVERGENCE_AT_2=
CORRECTED_REPAIR_CONVERGENCE_AT_3=
REPAIR3_RESCUED_CASES=0

STAGE_A_PARITY_ARTIFACT=
STAGE_A_PARITY_VALID=

REPAIR_CONTEXT_MODULE=

LOCAL_PATCH_REPAIR_IMPLEMENTED=
LOCAL_PATCH_REPAIR_PRODUCTION_ENABLED=false

LOCALIZABLE_ISSUE_CODES=

CANDIDATE_ANCHOR_RATE=
AMBIGUOUS_ANCHORS=

MAX_EVIDENCE_PER_ISSUE=
MAX_TOTAL_REPAIR_CONTEXT_CHARS=
LINKED_EVIDENCE_STARVATION=

PATCH_ACTIONS=
REPLACE_TEXT,COPY_EVIDENCE_SLICE

RUNTIME_GENERATED_PROSE_CHARS=0

NON_TARGET_TEXT_CHANGED_CHARS=

PREEXISTING_VERIFIED_EXACT_QUOTES_LOST=
PREEXISTING_VALID_CITATIONS_LOST_OUTSIDE_PATCH=

RUN1_COMPLETED=8
RUN1_PUBLISHED=
RUN1_REPAIR_TRIGGERED=
RUN1_REPAIR_CONVERGED=
RUN1_REPAIR_CONVERGENCE=

RUN2_EXECUTED=
RUN2_COMPLETED=
RUN2_PUBLISHED=
RUN2_REPAIR_CONVERGENCE=

EMPTY_FINAL=

PATCH_PROTOCOL_ERRORS=
SYSTEMIC_QUOTE_DELETION=

MAX_VALIDATION_REPAIRS=2

FINAL_VALIDATOR_ACCEPTANCE_SEMANTICS_CHANGED=false
QUOTE_BOUND_MATCHING_SEMANTICS_CHANGED=false

MODEL=deepseek-v4-pro
REPAIR_CONFIG=RP-B

PRODUCTION_MODEL_CHANGED=false
V3_HOLDOUT_RUN=false

PHILOSOPHER_AGENT_DIFF=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
AUTHORIZE_LOCAL_PATCH_PRODUCTION /
PATCH_REQUIRED

STOP

这次不用再犹豫“是不是差第 3 次”。

不是。

按完整 artifact 修正统计后，其实是：

2 repairs = 4/8
3 repairs = 4/8
third-repair rescues = 0

而不是回执里看起来的 3/8 → 4/8。

所以从现在开始，问题从：

“再给 Main Agent 一次机会会不会好？”

正式切换成：

“为什么一个只错了一句引文的 5000 字答案，要让 Main Agent重新写 5000 字？”

RCA-1 就是把这个结构性错误拆掉。