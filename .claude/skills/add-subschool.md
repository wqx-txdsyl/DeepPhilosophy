# Add Sub-School

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败才报错并**回滚/标记**（而非直接退出）。

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：数据生成
- [ ] 步骤 2：父流派注册
- [ ] 步骤 3：图片处理
- [ ] 步骤 4：构建验证

## 原子步骤

### 步骤 1：数据生成
- **动作**：`cd scripts && python add_subschool.py "ARG_NAME" "PARENT_NAME"`
- **门禁验证（Check）**：`python -c "import os,json; d=json.load(open('app/public/schools/school_ARG_NAME.json')); assert d.get('name'); print('JSON OK')"`
- **补全分支（Remediate）**：失败 -> 重试 2 次。

### 步骤 2：父流派注册
- **门禁验证（Check）**：`python -c "import json; d=json.load(open('app/public/schools/school_PARENT_NAME.json')); assert 'ARG_NAME' in str(d.get('sub_schools',{})); print('REGISTERED OK')"`
- **补全分支（Remediate）**：未注册 -> 手动添加 sub_schools 条目。

### 步骤 3：图片处理
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/schools/ARG_NAME.jpg'); print('IMG OK')"`
- **补全分支（Remediate）**：缺图 -> AI 生成（python gen_school_bg.py "ARG_NAME"），重试 2 次。

### 步骤 4：构建验证
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：`test -f app/dist/index.html && echo "BUILD OK"`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
