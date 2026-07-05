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

## 标签规则

标签自动规范化由 `scripts/_normalize_tags.py` 处理，`add_author.py` 入库后自动调用。手动修改时注意：

### 流派标签 (school)
- **X女性主义**（如"存在主义女性主义"）是独立合法流派，**不拆分**
- **合并相似项**：`_normalize_tags.py` 的 `MERGE_MAP` 自动处理
- **用 `/` 分隔**：多流派用 `/` 分割
- **禁止非人条目**：流派名/书名/术语不能混入哲人列表

### 时代标签 (era)
- **格式**：`YYYY-YYYY` 或 `约YYYY-YYYY年` 或 `YYYY-`
- 跨越世纪筛选由 `_era_to_centuries` 自动计算

### 国家标签 (country)
- **去掉所有括号注释**：`xxx（今yyy）` → `xxx`，以历史国名为准
- **保留移居双国籍**：`xxx（后移居yyy）` → `xxx/yyy`
- 由 `_normalize_tags.py` 的 `normalize_country()` 自动处理

### 头像
- 爬取：`fetch_philosopher_img.py`（Wikipedia → Commons）
- 人脸检测：`check_faces.py --fix`
- 批量爬取：`fetch_philosopher_batch.py --skip-existing`
- AI 兜底：`gen_portrait.py`（古代哲人无现存画像时）

### 介绍 (bio)
- ≥1000 字，中文，纯文本（不含 `**` 标记）

## 批量入库

```bash
cd scripts && python _batch_add.py --apply
```
从 `_not_in_db.txt` 读取名单，DeepSeek 批量生成信息，自动标签规范化。
