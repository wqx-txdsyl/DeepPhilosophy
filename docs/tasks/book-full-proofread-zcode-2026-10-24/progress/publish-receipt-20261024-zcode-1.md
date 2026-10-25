# ZCode 发布回执 #1（2026-10-24，锁 owner=zcode-proofread）

## 提交与上线
- push 643b38f69..ca16886f1 → origin/master（含 Q0 注释引擎、上帝之城序言试点、
  《从理想国到正义论》全书审读+介绍、康德著作集阶段性修复、34本介绍草稿）
- CF Pages 部署确认：生产 meta dp-commit = ca16886f
- OSS 增量：章节 41 对象（0失败）；静态资产 20 对象（新前端构建，修复白屏事故）

## 事故与修复记录
- 首次部署后生产白屏：新构建 JS 资产未同步 OSS（章节同步≠前端产物同步）。
  已重建+dp_sync_oss_static.py 上传后恢复。教训入流程：凡含阅读器/前端变更的发布，
  章节与 static 两次同步都必须做。

## 两端验收（生产 deepphilosophy.top）
- 上帝之城 ch0：50 上标 + 50 注释渲染 ✓
- 上标→章末注释→原引用位 双向跳转 ✓（flash 高亮确认）
- URL 直达 ?ch=0&note=10 ✓
- 康德集 ch17 OSS：21 注/21 token ✓；f15e7fd89491 ch12 合并修复 ✓
- 主站 books.json：557 条（含 Codex 新增2本），《从理想国到正义论》新介绍已上线 ✓
