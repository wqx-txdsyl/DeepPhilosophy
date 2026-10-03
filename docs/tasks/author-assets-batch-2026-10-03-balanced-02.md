# 哲学家资料资产批次报告 · 2026-10-03-balanced-02

执行环境：`/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（分支见台账），基线 `9fde01017`。执行日期：2026-10-03。

## 1. 批次构成（15 人，5/5/5）

| 地域组 | 人物 |
|---|---|
| 古希腊与欧洲思想 | 托马斯·阿奎那、巴鲁赫·斯宾诺莎、大卫·休谟、约翰·斯图尔特·密尔、西蒙娜·德·波伏娃 |
| 东亚思想 | 慧能、韩非、孙武、宗喀巴·罗桑扎巴、道元 |
| 南亚、伊斯兰、非洲、拉美与原住民传统 | 安萨里、法拉比、帕坦伽利、世亲、弗雷德里克·道格拉斯 |

分组理由：跨世代与跨传统均衡（欧洲组覆盖13–20世纪含1位女性；东亚组覆盖先秦/唐/宋元/日本镰仓/藏传；第三组覆盖伊斯兰×2、南亚×2、非洲离散×1）。道格拉斯按非洲离散思想与美国19世纪思想史语境归入第三组。冻结批次 `2026-10-03-balanced-01`（30人）与海德格尔基准未触碰，新增测试保证新批次不复用冻结批次 ID。

特殊情形覆盖：无肖像（道元，页面正确回退思想背景图）、无自著（慧能 no-autographs，书目全 testimony）、稀少史料（孙武/帕坦伽利/世亲 limited-evidence）、长姓名（宗喀巴·罗桑扎巴，页面正确分两行）、无站内书（帕坦伽利/道元等，页面显示书目信息与来源）、站外相关人物（多条，页面走来源入口）。

## 2. 阶段 A 工具改进（先于扩充完成）

- `audit_author_assets.py` 与 `sync_author_catalog.py` 新增 `--date` 参数（默认当天）；同参数重跑输出幂等，历史基线文件不重写。验证：以历史日期（2026-10-02/2026-10-03）重跑，`author-content-audit.json`、`author-assets-audit.json`、`editorial-index.json` 与提交版零差异。
- 审计新增争议一致性约束：`debateAssessment=included` 必须有 debate 正文；非 included 不得有正文。
- `test_author_assets.py` 新增 6 类语义测试：关系端点可解析且不指向待核实人物、别名无链无环且目标存在、书籍 ID 存在于 books.json、no-autographs 不列自著/合著/编订、新批次与冻结批次隔离、争议评估一致性负例。
- 数据清理：philosophers.json 中 92 条悬空书籍引用（id 不存在于 books.json）——84 条按同题同作者修复为新 ID，8 条移除（苏格拉底 TXT 占位"论自然"、马克思《神圣家族》合著署名串不解析、马赫名下 2 条错误归属《基督教信仰》《论宗教》实为施莱尔马赫著作、列维纳斯 2 条已由 sync 按作者变体自动回补正确 ID）。移除项在 UI 上的行为与清理前一致（死链从不显示）。

## 3. 研究与复核方法

每人流程：身份核实 → 实际查阅来源（WebFetch 定向阅读，共 94 条来源记录、93 个不同 URL，含 SEP/IEP/原典影印与出版页/档案库）→ 证据记录（`docs/author-research/2026-10-03-balanced-02/<人名>.json`，合计 477 项逐条 checks，verdict 分 confirmed/corrected/uncertain，167 项不确定点如实记录）→ 草稿（drafts/ 目录，不进公开 editorial/）→ 独立第二轮复核（5 个复核代理重访来源，修正后才晋升）。复核实际发现并修正的错误包括：慧能书目误题译 者（哥大 2012 实为 Yampolsky 1967 重刊）、道元"携《碧岩录》东传"由史实改按传说、道格拉斯科维搏斗年份与子女人数、密尔"华兹华斯会面"实为卡莱尔、宗喀巴两处文本损坏与无据断语、安萨里对阿维森纳关系的伪引文改述等。

## 4. 内容规模与政策

129 个时间节点、90 项概念、81 条书目、80 条关系、43 条阅读路径；15 人全部有争议评估（included）且正文有据。政策分布：documented×10 / limited-evidence×5；authored×10 / no-autographs×1（慧能）/ single-surviving-corpus×3（韩非/孙武/帕坦伽利）。关键身份修正：宗喀巴 era→1357-1419、道格拉斯 era→约1818-1895、阿奎那 era→约1225—1274、安萨里生年两系并陈、法拉比生年→约870、帕坦伽利身份分层（个人不可考）。

## 5. 验证结果

- 结构：15/15 `source-backed`；audit 全目录 46 source-backed / 606 needs-review（原 621）。
- 测试：`test_author_assets.py` 13/13；`node --test` 27/27；`npm --prefix app run build` 成功（OSS 资产改写正常）。
- 校验：`sync_school_catalog.py --check`、`sync_genealogy_catalog.py --check` 通过；`git diff --check` 干净。
- 幂等：同日期重跑 sync+school sync+audit，四个聚合文件哈希一致。
- 保护：既有 31 份 editorial 零改动；冻结批次 10/10/10 不变；35 个旧名别名入口可解析；旧编译详情除书籍清理与 era 修正外无漂移；schools/catalog.json 差异仅为本批 13 人 era 修正的传播。
- 页面抽查（dev server）：桌面 1280（道元、宗喀巴）+ 移动 390（帕坦伽利、波伏娃），结构齐全（7 章节/背景图回退/长姓名换行/争议模块），视觉模型 QA 判定布局合格（轻微水印叠压为既有设计特征，非本批回归）。

## 6. 遗留不确定点（择要）

生年约数（阿奎那 1224–1226、密尔 1879 连载细节、波伏娃两卷出版月日）；史料性质已分层但不可确证项（韩非下狱细节为《史记》单一叙事、孙武生平整体、慧能早年叙事、《建撕记》性质）；部分出版页/档案页 403 仅摘要级访问（已在证据记录 readScope 如实标注）；本批 15 人肖像均未核验（portrait-audit 无记录，按 unverified 记录）。

## 7. 发布状态：待发布（validated-not-published）

本批已全部通过本地验证并提交至工作分支；Cloudflare 预览构建与 OSS 同步未执行（无本环境可用的部署 URL 与 OSS 凭证确认）。发布时按任务书第 9 节执行：

```sh
python backend/tools/dp_grab_cf_assets.py <实际成功的CF部署URL>
python backend/tools/dp_sync_oss_static.py --only=philosophers.json,philosopher/catalog.json,philosopher/data,philosopher/editorial,philosopher/editorial-index.json,philosopher/portrait-audit.json,schools/catalog.json,app/assets
python backend/tools/dp_grab_cf_assets.py <实际成功的CF部署URL> --verify-only
```

核验要求：生产 HTML `dp-commit` 对应预期提交；本批 15 人 JSON 在 CF 与 OSS 两端一致；页面实际加载新版资料。本批无新增/修正肖像，肖像 key 不入同步范围。

## 8. 剩余队列

thinkersToComplete 606；identitiesToResolve 26（未开始）；contextToReview 59（未开始）；既有 31 份继续保护。下一批建议：优先女性与未覆盖地域（玛莎·努斯鲍姆等）、琐罗亚斯德（limited-evidence 深水区）、密尔之外的全空记录（米歇尔·福柯等）。
