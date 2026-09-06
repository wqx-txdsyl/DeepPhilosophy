# O3 RECON & PLAN（侦察结论 + 改造设计，仅本地）
BASE = 7757452e92fb23230faaa2f7a2adee96cd8f423f（O2 FINAL PASS）

## 控制 owner 清单（6 个）与处置
1. ObligationLedger.admit（engine tools_node 闸1, agent_runtime:791-877）
   - 语义部分：query_family Jaccard≥0.45 判族 / family exec limit(2) / low_gain 族拒绝 /
     obligations_satisfied 总闸 / vi 分项配额（SEARCH_CAP=2, READ_CAP=2, META_CAP=1, WS_CAP=1-2）/
     复杂度包络 SEARCH_EXEC_LIMIT(2/4/3/6)+TOTAL_RETRIEVAL_LIMIT(3/5/3/10) / forced 轮只放未读 get_chapter
   - 机械部分：(book_id,chapter_idx) 已读/pending 判重（=EXACT_DUPLICATE）
   - 处置：tools_node 不再因 admit 拒绝执行。ledger 保留为 telemetry（record/mark_result 照旧，
     admit 仍可调用但返回恒通过并继续计数）→ CONTROL_EFFECT=0。精确重复由 DuplicateGuard 负责。
2. SkillReentryTracker.admit（tool_contracts:161-248, engine 闸1b）：SEMANTIC（purpose Jaccard 相似/同工具 cap3）
   → 移除拒绝权（telemetry only，admit 调用保留但恒通过，或 engine 不再消费拒绝结果）。
3. DuplicateGuard（agent_runtime:183-222）：MECHANICAL 精确归一判重（sha1(工具+归一参数)）→ 保留，
   复用时 ToolMessage 回旧结果（结果仍回模型✓），措辞机械（"重复调用已拦截"可保留/微调为 EXACT_DUPLICATE_REUSED 语义）。
4. agent_node forced 注入 4 源（engine:301-412）：
   a. budget.hard_reached → MECHANICAL 保留，但注入文案须机械（现有 HARD_BUDGET_DIRECTIVE 可用，
     需检查不暗含"库中无此书"）；forced 轮中新宣告的工具 → tools_node 机械拒绝 RESOURCE_CEILING_REACHED（T8）
   b. ledger.rejected>=3 → 随准入删除自然消失 → 移除触发
   c. no_gain_streak>=3 force（+streak2 warn）→ 移除控制（streak 留 done telemetry）
   d. sufficiency verdict force（vi: obligations_satisfied or exec>=4；非 vi: sufficiency_verdict）→ 移除控制
     （sufficiency 结论仅 done telemetry）
5. should_continue（engine:727-739）：仅保留 hard_reached 的 forced 补跑一轮后 end；
   其余一律 tools（模型宣告了工具就执行/机械拒绝）。移除 forced 语义触发。
6. validator/证据契约的 vi constraint（PRIMARY_ONLY/AUTHOR_ONLY）：final-answer 引用资格（O2 域），
   非工具控制 → 保留，文档注明。

## 其他必改
- soft budget：检查 agent_node 中 soft_reached 的用途 → 任何"收口提示"控制效果移除，仅 telemetry。
- 伪 search_books 条目（engine:658-676）：加 initiated_by="tool_internal"、parent_tool_call_id、
  parent_tool、pseudo=True 结构化字段（FAKE_TOP_LEVEL_TOOL_LOGS=0 的审计依据）；形状保持兼容证据池。
- 系统提示：铁律 1 已有"不追求最少工具"；按 §7 注入 Evidence Appetite 研究伦理段
  （主动检索/不止步于貌似可行/外部可验证主张优先直接证据/解释题寻找最强解读/有实质增益就继续/避免冗余调用）。
  禁止变成 Python EvidenceAppetiteGate。
- 工具结果措辞：准入拒绝消息删除后不再出现"检索收敛/无需继续搜索"类语义措辞；
  DuplicateGuard 复用消息改为机械描述（EXACT_DUPLICATE_REUSED: same tool+identical args, prior result reused）。
- tool_note "（检索收敛）该调用与已有检索重合或超出预算" 随准入删除而消失。
- verif_box computed 不刷新（repair 轮）→ 非工具控制，O3 不动（telemetry）。

## BEFORE 指标（代码级, BASE 7757452e9）
SEMANTIC_TOOL_ADMISSION_GATES_BEFORE = 5（ledger.admit / reentry.admit / no_gain force / sufficiency force / ledger.rejected force）
SEMANTIC_REJECTIONS_BEFORE = ledger.admit 全部分支 + reentry.admit（family/cap/purpose）
FORCED_CLOSEOUTS_BEFORE = 4 触发源（hard + rejected3 + no_gain3 + sufficiency）
SUFFICIENCY/NO_GAIN CONTROL_EFFECT_BEFORE = force stop + forced 准入收缩
FORCED_TOOL_PATHS_BEFORE = COMPARISON/MAP prompt 注入（纯提示）+ SEARCH_EXEC_LIMIT["COMPARISON"]=3 执行侧收紧
AFTER 全部 = 0；GLOBAL_HARD_CEILING 保留（hard_retrieval=20/hard_total=24 + RESOURCE_CEILING_REACHED 机械拒绝）

## 测试要点（test_o3_tool_authority.py T1–T14）
- 复用 test_phase_a._run_tools_node（直接驱动 tools_node；注意它没传 ledger/reentry → 改造后闸1移除，恰好）
- engine 级用 test_o2_final_ownership 的 ScriptedChat harness（script 多轮宣告）
- T1 3 连不同 search 全执行；T2 sufficiency=true 仍读；T3 no_gain 后换工具仍执行；
  T4 sufficiency=false 模型直接 final 不被强制工具（O2 validator 把关）；T5 本地空→不自动 websearch、宣告则执行；
  T6 精确重复→复用且结果回模型；T7 相似不同 query 全执行；T8 硬上限→RESOURCE_CEILING_REACHED；
  T9 非法 schema 机械拒绝；T10 repair 轮 get_chapter 执行；T11 compare_views 内部检索 provenance
  （initiated_by=tool_internal + parent_tool_call_id）；T12 comparison 题不强制 compare_views；
  T13 无 forced closeout（旧 soft/sufficiency 点后仍继续）；T14 每个宣告的 tool_call_id 都有终态。

## 已知风险
- 删语义准入后 live 行为变化：模型可能多检索（AVG_TOOLS 上升 = 允许，"MORE TOOLS != worse"）
- budget.count 的 info_gain/no_gain 计数保留（telemetry）；hard_reached 判定保留
- test_patch1_1 的 ObligationLedger.admit 单测：类逻辑保留 → 单测应继续通过（telemetry 化不动类）
- test_phase_a 的 no_gain/hard 引擎级用例：no_gain force 用例需改写为"无控制效果"断言
