# O9 Responsive Spec — 响应式规格

## 1. 断点与目标设备

| 断点 | 设备 | 布局 |
|---|---|---|
| ≥1024px | Windows/macOS desktop | 侧栏常驻（可折叠）+ 工作区 + 中央消息列 |
| 641–1023px | tablet（横/竖） | 侧栏默认折叠为抽屉（navOpen），工作区全宽 |
| ≤640px | iPhone / Android | 单列；抽屉/侧栏全屏化；EP 网格 2 列；深度控件横向滚动 |

## 2. 组件级规则

| 组件 | desktop | mobile（≤640px） |
|---|---|---|
| SourceDrawer | 右滑 400px | 全宽 100vw（无左边框） |
| EpStarter | auto-fill ≥170px 网格 | 2 列 |
| DepthControls | wrap | 单行横向滚动（chips 不换行不收缩） |
| Composer | 中央定宽 | 底部贴合, 附件面板全宽 |
| 侧栏 | sticky 常驻 | 抽屉（遮罩） |
| 消息正文 | 14.5px | 14.5px（不缩小, 阅读优先） |

## 3. 硬性验收（UAT 已执行口径）

- `document.documentElement.scrollWidth <= window.innerWidth`（零横向溢出）——390×844 实测通过。
- 触控目标 ≥ 36px 高（chips/padding 已达标）。
- 抽屉在移动端全宽可关闭（遮罩/Esc/×）。
- 引用 chips 在 390px 下可点击、标题截断不撑破。

## 4. 性能与加载

- 首屏仅 hydrate 会话列表 + 空态；mermaid/阅读器跳转按需。
- 流式渲染逐 token 写入 memo 气泡（既有）; O9 组件不引入新的重渲染路径（EvidenceChips 分层为纯函数分组）。

## 5. 已知边界

- 321–360px 窄屏（老旧 Android）：EP 网格退化为 1 列即可用，未做专项 UAT（列入 O13 复验）。
- 横屏 tablet 未单独验证（布局规则同 ≥1024 逻辑，列入 O13 复验）。
