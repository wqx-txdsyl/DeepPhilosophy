# Add Author Skill

## 新增哲学家

输入哲人名 → DeepSeek生成年代/地区/流派/千字简介 → 插入数据库 → 更新标签系统

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
2. DeepSeek 生成：era / country / school / bio(≥1000字) / wiki_url / baidu_url
3. 标签标准化 + 合并 + 去重（参考 README 标签系统）
4. 保存到 `philosophers.json`
5. 新标签 → 提示手动添加到三处同步点
6. 更新计数提示

## 三处标签同步点（修改标签时必同步）

- `backend/main.py` `_normalize_tag()`
- `app/src/pages/AuthorsPage.jsx` `normMap`
- `app/src/pages/BooksPage.jsx` `normMap`
