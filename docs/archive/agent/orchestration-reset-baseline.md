# PHIAGENT Orchestration Reset — O0 Final Baseline Report

> 性质: PRESERVATION ONLY ｜ O1 NOT STARTED ｜ 最终 O0 PASS 由 Reviewer 签发

## 1. Identity

| 项 | 值 |
| --- | --- |
| ORIGINAL_HEAD | `ec09e04da914d55ba3904fc5812785b2f81729f6`（master） |
| Preservation branch | `archive/phiagent-pre-orchestration-reset` |
| PRESERVATION_SHA | 见提交（本报告属于该提交本身） |
| Tag | `phiagent-pre-orchestration-reset`（annotated） |
| Refactor branch | `refactor/phiagent-main-agent-orchestration`（自 PRESERVATION_SHA 创建） |
| 目标架构 | **Main-Agent-Owned Orchestration**（ARCHITECTURE_DECISION = OPTION_B） |

## 2. Reviewer 前置裁决（继承）

- AUDIT_01 = PASS
- ARCHITECTURE_DECISION = OPTION_B → TARGET_ARCHITECTURE = Main-Agent-Owned Orchestration
- O0_R = PASS；O0_R_RECHECK = PASS
- quote_bound 对账: **LOC = 432**，SHA256 = `3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13`
  （pre-flight 实测一致）。**AUDIT-01 旧 aggregate digest 已废弃；不得要求恢复 429 行 quote_bound.py；不得再跑 O0-R。**
- O0-R candidate manifest（`docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md`）保留为 forensic artifact，不是最终 baseline manifest。

## 3. Drift 事件记录（SNAPSHOT 对账）

方法: 对全部基线候选文件（tracked modified + untracked，gitignore 生效）做 SHA256 snapshot（A/B 双采样，工作目录外保存）。

| 事件 | 时刻 | 内容 | 处置 |
| --- | --- | --- | --- |
| 1 | 18:11:18 | `docs/BOOK_SHELL_INVENTORY.md` 新出现（本任务外部进程写入） | **用户裁决: 纳入 baseline** |
| 2 | 18:15:48 / 18:22:36 | `docs/BOOK_SHELL_INVENTORY.md` 内容更新（59adf070…→4b8baf3a…）；新增 `docs/分章标准规范.md`（58a6964e…） | 同类并发书库工作流产物，按既有裁决纳入 |
| — | 18:31:35 | 稳定性探测: 写入方静默 >9 分钟，60 秒复测 SNAPSHOT_D == SNAPSHOT_FINAL，字节级一致 | 继续执行 |

两事件均为同一外部书库审计工作流的文档产物，非本任务写入；基线候选集由 78 → 80 文件滚动。任务全程 production code 零改动（PRODUCTION_CODE_CHANGED=false）。

## 4. EXACT_STAGING_MANIFEST

最终 preservation commit 共 **82 文件** = 80 个项目文件（下表）+ 2 个本报告流程产物（`docs/PHIAGENT_ORCHESTRATION_RESET_BASELINE.md`、`docs/PHIAGENT_BASELINE_HASH_MANIFEST_V2.md`）。

明确排除（未 stage）: `.env` 及一切 secret/token/key、`__pycache__`、`*.pyc`、`.pytest_cache`、runtime json/jsonl、admin_stats、embedding/runtime 输出、`backend/tools/_tmp`、logs、editor backup、ZCode artifact、repo 外 forensic copy。

### backend 源码（tracked modified） — 17 文件

- `backend/agent_runtime.py`
- `backend/answer_composer.py`
- `backend/engine_langgraph.py`
- `backend/epistemic_guard.py`
- `backend/evidence_contract.py`
- `backend/guard.py`
- `backend/interpretation_engine.py`
- `backend/main.py`
- `backend/philo_retrieval.py`
- `backend/routes/agent.py`
- `backend/routes/agent_core.py`
- `backend/routes/agent_tools_eval.py`
- `backend/routes/agent_tools_memory.py`
- `backend/routes/agent_tools_retrieval.py`
- `backend/routes/auth_routes.py`
- `backend/routes/upload.py`
- `backend/semantic_obligations.py`

### backend 新模块（untracked） — 3 文件

- `backend/quote_bound.py`
- `backend/reasoning_plan.py`
- `backend/tool_contracts.py`

### backend tests（tracked modified） — 4 文件

- `backend/tests/test_answer_composer.py`
- `backend/tests/test_interpretation_engine.py`
- `backend/tests/test_phase_s.py`
- `backend/tests/test_security.py`

### backend tests 新增（Patch1 / Patch1.1 / Phase T / Phase T.1） — 4 文件

- `backend/tests/test_patch1.py`
- `backend/tests/test_patch1_1.py`
- `backend/tests/test_phase_t.py`
- `backend/tests/test_phase_t1.py`

### 前端 app/src（tracked modified） — 12 文件

- `app/src/App.css`
- `app/src/components/ChapterReader.jsx`
- `app/src/components/school/HeroSection.jsx`
- `app/src/pages/AuthorDetailPage.jsx`
- `app/src/pages/EasternPhilosophiesPage.jsx`
- `app/src/pages/GenealogyPage.jsx`
- `app/src/pages/HomePage.css`
- `app/src/pages/ProfilePage.jsx`
- `app/src/pages/ReaderPage.jsx`
- `app/src/pages/SchoolDetailPage.jsx`
- `app/src/pages/WesternPhilosophiesPage.jsx`
- `app/src/pages/WorldPhilosophiesPage.jsx`

### schools/data（tracked modified） — 7 文件

- `app/public/schools/data/school_伊壁鸠鲁学派.json`
- `app/public/schools/data/school_分析哲学.json`
- `app/public/schools/data/school_前苏格拉底哲学.json`
- `app/public/schools/data/school_怀疑论.json`
- `app/public/schools/data/school_斯多葛学派.json`
- `app/public/schools/data/school_新柏拉图主义.json`
- `app/public/schools/data/school_犬儒学派.json`

### docs 文档（untracked） — 19 文件

- `docs/BOOK_SHELL_INVENTORY.md`
- `docs/PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md`
- `docs/PHIAGENT_BACKEND_DIAGNOSTIC.md`
- `docs/PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md`
- `docs/PHIAGENT_BACKEND_PATCH1_1_REGRESSION.md`
- `docs/PHIAGENT_BACKEND_PATCH1_FINAL_GATE.md`
- `docs/PHIAGENT_BACKEND_PATCH1_REGRESSION.md`
- `docs/PHIAGENT_BACKEND_QUALITY_GATE2.md`
- `docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md`
- `docs/PHIAGENT_O0_BASELINE_RECONCILIATION.md`
- `docs/PHIAGENT_PHASE_T1_SOURCE_VERIFICATION_REGRESSION.md`
- `docs/PHIAGENT_PHASE_T_REGRESSION.md`
- `docs/PHIAGENT_PHASE_T_TOOL_ARCHITECTURE.md`
- `docs/PHIAGENT_TOOL_ARCHITECTURE.md`
- `docs/PhiAgent_Conversation_Workspace_Design_Spec_v1.0.md`
- `docs/PhiAgent_Conversation_Workspace_Refactor.md`
- `docs/PhiAgent_agent_deploy.md`
- `docs/分章标准规范.md`
- `docs/设计说明-20260818-UI优化.md`

### .agents/skills（untracked） — 12 文件

- `.agents/skills/add-author/SKILL.md`
- `.agents/skills/add-school/SKILL.md`
- `.agents/skills/add-skill/SKILL.md`
- `.agents/skills/add-subschool/SKILL.md`
- `.agents/skills/agnes-image/SKILL.md`
- `.agents/skills/fetch-philosopher-img/SKILL.md`
- `.agents/skills/fix-counts/SKILL.md`
- `.agents/skills/local-check/SKILL.md`
- `.agents/skills/post-push/SKILL.md`
- `.agents/skills/relationship-constellation/SKILL.md`
- `.agents/skills/school-bg-gen/SKILL.md`
- `.agents/skills/timeline-designer/SKILL.md`

### 根目录 — 1 文件

- `AGENTS.md`

### scripts — 1 文件

- `scripts/build_phiagent_static.py`

## 5. BASELINE_MANIFEST_SHA256

- **BASELINE_MANIFEST_SHA256 = `e5605c4d8e5c8c6377cb75fdef28b1d4d0de701048a44183d4b0db54621070b1`**

Canonical 口径:

1. 输入 = 上述 80 个项目文件的 **staged blob**（`git cat-file blob :path`，即实际进入 commit 的对象；非工作树假设值）
2. repo-relative POSIX path，UTF-8 lexical sort
3. 每行 `<sha256><两个空格><relative_path>
`，对全部 canonical bytes 再取 SHA256

自指排除（文档化偏差）: 聚合输入不含 `docs/PHIAGENT_BASELINE_HASH_MANIFEST_V2.md`（任务书规定 V2 不进入自身 hash input）与 `docs/PHIAGENT_ORCHESTRATION_RESET_BASELINE.md`（本报告内嵌该聚合值，自嵌为不动点，不可计算）。两者的完整性由 V2 表内 per-file sha256 + git commit 本身约束。逐文件 size/sha256 见 V2 manifest。

## 6. Automated Tests

`pytest backend/tests -q`（.venv, Python 3.11.0, pytest 9.0.3）:

- **passed = 407**
- **failed = 0**（门槛 failed=0 满足）
- skipped = 0
- duration = 324.23s（5m24s）

## 7. Known-Good Smoke（production-equivalent）

运行方式与 Phase T1 回归一致: 直接驱动 `engine_langgraph.stream_agent(...)`（真实 DeepSeek 流式 + 真实库内检索，无 mock）。

### S1 — Source Verification → **PASS**

- 问题: 「言必有中出处」（general agent，47.4s）
- 实际读取《论语·先进》: `get_chapter` 执行，evidence `qb_read_2`，book_id `d9272a80942a`，chapter_idx 12（先进篇）
- 正确 passage: 鲁人为长府 → 闵子骞 → 仍旧贯/何必改作 → 夫人不言，言必有中；「闵子侍侧」零出现
- verified quote: quote_bound audit `{quotes:2, verified_exact:2, verified_near:0, memory_only:0, stitched:0, unverified_blockquote:0}`；verification `{term:言必有中, state:VERIFIED_EXACT, computed:true}`
- 正确 citation: 【《论语》·先进篇】（CITE_SANITIZE: verified）
- **stitching = 0**

### S2 — Deep Philosophy（QG2 Q12 复刻）→ **PASS**

- 问题: 「如果所有价值都是人创造的……尼采的价值创造最终会导致虚无主义。请拆解这个论证，然后告诉我最薄弱的一步在哪里。」（56.2s）
- 正常主动研究: `analyze_argument`（首）+ `search_books` + `concept_trace`
- depth 保持: 完整论证重构（结论/P1 显式/P2 隐含/桥接 + 三块未论证地基 a/b/c）→ 逐点检验 → 最薄弱环节；对库内未能定位的「精确原话」如实声明，未伪造逐字引文（quote_bound 全零异常）
- 无 runtime error、无 error 事件

### S3 — Temporal Persona（QG2 Q18 复刻）→ **PASS**

- 问题: 「如果晚年的你回头批评《悲剧的诞生》……」（nietzsche agent，71.3s）
- temporal evidence 正常: `temporal.detected=true`，words=[早年的,晚年的,晚年]，`philosopher_period` 首工具调用（period_tool_called=true），corpus_periods 载入；后随 philosopher_corpus / philosopher_quote / websearch / search_books / get_book_detail
- persona isolation 正常: 全程尼采第一人称（1886《自我批判的尝试》自锚定，「我自己的捶打，与旁人的指摘，不是一回事」），自我批判（艺术形而上学拄叔本华/康德拐杖等）与后世学者批评（维拉莫维茨）明确分开，无 general agent 视角泄漏

### S4 — Zero-tool Explanation（QG2 Q05 复刻）→ **PASS**

- 问题: 「不要查资料。给我解释一下：『我有理由相信P』和『P是真的』为什么不是同一件事……」（16.9s）
- **tools = 0**（tool_calls=[]，事件级零工具调用）
- 回答正常: 822 字符，直白两层区分（世界层面 vs 认知者层面），无术语堆砌

### S5 — Streaming Blockquote Witness → **PASS**

直接驱动当前 `QuoteBoundSanitizer`（432 行版）: chunk A = `> 「`，chunk B = `鲁人为长府，闵子骞曰：……
`，证据池 = get_chapter《论语·先进篇》原文。

- T1 chunk A 完全缓冲，无提前 emit（无 `> 「
` 腰斩特征）✓
- T2/T4 blockquote 不被腰斩: 渲染为单一完整引用行 `> 「鲁人为长府，闵子骞曰：……
` ✓
- T3 正文不掉出 blockquote（含「鲁人为长府」的行全部以 `>` 开头）✓
- T5 对已读原典 VERIFIED_EXACT（stats: verified_exact=1, converted=0）✓
- T6 **stitched = 0** ✓
- **432 行修复实际生效。** 按任务书，本轮不新增正式 regression test；O1 第一项再将 S5 固化为 behavior test。

## 8. Behavior Locks（preservation 提交即锁定）

1. citation integrity（CITE_SANITIZE 只放行 verified）
2. exact quote verification（VERIFIED_EXACT 逐字连续包含，单 span 单单元）
3. quote stitching prevention（T1.1-F 跨段拼接检测，stitched → MEMORY_ONLY）
4. streaming blockquote integrity（chunk 边界缓冲，引用块不腰斩、正文不掉出）
5. General / Nietzsche isolation（人格包与工具集按注册表切换）
6. temporal persona（时期检出 → philosopher_period 路由 → 语料时期档案）
7. conversation continuity（conversation_id/message_id 观测上下文）
8. Phase T specialized tool contracts（38 项 taxonomy，契约测试在库）
9. Socratic one-question contract（恰好一个问题）
10. SSE protocol（事件协议与自研版一致）

## 9. 状态声明

- **O1 NOT STARTED** — 本任务不重构、不修 bug、不改 production behavior、不删除旧 architecture
- PRODUCTION_CODE_CHANGED = **false**（本提交仅新增 2 个 docs 流程文件，其余为既有 working tree 成果的忠实保存）
- 最终 **O0 PASS 由 Reviewer 签发**
