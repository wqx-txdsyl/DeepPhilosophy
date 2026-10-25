# 全库逐段审读·并行任务书（B队列）

## 任务目标
与另一进行中的ZCode主校对对话**并行**完成B队列45本书的全库逐段审读循环。

## B队列
`docs/tasks/book-full-proofread-zcode-2026-10-24/queues-parallel-B.json`（45本中大书，
含《汉魏两晋南北朝佛教史》《西方的没落》《人类理解论》《作为意志和表象的世界》等）。
队列已从主队列切分，与主对话A队列**零重叠**，无需协调选书。

## 工作区（重要——必须独立worktree）
- **启动时先建独立worktree**（切勿与主对话共用工作区，books.json/progress等共享文件会冲突）：
  ```
  git -C /Users/sen/DeepPhilosophy worktree add \
    /Users/sen/.codex/worktrees/book-quality-B -b codex/book-quality-zcode-B master
  cd /Users/sen/.codex/worktrees/book-quality-B
  ```
- 之后所有读写在B worktree内进行；共享文件（books.json/progress.json/回执）天然隔离，
  发布push时若与master非快进，先 `git fetch && git merge origin/master` 再推
- 锁owner用 `zcode-proofread-B`（与主对话zcode-proofread锁互斥共库，天然协调发布时序）
- 提交规范：精确pathspec add，禁用 `git add -A`；commit message 用 `git commit -F` 文件方式；
  章节数据变更后 `git push origin HEAD:master`

## 每本书流程（与主对话完全一致）
1. **派实读代理逐字通读**（不可关键词扫描/抽样/机械正则替代），报告落盘
   `docs/tasks/book-full-proofread-zcode-2026-10-24/progress/reading/{bid}.full.json`
   （每条含 ch/block/quote逐字摘抄/issue/proposal修正词串/confidence；禁止指令性proposal）
2. **主校对核定修复**（管线：'应为/箭头/讹作'模式提取 → difflib对齐 → 整段quote替换 →
   通用形近对全章清扫 → 系统性模式清扫如页码嵌入/破折号断裂/署名破折号）。
   **教训**：proposal若为指令性文字（"删除撇号"类）绝不可当替换词；quote含\n时整段quote
   可能与文件不一致，须先核验。每次批量应用后与HEAD核对计数，发现误伤立即checkout重放。
3. **迁注**（如有行内[n]/①标记+注文块）：`backend/tools/dp_note_migrate_auto.py`
   （先dry）+ `dp_note_check.py {bid}` 校验PASS
4. **介绍重写**600—1000字（`backend/tools/dp_intro_lib.set_summary`，validate_summary
   PASS；禁内部词汇；**set_summary已四处同步** detail/books.json/资产）
5. **tags审读**：缺失主题词/张冠李戴/与简介一致；detail文件主键是**bookId**（非id），
   同步时两处都要改（曾两次漏更）
6. **结构收尾**：文硕阁平台页/缺篇目录章整章删除+重编号+meta/detail/books.json的
   chapterCount四处同步；德文/拉丁术语空格变音复原；页码嵌入清扫（排除"第N"合法用例，
   扫后必须与HEAD比对防误伤）
7. **精确pathspec+git commit -F提交**
8. **锁流程发布**：`backend/tools/dp_book_round_coordination.py acquire --owner zcode-proofread-B`
   （**新owner，与主对话锁隔离**）→ `dp_sync_oss_chapters.py` → push → 生产验收
   （`curl deepphilosophy.top/book_detail/{bid}.json` 核对 chapterCount/介绍字数/tags）
   → 回执 `progress/publish-receipt-*.md` → release
9. **每完成一本汇报**：书名、实读章/段、修复数、迁注与简介结果、生产状态、累计进度，
   然后立即继续下一本，中间不停下

## 修文原则
- 修文有据：据通行整理本/宋本/洛布本等校正；无法确证的讹字**保留并登记residuals**，不猜补
- 不重写原意，不删难文与原注清零；公开summary不写内部证据/门禁/批次/计数
- 实体书才可处理页缝脱文：无法复原的整句脱落如实登记（康德先例92处）

## 中断规程
- 用户叫停/额度中断：保存精确书/章/段、文件归属、提交hash与下一动作到
  `progress/zcode-progress.json`（键=bid，含status/note/residuals），报告后停
- 1308/1302额度中断：记具体位置→转主校对亲读→重置后重派代理，不无限重试

## 当前状态参考（启动时主对话）
- 主对话A队列：49/523已读、47/523已发布（回执#1-#19）
- 已登记对书项（与B队列无关，勿处理）：康德三大批判合集92处脱文、小说理论/悲剧的
  诞生索引类、新大西岛待可靠源

## 启动指令（直接粘贴为goal）
/goal 按 docs/tasks/book-full-proofread-zcode-2026-10-24/mission-parallel-B.md 与
queues-parallel-B.json 完成45本B队列全库逐段审读循环：每本书派实读代理逐字通读→
按管线核定修复→迁注→介绍600-1000字重写→tags审读→结构收尾→精确pathspec提交→
acquire锁(zcode-proofread-B)→OSS增量→push→生产验收→回执→release；每完成一本汇报
然后继续，中间不停下
