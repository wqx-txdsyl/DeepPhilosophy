# U03 不二论吠檀多 — 复核记录（review.md）

任务：U03 不二论吠檀多（Advaita Vedānta）· 学派资料包（school）
交付日：2026-10-04 · 工作目录：`docs/content-proposals/schools/U03/` · 状态：ready-for-review

## 一、同日草稿处置

开工前 `ls docs/content-proposals/schools/`：**U03 目录不存在，无同日草稿**，无需保留/重写处置。全部四个文件为本包首次撰写。

## 二、边界与分工（与 I04/I05 的衔接）

1. **I04 吠檀多总览（已交付）预留的 U03 接口，本包兑现**：I04 包 review.md 第 4 条约定"乔荼波陀—商羯罗师承细节、māyā—avidyā—adhyāsa 机制、不二论内部诸阶段与争论归 U03"。本包 overview 第 2—5 段、cihai（adhyāsa/avidyā/māyā/anirvacanīya）、subSchools（Bhāmatī/Vivaraṇa/mūlāvidyā）即为此接口的完整展开。
2. **商羯罗年代三口径自核后引用**：I04 记三口径（SEP "eighth century CE" vs 维基 Vedanta 页 "9th century" vs 站内页 "约7—8世纪/788 生"）。本包自核：SEP Shankara 条目亲读见 "flourished during the eighth century CE"；站内 philosophers.json 商羯罗条目 era 作 788—820（python 实查）；三十二岁寿与 digvijaya 叙事 IEP 明言近乎超凡、传记类文献 14—17 世纪成书（维基引 Dalal）。本包并陈不裁决，未采信 I04 转引的"维基 9 世纪"口径（本包核读的维基 Advaita 页作 8 世纪，与 SEP 一致；I04 所引为另一页面）。
3. **与 I05 的边界**：摩陀婆批评的学说本体（五别、三量、灵魂等级）归 I05。本包只写"被批评"一侧：时间线第 6 项（Bhāskara māyāvāda 指责、罗摩奴阇 prachanna bauddha、摩陀婆专驳著作名目 Upadhikhaṇḍana/Tattvodyota，均出自维基本页亲读）。Advaita 与 Dvaita 为对立学派，本包无任何师承/影响式表述。
4. **不泛化为印度哲学通说**：māyā、anirvacanīya、二谛等术语严格标注不二论脉络；站内《印度哲学》分支"现象世界为虚幻（Maya）"一句按 SEP/IEP 口径应读作 anirvacanīya 的"次于真实"——已写入 evidenceLimits 提示接入时核对，本包不改动站内数据。
5. **新吠檀多与现代西传归 I04**：本包时间线止于 19 世纪接受史节点（西方学术对不二论地位的过度强调，维基亲读），不展开维韦卡南达。

## 三、查重结论

- 任务 JSON：exactTopLevelEntries 空；exactBranches 为《印度哲学》分支"不二论吠檀多"（index 0）——本包即其深化扩展，性质为 related-branch deepening，与 I04（吠檀多传统群总览）、I05（Dvaita）分工清晰，无重复建设风险。
- 站内数据实查：philosophers.json（737 人，dict 键）仅"商羯罗"命中；books.json（409 本）检索"奥义书/梵经/薄伽梵歌/吠檀多/商羯罗/Advaita/Upanishad"0 命中 → 无荐书链接、无站内书 ID 伪造风险。其余六位人物（乔荼波陀、波陀摩帕陀、苏雷什瓦罗、曼陀纳·弥湿罗、伐差斯帕底·弥湿罗、维底罗尼耶）均为**站外人物**，已逐条标注。

## 四、分歧与证据限度（详单见 packet.evidenceLimits）

1. **生卒与传记**：商羯罗只写"8世纪盛年"（SEP 亲读）；788—820 为站内页口径（引而不改）；三十二岁寿、digvijaya、四道院创建均为传记性叙事——Śaṅkaravijaya 成书于 14—17 世纪、四道院 14 世纪前无文献提及（Hacker，维基亲读转述）。
2. **乔荼波陀**：SEP 6 世纪；维基一处 6 世纪、另一处 7 世纪 → 取"约6—7世纪"。
3. **《梵经》定年**：仅引 SEP"系谱回溯至跋达罗衍那（约前1世纪传统口径）"作为框架；现代定年分歧本包无来源，不写。《梵经》原典本包未核读（I04 已核并注意其 NOT PROOF-READ 声明），经义一律经 SEP/IEP 引述层。
4. **Prakāśātman**：IEP 作 10 世纪、维基作 c. 1200—1300，并陈不裁决。**IEP 页面内部矛盾**：该页后文有一句称《Vivaraṇa》为 Vacaspati Mishra 所作，与同页前文（Prakāśātman 作注）及维基不符——未采信，Vivaraṇa 归属以两处一致口径（Prakāśātman）为准。
5. **摩陀婆纪年**：维基本页作 14 世纪；I05 包口径 1199—1278 / 1238—1317。本包时间线写"13—14世纪"并注明页面口径差异。
6. **GRETIL《薄伽梵歌》注本**：标题作 "commentary ascribed to Śaṃkara" 且仅含 1—17 章；本包如实转述该归属措辞，真伪判定引 Mayeda 1965（经 SEP 书目）。
7. **托名著作**：《Vivekacūḍāmaṇi》等真伪存疑（维基：现代学者"倾向于否认"），一律不收入 works、不引其文句。苏雷什瓦罗《Naiṣkarmya-siddhi》按 IEP "supposed to have written" 口径标"传统归属"。
8. **佛教关系**：本包只写商羯罗一方论辩（中观 ChUbh 6.2.1–2、唯识自证 BrSūBh 2.2.28，SEP 亲读）与"隐蔽佛教"指控史；不代述佛教立场，不写影响方向定论（Dasgupta 强影响说与"非佛教"通说分歧如实并陈）。

## 五、复核方法与结果

1. 5 个来源全部 curl 全文抓取（/tmp/u03_research/：sep_shankara.txt 86,786 字符、iep_advaita.txt 28,160、wiki_advaita.txt 413,844、gretil_gaudapada_agamashastra.txt 30,837、gretil_shankara_gitabhashya.txt 520,003），逐关键词定位亲读相关段落；evidence.json 42 条，locator 均含亲眼核读的 verbatim 短引（学术来源英文原文、原典梵文转写），写稿后以脚本对 15 处关键引文逐字回对抓取原文全部命中（2 处初判失配经空白符规范化后确认命中，系抓取文本换行差异）。
2. 原典亲读：GRETIL《Āgamaśāstra》GpK_2.31/2.32/2.33—2.37/3.9—3.11 段落直接核读（quote 与 closingQuote 逐字取自该文件）；GRETIL《薄伽梵歌》+注 ||bhg_2.16|| 颂文与商羯罗注（sat/asat 判据段）直接核读。文件头版本信息（Apate 1921、AnSS 10、录入者 Schreiner）已录。节标约定经实测确认：该文件节标缀于所标节文之后（GpK_1.1、GpK_2.1 上下文可见），四章节数 29/38/48/100 与通行编本一致。
3. 引语纪律：所有中文译文标注"编辑译"；三条 quotes 的 kind 分别标"经 SEP 核读转引"（tat tvam asi，ChU 原典未另行核读）、"原典直引"（GRETIL 两处）、"传诵韵文"（匿名，IEP 明言 anonymous verse）；无一署名为商羯罗原话的未经核对引语。
4. 结构契约自检：schemaVersion/taskId/status/reviewedAt/reviewMethod/proposal/sources/overviewSourceRefs/conclusionSourceRefs/school/readingRoutes/evidenceLimits 均在顶层；sub_schools 未作顶层键（subSchools 在 school 内）；relations 6 条的 from/to 全部是本包 thinkers 七人；term 10、timeline 9、works 8、thinkers 7、subSchools 4，均在契约通常区间。
5. 两个 JSON 已过 `python3 -m json.tool` 校验；sourceRefs 引用的 S1—S5 在 sources 中唯一且可解析；evidence.json 的 fieldPath 指针抽查可解析到 packet.json 对应位置。

## 六、仍缺证据

- 商羯罗具体生卒与 digvijaya 行化的史学批判研究（Bader 2000 等只见于 SEP 书目，未核读原书）。
- Bhāmatī/Vivaraṇa 两派的一手文本（Bhāmatī、Vivaraṇa、Pañcapādikā 梵文本）未核读；两派细节均经 IEP/维基转述层。
- 《歌者奥义书》《大森林奥义书》原典（mahāvākya 的梵文原文）未在本包 GRETIL 核读，tat tvam asi/ahaṃ brahmāsmi 经 SEP 转引（kind 已标）。
- Vivaraṇa 系后学（如 Madhusūdana Sarasvatī《Advaitasiddhi》）仅 IEP 名单层提及，未写学说细节。
- Britannica 未尝试（I04 备案其反爬拦截，沿用）；SEP 无独立 "Advaita Vedanta" 条目（内容集中于 Shankara 条目）。

## 七、实际核读 URL 清单（2026-10-04，均 curl 全文 + 关键词定位亲读）

1. https://plato.stanford.edu/entries/shankara/ （SEP，学术级）
2. https://iep.utm.edu/advaita-vedanta/ （IEP，学术级）
3. https://en.wikipedia.org/wiki/Advaita_Vedanta （reference 级；引用模板噪声已剥离后精读）
4. https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/sa_gauDapAda-AgamazAstra.txt （GRETIL 原典；经 https://gretil.sub.uni-goettingen.de/gretil.html 索引定位）
5. https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/sa_bhagavadgItA-comm.txt （GRETIL 原典+注；索引页 Samkara: Bhagavadgitabhasya 锚点 org638cc74 定位）

## 八、写作边界备忘（给接入者）

- 学派标题不用"商羯罗创立"（SEP/维基/IEP 三源一致：体系化者非创始人；站内分支简介"由商羯罗创立"一句接入时建议核对）。
- "世界为幻"一律带 anirvacanīya/二谛限定语，避免虚无主义误读；māyāvādin 保持"论敌贬称"定性。
- 与 I05 互链建议：论敌关系（critique/counter-critique），非承继关系。

## 九、修订记录（2026-10-04 独立审计复核）

1. **审计主张"节标系统性 +1 偏移"（2.32→2.31、2.31→2.30、2.34→2.33、3.10→3.9）：复核后不改号。** 实测证据：GRETIL《Āgamaśāstra》明文本节标缀于所标节文之后（文件首节 `(bahiṣ...)prajño... // GpK_1.1`、第二品首节 `vaitathyaṃ sarvabhāvānāṃ... // GpK_2.1` 上下文直接可见），四章节数 29/38/48/100 与通行编本一致，SEP Shankara 条目所引 "GK 2.34"（anirvacanīya）与文件中 nānedaṃ 节的节标 2.34 吻合，外部检索亦见 na nirodho 一节多数引作 2.32（个别编本确有 2.31/2.33 的计数出入）。审计给出的数字恰为"节前标记"读法所得，疑将节后缀标误读为节前标。故文件节标即 Apate 1921 编本编号，本包原节号维持不变。
2. **按审计方案 B 执行"统一加注"**：quote/closingQuote 的 kind 字段、thinkers[乔荼波陀]、works[1]、subSchools[无生论]、readingRoutes[0] 一律注明"节号从 Apate 1921/GRETIL 文件，个别编本相邻节号有 ±1 出入"，检索以 GRETIL 节标为准；evidence[/school/works/1] locator 补记节标约定与章节数实测。
3. **审计对 [check!] 注记的批评成立，已改**：所引 saṃghātāḥ 节（GpK_3.10）首句确带 GRETIL 编辑 [check!] 疑误标记（'sarve' 异读处）；原 note 仅以 GpK_3.9 为例、易误读为所引节均干净。已改为如实披露（全文件 [check!] 共 3 处：GpK_3.9、3.10、3.25；所引 2.31—2.36 区间无）。
4. conclusion 段英文残留"reading 不二论"已改为通顺中文（"因此，阅读不二论要同时读它的两层"）。
5. 两个 JSON 重过 `python3 -m json.tool`；sourceRefs 与 fieldPath 一致性复检通过。
