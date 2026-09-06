# PhiAgent O7-B RP1 — Metadata Integrity, Conflict Semantics & Reproducible Runtime Data

> BASE_SHA = 9aaef1ed3（PATCH_REQUIRED 裁定点）
> CODE_SHA = 686973478（RP1 代码+数据; 确定性修复 47641e540）
> O7B_RP1_DATA_GATE_SHA = 47641e540
> 核心教训（Reviewer）: 「两行 OCR 一致」只能证明提取结果重复出现，
> 不能证明它在语义上就是那个 bibliographic field。

## 1. Kill Case 冻结与修复（RP1 §1-2）

`2c1a4c7d17a4 单向度的人`: 「上海译文出版社」曾被截为「上海译」→ `translator=上海 verified=true`。
真实版权页责任陈述是「刘继译」。

修复为**一般规则**（无 book_id 特判）:

```text
「译」后必须是: 行尾 / 标点 / 空白 / 引号
「译」后不得紧跟: 文 / 本 / 版 / 丛 / 书 / 社
责任者名与「译」之间允许空白（「卫茂平 译」）
```

R1-R4 回归矩阵: kill case 原文、翻译出版社、译文版本说明、译本排印、修订译本、
英汉对照译丛 全部不再产出假 translator; 「刘继译」「卫茂平 译」「涂又光译」正常。
重建后 `单向度的人.translator = null`（刘继 1 行证据 → 正确停留 OCR_CANDIDATE）。

## 2. 冲突模型（RP1 §5-§7, 真实现）

每字段结构: `candidates[](value/evidence/semantic_source_type/n_spans)` +
`selected_value` + `resolution_status ∈ {NO_CONFLICT, CONFLICT_UNRESOLVED, RESOLVED}` +
`resolution_basis`。

规则: **≥2 个 eligible 异值 → CONFLICT_UNRESOLVED → production 字段 null**;
禁止 majority-wins（R8: 甲 5 行 vs 乙 2 行仍冲突置 null）。

实际收益——重建后自动暴露一个此前被静默淹没的真实冲突:

```text
偶像的黄昏 publication_year: CIP_BIBLIOGRAPHIC_YEAR=2019 vs EDITION_YEAR=2020
→ CONFLICT_UNRESOLVED → edition.publication_year = null（R7 断言）
```

## 3. 年份语义分类（RP1 §6）

```text
EDITION_YEAR          「2020年4月第1版」            → 支持 publication_year
CIP_BIBLIOGRAPHIC_YEAR CIP 行尾「…出版社，2020」     → 支持（与版次异值即冲突）
PRINTING_YEAR         「2020年4月第1次印刷」         → 不支持（不同事实）
CIP_REGISTRATION_YEAR 「CIP数据核字（2020）」         → 不支持（登记≠出版）
```

R9 合成验证: 印刷年/核字年不得支持; CIP 2019 vs 版次 2020 → unresolved。

## 4. 国籍 ≠ 原文语种（RP1 §4/§16）

`（德）` 类作者国别标记只进 `author_nationality_hint`（非模型面向, verified=false,
不参与 work.original_language）。`work.original_language` 目前全库 null——本库无
「原文语种/原版语言」类明确语言事实。R5 回归冻结。

## 5. 实体 Identity（RP1 §8）

schema 新增 `work_id`（author+canonical_title 哈希）/ `edition_record_id`（ed-{book_id}）/
`digital_source_id`（ds-{book_id}）。R10 合成+真实双验证: 同 work_id 的多个
edition/source 不得折叠。当前库无已验证同作异版: **REAL_MULTI_EDITION_CASES=0**（如实）。

## 6. 运行时数据入库 + 可复现（RP1 §9-11）

- `backend/data/book_bibliography.json` 成为 **git 跟踪的 production reference data**
  （`git ls-files` = 1, R12）。文件头含 schema_version=o7b-2 / builder_hash /
  source_snapshot_hash / pilot_manifest_hash。
- **Clean checkout 门**（`dp_biblio_cleancheck.py`, 临时 git worktree, 无本机 untracked）:
  metadata 可见 / 非 pilot 零改动 / `CLEAN_CHECKOUT_LOCAL_GENERATION_REQUIRED=false`。
- **确定性重建**: 修复 set 迭代受 PYTHONHASHSEED 影响导致的采样值顺序漂移;
  `REBUILT_RUNTIME_DATA_HASH == TRACKED_RUNTIME_DATA_HASH`
  （bf7ad525…c543, R14 + cleancheck 双验证）。

## 7. 全量语义审计（RP1 §12-13, 取代弱抽样）

`docs/evidence/PHIAGENT_O7B_SEMANTIC_FIELD_AUDIT.json`: **全部 22 个 verified 字段**
（100% 审计率）逐个记录 value/raw spans/semantic class/SUPPORTS_FIELD_SEMANTICS:

| 字段 | 语义类判定 |
|---|---|
| isbn ×7 | span 必须含 ISBN 标识 |
| publisher ×8 | span 匹配 X出版社/出版公司/书馆 形态 |
| translator ×4 | span 整体匹配责任陈述（名+译+边界）且名字==value |
| publication_year ×3 | ≥2 独立证据行属 EDITION/CIP_BIBLIOGRAPHIC 类 |

`SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS = 0`。verified 字段从 25 → 22（-3:
年份语义收紧 + 上海类假象清除; 少几个可以, 错一个不可以）。

## 8. 数值快照（重建后）

```text
PILOT_WORKS=39  TRADITIONS=10
EDITION_IDENTITY: VERIFIED=7 / PARTIAL=5 / UNKNOWN=27
POPULATED_VERIFIED_FIELDS=22  METADATA_CONFLICTS=1（偶像的黄昏 publication_year, 如实暴露）
SILENT_CONFLICT_RESOLUTIONS=0  UNRESOLVED_CONFLICTS_EXPOSED_AS_VERIFIED=0
NATIONALITY_AS_ORIGINAL_LANGUAGE=0
FAKE_TRANSLATORS/PUBLISHERS/YEARS/LOCATORS/PAGES=0（kill case 回归 + 语义审计双保险）
```

## 9. Reviewer Sample Pool（RP1 §14）

| 类型 | 案例 |
|---|---|
| translator positive | 中国哲学简史 涂又光（双行责任陈述 verified） |
| translator publisher-collision negative | 单向度的人「上海译文出版社」（R1 kill case） |
| publication-year semantic case | 单向度的人 2008（CIP+第1版双类一致） |
| conflict case | 偶像的黄昏 2019/2020（CONFLICT_UNRESOLVED→null） |
| UNKNOWN edition | 悲剧的诞生（前部无版权页文本 → 全 null） |
| canonical locator | 尼各马可伦理学 BEKKER（作者门控, 16 hits） |
| OCR candidate | 单向度的人 translator=刘继（单行→未验证） |
| verified ISBN | 谈谈方法 978-7-5535-2100-8 |
| Tier2 catalogue / edition-page-only | **N/A**（本阶段仍无, 不补假样本） |

## 10. 工具暴露与生产冻结

- get_book_detail / get_chapter additive 不变; **冲突字段模型可见值 = null**
  （metadata_status.conflict_fields 列名, 不给竞争候选）。citation_label 零改动（R16）。
- SYSTEM_PROMPT / scholarly policy / final_validator / quote_bound 相对 O7-A BASE
  302f7380a diff=0（R17 硬冻结）; routes 相对 RP1 授权 commit 686973478 diff=0。
- 架构不变量全部保持; 未新增任何 BibliographyController/CitationSufficiencyGate。

## 11. Tests

R1-R17 + gate 硬门 = 34 项（backend/tests/test_o7b_bibliographic_metadata.py 全量重写）。
全量: **526 passed / FAILED=0 / SKIPPED=0**（含 R13 clean-checkout worktree 门、
R14 确定性重建门）。

## 12. Limitations

1. Tier2/3 仍未接入（RP1 范围明确禁止）; 大量字段停留 OCR_CANDIDATE。
2. REAL_MULTI_EDITION_CASES=0（库内无已验证同作异版, 如实）。
3. 原始 EPUB/PDF 源仍未回迁, Tier1 限于已内嵌的版权页/扉页文本。
