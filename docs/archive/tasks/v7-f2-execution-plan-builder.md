# V7-F2 Delivery Repair 执行计划（Builder 工作文档）

授权: docs/tasks/PHIAGENT_O7E_V7_F2_DELIVERY_REPAIR_AUTH.md（Reviewer 五原则）
BASE: 482c3f2f8 之后的工作分支（V7-F2 从 HEAD=554495542 起实施）
禁止: 放宽 gate / 追溯翻案 V7 / 动 scholarly pipeline / corpus / judge / ranking / primary retrieval

## 修复项（对应 Reviewer 五原则 4/5）

### ① 逐轮语义 observability（原则 5）
- engine_langgraph.py `_val_history.append` 处: 每轮追加 per-issue 明细
  `issue_details`: [{code, locator(截断 200), evidence_ref}]（bounded, 无正文）
- done 事件 validation.history 已含 _val_history → 自动带入
- o7e_production_calibration.run_case_production: 把 done.validation.history 存入
  run record 新字段 `validation_history`（V7 时缺失即观测缺口, 现已闭合）

### ② repair R1 暂态回归抑制（原则 4）
- REPAIR_SYSTEM_PROTOCOL（engine_langgraph 顶层协议文本）追加机械性减损指令:
  R1 修复优先最小改动——逐字保留未点名段落; 引用/引文改写必须复用已核验 evidence;
  禁止在修复中新增未经检索支持的引用或引文
  （注意: 这是修复行为策略, 不构成「放宽指标」——指标仍 any introduced = fail）
- 可选（若①②后探针仍复现暂态）: 不做, 如实报告

### ③ 指标版本化（原则 3, prospective only）
- run record 新增: `REPAIR_INTRODUCED_PERSISTED_FINGERPRINTS`（terminal 仍存活的
  introduced 指纹数）与 `REPAIR_INTRODUCED_TRANSIENT_FINGERPRINTS`
- 旧字段 REPAIR_CREATES_NEW_FATAL_ERROR 原样保留（V7 语义冻结）
- final gate 不改（V7-F2 不得动 final gate; 新指标仅供 V8+ 预注册使用）

## 回归验收
- 三簇探针（V6-F2 §2 的 5 条 query + 3 READ）不退化
- 全量 pytest @ 确切 CONTENT_HEAD（FULL_TEST_SHA == CONTENT_HEAD）
- 两阶段归档恢复: CONTENT_HEAD → evidence-only ARCHIVE_HEAD（parent==CONTENT_HEAD）
- 证据: docs/evidence/V7_F2_DELIVERY_REPAIR.json（inventory/diff/探针/测试, 全 SHA）

## 回执
新 ChatGPT 会话（原会话已满）, 附交接文档 docs/tasks/PHIAGENT_O7E_V7_F1_R1_HANDOFF.md
+ 本计划 + evidence, 请求审 V7-F2（repair policy 改动 + observability 的合规性）
