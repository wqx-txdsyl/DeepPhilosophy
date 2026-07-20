---
name: add-author
description: 添加哲学家——查重→AI简介标签→写入→头像→星丛→评分→推送
---

## 前置依赖
- `scripts/fetch_philosopher_img.py` `scripts/gen_portrait.py` `scripts/_lib.py`
- `backend/tools/build_philosopher_network.py`
- DeepSeek API Key（根目录 `.env`）、Pillow

## 原子步骤

### 1. 查重
`python -c "import json;d=json.load(open('app/public/philosophers.json','r',encoding='utf-8'));print('EXISTS' if 'ARG_NAME' in d else 'NEW')"`
→ 输出 `NEW` 则继续，`EXISTS` 则跳过

### 2. AI 生成（DeepSeek）
调用 DeepSeek API，生成 JSON：`{tags:[],bio(>=1000字),era,country,school}`。地区根据 country 自动分类（东方=中国，西方=欧美大洋洲，世界=其他）。

### 3. 写入 philosophers.json
写入 `app/public/philosophers.json`，同步到 `backend/data/philosophers.json`

### 4. 头像
```bash
cd scripts && python fetch_philosopher_img.py "ARG_NAME" || python gen_portrait.py "ARG_NAME"
```
转 WebP 删原图。

### 5. 更新星丛网络
```bash
cd backend && python tools/build_philosopher_network.py
```

### 6. 推送
```bash
git add -A && git commit -m "feat: 添加哲学家 ARG_NAME" && git push
```
