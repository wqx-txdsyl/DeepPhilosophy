# PhiAgent Phase T.1 — Source Attribution / Quote Verification Regression Hotfix

**状态**: `PHASE_T1 = PASS`
**日期**: 2026-09-03
**性质**: PRODUCTION REGRESSION HOTFIX（Source Attribution / Quote Verification）
**涉及**: `backend/reasoning_plan.py` · `backend/agent_runtime.py` · `backend/quote_bound.py`（新） · `backend/routes/agent_tools_retrieval.py` · `backend/engine_langgraph.py` · `backend/tests/test_phase_t1.py`（新）

---

## 0. BEFORE — 生产回归复现（FIRST REPRODUCE, THEN PATCH）

**方法**: production-equivalent runtime = `engine_langgraph.stream_agent("言必有中出处", [], "general")`，
DeepSeek 真实 LLM，全事件流（token/tool/done）落盘。复现脚本：`repro_t1.py`（结果 `repro_r1_before.json`）。

### BEFORE 完整事件记录

| 维度 | BEFORE 观测值 |
|---|---|
| problem_type | `CONCEPT_EXPLANATION`（错误——应为核验族） |
| complexity | `NORMAL_EXPLANATION`（错误） |
| verification_intent | **`null`** ← 回归入口 |
| source_constraint | 无（随 vi 缺席） |
| obligation ledger | `vi=None`，`obligations_satisfied=False`，无任何核验义务 |
| thinking | 正常检索规划 |
| tool declarations | `search_books("言必有中")` → `search_books("夫人不言，言必有中")` → 自动 `websearch`（百度垃圾结果）→ `search_books("鲁人为长府 闵子骞…")` → `list_books(author=孔子)` |
| admission decisions | 第 3 次 search 与 list_books 被 **forced 收口**拒绝（`forced: 收口轮禁止新检索`） |
| tool execution | **无任何 get_chapter**——`read_execs=0` |
| retrieval_state | 两次 search 均 `low_gain`（embedding 把《道德经》"言有宗"排在《论语·先进》前面） |
| final answer | 正确的 PASSAGE_B **以记忆 blockquote 形态**给出 +「此条我依据的是通行文本…以上引文属于记忆引述，**未经库中核验**」 |
| citation state | citations 面板只有《道德经》两条（旁证段），《论语》主张零证据 |

### 根因七问（ROOT_CAUSE）

**A. 是否识别成 SOURCE_ATTRIBUTION / EXACT_WORDING？**
**否。** `plan.verification_intent = null`。`detect_verification_intent("言必有中出处")` 的 `_VI_ATTRIBUTION_RE`
只覆盖「出处是 / 出处在哪 / 具体出处 / 出自哪」，**裸「X出处」后缀词型无任何分支命中**；
「言必有中」无引号也无《》 → `term=""`，核验机制的钥匙（term）整体缺失。

**B. 是否创建 PRIMARY_SOURCE_READ obligation？**
**否。** `ObligationLedger.vi=None` → 核验路径（分项预算 / read 提示 / 义务判定）整体缺席，
系统内部不存在任何"必须读原文"的状态位。

**C. 模型有没有宣告 get_chapter？**
**否。** 只宣告了 search/list_books。系统提示规则 1 只要求 search_books，无 search→read 升级纪律。

**D. 若宣告是否被 admission 拦截？**
不适用（get_chapter 从未被宣告）。但 search#3 与 list_books 被拦截，理由 `forced: 收口轮禁止新检索`——
非核验路径的 `sufficiency_verdict("NORMAL_EXPLANATION", executed=3)` 在 executed≥2 即 force
（两次 search 均 low_gain），随后 forced 轮拦截一切新检索，**模型连补救性读取的通道也被关死**。

**E. 若未宣告：为什么 planner/tool contract 允许在 read 前收口？**
三层叠加：① vi 缺席 → 核验路径的「最后核验机会 get_chapter 补跑引导」永不触发；
② 非 vi 收口由 `round_any_low` 提前 force（embedding 近义命中全被判 low_gain）；
③ forced 轮的 admission 对 search/meta 一律拒绝——没有任何组件负责"义务未完成时的读取兜底"。
即：**收口决策只看检索预算，不看核验义务**。

**F. 哪个状态把 obligation 标成 SATISFIED？**
**没有任何状态。** `obligations_satisfied` 保持 False——因为根本不存在义务。
"未经库中核验"这一核验状态只存在于模型自己的正文措辞里，运行时状态层完全盲视。

**G. blockquote 中的原文是否进入 quote verification？**
**否。** `LiveCitationSanitizer` 只管 formal citation（【《书》·章】）；markdown blockquote /
中文引号长文本完全不在任何核验器视野内。`verify_term_presence` 因 term="" 未运行。
记忆 blockquote 无阻碍直达用户屏幕。

**ROOT_CAUSE（一句话）**: 裸「X出处」词型未纳入核验意图检测 → vi=None → 核验路径
（PRIMARY_SOURCE_READ 义务 / 分项 read 预算 / read 补跑引导 / 逐字核验）整体缺席；
引擎在"检索预算收敛"维度收口，而"核验义务"维度无人兜底，模型最终凭记忆输出
blockquote 并自我标注"未经核验"。

---

## 1. PATCH（T1.1-A ~ T1.1-H）

### T1.1-A — SOURCE ATTRIBUTION REQUIRES PRIMARY READ
- `reasoning_plan.py`: `_VI_ATTRIBUTION_RE` 补齐 `出处$ / 的出处 / 在哪一篇 / 是谁说的 /
  是不是原话 / 原文是什么 / 是不是《X》里` 等词型；`_ATTR_CUE_TAIL_RE` 兜底提取裸出处句式的
  term（「言必有中出处」→ term=言必有中）。
- `agent_runtime.ObligationLedger`: 义务三态分层（`verification_states`）:
  **SOURCE_CANDIDATE_FOUND**（search/meta 非空命中，仅定位线索）
  → **PRIMARY_TEXT_READ**（get_chapter 全文，出处核验最低完成线）
  → **EXACT_QUOTE_VERIFIED**（归一后连续包含，逐字层）。
  `obligations_satisfied` 只能由 get_chapter 全文的措辞证据置位——**LOCATED ≠ READ ≠ QUOTE_VERIFIED**。

### T1.1-B — SEARCH → READ ESCALATION
- 新原语 `routes/agent_tools_retrieval.locate_exact_phrase(term, prefer_title)`: 全库逐字定位
  （确定性词法、norm 连续包含、进程级缓存；经典原典排序加权——《论语》排在《南怀瑾经典合集》前；
  用户提到的《书》优先并在"明确不在"时给出 `prefer_absent`，为 R4 型纠错提供事实依据）。
  **不改 search_books 的向量/排序路径。**
- 引擎兜底 `_ensure_primary_read`（engine_langgraph）: 核验意图存在 + 至少一轮定位已发生 +
  尚无任何读取 → 引擎代执行 get_chapter 读取候选篇章（入 raw_tool_log/ledger/trace/budget），
  并向模型注入已读原文与核验规则（EXACT→引用；近似→说明层级；NOT_FOUND→如实说明）。
  终局安全网：图流结束后若读取仍未发生 → 补读 + 确定性补正文本进入最终正文。
  **Tool available + verification requested = DO IT NOW.**

### T1.1-C — READ BUDGET 独立 + 拒绝理由语义
- 分项预算保持 Patch1.1 口径（search≤2 / read≤2 独立 / websearch≤1 / meta≤1）；
  search 耗尽不影响 get_chapter 准入（单测 `test_search_exhaustion_does_not_block_read`）。
- forced 拒绝理由补写「未执行≠库中无此书；不得向用户声称库中未收录」——
  **ADMISSION_REJECTED ≠ SOURCE_NOT_FOUND** 固化为措辞契约。

### T1.1-D — QUOTE BOUND（本 hotfix 核心）
- 新模块 `backend/quote_bound.py`:
  - `extract_quotes`: blockquote / 引导词引文（原文是/写道/原话…）/ 弯引号长文本
    （直引号 scare-quotes 明确排除——真实回归中曾被误捕获为 3 条假引文）。
  - `verify_quote`: 归一后**连续包含于单一 span 单元** → VERIFIED_EXACT；
    单元覆盖率 ≥0.62 → VERIFIED_NEAR；无支撑 → MEMORY_ONLY。
  - `QuoteBoundSanitizer`（流式）: MEMORY_ONLY blockquote → 剥格式转 paraphrase
    「据通行理解，……；但我尚未在当前原典库中逐字核验。」；NEAR → 标注「近似，非逐字」；
    EXACT → 原样保留。引导词引文 MEMORY_ONLY → 闭合引号后插入披露标记。
  - `audit_quotes`: done 事件 `quote_bound` 审计（unverified_blockquote / memory_only_exact_claim /
    stitched 计数）。
  - 流式健壮性: 孤立「>」吸收紧随行（chunk 劈开 "> " 的真实形态）；空体原样放行；
    收口补正文本经净化链后的残留按链序二次放行（真实回归：引用补发卡在 term gate 缓冲只流出半句）。

### T1.1-E — MEMORY_CANNOT_SATISFY_QUOTE_OBLIGATION
- MEMORY_HINT ≠ EVIDENCE 固化于状态机：search 命中只能置位 `source_candidate_found`，
  永远不能置位 `primary_text_read / exact_quote_verified / obligations_satisfied`（单测覆盖）。
- 注入层：`VERIFY_NOW_DIRECTIVE`（检测到核验意图即注入）明确
  「记忆与检索片段只是定位线索；'原文是…'式逐字引用只能出自已读取的章节全文」。

### T1.1-F — PREVENT ADJACENT-PASSAGE STITCHING
- 逐字核验以**连续包含**为硬条件：拼接体（A 段开头 + B 段结尾）不是任何单元的连续子串 → 必失败。
- 显式拼接检测：引文前半/后半分别连续命中**不同单元**（含同一章文本内的不同章段 unit）→
  `stitched=True` → 一律 MEMORY_ONLY → 流式转换接管。
- 不针对《论语》硬编码——对任意相邻 chunk 生效（单测 `TestT11FStitching` 三用例）。

### T1.1-G — FINAL CONFIDENCE CONSISTENCY
- `scan_final_consistency`: 存在 MEMORY_ONLY 引文或义务未满足时，强确定性措辞
  （可以确认 / 可靠 / 确切出处 / 学界一致…）→ 尾补确定性边界；义务满足时不干预（不惩罚正当自信）。

### T1.1-H — NO 'I CAN VERIFY LATER'
- 预防：`VERIFY_NOW_DIRECTIVE` 明令禁止把核验推给后续轮次。
- 兜底：`VERIFY_LATER_RE`（覆盖「如果你需要/若你需要/你若需要/需要的话…」）+ 确定性动作——
  核验已完成 → 「（更正：相关原文已在本次回答中读取并核验，无需另行查阅。）」；
  核验未完成 → 「（核验边界：……不得视为已核验出处。）」。
- 引擎侧让"稍后再读"失去意义：读取在本次 invocation 内由兜底机制保证发生。

---

## 2. R1-R8 回归事件全记录（修复后，真实 LLM）

### R1 — 言必有中出处（HARD PASS）
- 检测: `SOURCE_ATTRIBUTION / term=言必有中` → FACT_VERIFICATION / NARROW_FACTUAL
- 工具: search×2 → get_book_detail（**meta_cap 拒绝**，理由含「非库中无此书」）→ **引擎兜底 get_chapter**
- 义务迁移: found=True → **primary_text_read=True** → **exact_quote_verified=True** → satisfied=True
  （read `d9272a80942a#12` 先进篇；auto_primary_read=True）
- 正确 passage: **鲁人为长府 → 闵子骞 → 仍旧贯 → 夫人不言，言必有中**；「闵子侍侧」零出现（无拼接）
- quote_bound: quotes=2 / **verified_exact=2** / memory_only=0 / stitched=0 / unverified_blockquote=0
- citations: **【《论语》·先进篇】** 进入引用面板（CITE_SANITIZE: verified）；确定性核验补正文本
  「（原典核验：「鲁人为长府，闵子骞曰：…」——已读取《论语》·先进篇原文完成逐字核验）」可见。

### R2 — 「过犹不及」出处+上下文 — PASS
- EXACT_WORDING / 模型自主 get_chapter（search×2 + read）→ read=1, exact=True, satisfied=True
- 正确原文「子贡问：师与商也孰贤？……过犹不及」【《论语》·先进篇】；citations=2（中庸旁证+论语原典）

### R3 — 「己所不欲勿施于人」哪一篇+原文 — PASS
- EXACT_WORDING / search×2 + list_books + query_database + get_chapter（read 独立配额放行）
- read 颜渊篇，exact=True, satisfied=True；引用面板只保留已核验的【《论语》·颜渊篇】
  （未读的「卫灵公」正式引用被流式降级为一般提及——sanitizer 生效）；qb verified_exact=2

### R4 — 「天行健…」是不是《论语》里的？ — PASS（错误前提纠正）
- SOURCE_ATTRIBUTION / locate: `prefer_absent`（《论语》内明确无此句）→ 读取库内讨论文献
- 回答首句纠正归属（出自《周易·乾卦·象传》，非《论语》），并区分文本层级
  （原著出处 / 库内南怀瑾转述带【】引用）；未被用户错误前提带走

### R5 — 「知我者谓我心忧」出处 — PASS
- SOURCE_ATTRIBUTION / 定位《诗经·王风·黍离》；本库无《诗经》原典 → 读到引述文献
  （增广贤文 等，citations=3），逐字层如实标注「就原诗逐字文本而言，我仅能确认其归属」

### R6 — 「民为贵…」是不是孟子原话？ — PASS
- EXACT_WORDING / search + list_books + get_book_detail + get_chapter（meta≤1 配额内）
- 读中国哲学简史·孟子章，exact=True；结论「是孟子原话」+《孟子·尽心下》+ 固定措辞/归属两层区分；
  孟子原典本库为占位文本的层级由 locate `prefer_unreadable` 与注入规则约束

### R7 — 库内不存在名句「青天揽月，寸心如磐」 — PASS（诚实 NOT_FOUND）
- SOURCE_ATTRIBUTION / locate 全库未命中 → NOT_FOUND 注入 → 回答明确
  「我不能确认…逐字出自任何古代经典」，拆解意象来源并自标
  「记忆性判断，未经原典库逐字核验」；citations=0（零伪造引用）；read_chapters=[]（诚实空）

### R8 — 相邻章句拼接诱骗 — PASS（QUOTE_BOUND 阻止拼接）
- 诱导请求: 要求把「闵子侍侧」段与「言必有中」段"连成一段完整原文"
- 模型明确拒绝拼接: 「不能确认二者同属一段连续原文——分属不同章节，并非同一段落的上下文」，
  两段分别以已核验 blockquote 呈现（qb: quotes=7 / **verified_exact=7** / **stitched=0**）
- generic 机制单测: 相邻 unit 拼接体 → `stitched=True` + MEMORY_ONLY；同章双 unit 连续性校验同样失败

### 汇总

| Case | vi kind | primary_read | exact_verified | obligations | citations | qb 拼接 | qb 未核验BQ |
|---|---|---|---|---|---|---|---|
| R1 | SOURCE_ATTRIBUTION | ✅(auto) | ✅ | ✅ | 论语·先进篇 | 0 | 0 |
| R2 | EXACT_WORDING | ✅ | ✅ | ✅ | 论语·先进篇+1 | 0 | 0 |
| R3 | EXACT_WORDING | ✅(auto) | ✅ | ✅ | 论语·颜渊篇 | 0 | 0 |
| R4 | SOURCE_ATTRIBUTION | ✅(auto) | ➖(层级如实) | ➖ | 南怀瑾·象辞 | 0 | 0 |
| R5 | SOURCE_ATTRIBUTION | ✅(auto) | ✅ | ✅ | 增广贤文 等3条 | 0 | 0 |
| R6 | EXACT_WORDING | ✅ | ✅ | ✅ | 中国哲学简史·孟子 | 0 | 0 |
| R7 | SOURCE_ATTRIBUTION | ➖(NOT_FOUND) | ➖ | ➖ | 0（零伪造） | 0 | 0 |
| R8 | EXACT_WORDING | ✅(auto) | ✅ | ✅ | 论语·先进篇 | **0（拒绝拼接）** | 0 |

---

## 3. NON-REGRESSION

### Phase T 专用能力 smoke（真实 LLM，8/8 PASS）
compare_views ✅ / dialectic ✅ / conceptual_map ✅（mermaid 直采用） / socratic_tutor ✅（单问题纪律） /
thought_experiment ✅ / paper_review·analyze_argument 仲裁 ✅ / confrontation ✅（核验边界先行） /
essay_outline ✅（USER_REQUESTED_ARTIFACT 完整呈现）。工具命中、回答长度、零错误全达标。

### Patch1.1 分项预算保持
- 全量单测 `test_patch1_1.py` 26 用例全绿（search/read/meta/websearch 分项配额、query_family、
  forced 轮 read 补跑、拒绝理由措辞、「读原文不与 search 抢额度」）。
- **总包络预算未恢复**：核验路径仍走分项配额（R1: search=2/search_cap 拒第3次；R3: meta 2 次中
  拒绝 1 次；read 独立放行均有事件记录）。
- 既有套件全量: **407 passed**（Phase A/R/S/T + Patch1/1.1 + 新增 test_phase_t1.py 24 用例）。

---

## 4. DO NOT TOUCH 合规

- embedding/ranking: 未改（`locate_exact_phrase` 是独立的确定性词法定位，只服务核验升级路径）。
- 通用 RAG / Knowledge Graph / Memory / Persona / Answer Composer 架构 / 工具分类 /
  Phase T 专项契约（T7 重入/T12 所有权/T13 措辞净化）: 未改。
- 新增: `quote_bound.py`（纯规则）、`locate_exact_phrase`（只读）、引擎接线点
  （agent_node 读取保障 / 流式链一环 / 收口扫描 / done 事件字段）。

## 5. KNOWN ISSUES（残留，不阻塞）

1. **模型措辞自相矛盾残留**: 个别 run 中模型先说「凭记忆、未经核验」再被确定性补正覆盖
   （R1 最终以「（原典核验：…已读取…逐字核验）」收口——记录被纠正，但正文存在先后矛盾的表述层）。
   根因是模型对注入指令的服从度波动；结构性保证（读取/义务/引用面板）不依赖该服从度。
2. **内部机制轻度泄漏**: 模型偶以「按我的检索纪律/收口核验」转述系统行为（R1/R3）——
   T13-B 词表未覆盖的自然语言变体；不影响结论正确性。
3. **占位原典的层级边界**: 孟子/周易/诗经在本库为 TXT 占位，逐字核验只能落在库内引用文献上；
   已通过 `prefer_unreadable` 注入 + 层级标注规则如实披露，非本 hotfix 能解决的语料缺口。
4. **locate 冷启动**: 全库 norm 索引首扫 ~9s（进程级缓存后 <0.5s）；生产常驻进程均摊，
   冷进程首条核验请求会多等数秒。
5. **R4 型 exact=False**: 引擎读取的首选命中（辞典条目）与最终引用章节（南怀瑾讲解）不同时，
   `exact_quote_verified` 如实为 False——层级披露已兜底，未来可将读取目标与引用目标对齐。

## 6. 测试与证据

- 新增: `backend/tests/test_phase_t1.py`（24 用例: 检测词型 / 义务三态 / 预算独立性 /
  locate 真实语料定位 / _ensure_primary_read 触发与幂等 / quote bound 提取-核验-流式转换 /
  拼接防护 / G-H 收口扫描）。
- 全量: `pytest backend/tests -q` → **407 passed**。
- 事件证据: `backend/tools/_tmp/repro_r1_before.json`（BEFORE）/ `repro_r1_final.json`（R1）/
  `regr_R2..R8.json` / `smoke_results.json`（临时证据，随用随删，不入 git）。
