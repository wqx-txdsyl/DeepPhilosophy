# School Background Generator

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败则重试最多 2 次，仍失败标记并继续。

## 状态初始化
> 执行前必须先调用 `TodoWrite`：
- [ ] 步骤 1：API Key 校验
- [ ] 步骤 2：AI 生成背景图
- [ ] 步骤 3：缩略图
- [ ] 步骤 4：文件验证

## 原子步骤

### 步骤 1：API Key 校验
- **动作**：同 agnes-image 步骤 1。
- **门禁验证（Check）**：`KEY OK`。

### 步骤 2：生成
- **动作**：`cd scripts && python gen_school_bg.py "ARG_SCHOOL"`
- **门禁验证（Check）**：`python -c "import os; p='app/public/schools/ARG_SCHOOL.jpg'; assert os.path.exists(p); print(f'GEN OK: {os.path.getsize(p)//1024}KB')"`
- **补全分支（Remediate）**：失败 -> 检查 API 余额，重试 2 次。

### 步骤 3：缩略图
- **动作**：标准 400x300 thumb。

### 步骤 4：验证
- **动作**：`python -c "from PIL import Image; img=Image.open('app/public/schools/ARG_SCHOOL.jpg'); assert img.size[0]>=1200; print(f'{img.size[0]}x{img.size[1]} OK')"`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
