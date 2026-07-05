# Fix Counts

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败则重试最多 2 次，仍失败标记并继续。

## 状态初始化
> 执行前必须先调用 `TodoWrite`：
- [ ] 步骤 1：扫描 SCHOOL_MAP 统计
- [ ] 步骤 2：自动更新 HomePage/Settings/Genealogy
- [ ] 步骤 3：构建验证

## 原子步骤

### 步骤 1：扫描
- **动作**：`cd scripts && python add_school.py --update-counts-only`
- **门禁验证（Check）**：检查 HomePage/Genealogy/Settings 中计数是否一致。

### 步骤 2：验证
- **动作**：
```bash
python -c "import re; [print(f'{f}: OK') for f in ['HomePage','GenealogyPage','SettingsPage'] if '个流派' in open(f'app/src/pages/{f}.jsx',encoding='utf-8').read()]"
```

### 步骤 3：构建
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：`test -f app/dist/index.html && echo "BUILD OK"`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
