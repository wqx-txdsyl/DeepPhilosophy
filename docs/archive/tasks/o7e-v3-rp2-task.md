
我审完 2c224d7c3 → 5835da17a。这轮 V3-RP1 可以签 PASS_FOR_DIAGNOSIS，而且现在根因范围已经缩得很小了：不是 Local Patch，不是 judge，不是 primary evidence，也不是“模型为了安全所以被冤枉”；是 R25 在一个 REQUIRED 的学术能力场景里，安全地失败了。

正式裁定：

O7_E_V3_RP1_REVIEW = PASS_FOR_DIAGNOSIS

V3_DELIVERY_GATE = PASS
V3_SCHOLARLY_GATE = FAIL
O7_E_STATUS = NOT_CLOSED

V3_HOLDOUT_CONSUMED = true

TAIL_FAILURE_CELLS = 2
UNIQUE_TAIL_FAILURE_CASES = 1

TAIL_CASE = R25
QUESTION =
王阳明的「知行合一」如何批评朱熹的「格物」？

INTERPRETIVE_PLURALITY = 0
LITERATURE_ORIENTATION = 0

R25_SAFE_FALLBACK_BEHAVIOR = PASS

R25_REQUIRED_INTERPRETIVE_CAPABILITY = FAIL
R25_REQUIRED_LITERATURE_CAPABILITY = FAIL

MEASUREMENT_CHAIN = CLOSED
JUDGE_CHANGE = NOT_AUTHORIZED
GATE_CHANGE = NOT_AUTHORIZED
APPLICABILITY_CHANGE = NOT_AUTHORIZED

LOCAL_PATCH_REOPEN = false

Tail audit 本身是干净的：两个 <2 不是两个 case，而是同一个 R25 的两个 tail cell；两维都是三票 0/0/0，primary replay 是 4/4 完整，fatal=0。更关键的是，真实 telemetry 是 3 次 search_scholarship、0 次 fetch、0 content evidence。

所以回执中引用答案自己说的“两次检索”不能作为机械事实；canonical tool telemetry 是：

R25_SCHOLARLY_SEARCH_CALLS = 3
R25_SCHOLARLY_FETCH_CALLS = 0
R25_CONTENT_EVIDENCE_COUNT = 0
R25 到底算不算 Contract V4 的“模范执行”？

要拆成两件事。

它在安全/诚实策略上确实执行正确：

检索结果不相关
→ 没有 content evidence
→ 不伪造学者观点
→ 不硬构造“学界两派”
→ 回退到能够证明的原典分析

这一点应该记：

R25_SAFE_FALLBACK_BEHAVIOR = PASS

而且这也是为什么它没有任何 fabricated attribution、bibliography、access overclaim 等 fatal。

但这不等于这个 case 的产品能力通过。

V3 在模型运行之前已经把 R25 的：

interpretive_plurality
literature_orientation

预注册成 REQUIRED。系统真正需要证明的是：

对这个中国哲学问题，我不仅能在找不到资料时诚实退缩，还应该有足够的 scholarly retrieval / synthesis 能力把相关研究找到，并完成学术对话。

现在它做到了前半句，没有做到后半句。

所以不存在真正的合同矛盾，而是：

Safety obligation:
找不到证据时不要编
                ✅

Capability obligation:
本题应能取得足够研究并完成 REQUIRED 学术能力
                ❌

这正是 REQUIRED_DIMENSION_MEDIAN_LT_2 这道 tail gate 存在的意义。否则 27 个 case 很强、一个领域完全掉到 0，也会被总体均值掩盖。

因此我不授权现在去做任何这些事情：

R25 literature → OPTIONAL      ❌
R25 IP → OPTIONAL              ❌
MEDIAN_LT_2 gate 删除          ❌
judge 对“诚实没搜到”自动加分   ❌
重新解释 V3 为 PASS           ❌

那都会是在看完 holdout 后移动球门。

还有一个很小但真实的工具问题：o7e_final_gate.py 当前对这个 V3 的 FAIL 判定是正确的，但它还没有真正做到 fail-closed。

例如：

Python
Run
if (_num("REQUIRED_DIMENSION_MEDIAN_LT_2") or 0) != 0:

意味着这个字段如果整个缺失，也会被当成 0 而通过；fatal key 也有同样问题。脚本目前也没有强制检查：

EVALUATION_INVALID == false
JUDGE_CASES_VALID == JUDGE_CASES_EXPECTED
JUDGE_CASES_MISSING == 0

。

这不改变当前 V3 verdict，因为本轮 canonical artifact 的 MEDIAN_LT_2=2 是明确存在的；但既然这个 helper 是我们以后防止“artifact FAIL、receipt PASS”的最后机械保险，它必须在下一轮顺手 fail-close。

这属于checker correctness，不是重新开启 judge/measurement 设计。

下一步：O7-E V3-RP2
Scholarly Retrieval Coverage RCA

先不要改 Contract V5，也不要扩 corpus。

我们目前只知道：

R25 发起 scholarly search       ✅
结果相关性不足                  ✅
继续 fetch                      ❌
content evidence                ❌
最终 scholarly capability       ❌

但还不知道最关键的一层：

为什么搜不到？

可能至少有五种完全不同的根因：

QUERY_FORMULATION_FAILURE
RETRIEVAL_RANKING_FAILURE
CORPUS_COVERAGE_GAP
ACCESS_DEPTH_GAP
PROVIDER_COVERAGE_GAP

所以先做零 Agent / 零 Judge / 零网络 RCA。

IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 5835da17a

NEW_AGENT_RUN = false
NEW_JUDGE_RUN = false
NETWORK_CALLS = 0

PRODUCTION_CHANGE = false
PROMPT_CHANGE = false
JUDGE_CHANGE = false
REPLAY_CHANGE = false
GATE_CHANGE = false

V3_VERDICT = V3_SCHOLARLY_GATE_NOT_MET
V3_HOLDOUT_CONSUMED = true
§0 — Final Gate helper fail-close

只修机械 checker。

所有冻结 gate 字段：

missing
≠
0

而应：

missing
→ FAIL

scholarly 至少必须强制存在并满足：

JUDGE_CASES_EXPECTED
JUDGE_CASES_VALID
JUDGE_CASES_MISSING
EVALUATION_INVALID

APPLICABLE_DIMENSION_MEAN
全部 required dimension means

REQUIRED_DIMENSION_MISSING_SCORE
REQUIRED_DIMENSION_MEDIAN_LT_2

六个 fatal count

Hard：

JUDGE_CASES_VALID == JUDGE_CASES_EXPECTED
JUDGE_CASES_MISSING == 0
EVALUATION_INVALID == false

Delivery 侧同理，冻结的 required metric 缺字段必须 FAIL。

锁 4 个最重要 regression：

missing MEDIAN_LT_2
→ FAIL

missing one fatal key
→ FAIL

EVALUATION_INVALID=true
→ FAIL

JUDGE_CASES_MISSING=1
→ FAIL

当前 V3 重放仍必须机械输出：

DELIVERY_GATE=PASS
SCHOLARLY_GATE=FAIL
FAILED_GATES=["REQUIRED_DIMENSION_MEDIAN_LT_2"]
§1 — 从已存在 V3 artifact 提取 R25 的真实 retrieval trace

禁止新检索。

从：

docs/evidence/o7e_calib_V3_HOLDOUT.json

按时间顺序导出 R25 的 3 次真实：

search_scholarship

每次保存：

call_index
query
filters / args
provider mode
returned_count

每条返回：
source_record_id
title
authors
year
source_category
access_level
provider
rank

如果 artifact 有 fetch，则一并导出；按当前 canonical telemetry 预期：

FETCH_CALLS=0

但以 artifact 为准，不凭回执猜。

同时记录：

R25_TOOL_SELF_REPORT_TEXT = “两次检索……”
R25_ACTUAL_SCHOLARLY_SEARCH_CALLS = 3
SELF_REPORT_MATCH = false

仅 observability，不新增产品 gate。

§2 — 离线检查 O7-D 本地 scholarly corpus

只读当前冻结 registry / FTS，不得联网。

用 RCA-only query families 测试：

王阳明
Wang Yangming
Wang Shouren

朱熹
Zhu Xi

知行合一
unity of knowledge and action

格物
gewu
investigation of things

Neo-Confucianism
Song-Ming Confucianism

Great Learning
Daxue

这些名字只允许存在于：

RCA artifact / test

绝不能因此硬编码进 production prompt。

记录每个查询：

LOCAL_FTS_HITS
TOP_K_TITLES
RELEVANT_HITS
ACCESS_LEVEL

这里不是让 GLM 判断“看起来相关”。

尽量用现有 registry 的明确 metadata 做机械审计；需要人工 reviewer 才能确认 relevance 的条目放：

RELEVANCE_REVIEW_REQUIRED

不要偷偷新增 semantic classifier。

§3 — IP=0 也单独查，不要全部归因于 literature

R25 的两个 0 未必完全是同一个故障。

额外检查它 4 个已读 primary chapters：

WANG_PRIMARY_EVIDENCE_PRESENT =
ZHU_PRIMARY_EVIDENCE_PRESENT =

如果王、朱两侧原典本来都已取得，但最终答案仍完全只从王阳明一侧重构：

PRIMARY_INTERPRETIVE_SYNTHESIS_GAP =
SUPPORTED

因为即便没有现代二手文献，Main Agent 仍可以诚实地区分：

王阳明如何批评朱熹
vs
朱熹自己的文本是否完全等于王阳明所批评的那个版本

只要它不冒充“学界两派”，这种 primary-grounded alternative 并不违反 Contract V4。

反之，如果原典证据本身也是单边的：

PRIMARY_INTERPRETIVE_SYNTHESIS_GAP =
NOT_DEMONSTRATED

不要凭结果倒推。

§4 — 根因分类

最终只能从证据分类：

QUERY_FORMULATION_FAILURE =
本地存在相关记录，良好查询能命中，
但 Agent 实际 query 没命中

RETRIEVAL_RANKING_FAILURE =
Agent 实际 query 已匹配相关记录，
但相关记录落在返回 top-k 之外

CORPUS_COVERAGE_GAP =
当前 O7-D registry/index 根本没有相关研究

ACCESS_DEPTH_GAP =
相关记录确实返回，
但只有 metadata / 无可读内容证据，
且不存在本地可读替代

PROVIDER_COVERAGE_GAP =
只有在既有 captured provider evidence 足以证明时才能判；
RP2 禁止为此新联网

PRIMARY_INTERPRETIVE_SYNTHESIS_GAP =
双侧 primary evidence 已在 run 中，
但回答没有形成有纪律的替代解释

MIXED =
多个独立 blocker 同时成立

很可能最后是 MIXED，但现在禁止预判。

然后根据 RCA 决定产品刀法：

QUERY_FORMULATION_FAILURE
→ Scholarly Contract V5:
   relevance poor 时自主 reformulate
   canonical names / romanization /
   author+concept / translated terminology
   无固定 retry 次数

RETRIEVAL_RANKING_FAILURE
→ retrieval mechanics patch
   bilingual alias / normalization / ranking

CORPUS_COVERAGE_GAP
→ O7-D Chinese philosophy scholarly expansion
   做领域覆盖，不做 R25 专用补丁

ACCESS_DEPTH_GAP
→ abstract/fulltext availability expansion

PRIMARY_INTERPRETIVE_SYNTHESIS_GAP
→ Main Agent synthesis contract patch

MIXED
→ 对应组合

仍然遵守：

ONE BRAIN
SEMANTIC_ROUTER = 0
AUTO_SEARCH = 0
AUTO_FETCH = 0

R25 从现在开始只能作为 development regression，不能再用于最终 qualification。

修完产品后，需要：

NEW_UNTOUCHED_HOLDOUT

来真正关 O7-E；V3 这 28 题不能重跑后重新叫 Final Holdout。

回执：

O7_E_V3_RP2 = READY_FOR_REVIEW

BASE_SHA=5835da17a

GATE_HELPER_HARDEN_SHA=
RCA_SHA=

HEAD_SHA=
REMOTE_SHA=

NEW_AGENT_RUN=false
NEW_JUDGE_RUN=false
NETWORK_CALLS=0

FINAL_GATE_FAIL_CLOSED=true

TAIL_FAILURE_CELLS=2
UNIQUE_TAIL_CASES=1

R25_SEARCH_CALLS=3
R25_QUERY_1=
R25_QUERY_2=
R25_QUERY_3=

R25_RETURNED_RECORDS_TOTAL=
R25_RELEVANT_RECORDS_RETURNED=
R25_FETCH_CALLS=
R25_CONTENT_EVIDENCE_COUNT=

R25_WANG_PRIMARY_PRESENT=
R25_ZHU_PRIMARY_PRESENT=
PRIMARY_INTERPRETIVE_SYNTHESIS_GAP=

LOCAL_REGISTRY_RELEVANT_RECORDS=
LOCAL_FTS_ALT_QUERY_HITS=

QUERY_FORMULATION_FAILURE=
RETRIEVAL_RANKING_FAILURE=
CORPUS_COVERAGE_GAP=
ACCESS_DEPTH_GAP=
PROVIDER_COVERAGE_GAP=

ROOT_CAUSE=
QUERY_FORMULATION_FAILURE /
RETRIEVAL_RANKING_FAILURE /
CORPUS_COVERAGE_GAP /
ACCESS_DEPTH_GAP /
PRIMARY_INTERPRETIVE_SYNTHESIS_GAP /
MIXED

PRODUCTION_CHANGED=false
PROMPT_CHANGED=false
JUDGE_CHANGED=false
GATE_CHANGED=false

V3_HOLDOUT_CONSUMED=true

PROPOSED_NEXT=
QUERY_FORMULATION_PATCH /
RETRIEVAL_MECHANICS_PATCH /
CORPUS_EXPANSION /
ACCESS_DEPTH_PATCH /
SYNTHESIS_PATCH /
COMBINED

STOP

现在这个失败其实很有价值：整个 V3 不是被幻觉、引文错误、delivery 或历史纪律击穿，而是在 28 个案例里精准暴露出一个领域性 scholarly coverage tail——王阳明/朱熹这个 case。

而 R25 做到“找不到就不编”值得保留；下一步不是教它“找不到也要硬写两派”，而是查清楚为什么一个已经会主动搜索的 Agent，在这里连续搜了 3 次仍拿不到真正相关的学术材料。

You've reached the maximum length for this conversation, but you can keep talking by starting a new chat.

Start new chat