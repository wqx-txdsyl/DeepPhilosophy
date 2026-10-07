# 哲学家肖像审计 · 独立会话任务书（portrait-audit zcode）

交接日期：2026-10-07。本文件是**肖像审计专门会话**的唯一权威入口，与批次任务书（`philosopher-assets-continuation-zcode.md`）并行、互不阻塞。

## 1. 可直接复制给新会话的启动指令

> 请执行本仓库 `docs/tasks/philosopher-portrait-audit-zcode.md`。先读它，再读 `AGENTS.md`。工作分支 `codex/philosopher-assets-balanced-02`，工作区 `/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（git worktree；**不要碰** `/Users/sen/DeepPhilosophy`）。按第 3 节优先级逐批核对哲学家头像，向 `app/public/philosopher/portrait-audit.json` 追加停显记录，精确 pathspec 提交推送。不改任何 editorial 包，不跑批次管线。

## 2. 背景与机制（必读）

- 站内哲学家页头像 = `app/public/philosopher/<人名>.webp`；`app/public/philosopher/portrait-audit.json`（schemaVersion/scope/records）是**停显机制**：一条 `{"allowAsPortrait": false, "reviewedAt": "…", "path": "/philosopher/<人名>.webp", "reason": "…"}` 记录即让前端停止把该图当头像展示，**原文件保留不删**（先例：露西·伊利格瑞、智顗、铿迪、苏赫拉瓦迪、金·斯科特等）。
- 该文件随批次发布的 OSS 流程同步（`philosopher/portrait-audit.json` 在 --only 清单内），线上生效已验证（金·斯科特案例 OSS allowAsPortrait=false 生效）。
- 台账 `docs/tasks/philosopher-assets-progress.json` 的 `people[<名>].portraitStatus` 字段记录个人结论（先例：`mismatch-hidden-2026-10-07`、`unverified-checked-2026-10-04`）。
- **既有 360+ 包零改动是批次会话的不变式**：审计会话只改 `portrait-audit.json` 与台账 `portraitStatus` 字段，**绝不碰 editorial/、philosopher/data/、philosophers.json、scripts/**。

## 3. 工作范围与优先级（共 375 个已上线包，按此顺序）

1. **最高优先——身份纠正过的人物**（legacy 曾错配，旧图大概率是错人）：金·斯科特（已停显，核复影）、伊万娜·格巴拉、马丁-巴罗、特蕾西亚·特埃瓦（批次25 在途）等，凡台账 `identityFindings`/包内 `identity.verdict=corrected` 者。
2. **在世人物**：照片必须是本人可核实的公开照片（当代摄影); era/性别/族裔明显不符即停显。
3. **无存世真容的古代/中世纪人物**：雕塑/镶嵌画/手抄本插图/后世绘画可以接受，但须是**传统上被认为描绘此人**的作品；明显的他人作品、虚构形象、无关风景/符号题材即停显（伊利格瑞「斯芬克斯绘画」先例）。
4. **近世人物（有摄影术前后的）**：照片/版画年代与人物生卒冲突、性别/年龄明显不符即停显。
5. 其余抽查。

判定素材：各包 `identity.era`、`profile.life`、包内 sources 描述、维基共享资源等公开图库的原始说明（只作判断参考，不必写入包内）。**只判「这张图当此人头像是否可信」，不判艺术质量。**

## 4. 操作规范

- 每停显一张：向 `portrait-audit.json` 追加一条记录（reason 写明所见与依据，一句话即可），台账 `people[<名>].portraitStatus` 写 `mismatch-hidden-<日期>`；两个文件一次提交。
- 提交规范：精确 pathspec（只 add 这两个文件），`git commit -F <文件>`，message 形如 `fix: 肖像停显 N 张（<名单摘要>）`；push 分支。**不需要跑管线/构建**（portrait-audit.json 不进构建），但如需立即线上生效，可按批次任务书第 6 节跑 OSS 单文件同步（`dp_sync_oss_static.py --only=philosopher/portrait-audit.json`，.env 用完即删）。
- 汇报：每完成 50 张左右汇报一次（数字+停显名单），失败汇总整表随汇报。
- 硬过滤纪律：素拉·西瓦拉克相关页面**禁止任何在线抓取**（只看本地文件判断）。

## 5. 完成定义

- 375 包全覆盖一遍（允许分多轮），每张图结论 ∈ {可信, 停显(+reason)}；台账 portraitStatus 全部落值。
- 终态写 `docs/tasks/portrait-audit-report.md`（总数/停显数/典型案例/未决项）。
- 若批次会话同日发布新批（新增 15 张），下一轮补审即可，不需等待。
