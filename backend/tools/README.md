# backend/tools 运维手册

本目录为 DeepPhilosophy 数据管线工具。**一次性的调试/修复脚本一律归档到 `_archive/tmp_scripts/`**（可追溯，不删除）；有持续功能的临时工具（如 `_tmp_reimport.py`）保留在本目录。

---

## 目录

| 脚本 | 职责 |
|------|------|
| `dp_pdf_import.py` | **OCR 引擎**：PDF → 页级 OCR（断点续传）→ 章节化 → 章节 JSON + meta/detail。由 `dp_launch_ocr.py` 以壳+引擎 pythonw 对启动 |
| `dp_ocr_watchdog.py` | 引擎守护：每 5 分钟探活，引擎对死掉则重启（**绝不手动杀 pythonw 进程**——壳+引擎对是正常机制，唯一例外是重启引擎加载新代码） |
| `dp_import_epubs.py` | EPUB 批量导入 |
| `dp_import_txt.py` | TXT 导入（txt 只是占位符，不要花精力） |
| `dp_sync_books.py` | 章节/meta/detail/books.json 同步（**双写规则**：backend/data 与 app/public/backend/data 必须 MD5 一致） |
| `dp_fix_titles.py` | 目录标题修复（章节化强模式误切） |
| `dp_fix_catalog_chapters.py` | 目录章节类型修复（section 全改 chapter） |
| `rebuild_spine.py` | EPUB 章节重建 |
| `verify_book.py` | **单本验证**：`python verify_book.py <bid> --vite-check` —— 章节数/toc/双端 MD5/vite 静态页全绿才算完成 |
| `dp_ocr_watchdog.py` | 见上 |
| `dp_launch_ocr.py` | 引擎启动（壳+引擎对） |
| `dp_merge_summaries.py` | 摘要合并 |
| `dp_score_books.py` | 书籍评分 |
| `dp_gen_pdf_covers.py` / `dp_gen_txt_covers.py` / `dp_epub_covers.py` | 封面生成 |
| `build_book_json.py` / `build_and_sync_kb.py` / `build_knowledge_local.py` | 知识库构建 |
| `build_philosopher_network.py` | 哲学家星丛网络 |
| `build_covers_manifest.py` | 封面 manifest |
| `gen_summaries.py` | AI 批量摘要 |
| `download_gutenberg.py` | Gutenberg 下载 |
| `generate_catalog.py` | 目录生成 |
| `generate_worker_assets.py` | CF Workers 静态资产（books.json 直链映射） |
| `migrate_users_to_d1.py` | 用户数据迁移到 D1 |
| `sync_to_cloud.py` | OSS/云端同步 |

---

## OCR 引擎机制（dp_pdf_import.py）

- **启动方式**：`dp_launch_ocr.py` → `.venv/Scripts/pythonw.exe dp_pdf_import.py` 壳进程 + 引擎进程（成对存在，绝不可杀）
- **断点续传**：`ckpt["ocr"][safe]` 字典存每页文本（safe = rel 路径正则转换），每 10 页 dump 到 `backend/data/dp_pdf_import_ckpt.json`，`__FAILED__` 标记失败页
- **临时图片**：`$TEMP/dp_paddle/{safe}_p{i:04d}.png`，ZOOM=1.2 渲染，每页重新 fitz.open
- **实例重建**：RESTART_EVERY=100 页重建 PaddleOCR 实例（del + gc.collect）
- **章节化 chapterize**：强模式标题（`CH_PAT`：第X章/序/前言/§ 等，`<40` 字符且 50 行内不重复）切章，**"第一讲"类标题不识别**（"讲"不在 `[章节卷篇部]` 内）——讲座类书需专用修复脚本
- **FORCE_OCR**：无文本层的书强制 OCR；has_text_layer 多页抽样判断

### 单本重导（_tmp_reimport.py）

```bash
python _tmp_reimport.py <书名片段>   # 独立 TMP_CKPT，不碰主 ckpt，与引擎并行安全
```

- **SKIP_PAGES 污染页过滤**：源 PDF 混入无关页时在 SKIP_PAGES 字典登记（如现象学的观念 p20-p27 = 论文页），重导自动跳过
- reimport 只写 backend 侧，**public 副本需手动补**（双写规则）

---

## 数据双写规则（book-detail-sync-rule）

修复一本书必须同步：

1. `backend/data/book_chapters/<bid>/` 章节 JSON + meta.json
2. `app/public/backend/data/book_chapters/<bid>/` **同名副本**（MD5 必须一致，verify_book 会查）
3. `backend/data/book_detail/<bid>.json` + `app/public/book_detail/<bid>.json`
4. `app/public/books.json` 的 chapterCount

完成标准：`verify_book.py <bid> --vite-check` 全绿。

---

## 已知坑

- **GBK 控制台**：Python 脚本内 `sys.stdout = io.TextIOWrapper(..., encoding="utf-8")` 或设 `PYTHONIOENCODING=utf-8`，否则中文输出乱码
- **PowerShell 中 `python -c` 嵌套引号必崩**（中文引号/多层引号）—— 一律写临时脚本文件
- **vite 新书不可见**：引擎入库的新书 vite dev 看不到（public 预索引 + watch.ignored），必须重启 vite；8000 只挂 API
- **commit message 禁 ASCII 双引号**（PowerShell 5.1 兼容），用中文引号或单引号
- **正文 OCR 残字不修**：页内脚注编号（如 "认 14识批判"）、跨页断词（"方\n法"）等属 OCR 产物，保留
- **txt 只是占位符**，不要处理
- **神学大全必须分段**（章节化后章节太大需专用脚本）
- **大仓库 push 用 run_in_background**
- **新书 vite 不可见时检查**：`app/public/backend/data/book_chapters/<bid>/` 存在性

---

## 归档策略

- 一次性调试脚本：`backend/tools/_archive/tmp_scripts/`（保留文件名可追溯）
- 有持续功能的临时工具：留在 `backend/tools/`（如 `_tmp_reimport.py`）
