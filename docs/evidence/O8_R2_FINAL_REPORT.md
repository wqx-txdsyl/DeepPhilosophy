# O8-R2 Execution Audit — Final Report（PhiAgent）

> REVIEWED_BASE = 63732e09da98363b15b89e3954f47842c2c6c563（clean isolated worktree, porcelain=='' 验证）
> 审计范围: 72-case capability benchmark / 32-tool Mechanical Gate / Agentic Gate /
> tool rationalization / efficiency measurement / LOCAL_CURATED census /
> primary-text coverage census / orphan ownership / repair-safety measurement。
> 本轮只 MEASURE / AUDIT / CLASSIFY，零 production 行为变更。
> 机器可读件: O8_R2_CAPABILITY_RESULTS.json / O8_R2_EFFICIENCY.json /
> O8_R2_TOOL_AUDIT.json / O8_R2_RETRIEVAL_CENSUS.json /
> O8_R2_REPAIR_SAFETY_AUDIT.json / O8_R2_INTERACTION_OWNERSHIP.json。

## 1. 执行概况

| 项 | 值 |
|---|---|
| benchmark | 72/72 执行, 72 COMPLETED, **0 运行错误**, 69/72 发布（3 例干净拒绝） |
| judge | 72/72（glm-4.6, temperature=0, 固定 7 轴 + 12 维 schema）, 0 judge 错误 |
| Mechanical Gate | 32/32 工具 × 9 检查（含 N/A 显式理由） |
| Agentic Gate | 32/32 工具 SHOULD_CALL 探针 + 6 共享场景（NOTCALL/MULTI×2/BAD_FIRST/DEGRADED/RECOVERY） |
| 效率遥测 | 453 LLM 调用 / 1132 工具调用 / 1086 检索轮 / 793 重复调用 / 11,411,945 tokens（TOKEN_COST=null, COST_SOURCE=UNAVAILABLE） |
| repair | 50/72 case 触发 repair, 共 60 轮; 47 case 出现「引入后清除」, 3 case 终态残留 |
| 环境隔离 | 全部测量在 clean isolated worktree @ REVIEWED_BASE; 主工作树未提交的 409→410 manifest diff 未触碰 |

## 2. 能力画像（judge 维度均值, 0-4）

**强项**（≥3.4）: expression_naturalness 3.76 / explanation_quality 3.67 / argument_quality 3.58 /
philosophical_depth 3.56 / evidence_discipline 3.49 / textual_accuracy 3.40。

**弱项**（<3）: **efficiency 0.89**（54/72 案低于 2 分）/ **retrieval_strategy 1.61**（33 案<2）/
**tool_selection 2.22**（22 案<2）/ convergence 2.67（13 案<2）/ scholarship 3.06。

**诚实性**: honesty_flag=2（O8R2-23/24, 均为 04 类比较题; 两者连同 O8R2-10 共 3 例被
冻结 final gate 干净拒绝发布——**发布门兜底有效, 拒绝是合同行为而非伪造放行**）。
DEGRADED 探针（张载《正蒙》不在库）产出教科书级诚实降级：多路检索确认不在库 →
如实说明核验状态 → 记忆内容标注「转述/未经核验」→ 不伪造逐字引文（AG-SHARE-DEGRADED）。

**工具选择（Agentic SHOULD_CALL）**: 30/32 命中。未命中：paper_review（以 analyze_argument
替代）、**get_scholarly_source**（有 search_scholarship 命中但不取全文/摘要——学术双链第二跳缺口）。
NOTCALL 场景零工具调用，负向纪律满分。

## 3. 效率审计（最大系统性缺口）

- **793 次重复调用, 分布于 69/72 案例**（同名工具同参）——engine 的 A2 DuplicateGuard
  未挡住 agent 的实际重复检索形态。
- 检索轮均值 15.08/case（最高 24）; **cat10 简单题均值 8.83 次工具调用**（期望 0-1 次）,
  51/72 案例被判 overresearch; efficiency 维度均值 0.89。
- token 总量 11.41M（输入 10.88M）——过度检索直接放大成本。
- 证据: O8_R2_EFFICIENCY.json aggregate + overresearch_analysis + 各 case efficiency 字段。

## 4. Mechanical Gate 发现（真实工具缺陷, 非 N/A 类）

- **[O8R2-MECH-1, P1]** philosopher_debate 在 `speakers` 为 JSON 数组时崩溃
  （agent_tools_memory.py:520 `speakers.replace` 假设 str; LLM 调用方可能合法地传数组）。
- **[O8R2-MECH-2, P1]** search_books 向量路径无空查询守卫、相似度地板 0.35 过低——
  伪查询/空查询稳定返回不相关结果，EMPTY_RESULT 语义不可达（与 retrieval_strategy 1.61 互证）。
- **[O8R2-MECH-3, P2]** query_graph / get_philosopher / get_school 空字符串输入静默回退默认实体（柏拉图）。
- **[O8R2-MECH-4, P2]** concept_trace 对不存在概念返回模糊命中; list_books / history_timeline
  过滤无命中时返回全集（无空结果语义）。

## 5. Repair Safety 测量（O8-R1 裁定分类的量化）

- **LOCAL_PATCH 路径**: 既有 `evaluate_repair_safety` 门实际有效（定义 :1488 / 调用 :2378;
  AMBIGUOUS fail-closed; QUOTE/CITATION/BIBLIOGRAPHIC 家族 GENUINELY_NEW 拒绝; 拒绝回滚
  pre-patch candidate）。本轮仅验证, 未重做实现。
- **FULL_REWRITE / non-local 路径**: 全引擎安全门调用点唯一且被 `_lp_meta is not None`
  守卫 → 该路径**无** post-repair 语义验证 / 无新证据族检测 / 无 AMBIGUOUS fail-closed /
  无回滚 parity / 直接替换 candidate（仅 frozen final_validator 下一轮兜底）。
  与 O8-R1 裁定的 FULL_REWRITE_SAFETY_GAP 完全一致; **本轮只测量, 不实现 parity**。
- 47/50 repair 案例出现「repair 引入→后续清除」瞬态（V12-08 家族形态的成本证据）;
  3 案例终态残留并全部被发布门拒绝（诚实拒绝）。
- 测量缺口: runner 未捕获 REPAIR_OUTPUT_MODES（full_rewrite vs local_patch 每案观测）,
  已在 per_case 留空并在此声明。

## 6. Retrieval / Corpus Census

- **LOCAL_CURATED**: 587 records / 408 accepted cluster / DOI 覆盖 99.8% / stable_urls 覆盖 ~100% /
  长摘要（≥400ch）仅 79 条（13.5%）/ 年份 1947-2026 / 语言字段未记录 / DOI 零重复。
- **Primary Text**: catalog=410（books.json）; 有真实文本 333 本（12,768 章节文件, 抽样可读 333）;
  无可验证文本 77 本（全部 txt 占位）; chapter files = catalog+1 系统性偏移（0.json 书名页, 惯例良性）。
- **CANONICAL_COUNT=410 / MISMATCH=1**（tracked O7B manifest 记 409, catalog 记 410;
  主工作树未提交 diff 即对账修正——**只报告, 不修数据**, SOURCE_OF_TRUTH=clean checkout books.json）。
- 72-case 使用: 学术检索命中 case 数与原典链命中 case 数见 O8_R2_RETRIEVAL_CENSUS.json O8R2_CASE_HITS。

## 7. Interaction / Orphan Ownership

6 个孤儿文件全部**零外部引用**（组内互引不计; conversationSync.js 在 agent-app/src 无 importer）:
- backend/jwt_verify.py, backend/upstream.py, backend/user_profile_store.py,
  backend/routes/agent_history.py, backend/routes/auth_proxy.py → DELETE_CANDIDATE
- agent-app/src/data/conversationSync.js → 无 importer, 功能半成品 → DEPRECATE/DELETE_CANDIDATE
- 按 Reviewer C 项裁定: **本轮全部不删除不入库**, 仅产建议; 「零引用」≠「可安全删除」, 去留属用户资产决定。

## 8. 缺口清单（P0 / P1 / P2 / WONT_FIX）

### P0（系统性, O10 统一修复的主对象）
- **P0-1 检索过度研究/重复调用**: 793 重复调用/69 案; 检索轮均值 15.08; 简单题 8.83 工具调用;
  efficiency 均值 0.89; 51/72 overresearch。→ 修复方向: Main Agent 检索策略纪律（计划-检索-收敛）
  + DuplicateGuard 对同参重复的实际拦截 + 简问题的无工具直答路径。
  证据: O8_R2_EFFICIENCY.json / dimension_statistics.efficiency=0.89 / AG-NOTCALL 对照。
- **P0-2 工具选择纪律**: hard primary 题零语料接触（O8R2-13: 0 工具/4.1s 出全文答案）;
  get_scholarly_source 第二跳缺失（Agentic miss）; tool_selection 均值 2.22。
  证据: O8_R2_CAPABILITY_RESULTS per_case O8R2-13 / O8_R2_TOOL_AUDIT should_call_hits。

### P1（明确工程缺口, O10 修复）
- **P1-1** philosopher_debate speakers 数组崩溃（O8R2-MECH-1; agent_tools_memory.py:520）。
- **P1-2** search_books 向量路径空查询/相关性地板缺失（O8R2-MECH-2）。
- **P1-3** repair 瞬态引入率 47/50（「引入后清除」成本; V12-08 家族）+ FULL_REWRITE 安全 parity
  缺失（§5 路径测量）——O10 按既有裁定实现 parity。
- **P1-4** 比较类问题诱发越出语料的逐字引用（04 类 2/6 干净拒绝）——需要原典锚定的比较策略。

### P2（质量/卫生改进）
- **P2-1** 空输入静默默认实体（O8R2-MECH-3, 三工具）。
- **P2-2** 空结果语义缺失（O8R2-MECH-4, 三工具）。
- **P2-3** LOCAL_CURATED 长摘要覆盖 13.5%、语言字段缺失（census; 扩充属 corpus 政策, 需授权）。
- **P2-4** 书目对账 409 vs 410 MISMATCH + 77 txt 占位无文本（primary-text coverage policy 输入）。
- **P2-5** 6 个零引用孤儿文件清理（待用户逐个裁定去留）。

### WONT_FIX（本轮明确不做）
- 诚实拒绝行为本身（3 例未发布是发布门的正确行为, 不是缺陷）。
- corpus 扩库 / LOCAL_CURATED 内容扩充（Reviewer B 项: 实际 corpus 改动留待 O9/O10 证据之后）。
- V12 三项冻结失败（CLOSED_WITH_KNOWN_QUALIFICATION_FAILURES; 冻结不动）。
- judge / final gate / qualification thresholds（冻结不动）。

## 9. 结论

PhiAgent 的答案质量轴（哲学深度/论证/解释/表达）与诚实性合同表现扎实（强项 ≥3.4,
0 伪造发布, 干净拒绝 3 例, 诚实降级教科书级）；**系统性短板集中在检索经济性与工具选择纪律**
（efficiency 0.89 / retrieval_strategy 1.61 / tool_selection 2.22 + 793 重复调用），
其次是 repair 瞬态成本与 FULL_REWRITE 安全 parity 缺口、少量工具契约健壮性问题。
以上全部归类与证据已备齐，**O10 统一修复的对象与优先级由此定义**；O9（MetaSo/研究检索）
按 roadmap 独立进行，其证据将与本报告共同决定 corpus/retrieval 层的最终形态。

— Builder: ZCode / GLM-5.3, 2026-09-12, clean isolated worktree @ 63732e09d
