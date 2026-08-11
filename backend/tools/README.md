# backend/tools 运维手册

> **2026-08-11 分家**：本目录只保留 DeepPhilosophy 侧要用的运维工具；
> 书库构建/修复/同步/向量工具一律在 **PhiAgent** 仓库 `backend/tools/`（主工作侧，用 DP venv 运行，产物同步回本仓库）。
> 其余历史拷贝已删除（git 历史可追溯）。

---

## 目录

| 脚本 | 职责 |
|------|------|
| `verify_book.py` | **单本验证**：`python verify_book.py <bid> --vite-check` —— 章节数/toc/双端 MD5/vite 静态页全绿才算完成 |
| `generate_worker_assets.py` | CF api worker 静态资产（books.json 直链映射/stats/admin_stats，写 workers/api/src/） |
| `migrate_users_to_d1.py` | 旧 users.db → D1 导入 SQL 生成器（workers/api/migrations/002_import.sql） |
| `dp_fix_catalog_chapters.py` | books_catalog.json chapterCount 从 meta.json 校准 |
| `README.md` | 本手册 |
| `__init__.py` | 包标记 |

---

## 数据双写规则（book-detail-sync-rule）

修复一本书必须同步（由 PHA 侧工具执行，本手册记录核对标准）：

1. `backend/data/book_chapters/<bid>/` 章节 JSON + meta.json（**git 跟踪，jsDelivr CDN 生产源**）
2. `app/public/backend/data/book_chapters/<bid>/` **vite dev 镜像**（MD5 必须一致，verify_book 会查；**git 不跟踪**，.gitignore）
3. `backend/data/book_detail/<bid>.json`（本地运行时镜像）+ `app/public/book_detail/<bid>.json`（**正式源，git 跟踪**）
4. `app/public/books.json` 的 chapterCount

完成标准：`verify_book.py <bid> --vite-check` 全绿。

---

## 已知坑（跨仓库通用）

- **GBK 控制台**：Python 脚本内 `sys.stdout = io.TextIOWrapper(..., encoding="utf-8")` 或设 `PYTHONIOENCODING=utf-8`，否则中文输出乱码
- **PowerShell 中 `python -c` 嵌套引号必崩**（中文引号/多层引号）—— 一律写临时脚本文件
- **commit message 禁 ASCII 双引号**（PowerShell 5.1 兼容），用 `git commit -F` 文件最可靠
- **正文 OCR 残字不修**：页内脚注编号、跨页断词等属 OCR 产物，保留（toc/章节开头标题可修）
- **txt 只是占位符**，不要处理
- **大仓库 push 用 run_in_background**
- **新书 vite 不可见时检查**：`app/public/backend/data/book_chapters/<bid>/` 存在性（vite public 实时查盘，无需重启）
