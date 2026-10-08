# 批次报告：2026-10-09-sample-five（第二阶段：五项执行样本）

日期：2026-10-09。执行：ZCode（zcode-main），分支 `codex/zcode-author-quality-20261009`。

## 交付概览

五份新人物包全部 source-backed（editorial-index 441 = 436 + 5），全部通过新来源门禁（accessScope + 证据记录 + locator 检查）：

| 人物 | 区域 | 学理来源（实读） | 备注 |
|---|---|---|---|
| 阿尔贝·加缪 | 西方 | SEP（Aronson，2021修订）+ IEP，双全条目通读 | 任务书点名者；不在原队列（台账缺口），无既有包、未被他任务完成，按 canonical 键『阿尔贝·加缪』领取完成 |
| 伏尔泰 | 西方 | SEP（J. B. Shank，©2024）全条目 + 维基文库《老实人》英译第1/30章原文 + 法语维基文库《论宽容》著作著录页 | 出生/卒日月日、1717年巴士底等日级事实按通行记载处理不写确定句 |
| 希拉里·普特南 | 西方 | 卫报讣闻（O'Grady）+ SEP Functionalism + SEP Scientific Realism + Philosophy Now（Baghramian） | SEP/IEP 均无专条（404×2，如实记录），学理锚点改用关联条目 |
| 苏加诺 | 世界 | Loc《Indonesia: A Country Study》§14/16/19/20 + ANU Press 学术章节（Lin Hongxuan）+ 1926年《民族主义、伊斯兰与马克思主义》英译全文（转载页，McVey译标注）+ UNS 制宪综述（学生论文层如实标注） | 1965-70段核读时 WebFetch 触发内容过滤（1301），不重试；按通行记载降级并记入 uncertainties |
| 杨献珍 | 东方 | 《学习时报》/人民网转载文（魏建国，GB转码全文）+ 张法《共和国前期四大哲学家》（cssn，全文） | 检索两次触发 1301 后改关键词完成；张法全文为 http 转载页，正式包登记 https 题录页（浙师大主页）并双通道如实注明；两源关于『思维与存在同一性』立场表述相反，按学术叙述处理并并注 |

## 门禁运行情况

- 全量 CLI：gatedPackets=13（8 修复包 + 5 新包），failures={}。
- 新门禁拦截实效：伏尔泰（Loc国别研究 http→Wayback https 快照改道）、苏加诺（同）、杨献珍（cssn http→https 题录页双通道登记）——三个 http 来源问题在写入阶段即被审计/门禁拦下并按诚实方式解决。

## 访问受限与阻断（如实）

- 1301 内容过滤共 4 次：苏加诺 1965-70 段（Loc §21）、杨献珍相关检索×2、阳明大学「一分为二」研究页。均按任务书 §6 处理：不重试、检查点落盘、相关断言按通行记载降级、不作掩盖。
- 403 未读：Britannica（伏尔泰/苏加诺）、Harvard 讣闻页、USC Dornsife 详报（坎芙，前一批次）、UMY 页、OLL 页、HathiTrust。均有等价来源替代或如实降级。
- 苏加诺 packet 的毕业/创党年份两系并存（Loc vs 通行系年），正文采用无冲突表述并注。

## 检查与发布

管线全绿：guard --check ✓ / sync ✓ / audit（--date 2026-10-09）✓ 441 source-backed / test_author_assets 22 ✓ / node 9 ✓ / build ✓ / school+genealogy check ✓ / diff --check ✓ / publish-check ✓。
发布：本分支提交后 `git push origin HEAD:master`（授权发布），CF Pages 由主线触发。

## 用量与限额

无真实跨模型用量数据，不发明数字。本批产出：5 份新 source-backed 包 + 证据/草稿/检查点各 5 套。

## 下一对象

按任务书 §5 继续阶段 3：从 thinkersToComplete 未受阻对象按缺口推进（建议下一批从西方高分未完成者开始：施莱尔马赫、马尔库塞、斯宾塞、涂尔干、桑德尔、麦金泰尔等），并行穿插 26 项身份核查与 59 项背景审读。
