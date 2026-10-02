# School 内容审校记录

审校日期：2026-10-02。范围：对 `app/public/schools/data/school_*.json` 的 111 个页面作全量结构与高风险模式筛查，并对下列七个严重缺漏页面完成基于公开学术来源的全文重写。本记录的七页之外的修订由同次发布中的其他审校任务负责。

## 全库初始问题与审校边界

此次修订前，全部 111 页都有简介、人物、关系、词海和子流派字段，但字段存在不代表内容可靠：

- 7 页简介仅 31—124 字；3 页时间轴为空，4 页只有一条；6 页缺结语、7 页缺典籍，分析哲学没有思想短句。
- 1,980 条 `quotes` 均没有独立 `source` 字段，111 页均没有页面级 `sources`。不能据此将所有短句展示为某一译本的直接引文。
- 313 个 `thinker.works` 把列表写成字符串；怀疑论的词海包含嵌套列表而非词条对象。
- 20 页存在字面相同的词条；99 页恰好有 5 个子流派。数字整齐不是完整性的证据，应区别真正学派、时代分期、个人思想、方法与后世接受。
- 内容类型混合：地域传统、宗教思想、政治运动、研究领域与具有组织历史的学派同时存在。不能给所有条目编造统一创始人、固定五分支或一条连续师承链。
- 高风险模式包括逆时的影响边、把隔代承接写成师生、同名哲人混淆、把失传作品编成可读原典、把现代流行格言或总结加引号署给古人，以及将传说或类比写成确定史实。

**本次全量筛查不等于 111 页逐句完成同行评审。** 结构校验能证明页面可用及必需字段齐备，不能证明每条历史或概念陈述都正确。应以页面的 `contentReview.scope` 与所列原典/学术来源判断实际审校范围。后续新增“直接引文”须提供作品、篇章或页码、使用译本；没有精确原文依据的思想总结应标 `kind: "paraphrase"`。

## 七个空壳页面的修订

所有页面均补入四段有论证脉络的简介、完整结语、具体时间线、实际存在的原典或明确标为残篇/资料汇编的典籍、独立概念、历史分支与来源。中文思想短句全部明确标为概述，不冒充译本原句；Hero 和结尾同样带 `quoteKind` / `closingQuoteKind` 及来源说明。

| 页面 | 时间点 | 典籍 | 独立概念 | 主要纠错 |
|---|---:|---:|---:|---|
| 伊壁鸠鲁学派 | 8 | 6 | 14 | 奥诺安达第欧根尼改为公元 2 世纪；区分欲望分类与快乐分类；去除未经证实的菲洛德谟→卢克莱修师承式关系、假作品；偏斜不比附现代量子论 |
| 怀疑论 | 9 | 6 | 13 | 去除阿尔克西劳→卡尔内亚德直接师生、休谟→蒙田逆时关系；区别皮浪本人、后期皮浪主义、学园派和方法怀疑；悬置不是断言知识绝对不可能 |
| 斯多葛学派 | 9 | 7 | 13 | 区分无关善恶与毫无选择价值；激情批判不等于情感麻木；去除未经证明的塞内卡→穆索尼乌斯及希罗克勒斯→马可链；补早期逻辑、自然学和罗马伦理的材料差异 |
| 前苏格拉底哲学 | 9 | 6 | 14 | 明确后设名称并非纯年代界限；补留基伯及多元论；不把毕达哥拉斯定理直接断言为本人创立；注明原文残篇、证言和后世分类之别 |
| 分析哲学 | 11 | 10 | 16 | 将“早期/后期维特根斯坦”合为一个人；补完整历史与多种方法；新增克里普克；分清书籍初刊与单行本年份，不将全传统等同逻辑实证主义或语言哲学 |
| 犬儒学派 | 8 | 6 | 12 | 移除无法支持的假作品和伪造传承链；澄清木桶/陶瓮、安提斯泰尼师承争议；补希帕基娅、忒勒斯、斯多葛接受；明确古代犬儒与现代消极词义的差别 |
| 新柏拉图主义 | 9 | 7 | 14 | 区分雅典普鲁塔克与传记作者；纠正普罗克洛→伪狄奥尼修斯方向；去除普罗克洛→达马斯基乌斯直接师生；说明流溢不是时间中的物理流出，529 年不代表全部古代哲学终结 |

七页共有 63 个时间点、48 部典籍/文献条目、96 个独立概念。删除重复凑数不代表删去有价值的知识；同义内容合并为更准确的词条。人物中标为“相关传统”或“接受”的条目用于说明影响，不等于该人物属于同一学派。

## 核对来源

### 伊壁鸠鲁学派

- [SEP: Epicurus](https://plato.stanford.edu/entries/epicurus/)
- [SEP: Lucretius](https://plato.stanford.edu/entries/lucretius/)
- [SEP: Philodemus](https://plato.stanford.edu/entries/philodemus/)
- [Epicurus, Letter to Menoeceus（MIT Internet Classics Archive）](https://classics.mit.edu/Epicurus/menoec.html)

### 怀疑论

- [SEP: Ancient Skepticism](https://plato.stanford.edu/entries/skepticism-ancient/)
- [SEP: Pyrrho](https://plato.stanford.edu/entries/pyrrho/)
- [SEP: Sextus Empiricus](https://plato.stanford.edu/entries/sextus-empiricus/)
- [SEP: Michel de Montaigne](https://plato.stanford.edu/entries/montaigne/)
- [SEP: David Hume](https://plato.stanford.edu/entries/hume/)

### 斯多葛学派

- [SEP: Stoicism](https://plato.stanford.edu/entries/stoicism/)
- [SEP: Epictetus](https://plato.stanford.edu/entries/epictetus/)
- [SEP: Seneca](https://plato.stanford.edu/entries/seneca/)
- [SEP: Marcus Aurelius](https://plato.stanford.edu/entries/marcus-aurelius/)
- [Epictetus, Enchiridion（MIT Internet Classics Archive）](https://classics.mit.edu/Epictetus/epicench.html)

### 前苏格拉底哲学

- [SEP: Presocratic Philosophy](https://plato.stanford.edu/entries/presocratics/)
- [SEP: Heraclitus](https://plato.stanford.edu/entries/heraclitus/)
- [SEP: Parmenides](https://plato.stanford.edu/entries/parmenides/)
- [SEP: Ancient Atomism](https://plato.stanford.edu/entries/atomism-ancient/)
- [SEP: Pythagoras](https://plato.stanford.edu/entries/pythagoras/)

### 分析哲学

- [IEP: Analytic Philosophy](https://iep.utm.edu/analytic-philosophy/)
- [SEP: Analysis](https://plato.stanford.edu/entries/analysis/)
- [SEP: Gottlob Frege](https://plato.stanford.edu/entries/frege/)
- [SEP: Bertrand Russell](https://plato.stanford.edu/entries/russell/)
- [SEP: Ludwig Wittgenstein](https://plato.stanford.edu/entries/wittgenstein/)
- [SEP: Willard Van Orman Quine](https://plato.stanford.edu/entries/quine/)

### 犬儒学派

- [IEP: Cynics](https://iep.utm.edu/cynics/)
- [IEP: Diogenes of Sinope](https://iep.utm.edu/diogenes-of-sinope/)
- [SEP: Epictetus](https://plato.stanford.edu/entries/epictetus/)
- 原典定位：《名哲言行录》卷六；《谈话录》卷三 22 章；迪奥·克里索斯托姆演说第 6、8、9、10 篇。原典条目注明为相关传统的接受或后世证言，未假称为西诺普第欧根尼本人存世著作。

### 新柏拉图主义

- [SEP: Neoplatonism](https://plato.stanford.edu/entries/neoplatonism/)
- [SEP: Plotinus](https://plato.stanford.edu/entries/plotinus/)
- [SEP: Proclus](https://plato.stanford.edu/entries/proclus/)
- [SEP: Syrianus](https://plato.stanford.edu/entries/syrianus/)
- [SEP: Pseudo-Dionysius the Areopagite](https://plato.stanford.edu/entries/pseudo-dionysius-areopagite/)
- [Plotinus, The Six Enneads（MIT Internet Classics Archive）](https://classics.mit.edu/Plotinus/enneads.html)

## 数据检查

七页均已检查 JSON 可解析、人物作品为数组、关系两端对应实际人物、词海无字面重复、所有思想短句具有原典来源定位与可访问的学术来源 URL、时间线不少于五个有实际内容的节点，简介、结语、典籍、分支及页面级来源均不为空。

保留原有文件名、页面名称和公开资源路径。没有变更书库或章节文件；史料和典籍不因为列在本页就被假称为站内已收录、可直接阅读的书籍。
