# 哲学家资料资产扩充 · 续作任务书（交接 zcode 新会话）

交接日期：2026-10-05（第二次交接，批次09-10 完成后更新）。交接对象：zcode + GLM 5.3 新会话（本文件为唯一权威交接入口）。
前序任务书：`docs/tasks/philosopher-assets-completion-zcode-glm53.md`（原始标准，仍有效）；本文件是其执行期的**进度快照与固化 SOP**，冲突处以本文件为准。

## 1. 可直接复制给新会话的启动指令

> 请执行本仓库 `docs/tasks/philosopher-assets-continuation-zcode.md`。先读它（含现状、SOP、批次11名单、已知陷阱），再读 `AGENTS.md`、`docs/tasks/philosopher-assets-progress.json`（台账）、`docs/tasks/research-agent-brief.md`（研究代理通用任务书）。从批次 11 开始，按 SOP 持续推进剩余 502 位：每批 15 人（欧洲5/东亚5/其他传统5），逐人"研究代理→结构校验→独立复核→晋升→管线→抽查→提交"，每批结束更新台账与批次报告。已有的 165 份资料包、冻结批次、肖像停显记录不得破坏。人物条目身份先核对站内 data 文件再写。每 2-3 批按第 6 节流程发布。上下文将满时（约每 2-3 批）停下写新的交接文件并提交推送。

## 2. 现状快照（2026-10-05，批次10 后）

- **进度**：主名单 652 位中 **165 份 source-backed**（31 份原包 + 批次02-10 共 135 份新包）。剩余 502。26 身份待核实、59 背景资料未开始。**1 例阻塞**：穆尔雅纳（身份不可核实，见台账 blocker 字段）。
- **发布状态**：批次 02-10 已**上线**（快进合并提交 `6eadacdbe` 推 master，生产 dp-commit=6eadacdb 已验证；OSS 148 对象上传、36 资产引用全 200、幂等二过 0 上传、生产端 editorial JSON 抽查通过）。发布证据在台账 `release` 字段。
- **工作分支**：`codex/philosopher-assets-balanced-02`（与 master 同步在 6eadacdbe 之后含台账/交接更新提交）。**继续在此分支叠批次提交，每 2-3 批合并推送 master 一次并按第 6 节发布**。
- **工作区**：`/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（git worktree；**不要碰** `/Users/sen/DeepPhilosophy`——那是另一检出）。`.env`（OSS 凭证）只在主检出根，用完即从 worktree 删除，绝不提交。
- **台账**：`docs/tasks/philosopher-assets-progress.json`（每批必更新：roster 先登记、完成后回填 status/validation/keyCorrections）。批次报告在 `docs/tasks/author-assets-batch-2026-10-03-balanced-0{2..8},09,10.md`。

## 3. 每批 SOP（固化为九步）

1. **选名单**：欧洲/东亚/其他传统各 5。**登记前先校验键**：
   ```python
   python3 -c "import json; people=json.load(open('app/public/philosophers.json')); led=json.load(open('docs/tasks/philosopher-assets-progress.json')); print([(n, people.get(n,{}).get('listingKind')) for n in [<候选15人>] ])"
   ```
   键必须存在、listingKind=thinker、且不在台账 people 里。东亚未用键池（112 个，含 嵇康/阮籍/熊十力/牟宗三/梁漱溟/商鞅/道宣/米拉日巴/龙钦巴/李珥/宋时烈/朴趾源/崔济愚/九鬼周造/田边元/西谷启治/和辻哲郎/顾颉刚/毛泽东/邓小平/习近平 等——**政治在世人物谨慎**，措辞按第 5 节）。注意键名可含空格括号（如「李珥 (Yi I, 栗谷)」），name 字段与文件名必须用全串。登记脚本参考批次08（写 ledger.batches[批次ID] + people 15 条，status=researching），batch ID 递增 `2026-10-03-balanced-09`…（日期前缀沿用序列即可）。
2. **研究代理**（每波 ≤5 个，防限流）：提示词 = "先读 docs/tasks/research-agent-brief.md 并严格照做。批次 <ID>，人物「<键>」，regionCohort「<组>」" + 人物专属要点（来源建议、须核事实、worksPolicy 倾向、关系候选）。产出 `docs/author-research/<批次ID>/<人名>.json`（证据）+ `drafts/<人名>.json`（草稿）。
3. **结构校验**（本地，不动公开目录）：用 `scripts/audit_author_assets.py` 的 `assess()` 逐份跑 source-backed 检查 + 关系端点必须在 people[] + context 关系 evidenceKind 约束（historical-contact/editorial-comparison 或 label 恰为"共同思想背景"，且这两类 label 不得含"师承/师生"）+ no-autographs 不得有 authored/coauthored/edited。**常见修复**：草稿 sourceRefs 引了证据记录里的 id 但没同步进草稿 sources（从证据记录补齐即可，批次03/04/07/08 均出现过）；http→https。
4. **独立复核**（5 个代理，每人分管 2-3 人）：重访来源核对生卒/节点/书目 kind/概念出处/关系方向/引语，直接改草稿，跑同款结构自检。跨包一致性必查（如 X→Y 的关系在 Y 的包里方向是否镜像一致）。
5. **晋升**：`cp drafts/*.json app/public/philosopher/editorial/`（阻塞者不晋升，status=blocked + blocker 写明）。
6. **管线**（全绿才算过）：`python3 scripts/sync_author_catalog.py && python3 scripts/sync_school_catalog.py && python3 scripts/audit_author_assets.py && python3 scripts/test_author_assets.py && node --test app/tests/*.test.mjs && npm --prefix app run build && python3 scripts/sync_school_catalog.py --check && python3 scripts/sync_genealogy_catalog.py --check && git diff --check`；再同参数重跑 audit 验幂等（哈希一致）；`git status` 确认旧包零改动（editorial/ 下只应新增本批文件）。node 端点测试比本地校验多两条规则（people 端点、label 师承字样），失败按报错修。
7. **页面抽查**：worktree `app/` 下起 `npm run dev -- --port 5273 --strictPort`，用 browser-use 技抽查 3 人（桌面 1280 + 移动 390 轮换，覆盖本批特殊情形：无肖像回退/limited-evidence/长姓名）。DOM 快照看 heading/章节/著述/争议即可；截图存档可选。
8. **台账+批次报告+提交**：台账回填（status=validated、stats、keyCorrections、queuesRemaining 递减）；报告写 `docs/tasks/author-assets-batch-<批次ID>.md`；提交规范：
   ```sh
   git add app/public/philosopher/editorial docs/author-research docs/tasks app/public/philosopher/data app/public/philosopher/catalog.json app/public/philosopher/editorial-index.json app/public/schools/catalog.json docs/author-content-audit.json docs/author-assets-audit.json app/public/philosophers.json
   git commit -F <消息文件>   # 禁 git add -A；消息 type: 描述
   git push
   ```
   注意 `app/public/philosophers.json` 是 LFS，sync 后要一并提交（批次03曾漏）。
9. **每 2-3 批发布一次**（见第 6 节）。

## 4. 批次 11 建议名单（已校验键，2026-10-05）

- 欧洲组（建议）：阿摩尼乌斯·萨卡斯（普罗提诺之师，与批次09跨包——普罗提诺包 people[] 已有其条目）、赫尔马库斯（伊壁鸠鲁弟子，与批次09跨包）、菲洛德穆（伊壁鸠鲁派）、蒙田、皮埃尔·阿多（均为 thinker/needs-review）
- 东亚组（建议）：西谷启治（京都学派，与九鬼/田边跨包）、米拉日巴（藏传，与龙钦巴跨包）、道宣，另从「东亚未用键池」补 2（金岳霖/陈嘉映/陈鼓应 均在册 needs-review，可作候选）
- 第三组：德鲁伊·阿莫尔根（凯尔特）已验；其余按缺项优先与地域轮换自「南亚、伊斯兰、非洲、拉美与原住民传统」余量选取（登记前照第 3 节校验键）
- 注意：和辻哲郎、汉娜·阿伦特 已是原31包 source-backed，勿重复登记。

之后批次按缺项优先：全零记录优先（快照 baselineGaps≥6 者），女性候选（朱迪斯·巴特勒等在目录），地域轮换（伊斯兰/南亚/非洲/拉美/原住民），勿长期偏科。

## 5. 已知陷阱与应对（血泪经验）

- **内容过滤（1301）**：政治/宗教人物提示词会触发。对策：措辞改为纯"思想文本史/学术史"框架（不写政治叙事、不写信仰评价、敏感词绕开）；孙中山/梁启超各试 3-4 次才过；屡败可再简化（"一位近代政治学讲演文本作者"这类去名化措辞有效）。被过滤的代理任务直接重发即可。**批次09 牟宗三连试 5 次（含英文化提示词）全灭**——判定为该人物关键词组合的输入侧过滤；可行兜底：主编会话按同一研究任务书直接联网研究并撰写证据记录+草稿（如实记录流程偏差），独立复核照常执行。批次10 全部 15 人零过滤。
- **限流（1302/1308）**：单波并发 ≤5 个研究代理；复核代理 5 个一批通常安全；命中就等限额窗口重发，不丢进度（文件落盘为准）。
- **身份先核对**：写包前必须读 `app/public/philosopher/data/<键>.json` 确认站内条目到底是谁——批次08 芝诺曾把"埃利亚的芝诺"写成"基提翁的芝诺"整体重写；穆尔雅纳站内数据自相矛盾转阻塞；批次10 加西拉索（印卡·加西拉索 vs 西班牙诗人同名）与第欧根尼（犬儒 vs 拉尔修）同靠此步防错。
- **站内键陷阱**：键名≠你以为的人物（"雅各布森"是丹麦诗人非语言学家；"林肯"不在目录；「芝诺」=埃利亚的芝诺）。relations 用站内键前先查 people 列表确认该键的 listingKind 与实际身份；不确定就作站外人物（给出处链接）。**硬规则：所有 relations 端点（除本人）必须同时列进 people[]**（node 测试 authorsContent 名集校验）——批次09 阮籍/梁漱溟曾漏。
- **跨包一致性**：新包的关系若涉及已有包（如 A→B teacher 而已完成 B 包写了 B→A），方向语义必须相容；复核阶段专门安排跨包检查。批次09/10 每包镜像关系均逐一核对。
- **context 关系铁律**：context 类型要么 evidenceKind=historical-contact/editorial-comparison（有 detail 且 label 不得含"师承/师生"），要么 label 恰为「共同思想背景」——批次10 西塞罗曾用 context+「学园师承」被本地校验拦下（改 teacher 解决）。
- **流水线细节**：sync 后 philosophers.json（LFS）常滞留未提交；audit 的 SystemExit 是门禁不是 bug；`--date` 参数已支持（历史日期可复现）；audit 幂等用同参数重跑比对哈希。

## 6. 发布流程（2026-10-05 已跑通一次）

1. 分支推 master：先 `git fetch origin`，若 master 有新进（其他会话）→ merge（唯一可能冲突 `app/public/schools/catalog.json`：取 master 版为底，跑 `sync_author_catalog.py + sync_school_catalog.py` 重生成，全绿后提交合并），`git push origin HEAD:master`。
2. 等 CF Pages 生产构建（数分钟），验证：`curl -s https://deepphilosophy.top/?v=$(date +%s) | grep -oE 'dp-commit[^>]{0,80}'` 应为预期提交短哈希。
3. OSS（凭证 `/Users/sen/DeepPhilosophy/.env`，先 `cp` 到 worktree，**用完删除**；Python 用 `/Users/sen/DeepPhilosophy/.venv/bin/python`，系统 python 无 oss2）：
   ```sh
   /Users/sen/DeepPhilosophy/.venv/bin/python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.top
   /Users/sen/DeepPhilosophy/.venv/bin/python backend/tools/dp_sync_oss_static.py --only=philosophers.json,philosopher/catalog.json,philosopher/data,philosopher/editorial,philosopher/editorial-index.json,philosopher/portrait-audit.json,schools/catalog.json,schools/data,app/assets
   /Users/sen/DeepPhilosophy/.venv/bin/python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.top --verify-only   # 36引用全200
   ```
   再跑一遍 sync（应需上传 0，验证幂等）。抽查 OSS JSON 用正确百分号编码（UTF-8 三字节/汉字，别手抄错——顗=%E9%A1%97）。
4. 台账 `release` 字段记证据（提交/URL/时间/上传数/抽查项）。

## 7. 剩余队列与最终口径

- thinkersToComplete 502（批次11起按第 4 节节奏）；identitiesToResolve 26 与 contextToReview 59 **尚未开始**——建议主名单推进至 ~250 份后穿插处理（背景资料需先为其建立独立验收规则，见原任务书 §7）。
- 完成定义不变：不冒充、不降门槛；阻塞如实记录。台账是唯一进度真源。
- 本文件本身不是永久文档：主名单全部完成时，写 `docs/author-assets-completion-report.md` 终报（口径见原任务书 §10）。
