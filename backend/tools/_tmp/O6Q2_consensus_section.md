## 10. O7 方向共识纪要（与 Reviewer 三轮设计基调讨论）

> DESIGN CONSENSUS ONLY ｜ NO O7 IMPLEMENTATION ｜ NO PRODUCTION CHANGE ｜ NO GATE EFFECT

定位: O7 = Scholarly Research Agent（哲学研究型 Agent——研究对象是原典/论证/解释史/学术争议;
默认知识组织方式 = 学术研究式而非百科词条式）。

GPT-5.6 Sol 正式裁定（2026-09-05, O6-Q2 gate 进行中讨论）:
1. 路线: Q2 先收可靠性门（不动）→ O7 独立主轴: O7-A 规范+评审器 → O7-B 版本/译者/locator 元数据
   → O7-C 二手文献检索 → O7-D 二手语料规模化 → O7-E Scholarly Quality Gate（B/C 可部分并行;
   metadata-first, 禁止 prompt-first——工具不存在就先写"必须引两个学者"只会逼出伪造）。
2. 五维学术 rubric（各 0-4, evaluation-only）: TEXTUAL_GROUNDING / ARGUMENT_RECONSTRUCTION /
   INTERPRETIVE_PLURALITY / HISTORICAL_DISCIPLINE / LITERATURE_ORIENTATION; 深学术问题不允许单项 <2;
   六类硬 flag 与分数分离: FABRICATED_BIBLIOGRAPHY / FABRICATED_SCHOLAR_ATTRIBUTION /
   PRIMARY_TEXT_MISREPRESENTATION / MAJOR_ANACHRONISM / FALSE_EXACT_QUOTE / LITERATURE_ACCESS_OVERCLAIM。
3. 评审结构: Runtime ≠ judge; Independent LLM Judge（测量仪器）→ GPT-5.6 Sol（最终裁决; 100% 低分/疑似
   伪造复核 + 20% 随机 PASS 抽审）; judge 输入 = 问题+回答+证据 digest+书目记录+persona+任务类别。
4. 书目元数据: Tier1 版权页/扫描件自身 > Tier2 国图/CALIS/出版社目录 > Tier3 WorldCat/Crossref >
   Tier4 豆瓣（仅发现）; 记录带 value/source_type/source_locator/confidence/verified;
   WORK_LOCATOR_SCHEME 按传统（Stephanus/Bekker/KANT_AB/Akademia/work+§…）;
   CANONICAL 与 EDITION_SPECIFIC locator 分开; 精度阶梯 canonical→edition page→节/格言→章→书。
5. 二手文献: 存在性 = 检索命中记录; access_level 四态 METADATA_ONLY/ABSTRACT_AVAILABLE/
   FULL_TEXT_AVAILABLE/FULL_TEXT_READ; LITERATURE_ACCESS_HONESTY; FABRICATED_BIBLIOGRAPHIC_METADATA=0。
6. 产品原则: "缺少学术装置, 比伪造学术装置更专业"; 降引用粒度而不伪造精度, 降精度而不拒答整篇
   （预期反而降低 SAFE_REJECT）; "争议 ≥2 解读"仅在问题真涉及时启用（非万能模板）。
7. SCHOLARLY_CLAIM_LEDGER: evaluation-only（ObligationLedger 不复活）。
8. O7-A 交付物: Scholarly Contract（七纪律: textual/argument/interpretive plurality/historical/
   bibliographic honesty/literature access honesty/terminological）+ evaluation-only judge + 3 seed
   （S1 康德开放学术导航 / S2 先天综合判断论证重构 / S3 物自身解释争议）+ 5-10 calibration;
   PRODUCTION_POLICY/TOOLS/RUNTIME/CORPUS_CHANGED = false。
9. 纪律: O7 沿用 BASE_SHA/CODE_SHA/QUALITY_GATE_SHA/回执循环, gate 类型化
   （SPECIFICATION/DATA/CAPABILITY/CORPUS/SCHOLARLY_QUALITY_GATE_SHA）; Reviewer 不变。
10. 时序: Q2 PASS 后以其 accepted SHA 为 O7-A 干净 BASE; 在此之前不下 O7-A task book。
