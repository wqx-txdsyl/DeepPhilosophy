# 批次报告：2026-10-09-source-repairs（第一阶段：来源修复）

日期：2026-10-09。执行：ZCode（zcode-main），工作树 `author-quality-zcode-20261009`，分支 `codex/zcode-author-quality-20261009`。

## 交付概览

- 新来源验收门禁落地并可回归：`scripts/check_author_source_evidence.py`（CLI + 作为 `audit_author_assets.py` 的一部分）。八份修复包全部转为「新式包」（来源带 `accessScope`），其余 435 包不受影响。`scripts/test_author_assets.py` 由 11 增至 22 个用例，全绿。
- 七份来源疑点包逐人修复，第八项（维雷杜·维雷杜目录键）完成核实与裁决（未迁移，方案留档）。
- 审计保持基线：source-backed 436 / needs-review 216 / context-material 59 / identity-unresolved 26；node 前端测试 9/9；`npm run build` 通过；school/genealogy check 通过；publish-check 无 LFS 指针。

## 门禁规则（新）

新式包（任一来源带 `accessScope`）强制：
1. `accessScope ∈ {full-text, partial-text, abstract-or-catalog, search-summary, unread}` 且每条来源有实际访问范围说明（readScope/coverage）；
2. 检索摘要（search-summary）与未读（unread）来源不得出现在任何 sourceRefs；类型含 clue/search 或维基百科域名的来源一律按线索层处理，即使误标 full-text 也被拦（`clue-source-marked-readable`）；
3. 摘要/编目（abstract-or-catalog）来源可支撑题名、版次等书目事实；
4. 维基文库等明确性质的原典转录（primary-text-transcription）不算普通维基百科；
5. 每个实读且被引用的来源必须在研究证据记录中有对应条目，且 checks 的 confirmed/corrected/inferred/traditional-count 须有 locator，verdict 枚举区分确认/纠正/推断/传统计数/存疑（uncertain 免 locator）。

## 逐人修复记录（证据路径：`docs/author-research/author-quality-2026-10-09/2026-10-09-source-repairs/<人名>.json`）

1. **谭嗣同**：移除误标 academic-source 的 `leads`（中文维基百科线索）。狱中题壁异文之争改由实读来源支撑：维基文库通行本《獄中題壁》＋梁传录诗自注「蓋念南海也」（并发现梁传本作「投宿」而通行本作「投止」）＋《文摘报》2017-01-17 与湖南在线/华商报 2016 两则报道（孔祥吉《留庵日钞》抄本、黄彰健改诗说及其修正）；两则转述本身文字互有出入，如实并陈。张灏/陈善伟比重之争维持存疑、不转述。SEP §5.1 于 2026-10-09 回访复核。
2. **黑麋鹿**：移除 `wiki`（12 处引用）。替换：Ostler 2001（GPQ，开放获取全文升级）、Howard 1999（AICRJ/eScholarship，1911 年《Catholic Herald》信、1934 声明、Ben Black Elk 晚年证言与学界三分——取代原 wiki 支撑的 Sweeney/Costello/Hilda Neihardt 未读引语）、American History 特稿（黑麋鹿 1931 年回忆女王段落引语）、BBC（1887 金禧演出季背景）、UNL 档案 1931-06-08 奈哈特书信、转译链论文。女王观演具体日期（原 1887-05-11）来源未载已移除；1904 受洗降为通行系年；封圣进程纠正为「2016 更名＋2017 列品」两事。
3. **比尔·尼布利特**：移除 `wiki`（11 处）。OAM 1989、二战补给船做工、设园关键角色、Land Rights 关键证人改由澳大利亚国家肖像馆页承担；1988 NatGeo 纪录片改由 NFSA 档案文章承担；《Kakadu Man》合作与动机改由 Morrissey 全文 Works Cited 与 1989 纪录片对白承担。母系信息、Cape Don、达尔文空袭在场、Ubirr 成年礼年份、向 Davis 破例公开的动机叙述：无实读来源，移除或明注存疑。
4. **仁钦·乔玛**：移除 Rigpa 社区百科。ToL 条目（Alexander Gardner 2011）经 Wayback 2013 快照全文实读，接管全部关键断言：13 岁出家、975 赴印（「奉诏派遣」按 ToL 标注为 later histories）、七十五位以上班智达、85 岁托林会阿底峡（先赞后斥「Rotten translator!」）、弟子名单。改正一处引语误引（归名原话实为「Most of the attributions…invention of later tradition」）。率十名译师、rad ni 变体、「补授胜乐」等无据细节移除。
5. **佩吉·坎芙**：移除仅检索摘要层的 BA 公告线索（403 未读）。FBA 当选改由 USC 官方新闻（2023-08-03，实读）承担：本年度 86 位新院士之一、授奖理由照录；BA 原始公告日期（7 月 21 日）不再写入正文。
6. **马库伊尔肖奇特尔**：移除 403 未读的 Mexicolore 线索。Bierhorst 人物条目与两条书目改由馆藏/出版社著录层支撑（Archive.org 元数据：Stanford UP 1985、ISBN、「Based on an analytic transcription of the codex Cantares mexicanos」；OpenLibrary：同社同年三种卷册记录），写本 codex／分析性转写／英译三卷明确区分；译注正文维持未读不作转述。
7. **卡罗琳·汉弗莱**：移除 gov.uk 首页检索线索。DBE 授勋改由官方 2011 年新年授勋名单 CSV（实读检索）承担，授勋事由按名单原文照录（「Professor of Collaborative Anthropology, University of Cambridge. For services to Scholarship.」）；Clare Hall 页回访复核（Dame 在册、2010 荣休）。
8. **维雷杜·维雷杜**：核实规范名称 Kwasi Wiredu（1931—2022，IEP 标题即含卒年；USF 纪念页回访）。结论：目录键为历史工件；规范中文名「夸西·维雷杜」已是目录别名与 corrections.displayName，前端显示/搜索/SEO/星丛已用规范名，两路径均可达、无 404、无身份混淆。改键迁移需移动公共 editorial 文件，被工作树「不得删除公共路径」规则禁止，本轮不执行；安全迁移六步方案记入证据记录 `migrationPlan`，留待外层操作。

## 未能确认 / 存疑保留（如实）

- 谭嗣同：张灏《Chinese Intellectuals in Crisis》、陈善伟研究内文（借阅受限）；《留庵日钞》原抄本（未影印，二次转述互有出入）。
- 黑麋鹿：女王观演具体日期；1904 受洗年份（教会记录未读）；Sweeney/Costello 论著与 Hilda Neihardt 回忆录。
- 尼布利特：母系信息；Cape Don 与空袭在场细节；Ubirr 成年礼年份；NatGeo 杂志专题页细节。
- 仁钦·乔玛：校订 150 余种/率十名译师之数（已移除）；108 函译本逐函归名。
- 坎芙：BA 原始公告页（403）与 USC Dornsife 详报（403）。
- 马库伊尔肖奇特尔：Bierhorst 三卷正文。
- 汉弗莱：FBA 当选年份。
- 维雷杜：目录键本体（迁移方案留档）。

## 检查与发布

- 管线：guard --check ✓ / sync_author_catalog ✓ / sync_school_catalog ✓ / audit（--date 2026-10-09）✓（436 source-backed 保持）/ test_author_assets 22/22 ✓ / node --test authorContent 9/9 ✓ / npm run build ✓ / sync_school_catalog --check ✓ / sync_genealogy_catalog --check ✓ / git diff --check ✓ / publish-check（无 LFS 指针）✓
- 新门禁作为管线一部分实际运行（audit 内嵌 + CLI 全量扫描 gatedPackets=8，failures={}）。
- 发布：提交于本分支后 `git push origin HEAD:master`（授权发布），CF Pages 由 GitHub 主线触发构建；OSS 同步按需另行执行。

## 用量与限额

Codex 周额度数据本轮不可得，不发明数字；本批实际产出：修复 7 包 + 命名裁决 1 项 + 门禁与回归 1 套。
