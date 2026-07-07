# Add School

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败则重试最多 2 次，仍失败标记 `[SKIPPED:reason]` 并继续。
- **变量替换规则**：
  - `ARG_NAME` = 流派名
  - `ARG_JSON` = `app/public/schools/data/school_ARG_NAME.json`
  - `ARG_IMG` = `app/public/schools/ARG_NAME.webp`
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 架构说明（v2 — 2026-07）
- 学派数据：JSON 文件存储在 `app/public/schools/data/school_XXX.json`
- 图片：WebP 格式（`/schools/XXX.webp`），无缩略图（全分辨率 WebP 足够快）
- SCHOOL_MAP：在 `app/src/pages/SchoolDetailPage.jsx` 中注册，格式：
  ```js
  '流派名': {_json:'school_流派名.json', bg:'url(/schools/流派名.webp)'},
  ```
- 不再有内联 DATA 常量，不再修改 GenealogyPage/WorldMap

## 前置依赖
- `scripts/add_school.py`
- DeepSeek API Key、Agnes API Key (`scripts/api_keys.json`)

## 状态初始化
> 执行前必须先调用 `TodoWrite`：
- [ ] 步骤 1：数据生成
- [ ] 步骤 2：overview/conclusion 循环校验（>=500字）
- [ ] 步骤 3：图片处理（WebP）
- [ ] 步骤 4：SCHOOL_MAP 注册
- [ ] 步骤 5：星丛人物入库
- [ ] 步骤 6：构建验证

## 原子步骤

### 步骤 1：数据生成
- **动作**：`cd scripts && python add_school.py "ARG_NAME"`
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/schools/data/school_ARG_NAME.json'); print('JSON OK')"`
- **补全分支（Remediate）**：失败 -> 重试 2 次。

### 步骤 2：overview/conclusion 循环校验（>=500字）
- **门禁验证（Check）**：`python -c "import json; d=json.load(open('app/public/schools/data/school_ARG_NAME.json',encoding='utf-8')); assert len(d.get('overview',''))>=500; assert len(d.get('conclusion',''))>=500; print('TEXT OK')"`
- **补全分支（Remediate）**：不足 500 字 -> DeepSeek 扩充循环 2 次

### 步骤 3：图片处理（WebP）
- **动作**：检查 ARG_IMG 是否存在；无则生成
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/schools/ARG_NAME.webp'); print('WEBP OK')"`
- **补全分支（Remediate）**：
  1. 先用 Agnes 生成 JPG/PNG
  2. 转为 WebP 并删除原文件：
```bash
python -c "from PIL import Image; import os
for ext in ['.jpg','.png']:
    p=f'app/public/schools/ARG_NAME{ext}'
    if os.path.exists(p):
        img=Image.open(p).convert('RGB')
        img.save(f'app/public/schools/ARG_NAME.webp','WEBP',quality=80)
        os.remove(p); print('WEBP OK'); break
"
```

### 步骤 4：SCHOOL_MAP 注册
- **动作**：在 `app/src/pages/SchoolDetailPage.jsx` 的 `SCHOOL_MAP` 对象中添加条目：
  ```js
  'ARG_NAME': {_json:'school_ARG_NAME.json', bg:'url(/schools/ARG_NAME.webp)'},
  ```
- 同时添加到 `ENG_NAMES` 映射（英文名）。
- **门禁验证（Check）**：`python -c "c=open('app/src/pages/SchoolDetailPage.jsx',encoding='utf-8').read(); assert 'ARG_NAME' in c; print('MAP OK')"`

### 步骤 5：星丛人物入库
- **动作**：提取 ARG_JSON 中所有 thinkers 的 name，对每个新人物执行 add-author
- **门禁验证（Check）**：所有 thinkers 的 name 都存在于 `philosophers.json` 或 `name_aliases.json`
- **补全分支（Remediate）**：add_author 失败重试 2 次，仍失败标记 `[SKIPPED:ADD_FAILED]`

### 步骤 6：构建验证
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：无 error 输出，`BUILD OK`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
- 产物：ARG_JSON, ARG_IMG, SchoolDetailPage.jsx（SCHOOL_MAP 已更新）
