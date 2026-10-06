# PhiAgent O7-B RP2 — Independent Audit & Test Truth Closure

> BASE_SHA = d4e97d10a（RP1 PATCH_REQUIRED 裁定点）
> O7B_RP2_GATE_SHA = 本报告 commit
> RP1_RUNTIME_DATA_HASH = bf7ad52559f32a791d1cd5ed9030c6a0ee4cb93c5f009346a522949d6e2dc543
> RUNTIME_DATA_HASH_CHANGED = false（独立审计未发现真实数据错误）

## 1. 独立语义审计器（§2-§5）

新增 `backend/tools/dp_biblio_audit.py`——与生产 extractor **零共享**:
不 import `RE_TRANSLATOR/RE_PUBLISHER/RE_ISBN/extract_front_matter/_field_from_found`
（T1 用 AST 静态断言），自建逐字符 token 边界解析:

```text
translator  : 手工扫描「译」前汉字名; 「译」后紧跟 文/本/版/丛/书/社 → 词成分非职责标记;
              名与「译」间允许至多一个空白（含全角）; 名不得来自出版社 token
publisher   : 独立出版社 token 归并（后缀扫描, 非共享 regex）
isbn        : span 含 ISBN 标识且数字前缀匹配
pub_year    : 支持类 {EDITION, CIP_BIBLIOGRAPHIC} 与忽略类 {PRINTING, CIP_REGISTRATION}
              分离输出 supporting/ignored/rejected, 不再用单一标签概括混合证据
original_title: 「书名原文」陈述
```

每行输出 `audit_rule_id / audit_reason / supporting_spans / rejected_spans`。

**审计器自身也经历了一次真实调试**（如实披露）: 首跑对
`卫茂平　译`/`张竹明　译`/`王柯平　译`（名与译之间全角空格）误判不支持——
这是**审计器解析缺口**而非数据错误（span 是合法责任陈述）, 修审计器而非改数据。
这也正说明独立审计器与生产 extractor 行为确实不同源。

最终: **22/22 verified 字段独立审计通过, SEMANTICALLY_UNSUPPORTED=0**,
`AUDIT_IMPORTS_PRODUCTION_EXTRACTOR_RULES=0`。

### Independence Sentinel（§4）

- `translator=上海, evidence=[上海译文出版社 ×2]` → **false**（T2）
- `translator=刘继, evidence=[刘继译, 刘继 译]` → **true**（T3）

## 2. 合成 Multi-Edition 实体证明（§6-§7/§11）

R10 重写为真合成: evaluation-only 构造 `work-same + ed-A/ds-A + ed-B/ds-B`
（不同出版社/年份）, 断言 **恰好 2 条记录、无覆盖无合并、edition/source ID 互异**——
含非空转断言 `len(records_for_same_work) == 2`（T9-T11）。

Work identity 边界（§7）: 同 author+title → 同 work_id; edition 元数据变化 →
work_id 不变（T12）。局限如实:

```text
WORK_IDENTITY_CURRENTLY_TITLE_AUTHOR_DERIVED = true
CROSS_TITLE_WORK_RECONCILIATION = NOT_IMPLEMENTED
```

## 3. False-Green 清除（§9-§10）

- R9 的 `assert ... or True` 永真行已删除, 换成三条真行为断言:
  ① CIP=2019 + 版次=2019 + 印刷=2020 → selected=2019 无冲突（印刷年不制造冲突）;
  ② 仅印刷年 → 不 verify; ③ 仅核字年 → 不 verify（T7/T8 + R9 内嵌）。
- 静态永真扫描（T14）: `assert X or True` / `if False` / `assert True` 模式
  对 O7-B 测试文件零命中（顺带清掉 R5 里一处 `if False else` 残迹）。

## 4. 生产零改动证明

```text
PRODUCTION_METADATA_LOGIC_CHANGED = false   （dp_biblio_build.py 本轮零改动）
ROUTES_CHANGED = false                      （routes 相对 686973478 diff=0, T17）
SCHEMA_CHANGED = false / PILOT_SELECTION_CHANGED = false
RUNTIME_DATA_HASH_CHANGED = false           （T: hash 锁定 RP1 冻结值 bf7ad525…）
SYSTEM_PROMPT/FINAL_VALIDATOR/QUOTE_BOUND/scholarly policy diff = 0（R17）
```

## 5. Clean Checkout（§13）

runtime data 未变 → 按任务书只跑一次 `dp_biblio_cleancheck.py <RP2_GATE>`:
metadata 可见 / 非 pilot 零改动 / 确定性重建 hash 相等（T16）。

## 6. Tests

T1-T17 + 原 R 套件修正, 共 47 项（test_o7b_bibliographic_metadata.py）。
全量: **541 passed / FAILED=0 / SKIPPED=0**。

## 7. RP1 审计局限如实记录（§12）

> RP1 semantic audit covered 100% fields but reused production extraction
> regex for some field types, therefore coverage was complete but
> independence was not. RP2 replaces this with independent
> evidence-semantic validation.（不改写 RP1 历史。）
