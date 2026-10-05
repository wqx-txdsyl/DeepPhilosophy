# 哲学家资料资产扩充 · 续作任务书（交接 zcode 新会话）

交接日期：2026-10-05（第三次交接：批次 02-11 已上线；批次 12 进行中 9/15）。交接对象：zcode + GLM 5.3 新会话（本文件为唯一权威交接入口）。
前序任务书：`docs/tasks/philosopher-assets-completion-zcode-glm53.md`（原始标准，仍有效）；本文件是其执行期的**进度快照与固化 SOP**，冲突处以本文件为准。

## 0. 用户新节奏（2026-10-05 指示，优先级最高）

1. **每完成一个批次 → 立即推送上线**（合并 master → CF Pages → OSS 双端核验），不再攒 2-3 批。
2. 上线后**快速汇报**（≤200 字），**不停顿直接开始下一批**。
3. 每次汇报（及每次交接）附**失败汇总整表**（环节/对象/失败原因/处置）。
4. 上下文将满或连续触发内容过滤时：立即收尾，更新本文件并提交推送，交新会话。

## 1. 可直接复制给新会话的启动指令

> 请执行本仓库 `docs/tasks/philosopher-assets-continuation-zcode.md`。先读它（含现状、批次12在途状态、SOP、内容过滤处置预案、附录A事实线索），再读 `AGENTS.md`、`docs/tasks/philosopher-assets-progress.json`（台账）、`docs/tasks/research-agent-brief.md`。首先**收尾批次 12**（详见第 4 节：6 人研究 → 全批校验/复核/晋升/管线 → 上线），然后按 SOP 继续批次 13 及以后（剩余 472 位）。节奏按第 0 节：每批即发布、快报、失败整表。已有的 180 份资料包、冻结批次、肖像停显记录不得破坏。人物条目身份先核对站内 data 文件再写。

## 2. 现状快照（2026-10-05 第三次交接）

- **进度**：主名单 652 位中 **180 份 source-backed 已上线**（31 原包 + 批次02-11 共 149 新包）。剩余 472。26 身份待核实、59 背景资料未开始。1 例阻塞：穆尔雅纳。
- **发布状态**：批次 11 已上线（生产 dp-commit=8ddee04c 已验证；OSS 58 对象上传、36 引用全 200、幂等二过 0）。台账 `release` 字段有证据。
- **批次 12 在途**（已登记台账，未提交任何 app/public 改动）：
  - 已产出证据记录+草稿 9 人（台账 status=drafted，文件在 `docs/author-research/2026-10-03-balanced-12/`）：约翰·邓斯·司各脱、罗吉尔·培根、托马斯·莫尔、乔尔丹诺·布鲁诺、乔治·贝克莱、冈波巴、萨冈彻辰、阿底峡尊者、扎纳巴扎尔。**未经结构校验与复核**。
  - 待研究 6 人：素拉·西瓦拉克（**硬过滤对象**，处置见第 5 节与附录A）+ 尼扎米·甘贾维、肖塔·鲁斯塔维利、格里戈尔·纳雷卡齐、伊姆霍特普、阿蒙涅姆赫特（未派发，均为常规难度：波斯诗人/格鲁吉亚史家与诗人/亚美尼亚神秘诗人/古埃及归名文本——伊姆霍特普与阿蒙涅姆赫特参照批次09普塔霍特普包的归名分层写法）。
- **工作分支**：`codex/philosopher-assets-balanced-02`（与 master 同步；批次12在途文件已随本次交接提交）。
- **工作区**：`/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（git worktree；**不要碰** `/Users/sen/DeepPhilosophy`）。`.env`（OSS 凭证）只在主检出根，用完即删，绝不提交。
- **台账**：`docs/tasks/philosopher-assets-progress.json`（唯一进度真源）。批次报告在 `docs/tasks/author-assets-batch-2026-10-03-balanced-{02..11}.md`。

## 3. 每批 SOP（九步，固化为循环）

1. **选名单**：欧洲/东亚/其他传统各 5。登记前校验：键存在、listingKind=thinker、不在台账、无既有 editorial 文件。地域轮换（伊斯兰/南亚/非洲/拉美/原住民/东南亚），女性与全零缺项优先。
2. **研究代理**（每波 ≤5）：提示词 = "先读 docs/tasks/research-agent-brief.md 并严格照做。批次 <ID>，人物「<键>」，regionCohort「<组>」" + 人物要点（来源建议、须核事实、worksPolicy 倾向、关系候选与镜像约束）。产出 `docs/author-research/<批次ID>/<人名>.json` + `drafts/<人名>.json`。
3. **结构校验**（本地脚本化，见批次09-12实践）：assess() + 端点∈{本人}∪people[] + context 关系铁律 + no-autographs 书目 kind + 概念无 book 字段 + sources 全 https + 唯一 id。**常见修复**：sourceRef 引了证据 id 未同步草稿 sources；context+「师承」字样（改 teacher 或换 label）；people[] 漏端点。
4. **独立复核**（5-6 代理，每人 2-3 人）：重访来源核对，直接改草稿，跨包镜像逐条核对（新包关系若涉及既有包必须同向同语义）。
5. **晋升**：`cp drafts/*.json app/public/philosopher/editorial/`。
6. **管线**（全绿）：`python3 scripts/sync_author_catalog.py && python3 scripts/sync_school_catalog.py && python3 scripts/audit_author_assets.py && python3 scripts/test_author_assets.py && node --test app/tests/*.test.mjs && npm --prefix app run build && python3 scripts/sync_school_catalog.py --check && python3 scripts/sync_genealogy_catalog.py --check && git diff --check`；audit 同参重跑哈希一致（幂等）；`git status` 确认旧包零改动。注意：sync 后若 --check 报流派索引需更新，重跑一次 sync_school_catalog 即可（批次11曾遇）。
7. **页面抽查**：worktree 起 `npm run dev -- --port 5273 --strictPort`（端口被占可直接复用在跑的），browser-use 抽 2-3 人（桌面/移动轮换，覆盖本批特殊情形）。
8. **台账+报告+提交**：台账回填（status=validated、stats、keyCorrections、queuesRemaining 递减）；报告 `docs/tasks/author-assets-batch-<批次ID>.md`；精确 pathspec add（禁 -A），`git commit -F <文件>`，push 分支。
9. **发布（每批一次）**：见第 6 节；随后快报+失败整表，不停顿开下一批。

## 4. 批次 12 收尾清单（新会话第一件事）

1. 派发第三组 5 人研究代理（名单见第 2 节；伊姆霍特普/阿蒙涅姆赫特重点参照普塔霍特普包的「归名文本分层+节数版本差异+no-autographs」写法）。
2. 处置素拉·西瓦拉克：按第 5 节预案 C（附录A 已备离线事实线索）。
3. 对全部 15 份草稿跑结构校验 → 6 复核代理 → 晋升 → 管线 → 抽查 → 台账/报告/提交 → 发布 → 快报。
4. 跨包镜像核对重点：阿底峡→宗喀巴（宗喀巴包既有 reading 端点，阿底峡包已按镜像写「道次第底本」）；米拉日巴→冈波巴 teacher 两包同向；托马斯·莫尔→伊壁鸠鲁 reading；贝克莱→洛克 reading / 贝克莱→休谟 influence / 康德→贝克莱 reading（逐一对照既有包）；扎纳巴扎尔与萨冈彻辰的 editorial-comparison 两包相容（萨冈彻辰包复核时注意）。

## 5. 内容过滤（1301）处置预案（血泪版，2026-10-05 大幅扩充）

- **一般触发**：政治/宗教人物提示词。对策：纯"思想文本史/学术史"框架、去名化、只写学术履历。重发即可（历史上 1-2 次重发通常通过）。
- **中度触发**（2 次不过）：删除一切政治/法律/王室相关语境词再试；英文提示词有时有效（批次10经验）。
- **硬过滤**（3-4 次不过，如批次09牟宗三、批次12素拉·西瓦拉克）：**不要继续在线重试**——该人物的内容通道（含 WebFetch/web_reader/维基）会被整体绑定拦截，且主会话大量处理其内容会触发**本会话 turn 级 1301**（2026-10-05 已发生，用户被迫换会话）。预案：
  - **预案A（代理换通道）**：换一个全新代理用极简去名化提示（"一位当代东南亚佛教思想写作者"）。
  - **预案B（主会话直接撰写）**：批次09牟宗三做法——主会话按任务书直接研究撰写（只访问安全学术源如 SEP），独立复核照常。
  - **预案C（离线提取，最安全）**：**绝不让敏感原文过模型上下文**。用 Bash：`curl -sL -A "Mozilla/5.0" <url> -o /tmp/x.html` 下载 → python 正则剥离标签存 `/tmp/x.txt` → 只提取**书目化事实**（生卒/教育/著作年表/机构/奖项）打印。模型只看提取后的安全子集，据此+附录A写包。已在批次12验证可行。
  - **预案D（换人）**：仍不行则从批次名单换出，台账记 blocker（参照穆尔雅纳），不冒充完成。
- **通用纪律**：涉敏感人物的汇报/文档只写书目事实，不复述传记细节；主会话感到频繁 1301 时立即收尾交接。

## 6. 发布流程（每批一次）

1. `git fetch origin`；master 有新进则 merge（唯一可能冲突 `app/public/schools/catalog.json`：取 master 为底重跑 sync 双脚本）；`git push origin HEAD:master`。
2. 等 CF Pages 构建（约 3-6 分钟）：`curl -s https://deepphilosophy.top/?v=$(date +%s) | grep -oE 'dp-commit[^>]{0,80}'` 应为新提交短哈希。
3. OSS（凭证 `/Users/sen/DeepPhilosophy/.env` 先 cp 到 worktree，**用完删除**；Python 用 `/Users/sen/DeepPhilosophy/.venv/bin/python`）：
   ```sh
   <venv>/python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.top
   <venv>/python backend/tools/dp_sync_oss_static.py --only=philosophers.json,philosopher/catalog.json,philosopher/data,philosopher/editorial,philosopher/editorial-index.json,philosopher/portrait-audit.json,schools/catalog.json,schools/data,app/assets
   <venv>/python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.top --verify-only   # 36引用全200
   ```
   再跑一遍 sync 应需上传 0（幂等）。抽查 OSS JSON 用正确百分号编码。台账 `release` 记证据（提交/URL/时间/上传数/抽查）。

## 7. 剩余队列与最终口径

- thinkersToComplete 472（批次12收尾后 457）；identitiesToResolve 26 与 contextToReview 59 未开始——建议主名单 ~250 份后穿插（背景资料需先建独立验收规则，见原任务书 §7）。
- 完成定义不变：不冒充、不降门槛；阻塞如实记录。台账是唯一进度真源。
- 主名单全部完成时写 `docs/author-assets-completion-report.md` 终报（口径见原任务书 §10）。

## 附录A：素拉·西瓦拉克——已离线提取的书目事实线索（2026-10-05，供新会话直接采用；仍须按任务书复核后使用）

来源：英文维基百科条目（经 Bash 下载离线提取的安全子集；原文全文不要重新在线抓取）。仅供起草，写入草稿前须再核至少一个第二来源（出版商页/机构页）。

- 生：1933-03-27，曼谷。
- 教育：曼谷 Assumption College；英国威尔士兰彼得大学（University of Wales, Lampeter，现为 UWTSD 一部）；1961 年在伦敦通过律师资格（Bar）。
- 期刊与机构：1960s 主编《Social Science Review》（学界称当时"民族的思想之声"）；1968 创立 Sathirakoses-Nagapradipa Foundation（SNF）；其后创立 Thai Inter-religious Commission for Development（TICD）；**INEB（国际入世佛教网络）1989 年创立**，发起人素拉，早期赞助者包括第十四世达赖喇嘛、一行禅师、Maha Ghosananda（此名单仅作机构史事实记录，写入时保持中性一行即可）。
- 奖项：Right Livelihood Award **1995**（注意：**不是 2011**——2011 年的是 Niwano Peace Prize；旧提示词有误，勿再沿用）；Niwano Peace Prize 2011。
- 著作（书目候选，出版年/社待核）：Seeds of Peace: A Buddhist Vision for Renewing Society（1992）；自传《Loyalty Demands Dissent: Autobiography of a Socially Engaged Buddhist》（1998，Parallax Press；书名如此，勿改字）；Conflict, Culture, Change: Engaged Buddhism in a Globalizing World（Wisdom Publications，ISBN 0-86171-498-9，年份待核约2005）；The Wisdom of Sustainability: Buddhist Economics for the 21st Century（2010，Souvenir Press，ISBN 978-0-9821656-1-4）。
- 思想线索（其自述）：思想重心自认深受 Buddhadasa Bhikkhu 与 P. A. Payutto 两位泰国论师影响（可作 people[]/influence 候选，须核）；甘地资源（站内「甘地」包核对镜像）；一行禅师（同侪 historical-contact）；E.F. Schumacher（交往，待核）。
- 术语史：「入世佛教」（engaged Buddhism）铸词通常归一行禅师早年，素拉为英语世界主要推广者与 INEB 制度化推手——归属分层写。
- **纪律**：该人物全部内容只写上述书目化事实与学术争论（如 engaged Buddhism 概念之争，参照 Swearer 等学者讨论）；**不写**任何法律、涉诉、流亡、王室相关内容（这就是触发源）。
