# R13 托马斯主义 — 资料包复核记录

- 复核日期：2026-10-05
- 复核人：zcode 内容研究员（自检，非独立同行评审）
- 复核方法：继承 2026-10-04 立项备忘录的四个已核来源（SEP Aquinas、IEP Aquinas、SEP Maritain、SEP Aquinas' Moral/Political/Legal）；本日复核升级——WebFetch 重取 SEP 三条目逐节摘引核对英文原文；经 web_reader 与 WebFetch 双通道实际打开 vatican.va《永父》英文版原文（dateline 与第 7、17、19—22、31 段逐一核对），1879 环节由二手来源升级为一手文本；用 python3/grep 在本工作树重新计数站内三个学校页的『托马斯主义』术语（2/1/0）并 grep philosophers.json 核对人名。每条正文断言在 evidence.json（61 条）有对应记录。

## 一、备忘录处置

`research.md` 按任务要求原样保留（其中"经典托马斯主义细节先核实清单"仍有效，见第五、六节）。`evidence.json` 由备忘录格式重写为包格式：备忘录 14 条记录中，站内定位 3 条并入 proposal 与 S6；IEP 教义内核等阿奎那本人学说条目按边界不进本包正文（核读事实保留于备忘录与 S2 的 coverage 描述）；其余全部断言升级为带段落定位的包内记录。新增 `packet.json`、`review.md`、`artwork-brief.md`。

## 二、边界决定

1. **不重述阿奎那本人学说**：五路证明、存在与本质区分、类比说、自然法四分法、"恩典成全自然"等均不展开——由站内经院哲学页承载；阿奎那在 thinkers 中只作为"学派守卫与解释的源头"出现，overview 首段即声明本条目是"阿奎那之后"的学派史。
2. **与站内经院哲学页的分工**（写入 proposal.divisionOfLaborWithExistingEntries）：该页自述断代"公元 11 至 14 世纪中世纪大学"，结构上装不下 1879 年后的复兴；本条目接管 14 世纪以后的学派史，以"续写阿奎那身后史"衔接。本轮 grep 复核（worktree 内）：经院哲学页"托马斯主义"2 处（均为时间线/副流派提及）、唯名论页 1 处、基督教哲学页 0 处，无宿主判定成立。
3. **与 W02 逍遥学派包的接受史接口**（写入 proposal.divisionOfLaborWithW02）：W02 包 `proposal.divisionOfLaborWithR13` 已声明"托马斯对亚里士多德的系统吸收与托马斯主义体系全部留给 R13、thinkers 不收托马斯"；本包即其下游，两包在 1270/1277 巴黎谴责处对接（W02 从亚里士多德主义受冲击角度写，本包从学派身份成形角度写），双向不重复。
4. **哲学立场/建制事件/历史阶段分层**：封圣、列圣师、修会受命、通谕均写作建制事件及其后果，不写成哲学论证；修会规训下的接受（苏亚雷斯）标注为"接受（建制性）"而非师承。
5. **未核实不写**：de auxiliis、萨拉曼卡学派人物、Mercier/鲁汶研究所、超验托马斯主义一律未写（详见第六节）。安斯康姆、麦金太尔仅按 S1 列举提名，不设人物条目。
6. **subSchools 只收三个来源可证项**（新托马斯主义、存在论托马斯主义、格热戈日—菲尼斯一系），后两者在词头内注明"标签为描述性归纳"；不为凑数虚构分支。
7. **跨人物关系不写成影响**：芬尼斯↔马里旦明确标为"编辑比较"，detail 声明无师承/历史影响证据。

## 三、站内/站外人名处置

已 grep `app/public/philosophers.json`（worktree）核对：
- **站内沿用**：托马斯·阿奎那（站内名，本包 thinkers 直接使用）。
- **站外新增**（站内均为 0 命中）：约翰·卡普雷奥勒斯、卡耶坦（Cajetan/Thomas de Vio）、弗朗西斯科·苏亚雷斯、利奥十三世、雅克·马里旦（1882—1973，S3 有全日期）、吉尔松、约翰·芬尼斯。如入库建议沿用本包译名；吉尔松与芬尼斯生卒未核，条目内已留空处理。

## 四、来源核读清单（实际打开并读到相关段落的 URL）

1. https://plato.stanford.edu/entries/aquinas/ （SEP Aquinas；2026-10-04 备忘录首读，2026-10-05 重取：1277 谴责、刊误之争、接受史序列、1879 复兴与结语逐段核对）
2. https://iep.utm.edu/thomas-aquinas/ （IEP；2026-10-04 备忘录核读：1879《永父》表述与遗产叙述；本日未重取）
3. https://plato.stanford.edu/entries/maritain/ （SEP Maritain；2026-10-05 重取：§1 生卒与皈依、§3.1/§3.2/§3.5、§4 吉尔松批评原话）
4. https://plato.stanford.edu/entries/aquinas-moral-political/ （SEP Finnis 条；2026-10-05 重取：§1、§2.4.2、§2.5、§5.2；备忘录记录的 7.3 中部截断现象仍在，16 世纪后继者细节未自此源展开）
5. https://www.vatican.va/content/leo-xiii/en/encyclicals/documents/hf_l-xiii_enc_04081879_aeterni-patris.html （《永父》英文版原文；2026-10-05 web_reader+WebFetch 双通道打开，dateline 与 ¶7/17/19/20/22/31 逐段核对）
6. 站内文件（worktree）：`app/public/schools/data/school_经院哲学.json`、`school_唯名论.json`、`school_基督教哲学.json`、`app/public/philosophers.json`、`docs/content-proposals/schools/W02/packet.json`（python3/grep 实际解析）

**未能核读、已弃用的候选**（含备忘录两轮记录）：
- https://www.britannica.com/topic/Thomism — WebFetch 403（2026-10-04 与 2026-10-05 两轮均失败）。
- vatican.va 18790804 日期格式路径 — 404（备忘录）；实际可用路径为 04081879（ddmmyyyy），已改用并核读。
- New Advent 天主教百科 "Neo-Scholasticism"（候选 URL newadvent.org/cathen/10733a.htm）— 打开后实为 "Necessity" 条，与主题无关，弃用；检索服务本轮持续 429 限流，无法另寻正确卷号。
- https://iep.utm.edu/gilson/ — 404（IEP 无吉尔松条，两种路径均试）；吉尔松材料全部依托 S1/S3。
- https://sourcebooks.fordham.edu/mod/1879aeterni.asp — 500 服务器错误；《永父》一手文本改由 vatican.va 承担，不再依赖。

## 五、分歧与不确定（详见 evidence.json uncertainty 与 packet.evidenceLimits）

- **1277 细节校正**：备忘录摘记曾作"牛津大主教坎比尔基"，本次对原文核对为"Archbishop Robert Kilwardby"（未言教区与地点），正文改写为"大主教罗伯特·基尔沃德比"，不写教区/地点——以原文为准。
- **年代**：阿奎那生年 SEP"约 1225"与 IEP"1224/6"并存，正文从 SEP 并标注；刊误之争无具体起讫，timeline 用"约 1274—1299"证据范围；卡耶坦仅有"卡普雷奥勒斯约一个世纪后"的相对定位；耶稣会受命为"约 1567"。
- **标签限度**："existential Thomism""new natural law theory""Neo-Thomism/Neo-Scholasticism"作为英语标签均未在本次来源中逐字出现（S3 实为 "Christian existentialism"、S4 实为 "developments proposed by Grisez and Finnis"、S1 实为 "Thomisms of all kinds"），相应词头/子流派均注明归纳性质，不冒充来源原语。
- **转引层级**：路德语、吉尔松批评语均系 SEP 转引，quotes 署名标明转引；吉尔松原文出处未核。
- **《永父》文本**：拉丁原文未核读，全部引文出自 vatican.va 英文版；1879 年代有 S1/S2/S5 三源互证。
- **马里旦归属争议**：其托马斯主义程度"是争论话题"（S3 §4），行文保留张力，不作定论。

## 六、仍缺证据 / 待审读人定夺（先核实清单，与备忘录一致并收窄）

1. **de auxiliis（助佑之争）**：年代与裁决未核，未写——多明我会-耶稣会恩宠之争是经典托马斯主义的标志性内部争论，未来补核后可增时间线节点。
2. **萨拉曼卡学派**：维多利亚、索托等人物名单未核；现有来源仅 S4 §5.2"国际共同体理论须由其 16 世纪后继者发展"一处，正文按此为限。
3. **Mercier 与鲁汶高等哲学研究所**：作为新经院哲学建制起点未核，未写；《永父》¶20 仅把鲁汶列为旧日大学之一。
4. **超验托马斯主义**（拉内、朗尼根）：未核，subSchools 未收。
5. **卡耶坦、苏亚雷斯生卒与著述；吉尔松生平**：均未核，正文留白。
6. **18 世纪衰落的具体机制**（各大学逐案）：S1 仅一句概括，未展开。
7. **备选方案**（备忘录第 5 节）：若编辑部控制新条目总量，可并入经院哲学页 subSchools，但现代复兴段（马里旦—人权、菲尼斯—新自然法）仍无宿主，仅作次选。

## 七、质量标准核对

- 来源 6 个（S1–S5 网络 + S6 站内文件），类型覆盖 academic-encyclopedia（3 SEP + 1 IEP）、primary-text（vatican.va）、reference（站内文件）；互相独立、无转抄链（SEP 三条目分属不同主题与作者框架）。
- 学说范围与人物归属：S1/S3 支撑；原典/具体论证：S5（通谕原文段落）+ S4（实践理性原则论证与 1963 文本研究）。
- 数量：术语 8（6—10 ✓）、时间线 10（6—10 ✓）、著述 7（4—8 ✓）、人物 8（4—8 ✓）、子流派 3（有据则收，来源不足的分支已解释不收）。
- 引语 4 条（quote + quotes×3）+ closingQuote 均核对到版本与位置，转引层级逐条标注。
- 两个 JSON 均通过 `python3 -m json.tool` 校验。
