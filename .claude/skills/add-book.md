# Add Book Skill

## 新增书籍

扫描本地 `F:/philosophy` → DeepSeek生成标签+摘要 → 存入数据库 → 更新前端计数

## 用法

```bash
cd scripts

# 单本
python add_book.py "F:/philosophy/西方/尼采/查拉图斯特拉如是说.pdf"

# 批量（扫描全部新书）
python add_book.py --scan
```

## 流程

1. 解析路径 → region / author / title / file_type
2. DeepSeek 生成 2-5 个标签 + ≥300字摘要
3. 保存到 `book_summaries.json`（`书名||作者` 复合键）
4. 如有新标签 → 提示手动添加到规范化系统
5. TXT 文件标记为 `pending`，PDF/EPUB 为 `available`

## 注意

- 自动跳过 `jpg`/`合集&概述` 目录
- `book_summaries.json` 使用 `书名||作者` 复合键避免同名书覆盖
