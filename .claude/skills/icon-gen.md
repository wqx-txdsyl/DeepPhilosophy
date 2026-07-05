# Icon Generator

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败则重试最多 2 次，仍失败标记并继续。

## 状态初始化
> 执行前必须先调用 `TodoWrite`：
- [ ] 步骤 1：emoji -> AI 分析
- [ ] 步骤 2：生成透明背景图标
- [ ] 步骤 3：文件验证

## 原子步骤

### 步骤 1：生成
- **动作**：`cd scripts && python gen_icon_from_emoji.py "ARG_EMOJI"`
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/dist/icons/ARG_NAME.png'); print('ICON OK')"`
- **补全分支（Remediate）**：失败 -> 检查 API Key，重试 2 次。

### 步骤 2：验证
- **动作**：`python -c "from PIL import Image; img=Image.open('app/dist/icons/ARG_NAME.png'); assert img.mode=='RGBA'; print(f'{img.size[0]}x{img.size[1]} RGBA')"`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
