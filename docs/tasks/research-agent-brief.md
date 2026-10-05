# 研究代理通用任务书（balanced 系列批次）

适用批次：`2026-10-03-balanced-03` 及之后，按本文件 + 人物专属提示执行。本文件与人物提示冲突时以人物提示为准。

## 环境与纪律

- 工作目录：`/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（git worktree）。**绝对不要碰 `/Users/sen/DeepPhilosophy`**。
- 只创建两个新文件（证据记录 + 草稿），**不得修改** `app/public/`、`scripts/` 下任何文件，不得改 `philosophers.json`，不得运行 sync/audit/test。
- JSON 一律 UTF-8、`ensure_ascii=False`、`indent=2`、文件末尾一个换行。

## 第一步：必读文件

1. `docs/author-data-standard.md`（内容标准）
2. `app/public/philosopher/editorial/老子.json`（schema 样例：顶层字段、sources/id、sourceRefs、evidenceLimits、limited-evidence/attributed 政策）
3. `app/public/philosopher/editorial/荀子.json`（更丰富样例）
4. 人物旧数据 `app/public/philosopher/data/<人名>.json`（【未核实】legacy，只当线索，不得照抄为事实；旧 bio/concepts/people 多为流派摘抄产物，逐项判断后才可保留）

## 第二步：联网研究（必须实际查阅，不得凭模型记忆）

- 用 WebSearch 定位、WebFetch 定向阅读**至少 2 个合适学术来源**：优先 SEP（plato.stanford.edu）、IEP（iep.utm.edu）、Encyclopaedia Iranica、Treasury of Lives、大学/学术机构页、可信原典版本（Gutenberg/archive.org 影印/出版页）、学术出版物页面。中文学术来源（如中国哲学书电子化计划 ctext.org 的原典目录）可作辅助。
- 必须核实：身份（姓名/原文名/译名/生卒或活动年代/传统/与站内条目是否重复）、生平节点年份与事件性质（求学/任教/著述/出版/身后编订）、每部著作的原题/年代/文献性质、核心学说是否此人本人论证（具体到著述与篇章）、思想关系的方向与性质（不能把年代不可能相见的人连成师徒，不能把比较阅读写成历史影响）、直接引语的原文位置。
- 维基百科不当引用来源（可找线索）；互相转抄的页面不算独立来源；来源打不开或只读到摘要就**如实记录访问范围**，不得伪造"已查阅"。

## 第三步：证据记录 `<BATCH>/<人名>.json`

路径：`docs/author-research/<batch>/<人名>.json`。结构：

```json
{
  "schemaVersion": 1, "name": "<人名>", "batch": "<batch>", "researchedAt": "<当天日期>",
  "identity": {"verdict": "confirmed|corrected|uncertain", "findings": "...", "legacyIssues": ["旧数据问题..."]},
  "sources": [{"id": "sep", "title": "...", "url": "https://...", "type": "scholarly-encyclopedia", "accessedAt": "<当天>", "readScope": "读了哪些章节、支持哪些断言、未读到的部分"}],
  "checks": [{"field": "profile.life[0].year", "claim": "...", "sourceId": "sep", "locator": "章节/小节/经号", "verdict": "confirmed|corrected|uncertain", "notes": "..."}],
  "uncertainties": ["..."], "portraitNote": "unverified"
}
```

checks 必须覆盖：生卒/era、每个时间节点、每部书目（题名/年代/kind 性质）、每个概念的著作归属、每条人物关系依据、概述与争议中的关键断言。uncertain 的项不得在草稿中写成确定事实。

## 第四步：草稿 `<BATCH>/drafts/<人名>.json`

路径：`docs/author-research/<batch>/drafts/<人名>.json`。硬性要求（与审计脚本一致，任何一条不满足都会被拒）：

- 顶层：`schemaVersion:1`、`name`、`reviewedAt:"<当天>"`、`chronologyPolicy`（documented/limited-evidence）、`worksPolicy`（authored/no-autographs/single-surviving-corpus）、`evidenceLimits`（limited-evidence 或 no-autographs/single-surviving-corpus 时必须非空；其他情况也建议写）、`overviewSourceRefs`、`debateAssessment:{status:"included|not-required|insufficient-evidence",scope:"..."}`、`identity`（仅有据修正时，附 `identitySourceRefs`）、`regionCohort`（人物提示给出）、`batch`、`reviewMethod`
- `profile`：
  - `englishName`、`question`（一个具体问题，不空泛）、`overview`（≥3 段，每段 150–300 字：背景/主张与论证/影响与局限；不用"划时代巨人"式赞词）
  - `sources`（≥2 项：`id`（包内唯一）/`title`/`url`（必须 https）/`type`/`accessedAt`/`coverage`）
  - `life`（≥4 节点；limited-evidence 时 ≥2 个有意义的文本史节点；每项 `year`/`title`/`body`/`sourceRefs`，可加 `tag`；区分生平/讲授/成书/出版/身后编订；叙事性节点注明史料性质）
  - `concepts`（≥4 项：`name`/`original`（适用时）/`definition`/`source`（具体著述与篇章）/`sourceRefs`；**禁止** `book` 字段；`year` 仅在确有对应时间节点时用；不得把整个流派的通用词算作此人原创）
  - `bibliography`（≥3 项；no-autographs/single-surviving-corpus 时 ≥1 项：`title`/`originalTitle`（适用时）/`year`（可为年代范围并注明）/`kind`（authored/coauthored/edited/testimony/posthumous/attributed）/`description`/`sourceRefs`；**no-autographs 时 kind 不得为 authored/coauthored/edited**；同一书的不同译名不算三本书；研究著作不列入传世书目）
  - `people`（≥2 位：`name`/`era`/`eraSource`（editorial-peer/existing-catalog/unspecified）/`role`/`summary`/`sourceRefs`，可加 `entityType`/`evidenceKind`；相关人物优先用站内目录 canonical 名——先查 `app/public/philosophers.json` 的键；站外人物也可列并给出处）
  - `relations`（≥2 条：`from`/`to`/`type`（teacher/influence/reading/context）/`label`/`detail`/`sourceRefs`；**端点必须**等于本人、出现在 people[] 中、或是 `philosophers.json` 的 canonical 键（且不得是"待核实"review 类）；`context` 类型约束：要么 `evidenceKind` 为 `historical-contact`（真实历史接触，含注明叙事性质的传统记载）或 `editorial-comparison`（编辑性比较，label 不得含"师承/师生"），要么 label 必须恰为 `共同思想背景`；史实合作用 historical-contact，系统/文本比较用 editorial-comparison）
  - `readingRoutes`（≥2 条：`title`/`description`（具体篇章与问题顺序；"先读原著再读研究"不合格）/`sourceRefs`/`evidenceKind:"editorial-reading-guide"`）
  - `debate`（status=included 时必须：`title`/`year`/`paragraphs`（≥2 段）/`sourceRefs`；学说争论、文本归属、政治史分别处理，无据不编政治争议；在世人物敏感事实需直接可靠来源）
- 全部中文内容（人名/术语括注原文）；不虚构金句、日期、书目、经历；内容要写出此人独特的问题与论证，避免模板化开头结尾与机械改写词条。

## 返回格式

完成后返回 ≤300 字摘要：身份结论、实际阅读的来源清单、政策选择、对 legacy 数据的关键纠正、遗留不确定点。
