# O7-E Model Bakeoff V1 Report（已关闭）

## 结果
| 候选 | Stage A 修复微测(16) | Stage B 发布(8) | 修复收敛 | 判定 |
|---|---|---|---|---|
| deepseek-chat | 0.812 ✅ | 4/8（Round 9 baseline） | 3/7=0.429 | FAIL_REPAIR |
| glm-4-plus | 0.938 ✅ | **7/8 ✅** | 2/3=0.667 | FAIL_REPAIR |
| glm-4-air | 1.000 ✅ | 6/8 ❌ | 4/6=0.667 | FAIL_DELIVERY+REPAIR |
| glm-4.6 | 0.875 ✅ | 4/8 ❌（后补 artifact） | 3/7 | 未过交付门 |

## 学术 judge（NONCANONICAL_DIAGNOSTIC_ONLY）
- 自写简化 judge SYS，非 O7-A canonical contract；evidence 截断 1000 字。
- 诊断值: glm-4-plus 2.767/2 fatal；glm-4-air 2.423/4 fatal。不作 canonical 证据。
- glm-4-plus 在学术 judge 前已因机械修复门淘汰（2/3<0.80），无翻盘资格。

## 结论
CURRENT_4_MODEL_POOL = NO_QUALIFIED_MODEL。
候选池本身过时: deepseek-chat 已被官方淘汰（2026-07-24 起 v4 系取代）。
方向 = Bakeoff V2（deepseek-v4-pro/flash + general-API glm-5.3 系）。
