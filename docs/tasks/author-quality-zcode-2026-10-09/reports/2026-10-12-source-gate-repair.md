# 来源门禁纠偏与剩余资料补全——执行报告

任务书：`../2026-10-12-source-gate-repair.md`；授权名单：`../2026-10-12-source-gate-repair-queues.json`。
执行者：ZCode。执行分支：`codex/zcode-author-quality-20261009`（锁定工作区）。

## 阶段A：门禁加固与精确授权（2026-10-13 提交）

### 工作区核对

- 目录/分支核对通过：`codex/zcode-author-quality-20261009`，起点 `a9f79614f`（交接快照，无新增提交）。
- 交接时工作区已有上一执行段落的未提交成果（门禁脚本、guard、测试、锁文件授权登记、标准/研究简报模板更新、W66合并包及其草稿/检查点、鲍曼与合并包的released claim）。本段对其逐项验证后继续，未重置、未清理。
- `git fetch origin master` 完成；`merge-base(HEAD, origin/master) = a9f79614f`，主线（master）已前进，合并时按任务书第8节处理。

### 门禁修复内容（`scripts/check_author_source_evidence.py`）

- `packet_is_gated()` 改为按**包身份**判定：本轮授权名单（从锁文件 `roundAuthorization` 读取）∪ 不在冻结基线的包（新建）∪ 内容摘要与 `frozenEditorialHashes` 不符的包（被修订）一律门禁；仅字节级未变的基线包豁免并显式记为「历史基线兼容」。锁文件缺失/不可解析 → `SystemExit` 硬错误，不自动全免。
- 来源必填字段 `id/title/url/type/accessedAt/accessScope` 逐条校验，缺失报 `missing-required-field:<field>`。
- `abstract-or-catalog` 只支撑书目题名/版本/年代：出现在 life/concepts/people/relations/readingRoutes/overview/debate 的 `sourceRefs` 报 `abstract-catalog-supports-bibliography-only:<id>`。
- `confirmed/corrected/inferred` 的证据 checks 引用不可读来源报 `verdict-source-not-readable:<id>`。
- 命令入口（逐人与全量）、`audit_author_assets.assess()`（编译状态）、测试套件使用同一 `evaluate()`；`main()` 输出 `historicalCompatibilityExempt` 计数，历史兼容不再是静默豁免。

### 权限登记（`worktree-lock.json` + `scripts/guard_author_quality_worktree.py`）

- 锁文件新增 `roundAuthorization`：73 人修复名单（72漏检包+胡汉民）、`contextApplicationNames=[汉谟拉比]`、任务书路径、名单SHA256；原有 `repairExistingPackets` 11 人原样保留；`workspace/branch/baseCommit/baseline/frozenEditorialHashes` 未动。
- guard 新增 `round_authorization()`：读取锁文件授权表并与授权队列文件核对（名单集合、两个SHA256、任务书路径、原11人名单），任何不一致即 fail——锁表只能收窄不能扩权。
- guard 的 editorial 检查改用 `catalog_key_for_stem()` 解码文件名编码（`/`→`-`），修复了交接时 `GUARD FAILED: 正式资料包不是目录人物：让-弗朗索瓦何维勒-马修理查德.json` 的误报根因（文件名编码 vs 目录键），未放宽任意姓名校验。
- 修复白名单合并登记名单与原11人；冻结哈希保护仅对白名单内人物开放，其余已发布包维持原保护。

### 回归（任务书第3节负例清单 → `scripts/test_author_assets.py`）

| 负例 | 结果 |
|---|---|
| 阅读字段全缺的新包 | ✅ `missing-required-field:accessScope` |
| 基线包修订后继承豁免 | ✅ 修订即门禁（摘要不符） |
| 本轮名单中的包即使与冻结摘要一致 | ✅ 名单优先门禁 |
| 锁文件缺基线 | ✅ 硬错误/空冻结表→新包必门禁 |
| 未变基线单列兼容 | ✅ `historicalCompatibilityExempt` 显式计数 |
| search-summary/维基支撑正文 | ✅（原有负例保留并通过） |
| 书目层只支撑编目事实 | ✅ `abstract-catalog-supports-bibliography-only` |
| confirmed 引用未读来源 | ✅ `verdict-source-not-readable` |
| 编译状态一致性 | ✅ 编译测试改为「level 与 gaps/errors 一致；needs-review 必须给出可定位错误」 |

### 新规则全量诊断与真实状态重编译（2026-10-13）

- 门禁：gated 159 / 历史兼容 428 / **失败 94**。
- `sync_author_catalog.py --date 2026-10-13` + `audit_author_assets.py --date 2026-10-13` 重编译：索引 **source-backed 493 / needs-review 94**（652 thinkers）。586→493 的下降是门禁修复后的真实口径，非内容回滚；正文与路由全部保留可用。
- 94 = 授权73 + 原11人中仍缺阅读元数据的6（佩吉·坎芙、卡罗琳·汉弗莱、马库伊尔肖奇特尔、比尔·尼布利特、黑麋鹿、科林·豪森）+ 无本轮授权但被更严规则新揪出的15（伏尔泰、布莱兹·帕斯卡尔、布鲁诺·德·菲内蒂、歌德、托马斯·内格尔、托马斯·马尔萨斯、威廉·巴特勒·叶芝、弗里德里希·施莱尔马赫、彼得·厄巴哈、赫伯特·马尔库塞、加塔里、杨献珍、爱尔维修、汉斯·约纳斯、詹姆斯·科恩）。
- **无授权的15份按任务书如实保持待审，未擅改**；建议下轮授权按同一补证据方式处理。
- `audit_author_assets.py` 在存在待审包时按设计 exit=1 响铃；全部授权包修复后应回到0。

### W66 合并人物包（让-弗朗索瓦何维勒/马修理查德）的保全与隔离

- 该包为上一段落未提交成果，实体裁决（两人/对话组/集合记录）未完成，且22项门禁错误（全部正文引用建立在普通维基线索上）。按任务书第5节：**不提交其 source-backed 状态**。
- 处置：正式包文件移至研究区 `docs/author-research/author-quality-2026-10-09/2026-10-11-batch-w66/drafts/让-弗朗索瓦何维勒-马修理查德.editorial-packet.json`（连同草稿/检查点/编译快照四份副本完整保留）；公共路径 `philosopher/data/让-弗朗索瓦何维勒-马修理查德.json` 回退到 HEAD 遗留条目（正文与路由保持可用）；目录键不动。编译测试中「马修·理查德 关系端点不可解析」随包移出而消除；实体裁决进入待办（见阶段D）。

### 交接时遗留缺陷（不在本轮授权内，如实记录）

1. `安提斯泰尼` 包（W9批次，本任务产物）：`worksPolicy=no-autographs` 但书目两条佚失演说辞标 `kind=authored`——`test_no_autographs_are_not_invented_to_fill_the_bibliography` 在 HEAD 即失败。修复需将其加入修复授权，本轮不得擅动；**待办：下一轮授权单列**。
2. 胡汉民 `invalid-source-metadata`（jds-hu http URL）在授权名单内，阶段C处理。

### 检查快照

- `test_author_assets.py`：30 测试，唯一失败=上述预存安提斯泰尼项。
- `check_author_source_evidence.py`：gated 159 / exempt 428 / failures 94（=索引 needs-review，两口径一致）。
- `guard_author_quality_worktree.py --check`：`ok: true`。

## 阶段B：贯穿样本（进行中）

见下文逐项记录。
