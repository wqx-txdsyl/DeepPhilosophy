# P02 自然主义（Naturalism）· 立场资料包 — 复核记录

- 任务：P02（group 哲学立场入口，kind=position，coverage=related-branches-only）
- reviewedAt：2026-10-04
- 复核方法：WebFetch / web_reader 逐源实读（见下"实际核读 URL 清单"），非仅检索摘要；关键引语、年代、书目逐条回查原文定位；人物姓名与书籍 ID 用 python3 grep 站内 `philosophers.json` / `books.json` / `philosopher/data/*.json` / `school_分析哲学.json` 核对。本包为编辑自检，未做独立同行评审。

## 1. 目录处置

- P02 目录此前不存在（同日并行各包均已建，P02 为空），本次全新撰写四个文件，无旧稿需要取舍。
- 主仓库 /Users/sen/DeepPhilosophy 未触碰；仅写入 `docs/content-proposals/schools/P02/`，无任何 git 写操作。

## 2. 范围与边界决定

1. **与 P01 唯物主义/物理主义包（同日并行）的辨析接口**：本包以已核证据写明——不列颠百科：唯物主义是自然主义的，反之不必真；自然主义"没有本体论偏好"，甚至出现过"有神论自然主义"（S6）；SEP 主线则从物理因果封闭走向"彻底的物理主义"（S1）。分工：强本体论论题与物理主义论证细部归 P01；本包处理立场族总谱系、方法论/本体论两维度、杜威一系与自由意志自然主义。P01 稿件未读到，接口按任务书与本包证据写明，不猜测对方内容。
2. **与站内既有分支的分工**：`school_分析哲学.json` 已有分支"自然主义与整体论"（index 3，era"20世纪中叶起"）。本包不重复其分析哲学内部叙事，扩展为立场总览（杜威线、两维度之分、当代自由意志自然主义），建议互链。注意该分支文案用"奎因"、站内人物页用"蒯因"（威拉德·范·奥曼·蒯因），已在 proposal 建议统一。
3. **排除项**：任务 evidence.excludedLexicalMatches 所列"超验主义-梭罗式简朴自然主义"不计为已有分支，本包不覆盖；宗教研究/科学-宗教之争中的"方法论自然主义"用法只作界说提及（S1 交代后搁置的用法照实转述）；道德自然主义、非西方传统的"自然主义"标签（如荀子"天行有常"式解读）不入包——不凑东西方配额，也无证据基础。
4. **人物取舍**：thinkers 收 5 人（休谟、杜威、蒯因、丹尼特、帕皮诺），均在 4—8 区间。欧内斯特·内格尔、胡克、罗伊·伍德·塞拉斯、伍德布里奇、莫里斯·科恩只入时间线/概述（S1 点名自称自然主义者、S6 点名运动成员，但其余信息未核，不单列以免空壳条目）。**勿与站内"托马斯·内格尔"（Thomas Nagel, 1937— ）混淆——本包内格尔是欧内斯特·内格尔（Ernest Nagel, 1901— ），站内无其人物页。**
5. **站内姓名核对结果**（grep philosophers.json）：威拉德·范·奥曼·蒯因、约翰·杜威、大卫·休谟、丹尼尔·丹尼特、托马斯·内格尔在站；帕皮诺（David Papineau）不在站，thinkers 用中文通行译名附英文原名。生卒年：杜威 1859—1952（S3 正文亦证）；休谟 1711—1776、蒯因 1908—2000、丹尼特"20世纪至21世纪"取站内 philosopher data 口径。

## 3. 来源分歧记录

- **自然主义与物理主义的关系**：SEP（S1，帕皮诺）持窄读法（因果封闭引向物理主义）；不列颠百科（S6）持宽读法（无本体论偏好、可兼容二元论/有神论自然主义）。两说并存写入 overview 内部差异，并在 conclusion/P01 接口处明示张力。
- **杜威自称标签**：SEP（S3）用"文化自然主义"（cultural naturalism），并给出"实在论的、自然主义的、非还原的、涌现论的、过程的"概括；任务书所提"经验自然主义"（empirical naturalism）未能在可核原文中定位（见 §5），正文未采用。
- SEP 'Naturalism'（S1）与 SEP Naturalism in Epistemology（S2）分工：S1 基本不讨论蒯因自然化认识论（本次核读确认），蒯因材料全部取自 S2/S4——两包内容不互相转抄。

## 4. 实际核读 URL 清单（2026-10-04）

| id | URL | 状态 |
|---|---|---|
| S1 | https://plato.stanford.edu/entries/naturalism/ | 已读（Papineau 撰；2007 首发/2020-03-31 修订） |
| S2 | https://plato.stanford.edu/entries/epistemology-naturalized/ | 已读（2016-01-08 首发/2020-03-16 修订） |
| S3 | https://plato.stanford.edu/entries/dewey/ | 已读两次（第二次窄问询确认 'empirical naturalism' 不见于条目） |
| S4 | https://plato.stanford.edu/entries/quine/ | 已读（2010-04-09 首发/2023-07-06 修订） |
| S5 | https://plato.stanford.edu/entries/compatibilism/ | 已读（2004-04-26 首发/2024-04-16 修订） |
| S6 | https://www.britannica.com/topic/naturalism-philosophy | 已读（WebFetch 403 后经 web_reader 完整读取正文） |
| S7 | https://archive.org/stream/experiencenature00dewe_0/experiencenature00dewe_0_djvu.txt | 已读（1925 Open Court 版书名页+首章全文） |

搜索中另发现但**未采用**（未实读或读后无产出）：iep.utm.edu/naturalism（404 两次）；archive.org 1929 版（借阅制，全文不可读）；Project Gutenberg 无杜威《经验与自然》（eBook 71008 实读为误配书目，已弃）。Britannica 早期两次抓取仅返回截断元描述，其后才完整读得——最终稿只使用完整读得的内容；中途一次对 Britannica 细节（1930—40 年代名单等）的过早断言已在写入前纠正。

## 5. 仍缺证据 / 证据限度（与 packet.evidenceLimits 一致）

1. **"经验自然主义（empirical naturalism）"**：1925 版首章全文核对为否定性发现（不含该连字标签）；其常被系于 1929 修订版导言，archive.org 1929 版为借阅制无法打开。正文与术语条目均不把它用作杜威自称，仅存疑。
2. **帕皮诺**：生卒年与本人自由意志具体立场未核实（SEP 'Compatibilism' 未提 Papineau）；本包只把因果封闭论证归于他（自撰条目，归属可靠）。任务"如可核"的保留条件即落于此。
3. 休谟具体著述（《人性论》等）未在已核来源出现，thinkers.works 留空。
4. 站内两本蒯因中译本的译者/出版社未核实，works 只注原题与版本线索；丹尼特 Elbow Room 的通行中译名待编辑部确认。
5. SEP 'Naturalism in Epistemology' 与 'John Dewey' 条目作者名未在可见页面确认（推断值不写入）。

## 6. 质量自检

- 来源：7 个（≥3），SEP×5（不同作者、不同条目）+ Britannica + Dewey 1925 原典全文，无互相转抄；≥1 支持学说范围与人物归属（S1/S3/S6），≥1 支持原典/著述与具体论证（S2/S4/S5/S7）。
- 数量：术语 10（6—10）、时间线 9（6—10）、著述 8（4—8）、人物 5（4—8）、分支 5、关系 4、阅读路线 2。
- evidence.json：58 条断言—来源—定位记录（已程序化校验 fieldPath 全部指向 packet.json 实际位置、sourceRefs 全部落在已声明来源），覆盖全部时间线节点、术语、著述、人物归属、关系、引语与边界主张。
- 引语：全部为经 SEP 条目核对英文原文的转译，quoteKind 明示"中译转译"；closingQuote 为百科编者语并明示非哲学家原话。
