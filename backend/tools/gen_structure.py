# -*- coding: utf-8 -*-
"""生成项目全文件结构图 PROJECT_STRUCTURE.md (两个仓库各自生成, 各自放根目录)

用法: python gen_structure.py   # 输出 PhiAgent/PROJECT_STRUCTURE.md + DeepPhilosophy/PROJECT_STRUCTURE.md
规则:
- 排除 .git / node_modules / .venv / __pycache__ / .wrangler / dist
- 目录直接子条目 > 30 折叠为计数摘要 (数据大目录带专用注释)
- tools/ 长期可复用脚本清单强制全列
"""
import datetime, io, json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

EXCLUDE = {'.git', 'node_modules', '.venv', '__pycache__', '.wrangler', '.idea', '.claude', 'dist'}
FOLD = 30                     # 目录直接子条目超过此数折叠为计数摘要
ALWAYS_EXPAND = {'tools', 'scripts'}     # 脚本清单强制全列
ALWAYS_FOLD = {'ai_author', 'book_chapters', 'book_detail', 'book_images', 'embeddings', '_tmp'}  # 数据大目录强制折叠

# (仓库名, 根路径, 段标题) — 2026-08-14 PhiAgent 已并入, 单仓库一份结构图
REPOS = [
    ('DeepPhilosophy', r'F:\program\Python\DeepPhilosophy',
     'DeepPhilosophy × PhiAgent 合并后单仓库（2026-08-14: 平台 + 智能体 + 书库工具）'),
]


# ── 文件功能注释: 相对仓库根路径 → 一句话说明 ──
FILE_NOTES = {
    # PHA/DP backend 根
    'backend/main.py': '云端 API 服务器（书籍/文件/RAG/作者/用户/历史）',
    'backend/admin.py': '开发者管理后台（访问统计 + 用户管理）',
    'backend/agents.py': '智能体注册表（智能体广场）',
    'backend/auth.py': '用户认证（SQLite dev / D1 prod; 整库云备份已禁用 2026-08-14）',
    'backend/config.py': '云端部署配置（全部路径走环境变量）',
    'backend/db.py': '哲学家信息库（JSON 加载 O(1) 查找）',
    'backend/drawio_convert.py': 'mermaid → draw.io XML 转换器',
    'backend/engine_langgraph.py': 'LangGraph 引擎（PhiAgent v2 流式编排）',
    'backend/eval_agent.py': 'PhiAgent 评估基准 v1（四维评估）',
    'backend/fix_bios.py': '批量修复 <1000 字的哲学家 bio',
    'backend/mcp_client.py': 'MCP 客户端（外部工具生态接入）',
    'backend/models/__init__.py': '共享 Pydantic 请求/响应模型',
    # backend/modules
    'backend/modules/document_loader.py': '文档加载（PDF/EPUB/TXT，文本/扫描智能判断）',
    'backend/modules/embedding.py': '嵌入模型（文本向量化）',
    'backend/modules/llm_client.py': 'DeepSeek API 客户端（OpenAI 兼容）',
    'backend/modules/ocr_engine.py': 'OCR 引擎（PaddleOCR）',
    'backend/modules/rag_chain.py': 'RAG 检索增强生成链',
    'backend/modules/text_processor.py': '文本处理（分词/关键词/摘要）',
    'backend/modules/vector_store.py': '向量库存储与检索（ChromaDB）',
    # backend/routes
    'backend/routes/agent.py': '智能体核心：29 工具注册表 + stream_lg(LangGraph) + cite（旧引擎已删）',
    'backend/routes/ai.py': 'AI proxy / RAG QA / ASR 路由',
    'backend/routes/text.py': '文本提取 API（章节索引 + 单章读取，本地优先 OSS 兜底）',
    'backend/routes/health.py': '健康检查与统计',
    'backend/routes/history.py': '阅读历史/聊天记录/笔记/书聊',
    'backend/routes/admin_routes.py': '管理路由',
    'backend/routes/auth_routes.py': '认证路由',
    'backend/routes/knowledge.py': '知识库路由',
    'backend/routes/sync.py': '同步路由',
    'backend/routes/user.py': '用户路由',
    # backend/services
    'backend/services/book_scanner.py': '书库扫描（本地/OSS/GitHub/R2 统一接口）',
    'backend/services/summaries.py': '书籍摘要缓存加载/生成',
    'backend/services/tag_utils.py': '标签归一化工具',
    # backend/tests
    'backend/tests/test_config.py': '冒烟测试：配置加载',
    'backend/tests/test_health.py': '冒烟测试：健康检查',
    'backend/tests/test_philosophers.py': '冒烟测试：哲学家库查找',
    # PHA tools
    'backend/tools/dp_sync_all.py': '双端全量同步（章节 → DP public + backend）',
    'backend/tools/dp_sync_books.py': '汇总生成 app/public/books.json',
    'backend/tools/dp_sync_fixed.py': '已修复书的双端同步补漏',
    'backend/tools/dp_verify_dual.py': '双端入库一致性校验',
    'backend/tools/sync_full.py': '全库三端内容同步',
    'backend/tools/dp_embed_missing.py': '增量补嵌入（向量维护核心）',
    'backend/tools/build_embeddings.py': '章节向量索引构建（智谱 embedding-2）',
    'backend/tools/dp_clean_book.py': '单本专项清洗 + 回灌 DP 阅读器格式',
    'backend/tools/dp_pdf_import.py': 'PDF 入库（含 ckpt 断点续传）',
    'backend/tools/dp_import_epubs.py': 'epub 补入库（chapterCount<=1 的书）',
    'backend/tools/dp_import_txt.py': '⚠️ 勿运行：txt 占位符（无内容仅证明存在）',
    'backend/tools/dp_launch_ocr.py': '启动 OCR 单分片 + 看门狗（pythonw 独立进程）',
    'backend/tools/dp_ocr_watchdog.py': 'OCR 单分片看门狗（会话无关）',
    'backend/tools/dp_ocr_check.py': 'OCR 入库质量核查清单',
    'backend/tools/dp_ocr_epub.py': '图片型 epub OCR 入库',
    'backend/tools/dp_retry_ocr.py': '重 OCR FAILED 页（断点续传）',
    'backend/tools/dp_run_import.py': '未入库书逐本处理管线（质检→回灌→同步）',
    'backend/tools/rebuild_auto.py': '全库通用重建 v2（核查 A2/A4）',
    'backend/tools/rebuild_spine.py': '全库卷帙/分册结构重建',
    'backend/tools/dp_score_books.py': '批量书籍评分 → book_rankings.json',
    'backend/tools/dp_gen_pdf_covers.py': 'pdf 封面抓取（fitz 渲染首页）',
    'backend/tools/dp_gen_txt_covers.py': 'txt 占位书生成文字封面',
    'backend/tools/dp_epub_covers.py': 'epub 封面补全 + 重建 covers.json',
    'backend/tools/dp_merge_summaries.py': '历史摘要合并进 detail',
    'backend/tools/dp_toc_parts.py': '扁平 toc → 层级 toc（part 分组）',
    'backend/tools/dp_fix_authors.py': '作者字段修复',
    'backend/tools/build_book_json.py': 'EPUB/TXT → 结构化 JSON（rebuild_spine 依赖）',
    'backend/tools/build_covers_manifest.py': '封面 → public/covers/ + covers.json',
    'backend/tools/build_philosopher_network.py': '构建哲学家星丛网络（AI 识别思想关系）',
    'backend/tools/download_gutenberg.py': 'Project Gutenberg 下载 EPUB',
    'backend/tools/gen_summaries.py': '批量生成书籍摘要和标签（DeepSeek）',
    'backend/tools/generate_catalog.py': '生成书籍目录 JSON（离线兜底）',
    'backend/tools/gen_structure.py': '生成全文件结构图（本脚本）',
    # DP tools 独有（DP 仓库侧 6 个, 2026-08-11 分家后）
    'backend/tools/generate_worker_assets.py': '生成 Cloudflare api worker 静态资产',
    'backend/tools/migrate_users_to_d1.py': '旧 users.db → D1 导入 SQL 生成器',
    'backend/tools/dp_fix_catalog_chapters.py': 'catalog chapterCount 从 meta.json 校准',
    'backend/tools/verify_book.py': '书修复完成验证（模拟前端完整读取链）',
    # DP scripts（内容运营 + 历史运维, 与 scripts/ 目录一一对应）
    'scripts/_lib.py': '共享工具模块（load/save JSON + DeepSeek/Agnes 客户端）',
    'scripts/add_author.py': '一键新增哲人（DeepSeek 生成信息 → public JSON）',
    'scripts/add_book.py': '一键新增书籍（本地扫描 → 标签摘要 → 入库）',
    'scripts/add_school.py': '一键新增流派（全流程自动化）',
    'scripts/add_subschool.py': '一键新增下属流派（轻量版）',
    'scripts/fetch_portraits.py': '哲学家肖像自动爬取 + AI 验证',
    'scripts/fetch_philosopher_img.py': '哲学家头像爬取（Wikipedia/Wikimedia）',
    'scripts/fetch_bing_portraits.py': 'Bing 图片搜索 → 下载 → WebP',
    'scripts/fetch_philosopher_batch.py': '批量爬取哲学家头像',
    'scripts/fetch_wiki_zh.py': '中文维基百科图片爬取（走代理）',
    'scripts/gen_portrait.py': 'AI 生成哲学家肖像（Wikipedia 无画像的古代哲人）',
    'scripts/gen_school_bg.py': '流派背景图生成器（两阶段）',
    'scripts/verify_all_portraits.py': '哲学家肖像全方位验证算法',
    'scripts/check_portraits.py': '哲学家肖像校验（图像属性检测）',
    'scripts/cleanup_portraits.py': '清理肖像（MD5 相同对）',
    'scripts/ai_verify_all.py': 'Agnes AI 全量肖像验证（需代理）',
    'scripts/ai_verify_batch.py': 'Agnes AI 分批肖像验证（可断点续跑）',
    'scripts/ai_verify_portraits.py': 'Agnes AI 视觉验证肖像抽查',
    'scripts/delete_wrong_images.py': '删除已确认错图',
    'scripts/dedup_philosophers.py': '哲学家去重（括号别名/姓氏）',
    'scripts/expand_bios.py': '哲学家 bio 批量扩充至 1000+ 字',
    'scripts/fix_english_names.py': '翻译英文 bio + 改中文名',
    'scripts/fix_map_coords.py': 'Agnes 图像理解重新定位地图坐标',
    'scripts/list_missing.py': '列出缺图哲学家',
    'scripts/score_item.py': '哲学家/书籍五维度 AI 评分',
    'scripts/find_translations.py': '分析书籍找缺中译本的西哲著作',
    'scripts/gen_tags_batch.py': '为新书批量生成标签 + 摘要',
    'scripts/audit_all_chapters.py': '逐本审查章节标题质量（旧体系）',
    'scripts/batch_extract.py': '批量提取缺失章节的 EPUB（旧体系）',
    'scripts/extract_one.py': '从 EPUB 提取章节（旧体系）',
    'scripts/test_extract.py': '测试单个 EPUB 提取（旧体系）',
    'scripts/batch_import_books.py': '批量导入哲学书两阶段（旧体系）',
    'scripts/check_all_books.py': '全面检查所有书（封面/目录/章节/简介, 旧体系）',
    'scripts/fix_bad_chapters.py': '子进程调 rebuild_spine 修复章节（旧体系）',
    'scripts/fix_book_ids.py': 'books.json ID 对齐修复（旧体系）',
    'scripts/agnes_direct_test.py': '测试 Agnes AI（DNS 替换）',
    'scripts/agnes_quick_test.py': '快速测试 Agnes AI + 代理',
    # PHA app
    'app/src/App.jsx': '应用入口/路由',
    'app/src/main.jsx': '入口挂载',
    'app/src/auth.jsx': '登录态管理',
    'app/src/pages/AgentPage.jsx': '智能体广场页（对话/工具/cite 引用跳 DP）',
    'app/src/components/AgentSidebar.jsx': '智能体侧边栏',
    'app/src/components/AuthModal.jsx': '登录/注册弹窗',
    'app/src/components/DrawioInline.jsx': 'draw.io 图表内嵌',
    'app/src/components/DrawioModal.jsx': 'draw.io 图表弹窗',
    'app/src/components/Icon.jsx': '图标组件',
    'app/src/components/UserCenterModal.jsx': '用户中心弹窗',
    'app/src/utils/api.js': 'API 基址',
    'app/src/utils/i18n.jsx': '多语言',
    'app/src/utils/theme.js': '主题',
    # DP app components
    'app/src/components/ChapterReader.jsx': '章节阅读器',
    'app/src/components/ReadingProgress.jsx': '阅读进度条',
    'app/src/components/PhilosopherConstellation.jsx': '哲学家星丛图',
    'app/src/components/WorldMap.jsx': '世界地图（思想地理）',
    'app/src/components/NavBar.jsx': '顶部导航',
    'app/src/components/Footer.jsx': '页脚',
    'app/src/components/ErrorBoundary.jsx': '错误边界',
    'app/src/components/CountUp.jsx': '数字滚动动画',
    'app/src/components/ScrollToTop.jsx': '回到顶部',
    'app/src/components/SectionReveal.jsx': '滚动渐显动画',
    'app/src/components/AvatarUpload.jsx': '头像上传',
    # DP app pages
    'app/src/pages/HomePage.jsx': '首页',
    'app/src/pages/BooksPage.jsx': '书库列表',
    'app/src/pages/BookDetailPage.jsx': '书籍详情',
    'app/src/pages/ReaderPage.jsx': '阅读器（PDF/章节 + 批注/书聊）',
    'app/src/pages/QAPage.jsx': 'AI 问答（流式 + 自配 key 直连）',
    'app/src/pages/AuthorsPage.jsx': '哲学家列表',
    'app/src/pages/AuthorDetailPage.jsx': '哲学家详情',
    'app/src/pages/SchoolDetailPage.jsx': '学派详情',
    'app/src/pages/EasternPhilosophiesPage.jsx': '东方哲学',
    'app/src/pages/WesternPhilosophiesPage.jsx': '西方哲学',
    'app/src/pages/WorldPhilosophiesPage.jsx': '世界哲学',
    'app/src/pages/GenealogyPage.jsx': '思想谱系图',
    'app/src/pages/GamesPage.jsx': '小游戏',
    'app/src/pages/PHTIPage.jsx': 'PHTI 哲学类型测试',
    'app/src/pages/PHTISillyPage.jsx': 'PHTI 离谱版测试',
    'app/src/pages/AnswerBookPage.jsx': '答案之书',
    'app/src/pages/ProfilePage.jsx': '个人中心',
    'app/src/pages/ProfileEditPage.jsx': '个人资料编辑',
    'app/src/pages/SettingsPage.jsx': '设置',
    'app/src/pages/DeveloperPage.jsx': '开发者后台（访问统计）',
    'app/src/pages/PrivacyPage.jsx': '隐私政策',
    'app/src/pages/TermsPage.jsx': '服务条款',
    'app/src/utils/seo.js': 'SEO 工具',
    'app/src/utils/api.js': 'API 封装（生产同源/兜底链）',
    'app/src/data.js': '前端全局数据',
    'app/src/contexts/ToastContext.jsx': '全局提示（Toast）',
    # workers
    'workers/api/src/index.js': 'api worker：业务端点 + JWT + SSE 透传',
    'workers/auth/src/index.js': 'auth worker：登录/注册/JWT',
    'workers/api/src/books.json': '构建产物：书 id → 文件直链映射',
    'workers/api/src/stats.json': '构建产物：访问统计快照',
    'workers/api/src/admin_stats.json': '构建产物：管理统计快照',
    'workers/api/dist-check/index.js': '构建产物（dist）',
    'workers/api/migrations/001_schema.sql': 'D1 建表',
    'workers/api/migrations/002_import.sql': '旧数据导入 SQL',
    'workers/api/wrangler.toml': 'api worker 配置（D1 绑定/路由）',
    'workers/auth/wrangler.toml': 'auth worker 配置',
}

# ── 脚本状态标注: 一次性已完成 / Render 退役废弃 ──
ARCHIVED = {  # 一次性修复已完成历史使命, 仅存档参考 (不影响运行)
    # PHA tools 已归档 27 个已于 2026-08-11 删除（git 历史可找回）, 此处仅剩 DP scripts
    # DP scripts 一次性 (肖像时代 7 月 / 章节时代 8 月初, 已被 dp_clean_book 体系取代)
    'scripts/agnes_direct_test.py', 'scripts/agnes_quick_test.py',
    'scripts/ai_verify_all.py', 'scripts/ai_verify_batch.py', 'scripts/ai_verify_portraits.py',
    'scripts/audit_all_chapters.py', 'scripts/batch_extract.py', 'scripts/batch_import_books.py',
    'scripts/check_all_books.py', 'scripts/check_portraits.py', 'scripts/cleanup_portraits.py',
    'scripts/dedup_philosophers.py', 'scripts/delete_wrong_images.py', 'scripts/expand_bios.py',
    'scripts/extract_one.py', 'scripts/fetch_bing_portraits.py', 'scripts/fetch_philosopher_batch.py',
    'scripts/fetch_philosopher_img.py', 'scripts/fetch_wiki_zh.py', 'scripts/fix_bad_chapters.py',
    'scripts/fix_book_ids.py', 'scripts/fix_english_names.py', 'scripts/fix_map_coords.py',
    'scripts/gen_portrait.py', 'scripts/test_extract.py', 'scripts/verify_all_portraits.py',
}
# Render 已退役: build_and_sync_kb / build_knowledge_local / sync_to_cloud 已删除 (2026-08-11)

# ── 目录注释: 相对仓库根路径 → 一句话说明 ──
DIR_NOTES = {
    'backend/routes': '后端 API 路由',
    'backend/modules': '核心功能模块',
    'backend/services': '业务服务',
    'backend/tools': '数据构建/修复/同步工具集',
    'scripts': '内容运营与历史运维脚本（38 个, 多数一次性已完成）',
    'backend/tests': '冒烟测试',
    'backend/data': '运行数据（章节库/向量库/catalog）',
    'backend/mcp_servers': 'MCP 服务器（外部工具）',
    'backend/models': 'Pydantic 模型',
    'app/src/pages': '前端页面',
    'app/src/components': '前端组件',
    'app/src/data': '前端静态数据',
    'app/src/utils': '前端工具',
    'app/src/contexts': 'React 上下文',
    'app/public': '前端静态资源（被 gitignore）',
    'workers/api/src': 'api worker 源码与构建资产',
    'workers/auth/src': 'auth worker 源码',
    'workers/api/migrations': 'D1 迁移 SQL',
    'app/src/components/school': '学派详情组件',
    'app/src/assets': '前端打包资源',
}


def count_files(path):
    n = 0
    for _, _, fs in os.walk(path):
        n += len(fs)
    return n


def dir_size(path):
    total = 0
    for root, _, fs in os.walk(path):
        for f in fs:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def fold_comment(name, path, n):
    if name == 'book_chapters':
        books = sum(1 for e in os.scandir(path) if e.is_dir())
        return f'{books} 本书 × {count_files(path)} 个章节 json (按 bid 分目录, 顶层 dict 禁 list)'
    if name == 'book_detail':
        return f'{n} 个 detail json (三处同步规则: PHA/DP/app public)'
    if name == 'book_images':
        return f'{n} 个封面图片文件'
    if name == 'embeddings':
        k = 0
        idx = os.path.join(path, 'index.json')
        if os.path.exists(idx):
            try:
                k = len(json.load(io.open(idx, encoding='utf-8')))
            except Exception:
                k = 0
        return f'向量库: index.json ({k} 条 {{bid,idx,title,hash}}) + vectors.npy (float32 {k}×1024)'
    if name == 'ai_author':
        nd = sum(1 for e in os.scandir(path) if e.is_dir())
        return f'尼采 LoRA 生产数据 ({nd} 子目录, {count_files(path)} 文件, 约 {dir_size(path)/1024**3:.1f}G — 保留)'
    if name == '_tmp':
        return f'临时脚本/产物 ({n} 项, 随用随删)'
    if name in ('covers', 'philosopher', 'schools', 'icons', 'gene', 'phti', 'agent_images'):
        return f'前端静态资源 ({n} 文件)'
    return f'{n} 文件'


def note_for(rel, name, is_dir):
    if is_dir:
        return DIR_NOTES.get(rel) or DIR_NOTES.get(name) or ''
    return FILE_NOTES.get(rel) or FILE_NOTES.get(name) or ''


def render(path, root, prefix, out):
    entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
    entries = [e for e in entries if e.name not in EXCLUDE]
    entries = [e for e in entries if not (e.is_dir() and len(list(os.scandir(e.path))) == 0)]  # 跳过空目录
    total = len(entries)
    for i, e in enumerate(entries):
        last = (i == total - 1)
        conn = '└─ ' if last else '├─ '
        rel = os.path.relpath(e.path, root).replace('\\', '/')
        if e.is_dir():
            n = len(list(os.scandir(e.path)))
            fold = e.name in ALWAYS_FOLD or (n > FOLD and e.name not in ALWAYS_EXPAND) or rel.startswith('agent-app/public')
            line = prefix + conn + e.name + '/'
            if fold:
                if rel.startswith('agent-app/public'):
                    line += '  # agent 前端静态数据（本地工作副本, 不入库）'
                else:
                    line += '  # ' + fold_comment(e.name, e.path, n)
            else:
                note = note_for(rel, e.name, True)
                if note:
                    line += '  — ' + note
            out.append(line)
            if not fold:
                render(e.path, root, prefix + ('   ' if last else '│  '), out)
        else:
            try:
                sz = os.path.getsize(e.path)
            except OSError:
                sz = 0
            line = f'{prefix}{conn}{e.name}  ({sz:,} B)'
            note = note_for(rel, e.name, False)
            if note:
                line += '  — ' + note
            if rel in ARCHIVED:
                line += '  [已归档]'
            out.append(line)


def main():
    for name, root, title in REPOS:
        lines = [
            f'# {name} 全文件结构图',
            '',
            f'> 生成时间: {datetime.datetime.now():%Y-%m-%d %H:%M} · 排除 .git / node_modules / .venv / __pycache__ / .wrangler / dist',
            '> 大数据目录 (章节库 / 向量库 / 封面 / ai_author) 折叠为计数摘要',
            '',
            f'## {title}',
            '',
            '```',
            root,
        ]
        render(root, root, '', lines)
        lines += ['```', '']
        out_path = os.path.join(root, 'PROJECT_STRUCTURE.md')
        io.open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
        size_b = len('\n'.join(lines).encode('utf-8'))
        print(f'已生成: {out_path} ({size_b:,} B)')


if __name__ == '__main__':
    main()
