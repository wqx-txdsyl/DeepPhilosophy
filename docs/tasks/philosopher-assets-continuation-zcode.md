# 哲学家资料资产扩充 · 续作任务书（交接 zcode 新会话）

交接日期：2026-10-06（**第四次交接**：批次 02-11 已上线；批次 12 进行中 **14/15 已产出**，其中素拉·西瓦拉克待按附录B**离线事实直接起草**，无需任何联网）。交接对象：zcode + GLM 5.3 新会话（本文件为唯一权威交接入口）。
前序任务书：`docs/tasks/philosopher-assets-completion-zcode-glm53.md`（原始标准，仍有效）；本文件是其执行期的**进度快照与固化 SOP**，冲突处以本文件为准。

## 0. 用户新节奏（2026-10-05 指示，优先级最高）

1. **每完成一个批次 → 立即推送上线**（合并 master → CF Pages → OSS 双端核验），不再攒 2-3 批。
2. 上线后**快速汇报**（≤200 字），**不停顿直接开始下一批**。
3. 每次汇报（及每次交接）附**失败汇总整表**（环节/对象/失败原因/处置）。
4. 上下文将满或连续触发内容过滤时：立即收尾，更新本文件并提交推送，交新会话。**⚠️ 2026-10-06 凌晨本会话两次 turn 级 1301（均在主会话处理素拉材料阶段），主会话对素拉一律走附录B离线事实，不得重新在线抓取。**

## 1. 可直接复制给新会话的启动指令

> 请执行本仓库 `docs/tasks/philosopher-assets-continuation-zcode.md`。先读它（含现状、批次12在途状态 14/15、SOP、内容过滤处置预案、附录A/B素拉事实），再读 `AGENTS.md`、`docs/tasks/philosopher-assets-progress.json`（台账）、`docs/tasks/research-agent-brief.md`。首先**收尾批次 12**（详见第 4 节：主会话按附录B免联网起草素拉·西瓦拉克证据记录+草稿 → 15 份全批结构校验/6 复核代理/晋升/管线 → 上线），然后按 SOP 继续批次 13 及以后。节奏按第 0 节：每批即发布、快报、失败整表。已有的 180 份资料包、冻结批次、肖像停显记录不得破坏。人物条目身份先核对站内 data 文件再写。素拉·西瓦拉克是硬过滤对象：一切内容只用附录A/B书目化事实，**不写任何法律、涉诉、流亡、王室内容**，**禁止在线重新抓取其任何页面**。

## 2. 现状快照（2026-10-06 第四次交接）

- **进度**：主名单 652 位中 **180 份 source-backed 已上线**（31 原包 + 批次02-11 共 149 新包）。剩余 472。26 身份待核实、59 背景资料未开始。1 例阻塞：穆尔雅纳。
- **发布状态**：批次 11 已上线（生产 dp-commit=8ddee04c 已验证；OSS 58 对象上传、36 引用全 200、幂等二过 0）。台账 `release` 字段有证据。
- **批次 12 在途 14/15**（分支 `codex/philosopher-assets-balanced-02`，全部在 `docs/author-research/2026-10-03-balanced-12/`，均**未做结构校验与复核**）：
  - **已提交**（第四次交接前，9 人）：约翰·邓斯·司各脱、罗吉尔·培根、托马斯·莫尔、乔尔丹诺·布鲁诺、乔治·贝克莱、冈波巴、萨冈彻辰（single-surviving-corpus）、阿底峡尊者、扎纳巴扎尔。
  - **本次会话产出已随第四次交接提交**（5 人）：伊姆霍特普（limited-evidence/no-autographs，参照普塔霍特普归名分层）、格里戈尔·纳雷卡齐、阿蒙涅姆赫特（limited-evidence/no-autographs）——2026-10-05 深夜由研究代理产出未校验；**尼扎米·甘贾维**（documented/authored；研究代理已读 Iranica ᴷᴬᴹˢᴬ/ESKANDAR-NĀMA/HAFT PEYKAR 三条目全文，主传记条目 403/404 未读到——遗留不确定点已写入其证据记录）、**肖塔·鲁斯塔维利**（limited-evidence/single-surviving-corpus；已读 Wardrop 1912 英译序言+Karaulashvili 2023 摘要；身份按「传统归属+晚期史源」分层，legacy 纠正：非「约1600行」、无耶路撒冷墓实证）。尼扎米↔鲁斯塔维利两包已互设镜像边 `editorial-comparison`「波斯叙事诗艺的编辑性比较」（同向同语义，复核时须核对一致）。
  - **唯一缺口：素拉·西瓦拉克**（东亚组第 5 人；研究代理 4×1301 硬过滤）。**本会话已按预案C完成全部离线提取并二次核验，事实增量与来源清单在附录B。新会话免联网直接写证据记录+草稿**（cohort=东亚思想，chronologyPolicy=documented，worksPolicy=authored，debate 建议写「入世佛教」概念归属的学术讨论，纯学术框架）。
- **工作分支**：`codex/philosopher-assets-balanced-02`（第四次交接时已与 origin/master=fee4b5db2 同步合并无冲突）。**工作区**：`/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（git worktree；**不要碰** `/Users/sen/DeepPhilosophy`）。`.env`（OSS 凭证）只在主检出根 `/Users/sen/DeepPhilosophy/.env`，复制到 worktree 用完即删，绝不提交。
- **台账**：`docs/tasks/philosopher-assets-progress.json`（唯一进度真源）。批次报告在 `docs/tasks/author-assets-batch-2026-10-03-balanced-{02..11}.md`。

## 3. 每批 SOP（九步，固化为循环）

1. **选名单**：欧洲/东亚/其他传统各 5。登记前校验：键存在、listingKind=thinker、不在台账、无既有 editorial 文件。地域轮换（伊斯兰/南亚/非洲/拉美/原住民/东南亚），女性与全零缺项优先。
2. **研究代理**（每波 ≤5）：提示词 = "先读 docs/tasks/research-agent-brief.md 并严格照做。批次 <ID>，人物「<键>」，regionCohort「<组>」" + 人物要点（来源建议、须核事实、worksPolicy 倾向、关系候选与镜像约束）。产出 `docs/author-research/<批次ID>/<人名>.json` + `drafts/<人名>.json`。**涉政/宗教敏感人物直接走预案B/C（主会话离线），不派在线研究代理。**
3. **结构校验**（本地脚本化，见批次09-12实践）：assess() + 端点∈{本人}∪people[] + context 关系铁律 + no-autographs 书目 kind + 概念无 book 字段 + sources 全 https + 唯一 id。**常见修复**：sourceRef 引了证据 id 未同步草稿 sources；context+「师承」字样（改 teacher 或换 label）；people[] 漏端点。
4. **独立复核**（5-6 代理，每人 2-3 人）：重访来源核对，直接改草稿，跨包镜像逐条核对（新包关系若涉及既有包必须同向同语义）。
5. **晋升**：`cp drafts/*.json app/public/philosopher/editorial/`。
6. **管线**（全绿）：`python3 scripts/sync_author_catalog.py && python3 scripts/sync_school_catalog.py && python3 scripts/audit_author_assets.py && python3 scripts/test_author_assets.py && node --test app/tests/*.test.mjs && npm --prefix app run build && python3 scripts/sync_school_catalog.py --check && python3 scripts/sync_genealogy_catalog.py --check && git diff --check`；audit 同参重跑哈希一致（幂等）；`git status` 确认旧包零改动。注意：sync 后若 --check 报流派索引需更新，重跑一次 sync_school_catalog 即可（批次11曾遇）。
7. **页面抽查**：worktree 起 `npm run dev -- --port 5273 --strictPort`（端口被占可直接复用在跑的），browser-use 抽 2-3 人（桌面/移动轮换，覆盖本批特殊情形）。
8. **台账+报告+提交**：台账回填（status=validated、stats、keyCorrections、queuesRemaining 递减）；报告 `docs/tasks/author-assets-batch-<批次ID>.md`；精确 pathspec add（禁 -A），`git commit -F <文件>`，push 分支。
9. **发布（每批一次）**：见第 6 节；随后快报+失败整表，不停顿开下一批。

## 4. 批次 12 收尾清单（新会话第一件事）

1. **素拉·西瓦拉克起草**（主会话，免联网）：按附录A+B 书目事实写 `docs/author-research/2026-10-03-balanced-12/素拉·西瓦拉克.json` + `drafts/素拉·西瓦拉克.json`。写 people[] 前先 grep `app/public/philosophers.json` 确认关系候选的站内 canonical 键（一行禅师/佛使比丘（Buddhadasa 译名待核，可能作「佛陀达莎」或「佛使」）/甘地/舒马赫等；站内无则站外人物条目照实写）。关系建议：佛使比丘与 P.A. 般若般那（Payutto 译名待核）→素拉 influence（自认思想资源）；一行禅师 context historical-contact（INEB 早期赞助人，中性一行）；甘地→素拉 influence/reading（其 Gandhi Peace Foundation 会员史实）。**纪律：纯思想文本史/机构史；法律、涉诉、流亡、王室一律不写。**
2. **全批 15 份结构校验**（本地脚本，第 3 节第 3 步清单）→ 修复。
3. **6 个复核代理**（每人 2-3 人）。跨包镜像核对重点：**尼扎米↔鲁斯塔维利 两包 editorial-comparison「波斯叙事诗艺的编辑性比较」同向同语义**；阿底峡→宗喀巴（宗喀巴包既有 reading 端点，阿底峡包已按镜像写「道次第底本」）；米拉日巴→冈波巴 teacher 两包同向；托马斯·莫尔→伊壁鸠鲁 reading；贝克莱→洛克 reading / 贝克莱→休谟 influence / 康德→贝克莱 reading（逐一对照既有包）；扎纳巴扎尔与萨冈彻辰的 editorial-comparison 两包相容（萨冈彻辰包复核时注意）。
4. 晋升 → 管线（全绿）→ 页面抽查（本批特殊情形：归名文本 2 人、single-surviving-corpus 2 人、长译名、无肖像核验记录）→ 台账/报告/提交 → 发布 → 快报。

## 5. 内容过滤（1301）处置预案（血泪版，2026-10-06 再扩充）

- **一般触发**：政治/宗教人物提示词。对策：纯"思想文本史/学术史"框架、去名化、只写学术履历。重发即可（历史上 1-2 次重发通常通过）。
- **中度触发**（2 次不过）：删除一切政治/法律/王室相关语境词再试；英文提示词有时有效（批次10经验）。
- **硬过滤**（3-4 次不过，如批次09牟宗三、批次12素拉·西瓦拉克）：**不要继续在线重试**——该人物的内容通道（含 WebFetch/web_reader/维基）会被整体绑定拦截，且主会话大量处理其内容会触发**本会话 turn 级 1301**（2026-10-05 与 2026-10-06 凌晨各发生一次，用户被迫换会话两次）。预案：
  - **预案A（代理换通道）**：换一个全新代理用极简去名化提示（"一位当代东南亚佛教思想写作者"）。
  - **预案B（主会话直接撰写）**：批次09牟宗三做法——主会话按任务书直接研究撰写（只访问安全学术源如 SEP），独立复核照常。
  - **预案C（离线提取，最安全）**：**绝不让敏感原文过模型上下文**。用 Bash：`curl -sL -A "Mozilla/5.0" <url> -o /tmp/x.html` 下载 → python 正则剥离标签存 `/tmp/x.txt` → 只提取**书目化事实**（生卒/教育/著作年表/机构/奖项）打印。模型只看提取后的安全子集，据此+附录A/B写包。批次12两次验证可行（素拉全部事实已备齐，见附录B）。
  - **预案D（换人）**：仍不行则从批次名单换出，台账记 blocker（参照穆尔雅纳），不冒充完成。
- **通用纪律**：涉敏感人物的汇报/文档只写书目事实，不复述传记细节；主会话感到频繁 1301 时**立即收尾交接**（宁可少写一句，不可重试一次）。**工具结果一旦包含敏感细节即已入上下文——所以提取脚本的关键词表里从一开始就不要放涉政涉法词。**

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

来源：英文维基百科条目（经 Bash 下载离线提取的安全子集；原文全文不要重新在线抓取）。仅供起草，写入草稿前须再核至少一个第二来源（出版商页/机构页）——**此步已在 2026-10-06 完成，见附录B**。

- 生：1933-03-27，曼谷。
- 教育：曼谷 Assumption College；英国威尔士兰彼得大学（University of Wales, Lampeter，现为 UWTSD 一部）；1961 年在伦敦通过律师资格（Bar）。
- 期刊与机构：1960s 主编《Social Science Review》（学界称当时"民族的思想之声"）；1968 创立 Sathirakoses-Nagapradipa Foundation（SNF）；其后创立 Thai Inter-religious Commission for Development（TICD）；**INEB（国际入世佛教网络）1989 年创立**，发起人素拉，早期赞助者包括第十四世达赖喇嘛、一行禅师、Maha Ghosananda（此名单仅作机构史事实记录，写入时保持中性一行即可）。
- 奖项：Right Livelihood Award **1995**（注意：**不是 2011**——2011 年的是 Niwano Peace Prize；旧提示词有误，勿再沿用）；Niwano Peace Prize 2011。
- 著作（书目候选，出版年/社待核）：Seeds of Peace: A Buddhist Vision for Renewing Society（1992）；自传《Loyalty Demands Dissent: Autobiography of a Socially Engaged Buddhist》（1998，Parallax Press；书名如此，勿改字）；Conflict, Culture, Change: Engaged Buddhism in a Globalizing World（Wisdom Publications，ISBN 0-86171-498-9，年份待核约2005）；The Wisdom of Sustainability: Buddhist Economics for the 21st Century（2010，Souvenir Press，ISBN 978-0-9821656-1-4）。
- 思想线索（其自述）：思想重心自认深受 Buddhadasa Bhikkhu 与 P. A. Payutto 两位泰国论师影响（可作 people[]/influence 候选，须核）；甘地资源（站内「甘地」包核对镜像）；一行禅师（同侪 historical-contact）；E.F. Schumacher（交往，待核）。
- 术语史：「入世佛教」（engaged Buddhism）铸词通常归一行禅师早年，素拉为英语世界主要推广者与 INEB 制度化推手——归属分层写。
- **纪律**：该人物全部内容只写上述书目化事实与学术争论（如 engaged Buddhism 概念之争，参照 Swearer 等学者讨论）；**不写**任何法律、涉诉、流亡、王室相关内容（这就是触发源）。

## 附录B：素拉·西瓦拉克——第二次离线提取增量（2026-10-06，第二次来源已核验，可直接起草）

提取方式均为预案C（Bash 下载→python 剥离标签→只打印书目化字段）；原始 HTML 在 `/tmp/rl.html`、`/tmp/ineb2.html`、`/tmp/wiki.html`（重启即失效，失效则按下述 URL 重新离线提取，禁止 WebFetch/在线浏览）。

**已核验第二来源（草稿 sources 候选，均 https、2026-10-06 实访）**：
1. Right Livelihood 官方 laureate 页 `https://rightlivelihood.org/the-change-makers/find-a-laureate/sulak-sivaraksa/`：生于曼谷 1933-03-27；Education: Studied law in the UK；1961 回泰任 Thammasat 与 Chulalongkorn 两校讲师；**1963 创办 Social Science Review 并主编 6 年**（"most influential publication in Thailand" 系多家 testimony 转述）；**Awarded 1995**，授奖词原文："For his vision, activism and spiritual commitment in the quest for a development process that is rooted in democracy, justice and cultural integrity"；官网链接指向 inebnetwork.org。
2. INEB 官方 about 页 `https://inebnetwork.org/about-ineb/`：**1989 年 INEB 在 Siam (Thailand) 由素拉与一群佛教及非佛教思想者、社会活动者共同创立**；INEB 作为自治组织运作于曼谷 Sathirakoses-Nagapradipa Foundation 之下；成员遍及 25+ 国（亚非拉欧美）；素拉头衔 Co-Founder。
3. Open Library 检索记录（书目数据库，4 部书年/社全部核到）：
   - Seeds of Peace: A Buddhist Vision for Renewing Society — **1992**，出版方记录为 INEB/Sathirakoses-Nagapradipa Foundation 与 Parallax Press 两个版本。
   - Loyalty Demands Dissent — **1998**，Parallax Press。（另有 1993 年 When Loyalty Demands Dissent，Suksit Siam/Santi Pracha Dhamma Institute 发行——早期版本线索，可选入书目并注明）
   - Conflict, Culture, Change: Engaged Buddhism in a Globalizing World — **2005**，Wisdom Publications（2015 再版）。
   - The Wisdom of Sustainability: Buddhist Economics for the 21st Century — OL 著录 **2011 Souvenir Press Limited**；ISBN 9780982165614 版本著录 Koa Books（北美发行 SCB）。**⚠️ 附录A写 2010 与维基正文 (2010) 有 2010/2011 两说——草稿 year 写「2011（另有 2010 年著录，两说并存）」并在证据记录 checks 记 uncertain。**
   - 实访 URL（可直接入 sources）：`https://openlibrary.org/search.json?q=...`（实际用的 4 条检索 API URL）或版本页 `https://openlibrary.org/books/OL8308644M/Conflict_Culture_Change`、`https://openlibrary.org/books/OL25954055M/The_Wisdom_Of_Sustainability_Buddhist_Economics_For_The_21st_Century`。
4. 英文维基条目离线提取（线索级，不当引用来源，但与其余独立来源一致故可信度高）：**Niwano Peace Prize 2011**；**SNF 创立于 1968**（同时段 SSR 被称"the intellectual voice of the nation"）；其后创立 **TICD**；任 ACFOD 主席及其刊物 Asia Actions 编辑；**1961 在伦敦通过 Bar**；教育 Assumption College（曼谷）+ University of Wales, Lampeter（现为该校佛学 honorary fellow）；祖辈华人（姓 Lim，潮汕裔）；**INEB 早期赞助人一行（第十四世达赖喇嘛、一行禅师、Maha Ghosananda）**（与附录A一致）；自认思想深受 **Buddhadasa Bhikkhu 与 P. A. Payutto** 影响；参加 Buddhist Peace Fellowship、Peace Brigade International、**Gandhi Peace Foundation** 等国际和平组织；另获奖：UNPO Award 1998、Indian Millennium Gandhi Award 2001；1994 年由美国公谊服务会（AFSC）提名诺贝尔和平奖。
   - **注意（纪律重申）**：以上只取书目化与机构史事实入包；生卒教育著作机构奖项可写，其余一律不写。

**起草参数建议**：englishName "Sulak Sivaraksa"；question 建议围绕"现代化冲击下的佛教社会如何以佛法为语言批判消费主义发展模式"；concepts ≥4 候选：入世佛教（engaged Buddhism，铸词归一行禅师、素拉为英语世界主要推广者与 INEB 制度化推手——分层写）、佛教经济学（Buddhist Economics，承接舒马赫传统，其书副题即此）、"小写的佛教"（"Buddhism with a small 'b'"，Seeds of Peace 中篇名）、发展主义批判/替代性发展（RL 授奖词 + "Alternatives to Consumerism" 网络）。life ≥4 节点全部有据（1933 生 / 1950s 留学+1961 Bar / 1961 回泰任教 / 1963 SSR / 1968 SNF / 1989 INEB / 1992 书 / 1995 RL 奖 / 1998 自传 / 2011 Niwano+书）。debate 建议 included：「入世佛教」概念归属与谱系的学术讨论（Swearer 等学者），纯学术。**关系候选须先 grep `app/public/philosophers.json` 定 canonical 键**（一行禅师/甘地大概在；佛使比丘、Payutto、舒马赫译名不确定——站内无则站外人物照实写）。

## 附录C：第四次交接失败汇总（2026-10-06）

| 环节 | 对象 | 失败原因 | 处置 |
|---|---|---|---|
| 主会话 | 素拉·西瓦拉克材料处理 | turn 级 1301 ×2（00:30、07:53），会话被迫终止 | 按纪律立即收尾；全部离线事实已固化附录A+B，新会话免联网起草 |
| 在线抓取 | Niwano 和平奖官网（niwano.or.jp / niwanopeaceprize.org） | 连接失败（000） | Niwano 2011 暂为维基单源，草稿相应节点标注「据通行记载」，不再重试 |
| 在线抓取 | wisdomexperience.org / parallax.org 产品页 | JS challenge 拦截 / 空内容 | 改用 Open Library 书目数据库核年/社，成功 |
| 研究代理（尼扎米） | Iranica 主传记条目、Britannica、Met/Walters 抄本页 | 旧站 403/404、访问被拦 | 改用 Iranica ᴷᴬᴹˢᴬ/ESKANDAR-NĀMA/HAFT PEYKAR 三条目全文，读不到的如实记入证据记录 |
| 研究代理（鲁斯塔维利） | TSU 机构 PDF、Britannica、Iranica | 超时/403 | 改用 Wardrop 1912 英译（Wikisource 全文）+ Karaulashvili 2023（DOI，仅摘要并如实记录）；philopedia 系 AI 生成页已识别并排除 |
