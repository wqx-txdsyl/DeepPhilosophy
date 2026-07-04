# Add Author Skill

## 新增哲学家

输入哲人名 → DeepSeek生成年代/地区/流派/千字简介 → 插入数据库 → **爬取头像+人脸检测+缩略图** → 更新标签系统

## 用法

```bash
cd scripts

# 基础
python add_author.py "亚里士多德"

# 带本地著作提示
python add_author.py "尼采" --folder "F:/philosophy/西方/尼采"
```

## 流程

1. 检查是否已存在
2. DeepSeek 生成：era / country / school / bio(≥1000字) / wiki_url
3. 标签标准化 + 合并 + 去重（参考 README 标签系统）
4. 保存到 `philosophers.json`
5. **爬取头像**：Wikipedia API → Wikimedia Commons 备用 → 下载原图
6. **人脸检测**：OpenCV Haar Cascade（正脸+侧脸）→ 提示质量
7. **缩略图**：自动生成 200×280 thumb
8. 新标签 → 提示手动添加到三处同步点
9. 更新计数提示

## 图片输出

- `app/public/philosopher/{哲人名}.jpg` — 原图
- `app/public/philosopher/thumb/{哲人名}.jpg` — 缩略图（200×280）

## 标签规则（添加/修改哲学家时必须遵守）

### 流派标签 (school)
- **禁止组合标签**：不能出现"存在主义女性主义"等拼接，应拆为"存在主义/女性主义"
- **合并相似项**：如"希腊哲学"→"古希腊哲学"，"新儒家"→"现代新儒家"
- **用 `/` 分隔**：多流派用 `/` 分割，不用 `,` `、` `;`
- **禁止非人条目**：流派名/书名/术语不能混入哲人列表

### 时代标签 (era)
- **格式**：`YYYY-YYYY` 或 `约YYYY-YYYY年` 或 `YYYY-`
- **跨越世纪筛选**：哲学家生活过的所有世纪都应能筛选到。如1889-1976应同时出现在"19世纪"和"20世纪"筛选中（通过 `_era_to_centuries` 自动计算）

### 国家标签 (country)
- **禁止括号注释**：`英国（后移居美国）` → 应为 `英国/美国`（保留双国籍信息但去掉括号说明）
- **筛选行为**：双国籍哲人在两个国家的筛选中都出现

### 头像
- 爬取后必须通过人脸检测（`check_faces.py`）
- 无人脸则自动重爬，重爬失败标记为"无人脸"
- 古代哲人无现存画像 → `gen_portrait.py` AI 生成水墨肖像

### 介绍 (bio)
- ≥1000 字，中文
- 包含：生平背景、核心思想、主要著作、历史影响
- 不含 markdown `**` 标记（纯文本）

## 三处标签同步点（修改标签时必同步）

- `backend/main.py` `_normalize_tag()`
- `app/src/pages/AuthorsPage.jsx` `normMap`
- `app/src/pages/BooksPage.jsx` `normMap`
