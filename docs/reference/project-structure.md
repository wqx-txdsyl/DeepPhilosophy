# DeepPhilosophy 全文件结构图

> 生成时间: 2026-10-03 18:58 · 排除 .git / node_modules / .venv / __pycache__ / .wrangler / dist
> 大数据目录 (章节库 / 向量库 / 封面 / ai_author) 折叠为计数摘要

## DeepPhilosophy × PhiAgent 合并后单仓库（2026-08-14: 平台 + 智能体 + 书库工具）

```
/Users/sen/DeepPhilosophy
├─ .agents/
│  └─ skills/
│     ├─ add-author/
│     │  └─ SKILL.md  (1,847 B)
│     ├─ add-school/
│     │  └─ SKILL.md  (963 B)
│     ├─ add-skill/
│     │  └─ SKILL.md  (6,401 B)
│     ├─ add-subschool/
│     │  └─ SKILL.md  (2,741 B)
│     ├─ agnes-image/
│     │  └─ SKILL.md  (3,699 B)
│     ├─ fetch-philosopher-img/
│     │  └─ SKILL.md  (2,585 B)
│     ├─ fix-counts/
│     │  └─ SKILL.md  (989 B)
│     ├─ local-check/
│     │  └─ SKILL.md  (1,450 B)
│     ├─ post-push/
│     │  └─ SKILL.md  (1,472 B)
│     ├─ relationship-constellation/
│     │  └─ SKILL.md  (4,051 B)
│     ├─ school-bg-gen/
│     │  └─ SKILL.md  (1,147 B)
│     └─ timeline-designer/
│        └─ SKILL.md  (3,374 B)
├─ .github/
│  └─ workflows/
│     └─ consistency-check.yml  (786 B)
├─ .zcode/
│  └─ plans/
│     └─ plan-sess_d7f94975-3b44-4797-99ce-74cf86623dd8.md  (4,493 B)
├─ agent-app/
│  ├─ public/  # agent 前端静态数据（本地工作副本, 不入库）
│  ├─ src/
│  │  ├─ assets/
│  │  │  ├─ fonts/
│  │  │  │  ├─ OFL-BodoniModa.txt  (4,399 B)
│  │  │  │  └─ bodoni-moda-phiagent.ttf  (2,728 B)
│  │  │  ├─ phiagent-icon-180.png  (43,166 B)
│  │  │  └─ phiagent-icon.png  (334,764 B)
│  │  ├─ components/
│  │  │  ├─ conversation/
│  │  │  │  ├─ AccountMemory.jsx  (15,818 B)
│  │  │  │  ├─ AgentPlaza.jsx  (7,216 B)
│  │  │  │  ├─ AgentSelector.jsx  (3,734 B)
│  │  │  │  ├─ AnswerResearch.jsx  (9,587 B)
│  │  │  │  ├─ AttachmentCard.jsx  (2,476 B)
│  │  │  │  ├─ Composer.jsx  (11,041 B)
│  │  │  │  ├─ ConversationHeader.jsx  (2,653 B)
│  │  │  │  ├─ ConversationSidebar.jsx  (7,226 B)
│  │  │  │  ├─ ErrorBoundary.jsx  (1,658 B)
│  │  │  │  ├─ GeneralAnswer.jsx  (10,497 B)
│  │  │  │  ├─ MessageList.jsx  (28,284 B)
│  │  │  │  ├─ Modal.jsx  (5,619 B)
│  │  │  │  ├─ O9.jsx  (15,221 B)
│  │  │  │  ├─ PersonalizedQuestions.jsx  (4,074 B)
│  │  │  │  ├─ SettingsPanel.jsx  (22,166 B)
│  │  │  │  ├─ StreamNotice.jsx  (2,844 B)
│  │  │  │  ├─ ToolResult.jsx  (2,249 B)
│  │  │  │  └─ markdown.jsx  (15,887 B)
│  │  │  ├─ AuthModal.jsx  (5,833 B)
│  │  │  ├─ DrawioInline.jsx  (1,521 B)
│  │  │  ├─ DrawioModal.jsx  (1,996 B)
│  │  │  ├─ Icon.jsx  (625 B)
│  │  │  └─ UserCenterModal.jsx  (277 B)
│  │  ├─ data/
│  │  │  ├─ accountSettings.js  (1,446 B)
│  │  │  ├─ answer_book.json  (96,205 B)
│  │  │  ├─ cache.js  (493 B)
│  │  │  ├─ chatSessions.js  (2,722 B)
│  │  │  ├─ conversationLogic.js  (17,690 B)
│  │  │  ├─ conversationStore.js  (8,120 B)
│  │  │  ├─ conversationSync.js  (10,740 B)
│  │  │  ├─ coverUrls.js  (1,199 B)
│  │  │  ├─ crypto.js  (4,017 B)
│  │  │  ├─ dailyQuotes.js  (95,633 B)
│  │  │  ├─ generalStream.js  (13,128 B)
│  │  │  ├─ localPrefs.js  (1,337 B)
│  │  │  ├─ memoryProfile.js  (847 B)
│  │  │  ├─ phti_original_types.json  (3,490 B)
│  │  │  ├─ phti_questions.json  (72,115 B)
│  │  │  ├─ phti_silly_questions.json  (30,844 B)
│  │  │  ├─ schoolRanking.js  (6,572 B)
│  │  │  ├─ streamNotice.js  (3,717 B)
│  │  │  ├─ tagMaps.js  (7,928 B)
│  │  │  ├─ toolResultExtras.js  (8,794 B)
│  │  │  ├─ toolResultView.js  (11,760 B)
│  │  │  └─ userData.js  (6,463 B)
│  │  ├─ pages/
│  │  │  └─ AgentPage.jsx  (43,443 B)
│  │  ├─ utils/
│  │  │  ├─ api.js  (1,288 B)
│  │  │  ├─ clipboard.js  (1,348 B)
│  │  │  ├─ evidence.js  (3,561 B)
│  │  │  ├─ i18n.jsx  (18,579 B)
│  │  │  ├─ o9Research.js  (3,840 B)
│  │  │  ├─ primaryReference.js  (2,422 B)
│  │  │  ├─ theme.js  (739 B)
│  │  │  ├─ useAgents.js  (1,538 B)
│  │  │  ├─ useCompactViewport.js  (679 B)
│  │  │  └─ useLocalPref.js  (536 B)
│  │  ├─ App.jsx  (1,345 B)
│  │  ├─ auth.jsx  (7,585 B)
│  │  ├─ conversation.css  (68,124 B)
│  │  ├─ index.css  (1,922 B)
│  │  └─ main.jsx  (235 B)
│  ├─ tests/
│  │  ├─ accountSettings.test.mjs  (4,567 B)
│  │  ├─ clipboard.test.mjs  (1,273 B)
│  │  ├─ conversationLogic.test.mjs  (18,759 B)
│  │  ├─ conversationSync.test.mjs  (9,457 B)
│  │  ├─ generalMarkdown.test.mjs  (17,499 B)
│  │  ├─ generalStream.test.mjs  (22,620 B)
│  │  ├─ memoryProfile.test.mjs  (1,039 B)
│  │  ├─ o9Research.test.mjs  (3,725 B)
│  │  ├─ streamNotice.test.mjs  (3,031 B)
│  │  └─ toolResultView.test.mjs  (4,814 B)
│  ├─ index.html  (470 B)
│  ├─ package-lock.json  (101,755 B)
│  ├─ package.json  (866 B)
│  └─ vite.config.js  (568 B)
├─ app/
│  ├─ electron/
│  │  └─ main.cjs  (1,712 B)
│  ├─ public/  — 前端静态资源（被 gitignore）
│  │  ├─ backend/
│  │  │  └─ data/
│  │  │     └─ book_chapters/  # 331 本书 × 12736 个章节 json (按 bid 分目录, 顶层 dict 禁 list)
│  │  ├─ book_detail/  # 410 个 detail json (三处同步规则: PHA/DP/app public)
│  │  ├─ covers/  # 前端静态资源 (408 文件)
│  │  ├─ gene/
│  │  │  ├─ region/
│  │  │  │  ├─ africa.webp  (160,130 B)
│  │  │  │  ├─ america.webp  (164,776 B)
│  │  │  │  ├─ britain.webp  (154,116 B)
│  │  │  │  ├─ china.webp  (152,622 B)
│  │  │  │  ├─ egypt.webp  (90,726 B)
│  │  │  │  ├─ enlightenment.webp  (150,558 B)
│  │  │  │  ├─ france.webp  (152,382 B)
│  │  │  │  ├─ germany.webp  (213,916 B)
│  │  │  │  ├─ greece.webp  (148,038 B)
│  │  │  │  ├─ india.webp  (123,732 B)
│  │  │  │  ├─ islam.webp  (117,674 B)
│  │  │  │  ├─ japan.webp  (124,550 B)
│  │  │  │  ├─ korea.webp  (148,524 B)
│  │  │  │  ├─ latin_america.webp  (148,716 B)
│  │  │  │  ├─ medieval_europe.webp  (138,146 B)
│  │  │  │  ├─ mesopotamia.webp  (138,832 B)
│  │  │  │  ├─ renaissance.webp  (189,102 B)
│  │  │  │  ├─ rome.webp  (157,996 B)
│  │  │  │  ├─ southeast_asia.webp  (220,768 B)
│  │  │  │  └─ world_origin.webp  (194,936 B)
│  │  │  ├─ civilization_silhouette.webp  (229,736 B)
│  │  │  ├─ era_ancient.webp  (11,948 B)
│  │  │  ├─ era_greece.webp  (8,468 B)
│  │  │  ├─ era_medieval.webp  (20,638 B)
│  │  │  ├─ era_modern.webp  (36,272 B)
│  │  │  ├─ era_renaissance.webp  (6,080 B)
│  │  │  ├─ philosophy_symbols.webp  (332,872 B)
│  │  │  └─ philosophy_tree.webp  (908,994 B)
│  │  ├─ icons/  # 前端静态资源 (89 文件)
│  │  ├─ philosopher/  # 前端静态资源 (621 文件)
│  │  ├─ phti/
│  │  │  ├─ 亚里士多德的掉书袋.webp  (9,234 B)
│  │  │  ├─ 休谟的因果彩票.webp  (15,504 B)
│  │  │  ├─ 克尔凯郭尔的信仰跳楼.webp  (8,658 B)
│  │  │  ├─ 加缪的副驾驶.webp  (13,136 B)
│  │  │  ├─ 卢梭的逆行自然人.webp  (27,386 B)
│  │  │  ├─ 尼采的锤子砸脚.webp  (13,584 B)
│  │  │  ├─ 康德的准点废柴.webp  (18,590 B)
│  │  │  ├─ 斯宾诺莎的猫.webp  (10,916 B)
│  │  │  ├─ 柏拉图的洞穴保安.webp  (9,280 B)
│  │  │  ├─ 笛卡尔的冥想僵尸.webp  (9,234 B)
│  │  │  ├─ 第欧根尼的木桶VIP.webp  (17,308 B)
│  │  │  ├─ 维特根斯坦的已读不回.webp  (10,152 B)
│  │  │  ├─ 萨特的他人地狱.webp  (13,272 B)
│  │  │  ├─ 边沁的快乐计算器.webp  (13,834 B)
│  │  │  ├─ 霍布斯的办公室丛林.webp  (23,854 B)
│  │  │  └─ 黑格尔的螺旋滑梯.webp  (12,030 B)
│  │  ├─ schools/  # 前端静态资源 (121 文件)
│  │  ├─ .nojekyll  (0 B)
│  │  ├─ _headers  (696 B)
│  │  ├─ books.json  (562,952 B)
│  │  ├─ config-bootstrap.js  (1,113 B)
│  │  ├─ covers.json  (21,610 B)
│  │  ├─ favicon.png  (11,953 B)
│  │  ├─ favicon.svg  (9,522 B)
│  │  ├─ icons.svg  (5,031 B)
│  │  ├─ manifest.json  (705 B)
│  │  ├─ philosopher_network.json  (378,772 B)
│  │  ├─ philosophers.json  (3,019,492 B)
│  │  ├─ robots.txt  (71 B)
│  │  ├─ sitemap.xml  (1,074 B)
│  │  └─ sw.js  (1,890 B)
│  ├─ src/
│  │  ├─ assets/  — 前端打包资源
│  │  │  └─ fonts/
│  │  │     ├─ playfair-latin-400-italic.woff2  (21,884 B)
│  │  │     ├─ playfair-latin-400-normal.woff2  (21,856 B)
│  │  │     ├─ playfair-latin-500-italic.woff2  (23,076 B)
│  │  │     ├─ playfair-latin-500-normal.woff2  (23,048 B)
│  │  │     ├─ playfair-latin-600-normal.woff2  (23,228 B)
│  │  │     └─ playfair-latin-700-normal.woff2  (23,224 B)
│  │  ├─ components/  — 前端组件
│  │  │  ├─ school/  — 学派详情组件
│  │  │  │  ├─ ConstellationMap.jsx  (14,062 B)
│  │  │  │  ├─ EpilogueSection.jsx  (2,831 B)
│  │  │  │  ├─ GlossaryCloud.jsx  (3,663 B)
│  │  │  │  ├─ HeroSection.jsx  (4,086 B)
│  │  │  │  ├─ OverviewSection.jsx  (2,673 B)
│  │  │  │  ├─ QuotesGallery.jsx  (3,052 B)
│  │  │  │  ├─ TimelineSection.jsx  (6,129 B)
│  │  │  │  ├─ WorksList.jsx  (2,149 B)
│  │  │  │  └─ tokens.js  (735 B)
│  │  │  ├─ AvatarUpload.jsx  (6,779 B)  — 头像上传
│  │  │  ├─ ChapterReader.jsx  (38,390 B)  — 章节阅读器
│  │  │  ├─ CountUp.jsx  (1,268 B)  — 数字滚动动画
│  │  │  ├─ ErrorBoundary.jsx  (1,440 B)  — 错误边界
│  │  │  ├─ Footer.jsx  (2,466 B)  — 页脚
│  │  │  ├─ Icon.jsx  (625 B)  — 图标组件
│  │  │  ├─ NavBar.jsx  (4,356 B)  — 顶部导航
│  │  │  ├─ PhilosopherConstellation.jsx  (9,510 B)  — 哲学家星丛图
│  │  │  ├─ ReadingProgress.jsx  (1,142 B)  — 阅读进度条
│  │  │  ├─ ScrollToTop.jsx  (939 B)  — 回到顶部
│  │  │  ├─ SectionReveal.jsx  (827 B)  — 滚动渐显动画
│  │  │  └─ WorldMap.jsx  (11,234 B)  — 世界地图（思想地理）
│  │  ├─ contexts/  — React 上下文
│  │  │  └─ ToastContext.jsx  (1,636 B)  — 全局提示（Toast）
│  │  ├─ data/  — 前端静态数据
│  │  │  ├─ answer_book.json  (96,205 B)
│  │  │  ├─ cache.js  (493 B)
│  │  │  ├─ chatSessions.js  (2,722 B)
│  │  │  ├─ coverUrls.js  (2,871 B)
│  │  │  ├─ crypto.js  (4,017 B)
│  │  │  ├─ dailyQuotes.js  (95,633 B)
│  │  │  ├─ ossUrls.js  (1,114 B)
│  │  │  ├─ phti_original_types.json  (3,490 B)
│  │  │  ├─ phti_questions.json  (72,115 B)
│  │  │  ├─ phti_silly_questions.json  (30,844 B)
│  │  │  ├─ schoolRanking.js  (6,572 B)
│  │  │  ├─ tagMaps.js  (9,724 B)
│  │  │  └─ userData.js  (6,606 B)
│  │  ├─ pages/  — 前端页面
│  │  │  ├─ AnswerBookPage.jsx  (3,891 B)  — 答案之书
│  │  │  ├─ AuthorDetailPage.jsx  (9,880 B)  — 哲学家详情
│  │  │  ├─ AuthorsPage.jsx  (19,659 B)  — 哲学家列表
│  │  │  ├─ BookDetailPage.jsx  (10,537 B)  — 书籍详情
│  │  │  ├─ BooksPage.jsx  (10,850 B)  — 书库列表
│  │  │  ├─ DeveloperPage.jsx  (5,322 B)  — 开发者后台（访问统计）
│  │  │  ├─ EasternPhilosophiesPage.jsx  (8,014 B)  — 东方哲学
│  │  │  ├─ GamesPage.jsx  (2,167 B)  — 小游戏
│  │  │  ├─ GenealogyPage.jsx  (28,630 B)  — 思想谱系图
│  │  │  ├─ HomePage.css  (10,359 B)
│  │  │  ├─ HomePage.jsx  (7,597 B)  — 首页
│  │  │  ├─ PHTIPage.jsx  (15,554 B)  — PHTI 哲学类型测试
│  │  │  ├─ PHTISillyPage.jsx  (15,252 B)  — PHTI 离谱版测试
│  │  │  ├─ PrivacyPage.jsx  (2,276 B)  — 隐私政策
│  │  │  ├─ ProfileEditPage.jsx  (6,337 B)  — 个人资料编辑
│  │  │  ├─ ProfilePage.jsx  (24,196 B)  — 个人中心
│  │  │  ├─ QAPage.jsx  (15,819 B)  — AI 问答（流式 + 自配 key 直连）
│  │  │  ├─ ReaderPage.jsx  (26,712 B)  — 阅读器（PDF/章节 + 批注/书聊）
│  │  │  ├─ SchoolDetailPage.jsx  (34,809 B)  — 学派详情
│  │  │  ├─ SettingsPage.jsx  (6,422 B)  — 设置
│  │  │  ├─ TermsPage.jsx  (1,730 B)  — 服务条款
│  │  │  ├─ WesternPhilosophiesPage.jsx  (9,458 B)  — 西方哲学
│  │  │  └─ WorldPhilosophiesPage.jsx  (14,062 B)  — 世界哲学
│  │  ├─ utils/  — 前端工具
│  │  │  ├─ api.js  (701 B)  — API 封装（生产同源/兜底链）
│  │  │  └─ seo.js  (1,280 B)  — SEO 工具
│  │  ├─ App.css  (32,485 B)
│  │  ├─ App.jsx  (9,419 B)  — 应用入口/路由
│  │  ├─ data.js  (2,663 B)  — 前端全局数据
│  │  ├─ index.css  (1,070 B)
│  │  └─ main.jsx  (527 B)  — 入口挂载
│  ├─ .env  (286 B)
│  ├─ eslint.config.js  (750 B)
│  ├─ index.html  (4,220 B)
│  ├─ package-lock.json  (232,945 B)
│  ├─ package.json  (1,245 B)
│  ├─ postbuild.mjs  (3,429 B)
│  ├─ skills-lock.json  (3,268 B)
│  ├─ vercel.json  (72 B)
│  └─ vite.config.js  (6,343 B)
├─ backend/  # 93 文件
├─ data/
│  ├─ ai_author/  # 尼采 LoRA 生产数据 (6 子目录, 210 文件, 约 1.7G — 保留)
│  ├─ corpus/
│  │  ├─ books/
│  │  │  ├─ bios/
│  │  │  │  ├─ 尼采-牛津通识读本.epub  (196,975 B)
│  │  │  │  ├─ 尼采.pdf  (5,055,979 B)
│  │  │  │  ├─ 尼采与哲学.pdf  (2,021,685 B)
│  │  │  │  ├─ 尼采传.epub  (367,632 B)
│  │  │  │  ├─ 当尼采哭泣.epub  (481,077 B)
│  │  │  │  ├─ 最伟大的思想家 - 尼采.pdf  (5,128,997 B)
│  │  │  │  └─ 瞧，这个人.pdf  (1,514,252 B)
│  │  │  ├─ works/
│  │  │  │  ├─ 不合时宜的沉思.pdf  (21,418,313 B)
│  │  │  │  ├─ 人性的，太人性的.pdf  (8,475,343 B)
│  │  │  │  ├─ 偶像的黄昏.epub  (317,345 B)
│  │  │  │  ├─ 反基督.pdf  (5,043,004 B)
│  │  │  │  ├─ 善恶的彼岸.pdf  (36,081,580 B)
│  │  │  │  ├─ 尼采最后的文字.pdf  (77,847,266 B)
│  │  │  │  ├─ 尼采著作全集（第12卷）.pdf  (18,284,159 B)
│  │  │  │  ├─ 尼采诗歌新编.epub  (305,800 B)
│  │  │  │  ├─ 悲剧的诞生.pdf  (1,673,088 B)
│  │  │  │  ├─ 朝霞.pdf  (99,728,718 B)
│  │  │  │  ├─ 权力意志：重估一切价值的尝试.epub  (244,139 B)
│  │  │  │  ├─ 狄俄尼索斯颂歌.pdf  (82,670,619 B)
│  │  │  │  ├─ 瓦格纳事件.epub  (5,471,383 B)
│  │  │  │  └─ 论道德的谱系.pdf  (5,126,069 B)
│  │  │  └─ _collection_查拉图斯特拉如是说.epub.bak  (3,799,898 B)
│  │  ├─ checkpoints/
│  │  │  ├─ _inspect.py  (2,328 B)
│  │  │  ├─ _probe.py  (914 B)
│  │  │  ├─ para_llm_反基督.json  (276 B)
│  │  │  ├─ para_llm_尼采最后的文字.json  (39 B)
│  │  │  ├─ para_llm_狄俄尼索斯颂歌.json  (654 B)
│  │  │  ├─ sub_人性的_太人性的.json  (1,086,537 B)
│  │  │  ├─ sub_反基督.json  (450,943 B)
│  │  │  ├─ sub_善恶的彼岸.json  (523,460 B)
│  │  │  ├─ sub_尼采最后的文字.json  (113,189 B)
│  │  │  ├─ sub_尼采著作全集_第12卷_.json  (857,829 B)
│  │  │  ├─ sub_狄俄尼索斯颂歌.json  (462,060 B)
│  │  │  ├─ sub_瞧_这个人.json  (214,272 B)
│  │  │  ├─ 人性的_太人性的.json  (489,932 B)
│  │  │  ├─ 人性的_太人性的_failed.json  (19,305 B)
│  │  │  ├─ 反基督.json  (1,750 B)
│  │  │  ├─ 反基督_failed.json  (4,648 B)
│  │  │  ├─ 尼采.json  (177,283 B)
│  │  │  ├─ 尼采与哲学.json  (531,212 B)
│  │  │  ├─ 最伟大的思想家_-_尼采.json  (232,240 B)
│  │  │  └─ 瞧_这个人.json  (211,281 B)
│  │  ├─ chunks/
│  │  │  ├─ all_chunks.json  (453,267,445 B)
│  │  │  ├─ 人性的_太人性的_chunks.json  (1,040,138 B)
│  │  │  ├─ 反基督_chunks.json  (530,146 B)
│  │  │  ├─ 善恶的彼岸_chunks.json  (628,854 B)
│  │  │  ├─ 尼采最后的文字_chunks.json  (142,366 B)
│  │  │  ├─ 尼采著作全集_第12卷_chunks.json  (1,149,621 B)
│  │  │  └─ 狄俄尼索斯颂歌_chunks.json  (610,377 B)
│  │  ├─ clean/
│  │  │  ├─ 不合时宜的沉思.json  (688,703 B)
│  │  │  ├─ 人性的_太人性的.json  (992,517 B)
│  │  │  ├─ 偶像的黄昏.json  (306,630 B)
│  │  │  ├─ 反基督.json  (435,322 B)
│  │  │  ├─ 善恶的彼岸.json  (541,622 B)
│  │  │  ├─ 尼采-牛津通识读本.json  (217,423 B)
│  │  │  ├─ 尼采.json  (170,058 B)
│  │  │  ├─ 尼采与哲学.json  (517,165 B)
│  │  │  ├─ 尼采传.json  (637,223 B)
│  │  │  ├─ 尼采最后的文字.json  (100,792 B)
│  │  │  ├─ 尼采著作全集_第12卷_.json  (826,647 B)
│  │  │  ├─ 尼采诗歌新编.json  (209,195 B)
│  │  │  ├─ 当尼采哭泣.json  (725,435 B)
│  │  │  ├─ 快乐的科学.json  (737,325 B)
│  │  │  ├─ 悲剧的诞生.json  (662,956 B)
│  │  │  ├─ 最伟大的思想家_-_尼采.json  (226,342 B)
│  │  │  ├─ 朝霞.json  (666,303 B)
│  │  │  ├─ 权力意志_重估一切价值的尝试.json  (442,930 B)
│  │  │  ├─ 查拉图斯特拉如是说.json  (786,888 B)
│  │  │  ├─ 狄俄尼索斯颂歌.json  (438,207 B)
│  │  │  ├─ 瓦格纳事件.json  (557,384 B)
│  │  │  ├─ 瞧_这个人.json  (215,107 B)
│  │  │  └─ 论道德的谱系.json  (299,968 B)
│  │  ├─ clean_backup/
│  │  │  ├─ 不合时宜的沉思.json  (686,670 B)
│  │  │  ├─ 人性的_太人性的.json  (1,063,159 B)
│  │  │  ├─ 偶像的黄昏.json  (305,381 B)
│  │  │  ├─ 反基督.json  (455,497 B)
│  │  │  ├─ 善恶的彼岸.json  (531,344 B)
│  │  │  ├─ 尼采-牛津通识读本.json  (223,890 B)
│  │  │  ├─ 尼采.json  (184,962 B)
│  │  │  ├─ 尼采与哲学.json  (536,614 B)
│  │  │  ├─ 尼采传.json  (635,165 B)
│  │  │  ├─ 尼采最后的文字.json  (111,121 B)
│  │  │  ├─ 尼采著作全集_第12卷_.json  (843,981 B)
│  │  │  ├─ 尼采诗歌新编.json  (204,923 B)
│  │  │  ├─ 当尼采哭泣.json  (717,526 B)
│  │  │  ├─ 快乐的科学.json  (727,148 B)
│  │  │  ├─ 悲剧的诞生.json  (677,114 B)
│  │  │  ├─ 最伟大的思想家_-_尼采.json  (233,693 B)
│  │  │  ├─ 朝霞.json  (657,746 B)
│  │  │  ├─ 权力意志_重估一切价值的尝试.json  (439,425 B)
│  │  │  ├─ 查拉图斯特拉如是说.json  (775,091 B)
│  │  │  ├─ 狄俄尼索斯颂歌.json  (463,320 B)
│  │  │  ├─ 瓦格纳事件.json  (556,131 B)
│  │  │  ├─ 瞧_这个人.json  (209,535 B)
│  │  │  └─ 论道德的谱系.json  (300,788 B)
│  │  ├─ evaluation/
│  │  │  ├─ chunks_text_pre_para.json  (13,617,074 B)
│  │  │  ├─ compare_deepseek-chat.jsonl  (32,225 B)
│  │  │  ├─ compare_glm-4-flash.jsonl  (26,611 B)
│  │  │  ├─ cross_judged.jsonl  (36,258,225 B)
│  │  │  ├─ eval_report.json  (2,324 B)
│  │  │  ├─ evaluation_report.html  (25,021 B)
│  │  │  ├─ evaluation_report.json  (50,511 B)
│  │  │  ├─ evaluation_report_final.html  (27,419 B)
│  │  │  ├─ evaluation_report_v2.html  (50,491 B)
│  │  │  ├─ qa_details.json  (94,356 B)
│  │  │  ├─ raw_eval.jsonl  (56,776,297 B)
│  │  │  ├─ raw_eval_baseline_standard.jsonl  (86,046,869 B)
│  │  │  ├─ retrieval_details.json  (42,420 B)
│  │  │  ├─ scored_eval.jsonl  (56,804,489 B)
│  │  │  └─ test_set.json  (155,250 B)
│  │  ├─ external/
│  │  │  ├─ se_nietzsche.json  (171,992 B)
│  │  │  └─ se_nietzsche_zh.json  (160,677 B)
│  │  ├─ lora/
│  │  │  ├─ raw_aphorisms.jsonl  (2,874,574 B)
│  │  │  ├─ test_data.jsonl  (55,309 B)
│  │  │  └─ train_data.jsonl  (2,980,700 B)
│  │  ├─ raw/  # 41 文件
│  │  ├─ .indexed_books  (511 B)
│  │  ├─ backfill_report.json  (134 B)
│  │  ├─ book_metadata.json  (6,216 B)
│  │  ├─ corpus_tiers.json  (2,380 B)
│  │  ├─ name_keys.json  (798 B)
│  │  └─ restructure_report.json  (3,528 B)
│  ├─ graph/
│  │  ├─ external/
│  │  │  ├─ people.json  (10,391 B)
│  │  │  ├─ timeline.json  (7,881 B)
│  │  │  └─ works.json  (4,419 B)
│  │  ├─ argument_extraction_checkpoint.json  (27,151,645 B)
│  │  ├─ argument_spotcheck.json  (125 B)
│  │  ├─ cleanup_applied.json  (99,132 B)
│  │  ├─ cleanup_candidates.json  (505,637 B)
│  │  ├─ cleanup_pass2.json  (107,373 B)
│  │  ├─ cypher_templates.md  (5,533 B)
│  │  ├─ dangling_fixes.json  (33,810 B)
│  │  ├─ dropped_relations.json  (2,797 B)
│  │  ├─ enrichment_candidates.json  (346 B)
│  │  ├─ extraction_checkpoint.json  (2,317,647 B)
│  │  ├─ import.cypher  (770,324 B)
│  │  ├─ import_final.cypher  (758,649 B)
│  │  ├─ knowledge_graph.json  (1,405,431 B)
│  │  ├─ knowledge_graph_final.json  (1,432,754 B)
│  │  ├─ knowledge_graph_v2.json  (1,363,087 B)
│  │  ├─ knowledge_graph_v3.json  (1,360,228 B)
│  │  ├─ knowledge_graph_v4.json  (1,370,318 B)
│  │  ├─ knowledge_graph_v5.json  (1,331,611 B)
│  │  ├─ knowledge_graph_v6.json  (596,113 B)
│  │  ├─ knowledge_graph_v6_pass1.json  (966,777 B)
│  │  ├─ knowledge_graph_v7.json  (61,305,275 B)
│  │  ├─ llm_sample.json  (8,960 B)
│  │  ├─ llm_spotcheck_result.json  (18,951 B)
│  │  ├─ merge_aliases.json  (7,333 B)
│  │  ├─ noise_entities.json  (15,037 B)
│  │  └─ quality_report.json  (1,903 B)
│  ├─ memory/
│  │  ├─ checkpoints/
│  │  │  └─ memory_checkpoint.json  (207,361 B)
│  │  ├─ anecdotes.json  (6,994 B)
│  │  └─ nietzsche_memories.json  (222,601 B)
│  ├─ persona/
│  │  ├─ external/
│  │  │  └─ 弗里德里希·尼采.json  (3,820 B)
│  │  ├─ contradiction_rules.json  (5,238 B)
│  │  ├─ persona_model.json  (13,977 B)
│  │  ├─ persona_snapshots.json  (3,131 B)
│  │  └─ style_lexicon.json  (9,105 B)
│  ├─ user_model/
│  │  ├─ difficulty_levels.json  (2,140 B)
│  │  ├─ misconceptions.json  (13,660 B)
│  │  └─ user_profiles.json  (17,419 B)
│  └─ vector/
│     ├─ embeddings/  # 向量库: index.json (0 条 {bid,idx,title,hash}) + vectors.npy (float32 0×1024)
│     ├─ qdrant/
│     │  ├─ collection/
│     │  │  └─ nietzsche_corpus/
│     │  │     └─ storage.sqlite  (378,380,288 B)
│     │  ├─ .lock  (13 B)
│     │  └─ meta.json  (517 B)
│     ├─ nietzsche_chunks.jsonl  (13,916,568 B)
│     ├─ nietzsche_meta.json  (1,998,076 B)
│     └─ nietzsche_vectors.npy  (26,574,976 B)
├─ docs/
│  ├─ agent/
│  │  ├─ AUTONOMOUS_HANDOFF_CONTRACT.json  (6,069 B)
│  │  ├─ README.md  (516 B)
│  │  ├─ academic-roadmap.md  (10,390 B)
│  │  ├─ account-memory.md  (5,986 B)
│  │  ├─ autonomous-loop-state.md  (17,284 B)
│  │  ├─ current-state.md  (1,316 B)
│  │  └─ soul-preview.md  (3,828 B)
│  ├─ archive/
│  │  ├─ agent/  # 37 文件
│  │  ├─ library/
│  │  │  └─ zlib-batch-status.md  (1,895 B)
│  │  ├─ snapshots/
│  │  │  ├─ handover-2026-09-06.md  (19,280 B)
│  │  │  └─ nowstate.md  (10,076 B)
│  │  ├─ tasks/  # 75 文件
│  │  ├─ ui/
│  │  │  └─ ui-optimization-2026-08-18.md  (15,345 B)
│  │  └─ README.md  (606 B)
│  ├─ course/
│  │  ├─ chapters/
│  │  │  ├─ 00-learning-map-and-environment.md  (4,425 B)
│  │  │  ├─ 01-python-migration.md  (4,868 B)
│  │  │  ├─ 02-python-engineering.md  (4,389 B)
│  │  │  ├─ 03-async-and-lifecycle.md  (4,011 B)
│  │  │  ├─ 04-http-and-fastapi.md  (3,978 B)
│  │  │  ├─ 05-sql-and-conversations.md  (3,597 B)
│  │  │  ├─ 06-javascript-migration.md  (4,366 B)
│  │  │  ├─ 07-html-and-css.md  (3,684 B)
│  │  │  ├─ 08-promises-fetch-and-streaming.md  (4,003 B)
│  │  │  ├─ 09-react-workspace.md  (4,040 B)
│  │  │  ├─ 10-model-api-protocol.md  (3,527 B)
│  │  │  ├─ 11-prompts-and-context.md  (4,077 B)
│  │  │  ├─ 12-manual-agent-loop.md  (3,881 B)
│  │  │  ├─ 13-langgraph-state.md  (3,864 B)
│  │  │  ├─ 14-rag-retrieval.md  (3,851 B)
│  │  │  ├─ 15-citations-and-verification.md  (3,604 B)
│  │  │  ├─ 16-library-data-pipeline.md  (3,592 B)
│  │  │  ├─ 17-persona-and-memory.md  (3,953 B)
│  │  │  ├─ 18-research-workflows.md  (3,759 B)
│  │  │  ├─ 19-mcp-and-files.md  (3,689 B)
│  │  │  ├─ 20-authentication.md  (3,870 B)
│  │  │  ├─ 21-testing-and-observability.md  (3,481 B)
│  │  │  ├─ 22-implementation-order.md  (3,809 B)
│  │  │  ├─ 23-evidence-and-comparison.md  (3,344 B)
│  │  │  ├─ 24-debugging-and-self-check.md  (3,914 B)
│  │  │  ├─ 25-official-sources.md  (3,511 B)
│  │  │  ├─ 26-python-architecture.md  (4,731 B)
│  │  │  ├─ 27-javascript-typescript.md  (4,234 B)
│  │  │  ├─ 28-requirements-to-features.md  (4,089 B)
│  │  │  └─ 29-graduation-project.md  (3,596 B)
│  │  ├─ README.md  (7,477 B)
│  │  ├─ complete-course.md  (158,475 B)
│  │  ├─ exercise-solutions.md  (5,881 B)
│  │  ├─ first-tool.md  (3,494 B)
│  │  ├─ graduation-checklist.md  (7,491 B)
│  │  ├─ learning-plan.md  (2,304 B)
│  │  ├─ source-code-guide.md  (6,483 B)
│  │  ├─ source-tools.md  (12,110 B)
│  │  └─ validation-record.md  (2,488 B)
│  ├─ evaluation/
│  │  ├─ README.md  (623 B)
│  │  ├─ benchmark-ledger.md  (43,709 B)
│  │  └─ version-comparison.md  (1,834 B)
│  ├─ evidence/  # 341 文件
│  ├─ library/
│  │  ├─ README.md  (579 B)
│  │  ├─ expansion-plan.md  (6,266 B)
│  │  ├─ manual-downloads.md  (8,618 B)
│  │  ├─ research-database-operations.md  (6,687 B)
│  │  ├─ research-database-scale-plan.md  (7,099 B)
│  │  ├─ shell-inventory.md  (11,018 B)
│  │  └─ shell-triage.md  (8,642 B)
│  ├─ operations/
│  │  ├─ README.md  (318 B)
│  │  ├─ agent-deployment.md  (6,617 B)
│  │  ├─ database.md  (1,890 B)
│  │  └─ deployment.md  (13,222 B)
│  ├─ phiagent-course/
│  │  ├─ PhiAgent教程与代码.zip  (217,301 B)
│  │  └─ assemble.py  (2,597 B)
│  ├─ reference/
│  │  ├─ docs-cleanup-validation-2026-10-03.json  (798 B)
│  │  ├─ docs-migration-2026-10-03.json  (87,348 B)
│  │  └─ project-structure.md  (37,864 B)
│  ├─ tasks/
│  │  └─ README.md  (365 B)
│  ├─ ui/
│  │  ├─ README.md  (502 B)
│  │  ├─ conversation-workspace-design-v1.0.md  (21,066 B)
│  │  ├─ conversation-workspace-refactor.md  (13,790 B)
│  │  ├─ design-system.md  (2,883 B)
│  │  ├─ information-architecture.md  (3,199 B)
│  │  ├─ interaction-spec.md  (3,847 B)
│  │  ├─ responsive-spec.md  (1,690 B)
│  │  ├─ uat.md  (4,745 B)
│  │  └─ ui-audit.md  (3,325 B)
│  ├─ README.md  (1,187 B)
│  ├─ naming.md  (1,588 B)
│  └─ 分章标准规范.md  (7,223 B)
├─ examples/
│  └─ phiagent-lab/
│     ├─ exercises/
│     │  ├─ __init__.py  (92 B)
│     │  ├─ advanced.py  (3,818 B)
│     │  ├─ corpus.py  (3,494 B)
│     │  ├─ evaluate.py  (1,429 B)
│     │  ├─ manual_agent.py  (1,154 B)
│     │  ├─ migration.mjs  (577 B)
│     │  ├─ migration.py  (563 B)
│     │  └─ ownership.mjs  (592 B)
│     ├─ phiagent_lab/
│     │  ├─ __init__.py  (81 B)
│     │  ├─ app.py  (4,190 B)
│     │  ├─ cli.py  (684 B)
│     │  ├─ engine.py  (4,430 B)
│     │  ├─ library.py  (3,252 B)
│     │  ├─ model.py  (5,304 B)
│     │  └─ store.py  (1,250 B)
│     ├─ react-web/
│     │  ├─ src/
│     │  │  └─ main.jsx  (3,514 B)
│     │  ├─ index.html  (262 B)
│     │  ├─ package-lock.json  (56,205 B)
│     │  ├─ package.json  (294 B)
│     │  └─ vite.config.js  (216 B)
│     ├─ runtime/
│     │  └─ chat.sqlite3  (12,288 B)
│     ├─ tests/
│     │  ├─ ownership.test.mjs  (1,330 B)
│     │  ├─ sse.test.mjs  (1,073 B)
│     │  ├─ test_advanced.py  (1,997 B)
│     │  ├─ test_corpus.py  (1,024 B)
│     │  ├─ test_http_model.py  (2,140 B)
│     │  └─ test_project.py  (4,805 B)
│     ├─ web/
│     │  ├─ app.js  (3,456 B)
│     │  ├─ index.html  (954 B)
│     │  ├─ sse.mjs  (1,377 B)
│     │  └─ style.css  (1,008 B)
│     ├─ .gitignore  (175 B)
│     ├─ README.md  (3,337 B)
│     ├─ pytest.ini  (42 B)
│     ├─ requirements.lock  (853 B)
│     └─ requirements.txt  (173 B)
├─ outputs/
│  ├─ 01a0bf1f-2e23-7522-b6e1-d5cde17094b2/
│  │  ├─ PhiAgent_学术评分表_v1.1_冻结.xlsx  (22,035 B)
│  │  ├─ PhiAgent_学术评分表_v1.1_冻结.xlsx.inspect.ndjson  (288,818 B)
│  │  ├─ PhiAgent_学术评分表_v1.xlsx  (12,275 B)
│  │  ├─ PhiAgent_学术评分表_v1.xlsx.inspect.ndjson  (107,022 B)
│  │  └─ rubric-v1.json  (4,355 B)
│  ├─ answer-footer-20261002/
│  │  └─ preview.jpg  (55,626 B)
│  ├─ deleted-home-recommendations-20261002/
│  │  ├─ after.png  (43,697 B)
│  │  └─ before.png  (45,762 B)
│  ├─ error-notice-20261002/
│  │  ├─ mobile.png  (11,558 B)
│  │  └─ preview.png  (14,655 B)
│  ├─ memory-settings-20261002/
│  │  ├─ desktop.png  (48,533 B)
│  │  ├─ mobile.png  (36,582 B)
│  │  └─ sidebar.png  (29,515 B)
│  ├─ memory-summary-v2-20261002/
│  │  ├─ desktop-interaction.png  (59,775 B)
│  │  ├─ desktop-summary.png  (63,931 B)
│  │  └─ mobile-interaction.png  (6,606 B)
│  ├─ phiagent-benchmark-ledger/
│  │  └─ score-matrix.png  (261,285 B)
│  ├─ primary-links-20261002/
│  │  ├─ links.jpg  (18,660 B)
│  │  └─ reader-ch17.jpg  (162,264 B)
│  ├─ quote-render-20261002/
│  │  ├─ desktop.png  (36,496 B)
│  │  └─ mobile.png  (32,787 B)
│  ├─ settings-unified-20261002/
│  │  ├─ desktop.png  (26,461 B)
│  │  └─ mobile.png  (21,287 B)
│  ├─ tool-results-20261002/
│  │  └─ preview.jpg  (30,952 B)
│  ├─ phiagent-account-home-preview.jpg  (46,373 B)
│  └─ phiagent-mobile-answer-fixed.jpg  (23,633 B)
├─ scripts/  — 内容运营与历史运维脚本（38 个, 多数一次性已完成）
│  ├─ archive/
│  │  ├─ agnes_direct_test.py  (1,902 B)
│  │  ├─ agnes_quick_test.py  (2,628 B)
│  │  ├─ ai_verify_all.py  (4,904 B)
│  │  ├─ ai_verify_batch.py  (8,395 B)
│  │  ├─ ai_verify_portraits.py  (5,350 B)
│  │  ├─ audit_all_chapters.py  (3,571 B)
│  │  ├─ batch_extract.py  (2,375 B)
│  │  ├─ batch_import_books.py  (10,185 B)
│  │  ├─ check_all_books.py  (3,527 B)
│  │  ├─ check_portraits.py  (7,919 B)
│  │  ├─ cleanup_portraits.py  (6,082 B)
│  │  ├─ dedup_philosophers.py  (4,644 B)
│  │  ├─ delete_wrong_images.py  (2,318 B)
│  │  ├─ expand_bios.py  (3,667 B)
│  │  ├─ extract_one.py  (5,774 B)
│  │  ├─ fetch_bing_portraits.py  (6,154 B)
│  │  ├─ fetch_philosopher_batch.py  (2,632 B)
│  │  ├─ fetch_wiki_zh.py  (6,413 B)
│  │  ├─ fix_bad_chapters.py  (2,732 B)
│  │  ├─ fix_book_ids.py  (5,334 B)
│  │  ├─ fix_english_names.py  (3,753 B)
│  │  ├─ fix_map_coords.py  (2,647 B)
│  │  ├─ test_extract.py  (837 B)
│  │  └─ verify_all_portraits.py  (14,919 B)
│  ├─ README.md  (915 B)
│  ├─ _lib.py  (5,675 B)  — 共享工具模块（load/save JSON + DeepSeek/Agnes 客户端）
│  ├─ add_author.py  (7,914 B)  — 一键新增哲人（DeepSeek 生成信息 → public JSON）
│  ├─ add_book.py  (7,492 B)  — 一键新增书籍（本地扫描 → 标签摘要 → 入库）
│  ├─ add_school.py  (21,663 B)  — 一键新增流派（全流程自动化）
│  ├─ add_subschool.py  (13,210 B)  — 一键新增下属流派（轻量版）
│  ├─ build_phiagent_static.py  (1,668 B)
│  ├─ fetch_philosopher_img.py  (7,769 B)  — 哲学家头像爬取（Wikipedia/Wikimedia）  [已归档]
│  ├─ fetch_portraits.py  (10,678 B)  — 哲学家肖像自动爬取 + AI 验证
│  ├─ find_translations.py  (5,014 B)  — 分析书籍找缺中译本的西哲著作
│  ├─ gen_portrait.py  (7,070 B)  — AI 生成哲学家肖像（Wikipedia 无画像的古代哲人）  [已归档]
│  ├─ gen_school_bg.py  (7,895 B)  — 流派背景图生成器（两阶段）
│  ├─ gen_tags_batch.py  (4,696 B)  — 为新书批量生成标签 + 摘要
│  ├─ list_missing.py  (957 B)  — 列出缺图哲学家
│  └─ score_item.py  (2,904 B)  — 哲学家/书籍五维度 AI 评分
├─ workers/
│  ├─ api/
│  │  ├─ dist-check/
│  │  │  ├─ README.md  (119 B)
│  │  │  ├─ index.js  (191,362 B)  — 构建产物（dist）
│  │  │  └─ index.js.map  (303,963 B)
│  │  ├─ migrations/  — D1 迁移 SQL
│  │  │  ├─ 001_schema.sql  (1,581 B)  — D1 建表
│  │  │  ├─ 002_import.sql  (27,446 B)  — 旧数据导入 SQL
│  │  │  └─ 003_agent_conversations.sql  (513 B)
│  │  ├─ src/  — api worker 源码与构建资产
│  │  │  ├─ admin_stats.json  (2,143 B)  — 构建产物：管理统计快照
│  │  │  ├─ books.json  (81,025 B)  — 构建产物：书 id → 文件直链映射
│  │  │  ├─ index.js  (25,259 B)  — api worker：业务端点 + JWT + SSE 透传
│  │  │  └─ stats.json  (51 B)  — 构建产物：访问统计快照
│  │  ├─ package-lock.json  (585 B)
│  │  ├─ package.json  (142 B)
│  │  └─ wrangler.toml  (701 B)  — api worker 配置（D1 绑定/路由）
│  └─ auth/
│     ├─ src/  — auth worker 源码
│     │  └─ index.js  (9,103 B)  — auth worker：登录/注册/JWT
│     ├─ .dev.vars  (39 B)
│     ├─ package-lock.json  (589 B)
│     ├─ package.json  (143 B)
│     └─ wrangler.toml  (524 B)  — auth worker 配置
├─ .dockerignore  (226 B)
├─ .env  (1,727 B)
├─ .gitattributes  (821 B)
├─ .gitignore  (2,451 B)
├─ .zcodeignore  (3,053 B)
├─ AGENTS.md  (8,206 B)
├─ README.md  (6,946 B)
├─ requirements.lock  (14,701 B)
├─ requirements.txt  (860 B)
└─ vercel.json  (62 B)
```
