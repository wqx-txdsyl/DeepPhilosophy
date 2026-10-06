# 宗教七教条目审计扩充任务书 · 2026-10-06

## 0. 直接复制给执行者的启动指令

> 请执行 `docs/tasks/religion-expansion-audit-2026-10-06.md`。任务：更多频道（/more）的七个宗教条目（佛教、道教、印度教、伊斯兰教、天主教、东正教、基督新教）数据量普遍不足，按本任务书的量化目标逐条充实，标准以 `religion/buddhism.js`（41KB，首例数据）为下限、以流派管线（docs/content-proposals 与 docs/tasks/school-content-expansion-zcode-2026-10-04.md）的研究纪律为准绳。只改 `app/src/data/moreTopics/religion/*.js` 七个文件，不改组件、不改其他模块。完成后 node --test 全绿、vite build 通过、报告各项前后对比。

## 1. 背景与基准

- 位置：`app/src/data/moreTopics/religion/{buddhism,taoism,hinduism,islam,catholic,orthodox,protestant}.js`，由 `app/src/components/more/ReligionDetail.jsx` 渲染。
- **注意：宗教模块没有 expand 合并机制**（神话体系才有），充实直接写入主模块文件。
- 基准：`buddhism.js`（41,090 字节）是首例数据，字段最全；但按用户要求"全部数据量均不足"，**佛教自身也在扩充范围内**（overview 仅 1315 字，低于神话基准 2400 字）。

## 2. 量化诊断（2026-10-06 实测）

| 教 | 文件 | overview | lineage | doctrines | scriptures | rituals | branches | bridges | keywords |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 佛教（基准下限） | 41KB | 1315字 | 2292B | 5021B | 1833B | 1626B | 2277B | 1367B | 40 |
| 道教 | 13.8KB | 667B | 997B | 1069B | 798B | 528B | 541B | 603B | 20 |
| 印度教 | 10.7KB | 490B | 645B | 1052B | 461B | 462B | 430B | 385B | 20 |
| 伊斯兰教 | 18.7KB | 871B | 1182B | 2044B | 569B | 813B | 613B | 760B | 20 |
| 天主教 | 19.9KB | 761B | 1330B | 1867B | 976B | 1004B | 895B | 778B | 20 |
| 东正教 | 19.0KB | 825B | 1278B | 2023B | 787B | 744B | 872B | 716B | 20 |
| 基督新教 | 16.5KB | 954B | 1010B | 1069B | 554B | 516B | 939B | 784B | 20 |

**结论**：六教各字段只有佛教基准的 1/4 到 1/2；佛教的 overview/keywords 也低于神话体系基准（2400字/38+）。

## 3. 字段契约（ReligionDetail 实际渲染）

| 字段 | 结构 | 充实要求（按教分别达到） |
|---|---|---|
| `overview` | {lead[3段], sections[{title,paras}]} | ≥2400 字、lead 3 段 + 4-6 个专题节（对标神话体系）；开头进入具体文本/场景/人物，不用定义式套话 |
| `lineage` | {intro, …历史脉络条目} | ≥2200B：从创立到当代的完整史线，含关键分裂/会议/改革节点 |
| `doctrines` | {intro, …教义条目} | ≥4500B：核心教义逐条立目（条目含 name/description，有经证给经证），内部学派分歧如实 |
| `scriptures` | {intro, …经卷条目} | ≥1800B：正典形成史+各经卷条目（成书、结构、地位、译本史） |
| `rituals` | {intro, …仪轨条目} | ≥1600B：每条 {name, purpose, era, regions, description}——礼仪的意义写出来，不是流程清单 |
| `branches` | {intro, …宗派条目} | ≥2200B：每条 {name, era, regions, coreBelief, distinction, description}——教派间差异用" dist­inction 一句话说清"标准 |
| `bridges` | {intro, …勾连条目} | ≥1400B：与哲学的实质勾连（对哲学问题的回答/争论），links 指向站内真实流派/哲学家（atlas.json 与 philosophers.json 实存名） |
| `keywords` + `keywordGlosses` + `keywordTargets` | 数组/映射 | ≥38 组，glosses 是写给读者的 2-3 句释义，targets 指向页面内真实锚点/条目 id（无死链） |
| `crossLinks` | {schools[], authors[], books[]} | 指向站内实存条目；站内未收录的书注明"站内未收录" |
| `epilogue` | 字符串 | 一段有收束力的结语，不写展望式空话 |

具体字段名以 `buddhism.js` 现有结构为准（它是渲染通过的活例）——**保持键名与结构不变，只做增补与改写**。

## 4. 各教专题建议（出发点，执行者可按档案调整）

- **佛教**：overview 补部派-大乘-密教-南传的传播史专题与"佛教是否是宗教"的现代争论；doctrines 补因明/中观/唯识/如来藏的论证书维度；scriptures 补巴利三藏/汉译/藏译三大正典系统；branches 补南传上座部/汉传/藏传/日本佛教的现代形态。
- **道教**：从 667B 起步，量最大。覆盖：道家与道教之辨、正一/全真两大教团、丹道南宗北宗、斋醮科仪、《道藏》形成史、民间信仰边界。
- **印度教**：最薄（430-645B）。覆盖：吠陀祭祀→婆罗门教→印度教的转型、六派哲学、毗湿奴/湿婆/萨克蒂三大教派、《薄伽梵歌》的行动伦理、种姓与改革的现代争论（以证据呈现各方）。
- **伊斯兰教**：逊尼/什叶分裂的起源与教义差异、五功与六信、四大法学派、苏非主义、伊斯兰黄金时代的哲学（法拉比-阿维森纳-阿威罗伊，links 指向站内伊斯兰哲学）。
- **基督教三教**（建议同一执行者完成以保证口径一致）：东西教会大分裂 1054、宗教改革 1517 的教义分歧点（因信称义、圣传地位、圣事数目）、各自信经（使徒/尼西亚）、圣餐观的三大立场、政教关系的不同传统。三教条目交叉引用、避免重复叙事——用"详见天主教条目"式的站内互链。

## 5. 研究与文风纪律（违反=不合格）

1. **来源**：每条重要断言有据可查。原典章节级引用（如"《古兰经》2:255""《尼西亚信经》325 年"）；扩充前用 WebFetch 实际核读（Bible Gateway、Quran.com、sacred-texts、Britannica、Stanford Encyclopedia of Philosophy 的宗教条目、维基文库）。禁止凭记忆写教义细节。
2. **活态宗教敏感性**：这是七条与神话体系的根本区别——它们是活着的信仰。①各传统自称与学术称谓并举（"穆斯林自称……学术上称……"）；②教内多样性如实（逊尼什叶、公会议与泛正教、福音派与主流派）；③争议以证据呈现各方（如梵蒂冈一百年争论、女性圣职各派立场），不裁断信仰真伪；④不嘲讽、不布道、不用"迷信"等贬词；⑤政治敏感处（政教关系、当代冲突）以史学证据呈现、不作立场判断。
3. **文风**：与全站流派管线一致——写给读者的连贯散文，零元话语（本条目/站内/边界辨析/证据限度等审稿语言禁用）；学术分歧改写成叙述；判断有锋芒；开篇从具体文本/场景/人物切入。
4. **事实红线**：禁止新增核读材料之外的人物、年代、经文引语；经文引语逐字核对（给出处）；拿不准就不写。
5. **结构红线**：保持 buddhism.js 的键名与结构；不增删顶层字段；不修改 ReligionDetail 组件；crossLinks/bridges links 只指向站内实存条目。

## 6. 工作流与验收

1. **批次建议**：4 批——①佛教（补自身短板：overview/keywords）②道教+印度教（量最大）③伊斯兰教 ④基督教三教（同一人做）。每批完成即校验。
2. **自检**：每条完成后 ①`node --check` 通过；②用 vite ssrLoadModule 加载并复测各字段字节数达标（§3 表）；③元话语词表扫描清零；④links/glosses/targets 无死链。
3. **全局验收**：`node --test tests/*.test.mjs` 全绿；`npx vite build` 通过；`git add app/src/data/moreTopics/religion` 精确提交；推送 master 部署；`dp_sync_oss_static.py` 同步（宗教数据打进 JS bundle，构建资产走 OSS）。
4. **最终报告**：各教前后字节数对比表、各字段达标情况、实际核读 URL 清单、修正的既有错误、敏感内容的处理说明。

## 7. 边界

- 只改 `app/src/data/moreTopics/religion/*.js` 七个文件。ReligionDetail.jsx / MorePage.jsx / 路由 / 其他模块不动。
- 与神话体系共用 hero 图目录 `app/public/more/`，宗教 hero 图已就位，不需要新增图片。
- 文风规范全文见 `/tmp/rewrite_style.md` 已失效，按本任务书 §5.3 执行；神话管线的同款范文见 `docs/tasks/religion-expansion-audit-2026-10-06.md` 附录（中国神话 overview 文本已在站内 `moreTopics/chineseMythology/overview.js` 可直接读取作对照）。
