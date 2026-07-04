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

## 三处标签同步点（修改标签时必同步）

- `backend/main.py` `_normalize_tag()`
- `app/src/pages/AuthorsPage.jsx` `normMap`
- `app/src/pages/BooksPage.jsx` `normMap`
