# PhiAgent O7-B — Bibliographic Metadata Foundation Report

> PHASE = O7-B — BIBLIOGRAPHIC METADATA FOUNDATION
> BASE_SHA = 9edf34775（任务书落盘）｜CODE_SHA = e373a614b｜O7B_DATA_GATE_SHA = 本报告 commit
> 评价标准: 宁可一个字段是 null，也不要一个"很像学术书目"的假字段。

## 1. Corpus Inventory（如实盘点）

```text
CURRENT_BOOK_COUNT=409
BOOKS_WITH_SOURCE_FILES=2            # 本机仅存导入 checkpoint 内的 2 本 OCR 残留
                                      # （原始 EPUB/PDF 源在换机前 Windows 机器 F:/philosophy，未随迁;
                                      #   另有 data/ai_author/corpus 尼采人格语料 21 个源文件, 属人格库非书库源）
BOOKS_WITH_SCANNED_FRONT_MATTER=117  # 章节 0/前部含扉页/版权页文本（110 含出版社字样, 43 含 ISBN, 24 含完整 CIP 块）
BOOKS_WITH_EXISTING_EDITION_METADATA=0   # 改造前 books.json/book_detail 无任何版本元数据字段
BOOKS_WITH_TRANSLATOR_METADATA=0
BOOKS_WITH_PUBLISHER_METADATA=0
BOOKS_WITH_PUBLICATION_YEAR=0
BOOKS_WITH_PAGE_MAPPING=0
BOOKS_WITH_CANONICAL_LOCATOR=0
```

## 2. Work / Edition / Digital Source 模型

三分离落地于 `backend/data/book_bibliography.json`（schema_version=o7b-1, 构建器
`backend/tools/dp_biblio_build.py` 确定性可重建）:

- **work**: author / canonical_title / original_title? / original_language?（仅 Tier1 双证据才非 null）/ original_publication_year?（无证据 → null）
- **edition**: language / translator[]? / publisher? / publication_year? / isbn? / edition_identity ∈ {VERIFIED, PARTIAL, UNKNOWN}
- **digital_source**: source_type / source_file_ref（章节 JSON 目录, 唯一本地数字源）/ source_hash（章节目录全文件 sha256）/ provenance（导入管线说明）
- **field_provenance**: 每字段 value + source_tier + source_type + source_locator（chapter/line）+ confidence + verified + 原始 evidence spans

## 3. Metadata Source Hierarchy 执行情况

- **Tier 1（本数字源自身的版权页/扉页文本）**: 唯一实际使用的层。抽取范围严格限定为
  标题含「版权/扉页/出版说明/版本」的章节（§序言/导言散文不参与），行 ≤80 字符的版式行。
  **verified 规则: 同值须出现在 ≥2 个独立 (chapter, line) 证据行**（OCR ≠ 事实本身,
  §5）; 单证据 = OCR_CANDIDATE / verified=false。
- **Tier 2/3（国图/CALIS/WorldCat 等）**: 本轮未接入（网络目录核验留给后续批次）——
  如实记 0, 不用 Tier 4 冒充。
- **Tier 4**: 完全未使用。TIER4_ONLY_VERIFIED_FIELDS=0（测试 B2 断言）。

## 4. Conflict / Missingness / Locator

- 冲突模型: 候选值全部保留在 field_provenance.evidence; 本轮未出现 ≥2 证据行的竞争值
  （METADATA_CONFLICTS=0, SILENT_CONFLICT_RESOLUTIONS=0）。同作品不同译本不合并（B5）。
- Missingness: 缺失字段一律 null; 「未知译者/未知出版社/第?页/不详/佚名」占位字符串
  被 B8 测试禁止; 无任何模型记忆回填（出版年/译者/ISBN 全部机械抽取或 null）。
- Locator: 机械证据驱动探测, **canonical scheme 按作者门控**（Stephanus→柏拉图,
  Bekker→亚里士多德, KANT_AB→康德）, 防跨作品偶发数字误报; 命中 ≥3 个不同值才声明可用。
  结果: CANONICAL=1（尼各马可伦理学 BEKKER, 16 distinct hits, 样例 1094a1/1096a5）;
  STRUCTURAL=30（卷篇章/§节号/中国典籍篇名体系——论语 20 篇/孟子 7 篇/孙子 13 篇/庄子内篇 7）;
  EDITION_SPECIFIC=0（无页码映射, 不虚报——B7 禁 EDITION_PAGE）。
- Citation capability: max_verified_granularity 机械计算——CANONICAL_LOCATOR=1,
  SECTION=1, CHAPTER=37, EDITION_PAGE=0, WORK=0。它只描述「系统能验证到哪里」。

## 5. Pilot Manifest（§11/§12/§13）

- **PILOT_WORKS=39 ≥ 30**; TRADITIONS_OR_PERIODS=10 ≥ 5:
  O7A_CALIBRATION / NIETZSCHE_PRIMARY / ANCIENT_GREEK / ANCIENT_ROME / LATE_ANTIQUITY /
  EARLY_MODERN / GERMAN_IDEALISM / NINETEENTH_CENTURY / TWENTIETH_CENTURY / CHINESE_PHILOSOPHY
- 选型理由逐书写入 manifest（代表性 metadata pilot, 非 canon ranking）。
- edition_identity: VERIFIED=8, PARTIAL=4, UNKNOWN=27（accuracy > completeness）。
- POPULATED_VERIFIED_FIELDS=25, VERIFIED_FIELDS_WITH_PROVENANCE_RATE=100%,
  UNSUPPORTED_VERIFIED_FIELDS=0; OCR_CANDIDATE_FIELDS=21（全部 verified=false, 保留候选）。

## 6. Accuracy Sampling Gate（§20, seed=20260906）

- 随机抽 15 records（ids 见 docs/evidence/PHIAGENT_O7B_ACCURACY_SAMPLE.json）,
  其全部 3 个 verified 字段从 source evidence 逐行重验:
  SAMPLED_UNSUPPORTED=0, WRONG_EDITION_BINDINGS=0, SILENT_CONFLICT_RESOLUTIONS=0。
- 追加全量自审（超出任务要求）: 39 书全部 25 个 verified 字段确定性重抽复现 25/25。

## 7. Reviewer Sample Pool（§21）

| 类型 | book_id | 说明 |
|---|---|---|
| Tier1 OCR case | d1986c75d6b2 偶像的黄昏 | CIP 块双行证据 → ISBN 978-7-208-16305-8 / 上海人民出版社 |
| translation case | 32093eed6ff1 中国哲学简史 | 涂又光译（双行证据 verified） |
| original-language case | 17fda3378628 美学理论 | （德）→ de hint |
| UNKNOWN edition case | 29b3de571c12 悲剧的诞生 | 前部无版权页文本 → 全字段 null |
| canonical locator case | e574c8e7f515 尼各马可伦理学 | BEKKER 16 hits |
| OCR candidate ≠ verified | d1986c75d6b2 卫茂平（translator） | 单行证据 → edition 层 null |
| Tier2 catalogue case | —（本轮未接入 Tier2, 如实缺位） |
| edition-page-only case | —（无页码映射数据, 不虚报） |

## 8. Tool Exposure（§14-§17）与兼容

- get_book_detail / get_chapter 返回值 **additive** 新增 `bibliographic_metadata`
  （pilot 39 书; 非 pilot 书无此键, 零行为改动）——B9/B10 断言。
- 模型可见精简视图: work/edition 字段 + citation_capability + verified_fields 名单;
  完整 provenance audit tree 留 backend/data 层（§17 防上下文膨胀）。
- null 语义随附 note: 「字段为 null 表示当前数字源未提供或未通过双重证据核验; 不得臆测补全」。
- **citation_label 语义零改动**（§15, B11 断言）; search_books 未改。

## 9. Production Policy Freeze（§23/§24）

- engine_langgraph / final_validator / quote_bound / agents / agent_runtime /
  evidence_contract 相对 O7-A BASE 302f7380a diff=0（pytest T19 硬冻结）。
- backend/routes 相对 O7-B §14 授权改动落地 commit e373a614b diff=0（T19 更新基线,
  仅因 §14 明文授权 additive 工具暴露; 认知/校验核心不受影响）。
- 架构不变量: ENGINE_COGNITIVE_AUTO_TOOLS=0 等全部保持（未新增任何 Controller/Gate）。

## 10. Tests

- 新增 backend/tests/test_o7b_bibliographic_metadata.py: B1-B12 + gate 硬门（16 tests）。
- 全量: `.venv/bin/python -m pytest backend/tests -q` → **510 passed / FAILED=0 / SKIPPED=0**。
- 旧测试唯一改动 = T19 routes 基线更新（上述 §9 明确授权理由, 非「适应 side effects」）。

## 11. Limitations（如实）

1. 原始 EPUB/PDF 源文件未随迁移（Windows F:/philosophy）→ Tier1 只能用导入时内嵌的
   版权页/扉页文本（117/409 书有）; 物理源回迁后可做更细 OCR 批次。
2. Tier2/3 目录核验未接入 → 大量字段停留在 OCR_CANDIDATE; edition VERIFIED 仅 8。
3. 无页码映射 → EDITION_PAGE 粒度全库不可用（如实为 0）。
4. 修 T19 routes 基线是本阶段唯一的旧测试改动, 已给授权依据。

## 12. O7-C Readiness

- schema/provenance/manifest/工具暴露已就绪; O7-C（二手文献检索, access_level 四态）
  可直接复用 field_provenance 的 tier/verified 模型与 citation_capability 表达。
- 未越权开始 O7-C（O7_C_AUTHORIZED=false）。

## 数据 Gate 绑定（§27/§28）

```text
O7B_DATA_GATE_SHA= <本 commit>
BOOK_UNIVERSE_HASH=298d5e0a30b11da2…
CORPUS_SNAPSHOT_HASH=e5dfe4659ab619c9…
PILOT_MANIFEST_HASH=36132f91d1f455c2…
```
