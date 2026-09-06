# O3 TASK BRIEF（从 ChatGPT 抓取，含 RP1 PASS 批复头部）

```text
O2_RP1_REVIEW = PASS
O2_FINAL_REVIEW = PASS

FINAL_ANSWER_OWNERSHIP = ACCEPTED
VALIDATOR_REPAIR_LOOP = ACCEPTED
REPAIR_EXHAUSTION = ACCEPTED

ACCEPTED_SHA =
7757452e92fb23230faaa2f7a2adee96cd8f423f

O3_AUTHORIZED = true
```

O2 至此关闭。`Main Agent Writer + Runtime Verifier` 边界已经成立；repair exhaustion 也已经做到 **宁可失败收口，也绝不发布 validator 明知无效的候选答案**。

下一步直接执行：

# TASK — PhiAgent Orchestration Reset O3
## Tool Authority / Main-Agent-Owned Research Control

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
7757452e92fb23230faaa2f7a2adee96cd8f423f

PRECONDITION:

O1_FINAL_REVIEW = PASS
O2_FINAL_REVIEW = PASS

DO NOT:
- merge master
- modify preservation branch/tag
- start O4
- redesign retrieval/ranking/embedding
- delete reasoning_plan/semantic_obligations wholesale yet
- reintroduce auto-read / auto-websearch
- reintroduce runtime semantic writer
```

## 0. Architecture Goal

O1 solved:

```text
WHO DECIDES NEXT COGNITIVE ACTION?
→ Main Agent
```

O2 solved:

```text
WHO WRITES FINAL ANSWER?
→ Main Agent
```

O3 solves:

```text
WHEN MAIN AGENT DECLARES A TOOL,
WHO DECIDES WHETHER THAT TOOL IS ALLOWED TO EXECUTE?

→ Runtime only for mechanical constraints.
→ Runtime must NOT make semantic/research judgments.
```

Target:

```text
Main Agent
    ↓
declares tool
    ↓
Mechanical Gate
    ├─ schema invalid
    ├─ unavailable
    ├─ permission/safety
    ├─ cancellation
    ├─ hard resource ceiling
    ├─ exact duplicate reuse
    │
    └─ otherwise EXECUTE
            ↓
        real tool result
            ↓
        same Main Agent
```

Runtime must NOT decide:

```text
“已经有足够证据”
“这个搜索信息增益太低”
“你已经搜过两次了”
“当前 problem type 不应该用这个工具”
“这个工具不是 preferred tool”
“现在必须收口”
“现在不能再 read”
“当前 verification intent 的 quota 用完了”
```

Core target:

```text
TOOL_DECISION_OWNER = MAIN_AGENT

SEMANTIC_TOOL_ADMISSION_GATES_AFTER = 0
SEMANTIC_TOOL_FORCE_PATHS_AFTER = 0
SEMANTIC_STOP_FORCE_PATHS_AFTER = 0

ENGINE_COGNITIVE_AUTO_TOOLS = 0
```

---

## 1. FIRST REPRODUCE — Current Tool Authority

Do not modify code first.

From BASE_SHA, construct:

```text
O3_BEFORE_TOOL_AUTHORITY_TRACE
```

At minimum reproduce:

### B1 — verification quota pressure

A Main Agent scripted sequence:

```text
search_books(query A)
search_books(query B)
search_books(query C)
get_book_detail(...)
get_chapter(...)
```

Observe which declared calls execute/reject.

### B2 — sufficiency pressure

Agent:

```text
search
→ runtime considers evidence sufficient
→ Agent still declares another semantically useful search/read
```

Observe whether runtime blocks it.

### B3 — no_gain pressure

```text
search with low/no gain
→ Main Agent declares a different follow-up tool
```

Observe control effect.

### B4 — forced closeout

Find current path where:

```text
forced
收口轮
tool budget exhausted
sufficiency
obligation
```

changes tool execution.

### B5 — validation repair research

O2 repair invocation declares a new research tool after prior retrieval history.

Observe whether existing admission state blocks legitimate repair research.

For each declared tool call record:

```text
tool_call_id
decision_group_id
tool
args

MAIN_AGENT_DECLARED=true/false

ADMISSION_DECISION
ADMISSION_REASON

EXECUTED=true/false
REUSED=true/false

SEMANTIC_REASON=true/false
MECHANICAL_REASON=true/false

RESULT_RETURNED_TO_MODEL=true/false
```

Produce:

```text
MODEL_DECLARED_CALLS_BEFORE=
EXECUTED_BEFORE=
SEMANTIC_REJECTIONS_BEFORE=
MECHANICAL_REJECTIONS_BEFORE=
FORCED_CLOSEOUTS_BEFORE=
```

---

## 2. Inventory Every Tool-Control Owner

Audit production path for all code that can:

```text
reject
delay
force
replace
requeue
auto-select
stop
close out
change budget
```

a Main Agent tool decision.

Especially inspect:

```text
ObligationLedger.admit
RetrievalState
sufficiency
no_gain
forced closeout

problem_type
complexity
verification_intent
source_constraint

per-intent search/read quotas
verification-specific budgets

SkillReentryTracker
DuplicateGuard

reasoning_plan tool preference
tool_contract routing hints
preferred tools
required tools

engine soft/hard tool budget logic
repair-round admission
```

Classify every owner:

```text
MECHANICAL
SEMANTIC
TELEMETRY_ONLY
DEAD
```

Do not assume names correspond to real behavior.
Trace actual production calls.

---

## 3. Mechanical Gate Contract

After O3, runtime may reject/reuse a tool only for mechanically decidable reasons.

Allowed:

```text
INVALID_SCHEMA
INVALID_ARGUMENT_SHAPE
TOOL_NOT_AVAILABLE

PERMISSION_DENIED
SAFETY_DENIED

REQUEST_CANCELLED
TIMEOUT
TRANSPORT_FAILURE

HARD_GLOBAL_RESOURCE_CEILING

EXACT_DUPLICATE_REUSED
```

Exact duplicate means:

```text
same tool
+
canonicalized identical args
+
same relevant execution context
```

It may be:

```text
cache/reuse
```

instead of re-execution.

That is mechanical.

Runtime rejection messages must describe the mechanism.

Example:

```text
“Identical tool call already executed; prior result reused.”
```

Never:

```text
“无需继续搜索”
“证据已经充分”
“没有必要再读”
```

---

## 4. Explicitly Forbidden Semantic Gates

Remove execution authority from:

```text
LOW_GAIN
NO_GAIN
SUFFICIENCY_REACHED

PROBLEM_TYPE_MISMATCH
COMPLEXITY_LEVEL
VERIFICATION_INTENT

PRIMARY_SOURCE_OBLIGATION
PREFERRED_TOOL
SKILL_PREFERENCE

SEARCH_COUNT_FOR_INTENT
READ_COUNT_FOR_INTENT

SEMANTIC_DUPLICATE
QUERY_TOO_SIMILAR

FORCED_CLOSEOUT
SOFT_BUDGET_SEMANTIC_STOP
```

Important:

The underlying detectors may temporarily remain for telemetry because O4 will collapse cognitive modules.

But:

```text
CONTROL_EFFECT = 0
```

They may not:

```text
reject tool
force tool
stop loop
force final
change tool availability
```

---

## 5. Tool Budget Principle

Preserve a hard mechanical resource ceiling.

Do NOT preserve semantic quotas.

Correct:

```text
MAX_TOTAL_AGENT_ROUNDS
MAX_TOTAL_TOOL_EXECUTIONS
wall-clock timeout
cancellation
```

Incorrect:

```text
SOURCE_ATTRIBUTION:
search <= 2

VERIFICATION:
read <= 2

NORMAL_EXPLANATION:
tool <= 3
```

Do not invent a new complex budget matrix.

One simple global protection mechanism is preferable.

Record existing hard ceiling and any change.

---

## 6. Tool Budget Is Not Knowledge Judgment

This distinction is mandatory.

Runtime must distinguish:

```text
TOOL_NOT_EXECUTED
```

from:

```text
TOOL_EXECUTED_NO_HIT
```

and from:

```text
SOURCE_NOT_IN_LIBRARY
```

A hard ceiling means only:

```text
RESOURCE_CEILING_REACHED
```

Never imply:

```text
no such book
no such quote
no relevant source
```

if the search/read never executed.

---

## 7. Main Agent Research Policy — Evidence Appetite

Do NOT insert:

```text
“Use the minimum tools needed.”
```

Do NOT optimize for minimum tool count.

Main Agent system policy should express:

```text
Use tools proactively when they can improve reliability,
depth, or source grounding.

Do not stop merely because you already know a plausible answer.

For externally verifiable claims, quotations, source attribution,
and historical claims, prefer direct evidence over memory.

For interpretive questions, seek enough evidence to represent
the strongest relevant readings rather than settling on the first
plausible interpretation.

Continue researching while additional evidence is likely to
materially improve the answer.

Avoid redundant calls and mechanical searching that adds no
new understanding.
```

This is a research ethic for the Main Agent.

It must NOT become:

```text
Python EvidenceAppetiteGate
```

No new classifier.

No new semantic runtime policy.

---

## 8. Stop Authority

Normal stop owner:

```text
MAIN_AGENT
```

Main Agent decides:

```text
continue research
or
produce Final Candidate
```

Runtime may stop only for:

```text
hard ceiling
timeout
cancel
fatal provider/tool failure
```

Remove:

```text
sufficiency → force final
no_gain → force final
budget hint → forced closeout
obligation satisfied → forced final
```

Evidence sufficiency may remain observable:

```text
done.telemetry
```

but:

```text
SUFFICIENCY_CONTROL_EFFECT = 0
```

---

## 9. Main Agent May Continue After “Enough Evidence”

Add explicit behavior proof:

```text
Runtime telemetry says:
sufficiency=true

Main Agent still declares:
get_chapter / query_graph / another search

→ call executes
```

This is important.

`ANSWERABLE` does not imply:

```text
RESEARCH_COMPLETE
```

Runtime does not own that distinction.

---

## 10. Main Agent May Stop Before Runtime Thinks It Is Enough

Opposite test:

```text
telemetry says:
sufficiency=false

Main Agent produces Final Candidate
```

Runtime must not force an additional cognitive tool call.

Final then goes through O2 deterministic validator.

If mechanically valid:

```text
publish
```

The runtime cannot say:

```text
“你还没研究够。”
```

---

## 11. DuplicateGuard

Keep only exact mechanical duplicate protection.

Audit current behavior.

Allowed:

```text
search_books({"query":"X"})
search_books({"query":"X"})
```

Second may reuse first result.

Not allowed to block:

```text
search_books("言必有中")
search_books("夫人不言 言必有中")
search_books("鲁人为长府 闵子骞")
```

merely because semantic similarity is high.

No embedding/semantic similarity admission.

Target:

```text
EXACT_DUPLICATE_GUARD = KEEP
SEMANTIC_DUPLICATE_GUARD = REMOVE_CONTROL
```

---

## 12. Repair Loop Tool Authority

O2 repair loop must receive the same tool authority as ordinary Main Agent rounds.

Example:

```text
candidate
→ UNSUPPORTED_EXACT_QUOTE
→ Main Agent repair
→ get_chapter
```

If prior search/read history exists:

runtime must not block the new call because:

```text
no_gain
sufficiency
verification quota
forced closeout
```

Only mechanical gate applies.

This explicitly closes O2 known issue:

```text
repair research constrained by old admission governance
```

---

## 13. Auto Tool Paths Remain Forbidden

O1 behavior remains immutable:

```text
ENGINE_COGNITIVE_AUTO_TOOLS = 0
```

Therefore after removing semantic admission, do NOT “compensate” by adding:

```text
if model didn't read:
    runtime get_chapter()

if local search empty:
    runtime websearch()
```

Main Agent owns those decisions.

---

## 14. Forced Specialized Tool Routing

Audit any runtime behavior like:

```text
COMPARISON
→ compare_views required/preferred

MAP
→ conceptual_map forced

SOURCE_ATTRIBUTION
→ primary tool forced

SOCRATIC
→ socratic_tutor required
```

O3 target:

Runtime cannot force them.

Tool descriptions may explain capabilities.

Main Agent chooses.

If `reasoning_plan` still computes these fields for telemetry:

fine temporarily.

But:

```text
ROUTING_CONTROL_EFFECT = 0
```

O4 will address whether the classifier/module should exist at all.

---

## 15. Tool Contracts Boundary

After O3, tool contracts may define:

```text
tool name
arguments schema
capability description
output shape
side effects
permission/safety requirements
```

They must not be an independent cognitive router.

Remove/neutralize executable authority of:

```text
preferred route
required route
fallback cognitive strategy
semantic tool priority
```

Do not delete useful schemas.

---

## 16. Tool-Internal Delegation Boundary

Specialized tools such as:

```text
compare_views
confrontation
thought_experiment
```

may internally perform helper retrieval if that is part of the explicitly delegated capability.

O3 does NOT require redesigning all 38 tools.

But internal calls must be truthful:

```text
initiated_by = tool_internal
parent_tool_call_id = parent Main Agent tool call
```

They may not appear as fake:

```text
main_agent search_books
```

when the Main Agent never declared search_books.

Target:

```text
FAKE_TOP_LEVEL_TOOL_LOGS_AFTER = 0
```

If current evidence pool needs internal retrieval provenance,
record it explicitly as internal evidence.

Do not redesign internal reasoning algorithms yet.

---

## 17. No Hidden Tool Result

Every Main Agent-declared tool call must resolve to one of:

```text
EXECUTED_RESULT
EXACT_DUPLICATE_REUSED
MECHANICAL_REJECTION
TOOL_ERROR
CANCELLED
```

And that outcome must return to the Main Agent.

Target:

```text
UNEXPLAINED_DECLARED_TOOL_DROPS = 0
TOOL_OUTCOME_RETURNED_TO_MODEL_RATE = 100%
```

---

## 18. O3 Behavior Tests

Create:

```text
backend/tests/test_o3_tool_authority.py
```

At minimum:

### T1 — Third semantic search executes

Main Agent declares 3 distinct verification searches.

All three execute.

No per-intent quota rejection.

### T2 — Read after sufficiency

Telemetry `sufficiency=true`.

Main Agent declares `get_chapter`.

It executes.

### T3 — Continue after no_gain

Previous result `no_gain`.

Agent declares another different tool.

It executes.

### T4 — Stop despite insufficiency

Telemetry `sufficiency=false`.

Agent produces final.

Runtime does not force a cognitive tool.

O2 validator decides publishability.

### T5 — No auto-websearch

Local search empty.

Runtime does not websearch.

Next Main Agent invocation declares websearch.

It executes.

### T6 — Exact duplicate reuse

Exact same tool+args twice.

Second is mechanically reused/rejected as exact duplicate.

Result still returned to Main Agent.

No semantic language.

### T7 — Similar but distinct calls are not duplicates

Three related search queries all execute.

### T8 — Hard ceiling

At actual global hard ceiling:

new tool call mechanically fails/stops with:

```text
RESOURCE_CEILING_REACHED
```

No “evidence sufficient” implication.

### T9 — Invalid schema

Invalid tool args rejected mechanically.

### T10 — Repair research

O2 validator FAIL
→ repair Main Agent declares new get_chapter
→ executes despite prior retrieval history.

### T11 — Specialized tool provenance

Main Agent calls compare_views.

Internal helper retrieval:

```text
initiated_by=tool_internal
parent_tool_call_id != null
```

No fake top-level Main Agent search log.

### T12 — No forced specialized routing

Scripted Main Agent answers comparison using normal retrieval tools.

Runtime does not force compare_views.

### T13 — No forced closeout

Main Agent continues purposefully beyond old soft budget/sufficiency point.

Calls execute until hard mechanical ceiling or Agent stops itself.

### T14 — Tool outcome completeness

Every declared tool_call_id has a terminal outcome visible to Main Agent.

---

## 19. Static Authority Audit

Add a structural test/audit proving no production execution gate uses:

```text
problem_type
complexity
verification_intent
sufficiency
no_gain
semantic similarity
preferred_tool
obligation satisfaction
```

to:

```text
reject
force
auto-execute
force-final
```

Do not implement this as a brittle grep-only gate.

Prefer actual behavior tests plus a small static ownership audit.

Report:

```text
SEMANTIC_TOOL_CONTROL_REFERENCES=
SEMANTIC_TOOL_CONTROL_EFFECTS=
```

Target effects:

```text
0
```

Telemetry references may remain temporarily.

---

## 20. LIVE UAT

Real Main Agent.

### U1 — 言必有中出处

Expected:

```text
Main Agent search/read autonomously
semantic admission rejects = 0
primary text can be read
validator integrity preserved
```

### U2 — Research-heavy source verification

Choose a case requiring multiple distinct localization attempts.

Require:

```text
>=3 purposeful searches
>=1 read
```

if the model naturally decides so.

Do NOT force counts in prompt solely to satisfy metric.

The key is:

no old semantic quota blocks it.

### U3 — Deep synthesis

Use a QG2-style deep synthesis.

Require:

```text
Agent may continue research after answerable state
no forced closeout
depth not degraded
```

### U4 — Local miss → web

Use a query where local corpus misses.

Expected:

```text
local result
→ Main Agent sees miss
→ Main Agent decides websearch or honest downgrade

runtime websearch = 0
```

### U5 — zero-tool

Simple conceptual question.

Agent can answer with zero tools.

Runtime does not force research.

### U6 — Validator repair research

Trigger O2 validation issue.

Expected:

```text
repair invocation
→ Main Agent chooses research
→ tool executes
→ repaired final
```

No old quota interference.

### U7 — specialized tool

Agent voluntarily calls one Phase T specialized tool.

Check parent/internal provenance.

---

## 21. BEFORE / AFTER Metrics

Report:

```text
MODEL_DECLARED_TOOL_CALLS=

EXECUTED_TOOL_CALLS=
EXACT_DUPLICATE_REUSES=
MECHANICAL_REJECTIONS=

SEMANTIC_REJECTIONS_BEFORE=
SEMANTIC_REJECTIONS_AFTER=

FORCED_TOOL_PATHS_BEFORE=
FORCED_TOOL_PATHS_AFTER=

FORCED_CLOSEOUTS_BEFORE=
FORCED_CLOSEOUTS_AFTER=

SUFFICIENCY_CONTROL_EFFECT_BEFORE=
SUFFICIENCY_CONTROL_EFFECT_AFTER=

NO_GAIN_CONTROL_EFFECT_BEFORE=
NO_GAIN_CONTROL_EFFECT_AFTER=

PROBLEM_TYPE_ROUTING_EFFECT_AFTER=
VERIFICATION_INTENT_ROUTING_EFFECT_AFTER=

UNEXPLAINED_DECLARED_TOOL_DROPS=
TOOL_OUTCOME_RETURNED_TO_MODEL_RATE=

ENGINE_COGNITIVE_AUTO_TOOLS=
FAKE_TOP_LEVEL_TOOL_LOGS=
```

Targets:

```text
SEMANTIC_REJECTIONS_AFTER = 0
FORCED_TOOL_PATHS_AFTER = 0
FORCED_CLOSEOUTS_AFTER = 0

SUFFICIENCY_CONTROL_EFFECT_AFTER = 0
NO_GAIN_CONTROL_EFFECT_AFTER = 0

PROBLEM_TYPE_ROUTING_EFFECT_AFTER = 0
VERIFICATION_INTENT_ROUTING_EFFECT_AFTER = 0

UNEXPLAINED_DECLARED_TOOL_DROPS = 0
TOOL_OUTCOME_RETURNED_TO_MODEL_RATE = 100%

ENGINE_COGNITIVE_AUTO_TOOLS = 0
FAKE_TOP_LEVEL_TOOL_LOGS = 0
```

---

## 22. Quality Must Not Collapse

Compare against O2:

```text
PRIMARY_READ_RATE
CITATION_INTEGRITY
QUOTE_INTEGRITY

RESEARCH_DEPTH
ANSWER_DEPTH

AVG_TOOLS
P50_LATENCY
P95_LATENCY
```

Important:

```text
MORE TOOLS != automatically worse
FEWER TOOLS != automatically better
```

Evaluate:

```text
epistemic gain
source grounding
depth
non-redundancy
```

We explicitly do NOT want the old regression:

```text
runtime blocks research
→ model memory compensates
→ answer looks plausible but evidence is weak
```

---

## 23. O3 Scope Guard

Do NOT yet wholesale delete:

```text
reasoning_plan.py
semantic_obligations.py
answer_composer.py
interpretation_engine.py
epistemic_guard.py
```

O3 removes their **tool-control authority**.

O4 will decide which cognitive modules can now be deleted/collapsed.

Do NOT redesign:

```text
vector retrieval
ranking
embedding
KG
Persona
conversation memory
frontend
38 specialized tools wholesale
```

---

## 24. Full Regression

Run exact:

```bash
pytest backend/tests -q
```

No exclusions.

Also report separately:

```text
O1 causal
O1 thinking safety
O2 final ownership
O3 tool authority
```

Requirements:

```text
FAILED = 0
SKIPPED = accurately reported
```

---

## 25. Documentation

Generate:

```text
docs/PHIAGENT_O3_TOOL_AUTHORITY.md
```

Must include:

```text
BEFORE tool authority graph
AFTER mechanical gate graph

all former semantic admission owners
which control effects were removed

mechanical gate contract
global ceiling
duplicate behavior

Evidence Appetite policy

repair-loop tool authority
specialized-tool internal provenance

T1–T14
U1–U7
before/after metrics
known issues

explicit candidates for O4 deletion
```

Do not start O4.

---

## 26. Git

Commit:

```text
refactor(phiagent): return tool authority to main agent
```

Push:

```text
refactor/phiagent-main-agent-orchestration
```

Do not merge master.

---

# FINAL RECEIPT

```text
O3 = READY_FOR_REVIEW / NOT_READY

BASE_SHA=
FINAL_SHA=
REMOTE_SHA=

CHANGED_FILES=

TOOL_DECISION_OWNER=

SEMANTIC_TOOL_ADMISSION_GATES_BEFORE=
SEMANTIC_TOOL_ADMISSION_GATES_AFTER=

SEMANTIC_REJECTIONS_BEFORE=
SEMANTIC_REJECTIONS_AFTER=

MECHANICAL_GATE_REASONS=

FORCED_TOOL_PATHS_BEFORE=
FORCED_TOOL_PATHS_AFTER=

FORCED_CLOSEOUTS_BEFORE=
FORCED_CLOSEOUTS_AFTER=

SUFFICIENCY_CONTROL_EFFECT_BEFORE=
SUFFICIENCY_CONTROL_EFFECT_AFTER=

NO_GAIN_CONTROL_EFFECT_BEFORE=
NO_GAIN_CONTROL_EFFECT_AFTER=

PROBLEM_TYPE_ROUTING_EFFECT_AFTER=
VERIFICATION_INTENT_ROUTING_EFFECT_AFTER=

EXACT_DUPLICATE_GUARD=
SEMANTIC_DUPLICATE_GUARD=

GLOBAL_HARD_CEILING=

ENGINE_COGNITIVE_AUTO_TOOLS=
FAKE_TOP_LEVEL_TOOL_LOGS=

UNEXPLAINED_DECLARED_TOOL_DROPS=
TOOL_OUTCOME_RETURNED_TO_MODEL_RATE=

REPAIR_LOOP_TOOL_AUTHORITY=

TOOL_INTERNAL_PROVENANCE=

T1=
T2=
T3=
T4=
T5=
T6=
T7=
T8=
T9=
T10=
T11=
T12=
T13=
T14=

U1=
U2=
U3=
U4=
U5=
U6=
U7=

PRIMARY_READ_RATE=
CITATION_INTEGRITY=
QUOTE_INTEGRITY=
RESEARCH_DEPTH=

AVG_TOOLS=
P50_LATENCY=
P95_LATENCY=

O1_CAUSAL_TESTS=
O1_THINKING_SAFETY_TESTS=
O2_OWNERSHIP_TESTS=
O3_TOOL_AUTHORITY_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

O4_DELETION_CANDIDATES=

REPORT=
docs/PHIAGENT_O3_TOOL_AUTHORITY.md

KNOWN_ISSUES=

STOP
```

**不得开始 O4。**

O3 的判断标准只有一个核心问题：

```text
Main Agent:
“我要调用这个工具。”

Runtime:
“schema/safety/resources mechanically okay?”

YES
→ execute.
```

而不是 Runtime 再补一句：

```text
“但根据我对哲学问题的理解，你其实已经查够了。”
```

那种判断从 O3 开始正式不再属于 Runtime。