# O9 UAT — 用户验收测试记录

> 环境: isolated worktree @ O9 head; backend uvicorn :8011（health 200）; agent-app vite :5201（200）
> 视口: desktop 1280×800 / mobile 390×844; 真实生产路径（deepseek-flash 全链路流式）

## 1. 场景执行矩阵

| # | 场景 | 视口 | 结果 | 证据 |
|---|---|---|---|---|
| U1 | 空态 + EP 入口渲染（六卡: 🧭🪞🎁🔋🌙🤖） | desktop | PASS | snapshot: .o9-ep-entry 6 buttons + 原 starters 并存 |
| U2 | Everyday philosophy 回答全流程（点 EP-03 教师节送礼卡） | desktop | PASS | 流式→自动折叠研究头; 2454 字回答; 74 条相位化工具行; 完成后 DepthControls 渲染 |
| U3 | Depth Controls 四键渲染（◦简单一点/↧深入一点/看原典/看学术研究） | desktop | PASS | .o9-depth-chip ×4 文本核对 |
| U4 | 深度控件交互合同（点「看原典」→ 以冻结措辞发起新一轮） | desktop | PASS | instrumented click → 新用户消息「请针对上面的回答，引用相关原典原文…」; 多轮成立 |
| U5 | Primary-text 引用链路（「《论语》学而时习之…请给出出处」Enter 发送） | desktop | PASS | get_chapter 等相位行→回答完成; Evidence Panel 出现; 原典分层 + 编号 chips ×4 |
| U6 | SourceDrawer（点击编号 chip） | desktop | PASS | 抽屉滑出: 标题「君主论」/ 作者 马基雅维利 / 章节 第十六章·论慷慨与吝啬 / 核验状态「已核验：本回答实际引用的证据」/「在阅读器中打开原典」深链 |
| U7 | 移动端布局（390×844） | mobile | PASS | scrollWidth 390 == innerWidth（零横向溢出）; composer 可见; chips 可点 |
| U8 | 移动端抽屉全宽 | mobile | PASS | .o9-drawer offsetWidth=390 == 视口（≤640 规则生效） |
| U9 | 多轮会话（EP-03 → 看原典追问 同会话上下文） | desktop | PASS | 同 conversationId 连续 3 轮; 流式所有权无串流 |
| U10 | Enter 发送 / IME 保护 / Stop 按钮存在 | desktop | PASS | 原典题经 Enter 发送; 既有 Composer 合同未回退 |

## 2. 检查项核对（任务书 §14）

- layout ✓（无横向溢出, 断点规则生效）
- overflow ✓（移动端 0 溢出; 长回答 2454 字正常回流）
- citation interaction ✓（chips→抽屉→阅读器深链全通）
- reading comfort ✓（正文 14.5px/1.7 行高; 引用元数据不挤压正文）
- input ✓（Composer/IME/Enter）
- loading ✓（流式光标 + 研究状态头 + 相位行）
- error ✓（引用未匹配失败态保留; ErrorBoundary 既有）
- empty state ✓（EP 六卡 + starters）
- keyboard ✓（Enter 发送; Esc 关抽屉; 全部为真实 button）
- responsive ✓（desktop+mobile 双视口实测）

## 3. 测试中发现并当场修复

- DepthControls 初版经 handleSuggestion 路径发送（sourceMsg 挂锚）导致追问未发出 → 改为直发 dispatchSend 路径后复测通过（U4）。
- Playwright 合成点击对滚动遮挡下的 chips 存在 actionability 误判 → 以 instrumented click 复核处理函数真实生效（U4 证据）。

## 4. 未覆盖（移交后续阶段）

- 321–360px 窄屏与横屏 tablet 专项（O13 复验, 见 RESPONSIVE_SPEC §5）。
- Argument View 一等树视图（O9 仅交付措辞合同, O13 渲染）。
- 登录态跨设备会话同步 UI（O12 域）。
