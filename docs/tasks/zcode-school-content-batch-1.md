# 批次交付报告 · 第 1 批（F02 形而上学 + F06 美学）

日期：2026-10-04。分支：`codex/zcode-school-content`。提交：`53b5a94a9`。

## 交付内容

| 任务 | 文件 | 来源数 | 证据记录 | 状态 |
|---|---|---:|---:|---|
| F02 形而上学 | `docs/content-proposals/schools/F02/`（packet/evidence/review/artwork-brief） | 11 | 40 | ready-for-review |
| F06 美学 | `docs/content-proposals/schools/F06/`（同构四件） | 12 | 61 | ready-for-review |

两包均为领域总览（kind=field），与既有条目为导流/互链关系，未修改任何共享目录、页面或正式数据。

## 复核方式

- 研究员自查：全部来源于 2026-10-04 以 WebFetch/curl 实际打开并读到相关段落，检索片段一律不计为已核实；放弃来源（Britannica 反爬、IEP 404/目录页、ctext 反爬）逐项备案于 review.md。
- 主会话独立复核：另行抓取两包全部来源 URL 比对 verbatim 定位，全部吻合；康德"无直观的概念是空的"（A52/B76）经二次定向抓取确认逐字存在于 SEP kant-metaphysics 条目；F06 的 Gutenberg §2 标题与维基文库《知北游》原文逐字比对一致。
- 两个 JSON 均通过 `python3 -m json.tool`；sourceRefs 无悬空引用（F02: 11 源 10 用、F06: 12 源 12 用）。
- 人物姓名对照 `app/public/philosophers.json`；F02 四个、F06 九个建议书籍 ID 均在 `app/public/books.json` 实际查得。

## 要点与边界

- F02：与唯心主义、神秘主义、科学假说的三重边界在正文与 review.md 辨析；唯一相关既有分支为分析哲学→"模态、指称与形而上学"（建议互链而非重复）；三处跨传统比较（亚里士多德—朱熹、亚里士多德—龙树、康德—蒯因）均标注编辑比较。
- F06：学科史（18 世纪欧洲定名）与审美思想史（柏拉图、《诗学》、《庄子》《论语》）显式区分；日本物哀、阿兹特克"花与歌"因无可核读来源未写入，建议由站内专门条目承载；黑格尔"艺术终结"全程使用谨慎表述。
- 证据限度逐条进 `evidenceLimits`（如蒯因《论何物存在》1948 首发未核、鲍姆嘉通《Aesthetica》成书年未核、克里普克事实暂依赖 reference 级来源等）。

## 进行中与受阻

- 在跑：F01 认识论、T01 佛教哲学、I01 正理派（后台研究代理）。
- 受阻后待重试：F03、F04、F05、I02、I06、J01、A01 —— 研究代理因账户速率限制（错误 1302）中断，无产出；将随限流恢复分小批重试。
