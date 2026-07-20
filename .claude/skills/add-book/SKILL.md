---
name: add-book
description: 添加书籍——下载EPUB→章节→封面→摘要→评分→排序→推送
---

## 前置依赖
- `backend/tools/rebuild_spine.py`（EPUB→章节JSON）
- `backend/tools/build_covers_manifest.py`（封面提取）
- `backend/tools/gen_summaries.py`（AI摘要标签）
- `backend/tools/download_gutenberg.py`（公版书下载）
- DeepSeek API Key（根目录`.env`）

## 流程

### 1. 获取 EPUB
- 方式A：`python backend/tools/download_gutenberg.py --search "书名" --author "作者"`
- 方式B：手动放到 `F:/philosophy/{区域}/{作者}/书名.epub`

### 2. 重建章节
```bash
cd backend && python tools/rebuild_spine.py
```
生成 `data/book_chapters/{book_id}/` + `data/book_detail/{book_id}.json`

### 3. 提取封面
```bash
cd backend && python tools/build_covers_manifest.py
```
生成 `app/public/covers/{book_id}.webp` + 更新 `covers.json`

### 4. 生成 AI 摘要和标签
```bash
cd backend && python tools/gen_summaries.py
```
写入 `data/book_detail/{book_id}.json` 的 `summary` 和 `tags`

### 5. AI 评分（五维度）
```bash
cd scripts && python score_item.py "ARG_TITLE" --type book --extra "ARG_AUTHOR"
```
返回 `{scores:[深度,影响力,学术,原创,可读], rank:加权综合分}`。写入 book_detail 和 books.json 的 `rank` 字段。

### 6. 更新 books.json
从 `data/book_detail/` 重新生成 `app/public/books.json`，按 rank 降序排列。

### 7. 同步 + 推送
```bash
python -c "import shutil;shutil.copytree('backend/data/book_chapters','app/public/book_chapters',dirs_exist_ok=True)"
git add -A && git commit -m "feat: 添加书籍 ARG_TITLE" && git push
```
