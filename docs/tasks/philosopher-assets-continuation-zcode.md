# 哲学家资料资产扩充 · 续作任务书（交接 zcode 新会话）

交接日期：2026-10-07 深夜（**第十五次交接**：批次 02-**28** 已上线（**424** 份 source-backed）；批次 **29 进行中**（丹尼特 reviewed、拉姆齐 drafted 待复核、利奥波德源锁定 SEP环境伦理+基金会+OL；队列纯剩余 228）。阻断待人工 2+10：**李达**（两次1301，第1页已核事实存 checkpoints/李达.json progressFacts——汪信砚光明日报文 rmlt 494796 可作来源，第2页晚年段触发过滤）与**阿布·穆斯林·阿特-图尔基**（nisya 身份裁决：主会话主张按呼罗珊的阿布·穆斯林立包，并行核验主张 uncertain；复核稿在 drafts/ 供裁决）。交接对象：zcode + GLM 5.3 新会话（本文件为唯一权威交接入口）。

**本日要点（2026-10-07 会话）**：①批次 27/28 双批聚合发布（27=12人 source-backed，28=7人；audit 405→424）；②复核代理曾越权重写 353 既有包，已回滚——reviewer-brief-27.md 已加硬禁令（只许写两份许可文件、bash 重定向白名单、完工 git status 自查）；③两例站内虚构身份被识破并整体重写（达维德·阿纳赫特=6世纪亚美尼亚新柏拉图主义者、阿布·穆斯林=呼罗珊的阿布·穆斯林），接手者警惕：legacy bio 的当代学者身份+西方书名组合是高危信号；④SEP 谢林复兴节之 Matthews 系 Bruce Matthews 非弗雷亚·马修斯（同姓异人），引用该节者注意；⑤聚合脚本 backend/tools/_tmp/aggregate_27_28.sh 可改造复用；⑥并行会话曾在同 worktree 工作（批次27五人），其文件已并入本批提交；⑦GitHub LFS 曾 502（philosophers.json 上传），等待重试即可恢复。

前序任务书：`docs/tasks/philosopher-assets-completion-zcode-glm53.md`（原始标准，仍有效）；本文件是其执行期的**进度快照与固化 SOP**，冲突处以本文件为准。

## 0. 用户新节奏（2026-10-05 指示，优先级最高）

1. **每完成一个批次 → 立即推送上线**（合并 master → CF Pages → OSS 双端核验），不再攒 2-3 批。
2. 上线后**快速汇报**（≤200 字），**不停顿直接开始下一批**。
3. 每次汇报（及每次交接）附**失败汇总整表**（环节/对象/失败原因/处置）。
4. 上下文将满时先落盘检查点。发生 turn 级 1301 时，模型无法保证执行报错后的记录和换项操作，由操作人或外层调度接管，按第 5 节恢复。历史阻断记录不证明人物被永久封禁；不能据此删去人物或应有的史实。

## 1. 可直接复制给新会话的启动指令

> 继续哲学家数据审计补全。先读 AGENTS.md，再运行 `python3 scripts/author_resume_queue.py --limit 1`，只读取其选中对象及对应资料。若已有草稿或正式包，先接续复核、索引或发布核对，不重复研究。研究标准读 `docs/tasks/research-agent-brief.md`；执行策略运行 `python3 scripts/author_resume_queue.py --instructions` 即可取得，不全文载入历史批次和附录。摘要默认首项只是候选检查，不能机械按顺序研究；主调度先核对当前批次与占用情况，再用 `--name "真实姓名"` 逐人接续，保持地域均衡。一次一人，每个阶段落盘检查点。1301 由外层记录并转待人工复核，原请求不自动重发；阻断项不计完成。每批地域均衡，已完成包、冻结批次和肖像停显记录保留，全部质量与来源门槛不变。

## 2. 现状快照（2026-10-07 第十七次交接）

- **进度**：主名单 652 位中 **405 份 source-backed 已上线**（31 原包 + 批次02-26 共 374 新包）。剩余 **250**。10 例阻塞：穆尔雅纳、苏莱曼诺娃、傅佩荣、徐英瑾、周濂、顶果钦哲仁波切、杜达罗娃、雅各布森（讹变 uncertain）、刘小播、伊娃·海勒（1301 个人级）——均按第 5 节记录 checkpoint，待外层/人工复核，非永久封禁。26 身份待核实、59 背景资料未开始。
- **发布状态**：批次 24 已上线（dp-commit=5147e9a8；OSS 上传 54、47 引用全 200、幂等二过 0；editorial-index profiles=375；台账 release 有证据）。
- **批次 22 结果**：15/15 source-backed（奥尔特加/乌纳穆诺/伊利亚德/麦克卢汉/格巴拉；丁文江/陈鼓应/张祥龙/张岱年/仁钦·乔玛；贝萨里翁/普拉努德斯/马马尔达什维利/博斯特罗姆/马修斯）；报告 `docs/tasks/author-assets-batch-2026-10-03-balanced-22.md`。**两大身份纠正**：伊万娜·格巴拉=巴西解放神学家 Ivone Gebara（legacy 克罗地亚条目全无据；台账组别归拉美）；仁钦·乔玛=仁钦桑波 958—1055（非匈牙利藏学家乔玛·山多尔；改键属目录级遗留）。东亚组两轮 1301 → 拆组（3 中文+2 英文通道）通过。批次23 候选建议：欧洲池 泰勒（查「泰勒」键歧义）/科拉科夫斯基/哈维尔(政治敏感走预案B)/密茨凯维奇/海勒/赫格斯特罗姆/马丁-巴罗；东亚池 善导已用，余 陈鼓应用讫→ 富增章成/高清海/李泽厚等先查键；第三组 恰夫恰瓦泽/普沙韦拉（格鲁吉亚）、伊丽莎白公主（波希米亚，1618—1680）、皮尔森/金·斯科特（澳洲原住民）、苏莱曼诺娃（哈萨克）、洛德/科林斯/克伦肖/米利特/费尔斯通（女性池 25）。
- **批次 20 结果**：15/15 source-backed（伊利格瑞/卡特赖特/博登/海尔斯/吉利根；司马穰苴/惠栋/王念孙/李塨/韩炳哲；姆班贝/坦佩尔斯/古铁雷斯/赖特/法尔斯·博尔达）；6 组复核 + 1 组镜像专项；报告 `docs/tasks/author-assets-batch-2026-10-03-balanced-20.md`（含失败汇总整表与遗留项：王念孙卒年两说、惠栋官衔两源相反、拉康/戴震/孙武系既有包可补镜像端点）。重点纠正：法尔斯·博尔达 legacy 整体错误（阿根廷→哥伦比亚 1925—2008，编造著作与伪概念清除）、卡特赖特生于美国（legacy 作英国）、海尔斯 1943、博登卒 2025-07-18、古铁雷斯卒 2024-10-22、坦佩尔斯方济各会；R2 误将 wikipedia 升为正式来源两处已由主会话回退（换 Open Library 源或降级为诚实存疑）——**复核代理任务书已强化（reviewer-brief-20.md）， wikipedia 仍禁作正式来源，复核加源前先查禁引清单**。
- **批次 21 候选建议**（批次20 收尾时筛选，登记前仍须核键/查重）：东亚池约 42（禽滑厘/王引之/段玉裁未收/张祥龙/陈鼓应/丁文江/善导/河上公/富增章成/黄珍奎等）；女性池余约 26（奥德丽·洛德/帕特丽夏·科林斯/金伯利·克伦肖/凯特·米利特/舒拉米斯·费尔斯通/弗吉尼亚·伍尔夫/卡伦·霍妮/玛格丽特·富勒/弗雷亚·马修斯/伊万娜·格巴拉等）；轮换地区稀薄（拜占庭 4：帕拉马斯/贝萨里翁/普莱索/普拉努德斯；格鲁吉亚 3；捷克 帕托契卡；挪威 阿恩·内斯；芬兰 冯·赖特；波兰 英伽登/科拉科夫斯基；南非 戴维·刘易斯-威廉斯；墨西哥 马库伊尔肖奇特尔/特蕾西亚·特埃瓦；秘鲁 梅希亚；哈萨克斯坦 苏莱曼诺娃；印尼/瓦努阿图已用）。**这一段是历史候选记录。是否调度以当前台账、来源可用性和实际错误为准，不按人物姓名预判阻断。**
- **工作分支**：`codex/philosopher-assets-balanced-02`。**工作区**：`/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（git worktree；**不要碰** `/Users/sen/DeepPhilosophy`）。`.env`（OSS 凭证）只在主检出根 `/Users/sen/DeepPhilosophy/.env`，复制到 worktree 用完即删，绝不提交。
- **台账**：`docs/tasks/philosopher-assets-progress.json`（唯一进度真源）。批次报告在 `docs/tasks/author-assets-batch-2026-10-03-balanced-{02..26}.md`。

## 3. 每批 SOP（九步，固化为循环）

1. **选名单**：欧洲/东亚/其他传统各 5。登记前校验：键存在、listingKind=thinker、不在台账、无既有 editorial 文件。地域轮换（伊斯兰/南亚/非洲/拉美/原住民/东南亚），女性与全零缺项优先。
2. **研究代理**（每波 ≤5）：提示词 = "先读 docs/tasks/research-agent-brief.md 并严格照做。批次 <ID>，人物「<键>」，regionCohort「<组>」" + 人物要点（来源建议、须核事实、worksPolicy 倾向、关系候选与镜像约束）。产出 `docs/author-research/<批次ID>/<人名>.json` + `drafts/<人名>.json`。一次只把一位人物的必要上下文交给研究代理；发生 1301 按第 5 节处理，不按人物所属地域或传统删减事实。
3. **结构校验**（本地脚本化，见批次09-12实践）：assess() + 端点∈{本人}∪people[] + context 关系铁律 + no-autographs 书目 kind + 概念无 book 字段 + sources 全 https + 唯一 id。**常见修复**：sourceRef 引了证据 id 未同步草稿 sources；context+「师承」字样（改 teacher 或换 label）；people[] 漏端点（批次12伊姆霍特普被 node 门禁抓漏）。
4. **独立复核**（5-6 代理，每人 2-3 人）：重访来源核对，直接改草稿，跨包镜像逐条核对（新包关系若涉及既有包必须同向同语义）。**来源卫生也是复核项**：不得引用百科线索级来源（wikipedia）与第三方全文镜像（dokumen.pub 一类），发现即改引正式出版页或删除依赖断言（批次12两例）。
5. **晋升**：`cp drafts/*.json app/public/philosopher/editorial/`。
6. **管线**（全绿）：`python3 scripts/sync_author_catalog.py && python3 scripts/sync_school_catalog.py && python3 scripts/audit_author_assets.py && python3 scripts/test_author_assets.py && node --test app/tests/*.test.mjs && npm --prefix app run build && python3 scripts/sync_school_catalog.py --check && python3 scripts/sync_genealogy_catalog.py --check && git diff --check`；audit 同日期重跑哈希一致（幂等）；`git status` 确认旧包零改动。注意：sync 后若 --check 报流派索引需更新，重跑一次 sync_school_catalog 即可（批次11曾遇）。
7. **页面抽查**：worktree 起 `npm run dev -- --port <空闲端口> --strictPort`（5273 常被占用，换 5287 等），抽 2-3 人核 data/editorial JSON 与页面 200（本会话无 browser-use，用 curl + JSON 结构核对；有 browser-use 时按桌面/移动双视口）。
8. **台账+报告+提交**：台账回填（status=validated、stats、validation、keyCorrections；queuesRemaining 递减）；报告 `docs/tasks/author-assets-batch-<批次ID>.md`；精确 pathspec add（禁 -A），`git commit -F <文件>`，push 分支。
9. **发布（每批一次）**：见第 6 节；随后快报+失败整表，不停顿开下一批。

## 4. 批次 21 起步清单（批次 20 已发布）

1. 选名单登记（第 2 节候选建议；键存在、listingKind=thinker、不在台账、无既有 editorial 文件）→ 三个研究代理（每代理 5 人，提示词 = brief + 批次ID `2026-10-03-balanced-21` + 人物要点；要点文件写 `docs/tasks/batch21-assignments.md` 入库）。
2. 结构校验（**前端 node 门禁口径：relation 端点必须出现在本包 people[]**）→ 6 个复核代理（模板 `backend/tools/_tmp/reviewer-brief-20.md`，记得把批次号改 21；**wikipedia 禁作正式来源要写明**）+ 1 组跨包镜像专项。
3. 晋升 → 管线（全绿）→ 页面抽查 → 台账/报告/提交 → 发布（第 6 节）→ 快报+失败整表。
4. 复核完成通知晚到时的教训（批次20 R5）：代理可能在校验/晋升之后才落盘改稿——**晋升前用 diff 确认 drafts 与 editorial 一致、晋升后重跑一次扫描**。

## 5. 1301 阻断恢复

1301 可能来自输入或生成内容的审核。`Turn execution failed` 且 `retryable=false` 表示本轮已终止；不能依靠同一轮模型在报错后自己记录失败并继续。错误也不能证明人物、账户或整条研究通道被永久封禁。

### 单人处理与检查点

一次只处理一位人物。提交网络阅读或生成请求前，先把当前阶段写入 `docs/author-research/<batch>/checkpoints/<人名>.json`。阶段依次为身份核对、来源证据、草稿、复核、校验、发布核对；每完成一阶段先保存成果，再进入下一阶段。研究代理只写自己的证据、草稿和检查点，不改总台账或正式源。

检查点至少含 `name`、`batch`、`stage`、`updatedAt`、`savedFiles`、`nextAction`。`savedFiles` 只列已经存在的文件，文件写入采用临时文件后原子替换。不要只把成果留在对话或尚未结束的流式输出里。

### 外层处置

操作人或可捕获调用失败的调度器承担以下步骤；普通任务提示词不能替代这个控制层：

1. 出现 1301 后停止原样自动重试，保留已有文件，不重置整个批次。
2. 核对失败对象和阶段。记录时间、模型、错误码、request ID、TraceID；原始响应若有 `contentFilter.role/level`，如实记录，没有则记为未知。
3. 将诊断写入该对象检查点，诊断日志不包含 API 密钥、认证头或无关的全文输入。任务协调人使用现有台账允许的 `blocked` 状态和 `blocker` 字段；保留原有 `blocker` 状态记录，不静默重写历史。
4. 若同时有人写总台账，先交协调人合并，不覆盖他人的进度。原对象转待人工复核，下一次单独启动另一位未受阻对象，地域均衡要求仍有效。
5. 已保存草稿接续审读，已有正式包先核对索引和发布记录。阻断、部分完成及仅通过结构校验均不冒充 source-backed 完成。

### 上下文与资料质量

只读当前对象的身份资料、结构要求和实际引用的来源段落。保留真实姓名、文献题名、URL 和原文位置，不把无关历史失败记录及整批旧传记反复加入输入。

不通过改名、编码、同音字或切换语言尝试掩盖请求；不为通过审核删掉应有的政治、宗教或历史事实。必要材料在当前通道无法处理时，标明缺项并交给人工或获准使用的学术研究工具审读，不靠模型记忆补写来源。更换会话用于缩小必要上下文和定位问题，不保证解除审核。

向智谱或 ZCode 支持提交带请求标识的最小合法复现，请其定位输入或输出审核。该通道适合完成的校验、格式整理、目录与索引工作可以继续；无法完成的研究字段保持待复核。

参考：[智谱错误码](https://docs.bigmodel.cn/cn/faq/api-code)、[内容安全说明](https://docs.bigmodel.cn/cn/guide/platform/securityaudit)。

## 6. 发布流程（每批一次）

1. `git fetch origin`；master 有新进则 merge（唯一可能冲突 `app/public/schools/catalog.json`：取 master 为底重跑 sync 双脚本）；`git push origin HEAD:master`。
2. 等 CF Pages 构建（约 3-6 分钟）：`curl -s https://deepphilosophy.top/?v=$(date +%s) | grep -oE 'dp-commit[^>]{0,80}'` 应为新提交短哈希。
3. OSS（凭证 `/Users/sen/DeepPhilosophy/.env` 先 cp 到 worktree，**用完删除**；Python 用 `/Users/sen/DeepPhilosophy/.venv/bin/python`）：
   ```sh
   <venv>/python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.top
   <venv>/python backend/tools/dp_sync_oss_static.py --only=philosophers.json,philosopher/catalog.json,philosopher/data,philosopher/editorial,philosopher/editorial-index.json,philosopher/portrait-audit.json,schools/catalog.json,schools/data,app/assets
   <venv>/python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.top --verify-only   # 44 引用全 200
   ```
   再跑一遍 sync 应需上传 0（幂等）。抽查 OSS JSON 用正确百分号编码。台账 `release` 记证据（提交/URL/时间/上传数/抽查）。
4. **注意**：merge master 后重跑 sync 会再生成一批 `philosopher/data/*.json`（master 的流派数据变动会传播到 profile.schoolLinks）；这是既有管线的正常行为，批次12 遇到 106 份，作为管线输出提交即可，editorial 包不受影响。

## 7. 剩余队列与最终口径

- thinkersToComplete 442（批次14收尾后 427）；identitiesToResolve 26 与 contextToReview 59 未开始——建议主名单 ~250 份后穿插（背景资料需先建独立验收规则，见原任务书 §7）。
- 完成定义不变：不冒充、不降门槛；阻塞如实记录。台账是唯一进度真源。
- 主名单全部完成时写 `docs/author-assets-completion-report.md` 终报（口径见原任务书 §10）。

## 附录A：素拉·西瓦拉克——已离线提取的书目事实线索（2026-10-05）

来源：英文维基条目经 Bash 下载离线提取的安全子集（历史摘录；不得替代对必要事实及原始出处的复核）。

- 生：1933-03-27，曼谷。
- 教育：曼谷 Assumption College；英国威尔士兰彼得大学（University of Wales, Lampeter，现为 UWTSD 一部）；1961 年在伦敦通过律师资格（Bar）。
- 期刊与机构：1963 创办并主编《Social Science Review》；1968 创立 Sathirakoses-Nagapradipa Foundation（SNF）；其后创立 Thai Inter-religious Commission for Development（TICD）；INEB（国际入世佛教网络）1989 年创立，早期赞助人包括一行禅师等。
- 奖项：Right Livelihood Award **1995**（不是 2011）；Niwano Peace Prize 2011。
- 著作：Seeds of Peace（1992）；Loyalty Demands Dissent（1998，Parallax Press，书名勿改字）；Conflict, Culture, Change（2005，Wisdom Publications，ISBN 0-86171-498-9）；The Wisdom of Sustainability（Souvenir Press 2011 著录，另有 2010 著录，两说并存）。
- 术语史：「入世佛教」（engaged Buddhism）铸词通常归一行禅师早年，素拉为英语世界主要推广者与 INEB 制度化推手——归属分层写。
- **纪律**：只写书目化与机构史事实与学术争论（如 engaged Buddhism 概念归属之争）；**不写**任何法律、涉诉、流亡、王室相关内容。

## 附录B：素拉·西瓦拉克——已核验第二来源清单（2026-10-06）

1. `https://rightlivelihood.org/the-change-makers/find-a-laureate/sulak-sivaraksa/`：生 1933-03-27 曼谷；Studied law in the UK；1961 回泰任 Thammasat 与 Chulalongkorn 讲师；1963 创办 Social Science Review 并主编约六年；1995 获奖及授奖词原文。
2. `https://inebnetwork.org/about-ineb/`：1989 年在泰国由素拉与一群佛教及非佛教思想者、社会活动者共同创立；自治运作于曼谷 SNF 之下；成员 25+ 国；Co-Founder。
3. Open Library 版本页：`https://openlibrary.org/books/OL8308644M/Conflict_Culture_Change`、`https://openlibrary.org/books/OL25954055M/The_Wisdom_Of_Sustainability_Buddhist_Economics_For_The_21st_Century`。
- 已发布包：`app/public/philosopher/editorial/素拉·西瓦拉克.json`（2026-10-06 上线，dp-commit=253880e4）。**不得在线抓取该人物任何页面。**

## 附录C：批次12 失败汇总（2026-10-06）

| 环节 | 对象 | 失败原因 | 处置 |
|---|---|---|---|
| 研究代理 | 素拉·西瓦拉克 | 4×1301 硬过滤（另 2 次 turn 级 1301 逼停会话） | 预案C离线提取+主会话免联网起草，事实固化附录A/B |
| 在线抓取 | Niwano 和平奖官网 | 连接失败（000） | 仅存通行记载，标注，不再重试 |
| 在线抓取 | wisdomexperience.org / parallax.org | JS challenge / 空内容 | 改 Open Library 书目数据库 |
| 研究代理（尼扎米） | Iranica 主传记条、Britannica、Met/Walters | 403/404 | 改 Iranica 四条目全文 + JASB 1905，读不到如实记录 |
| 研究代理（鲁斯塔维利） | TSU PDF、Britannica、Iranica、prelacy | 超时/403 | 改 Wardrop 1912 + Karaulashvili 2023（仅摘要，如实记录）；philopedia AI 生成页排除 |
| 研究代理（埃及二人） | UCL 原站、Lichtheim、帕金森 | 403/未读 | 走 Wayback 与 archive.org（Met/Budge/Gunn/Petrie） |
| 复核（来源卫生） | 鲁斯塔维利 | 引用 4 条百科线索级来源 | 全部移除及依赖断言，改正式来源支撑 |
| 复核（来源卫生） | 萨冈彻辰 | elverskog 引第三方全文镜像 | 改引 CUP 正式书目页（实访 200） |
| 复核（证据强度） | 素拉 | 甘地关系无 coverage；INEB coverage 不含一行禅师 | 删甘地条；补 coverage；reviewMethod 更正 |
| 结构校验 | 伊姆霍特普 | 新增批内镜像端点后 people[] 漏列 | node 门禁抓漏，补齐后 44/44 |
| 结构校验 | 布鲁诺、扎纳巴扎尔 | sourceRefs 未同步草稿 sources | 脚本从证据记录补入 |
| 镜像专项 | 阿底峡↔冈波巴 / 尼扎米↔鲁斯塔维利 / 萨冈彻辰↔扎纳巴扎尔 / 伊姆霍特普↔阿蒙涅姆赫特 | 类型对立、方向互反、批内单向 | 逐一统一/补齐，两包逐字一致 |
| 旧包口径 | 大卫·休谟（既有包） | 其 evidenceLimits 称贝克莱—休谟关系未获核实，与新包 influence 条目对立 | 本轮不改既有包（保持零改动不变式），列入批次12报告第5节遗留项，待后续批次统一 |

## 附录C2：批次19 失败汇总（2026-10-06）

| 环节 | 对象 | 失败原因 | 处置 |
|---|---|---|---|
| 会话连续性 | 批次19 复核收尾 | 前会话上下文中断（镜像报告写完后未及晋升/发布） | 新会话接手：核对现状→落实改稿建议→管线→发布，未返工研究/复核 |
| 研究代理 | 艾耶尔包 | Britannica、英国科学院 403 | 改 Encyclopedia.com（Gale）+ archive.org 编目，未读如实记录 |
| 研究代理 | 安瑟伦包 | 拉丁校勘本未直读 | 以 Deane 1903 英译（archive.org 影印）为准并标注 |
| 结构门禁 | 狄尔泰/卡尔纳普两包 | people[] 漏 relation 端点（卡尔纳普、库恩），node 测试拦截 | 补 people[]（existing-catalog 口径）+ 重跑 sync，44/44 |
| 主会话补核 | 大卫·弗里德里希·施特劳斯生卒 | Britannica 403 | 改 Open Library 作者档 OL134023A（书目事实） |
| 来源卫生误报 | archive.org 8 处 | 扫描脚本启发式误标 | 逐一核为编目/前版权期影印（Loeb 1916、Deane 1903），判合规 |
| 旧包口径 | 孙武包 people[孙膑] era | 与 canonical「活动于前4世纪」相悖 | 本轮不改既有包，列入批次19 报告遗留项 |

## 附录C3：批次20 失败汇总（2026-10-06）

| 环节 | 对象 | 失败原因 | 处置 |
|---|---|---|---|
| 复核来源卫生 | 海尔斯/吉利根包 | R2 误将 wikipedia 升为正式来源（简报明令禁止） | 主会话回退：Writing Machines 年份改 Open Library 书目支撑；生月日/研究助理细节降级为诚实存疑；复核任务书已写明禁引清单 |
| 委派质量 | 坦佩尔斯会籍 | 派发提示词误作「圣母圣心会」 | 研究代理按三源纠正为方济各会（OFM） |
| 镜像专项 | 坦佩尔斯↔维雷杜 | 洪通吉两名字符串不一致 | 统一为既有包口径「保林·洪通吉」（含段落内文本） |
| 字符串修正 | 坦佩尔斯草稿 | 首次替换脚本漏数组内段落字符串 | 重写递归后清零并 grep 复验 |
| 会话时序 | R5 复核代理 | 完成通知晚于校验/晋升（改动已赶在 cp 前落盘，未造成不一致） | diff 确认一致；流程教训写入第 4 节（晋升前后各校验一次） |
| 在线抓取 | 卡特赖特（SEP 404/Durham 403）、博登（PhilPapers 403）、海尔斯（encyclopedia.com 404）、古铁雷斯（Britannica 反爬）、法尔斯·博尔达（Cambridge 429/Sage 拒）、韩炳哲（Stanford UP 拦截）、东亚组（清史稿 WebFetch 过滤拒） | 各源不可读 | 均改等价学术源（BBVA/AE/ISEPP/NDPR、讣告与出版社页、Scholars@Duke、Springer OA、CLACSO/Banrep/EPAA、MSB/DNB/LARB、curl 直读），如实记录 |
| canonical 休眠字段 | 坦佩尔斯/法尔斯·博尔达 | philosophers.json 遗留 centuries 错误（「13世纪」「19世纪/20世纪」，sync 不重建、前端不消费） | 按本批核实 era 移除字段，台账记录 |
