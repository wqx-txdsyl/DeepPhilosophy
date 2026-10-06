---
name: add-school
description: 添加哲学流派——生成背景图→创建JSON→更新SchoolDetailPage→推送
---

## 前置依赖
- `scripts/gen_school_bg.py`（AI 生成流派背景图）
- `scripts/add_school.py`
- Agnes API Key（根目录`.env`）、DeepSeek API Key、Pillow

## 流程

### 1. 生成流派背景图
```bash
cd scripts && python gen_school_bg.py "ARG_NAME"
```
保存到 `app/public/schools/ARG_NAME.webp`

### 2. 创建流派 JSON
```bash
cd scripts && python add_school.py "ARG_NAME"
```
生成 `app/public/schools/data/school_ARG_NAME.json`。若已存在则跳过。

### 3. 更新 SchoolDetailPage 映射
在 `app/src/pages/SchoolDetailPage.jsx` 中添加该流派的 `_json` 和 `bg` 映射。

### 4. 关联哲学家
检查 `app/public/philosophers.json` 中有哪些哲学家属于此流派，确保 `school` 字段一致。

### 5. 推送
```bash
git add -A && git commit -m "feat: 添加流派 ARG_NAME" && git push
```
