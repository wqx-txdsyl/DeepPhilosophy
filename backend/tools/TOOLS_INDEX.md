# PHA backend/tools 脚本分类索引（含 DP tools / DP scripts）

> 模块化原则：**不物理移动脚本**（`dp_clean_book.py` 被 13 个脚本 import，分目录会断依赖）。
> 用本索引按功能分类表达模块边界；新增脚本请按前缀命名并在对应类别下登记。
> 一次性调试/修复脚本一律放 `_tmp/`，随用随删，**不提交 git**。
>
> 状态标注：无标记 = 长期可复用；`[已归档]` = 一次性修复已完成（DP scripts 侧仅存档参考；
> PHA tools 侧已归档 27 个已删除，见第 13 节）；`[勿运行]` = 占位符保护。

## 1. 书籍导入与入库（书库入口）

| 脚本 | 状态 | 用途 |
|---|---|---|
| `dp_pdf_import.py` | 保留 | PDF 导入（文本层提取 / OCR 断点续传 / 章节化） |
| `dp_import_epubs.py` | 保留 | epub 补入库（chapterCount<=1 的书） |
| `dp_import_txt.py` | 勿运行 | txt 占位导入（91 本无内容仅证明存在） |
| `dp_run_import.py` | 保留 | 未入库书逐本处理管线（质检→回灌→同步） |
| `download_gutenberg.py` | 保留 | Gutenberg 公有领域文本下载 |

## 2. OCR 流水线

| 脚本 | 状态 | 用途 |
|---|---|---|
| `dp_launch_ocr.py` | 保留 | 启动 OCR 单分片（venv launcher 壳+引擎对，勿杀进程） |
| `dp_ocr_epub.py` | 保留 | 图片型 epub OCR 入库 |
| `dp_ocr_check.py` | 保留 | OCR 入库质量核查清单 |
| `dp_ocr_watchdog.py` | 保留 | OCR 看门狗（心跳/异常恢复，会话无关） |
| `dp_retry_ocr.py` | 保留 | 重 OCR FAILED 页（断点续传只补失败页） |
| `dp_clean_book.py` | 保留 | **核心清理模块**：单本书章节清洗/重建/降级/弃用（被 13 脚本 import） |

## 3. 章节构建与重建

| 脚本 | 状态 | 用途 |
|---|---|---|
| `rebuild_spine.py` | 保留 | 章节骨架重建（印刷页码偏移/接排标题/扫描重复页） |
| `rebuild_auto.py` | 保留 | 全库通用重建 v2（核查 A2/A4） |
| `dp_toc_parts.py` | 保留 | 扁平 toc → 层级 toc（part 分组）全库转换 |

## 4. 单本书修复（dp_fix_*，按书命名）

| 脚本 | 状态 | 对应书籍 |
|---|---|---|
| `dp_fix_authors.py` | 保留 | 作者字段修复（通用，未来新书仍可能用） |

> 2026-08-07 系列一次性修复（康德/尼采/擬仿物/恐惧与战栗/地下室手记/理想国/美学中的不满/资本论/书名污染等 23 个 dp_fix_*）已完成使命，2026-08-11 全部删除，git 历史可找回。

## 5. 同步（三层同步：PHA → DP → app/public）

| 脚本 | 状态 | 用途 |
|---|---|---|
| `dp_sync_books.py` | 保留 | 汇总生成 app/public/books.json（PDF 入库后必跑） |
| `dp_sync_all.py` | 保留 | 双端全量同步（章节 → DP public + backend） |
| `dp_sync_fixed.py` | 保留 | 已修复书的双端同步补漏 |
| `sync_full.py` | 保留 | 全库三端内容同步 |

## 6. 向量库

| 脚本 | 状态 | 用途 |
|---|---|---|
| `build_embeddings.py` | 保留 | 全量向量构建（智谱 embedding-2） |
| `dp_embed_missing.py` | 保留 | 增量嵌入缺失章节（text_hash 去重） |
| `dp_build_nietzsche_index.py` | 保留 | AIAuthor 尼采语料运行时检索索引（all_chunks.json → vectors.npy/meta/chunks.jsonl, 源文件只读不动; Phase R2/R3） |

## 7. 资产与数据构建

| 脚本 | 状态 | 用途 |
|---|---|---|
| `build_book_json.py` | 保留 | EPUB/TXT → 结构化 JSON（rebuild_spine 依赖） |
| `build_covers_manifest.py` | 保留 | 封面 → public/covers/ + covers.json 清单 |
| `dp_epub_covers.py` | 保留 | epub 封面补全 + 重建 covers.json |
| `dp_gen_pdf_covers.py` | 保留 | pdf 封面抓取（fitz 渲染首页，不需 OCR） |
| `dp_gen_txt_covers.py` | 保留 | txt 占位书文字封面 |
| `dp_merge_summaries.py` | 保留 | 历史 book_summaries.json 合并进 detail |
| `gen_summaries.py` | 保留 | 批量生成书籍摘要和标签（DeepSeek） |
| `generate_catalog.py` | 保留 | books_catalog.json 生成（离线兜底） |
| `dp_score_books.py` | 保留 | 批量书籍评分 → book_rankings.json |
| `build_philosopher_network.py` | 保留 | 哲学家星丛网络（AI 识别思想关系） |

## 8. 校验

| 脚本 | 状态 | 用途 |
|---|---|---|
| `dp_verify_dual.py` | 保留 | 双库入库一致性校验 |
| `dp_ocr_check.py` | 保留 | OCR 质量检查（见第 2 类） |

## 9. 生产运维工具（2026-08-14 两仓合并后随仓库保留）

> 2026-08-14：PhiAgent 已并入 DeepPhilosophy 单仓库，第 1-8 类的书库工具与本节运维工具现同处 `backend/tools/`，不再分仓。

| 脚本 | 状态 | 用途 |
|---|---|---|
| `verify_book.py` | 保留 | 书修复完成验证（模拟前端完整读取链，皮尔斯事故后固化） |
| `generate_worker_assets.py` | 保留 | 生成 Cloudflare api worker 静态资产 |
| `migrate_users_to_d1.py` | 保留 | 旧 users.db → D1 导入 SQL 生成器 |
| `dp_fix_catalog_chapters.py` | 保留 | books_catalog.json chapterCount 从 meta.json 校准 |
| `dp_grab_cf_assets.py` | 保留 | 从 CF Pages 部署 URL 抓取构建产物（含懒加载 chunk）→ dist/assets；`--upload` 调 `dp_sync_oss_static.py` 传 OSS |
| `dp_consistency_check.py` | 保留 | 双端数据一致性校验 |
| `dp_perf_phase_r.py` | 保留 | Phase R 性能回归测量（冷启动/persona-only/语料检索/10轮会话/旧基线对比, 结果落 data/phase_r_perf.json） |
| `dp_uat_phase_r.py` | 保留 | Phase R 真实 retrieval UAT（新检索 vs 旧 term-count 基线 + 存量向量 dense 管线锚点, 结果落 data/phase_r_uat.json） |
| `README.md` | 保留 | tools 运维手册（含双写规则/已知坑） |
| `__init__.py` | 保留 | 包标记 |

> 历史说明：2026-08-11 曾将 22 个工具从 DP 侧删除、统一放 PHA 侧；2026-08-14 两仓合并后统一目录，分家历史已归档。

## 10. DP scripts（内容运营 + 历史运维，38 个）

| 脚本 | 状态 | 用途 |
|---|---|---|
| `_lib.py` | 保留 | 共享工具模块（JSON + DeepSeek/Agnes 客户端） |
| `add_author.py` / `add_book.py` | 保留 | 一键新增哲人/书籍（直操作 public JSON + DeepSeek） |
| `add_school.py` / `add_subschool.py` | 保留 | 一键新增流派/下属流派（全流程自动化） |
| `fetch_portraits.py` / `fetch_philosopher_img.py` / `fetch_philosopher_batch.py` / `fetch_bing_portraits.py` / `fetch_wiki_zh.py` | 保留 | 哲学家肖像爬取（新哲人入库时用） |
| `gen_portrait.py` / `gen_school_bg.py` | 保留 | AI 生成肖像/流派背景（低频） |
| `verify_all_portraits.py` / `check_portraits.py` / `cleanup_portraits.py` / `ai_verify_*.py` | 已归档 | 肖像验证系列（7 月错图清理已完成） |
| `delete_wrong_images.py` / `dedup_philosophers.py` / `expand_bios.py` / `fix_english_names.py` / `fix_map_coords.py` / `list_missing.py` / `score_item.py` / `find_translations.py` / `gen_tags_batch.py` | 已归档/保留 | 内容运营辅助（多数已完成，score_item/find_translations/gen_tags_batch 仍可复用） |
| `audit_all_chapters.py` / `batch_extract.py` / `extract_one.py` / `test_extract.py` / `batch_import_books.py` / `check_all_books.py` / `fix_bad_chapters.py` / `fix_book_ids.py` | 已归档 | 章节时代旧体系（已被 rebuild_spine / dp_clean_book 取代） |
| `agnes_direct_test.py` / `agnes_quick_test.py` | 已归档 | Agnes AI 连通性测试（一次性） |

## 11. 规范文档（长期保留）

| 文档 | 用途 |
|---|---|
| `CHKLIST.md` | 402 本书分组/状态台账（A 已完成 / B 待推进 / C 引擎组 / D txt 占位，总数恒等于 402） |
| `OCR_CHECKLIST.md` | OCR 检查清单 |
| `分章标准规范.md` | 章节结构规范（顶层 dict 禁 list；toc 对象数组 part/chapter/section） |
| `TOOLS_INDEX.md` | 本索引 |

## 12. 临时区（不提交）

| 路径 | 规则 |
|---|---|
| `_tmp/` | 临时脚本/产物，随用随删 |

## 13. 已清理（2026-08-11 审计）

- 用户级 `.claude/skills/` 空壳目录 10 个已删：add-author / add-book / add-school / add-subschool / check-philosopher-images / fetch-philosopher-img / fix-counts / local-check / post-push / relationship-constellation（全部 0 文件，07-20 创建后从未填充，对应流程已被 tools/ 体系取代）
- DP `scripts/qa_scripts/` 已删（仅含萨特重建方案笔记 1 份，重建已完成）
- **两边 tools 分家**：DP tools 28 → 6（22 个 PHA 重复拷贝 + 3 个 Render 废弃删除）；PHA tools 删 3 个 Render 废弃（build_and_sync_kb / build_knowledge_local / sync_to_cloud）
- **Render 退役清理**：DP `Dockerfile` `render.yaml` 已删（keepalive.yml 此前已删）；`gen_school_bg.py` onrender URL → deepphilosophy.top；README 架构/部署表已改 Cloudflare Workers
- **git 双份章节跟踪解除**：`app/public/backend/data/book_chapters/`（12210 文件，vite dev 镜像）已 `git rm --cached` + .gitignore；生产 CDN 读 `backend/data/book_chapters/`（仍跟踪）
- **零引用纹理删除**：gene/ + schools/ 各 4 个（gold_particles / old_map_texture / paper_texture / 哲学星图，前端零引用）
- **PHA tools 已归档 27 个删除**（08-07 一次性修复全部完成，git 历史可找回）：dp_rebuild_ocr_books / dp_rebuild_kjy / dp_rebuild_ysdh / dp_rebuild_ysdh_emb / dp_rebuild_epub_emb / dp_scan_part_anchors / dp_fix_part_anchors / fix_page_num_lines / fix_merge_empty / dp_fix_kant / dp_fix_nietzsche_toc / dp_inspect_nietzsche / dp_fix_nfw_toc / dp_fix_nfw_t2 / dp_fix_kjy_toc / dp_fix_dxs_toc / dp_fix_jihe_toc / dp_fix_lxg_toc / dp_fix_mxm_toc / dp_fix_zbjl_toc / dp_fix_orphan_toc / dp_fix_title / dp_fix_titles / dp_fix_titles2 / dp_fix_titles3 / dp_fix_empty_blocks / fix_toc_sync → PHA tools 61 → 34；DP scripts 侧 `[已归档]` 26 个保留存档（不影响运行）
