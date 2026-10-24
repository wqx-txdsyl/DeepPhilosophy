# 任务B goal 建立回执 · 2026-10-24

- sessionId：`session_5757f4968c76d3c94837635a635082a7`（ZCode 桌面端会话，工作目录 /Users/sen/DeepPhilosophy）
- goalId：平台未提供独立 goalId 字段；goal 由官方 `/goal` 命令建立，运行时已回执 active 状态与预算（Time 0s / Token budget none），并由 goal-continuation 系统提醒持续跟踪。
- goal 原文：用户以 `/goal` 逐字粘贴 launch-b.txt 全文（与任务B派发文本一致），要点：先重算历史真实缺口/版本分叉/357项应收未录现状→逐人补齐→完整实读全部现有及新增人物前台正文→谱系同等标准改写→逐人逐字段台账→每完成一人简报并继续→测试、正式发布、主站/OSS验收后才算完成→真实阻断留证，上下文结束保存精确游标。
- goal 状态：active（运行时完成核验器在每轮后检查；不以待办代替 goal）。
- 工作区：`/Users/sen/.zcode/worktrees/zcode-readable-b-20261024/DeepPhilosophy`
- 分支：`zcode-readable-b-20261024`（基点 `bca495412` = 清理分支3a29bb3b0 之后、含最新书库工作；master 独有13提交不触作者数据）
- 基线：线上生产 philosophers.json = 639 条，SHA256 前8 `6529c953`，与清理工作区当前文件逐字节一致；主检出 737 为历史目录（未部署，不回灌）。
- 只读输入：`/Users/sen/.codex/worktrees/author-quality-zcode-20261009/DeepPhilosophy`（锁 owner：Codex completion 2026-10-20，只读）。
- 首个对象：老普林尼（基础资料缺口：无 editorial 包，overview/life/concepts/bibliography/readingRoutes/editorial-review 缺）。

## B0 对账结论（重算）

| 集合 | 数量 | 说明 |
|---|---:|---|
| 现有保留哲人 | 639 | 线上=清理版；637 有 editorial 包 |
| 基础资料缺口 | 2 | 老普林尼、李斯（无 editorial） |
| 来源/编辑未过（needs-review） | 319 | 逐人全读时处理，不作为免读理由 |
| debate 缺失 | 22 | 逐人判断是否需要补 |
| 旧缺口独立条目 | 5 | 希帕基娅、何维勒(Revel)、理查德(Ricard)、斯通普夫、菲泽 |
| 周龙辉 | 1 | 3项具体未完来源+17条门禁问题 |
| 应收未录建议 | 357 | P1 190 / P2 167；对639+33别名去重复核无一被吸收；8个名称部分重合均为同名异人 |
| 边界待议（不计入） | 18 | 未经裁决不算新增哲学家 |
| 旧 492/549/99/30/59 等历史数 | — | 仅追溯；本轮一律以重算集合为准，任何当前正文不免读 |

数据管线：改 `app/public/philosopher/editorial/{name}.json`（海德格尔特例改 `scripts/author-curation/heidegger.json`）→ `python3 scripts/sync_author_catalog.py` 再生 data/*/philosophers.json bio/catalog/editorial-index/retiredAuthors.js/authorArtworkVersions.js。前端消费：AuthorDetailPage.jsx（question/overview/life/concepts(name,original,definition,source)/people/relations(label,detail)/bibliography(description)/readingRoutes/debate(title,year,paragraphs)/sources(标题链接)）、authorContent.js（bio→SEO 160字、books）、AuthorsPage.jsx（name/englishName/country/school/era 搜索）。

固定复核点现状（2026-10-24 核）：弗洛姆 source-backed 身份已确认（不返工，入普通全读）；安提斯泰尼 source-backed 作品policy已修（同上）；Jaynes 区分已解决（仅存朱利安·杰恩斯，埃德温已退役）；老普林尼/李斯仍缺 editorial（本轮首两项）；周龙辉 needs-review 未完来源3项仍在；Revel/Ricard/希帕基娅/斯通普夫/菲泽确认缺席，本轮建独立条目。
