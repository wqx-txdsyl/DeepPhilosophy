# DeepPhilosophy 全文件结构图

> 生成时间: 2026-08-14 21:25 · 排除 .git / node_modules / .venv / __pycache__ / .wrangler / dist
> 大数据目录 (章节库 / 向量库 / 封面 / ai_author) 折叠为计数摘要

## DeepPhilosophy × PhiAgent 合并后单仓库（2026-08-14: 平台 + 智能体 + 书库工具）

```
F:\program\Python\DeepPhilosophy
├─ .github/
│  └─ workflows/
│     └─ consistency-check.yml  (269 B)
├─ agent-app/
│  ├─ public/  # agent 前端静态数据（本地工作副本, 不入库）
│  ├─ src/
│  │  ├─ components/
│  │  │  ├─ AgentSidebar.jsx  (6,351 B)
│  │  │  ├─ AuthModal.jsx  (4,322 B)
│  │  │  ├─ DrawioInline.jsx  (1,407 B)
│  │  │  ├─ DrawioModal.jsx  (2,042 B)
│  │  │  ├─ Icon.jsx  (625 B)
│  │  │  └─ UserCenterModal.jsx  (12,351 B)
│  │  ├─ data/
│  │  │  ├─ answer_book.json  (96,205 B)
│  │  │  ├─ cache.js  (493 B)
│  │  │  ├─ chatSessions.js  (2,722 B)
│  │  │  ├─ coverUrls.js  (1,199 B)
│  │  │  ├─ crypto.js  (4,017 B)
│  │  │  ├─ dailyQuotes.js  (96,420 B)
│  │  │  ├─ phti_original_types.json  (3,490 B)
│  │  │  ├─ phti_questions.json  (74,596 B)
│  │  │  ├─ phti_silly_questions.json  (31,845 B)
│  │  │  ├─ schoolRanking.js  (6,572 B)
│  │  │  ├─ tagMaps.js  (7,928 B)
│  │  │  └─ userData.js  (6,463 B)
│  │  ├─ pages/
│  │  │  └─ AgentPage.jsx  (38,866 B)
│  │  ├─ utils/
│  │  │  ├─ api.js  (87 B)
│  │  │  ├─ i18n.jsx  (11,710 B)
│  │  │  └─ theme.js  (739 B)
│  │  ├─ App.jsx  (1,013 B)
│  │  ├─ auth.jsx  (2,529 B)
│  │  ├─ index.css  (1,022 B)
│  │  └─ main.jsx  (235 B)
│  ├─ index.html  (350 B)
│  ├─ package-lock.json  (101,898 B)
│  ├─ package.json  (449 B)
│  └─ vite.config.js  (310 B)
├─ app/
│  ├─ electron/
│  │  └─ main.cjs  (1,427 B)
│  ├─ public/  — 前端静态资源（被 gitignore）
│  │  ├─ backend/
│  │  │  └─ data/
│  │  │     └─ book_chapters/  # 318 本书 × 12481 个章节 json (按 bid 分目录, 顶层 dict 禁 list)
│  │  ├─ book_detail/  # 407 个 detail json (三处同步规则: PHA/DP/app public)
│  │  ├─ covers/  # 前端静态资源 (407 文件)
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
│  │  ├─ philosopher/  # 前端静态资源 (617 文件)
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
│  │  ├─ books.json  (583,956 B)
│  │  ├─ covers.json  (21,587 B)
│  │  ├─ favicon.png  (11,953 B)
│  │  ├─ favicon.svg  (9,522 B)
│  │  ├─ icons.svg  (5,031 B)
│  │  ├─ manifest.json  (705 B)
│  │  ├─ philosopher_network.json  (394,531 B)
│  │  ├─ philosophers.json  (3,030,438 B)
│  │  ├─ robots.txt  (71 B)
│  │  ├─ sitemap.xml  (1,074 B)
│  │  └─ sw.js  (1,890 B)
│  ├─ src/
│  │  ├─ assets/  — 前端打包资源
│  │  │  ├─ fonts/
│  │  │  │  ├─ playfair-latin-400-italic.woff2  (21,884 B)
│  │  │  │  ├─ playfair-latin-400-normal.woff2  (21,856 B)
│  │  │  │  ├─ playfair-latin-500-italic.woff2  (23,076 B)
│  │  │  │  ├─ playfair-latin-500-normal.woff2  (23,048 B)
│  │  │  │  ├─ playfair-latin-600-normal.woff2  (23,228 B)
│  │  │  │  └─ playfair-latin-700-normal.woff2  (23,224 B)
│  │  │  └─ books.json  (583,450 B)
│  │  ├─ components/  — 前端组件
│  │  │  ├─ school/  — 学派详情组件
│  │  │  │  ├─ ConstellationMap.jsx  (14,062 B)
│  │  │  │  ├─ EpilogueSection.jsx  (2,831 B)
│  │  │  │  ├─ GlossaryCloud.jsx  (3,663 B)
│  │  │  │  ├─ HeroSection.jsx  (4,030 B)
│  │  │  │  ├─ OverviewSection.jsx  (2,673 B)
│  │  │  │  ├─ QuotesGallery.jsx  (3,052 B)
│  │  │  │  ├─ TimelineSection.jsx  (6,129 B)
│  │  │  │  ├─ WorksList.jsx  (2,149 B)
│  │  │  │  └─ tokens.js  (735 B)
│  │  │  ├─ AvatarUpload.jsx  (6,779 B)  — 头像上传
│  │  │  ├─ ChapterReader.jsx  (37,645 B)  — 章节阅读器
│  │  │  ├─ CountUp.jsx  (1,268 B)  — 数字滚动动画
│  │  │  ├─ ErrorBoundary.jsx  (1,489 B)  — 错误边界
│  │  │  ├─ Footer.jsx  (2,493 B)  — 页脚
│  │  │  ├─ Icon.jsx  (625 B)  — 图标组件
│  │  │  ├─ NavBar.jsx  (4,356 B)  — 顶部导航
│  │  │  ├─ PhilosopherConstellation.jsx  (9,510 B)  — 哲学家星丛图
│  │  │  ├─ ReadingProgress.jsx  (1,142 B)  — 阅读进度条
│  │  │  ├─ ScrollToTop.jsx  (939 B)  — 回到顶部
│  │  │  ├─ SectionReveal.jsx  (827 B)  — 滚动渐显动画
│  │  │  └─ WorldMap.jsx  (11,408 B)  — 世界地图（思想地理）
│  │  ├─ contexts/  — React 上下文
│  │  │  └─ ToastContext.jsx  (1,636 B)  — 全局提示（Toast）
│  │  ├─ data/  — 前端静态数据
│  │  │  ├─ answer_book.json  (96,205 B)
│  │  │  ├─ cache.js  (493 B)
│  │  │  ├─ chatSessions.js  (2,722 B)
│  │  │  ├─ coverUrls.js  (2,871 B)
│  │  │  ├─ crypto.js  (4,017 B)
│  │  │  ├─ dailyQuotes.js  (96,420 B)
│  │  │  ├─ ossUrls.js  (1,114 B)
│  │  │  ├─ phti_original_types.json  (3,490 B)
│  │  │  ├─ phti_questions.json  (74,596 B)
│  │  │  ├─ phti_silly_questions.json  (31,845 B)
│  │  │  ├─ schoolRanking.js  (6,572 B)
│  │  │  ├─ tagMaps.js  (7,928 B)
│  │  │  └─ userData.js  (6,606 B)
│  │  ├─ pages/  — 前端页面
│  │  │  ├─ AnswerBookPage.jsx  (3,891 B)  — 答案之书
│  │  │  ├─ AuthorDetailPage.jsx  (10,113 B)  — 哲学家详情
│  │  │  ├─ AuthorsPage.jsx  (19,760 B)  — 哲学家列表
│  │  │  ├─ BookDetailPage.jsx  (10,516 B)  — 书籍详情
│  │  │  ├─ BooksPage.jsx  (11,552 B)  — 书库列表
│  │  │  ├─ DeveloperPage.jsx  (5,443 B)  — 开发者后台（访问统计）
│  │  │  ├─ EasternPhilosophiesPage.jsx  (8,090 B)  — 东方哲学
│  │  │  ├─ GamesPage.jsx  (2,167 B)  — 小游戏
│  │  │  ├─ GenealogyPage.jsx  (29,041 B)  — 思想谱系图
│  │  │  ├─ HomePage.css  (10,048 B)
│  │  │  ├─ HomePage.jsx  (30,737 B)  — 首页
│  │  │  ├─ PHTIPage.jsx  (15,920 B)  — PHTI 哲学类型测试
│  │  │  ├─ PHTISillyPage.jsx  (15,252 B)  — PHTI 离谱版测试
│  │  │  ├─ PrivacyPage.jsx  (2,276 B)  — 隐私政策
│  │  │  ├─ ProfileEditPage.jsx  (6,348 B)  — 个人资料编辑
│  │  │  ├─ ProfilePage.jsx  (23,928 B)  — 个人中心
│  │  │  ├─ QAPage.jsx  (16,242 B)  — AI 问答（流式 + 自配 key 直连）
│  │  │  ├─ ReaderPage.jsx  (26,497 B)  — 阅读器（PDF/章节 + 批注/书聊）
│  │  │  ├─ SchoolDetailPage.jsx  (35,342 B)  — 学派详情
│  │  │  ├─ SettingsPage.jsx  (6,580 B)  — 设置
│  │  │  ├─ TermsPage.jsx  (1,730 B)  — 服务条款
│  │  │  ├─ WesternPhilosophiesPage.jsx  (9,551 B)  — 西方哲学
│  │  │  └─ WorldPhilosophiesPage.jsx  (14,251 B)  — 世界哲学
│  │  ├─ utils/  — 前端工具
│  │  │  ├─ api.js  (701 B)  — API 封装（生产同源/兜底链）
│  │  │  └─ seo.js  (1,280 B)  — SEO 工具
│  │  ├─ App.css  (29,495 B)
│  │  ├─ App.jsx  (9,762 B)  — 应用入口/路由
│  │  ├─ data.js  (2,635 B)  — 前端全局数据
│  │  ├─ index.css  (1,070 B)
│  │  └─ main.jsx  (527 B)  — 入口挂载
│  ├─ .env  (286 B)
│  ├─ eslint.config.js  (568 B)
│  ├─ index.html  (4,279 B)
│  ├─ package-lock.json  (238,775 B)
│  ├─ package.json  (1,266 B)
│  ├─ postbuild.mjs  (3,429 B)
│  ├─ skills-lock.json  (3,268 B)
│  ├─ vercel.json  (72 B)
│  ├─ vite-debug.err.log  (179,124 B)
│  ├─ vite-debug.log  (6,437 B)
│  └─ vite.config.js  (4,396 B)
├─ backend/
│  ├─ data/  — 运行数据（章节库/向量库/catalog）
│  │  ├─ book_chapters/  # 319 本书 × 12548 个章节 json (按 bid 分目录, 顶层 dict 禁 list)
│  │  ├─ book_detail/  # 407 个 detail json (三处同步规则: PHA/DP/app public)
│  │  ├─ book_images/  # 11498 个封面图片文件
│  │  ├─ embeddings/  # 向量库: index.json (12111 条 {bid,idx,title,hash}) + vectors.npy (float32 12111×1024)
│  │  ├─ __init__.py  (0 B)
│  │  ├─ admin_stats.json  (202 B)
│  │  ├─ agent_memory.json  (30,991 B)
│  │  ├─ agent_stats.jsonl  (12,414 B)
│  │  ├─ book_checklist.json  (99,220 B)
│  │  ├─ book_checklist.md  (39,296 B)
│  │  ├─ book_rankings.json  (46,911 B)
│  │  ├─ book_summaries.json  (1,065,316 B)
│  │  ├─ books_catalog.json  (597,838 B)
│  │  ├─ dp_epub_ocr_ckpt.json  (543,463 B)
│  │  ├─ dp_pdf_import_ckpt.json  (22,798,457 B)
│  │  ├─ github_manifest.json  (42,431 B)
│  │  ├─ name_aliases.json  (5,933 B)
│  │  ├─ ocr_launch.log  (193 B)
│  │  ├─ ocr_s0.log  (8,511,386 B)
│  │  ├─ ocr_s0_err.log  (0 B)
│  │  ├─ ocr_watchdog.log  (191,211 B)
│  │  ├─ ocr_watchdog_err.log  (0 B)
│  │  ├─ oss_manifest.json  (65,292 B)
│  │  ├─ philosopher_rankings.json  (123,166 B)
│  │  ├─ philosophers.json  (2,305,015 B)
│  │  ├─ tag_normalization.json  (9,849 B)
│  │  └─ users.db  (90,112 B)
│  ├─ mcp_servers/  — MCP 服务器（外部工具）
│  │  └─ demo_server.py  (655 B)
│  ├─ models/  — Pydantic 模型
│  │  └─ __init__.py  (1,317 B)  — 共享 Pydantic 请求/响应模型
│  ├─ modules/  — 核心功能模块
│  │  ├─ __init__.py  (48 B)
│  │  ├─ document_loader.py  (11,006 B)  — 文档加载（PDF/EPUB/TXT，文本/扫描智能判断）
│  │  ├─ embedding.py  (5,974 B)  — 嵌入模型（文本向量化）
│  │  ├─ llm_client.py  (3,063 B)  — DeepSeek API 客户端（OpenAI 兼容）
│  │  ├─ ocr_engine.py  (3,880 B)  — OCR 引擎（PaddleOCR）
│  │  ├─ rag_chain.py  (4,636 B)  — RAG 检索增强生成链
│  │  ├─ text_processor.py  (6,341 B)  — 文本处理（分词/关键词/摘要）
│  │  └─ vector_store.py  (6,849 B)  — 向量库存储与检索（ChromaDB）
│  ├─ routes/  — 后端 API 路由
│  │  ├─ __init__.py  (0 B)
│  │  ├─ admin_routes.py  (607 B)  — 管理路由
│  │  ├─ agent.py  (110,825 B)  — 智能体核心：29 工具注册表 + stream_lg(LangGraph) + cite（旧引擎已删）
│  │  ├─ ai.py  (7,145 B)  — AI proxy / RAG QA / ASR 路由
│  │  ├─ auth_routes.py  (1,341 B)  — 认证路由
│  │  ├─ health.py  (1,787 B)  — 健康检查与统计
│  │  ├─ history.py  (3,251 B)  — 阅读历史/聊天记录/笔记/书聊
│  │  ├─ knowledge.py  (2,933 B)  — 知识库路由
│  │  ├─ sync.py  (1,637 B)  — 同步路由
│  │  ├─ text.py  (10,788 B)  — 文本提取 API（章节索引 + 单章读取，本地优先 OSS 兜底）
│  │  └─ user.py  (2,578 B)  — 用户路由
│  ├─ services/  — 业务服务
│  │  ├─ __init__.py  (0 B)
│  │  ├─ book_scanner.py  (17,285 B)  — 书库扫描（本地/OSS/GitHub/R2 统一接口）
│  │  ├─ summaries.py  (4,644 B)  — 书籍摘要缓存加载/生成
│  │  └─ tag_utils.py  (5,013 B)  — 标签归一化工具
│  ├─ tests/  — 冒烟测试
│  │  ├─ __init__.py  (0 B)
│  │  ├─ test_config.py  (1,108 B)  — 冒烟测试：配置加载
│  │  ├─ test_health.py  (953 B)  — 冒烟测试：健康检查
│  │  └─ test_philosophers.py  (1,378 B)  — 冒烟测试：哲学家库查找
│  ├─ tools/  — 数据构建/修复/同步工具集
│  │  ├─ data/
│  │  ├─ CHKLIST.md  (142,829 B)
│  │  ├─ OCR_CHECKLIST.md  (14,248 B)
│  │  ├─ README.md  (2,340 B)
│  │  ├─ TOOLS_INDEX.md  (9,347 B)
│  │  ├─ __init__.py  (28 B)
│  │  ├─ build_book_json.py  (12,032 B)  — EPUB/TXT → 结构化 JSON（rebuild_spine 依赖）
│  │  ├─ build_covers_manifest.py  (2,227 B)  — 封面 → public/covers/ + covers.json
│  │  ├─ build_embeddings.py  (4,261 B)  — 章节向量索引构建（智谱 embedding-2）
│  │  ├─ build_philosopher_network.py  (9,323 B)  — 构建哲学家星丛网络（AI 识别思想关系）
│  │  ├─ download_gutenberg.py  (5,428 B)  — Project Gutenberg 下载 EPUB
│  │  ├─ dp_clean_book.py  (48,247 B)  — 单本专项清洗 + 回灌 DP 阅读器格式
│  │  ├─ dp_consistency_check.py  (5,288 B)
│  │  ├─ dp_embed_missing.py  (5,890 B)  — 增量补嵌入（向量维护核心）
│  │  ├─ dp_epub_covers.py  (6,438 B)  — epub 封面补全 + 重建 covers.json
│  │  ├─ dp_fix_authors.py  (3,304 B)  — 作者字段修复
│  │  ├─ dp_fix_catalog_chapters.py  (994 B)  — catalog chapterCount 从 meta.json 校准
│  │  ├─ dp_gen_pdf_covers.py  (4,073 B)  — pdf 封面抓取（fitz 渲染首页）
│  │  ├─ dp_gen_txt_covers.py  (3,847 B)  — txt 占位书生成文字封面
│  │  ├─ dp_grab_cf_assets.py  (8,191 B)
│  │  ├─ dp_import_epubs.log  (348 B)
│  │  ├─ dp_import_epubs.py  (7,080 B)  — epub 补入库（chapterCount<=1 的书）
│  │  ├─ dp_import_txt.py  (6,985 B)  — ⚠️ 勿运行：txt 占位符（无内容仅证明存在）
│  │  ├─ dp_launch_ocr.py  (2,016 B)  — 启动 OCR 单分片 + 看门狗（pythonw 独立进程）
│  │  ├─ dp_merge_summaries.py  (1,661 B)  — 历史摘要合并进 detail
│  │  ├─ dp_ocr_check.py  (16,374 B)  — OCR 入库质量核查清单
│  │  ├─ dp_ocr_epub.py  (7,361 B)  — 图片型 epub OCR 入库
│  │  ├─ dp_ocr_watchdog.py  (3,539 B)  — OCR 单分片看门狗（会话无关）
│  │  ├─ dp_pdf_import.py  (20,568 B)  — PDF 入库（含 ckpt 断点续传）
│  │  ├─ dp_retry_ocr.py  (2,804 B)  — 重 OCR FAILED 页（断点续传）
│  │  ├─ dp_run_import.py  (12,223 B)  — 未入库书逐本处理管线（质检→回灌→同步）
│  │  ├─ dp_score_books.py  (4,556 B)  — 批量书籍评分 → book_rankings.json
│  │  ├─ dp_sync_all.py  (3,155 B)  — 双端全量同步（章节 → DP public + backend）
│  │  ├─ dp_sync_books.py  (12,827 B)  — 汇总生成 app/public/books.json
│  │  ├─ dp_sync_fixed.py  (5,581 B)  — 已修复书的双端同步补漏
│  │  ├─ dp_sync_oss_chapters.py  (6,054 B)
│  │  ├─ dp_sync_oss_images.py  (5,160 B)
│  │  ├─ dp_sync_oss_static.py  (7,042 B)
│  │  ├─ dp_toc_parts.py  (3,421 B)  — 扁平 toc → 层级 toc（part 分组）
│  │  ├─ dp_verify_dual.py  (4,952 B)  — 双端入库一致性校验
│  │  ├─ gen_structure.py  (20,625 B)  — 生成全文件结构图（本脚本）
│  │  ├─ gen_summaries.py  (4,869 B)  — 批量生成书籍摘要和标签（DeepSeek）
│  │  ├─ generate_catalog.py  (4,121 B)  — 生成书籍目录 JSON（离线兜底）
│  │  ├─ generate_worker_assets.py  (3,935 B)  — 生成 Cloudflare api worker 静态资产
│  │  ├─ migrate_users_to_d1.py  (5,251 B)  — 旧 users.db → D1 导入 SQL 生成器
│  │  ├─ rebuild_auto.py  (6,548 B)  — 全库通用重建 v2（核查 A2/A4）
│  │  ├─ rebuild_spine.py  (21,252 B)  — 全库卷帙/分册结构重建
│  │  ├─ sync_full.py  (4,157 B)  — 全库三端内容同步
│  │  ├─ verify_book.py  (5,691 B)  — 书修复完成验证（模拟前端完整读取链）
│  │  └─ 分章标准规范.md  (7,223 B)
│  ├─ DATABASE.md  (1,860 B)
│  ├─ __init__.py  (25 B)
│  ├─ admin.py  (5,671 B)  — 开发者管理后台（访问统计 + 用户管理）
│  ├─ agents.py  (19,501 B)  — 智能体注册表（智能体广场）
│  ├─ auth.py  (29,897 B)  — 用户认证（SQLite dev / D1 prod; 整库云备份已禁用 2026-08-14）
│  ├─ config.py  (4,500 B)  — 云端部署配置（全部路径走环境变量）
│  ├─ db.py  (2,243 B)  — 哲学家信息库（JSON 加载 O(1) 查找）
│  ├─ drawio_convert.py  (4,977 B)  — mermaid → draw.io XML 转换器
│  ├─ engine_langgraph.py  (39,495 B)  — LangGraph 引擎（PhiAgent v2 流式编排）
│  ├─ eval_agent.py  (5,011 B)  — PhiAgent 评估基准 v1（四维评估）
│  ├─ fix_bios.py  (2,418 B)  — 批量修复 <1000 字的哲学家 bio
│  ├─ guard.py  (4,674 B)
│  ├─ main.py  (97,125 B)  — 云端 API 服务器（书籍/文件/RAG/作者/用户/历史）
│  └─ mcp_client.py  (4,193 B)  — MCP 客户端（外部工具生态接入）
├─ data/
│  └─ ai_author/  # 尼采 LoRA 生产数据 (6 子目录, 207 文件, 约 1.6G — 保留)
├─ scripts/  — 内容运营与历史运维脚本（38 个, 多数一次性已完成）
│  ├─ _lib.py  (5,675 B)  — 共享工具模块（load/save JSON + DeepSeek/Agnes 客户端）
│  ├─ add_author.py  (7,914 B)  — 一键新增哲人（DeepSeek 生成信息 → public JSON）
│  ├─ add_book.py  (7,554 B)  — 一键新增书籍（本地扫描 → 标签摘要 → 入库）
│  ├─ add_school.py  (21,501 B)  — 一键新增流派（全流程自动化）
│  ├─ add_subschool.py  (13,133 B)  — 一键新增下属流派（轻量版）
│  ├─ agnes_direct_test.py  (1,902 B)  — 测试 Agnes AI（DNS 替换）  [已归档]
│  ├─ agnes_quick_test.py  (2,628 B)  — 快速测试 Agnes AI + 代理  [已归档]
│  ├─ ai_verify_all.py  (4,904 B)  — Agnes AI 全量肖像验证（需代理）  [已归档]
│  ├─ ai_verify_batch.py  (8,395 B)  — Agnes AI 分批肖像验证（可断点续跑）  [已归档]
│  ├─ ai_verify_portraits.py  (4,865 B)  — Agnes AI 视觉验证肖像抽查  [已归档]
│  ├─ audit_all_chapters.py  (3,571 B)  — 逐本审查章节标题质量（旧体系）  [已归档]
│  ├─ batch_extract.py  (2,375 B)  — 批量提取缺失章节的 EPUB（旧体系）  [已归档]
│  ├─ batch_import_books.py  (10,185 B)  — 批量导入哲学书两阶段（旧体系）  [已归档]
│  ├─ check_all_books.py  (3,527 B)  — 全面检查所有书（封面/目录/章节/简介, 旧体系）  [已归档]
│  ├─ check_portraits.py  (7,919 B)  — 哲学家肖像校验（图像属性检测）  [已归档]
│  ├─ cleanup_portraits.py  (6,082 B)  — 清理肖像（MD5 相同对）  [已归档]
│  ├─ dedup_philosophers.py  (4,644 B)  — 哲学家去重（括号别名/姓氏）  [已归档]
│  ├─ delete_wrong_images.py  (2,318 B)  — 删除已确认错图  [已归档]
│  ├─ expand_bios.py  (3,667 B)  — 哲学家 bio 批量扩充至 1000+ 字  [已归档]
│  ├─ extract_one.py  (5,774 B)  — 从 EPUB 提取章节（旧体系）  [已归档]
│  ├─ fetch_bing_portraits.py  (6,154 B)  — Bing 图片搜索 → 下载 → WebP  [已归档]
│  ├─ fetch_philosopher_batch.py  (2,632 B)  — 批量爬取哲学家头像  [已归档]
│  ├─ fetch_philosopher_img.py  (7,769 B)  — 哲学家头像爬取（Wikipedia/Wikimedia）  [已归档]
│  ├─ fetch_portraits.py  (10,485 B)  — 哲学家肖像自动爬取 + AI 验证
│  ├─ fetch_wiki_zh.py  (6,413 B)  — 中文维基百科图片爬取（走代理）  [已归档]
│  ├─ find_translations.py  (5,014 B)  — 分析书籍找缺中译本的西哲著作
│  ├─ fix_bad_chapters.py  (2,732 B)  — 子进程调 rebuild_spine 修复章节（旧体系）  [已归档]
│  ├─ fix_book_ids.py  (5,334 B)  — books.json ID 对齐修复（旧体系）  [已归档]
│  ├─ fix_english_names.py  (3,753 B)  — 翻译英文 bio + 改中文名  [已归档]
│  ├─ fix_map_coords.py  (2,598 B)  — Agnes 图像理解重新定位地图坐标  [已归档]
│  ├─ gen_portrait.py  (7,028 B)  — AI 生成哲学家肖像（Wikipedia 无画像的古代哲人）  [已归档]
│  ├─ gen_school_bg.py  (7,895 B)  — 流派背景图生成器（两阶段）
│  ├─ gen_tags_batch.py  (4,696 B)  — 为新书批量生成标签 + 摘要
│  ├─ list_missing.py  (957 B)  — 列出缺图哲学家
│  ├─ score_item.py  (2,904 B)  — 哲学家/书籍五维度 AI 评分
│  ├─ test_extract.py  (837 B)  — 测试单个 EPUB 提取（旧体系）  [已归档]
│  └─ verify_all_portraits.py  (14,919 B)  — 哲学家肖像全方位验证算法  [已归档]
├─ workers/
│  ├─ api/
│  │  ├─ dist-check/
│  │  │  ├─ README.md  (119 B)
│  │  │  ├─ index.js  (191,362 B)  — 构建产物（dist）
│  │  │  └─ index.js.map  (303,963 B)
│  │  ├─ migrations/  — D1 迁移 SQL
│  │  │  ├─ 001_schema.sql  (1,581 B)  — D1 建表
│  │  │  └─ 002_import.sql  (27,651 B)  — 旧数据导入 SQL
│  │  ├─ src/  — api worker 源码与构建资产
│  │  │  ├─ admin_stats.json  (2,189 B)  — 构建产物：管理统计快照
│  │  │  ├─ books.json  (82,314 B)  — 构建产物：书 id → 文件直链映射
│  │  │  ├─ index.js  (22,979 B)  — api worker：业务端点 + JWT + SSE 透传
│  │  │  └─ stats.json  (55 B)  — 构建产物：访问统计快照
│  │  ├─ package-lock.json  (585 B)
│  │  ├─ package.json  (142 B)
│  │  └─ wrangler.toml  (701 B)  — api worker 配置（D1 绑定/路由）
│  └─ auth/
│     ├─ src/  — auth worker 源码
│     │  └─ index.js  (8,391 B)  — auth worker：登录/注册/JWT
│     ├─ .dev.vars  (39 B)
│     ├─ package-lock.json  (589 B)
│     ├─ package.json  (143 B)
│     └─ wrangler.toml  (524 B)  — auth worker 配置
├─ .dockerignore  (226 B)
├─ .env  (1,113 B)
├─ .gitignore  (2,253 B)
├─ PROJECT_STRUCTURE.md  (18,738 B)
├─ README.md  (6,191 B)
├─ requirements.txt  (726 B)
└─ vercel.json  (62 B)
```
