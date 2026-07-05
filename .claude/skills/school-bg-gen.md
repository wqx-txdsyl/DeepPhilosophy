# School Background Generator（入口 -> agnes-image.md）

> 此文件为瘦入口，共享逻辑见 `agnes-image.md`。

## 变量
- `ARG_NAME` = 流派名
- `ARG_TYPE` = `school`
- `ARG_DIR` = `schools`
- `ARG_SIZE` = `2560x1440`

## 核心执行协议
同 `agnes-image.md` — 顺序执行，每步带检查-补全-验证闭环。

## 前置依赖
同 `agnes-image.md`，额外依赖 `scripts/gen_school_bg.py`

## 原子步骤（入口）
1. **API Key 校验**：同 agnes-image 步骤 1
2. **生成流派背景**：`cd scripts && python gen_school_bg.py "ARG_NAME"`
3. **文件验证**：同 agnes-image 步骤 3（min_w=1200）
4. **缩略图**：同 agnes-image 步骤 4（400x300）

## 执行报告
格式同 `agnes-image.md`
