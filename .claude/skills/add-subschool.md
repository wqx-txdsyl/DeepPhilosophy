# Add Sub-School

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_NAME` = 子流派名；`ARG_PARENT` = 父流派名
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- `scripts/add_subschool.py`、`scripts/gen_school_bg.py`、DeepSeek API Key

## 状态初始化
> TodoWrite: 步骤1数据生成 步骤2父流派注册 步骤3图片处理 步骤4构建验证

## 原子步骤

### 步骤 1：数据生成
- **动作**：`cd scripts && python add_subschool.py "ARG_NAME" "ARG_PARENT"`
- **门禁验证（Check）**：`python -c "import os,json; d=json.load(open('app/public/schools/school_ARG_NAME.json')); assert d.get('name'); print('JSON OK')"`
- **补全分支（Remediate）**：重试 2 次。

### 步骤 2：父流派注册
- **门禁验证（Check）**：`python -c "import json; d=json.load(open('app/public/schools/school_ARG_PARENT.json')); assert 'ARG_NAME' in str(d.get('sub_schools',{})); print('REGISTERED OK')"`
- **补全分支（Remediate）**：手动注册 ->
```bash
python -c "import json; d=json.load(open('app/public/schools/school_ARG_PARENT.json')); d.setdefault('sub_schools',{})['ARG_NAME']={'name':'ARG_NAME','desc':''}; json.dump(d,open('app/public/schools/school_ARG_PARENT.json','w'),ensure_ascii=False,indent=2); print('REGISTERED')"
```

### 步骤 3：图片处理
- **门禁验证（Check）**：`python -c "import os; p='app/public/schools/ARG_NAME.jpg'; print('IMG OK' if os.path.exists(p) else '[WARN:NO_IMG]')"`
- **补全分支（Remediate）**：`cd scripts && python gen_school_bg.py "ARG_NAME"` 重试 2 次。

### 步骤 4：构建验证
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：`test -f app/dist/index.html && echo "BUILD OK"`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z
