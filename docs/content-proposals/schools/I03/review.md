# I03 弥曼差派 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `I03`（proposedKind=school，P1-content-packet，coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查/主会话直研，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **前弥曼差 vs 后弥曼差（吠檀多）**：本包严格限定于 Pūrva-Mīmāṃsā；"Uttara-Mīmāṃsā"只在称谓史与接受关系中交代（S2 原句），吠檀多学说本体由站内 I04 任务承载——这是任务 scopeAndCautions "区分前弥曼差与吠檀多的历史称谓" 的直接落实。
2. **与姊妹任务的分工**：I01 正理（量与推理）、I02 胜论（范畴与本体）、本包（语言、证言、解释与规范）；弥曼差与佛教量论的论辩仅从弥曼差侧呈现，佛教侧由 B04/T01 承载。
3. **"无神论"标签的处理**：按 SEP（"Mīmāṃsā, however, is atheistic..."）与维基（"no need to postulate a maker..."）双源呈现为"拒斥创世神 + 维护吠陀权威"的结构，正文与 conclusion 均注明这一定性在学界的讨论空间，不引入未经核读的评论文献。
4. **传说与事实分层**：枯马立罗"自焚"传说在维基页自带 citation needed 标记——不写入正文；其生地三说并存照录不采信。
5. **查重**：mentions-only 成立（任务 JSON：exact 两数组为空，仅《印度哲学》提及）；无同名条目/分支，无重复建设。

## 二、分歧与证据限度（重点，本包证据面偏窄）

- **学术级来源仅一种**（SEP 印度认识论条目）；Mīmāṃsā / Kumārila / Jaimini 三页均为维基 reference 级。已将断言密度压缩到来源能承受的范围：普拉帕迦罗派对自证的独特立场、两派更多细节分歧均未获来源、不写。
- **原典不可直接核读**：GRETIL 全站索引检索弥曼差 0 命中、vedang 目录路径 404 实测；IEP 无弥曼差条目（404）；Britannica 历来反爬（沿用备案）。经文与《颂释》内容一律以 SEP/维基引述层使用并逐处标注（如第五经转述、《颂释》第112颂含页码的 SEP 引文）。
- **年代**：阇弥尼 ~400–200 BCE 为维基单一来源口径；萨跋罗不系年；枯马立罗 fl. 约7世纪；普拉帕迦罗 7 世纪。均与来源精度一致。

## 三、复核方法与结果

1. 主会话直研：SEP indiaepi 与维基三页 curl 全文抓取 + grep 定位；此前该文件已用于 T01（同一抓取），本次对弥曼差相关段落另行逐句提取。
2. evidence.json 44 条：thinkers 4、relations 5、timeline 6、cihai 10、works 4、subSchools 2、引语 4、coverage/books 2，locator 均含 verbatim 短引文。
3. 人物：站内 philosophers.json（737人，python 子串查证）无弥曼差人物——thinkers 全部站外并标注；站内商羯罗/甘地与本包来源无关，不强行收录。
4. 书籍：books.json 实查无相关藏书（检索仅命中无关书《声音与现象》），建议为空数组——与 I01/I02 的处理一致。
5. 两个 JSON 经 `python3 -m json.tool` 校验。

## 四、仍缺证据（进 packet.evidenceLimits）

- 《弥曼差经》分卷结构、萨跋罗注成书年代、普拉帕迦罗派自证立场的独立来源、两派论辩的原始文献层、abhihitānvaya 与 anvitābhidhāna 之争的对方表述、弥曼差在 8 世纪后的制度史——均无来源，不写。
- 待后续批次补强：若 Codex 审读认为需要，可在补强批寻找学术专文（如 Kataoka 2005 之外的书评/论文）替换或升级 reference 级来源。

## 五、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/epistemology-india/ （curl 全文，弥曼差段落逐句提取）
2. https://en.wikipedia.org/wiki/Mīmāṃsā （curl 全文+定位）
3. https://en.wikipedia.org/wiki/Kumārila_Bhaṭṭa （同上）
4. https://en.wikipedia.org/wiki/Jaimini （同上）
- 探测后放弃：SEP /entries/mimamsa|kumarila|prabhakara/ → 404；IEP /mimamsa/ → 404；GRETIL mimans 目录与全站索引 → 404/0 命中。


## 审计会话修订记录（2026-10-04）

- 契约修订 2026-10-04：2条端点非本包人物的关系迁入 proposal.relationSuggestions（内容未删，证据保留于 evidence.json 原 locator）；补 readingRoutes/evidenceLimits。
