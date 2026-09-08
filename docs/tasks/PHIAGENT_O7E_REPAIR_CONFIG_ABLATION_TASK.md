我审完 30e55055a → 4cfb60491。这次我不签“8 个候选已经穷尽，因此该上第三轮 repair”。

我接受的结论只有更窄的一条：

当前已经实际跑完、且配置证据可信的 full-E2E configuration
没有一个通过 O7-E 双硬门。

但 NO_MODEL_QUALIFIED 还不能升级成“模型路线已穷尽”。因为我抓到了一个足以解释你所说“micro fixture 很强、E2E 全崩”的重大 confound：Stage A 和 Stage B 根本没有使用同一套冻结 repair configuration。

正式裁定：

O7_E_MODEL_BAKEOFF_V2_REVIEW = PATCH_REQUIRED

CURRENT_OBSERVED_CONFIGURATIONS_QUALIFIED = 0
MODEL_POOL_EXHAUSTION = NOT_PROVEN

DEEPSEEK_V4_PRO_CURRENT_E2E_CONFIG = FAIL
DEEPSEEK_V4_FLASH_QUALIFICATION = INVALIDLY_CONFOUNDED
GLM_5_3_QUALIFICATION = INVALIDLY_CONFOUNDED
GLM_5_3_FLASH_QUALIFICATION = INVALIDLY_CONFOUNDED

MICRO_TO_E2E_GAP = REAL
MICRO_TO_E2E_GAP_ROOT_CAUSE = NOT_ISOLATED

MAX_VALIDATION_REPAIRS_3 = NOT_AUTHORIZED
GATE_REDUCTION = REJECTED
DUAL_MODEL_REPAIR_AGENT = REJECTED

REPAIR_MODE_CONFIG_ABLATION = AUTHORIZED
V3_STAGE_B_AUTHORIZED = false
最关键的发现：Stage A / Stage B 不是 apples-to-apples

现在 V2 candidate manifest 只冻结了：

normal.temp = 0.7
repair.temp = 0.0

没有冻结：

max_tokens
thinking mode
reasoning_effort
client implementation

。

而 Stage A 的 canonical 代码仍然写死：

Python
Run
payload = {
    "temperature": 0,
    "max_tokens": 4000,
    ...
}

并且没有显式写 thinking 配置。

但你追踪进 HEAD 的 deepseek-v4-pro Stage-A artifact 又是：

16 / 16
EMPTY = 0

。

这与回执自己披露的：

4000 token 首跑有 2/16 EMPTY，之后改 8000 才变成 16/16

直接说明：

最终 16/16 是用一个没有被当前 HEAD 的 Stage-A runner 表达出来的配置跑出来的。

所以它不是 canonical-reproducible Stage-A result。

更关键的是 Stage B 对 V4/GLM5 又单独做了另一套 override：

Python
Run
max_tokens = 8000

# DeepSeek V4
thinking = enabled
reasoning_effort = low

而且 normal 和 repair 都使用这套 explicit thinking 配置。

于是我们现在其实在比较：

Stage A:
direct HTTP
4000 / 某次手工 8000
thinking 未冻结

vs

Stage B:
LangChain client
8000
DeepSeek thinking=enabled
reasoning_effort=low

这已经足够让：

Stage A 16/16
Stage B repair 2/6

不能直接证明“复杂上下文导致 repair 能力坍塌”。

复杂上下文可能是原因，但实验还没有隔离它。

这还直接影响另外三个模型的淘汰

deepseek-v4-flash 是：

14 / 16
EMPTY = 2

。

而它正好是在 canonical Stage-A 4000-token harness 下跑的。

既然 V4-Pro 自己已经实证：

4000 → 出 EMPTY
8000 → EMPTY 消失

那我们没有资格一边给 Pro 用 8000 重赛，一边拿 Flash 的 4000 结果直接淘汰 Flash。

同理：

glm-5.3       0/16, EMPTY=16
glm-5.3-flash 8/16, EMPTY=8

。

这两个结果最多证明：

当前 Stage-A 调用配置下无法稳定产生 content。

还不能证明：

模型本身不适合作为 PhiAgent。

尤其 receipt 已经明确说 GLM 的失败形态是 reasoning 吃满 output budget。

所以我现在不授权第三次 repair

你建议：

MAX_VALIDATION_REPAIRS
2 → 3

现在证据还不够。

因为如果 repair invocation 本身的：

thinking
output budget
client path

都没有统一，那么第三轮只是：

给一个尚未定义清楚的 repair configuration 再多一次机会。

这不能告诉我们架构到底对不对。

而且目前 deepseek-v4-pro 的真实 full E2E 确实很差：

4 / 8 published
2 / 6 repair converged
= 0.333

。

离“多一轮就能救回来”还太远。

还有一个 academic judge blocker

judge2 现在确实已经复用了 O7-A 的：

JUDGE_SYSTEM_PROMPT
build_judge_input
render_judge_prompt
validate_verdict
DIMENSIONS
FATAL_FLAGS

这个方向我接受。

但它实际传入的所谓：

PRIMARY_TEXT_EVIDENCE

现在只是：

Python
Run
{
    "source": "read_chapters",
    "chapters": [...]
}

也就是章节 ID，没有原文 evidence。

同时 evidence_digest 又被截到 2000 字。

因此以后若某模型终于过 mechanical Gate，judge 要判断：

FALSE_EXACT_QUOTE
PRIMARY_TEXT_MISREPRESENTATION
TEXTUAL_GROUNDING

时仍可能缺真正的 primary evidence。

还有一个更隐蔽的问题：

judge 可以把某维判成 NOT_APPLICABLE → score=null；

随后代码又把 applicability 强行改成 manifest 的 REQUIRED，但 aggregate 只统计：

Python
Run
REQUIRED and median is not None

于是一个：

manifest = REQUIRED
judge score = null

的必评维度会直接从 denominator 消失。

这个在最终学术 Gate 前也必须关掉。

下一轮：不再扩大模型池，也不再改 prompt

我授权一个很小、但决定性的实验：

O7-E BAKEOFF V2.1
Matched Repair Configuration Ablation
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 4cfb60491

V3_HOLDOUT_RUN = false
MAX_VALIDATION_REPAIRS = 2

SCHOLARLY_CONTRACT_CHANGED = false
REPAIR_SYSTEM_PROTOCOL_CHANGED = false
REPAIR_PACKET_CHANGED = false
FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false

核心目标只有一句：

Stage A 和 Stage B 必须真的调用完全相同的 repair client configuration。

1. Candidate config 单一真源

不要再在：

o7e_bakeoff.py
o7e_bakeoff_b.py
manifest

分别手写配置。

新增单一：

BakeoffCandidateConfig

至少包含：

candidate_id
provider
base_url_class
requested_model

normal_temperature
normal_max_tokens
normal_thinking
normal_reasoning_effort

repair_temperature
repair_max_tokens
repair_thinking
repair_reasoning_effort

Stage A、Stage B 全部调用同一个：

build_candidate_client(config, mode)

Hard：

CANDIDATE_CONFIG_OWNER = 1
STAGE_A_REPAIR_CONFIG == STAGE_B_REPAIR_CONFIG
2. 记录实际调用身份

每次 trial 必须记录：

requested_model
response_model
temperature
max_tokens
thinking_mode
reasoning_effort
finish_reason
content_chars
reasoning_chars

不得存 reasoning 内容本身。

Hard：

REASONING_CONTENT_STORED = false

这样我们终于能分清：

EMPTY because model failed
vs
EMPTY because output budget全部耗在 reasoning
3. 先只测 V4-Pro

不要再烧四个模型。

因为 V4-Pro 已经同时具备：

micro repair potential = 16/16
full research capability
general API deployability

当前唯一值得隔离的是 repair mode。

冻结 normal：

MODEL = deepseek-v4-pro
NORMAL:
  temperature = 0.7
  max_tokens = 8000
  thinking = enabled
  reasoning_effort = low

normal 不动。

repair 只做两个预先声明的 configurations：

RP-A
temperature = 0
max_tokens = 8000
thinking = enabled
reasoning_effort = low

也就是当前 Stage-B repair。

RP-B
temperature = 0
max_tokens = 8000
thinking = disabled

前提是 general API preflight 确认该模型支持。

如果 provider 不支持：

RP-B = INCOMPATIBLE

不要模拟。

4. 为什么允许关 thinking

这不违反 one-brain。

仍然是：

deepseek-v4-pro
        ↓
同一个 Main Agent

只是：

research generation
→ reasoning enabled

deterministic evidence repair
→ reasoning disabled

和我们此前已经允许：

normal temp 0.7
repair temp 0

属于同一类 invocation configuration。

它不是 Repair Agent，也不是第二模型。

5. Stage A 重新跑，但只作为 config verification

每个 RP config：

8 fixtures × 2 = 16

必须：

>= 13/16
EMPTY = 0

并且这次 artifact 里 config 必须完整。

如果 RP-A 不再复现之前的高分：

说明此前 16/16 本身存在 config drift

如实记录。

6. Stage B 采用 sequential Gate，省钱

只给 Stage-A PASS 的 config 跑已有 8-case calibration。

先跑一次 8-case。

如果：

published <= 5/8

或：

repair triggered >=3
and convergence <0.60

直接判该 config FAIL，不跑第二遍。

如果第一次达到：

published >=7/8
and
repair convergence >=0.80

再用同配置完整重复一次 8-case。

最终 qualification 要：

RUN1 PASS
RUN2 PASS

因为我们已经看过太多：

7/8 → 3/8

这种方差。

不再让单次幸运值决定生产模型。

7. 两轮都 PASS 才冻结

要求：

TOTAL_E2E_CASE_RUNS = 16
TOTAL_PUBLICATIONS >= 14

RUN1_PUBLICATIONS >=7
RUN2_PUBLICATIONS >=7

每轮：
if repair_triggered >=3
    repair_convergence >=0.80

EMPTY_FINAL = 0

然后才进入 academic judge。

8. 如果 RP-B 仍失败

如果：

matched config
+
thinking disabled repair
+
8000 output
+
protocol/packet unchanged
+
2 repairs

仍显著失败

那我会第一次真正接受：

FULL_CONTEXT_REPAIR_ARCHITECTURE_BOTTLENECK = SUPPORTED

到那时再决定：

2 → 3 repairs

或者改变 repair input architecture。

不是再换第九、第十个模型。

9. 暂时不要重跑 V4-Flash / GLM5

先让 V4-Pro 把这个变量隔离掉。

如果 V4-Pro RP-B 成功，我们就没必要继续烧别的。

如果失败，再用同一个 canonical config factory重新测：

v4-flash
glm-5.3
glm-5.3-flash

届时它们才是公平数据。

10. Academic judge 顺手修，但先不调用

修两个 mechanical blocker。

必评维不得消失

如果 manifest：

REQUIRED

但 vote：

score=null

则：

vote/case evaluation invalid

不能从 denominator 消失。

Hard：

REQUIRED_DIMENSION_MISSING_SCORE = 0
Primary evidence 真输入

至少把已有安全 mechanical evidence：

quote_bound verified entries
used primary evidence
read chapter identities
citation provenance

放进 PRIMARY_TEXT_EVIDENCE。

若 fatal 所需的证据根本没提供给 judge：

不得让 judge 凭空判 FALSE_EXACT_QUOTE

最终 judge 仍由 O7-A constitution 单一持有。

最终回执
O7_E_BAKEOFF_V2_1 =
READY_FOR_REVIEW /
NO_CONFIG_QUALIFIED /
BLOCKED

BASE_SHA=

CONFIG_FACTORY_SHA=
CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

CANDIDATE_CONFIG_OWNER=1

MODEL=deepseek-v4-pro

NORMAL_TEMP=0.7
NORMAL_MAX_TOKENS=8000
NORMAL_THINKING=enabled
NORMAL_REASONING_EFFORT=low

RP_A_REPAIR_THINKING=enabled
RP_B_REPAIR_THINKING=disabled

STAGE_A_STAGE_B_REPAIR_CONFIG_EQUAL_RP_A=
STAGE_A_STAGE_B_REPAIR_CONFIG_EQUAL_RP_B=

REQUESTED_RESPONSE_MODEL_MISMATCH=

--- RP-A ---
STAGE_A_VALID=/16
STAGE_A_EMPTY=

E2E_RUN1_PUBLISHED=/8
E2E_RUN1_REPAIR_TRIGGERED=
E2E_RUN1_REPAIR_CONVERGED=
E2E_RUN1_REPAIR_CONVERGENCE=

E2E_RUN2_EXECUTED=
E2E_RUN2_PUBLISHED=/8
E2E_RUN2_REPAIR_CONVERGENCE=

RP_A_HARD_GATE=

--- RP-B ---
STAGE_A_VALID=/16
STAGE_A_EMPTY=

E2E_RUN1_PUBLISHED=/8
E2E_RUN1_REPAIR_TRIGGERED=
E2E_RUN1_REPAIR_CONVERGED=
E2E_RUN1_REPAIR_CONVERGENCE=

E2E_RUN2_EXECUTED=
E2E_RUN2_PUBLISHED=/8
E2E_RUN2_REPAIR_CONVERGENCE=

RP_B_HARD_GATE=

EMPTY_FINAL=

REQUIRED_DIMENSION_MISSING_SCORE=
CANONICAL_JUDGE_CONSTITUTION_OWNER=1

MAX_VALIDATION_REPAIRS=2
PRODUCTION_MODEL_CHANGED=false
V3_HOLDOUT_RUN=false

FULL_TESTS=

PROPOSED_VERDICT=
SELECT_CONFIG /
NO_CONFIG_QUALIFIED

STOP

所以这次我不接受：

“8 个旗舰全试完了，模型路线没救。”

当前更准确的是：

我们试了很多模型，但 Stage-A 与 Stage-B 的 repair configuration 没有真正冻结成同一个实验条件。

特别是 V4-Pro：Stage-A 的 canonical runner 还是 max_tokens=4000，最终 artifact 却来自你披露的 8000-token 重跑；而 Stage-B 又显式用了 8000 + thinking enabled。

这个变量比“第三次 repair”优先级高得多。

先把实验做干净。匹配配置后的 V4-Pro 如果还崩，我再授权真正的架构变化。