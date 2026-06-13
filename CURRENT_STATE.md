# DeepPhilosophy 开发状态 (2026-06-13)

## 当前阶段：网页端完善中，Android & EXE 待构建

---

## 项目总览

| 组件 | 状态 | 说明 |
|------|------|------|
| 后端 API | ✅ 运行中 | FastAPI + uvicorn, localhost:8000, KNOWLEDGE_DIR=F:/philosophy |
| 前端网页 | ✅ 运行中 | React + Vite, localhost:5173 |
| 书库 | ✅ 319本 | PDF/EPUB 212 + TXT占位 107, 全部有标签+简介 |
| Android APK | ⬜ 待构建 | 前端已就绪，需 Gradle 打包 |
| Windows EXE | ⬜ 待构建 | Electron 壳已就绪，需配置打包 |
| GitHub | ✅ 已推送 | git@github.com:wqx-txdsyl/DeepPhilosophy.git |
| 云端部署 | ✅ 已部署 | https://deepphilosophy.onrender.com |

---

## 启动命令

```bash
# 后端（必须设置 KNOWLEDGE_DIR，使用 C:\dp junction 避免路径 & 问题）
cd C:\dp\backend && KNOWLEDGE_DIR=F:/philosophy python main.py

# 前端
cd C:\dp\app && npx vite --host

# 批量生成标签+简介
cd C:\dp\backend && KNOWLEDGE_DIR=F:/philosophy python generate_tags_summaries.py
```

---

## 后端功能

| 端点 | 说明 |
|------|------|
| `GET /api/books` | 书籍列表（排序/标签筛选/摘要缓存） |
| `GET /api/books/{id}` | 书籍详情 |
| `GET /api/books/{id}/file` | 文件下载 |
| `GET /api/books/tags` | 标签列表 |
| `GET /api/authors` | 作者列表（时间排序/多维度筛选） |
| `GET /api/authors/{name}` | 作者详情（含作品跳转） |
| `GET /api/authors/filters` | 作者筛选选项 |
| `POST /api/qa` | RAG 问答 |
| `POST /api/auth/register` | 注册 |
| `POST /api/auth/login` | 登录 |
| `POST /api/sync/upload` | 上传书籍 |

## 前端 App — 4 个分区

| 分区 | 功能 |
|------|------|
| 📚 书籍 | 319 本时间排序、标签筛选（折叠20）、摘要预览、直达阅读 |
| ✒️ 作家 | 140 位哲学家、多标签AND筛选、归一化标签、百科链接 |
| 💬 问答 | 流式输出、思考动画、聊天历史、自动滚动 |
| 👤 我的 | 登录/注册、阅读历史、聊天历史 |

---

## 关键数据文件

| 文件 | 内容 |
|------|------|
| `backend/philosophers_db.py` | 60+ 位哲学家（别名/年代/流派/百科） |
| `backend/data/book_summaries.json` | 全部书籍摘要+标签（`书名||作者` 键） |
| `backend/data/books_cache.json` | 书籍关键词缓存 |
| `F:/philosophy/` | 书籍文件（东方/西方目录） |
| `TXT_BOOKS_LIST.txt` | TXT 占位书清单（107 本待收录） |

---

## 已知问题

- `&` 路径问题：`Q&ASystem` 在 bash 中需用 `C:\dp` junction 或 PowerShell
- 公版书下载需代理（Internet Archive / Wikimedia 被墙）
- 部分现当代著作受版权保护，无法下载
