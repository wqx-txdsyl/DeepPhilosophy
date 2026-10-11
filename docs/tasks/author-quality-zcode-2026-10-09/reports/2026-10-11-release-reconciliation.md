# 已发布资料 OSS 同步回执（2026-10-11）

## 背景与范围

主线已有 513 份 source-backed 资料发布于正式提交 `185e52c0d6bb4766b0821e5f356091f709476df9`（origin/master，2026-10-11 fetch 后仍为该提交，无新增成果），但 OSS 加速源索引仅 466 份（缺 47）。前端 `fetchSchoolJSON` 生产环境优先读 OSS、命中旧 JSON 不回退主站，故只推 Git 不构成发布。本阶段仅修复已发布资料的送达，不重新研究这 47 人，不计为新增研究成果。

同步对象限定为正式提交内的作者 JSON：`philosopher/data/*.json`、`philosopher/editorial/*.json`、`philosopher/catalog.json`、`philosopher/editorial-index.json`、`philosophers.json`（LFS，从本地 LFS 存储取真实内容并校验 sha256）、`philosopher/portrait-audit.json`（快照中若存在）。未上传学校背景、肖像图、书籍、章节与构建产物，未更改桶权限或缓存策略。

## 执行方式

- 全部字节经 `git cat-file` 从正式提交读取（工作区尚有未提交的叶芝资料，未做任何整目录同步）；唯一例外 `philosophers.json` 经 `git lfs fetch origin master --include=app/public/philosophers.json` 取回 LFS 对象（仅下载，不触碰工作树），上传前校验 sha256 与 size。
- 增量对比：OSS ListObjects 取 ETag（md5），仅上传缺失或内容不同者，`Content-Type: application/json`。
- 工具：一次性脚本存放于仓库外 `/tmp/dp-release-20261011/`（sync_philosopher_oss_20261011.py、verify_oss_sync_20261011.py；本任务守卫将 `backend/tools/_tmp/` 列为越界路径，故不入树，随用随删）。

## 上传结果

| 项目 | 数量 |
|---|---:|
| 快照内对象（data 773 + editorial 513 + catalog/索引/philosophers/portrait-audit 4） | 1290 |
| OSS 远端对象（同步前） | 2010 |
| 需上传（缺失或内容不同） | 116 |
| 其中47人相关（data+editorial 成对 47×2） | 94 |
| 其余为 catalog.json、editorial-index.json、philosophers.json 及19个已修复旧包的内容差异 | 22 |
| 上传成功 | 116 |
| 上传失败 | 0 |

上传清单见同目录 `2026-10-11-oss-sync-receipt.json`（syncedAt 2026-10-11T04:48:54Z，failed 为空）。

## 发布验收（2026-10-11）

1. **两端索引一致**：`philosopher/editorial-index.json` 在正式提交、主站 `deepphilosophy.top`、OSS 三端 `coverage.levels.source-backed` 均为 **513**，profiles 均 513 条，**姓名集合完全一致**；索引 updatedAt 均为 2026-10-10。
2. **抽查详情一致**：歌德、科林·豪森、彼得·厄巴哈三人的 OSS `philosopher/data/*.json` 与正式提交字节一致（md5 相同），且 `profile.editorial`、来源（sources）、阅读路线（readingRoutes）齐全。
3. 快照 SHA、索引日期、两端数量、上传清单与抽查结果均已保存于本文件及回执 JSON。

验收脚本：`/tmp/dp-release-20261011/verify_oss_sync_20261011.py`，结果 **PASS**。

## 批次管线中发现的既有缺陷（未修复，记遗留）

- `scripts/test_author_assets.py` 22 例中 21 过 1 败：`test_no_autographs_are_not_invented_to_fill_the_bibliography` 报 **安提斯泰尼**（已发布包，w9 批次）`worksPolicy=no-autographs` 但书目两篇存世演说辞（《阿贾克斯》《奥德赛》）`kind:authored`，违反项目硬门禁。该失败在未做任何本地修改的 HEAD（=已发布主线 185e52c0d 状态）即复现，与叶芝无关。
- 已尝试最小修正（`worksPolicy` → `authored`，对照已发布先例查士丁；仅改标签与 evidenceLimits 中一处短语），被 `guard_author_quality_worktree.py` 以「越权改写已完成资料包」拦截——安提斯泰尼不在 `worktree-lock.json` 的 `repairExistingPackets` 白名单，按纪律不改检查器或锁文件放行，修改已撤回、工作树复原。
- **遗留修复建议**（供白名单内授权轮执行）：editorial 包 `worksPolicy` 改 `authored`；evidenceLimits 中「著作60余部无一完整传世（仅存两篇短篇演说辞），worksPolicy=no-autographs。」改为「仅两篇短篇演说辞完整传世（worksPolicy=authored），其余60余部著作全部已佚。」；重跑 `sync_author_catalog.py` + `test_author_assets.py`。依据：IEP（Julie Piering）§1 确认两篇演说辞完整存世；标准文档「无亲笔著作者标明 no-autographs」不适用。

## 结论

已发布 513 份资料在 Git、主站、OSS 三端可达且一致；47 份加速源缺口闭合。本阶段不改变 source-backed 计数（仍为 513），叶芝发布后应为 514。
