# 哲学家资料资产标准 v1

目标是让人物专题具有可追溯的内容。页面模块能渲染、字数够长、存在百科链接，都不等于内容经过核验。

## 数据来源与职责

- `app/public/philosophers.json`：唯一人物目录，保留既有标识和链接。
- `app/public/philosopher/editorial/{原有姓名}.json`：按来源编写的人物资料包，可单独审读和扩充。
- `app/public/philosopher/data/{原有姓名}.json`：页面直接读取的汇总结果，由 `scripts/sync_author_catalog.py` 合成。已编写的专题字段优先，不能被流派摘录重新覆盖。
- `docs/author-assets-audit.json`：每个人物的覆盖、缺项及审核状态；生成命令为 `python scripts/audit_author_assets.py`。
- `docs/author-assets-baseline-2026-10-03.json`：本轮开始前的覆盖快照，不能用后来的数据重写。

## 一份可供上线审读的资料包

1. 身份与概述：身份、年代、核心问题、思想背景、主要贡献及影响。概述至少三个相互衔接的段落。
2. 思想发展：通常至少四个有出处的节点，区分出生、讲授、写作、出版及身后编辑。史料不足者采用 `limited-evidence`，解释证据局限，不编造精确日期。
3. 核心概念：至少四项，说明术语、含义、对应著述和容易产生的误解。不能仅因一段流派释义提到某人，就把该概念归为此人的原创。
4. 著述：通常至少三项，记录原题、年代及文献性质。无亲笔著作者标明 `no-autographs`，区分本人的作品、弟子记录、托名材料和后人的研究。只留单一文献传统者说明原因。
5. 关系：至少两位有材料支持的人物。师承、文本阅读、接受、批判分别记录；不能把时间上不可能相见的人连成师徒。
6. 阅读路径：至少两个有具体著述或篇章的起点，说明先读什么、关注什么问题。
7. 争议评估：记录 `included`、`not-required` 或 `insufficient-evidence`。有证据时讨论学说争论、文本问题或政治经历；不为凑模块添加政治污点。区分史实、解释与评价。
8. 来源：至少两项适当的学术或原典来源。每个时间节点、概念、书目、人物关系和阅读路径带 `sourceRefs`；概述与争议也必须对应来源。来源附查阅日期、类型及使用范围。

## 来源阅读元数据与门禁（2026-10-12 起强制）

每个来源至少填写 `id`、`title`、`url`（https）、`type`、`accessedAt`、`accessScope`，并以 `readScope` 或 `coverage` 说明实际阅读范围。`accessScope` 使用既有枚举：

| 值 | 含义 | 能支撑什么 |
|---|---|---|
| `full-text` | 全文读毕 | 正文断言 |
| `partial-text` | 读了正文相关章节/段落 | 正文断言（以读到的部分为限） |
| `abstract-or-catalog` | 仅摘要、编目或馆藏著录 | 仅书目题名/版本/年代等编目事实；不得放入 life/concepts/people/relations/readingRoutes/概述/争议的 `sourceRefs` |
| `search-summary` | 仅检索摘要 | 任何正文位置都不支撑；只能作发现线索 |
| `unread` | 未读（访问失败须说明） | 任何正文位置都不支撑 |

合格示例：

```json
{
  "id": "sep",
  "title": "Stanford Encyclopedia of Philosophy: X",
  "url": "https://plato.stanford.edu/entries/x/",
  "type": "scholarly-encyclopedia",
  "accessedAt": "2026-10-12",
  "accessScope": "partial-text",
  "readScope": "读了 §1–§3（生平与学说），§4 伦理学部分未读；支持生卒、主要著作与学说定位"
}
```

门禁规则（`scripts/check_author_source_evidence.py`，命令入口、逐人检查、全量审计与编译状态同此一规则）：

- **资格按包判定，不按字段是否已填判定**：基线之后新建的包、内容被修订过的基线包、本轮授权修复名单中的包一律进入门禁；只有字节级未变、能通过锁文件 `frozenEditorialHashes` 摘要验证的历史基线包豁免，且明确记为「历史基线兼容」。锁文件缺失或不可读时报错，不自动全免。
- 普通维基百科（wikipedia.org）按本项目标准只是发现线索：即使读了全文也不得标为可读正文来源，不得出现在任何 `sourceRefs` 中支撑断言。经校勘与身份确认的原典转录（如 Wikisource，type `primary-text-transcription`）另行判断，不与普通百科混同。
- 官方域名、正规出版社、SEP/IEP 网址不自动等于已读；`accessedAt` 与 `accessScope` 记录真实阅读事实，不伪造、不用本次日期替代历史阅读事实。
- 研究证据记录须含真实阅读范围、对应 source ID、断言或字段、核对结论及定位；`confirmed/corrected/inferred` 结论不得引用 `search-summary`、`unread`、线索级来源；唯一例外是字段限于书目（`profile.bibliography`）时，可用 `abstract-or-catalog` 支撑题名/版本/年份类结论。
- 门禁失败的包在索引中标 `needs-review`，正文与路由保持可用；不以删字段、换 URL 或改标签方式恢复数字。

## 质量状态

- `source-backed`：按声明来源编写，逐项来源和结构检查通过，允许进入上线审读。
- `needs-review`：旧简介、自动整理的流派材料，或尚未达到上述标准的资料。完整字段不自动升级。
- `identity-unresolved`：身份尚未确认，不能用模板补写成确定人物。
- `context-material`：历史人物、神话、集体或文本传统，使用适合其性质的资料标准。

这里的审核不代表外部同行评审。学术分歧和史料的不确定性必须保留；缺少争议不构成缺陷，缺少出处与对争议是否适用的判断才构成缺项。

## 维护约束

不得更换公共文件路径、移除旧译名入口或丢失站内书籍关联。新增内容先写人物资料包，再合成页面数据、运行审计与构建。完整性检查不得把不明身份、缺少文献或未核实关系默认为通过。
