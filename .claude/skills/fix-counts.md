# Fix Counts

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：无（自动扫描 SCHOOL_MAP）
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- `scripts/add_school.py`（含 `--update-counts-only` 模式）

## 状态初始化
> TodoWrite: 步骤1扫描 步骤2更新 步骤3验证

## 原子步骤

### 步骤 1：扫描 SCHOOL_MAP
- **动作**：`cd scripts && python add_school.py --update-counts-only`
- **门禁验证（Check）**：检查 HomePage/Settings/Genealogy 计数一致。

### 步骤 2：验证
- **动作**：`python -c "import re; [print(f'{f}: OK') for f in ['HomePage','GenealogyPage','SettingsPage'] if '个流派' in open(f'app/src/pages/{f}.jsx',encoding='utf-8').read()]"`

### 步骤 3：构建
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：`test -f app/dist/index.html && echo "BUILD OK"`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z
