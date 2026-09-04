# PHIAGENT_O0_BASELINE_RECONCILIATION

- 性质: O0-R — Baseline Reconciliation Gate（只读司法鉴定式对账；除本文档与
  `docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md` 外未写入任何文件，未执行任何
  git 状态变更操作，未重启/修改任何服务）。
- 执行时刻: 2026-09-04（AUDIT-01 冻结同日）。
- 结论速读: **+3 行已被字节级精确复原并双 sha 校验**；它是 AUDIT-01 会话自身在定稿后
  23 分钟针对用户实报的流式渲染断裂 bug 所做的生产修复，与 T1.1-H 无关、未被任何
  测试钉住、当前运行时正在加载。可安全纳入基线。

---

## 1. CURRENT STATE SNAPSHOT

### 1.1 git 状态

| 项 | 值 |
|---|---|
| HEAD | `ec09e04da914d55ba3904fc5812785b2f81729f6` |
| branch | `master` |
| last commit | 2026-08-31 21:46:54 +0800 — `fix: 查阅资料无法展开 — merged 组 isOpen 读取键与写入键不一致` |
| tracked modified | 40 files，`+3890 / −521`（app 前端 12 + schools json 7 + backend 21，均为 AUDIT-01 之前既存的工作树状态） |
| untracked | 25 个顶层路径（`.agents/`、`AGENTS.md`、backend 新模块×5、backend/tests×4、docs×15、scripts×1） |

### 1.2 quote_bound.py（当前）

| 项 | 值 |
|---|---|
| size | 23,493 bytes |
| line count | **432** |
| mtime | 2026-09-04 **16:33:53.979** +0800 |
| sha256 | `3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13` |
| git 状态 | untracked |

### 1.3 16:10 之后发生变化的文件（全仓扫描，按类别）

AUDIT-01 文档本身定稿于 **2026-09-04 16:10:01.079**（mtime），与 quote_bound.py 的
mtime 差 **+23 分 52 秒**，与 O0 PRE-FLIGHT 的「约 23 分钟」吻合。

| 类别 | 文件 | mtime | 说明 |
|---|---|---|---|
| **SOURCE** | `backend/quote_bound.py` | 16:33:53 | 16:10 后**唯一**变动的 backend Python 源文件（`find -newermt '16:10'` 全量扫描证实） |
| TEST | — | — | 无（`test_phase_t1.py` 最后修改 09-03 23:14，`test_phase_t.py` 09-03 07:54，均早于冻结点） |
| DOC | — | — | 无（AUDIT-01 16:10:01 为冻结动作本身；DECISION_AUTHORITY_MAP 16:09:25 在冻结前） |
| TRACE/CACHE | `backend/__pycache__/quote_bound.cpython-311.pyc` | 16:34:13 | 编辑后 20 秒由 Python 3.11 编译，编译自当前 432 行版（对复原 BEFORE 无证据价值） |
| TRACE/CACHE | `backend/.pytest_cache/v/cache/nodeids` | 16:42:18 | O0 PRE-FLIGHT 的 pytest 收集痕迹 |
| TRACE/CACHE | `backend/data/*.jsonl` ×7、`admin_stats.json` | 16:41–16:44 | 运行中服务的 tracing/stat 写入（runtime trace，非源码） |

### 1.4 LOC 对账

按 AUDIT-01 自己的口径（`backend/*.py + routes/*.py`，47 个文件）现算：
**15,980 = 15,977（AUDIT-01）+ 3**，差值与 quote_bound.py 的 +3 行完全闭合，
不存在第二处未解释的源码增量。

---

## 2. EXACT 3-LINE FORENSICS

quote_bound.py 为 untracked，无法依赖 git diff。按证据优先级执行：

### 2.1 证据链（来源 A：历史副本 = 编辑器级快照）

1. 全仓搜索 `*quote_bound*`：仅两份——当前源文件与 16:34:13 的 pyc（后者晚于编辑，
   无效）。无 editor backup、无临时复制、无 patch 文件；`~/.bash_history` 不存在。
2. **决定性证据**：ZCode 会话工件
   `~/.zcode/cli/artifacts/sess_625be044-f1c2-4a81-9a1a-2335b1a2ff84/call_f7b5747a91d94d2387361a26-tool-result-58f7c69f-bc55-4de0-971a-8fe3f353778a.json`
   （`kind: workspace_file_before_change`，createdAt **2026-09-04T08:33:53.999Z** =
   16:33:53.999 +0800，与源文件 mtime 差 20ms）。Edit 工具在落盘前把**完整编辑前
   文件内容（beforeContent）+ 结构化 patch** 存入了该工件。
3. **跨会话排他性**：扫描所有会话的 artifacts 目录，16:10–16:35 窗口内全系统只有两条
   工件写入——16:10:01（AUDIT-01 文档保存）与 16:33:54（本次 Edit）。即**冻结后唯一
   的工作区变更就是这一次 Edit**。

### 2.2 复原与验证（禁止伪造 → 全部机器校验）

| 校验项 | 结果 |
|---|---|
| beforeContent 行数 | **429 行**（= AUDIT-01 冻结值） |
| BEFORE sha256 | `c184798e3ab3282e30dd705924ffd1c6eaf7364a9189c0086c3e052d4b5a15f0`（23,149 bytes UTF-8） |
| patch 形状 | oldStart=335，−3 行 / +6 行（净 **+3**） |
| beforeContent + patch 重构 vs 当前磁盘文件 | **字节级完全一致（True）** |
| Edit 工具入参 old_string/new_string（rollout 记录） | 与 structuredPatch 逐字吻合 |
| 当前文件 sha256 | `3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13` ✓ |

**EXACT_DIFF_RECONSTRUCTABLE = true**（非推断，是带双 sha 的字节级复原；
BEFORE 副本留存于 repo 外临时目录 `%TEMP%/o0r_forensics/quote_bound_before_429.py`）。

### 2.3 那 3 行：精确内容

位置：`QuoteBoundSanitizer.push()` 尾部残余处理（BEFORE 338–340 行 → AFTER 338–343 行）。

BEFORE（429 行版，3 行）：

```python
        # 尾部残余按一行处理: blockquote 行进缓冲（等闭合）, 普通文本即时放行（保流式节奏）
        line, self._buf = self._buf, ""
        out += self._process_line(line)
```

AFTER（432 行版，6 行）：

```python
        # 尾部残余: 普通文本即时放行（保流式节奏）; blockquote 行残余必须留在缓冲等下一块拼接。
        # chunk 可能把 "> 「…" 从中间劈开（无换行符）——若把残余当完整行处理, 引用行会被腰斩成
        # "> 「\n正文"（引用块只剩半个引号、正文掉出引用块; 真实回归: 言必有中 R 系列渲染断裂）。
        if self._buf and not BLOCKQ_LINE_RE.match(self._buf):
            line, self._buf = self._buf, ""
            out += self._process_line(line)
```

### 2.4 证据来源 B/C/D

- **B（T.1 报告逐字描述）**：`PHIAGENT_PHASE_T1_SOURCE_VERIFICATION_REGRESSION.md`
  （09-03 23:39）对 T1.1-H 只记录 `VERIFY_NOW_DIRECTIVE` + `VERIFY_LATER_RE`，
  从未提及 `VERIFY_LATER_OPEN_RE` 独立常量，更未提及 push() 残余处理——**3 行与 T.1
  报告描述不对应**。
- **C（测试依赖）**：无任何测试依赖这 3 行——§5 中 BEFORE 版本同样 24/24 全绿
  （测试文件本身早于该修改存在，逻辑上也不可能依赖）。
- **D（mtime/注释/patch marker）**：mtime 16:33:53 唯一命中冻结后窗口；新增注释自述
  动机（流式 chunk 劈开 `> 「` 的真实回归）。

---

## 3. PROVENANCE CLASSIFICATION

### 3.1 事件还原（来自会话 rollout `sess_625be044` = AUDIT-01 同一会话）

1. 该会话即产出 AUDIT-01 的工作会话（首条消息为「审计测试架构分类」子代理报告）；
   16:10:01 定稿 `PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md`。
2. 其后用户发来截图报障：「前端渲染有点坏了」——blockquote 只剩一个 `「`，
   引文正文掉出引用块变成普通段落。
3. 会话用复现脚本确认根因（未改代码）：push 序列
   `push3 = "> 「\n鲁人为长府，闵子骞曰：…"` 使引用行被腰斩成 `> 「` + 掉块正文，
   与截图一致；BEFORE 代码对「chunk 恰好终结在 `> 「` 之后」的残余无条件按整行处理，
   导致孤立 `「` 闭块放行。
4. 16:33:53 执行上述 Edit 修复；16:34:13 快速 import 验证（pyc）；16:37–16:41 经本地
   8011 服务做了多轮真实验证（agent_loop_trace 计数：16:37×9、16:38×7、16:40×7、
   16:41×4）；16:43:08 服务以新代码重启（见 §4）。

### 3.2 与 T1.1-H 正式行为的对照（task 第 3 节指定）

| T1.1-H 已批准行为 | BEFORE(429) 是否已实现 | 本次 3 行是否触及 |
|---|---|---|
| `VERIFY_NOW_DIRECTIVE` | 已实现（`routes/agent_tools_retrieval.py` 注入层，冻结前） | 否 |
| `VERIFY_LATER_RE` | 已实现（58–62 行，逐字未动） | 否 |
| 核验已完成时补正（`_CORRECT_H_*`） | 已实现（403–405 行，逐字未动） | 否 |
| 核验未完成时边界说明（`_BOUNDARY_H_*`） | 已实现（406–408 行，逐字未动） | 否 |

机器佐证：`VERIFY_LATER_OPEN_RE` 在 beforeContent 中**已存在**（T1.1-H 本体在 T1 阶段
就已定形）。这 3 行完全不在 T1.1-H 语义面内。

### 3.3 分类

**POST_AUDIT_CHANGE_CLASS = C** — 不属于 A（非 T1.1-H 既定实现）、不属于 B（非
test/debug 埋点，是生产流式渲染路径的正式修复）、不属 D（出处 100% 确定）。
「unrelated/manual edit」取其「冻结范围之外」的严格含义：它是**审计会话自身在冻结后
应实报 bug 做的一次有完整证据链的预算外生产修复**，动机、内容、验证过程全部可考。

---

## 4. PRODUCTION ALIGNMENT

只读确认，未触碰服务：

| 项 | 值 |
|---|---|
| 运行时 | 本地 FastAPI :8011（即 AGENTS.md 所述统一后端 = agent 生产运行时；公网 CF Workers 不执行此 Python 模块） |
| 进程 | PID **10220**，`"…\Python311\python.exe" main.py`，**创建于 2026-09-04 16:43:08** |
| 加载判定 | 进程启动时间(16:43:08) **晚于** quote_bound.py mtime(16:33:53)；`engine_langgraph.py:23` 顶层 `import quote_bound as QB` → 启动即加载**当前 432 行版** |
| 存活佐证 | `GET /api/health`（只读）→ `{"status":"healthy","version":"1.2.0"}`（17:26:46）；`backend/data/admin_stats.json` 由该实例于 16:44:09 写入（证明 cwd = 本仓库 backend/） |
| 附加证据 | 前一会话记录在案：此前常驻进程 PID 18852 启动于 16:19:36（watchdog 拉起，早于编辑，当时加载的是 429 行版）→ 16:43:08 由现 PID 10220 接替 |

- `PRODUCTION_QUOTE_BOUND_SHA` = `3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13`
- `LOCAL_QUOTE_BOUND_SHA` = `3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13`
- **MATCH = true**（依据：加载时序 + 顶层 import 语义 + 存活/写入佐证。未对运行中进程
  做内存 dump——那需要注入/调试器，违反「不得重启服务/不动服务」的约束，故标注为
  高置信推理而非直接哈希读出。）

---

## 5. TEST IMPACT

只跑了测试，未改任何代码（`.pytest_cache` 用 `-p no:cacheprovider` 抑制）。

| 运行 | 对象 | 结果 |
|---|---|---|
| ① 常规 | 当前 432 行版，`test_phase_t1.py` 全量（T1.1-A~H，含 TestT11DQuoteBound / TestT11FStitching / G·H scan） | **24 passed** (6.92s) |
| ② 隔离 | repo 外临时目录中的 **429 行 BEFORE 副本**，通过一次性 pytest 插件在 `sys.modules` 层替换 `quote_bound`（测试文件与其余 backend 全部用真实当前版），插件在 `pytest_unconfigure` 打印实际加载路径以供核验 | **24 passed** (5.72s)，实测加载路径 = BEFORE 副本 ✓ |

结论：**两个版本测试完全等价（24/24 = 24/24）**。测试套件（09-03 定稿）早于该修改，
不 pin 这 3 行；反之，回退到 429 行版也不会红任何测试，只会重新引入已复现的
流式渲染断裂。quote_bound 相关测试 = `test_phase_t1.py` 内 T1.1-D/F/G/H 全部用例，
无独立 quote_bound 专属测试文件。

---

## 6. REVIEWER-USEFUL CONCLUSION

```text
POST_AUDIT_CHANGE_CLASS      = C   （冻结范围外的生产修复；出处 100% 确定，非 T1.1-H、非埋点、非未知）
BEHAVIOR_CHANGE              = YES （仅 QuoteBoundSanitizer.push() 的 chunk 尾残余调度：
                                     blockquote 行残余由"立即按整行处理"改为"留缓冲等下一块拼接"；
                                     核验/闭块/审计语义不变，仅影响引用行被 chunk 劈开的流式形态）
PART_OF_T1_APPROVED_SCOPE    = NO  （T1.1-H 四要素在 BEFORE 中已全部存在且逐字未动）
CURRENT_PRODUCTION_USES_IT   = YES （PID 10220 于 16:43:08 随启动加载 432 行版，健康运行中）
SAFE_TO_INCLUDE_IN_BASELINE  = YES （字节级出处+动因+验证链完整；两版测试全绿；正在生产服役；
                                     回退反而复活已复现的用户可见 bug。
                                     建议（非 O0 范围）：后续补一条"chunk 劈开引用行"的回归测试，
                                     把该行为钉进测试面）
```

---

## 7. HASHING PROCESS 修正（取代 AUDIT-01 聚合 digest）

AUDIT-01 的 `716d7175…000a8` 只记录了「对全部 backend 跟踪+未跟踪文件逐一 sha256sum
后再聚合」，未写死文件清单/聚合算法/顺序，**不可复现**，自本 Gate 起废弃。

新基线口径：**逐文件 manifest + MANIFEST_SHA256**，见
[PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md](PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md)：

- 范围：`backend/**/*.py` 全量 130 个（含 untracked 新模块与 `backend/data/__init__.py`
  空包标记）+ `docs/PHIAGENT_*.md` 11 份 = **141 条**（tracked 123 / untracked 18）
- 排除：`.env`/secret、`__pycache__`、`.pytest_cache`、`backend/data` 运行时数据、
  临时 json、本 Gate 两份输出文档（按名排除，生成于哈希之后）
- 算法（写死）：repo-relative POSIX path → UTF-8 码点序排序 → 每行
  `<sha256><两空格><path>\n` → 对完整 manifest bytes 取 sha256

```text
MANIFEST_SHA256 = 45ffe862c8b088e5303ac44b84bd1bb8ced48645a9ca90d6d03d1fb5b2d28769
```

---

## RECEIPT

```text
O0_R                       = COMPLETE

HEAD                       = ec09e04da914d55ba3904fc5812785b2f81729f6
CURRENT_WORKTREE_FILES     = 40 tracked-modified + 25 untracked top-level paths
                             （快照时刻；本 Gate 另新增 2 份 docs 文档，未触碰任何既有文件）

AUDIT_QUOTE_BOUND_LOC      = 429
CURRENT_QUOTE_BOUND_LOC    = 432
EXACT_DIFF_RECONSTRUCTABLE = true
                             （beforeContent 429 行 sha256=c184798e…5a15f0，+patch → 与当前
                              432 行 sha256=3c0b88c1…fca13 字节级一致，双 sha 机器校验）

POST_AUDIT_CHANGE_CLASS    = C
BEHAVIOR_CHANGE            = YES
PART_OF_T1_APPROVED_SCOPE  = NO
CURRENT_PRODUCTION_USES_IT = YES
SAFE_TO_INCLUDE_IN_BASELINE= YES

T1_TESTS                   = test_phase_t1.py 24/24 PASS（当前 432 行版）
                             隔离 429 行 BEFORE 版 24/24 PASS（sys.modules 替换法，路径已核验）
PRODUCTION_CODE_CHANGED    = false

HASH_MANIFEST              = docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md
MANIFEST_SHA256            = 45ffe862c8b088e5303ac44b84bd1bb8ced48645a9ca90d6d03d1fb5b2d28769

REPORT                     = docs/PHIAGENT_O0_BASELINE_RECONCILIATION.md
```

STOP — O0 后续步骤未执行，等待放行。

---

## 8. RE-VERIFICATION ADDENDUM（2026-09-04 17:45–17:55 第二遍独立复核）

本文档初版完成后，O0-R 以**不信任初版、全部重算**的方式执行了第二遍独立复核。
所有关键值均从原始证据重新推导，结果与初版**逐项一致**：

| 复核项 | 方法 | 结果 |
|---|---|---|
| BEFORE 字节复原 | 直接读取会话工件 `call_f7b5747a…json` 的 `beforeContent`，独立 sha256 + 独立应用 structuredPatch | BEFORE = 23,149 bytes / 429 行 / sha256 `c184798e…5a15f0`；RECON bytes 23,493，**与当前磁盘文件逐字节相等（True）**，双 sha 吻合 ✓ |
| 冻结后排他性 | `find ~/.zcode/cli/artifacts -newermt 16:10 ! -newermt 16:36` 全系统扫描 | 恰好 3 条写入，全在 sess_625be044：16:10:01.126（AUDIT-01 保存）、**16:27:32.832（用户上传 PNG 截图=data:image/png;base64，即报障图）**、16:33:54.001（本 Edit）✓ |
| 16:10 后源码变动 | `find backend -name '*.py' -newermt 16:10` 重扫 | 仍仅 `backend/quote_bound.py` ✓ |
| 历史副本 | `find . -name '*quote_bound*'`（排除 .git/__pycache__）+ `~/.bash_history` | 全仓仅 1 份源文件；无 bash history ✓ |
| T1.1-H 对照 | T1 报告 grep + BEFORE 文件 grep | T1 报告无 `push()`/尾部残余描述；`BLOCKQ_LINE_RE`（BEFORE 第 44 行）、`VERIFY_LATER_OPEN_RE`（BEFORE 第 57 行）在 BEFORE 中已存在 ✓ |
| LOC 对账 | `wc -l backend/*.py backend/routes/*.py` 重算 | 47 文件 / 15,980 行 = 15,977 + 3，闭合 ✓ |
| §4 production | 进程/健康检查重做 | 服务 healthy；**两个 PID 关系澄清：10108（.venv 启动器）是 10220（Python311 实际解释器）的父进程**（ParentProcessId=10108），二者同创于 16:43:08 > 源文件 mtime 16:33:53，同一逻辑服务，加载 432 行版 ✓ |
| §5 测试重跑 | ① 当前版 `test_phase_t1.py` | **24 passed** (9.41s) ✓ |
| §5 测试重跑 | ② 隔离 BEFORE 版（`PYTHONPATH` + `-p qb_before_plugin` 模块名形式；注意 pytest `-p` 不接受路径形式） | **24 passed** (5.60s)，插件打印实际加载路径 = `…/o0r_forensics/quote_bound_before_429.py` ✓ |
| §7 manifest 重算 | 全新遍历 `backend/**/*.py` + `docs/PHIAGENT_*.md`（同名排除两份 Gate 文档）重算 | 141 条（tracked 123 / untracked 18）、manifest bytes 13,685、**MANIFEST_SHA256 = `45ffe862…28769` 与初版完全一致**；清单文档 141 行逐行与活树机器比对 **0 mismatch**，基线无漂移 ✓ |
| worktree 计数 | `git status --porcelain` | 40 tracked-modified；untracked 顶层路径 **27 = 25（快照时刻）+ 本 Gate 两份输出文档**，与 RECEIPT 口径闭合 ✓ |

**复核结论：初版全部结论维持成立，RECEIPT 原样 reaffirm；本附录仅为第二遍独立验证的存证。**
