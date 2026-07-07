# Add Sub-School

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：
  - `ARG_NAME` = 子流派名
  - `ARG_PARENT` = 父流派名
  - `ARG_JSON` = `app/public/schools/data/school_ARG_NAME.json`
  - `ARG_PARENT_JSON` = `app/public/schools/data/school_ARG_PARENT.json`
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 架构说明（v2 — 2026-07）
- 学派数据：JSON 文件存储在 `app/public/schools/data/school_XXX.json`
- 图片：WebP 格式，无缩略图
- SCHOOL_MAP：在 `app/src/pages/SchoolDetailPage.jsx` 中注册
- 父流派注册：在父 JSON 的 `subSchools` 对象中添加条目

## 前置依赖
- `scripts/add_subschool.py`、DeepSeek API Key

## 状态初始化
> TodoWrite: 步骤1数据 步骤2父流派注册 步骤3图片 步骤4构建

## 原子步骤

### 步骤 1：数据生成
- **动作**：`cd scripts && python add_subschool.py "ARG_NAME" "ARG_PARENT"`
- **门禁验证（Check）**：`python -c "import os,json; d=json.load(open('app/public/schools/data/school_ARG_NAME.json',encoding='utf-8')); assert d.get('name'); print('JSON OK')"`
- **补全分支（Remediate）**：重试 2 次。

### 步骤 2：父流派注册
- **门禁验证（Check）**：`python -c "import json; d=json.load(open('app/public/schools/data/school_ARG_PARENT.json',encoding='utf-8')); assert 'ARG_NAME' in str(d.get('subSchools',{})); print('REGISTERED OK')"`
- **补全分支（Remediate）**：手动注册 ->
```bash
python -c "
import json
p='app/public/schools/data/school_ARG_PARENT.json'
d=json.load(open(p,encoding='utf-8'))
d.setdefault('subSchools',{})['ARG_NAME']={'name':'ARG_NAME','desc':'','era':''}
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('REGISTERED')
"
```

### 步骤 3：图片处理（WebP，无缩略图）
- **门禁验证（Check）**：`python -c "import os; p='app/public/schools/ARG_NAME.webp'; print('WEBP OK' if os.path.exists(p) else '[WARN:NO_WEBP]')"`
- **补全分支（Remediate）**：生成 JPG/PNG 后转为 WebP 并删除原文件，重试 2 次。

### 步骤 4：SCHOOL_MAP 注册
- **动作**：在 `app/src/pages/SchoolDetailPage.jsx` 的 `SCHOOL_MAP` 中添加：
  ```js
  'ARG_NAME': {_json:'school_ARG_NAME.json', bg:'url(/schools/ARG_NAME.webp)'},
  ```

### 步骤 5：构建验证
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：无 error，`BUILD OK`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z
