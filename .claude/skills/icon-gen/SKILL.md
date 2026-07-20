---
name: icon-gen
description: Icon Generator
---
# Icon Generator

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_EMOJI` = 输入 emoji 字符
- **标记格式**：`[SKIPPED:reason]`

## 前置依赖
- `N/A（已删除，改用 Icon 组件）`、Agnes API Key、Pillow

## 状态初始化
> TodoWrite: 步骤1生成 步骤2验证

## 原子步骤

### 步骤 1：生成
- **动作**：`cd scripts && python gen_icon_from_emoji.py "ARG_EMOJI"`
- **门禁验证（Check）**：`python -c "import os; p='app/dist/icons/ARG_NAME.png'; print('ICON OK' if os.path.exists(p) else '[SKIPPED:GEN_FAILED]')"`
- **补全分支（Remediate）**：重试 2 次。

### 步骤 2：验证
- **动作**：`python -c "from PIL import Image; img=Image.open('app/dist/icons/ARG_NAME.png'); assert img.mode=='RGBA'; print(f'{img.size[0]}x{img.size[1]} RGBA')"`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z
