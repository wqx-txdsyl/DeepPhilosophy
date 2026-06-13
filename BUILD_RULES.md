# DeepPhilosophy 数据库构建规则（第一指令）

> 最后更新：2026-06-13 · 当前藏书 319 本（PDF/EPUB 212 本 + TXT 占位 107 本）

## 1. 书籍排序方法

按东西方分组，每组内部按哲学家**出生年份**升序：

1. 每组第一个固定为「合集&概述」
2. 其余哲学家按出生年份升序（古希腊→中世纪→近代→现代→当代）
3. 年代来源优先级：**philosophers_db.py 内置数据 → 百度百科爬虫 → AI/上网检索**
4. 未知年代的哲学家排在最末

排序实现位于 `backend/main.py:_author_sort_key()`，从 `philosophers_db.py` 的 `era` 字段提取年份：
- `约公元前624-前546年` → 解析为 -624
- `1770-1831年` → 解析为 1770
- 含"公元前/前"前缀的年份取反，确保公元前早于公元后
- 无年份信息的返回 9999（排最后）

## 2. 书籍扫描 (scan_books)

位置：`backend/main.py:169`

**流程：**
1. `os.walk(KNOWLEDGE_DIR)` 遍历 `region/author/title.ext` 结构
2. 过滤扩展名：`.pdf / .epub / .txt / .md`
3. 从路径解析 region、author、title（`Path(f).stem`）
4. `###合集&概述###` → 清洗为 `合集&概述`
5. 调用 `_classify_book()` 生成 pattern 初筛标签
6. 对空目录补 `status=pending` 占位条目

**文件名→显示标题修正：** `TITLE_FIXES` 字典，处理文件系统不允许的字符：
```python
TITLE_FIXES = {
    "SZ": "S/Z",   # 文件名不能含 /
}
```

## 3. 书籍标签与简介生成方法

### 优先级
1. **内置缓存** — `backend/data/book_summaries.json`（AI 生成，优先使用）
2. **AI 生成** — DeepSeek API（`backend/generate_tags_summaries.py` 批量调用）
3. **上网检索** — 百度百科等（暂未实现批量，仅 AuthorDetailPage 详情页用）
4. **兜底模板** — 绝对不用，一旦发现需立即替换

### 标签生成
- 每个标签为短关键词，用于前端筛选分类
- 必须是公认的哲学流派/学派名称：`古希腊哲学`、`存在主义`、`德国古典哲学`、`伦理学`……
- 每本书 2-5 个标签
- `/api/books` 列表端点附加缓存标签，**覆盖** `_classify_book()` 的 pattern 标签

### 简介生成
- 每篇 **不少于 50 字**
- 涵盖：主题、核心思想、哲学贡献（佚失作品说明历史意义）
- 模板兜底的特征：含 `"的著作，TXT格式，约 X.XMB"` 等机械拼接 → 发现即清理

### 缓存格式
`book_summaries.json` 使用 `{书名}||{作者}` 复合键：
```json
{
  "论语||孔子": {
    "summary": "《论语》是孔子及其弟子的语录集…",
    "tags": ["儒家", "伦理学", "政治哲学", "教育哲学"]
  },
  "S/Z||罗兰·巴特": {
    "summary": "罗兰·巴特的《S/Z》是一部解构主义文学批评…",
    "tags": ["后结构主义", "符号学", "文学批评"]
  }
}
```
**必须包含作者名**：同名不同作者的书（如《论自然[已佚失]》×3、《论自然[残篇]》×3）各自独立存储。

### 摘要查询 (_generate_summary)
位置：`backend/main.py`，查询逻辑：
1. 优先查 `{title}||{author}` 复合键
2. 兼容旧格式 `{title}` 单键
3. 都未命中才走兜底

### 批量生成流程
```bash
cd backend && KNOWLEDGE_DIR=F:/philosophy python generate_tags_summaries.py
```
分两阶段：
1. **Phase 1** — 有真实摘要但缺标签的，AI 从摘要提取标签（快）
2. **Phase 2** — 模板/空白摘要的，AI 生成完整简介+标签（慢）

每 5-10 本自动保存，可中断续跑。`is_template_summary()` 自动识别假摘要。

### 同名书修复
`backend/fix_duplicates.py` — 手动为同名不同作者的书写入独立摘要。

## 4. 作家页面

### 作家列表
- 排除「合集&概述」类条目（`is_valid_author()` 过滤）
- 按东西方分组，组内按时序排列
- 每位作家显示：年代 / 国家 / 流派 / 收录作品（可点击跳转） / 简介
- 数据来自 `philosophers_db.py`（60+ 位哲学家，含别名/年代/流派/百科链接）

### 标签筛选
前端 `AuthorsPage.jsx` 和后端 `_normalize_tag()` 各自维护**归一化映射**（两处须保持同步）：
- `存在主义先驱`→`存在主义`、`柏拉图主义`→`古希腊哲学` ……
- 归一化仅作用于筛选，不改变详情页原始显示
- 流派标签默认展示 20 个，超出的可展开/收起
- 多标签 AND 逻辑，选中标签显示在顶部可逐个移除

### 前端统计
- 书籍页：`📚 共 X 本书，Y 位作者`（排除合集&概述）
- 作家页：`✒️ 共 X 位作家，Y 部作品`

## 5. AI 问答与伴读

### QAPage 问答页
- 流式调用 DeepSeek API，逐字输出
- 聊天历史本地自动保存（`userData.js`）
- 思考阶段轮播动画（检索→分析→深度思考→组织回答）
- 自动滚动到底部（哨兵 div + `scrollIntoView`）

### ReaderPage AI 伴读
- 预设阅读上下文（书名/作者/页码/哲学传统）
- 流式输出，支持多轮对话
- 自动滚动跟随输出
- 侧边栏面板，与批注共享空间

## 6. 数据库更新流程

每次增删书籍或作者后：
1. 重新扫描 `KNOWLEDGE_DIR` → 后端自动感知新文件
2. 运行 `generate_tags_summaries.py` 为新书生成标签+简介
3. 新增/修改的作者 → 补充到 `philosophers_db.py`
4. 更新 `TXT_BOOKS_LIST.txt`（`backend/` 目录下运行生成脚本）
5. 验证：API 返回正确排序、全部有标签+摘要

**更新必须慎重，不丢失已有手工数据。**

## 7. 公版书下载

- 可下载：作者逝世超 50-70 年的公版书（前苏格拉底至 19 世纪）
- 不可下载：版权期内的 20 世纪著作
- 下载后放到 `F:/philosophy/{东方/西方}/{作者}/` 目录下，删除同名 `.txt` 占位
- 源站：Internet Archive、Project Gutenberg、Wikimedia Commons（国内需代理）

## 关键文件

| 文件 | 用途 |
|------|------|
| `backend/main.py` | API 服务器（扫描/TITLE_FIXES/排序/筛选/标签归一化/摘要缓存） |
| `backend/philosophers_db.py` | 哲学家数据（60+位，含别名/年代/流派/百科链接） |
| `backend/data/book_summaries.json` | 书籍摘要+标签缓存（AI 生成，`书名||作者` 键） |
| `backend/data/books_cache.json` | 书籍关键词缓存 |
| `backend/generate_tags_summaries.py` | DeepSeek API 批量生成工具（两阶段） |
| `backend/fix_duplicates.py` | 修复同名书覆盖问题 |
| `TXT_BOOKS_LIST.txt` | TXT 占位书籍清单（项目根目录） |
| `app/src/pages/BooksPage.jsx` | 书籍前端（统计/标签折叠/搜索/分组展开/摘要预览） |
| `app/src/pages/AuthorsPage.jsx` | 作家前端（统计/归一化筛选/标签折叠/多标签AND） |
| `app/src/pages/AuthorDetailPage.jsx` | 作者详情（百科爬虫/作品跳转） |
| `app/src/pages/QAPage.jsx` | AI 问答（流式输出/聊天历史/自动滚动） |
| `app/src/pages/ReaderPage.jsx` | 阅读器（PDF+EPUB/AI伴读/批注/自动滚动） |
