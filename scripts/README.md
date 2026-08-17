# scripts/ — 平台运维脚本（S17 职责边界，audit 2026-08-17）

本目录与 `backend/tools/` 分工如下，避免两处跳转：

| 目录 | 职责 | 说明 |
|---|---|---|
| `backend/tools/` | 书库数字化工序 | `dp_*` 系列：导入/OCR/章节重建/向量化/OSS 同步/逐本验收（43 个，见 `backend/tools/TOOLS_INDEX.md`） |
| `scripts/`（本目录） | 平台元数据运维 | 哲人/学校/书籍条目（add_*）、画像（fetch_*/gen_*/score_item）、标签（gen_tags_batch）、翻译检索（find_translations）、缺漏清单（list_missing） |
| `scripts/archive/` | 旧版/一次性脚本 | 历史归档，不参与维护（`_lib.py` 为共享库，勿入 archive） |

约定：
- 新脚本按职责放对应目录，前缀遵循现有命名（书库→`dp_`，运维→动词开头）。
- 不要在两侧复制同一功能；发现重复先归档旧版再新增。
