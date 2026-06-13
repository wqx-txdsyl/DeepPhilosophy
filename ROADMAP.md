# DeepPhilosophy 三线推进计划

> 策略：网页先行完善 → Android APK → Windows EXE，逐步覆盖全平台。

---

## 第一线：网页端（当前）

### 1.1 书库完善
- [ ] 公版书下载（约 40-50 本可下，TXT → PDF/EPUB）
- [ ] 版权书标记不可下载，保留 TXT 占位
- [ ] 每新增一本书 → 运行 `generate_tags_summaries.py` 补标签+简介
- [ ] 更新 `TXT_BOOKS_LIST.txt`

### 1.2 体验优化
- [ ] 书籍页顶部加东西方切换 tab（替代现在的滚动分区）
- [ ] 搜索支持标签匹配（如搜"古希腊"能匹配到标签含古希腊的书）
- [ ] 问答页支持多轮对话上下文（目前仅单轮）
- [ ] 阅读器 EPUB 翻页动画优化
- [ ] 移动端触控适配（左右滑翻页、下拉刷新）

### 1.3 后端增强
- [ ] 书籍上传功能完善（拖拽上传 + 自动扫描入库）
- [ ] 知识库向量初始化一键化（目前需手动调用 `/api/knowledge/init`）
- [ ] RAG 检索质量优化（BGE 模型切换测试）

### 1.4 内容
- [ ] 哲学家数据库扩充至 100+ 位
- [ ] 书籍摘要质量抽查 & 人工修正
- [ ] 20 本核心著作联网搜索深度摘要

---

## 第二线：Android APK

### 2.1 构建准备
- [ ] 清理旧的 Android 构建残留（.gradle / build 目录）
- [ ] 更新 Capacitor 配置（`capacitor.config.json`）
- [ ] 配置 JDK 17 + Android SDK 环境变量
- [ ] 前端 build：`vite build` → `dist/`

### 2.2 打包
- [ ] `npx cap sync android` 同步前端到 Android 项目
- [ ] `gradlew assembleDebug` 生成 debug APK
- [ ] 真机测试：PDF/EPUB 本地文件读取
- [ ] 修复 Capacitor 文件系统路径问题

### 2.3 发布
- [ ] `gradlew assembleRelease` + 签名
- [ ] APK 分发（GitHub Release / 本地安装）

---

## 第三线：Windows EXE

### 3.1 Electron 打包
- [ ] 更新 `electron/main.js`（窗口大小/菜单/文件关联）
- [ ] 配置 `electron-builder`（`package.json` build 段）
- [ ] 打包命令：`npm run electron:build`
- [ ] 输出：`release/DeepPhilosophy.exe`（portable 单文件）

### 3.2 优化
- [ ] 内嵌本地后端？或保持连接 localhost:8000
- [ ] 自动启动后端 + 前端（托盘图标管理）
- [ ] 文件关联（.epub / .pdf 默认打开）

---

## 进度总览

| 阶段 | 状态 | 预计 |
|------|------|------|
| 网页端完善 | 🟡 进行中 | — |
| Android APK | ⬜ 待开始 | 网页端完成后 |
| Windows EXE | ⬜ 待开始 | Android 完成后 |
