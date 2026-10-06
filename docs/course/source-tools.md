# 写作时的源码工具清单

2026-09-23 静态扫描 `backend/routes/agent_tools_*.py` 的 register_tool 调用。此清单不等于运行时启用列表；人格额外工具、动态覆盖及 MCP 工具需继续检查 engine_langgraph.py、agents.py、deep_agent_tools.py 与 mcp_client.py。

共提取 32 个静态注册调用。名称来自源码，不沿用旧注释中的数量。

| 名称 | 源码位置 | 描述摘录 |
|---|---|---|
| `phti_test` | [backend/routes/agent_tools_eval.py:43](../../backend/routes/agent_tools_eval.py#L43) | 哲学人格测试（PHTI）——出 5 道维度题, 用于判断用户哲学倾向（斯多葛/存在主义/功利主义等）。 |
| `compare_views` | [backend/routes/agent_tools_eval.py:130](../../backend/routes/agent_tools_eval.py#L130) | 生成两个哲学家/概念的比较分析结构（comparison scaffold: 共同问题/比较轴线/双方候选主张/最根本分歧/证据需求/候选后果），供主 Agent 结合证据二次综合——不直接产出最终对比成品或胜负结论。用于'休谟和康德对因果的看法有何不同'类问题。 |
| `socratic_tutor` | [backend/routes/agent_tools_eval.py:229](../../backend/routes/agent_tools_eval.py#L229) | 苏格拉底式思辨引导（每次调用只返回一个问题）——诊断对方隐含假设并给出下一个追问; 用户回答后再次调用并传 user_reply=用户的回答以推进。ONE CALL = ONE QUESTION, 不预生成后续轮次（用于'不要告诉我答案, 只问我一个问题'类请求）。 |
| `advisor_council` | [backend/routes/agent_tools_eval.py:267](../../backend/routes/agent_tools_eval.py#L267) | 智者内阁——召集亚里士多德/斯多葛/存在主义三种思维模型, 对人生决策/困惑生成多视角建议脚手架（视角/预设/张力点/综合提示）, 供主 Agent 结合语境综合。用户要求'从几个/多个哲学传统或视角分析'某个现实抉择时必须用本工具——不要以单一视角直接作答。 |
| `paper_review` | [backend/routes/agent_tools_eval.py:310](../../backend/routes/agent_tools_eval.py#L310) | 论文评审（peer review）——thesis/结构/证据/最强反驳/修改优先级的结构化产物。路由看用户框架不看文本长度: 只要用户以'评审/审稿/评价这篇论文/这篇摘要'框架提出（摘要、片段、短文也算）→ 用本工具; 只有用户单纯要'拆解一段论证的逻辑结构'且无评审框架时才用 analyze_argument。 |
| `analyze_argument` | [backend/routes/agent_tools_eval.py:349](../../backend/routes/agent_tools_eval.py#L349) | 单个论证的逻辑结构分析（结论/前提显隐/隐含假设/谬误/最薄弱一步/补强建议）——针对一段论证或短文本; 触发语是'分析一下这段话''帮我看看这个论证''指出逻辑结构'。⚠ 用户以论文评审框架提问（'评审/审稿/评价这篇论文（或摘要/成篇文本）'）时不要用本工具, 改用 paper_review。 |
| `profile` | [backend/routes/agent_tools_eval.py:375](../../backend/routes/agent_tools_eval.py#L375) | 个性化哲学画像——分析用户当前问题的哲学倾向, 推荐真实书目与下一步方向（人生顾问/学习路径的基础）。 |
| `conceptual_map` | [backend/routes/agent_tools_eval.py:492](../../backend/routes/agent_tools_eval.py#L492) | 通用哲学关系图（MAP_TYPE: CONCEPT_NETWORK 概念网络 / PROCESS_FLOW 过程流 / ARGUMENT_GRAPH 论证依赖图 / HISTORICAL_GENEALOGY 历史谱系 / PERSON_RELATION 人物关系 / SYSTEM_ARCHITECTURE 体系结构）——返回结构化 graph + 已验证的  |
| `essay_outline` | [backend/routes/agent_tools_eval.py:522](../../backend/routes/agent_tools_eval.py#L522) | 论文大纲生成（USER_REQUESTED_ARTIFACT——大纲本身就是用户请求的产物, 可输出完整结构）: 题目/方向 → 中心论点/引言/分论点(带原典支撑)/反方回应/结论。用于'帮我列个大纲''论文骨架'类请求。 |
| `life_coach` | [backend/routes/agent_tools_eval.py:542](../../backend/routes/agent_tools_eval.py#L542) | 结构化人生疏导（斯多葛 + CBT）——情绪识别→认知扭曲检测→可控/不可控二分→行动重构。用于'我焦虑/迷茫/纠结'类求助。 |
| `dialectic` | [backend/routes/agent_tools_eval.py:607](../../backend/routes/agent_tools_eval.py#L607) | 辩证矛盾运动分析——返回动态结构字段（initial_concept/internal_tension/self_negation/transformation/new_determination/residual_tension, 按问题需要取舍）, 不使用固定'正题—反题—合题'模板。用户对形式的约束（如'不要用正反合标签'）必须经 constraint |
| `history_timeline` | [backend/routes/agent_tools_eval.py:637](../../backend/routes/agent_tools_eval.py#L637) | 哲学史时间线——流派/概念/哲人的历史脉络（基于哲学库流派时间线与哲人时代数据）。用于'存在主义的发展史''XX的时间线'类请求。 |
| `confrontation` | [backend/routes/agent_tools_eval.py:708](../../backend/routes/agent_tools_eval.py#L708) | 哲学文献隔空对质——两位哲学家就同一主题各自引用原文交锋（休谟vs康德、尼采vs黑格尔等），输出原文立场（textual claim）/模拟交锋/裁判注候选。用于'让XX和XX的原文对质'类请求。 |
| `school_arena` | [backend/routes/agent_tools_eval.py:797](../../backend/routes/agent_tools_eval.py#L797) | 哲学流派 PK 竞技场——随机抽取两个流派就当代热点议题对抗（也可指定 topic/school_a/school_b）。输出两轮交锋 + 裁判总结 + 演变图。用于'流派PK/随机对决/让两个流派辩论'类请求。 |
| `agent_council` | [backend/routes/agent_tools_eval.py:861](../../backend/routes/agent_tools_eval.py#L861) | 多智能体协作——深哲（通用视角, 检索原典）与尼采（人格视角）就同一议题各自发言, 再综合两种视角的交汇与分歧。用于'让深哲和尼采讨论XX'类请求。 |
| `search_books` | [backend/routes/agent_tools_retrieval.py:176](../../backend/routes/agent_tools_retrieval.py#L176) | 在 403 本哲学原著中全文检索（书名/作者/章节内容关键词命中）。用于回答哲学问题时找原文依据、引言、概念出处。对于按格言号/节号/篇章编号组织的作品（如尼采《快乐的科学》、马基雅维利《君主论》），若检索结果无法直接定位编号，可先查询作品详情/目录确认章节结构再读取。 |
| `get_book_detail` | [backend/routes/agent_tools_retrieval.py:249](../../backend/routes/agent_tools_retrieval.py#L249) | 获取一本书的详情（简介/作者/目录/章节数）。对于按格言号/节号/篇章编号组织的作品（如尼采《快乐的科学》、马基雅维利《君主论》），若检索结果无法直接定位编号，可先查询作品详情/目录确认章节结构再读取。 |
| `get_chapter` | [backend/routes/agent_tools_retrieval.py:283](../../backend/routes/agent_tools_retrieval.py#L283) | 读取某本书指定章节的全文（用于深入引用原文、分析论证）。出处/原话核验的必经步骤: search_books 只提供片段定位线索, 确认出处、措辞与上下文必须读取对应章节原文——检索命中候选后应读取该章再下结论, 不得仅凭检索片段或记忆给出原文引用。 |
| `query_graph` | [backend/routes/agent_tools_retrieval.py:314](../../backend/routes/agent_tools_retrieval.py#L314) | 查询哲学家星丛图谱关系（师承/论敌/影响/思想关联）。用于回答'谁影响了谁'、'思想传承脉络'、'对立观点'类问题。 |
| `get_philosopher` | [backend/routes/agent_tools_retrieval.py:336](../../backend/routes/agent_tools_retrieval.py#L336) | 获取哲学家生平资料（时期/流派/代表作/简介）。回答涉及时期/流派归属/代表作等事实资料时先查本工具核对, 避免凭记忆给出可能失准的资料。 |
| `list_books` | [backend/routes/agent_tools_retrieval.py:366](../../backend/routes/agent_tools_retrieval.py#L366) | 按作者/地区/流派筛选书籍列表（用于推荐阅读、书目检索）。 |
| `get_school` | [backend/routes/agent_tools_retrieval.py:410](../../backend/routes/agent_tools_retrieval.py#L410) | 查询哲学流派/学派详情（流派介绍/代表哲人/思想时间线）。用于回答'存在主义是什么''儒家思想'类问题。 |
| `concept_trace` | [backend/routes/agent_tools_retrieval.py:444](../../backend/routes/agent_tools_retrieval.py#L444) | 概念溯源——检索概念在 403 本原典中的出现分布与原文片段, 用于追踪概念的历史用法与演变（如'自由意志'在哪些书里出现）。 |
| `websearch` | [backend/routes/agent_tools_retrieval.py:535](../../backend/routes/agent_tools_retrieval.py#L535) | 上网搜索（维基百科中文, 含摘要）。用于补充原典库之外的信息: 外部标准/政策/最新研究/现代评论/词条解释。 |
| `query_database` | [backend/routes/agent_tools_retrieval.py:583](../../backend/routes/agent_tools_retrieval.py#L583) | 通用数据库查询: books（书籍）/ philosophers（哲学家）/ network（星丛）/ schools（流派）。按关键词过滤。 |
| `write_essay` | [backend/routes/agent_tools_memory.py:56](../../backend/routes/agent_tools_memory.py#L56) | 根据题目写一篇哲学作文（议论文/读后感等）。自动检索原典原文支撑论据, 带引用标注。用户说'修改/重写/改一下作文'时传 modify='修改要求', 工具自动基于上次作文修改。 |
| `generate_image` | [backend/routes/agent_tools_memory.py:327](../../backend/routes/agent_tools_memory.py#L327) | 生成哲学艺术图像（Agnes 生图: 概念插画/肖像/意境图）。人物肖像自动绑定本地参考图; '修改/改成/调整/重画刚才的图'时基于上次结果图生图修改。触发: '生成图片/画一张画/概念插画/画像/艺术图'。**星图/脑图/关系图/结构图/地图不是本工具职责——那是 conceptual_map 的。** |
| `role_play` | [backend/routes/agent_tools_memory.py:454](../../backend/routes/agent_tools_memory.py#L454) | 扮演哲学家（人格层）——以尼采第一人称回答。persona/记忆来自 AIAuthor 数字作者系统, 自动召回相关生平记忆。触发: 用户要求'扮演尼采/如果你是尼采/尼采会怎么看/以尼采的口吻'。 |
| `philosopher_debate` | [backend/routes/agent_tools_memory.py:615](../../backend/routes/agent_tools_memory.py#L615) | 哲学家辩论——三种模式: auto=一次性多轮（默认）; step=逐轮（用户说'继续'触发下一轮, '结束辩论'总结）; vs_user=用户参与（用户发言后传 user_reply=用户的话, 哲学家回应）。 |
| `thought_experiment` | [backend/routes/agent_tools_memory.py:675](../../backend/routes/agent_tools_memory.py#L675) | 设计/推演哲学思想实验（电车难题变体/洞穴比喻现代版）——返回设定/多立场推演/揭示问题的结构化脚手架; 用户明确要求变体时（'改成/换成/如果'）基于上次实验迭代。同一实验的重复调用受重入策略约束——除非用户要求迭代或前次结果不可用。 |
| `search_scholarship` | [backend/routes/agent_tools_scholarly.py:109](../../backend/routes/agent_tools_scholarly.py#L109) | 检索真实学术文献记录（期刊论文/专著章节等; Crossref+OpenAlex 双源）。⚠ metadata/discovery only: 只返回书目与访问层级信息, 内容归因必须再用 get_scholarly_source 取得摘要/正文证据。记录可能是 scholarly secondary、reference、primary publicatio |
| `get_scholarly_source` | [backend/routes/agent_tools_scholarly.py:132](../../backend/routes/agent_tools_scholarly.py#L132) | 按 source_record_id 取得实际可读证据: requested_access=ABSTRACT 取真实摘要; FULL_TEXT_IF_LEGALLY_AVAILABLE 尝试合法开放获取全文并返回节选段落（访问边界诚实: 未读全文不会谎报已读）。输入只接受检索返回的 source_record_id。 |
