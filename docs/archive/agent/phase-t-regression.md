# PhiAgent Phase T — Regression Report（Tool Architecture Rationalization）

> HEAD_BEFORE = HEAD_AFTER = ec09e04da914d55ba3904fc5812785b2f81729f6（未提交; Patch1/1.1 工作区冻结状态延续）
> RUNTIME = backend/main.py（python 3.11, 127.0.0.1:8011）, MODEL = deepseek-chat（thinking enabled）
> LIVE 回归 = 真实 HTTP SSE（`tools/_tmp/phase_t_client.py`）; 原始事件流与 digest 留存于
> `backend/tools/_tmp/phase_t_runs/`（临时目录, 不提交 git）。
> RUN_DATE = 2026-09-03 07:30 ~ 08:40 (+08:00); 全部调用零 429 / 零 timeout / 零 error 事件。

# 1. Automated Tests（contract tests, 纯规则, LLM 全 mock）

```
tests/test_phase_t.py            68 PASSED（新增）
  - Taxonomy: 38 项全覆盖 / 契约字段完整 / reasoning skill 不得 RETURNS_FINAL_PROSE
  - compare_views: 结构化 scaffold / 无成品字段(comparison,image_url) / description 无"结果即成品"
    / 内部 prompt 明令"不得给出最终胜负判断" / LLM 坏输出兜底
  - dialectic: 动态字段 / constraints 逐字传入执行层 prompt / 正反合标签键丢弃+值净化
  - conceptual_map: 用户 nodes/relations 确定性构图 / LLM 只产 graph JSON 违规 Mermaid 不被采信
    / Q13 括号+内嵌双引号 label 渲染与 parse 回归 / PROCESS/ARGUMENT/分组图 / 数量对账
  - socratic_tutor: 恰好一个问题 / 多问截断 / 第二问生成输入必须含用户真实回答 / 无 rounds 参数
  - reentry: 首调免费 / 退化重入(Q11 形态)拒绝 / 用户迭代放行+上限 / 前次失败放行 / 新议题放行
    / 总量上限绝对 / 非技能工具不受影响
  - paper_review/analyze_argument: 结构化产物 / 能力匹配互相写进 description / 无"毒舌"
  - confrontation: stance/exchanges(模拟)/裁判注分离 / citations+evidence 结构化 / 呈现纪律
  - citation variants: canonical/【《书》】/【《书名·章节》】/【《书》节数】/【作者·《作品》】
    全部识别; 流式净化 verified+downgraded 双路径; 终检 actions 覆盖变体
  - runtime phrase: 全短语去除 / 跨 chunk 无泄漏 / 干净文本零改动
  - obligation UNKNOWN: 高层义务未命中→UNKNOWN / 命中→SATISFIED / 事实类保持两态
  - ownership audit: BYPASSED 捕获 / USED / 未准入 REDUNDANT / 检索类不计专用
存量套件（Phase T 后全绿）:
  test_phase_s.py + test_interpretation_engine.py + test_phase_t.py   126 PASSED
  test_evidence_contract + test_patch1 + test_patch1_1 + test_thinking_events   99 PASSED
  全量 tests/（回归前基线）380 PASSED / 3 failed → 3 处均为本 Phase 有意行为变更或存量 flaky, 处置:
    ① test_phase_s 两例: 断言旧的"关键词未命中→UNSATISFIED"语义 → 按 T13-C 新契约更新
       （analogy 补正改由 overclaim 结构信号驱动, 补正行为不变; UNKNOWN 不再产生误报补正项）
    ② test_interpretation_engine 引擎级用例: 喂 <60 字答案触发真实 DeepSeek 兜底调用,
       两次全量跑失败用例不同（LLM 非确定性）→ _run_stream 密封化（stub AG.llm_chat/llm_stream）,
       结构断言不变。非本 Phase 代码问题（首次全量跑即复现, 早于任何相关行为路径变更验证）。
```

# 2. Live Regression（11 Case, 各最终态 1 次; executed 口径 = 排除准入/重入拦截）

| Case | executed | 专用工具路由 | final_use | answer_chars | total | Gate |
|---|---|---|---|---|---|---|
| Q08 斯多葛vs伊壁鸠鲁（欲望方案差别） | 3 | **compare_views（首位）** | PARTIALLY_USED(substantive) | 1274 | 52s | **PASS** |
| Q10 辩证法·自由与规则（禁标签） | 3 | dialectic（首位） | PARTIALLY_USED | 986 | 39s | **PASS** |
| Q11 全知之镜思想实验 | 3 | thought_experiment ×**1** | PARTIALLY_USED | 1121 | 37s | **PASS** |
| Q13 康德认识论概念图 | 2 | conceptual_map（首位） | PARTIALLY_USED(图逐字采用) | 1169 | 33s | **PASS** |
| Q14 多数同意=真？（只要一个问题） | 1 | socratic_tutor | **USED** | 92 | 29s | **PASS** |
| Q15 评审短论证 | 1 | **analyze_argument**（仲裁正确） | PARTIALLY_USED | 887 | 28s | **PASS** |
| Q16 休谟因果 3000 字大纲 | 4 | essay_outline（首位） | PARTIALLY_USED | 3665 | 67s | **PASS** |
| T-A 亚里士多德vs康德论范畴 | 3 | compare_views（首位） | PARTIALLY_USED(substantive) | 1509 | 52s | **PASS** |
| T-B 宽容悖论辩证（禁标签） | 4 | dialectic（首位） | PARTIALLY_USED(grams 6/31) | 1259 | 49s | **PASS** |
| T-C 休谟→康德论证依赖图 | 3 | conceptual_map（首位） | **USED**(grams 25/25) | 1324 | 39s | **PASS** |
| T-D 苏格拉底多轮（2 用户轮） | 1+0 | socratic_tutor ×2 轮中 T1 | — | 98/131 | 25+3s | **PASS** |

## Hard Gates 逐项

```
Q08  compare_views useful=true      ✓（首位调用, 实质脚手架——3 axes/shared_problem; 4/6 次运行首位;
                                        COMPARISON 包络收紧后 executed 3~5 稳定 ≤5）
     tool domination=false          ✓（最终答案为模型对 scaffold+检索证据的二次综合, 非照搬）
     tools <=5                      ✓（最终态 executed=3）
Q10  dialectic 尊重 no-label 请求   ✓（约束经 constraints 参数进入执行层; 工具产物与 Final 均无
                                        正题/反题/合题字样; 字段为动态辩证运动）
Q11  thought_experiment calls <=2   ✓（=1; QG2 为 3 连调且第 3 次退化）
     tools <=4                      ✓（=3）
Q13  conceptual_map output used     ✓（模型逐字采用工具渲染的 mermaid——QG2 为整体架空/BYPASSED）
     MAP_TYPE correct               ✓（PROCESS_FLOW; 用户链条完整覆盖 感性/知性/范畴/统觉/经验对象）
     Mermaid parse/render PASS      ✓（validate_mermaid: 12 节点/14 边, 逐行语法+计数对账通过;
                                        括号/内嵌双引号 label 均安全——QG2 §12-3 两项语法风险根除）
Q14  socratic_tutor used            ✓（QG2 为 0 工具绕开）
     visible questions=1            ✓（92 字答案恰一个问句）
     DIRECT_ANSWER=false            ✓（不给答案, 等待回答）
Q15  analyze_argument 胜出          ✓（短论证→逻辑结构工具; 仲裁按输入形态与能力匹配, 非关键词）
     capability-fit rationale       ✓（两工具 description 互相写明边界; 系统提示 4'''' 仲裁规则;
                                        analyze_argument 返回 argument_structure 结构化产物）
Q16  essay_outline 不退化           ✓（3665 字详尽大纲: 中心论点/字数预算/反方位置策略/证据边界;
                                        USER_REQUESTED_ARTIFACT 属性保留）
```

## T-D 多轮依赖性（核心 gate: 第二问必须依赖用户真实回答, 不得预固定）

```
Turn1（用户）: 不要告诉我答案，只问一个问题：如果所有人都相信地球是平的，它就会变平吗？
Turn1（tutor）: socratic_tutor 调用; 工具返回恰好一个问题（硬截断保证）;
               回复围绕"相信改变的是地球还是相信的分量"。
Turn2（用户）: 不会，因为事实不会因为投票改变。
Turn2（tutor）: 零工具（模型直接延续苏格拉底角色——可接受形态）;
               新追问完全咬合用户回答中的"事实/投票"：「一个时代所有人心中的'事实'都显示
               地球是平的时，航海者…依据什么判断自己信错了？…一个无法与当时流行信念相区分的
               '事实'，对你而言究竟算事实，还是只是另一种更孤独的相信？」
判定: 依赖性 PASS——第二问由用户真实回答内容驱动, 非预写第二轮。
（任务书示例问句"多数同意最多能证明什么"仅为形态说明; 实际追问同等依赖回答且更贴题。）
```

## 全局 Gates

```
BYPASSED_SPECIALIZED_TOOL   = 0  (gate ≤1)  ✓  QG2 的 Q13 架空形态已被 T5 从源头消除,
                                                审计层 11 Case 零 BYPASSED
REDUNDANT_SPECIALIZED_TOOL  = 0  (gate ≤1)  ✓  重入策略拦截的技能调用按 executed 口径不计
RAW_COT_EXPOSED             = false ✓（11 份 Final 扫描无 rationale/thinking/scratchpad 标记;
                                        thought_stream 仍为 UI 通道）
RUNTIME_PHRASE_IN_FINAL     = 0  ✓（TC.RUNTIME_PHRASES 全表扫描 11 份 Final 零命中;
                                        流式 scrubber + 系统提示铁律 15 双保险）
UNVERIFIED_FORMAL_CITATION  = 0  ✓（QG2 同口径: 流式核验层为正式引用的执法层——11 份 Final 中
                                    存活的每一个【《书》·章】均经 LiveCitationSanitizer 核验,
                                    未核验者在流式阶段即被降级, 各 Case live.downgraded 0~1）
USEFUL_SPECIALIZED_TOOL_RATE = 11/11（Q08/Q10/Q11/Q13/Q14/Q15/Q16/TA/TB/TC/TD——专用工具被路由、
                                     产物实质可用、无 domination; QG2 口径的 6/9+1 失败显著改善）
EXPECTED_TOOL_NAME_MATCH_RATE 不再作为成功指标（T11; Q14/Q15 型"绕开即合规"形态消失）
多轮回归: T-D 绿（上文）; Persona: 工具注册表/人格提示词回归测试绿（test_tool_registry_unchanged 等）,
Q17/Q18 型人格 Case 不在本 Phase 重跑清单, 相关注册表与 temporal 路径零改动。
```

# 3. 迭代修复记录（Live 期间发现并当场修复, 均已回归验证）

1. **流式逗号吞噬（严重, 已修）**: RuntimePhraseScrubber 逐 chunk 处理时无条件执行"行首标点清理"，
   把每个以"，"开头的流式 chunk 的逗号剥掉（Q08 首跑正文标点丢失）。修复: 仅当 chunk 内确有
   运行时短语被移除时才做标点清理; `strip_runtime_phrases(text, cleanup=False/True)` 分层。
2. **thought_experiment KeyError 'experiment'（已修）**: 测试写入污染了运行时 agent_memory.json
   （default 槽被旧格式迁移启发式二次嵌套, 槽缺 experiment 键）。修复: ①修复数据文件;
   ②`_mem_slot` 逐键 setdefault 兜底（含新增 socratic 键）; ③工具侧 `slot.get("experiment")`;
   ④test_phase_t 增加 MEM_FILE 隔离 fixture（防再污染）。
3. **compare_views scaffold JSON 截断（已修）**: max_tokens 1400 下长 JSON 被截断 → 解析失败 →
   空脚手架（Q08 第 2 跑"0 条比较轴线"）。修复: max_tokens 2200 + 字段紧凑化 + `extract_json`
   截断括号配平修复。
4. **比较类路由不确定（已修）**: 3/6 跑 compare_views 未被首选或完全手工。修复: ①规则 4 明确
   "首选直接调用 compare_views, 不要先手工多路检索"; ②plan.problem_type==COMPARISON 时注入
   确定性路由提示（与 MAP_HINTS 同机制）; ③COMPARISON 检索配额收紧（QG2 报告背书的
   "比较类任务检索上限"）: SEARCH_EXEC_LIMIT 5→3、TOTAL_RETRIEVAL_LIMIT 7→3——compare_views
   计 1 次, 手工补检索 ≤2。修复后 compare_views 首位路由稳定。
5. **infer_map_type 单字标记误判（已修）**: "先验演绎"的"先"触发 PROCESS_FLOW（T-C 目标
   ARGUMENT_GRAPH）。修复: 标记全部 ≥2 字 + 计分式取最大。重跑 T-C → ARGUMENT_GRAPH ✓。
6. **compare_views citations 缺 snippet（已修）**: T9 证据入池后 book+chapter 可过流式核验,
   但无片段重叠进不了 used_evidence（终检记 1 条）。修复: citations 携带 snippet/author。
7. **Q14 工具问题之外追加自设问题（已修）**: 规则 14 增加"只呈现 next_question, 不得追加
   自己的新问题"; 重跑后恰 1 个可见问句且 socratic_turn=USED。

# 4. Known Issues（不阻塞 Phase T 验收, 记录供下一阶段）

1. **终检断言层 vs 流式执法层的"转述式引用"差位**: compare_views 场景答案大量转述双方观点时,
   存活正式引用通过流式核验（书+章确在检索池）但与 snippet 无字面重叠 → `citation_sanitize
   .unverified_before` 记 1~3 条（Patch1.1 设计为 log-only, 不改正文）。属"引用标注+转述内容"
   灰区而非编造引用; 建议下一阶段: 对"引用标注紧邻引号引句"的场景做 quote-bound 流式核验
   （触及 Evidence Contract 主体, 本 Phase 冻结未动）。
2. **get_school 对"斯多葛主义/伊壁鸠鲁主义"报错**: schools 数据命名（斯多葛学派等）与模型传入
   名不精确匹配; 预存在数据匹配问题（本 Phase 未触碰 get_school）, 观测到 2 次/3 跑。
3. **socratic 多轮 Turn2 零工具**: 模型有时直接以苏格拉底口吻延续而不二次调用工具（合同仍满足:
   只问不答、依赖真实回答）。T11"允许不调用"原则下可接受; 若要求强一致可后续加状态提示注入。
4. **所有权审计的转述盲区**: PARTIALLY_USED(no_literal_overlap_but_substantive) 与"实质被采纳"
   靠结构启发区分, 极端转述下与 BYPASSED 的边界依赖载荷实质阈值（≥60 CJK 字）。语义级判定
   需引入 LLM 审计, 本 Phase 保持纯规则。
5. **Q15 plan 分类漂移**: "评审这个小论证"被判 HISTORICAL_GENEALOGY/COMPARISON（分类偏差不影响
   结果——路由按 description 能力匹配正确选中 analyze_argument）; reasoning_plan 分类改进不在
   本 Phase 范围。

# 5. RUN_SUMMARY

```
LIVE_INVOCATIONS        = 11 Case 最终态（另含迭代期 Q08×5 / Q11×1 / Q14×1 / TC×1 / TD×1 重跑）
RUNTIME_ERRORS          = 0（零 429 / 零 timeout / 零 error 事件 / 零 answer 异常）
AUTOMATED_TESTS         = 68（新增 Phase T）+ 126 + 99 存量组合 全部 PASSED
HARD_GATES              = 7/7 Case PASS + T-A/T-B/T-C/T-D PASS
GLOBAL_GATES            = 5/5 PASS（BYPASSED=0, REDUNDANT=0, RAW_COT=false, RUNTIME_PHRASE=0,
                           UNVERIFIED_FORMAL_CITATION=0[执法层口径; 断言层差位见 Known Issues 1]）
CODE_MODIFIED           = true（Phase T 范围内; 冻结清单零触碰——见架构报告 §9）
```
