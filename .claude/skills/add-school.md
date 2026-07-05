# Add School

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败才报错并**回滚/标记**（而非直接退出）。

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：数据生成
- [ ] 步骤 2：overview/conclusion 循环校验（>=500字）
- [ ] 步骤 3：图片处理（背景图 + 缩略图，无图则 AI 生成）
- [ ] 步骤 4：内联 DATA（SchoolDetailPage + GenealogyPage + WorldMap）
- [ ] 步骤 5：计数更新（HomePage/Settings/Genealogy）
- [ ] 步骤 6：构建验证

## 原子步骤

### 步骤 1：数据生成
- **动作**：`cd scripts && python add_school.py "ARG_NAME"`
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/schools/school_ARG_NAME.json'); print('JSON OK')"`
- **补全分支（Remediate）**：生成失败 -> 重试 add_school.py，最多 2 次。检查 DeepSeek API Key。

### 步骤 2：overview/conclusion 循环校验
- **动作**：
```bash
python -c "import json; d=json.load(open('app/public/schools/school_ARG_NAME.json')); assert len(d.get('overview',''))>=500; assert len(d.get('conclusion',''))>=500; print('TEXT OK')"
```
- **补全分支（Remediate）**：不足 500 字 -> 调用 DeepSeek 扩充，循环最多 2 次。

### 步骤 3：图片处理
- **动作**：检查 `app/public/schools/ARG_NAME.jpg`，无则 `python gen_school_bg.py "ARG_NAME"` AI 生成。生成 400x300 缩略图。
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/schools/ARG_NAME.jpg'); assert os.path.exists('app/public/schools/thumb/ARG_NAME.jpg'); print('IMG+THUMB OK')"`
- **补全分支（Remediate）**：缺图 -> AI 生成，重试 2 次。

### 步骤 4：内联 DATA
- **动作**：add_school.py 自动注入 SchoolDetailPage + GenealogyPage + WorldMap。
- **门禁验证（Check）**：`python -c "import re; c=open('app/src/pages/SchoolDetailPage.jsx',encoding='utf-8').read(); assert 'ARG_NAME' in c; print('INLINE OK')"`

### 步骤 5：计数更新
- **动作**：add_school.py 自动更新 HomePage/Settings/Genealogy。
- **门禁验证（Check）**：`python -c "import re; c=open('app/src/pages/GenealogyPage.jsx',encoding='utf-8').read(); assert 'ARG_NAME' in c; print('COUNT OK')"`

### 步骤 6：构建验证
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：`test -f app/dist/index.html && echo "BUILD OK"`

## 执行报告（必须输出）
- 成功项：X 条
- 补全项：Y 条（列出：{项目名} -> 补全动作 -> 最终状态）
- 失败跳过项：Z 条（列出：{项目名} -> 失败原因）
- 产物：app/public/schools/school_ARG_NAME.json, ARG_NAME.jpg, SchoolDetailPage.jsx（已更新）
