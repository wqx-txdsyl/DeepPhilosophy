# Post-Push Cleanup

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：无
- **标记格式**：`[SKIPPED:reason]`

## 前置依赖
- Python 3、Git

## 状态初始化
> TodoWrite: 步骤1数据计数 步骤2临时文件 步骤3Git提交

## 原子步骤

### 步骤 1：数据计数一致性
- **动作**：
```bash
python -c "import json,os; p=json.load(open('backend/data/philosophers.json',encoding='utf-8')); imgs=len([f for f in os.listdir('app/public/philosopher') if f.endswith('.jpg')]); print(f'Philosophers:{len(p)} Images:{imgs}')"
```
- **门禁验证（Check）**：哲人数与图片数一致。

### 步骤 2：临时文件清理
- **动作**：`cd scripts && ls _*.txt _*.log 2>/dev/null | wc -l`
- **补全分支（Remediate）**：列出供审查，手动决定删除。非阻塞。

### 步骤 3：Git 提交
- **动作**：`git status --short | wc -l` -> 确认后手动 `git commit && git push`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z
