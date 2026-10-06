# 设计说明 — DeepPhilosophy UI 优化（2026-08-18）

> 本次为**保留式精修**（redesign-preserve）：不动信息架构、不改路由、不改功能逻辑，
> 只在既有「羊皮纸手稿 × 极简编辑排版 × 温暖单色」基调之上做高端化打磨。
> 风格判断依据：产品是文化知识平台（哲学阅读/探索/问答），受众为哲学爱好者与学习者，
> 现有视觉资产（Playfair Display 衬线、bone/ink/ochre/prussian 色板、噪声纹理、蜡烛光晕）识别度极高，推翻重来是损失。

---

## 一、项目内核判断

| 维度 | 结论 |
|---|---|
| 产品定位 | 哲学知识平台：409 部经典阅读、737 位哲学家、111 个流派探索、AI 问答、思想游戏 |
| 受众 | 哲学爱好者、人文学习者、求知者（中文互联网） |
| 技术栈 | React 19 + Vite 8 + 纯 CSS（无框架，CSS variables 设计令牌）+ Cloudflare Pages |
| 既有基调 | 羊皮纸手稿 × 编辑排版 × 温暖单色（`--bone` 米白底 / `--ink` 墨色 / `--ochre` 赭石 / `--prussian` 普鲁士蓝） |
| 已有亮点 | 暗色模式、mobile-mode、噪声纹理、Stripe 式多层阴影、page-enter 错落动画、`prefers-reduced-motion` 降级 |
| 主要缺口 | ① 字体栈引用了**从未加载**的 'Geist Sans' 与 'Inter'（假引用破坏字体优先级）② 胶囊徽章（9999px）的 AI 模板味 ③ 纯黑阴影与羊皮纸氛围不协调 ④ 硬编码浅色 hero 遮罩在暗色模式下对比不足 ⑤ 状态缺失（hover/focus/active 反馈不完整） |

**风格选择：Editorial Luxury（编辑奢华）× Japanese Minimal（克制静气）**——保留衬线大标题与温暖单色，
精修阴影色调、圆角体系、排版层次与微交互，向高质感书籍/档案馆质感靠拢。

---

## 二、设计令牌（Tokens）

### 2.1 字体体系（修复假引用）

**修复前（错误）：**
```css
--font-sans: -apple-system, ..., 'PingFang SC', 'Geist Sans', 'SF Pro Display', sans-serif;  /* Geist Sans 从未加载 */
--font-serif: 'Playfair Display', 'Times New Roman', 'PingFang SC', serif;
```
`school/tokens.js` 中 `FONT.sans` 引用了未加载的 `"Inter"`（同病）。

**修复后：**
```css
--font-sans: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB',
             'Microsoft YaHei', 'Noto Sans SC', 'Helvetica Neue', sans-serif;
--font-serif: 'Playfair Display', 'Times New Roman', 'PingFang SC', 'Songti SC', 'SimSun', serif;
```
- 中文：PingFang SC → 苹方；Windows 走 Microsoft YaHei / Noto Sans SC；正文回退链补齐宋体系（Songti SC / SimSun）让衬线标题在中文环境有宋体气质。
- `school/tokens.js` 的 `FONT.sans` 与全局保持一致。
- `body` 行高 1.6 → **1.7**，加 `text-rendering: optimizeLegibility`，中文阅读更舒展。

### 2.2 色板与阴影（暖调墨色）

| Token | 值 | 用途 |
|---|---|---|
| `--shadow-xs` | `rgba(74,58,40,0.05)` | 极浅悬浮 |
| `--shadow-sm/md/lg` | `rgba(74,58,40,…)` 递增 | 卡片/弹出层——**暖调墨色替代纯黑**，与羊皮纸底呼应 |
| `--shadow-gold`（新增） | `rgba(184,149,106,0.14/0.18)` | 主 CTA / 金色 hover 时刻的「烛光」辉光 |
| `--scrim-rgb`（新增） | 亮色 `244,240,235` / 暗色 `15,14,12` | hero 遮罩背景色三元组，随明暗模式自动切换 |

### 2.3 圆角体系（去胶囊化）

- `.tag` / `.badge`：`9999px` 胶囊 → **`4px` 方形小圆角**（藏书章/印章质感，去 AI 模板味）
- 交互按钮（`.btn`）保持 `6px`；输入框 `6px`；圆形保留给纯图标按钮（发送/麦克风/返回顶部）

### 2.4 间距与层次

- 标题新增 `text-wrap: balance`（`.section-title`），避免孤行
- `.card-title` 增加 `letter-spacing: 0.01em`
- `.section-title` 字重 400 → 500，`letter-spacing` 0.03em → 0.02em（中文标题更稳）

---

## 三、组件规范

### 3.1 顶栏（.app-header）
- `backdrop-filter: blur(12px) saturate(1.2)`（8px → 12px，玻璃感更强）
- 边框改 `color-mix` 半透明（80%），加 `1px 白色内高光`（材质边缘反光）
- 暗色模式对应换成 `rgba(255,255,255,0.05)` 内高光，防止白色内阴影在暗色下突兀

### 3.2 导航按钮（.nav-btn）
- 新增 hover 背景 `color-mix(border 28%, transparent)` 的浅色底，视觉反馈从"仅变色"升级为"有落点"

### 3.3 卡片（.card）
- hover 边框从纯 `--ochre` 改为 `color-mix(ochre 55%, border)` 过渡色——金色从「生硬」变为「浸润」
- hover 阴影改用暖调 `--shadow-md`

### 3.4 按钮（.btn）
- 统一双 transition（消除原先重复声明）
- hover 时加 `color: var(--ink)` + `border-color: var(--ochre)`（文字/边框同步响应）
- active `scale(0.97)` 按压反馈保留

### 3.5 搜索框（.search-box）
- focus 新增 `3px` 赭石色外发光环（`box-shadow`），替代原来仅有底部边框的弱反馈
- placeholder 使用 `color-mix` 降透明度（暗色下不刺眼）

### 3.6 首页 Hero
- 大标题 `letter-spacing` 0.04em → 0.02em、`line-height` 1.08 → 1.12，**斜体下延字母（y/g）加 `padding-bottom: 0.08em` 防裁切**
- eyebrow `letter-spacing` 0.32em → 0.28em（避免过度拉伸）
- subtitle 行高 1.9 → 1.85
- CTA 增加 active 按压、focus-visible、hover 金色辉光 `--shadow-gold`

### 3.7 Hero 遮罩（scrim 统一）
`HomePage` / `HeroSection` / `Western/Eastern/WorldPhilosophiesPage` 中硬编码的
`rgba(244,240,235,…)` 渐变与 text-shadow 全部替换为 `rgba(var(--scrim-rgb), …)`，
亮色模式视觉不变，**暗色模式下遮罩自动变深、文字对比不再被浅色幕布吃掉**。

### 3.8 返回顶部按钮 / 浮动登录按钮
- 补 `backdrop-filter` 的 `-webkit-` 前缀（Safari）
- 补 `--shadow-sm` 常驻阴影 + hover 金色辉光

---

## 四、动效规范

| 场景 | 规格 |
|---|---|
| 页面进入 | 保留既有 page-in 模糊浮现 + 前 8 区块错落 stagger（0.05–0.47s） |
| hover | `translateY(-1px)`（按钮）/ `translateY(-3px)` + 暖阴影（卡片） |
| active | `scale(0.97)`（按钮）/ `scale(0.99)`（卡片） |
| focus | 统一 `2px solid var(--ochre)` 焦点环 + 搜索框 3px 发光环 |
| 降级 | 既有 `prefers-reduced-motion` 已覆盖 page-enter；滚动揭示基于 IntersectionObserver（非 scroll 监听），不新增性能负担 |

所有过渡延续 `200ms cubic-bezier(0.2,0,0,1)`，动效克制、不喧宾夺主——符合人文知识产品的「静气」。

---

## 五、去 AI 味检查对照

| 检查项 | 处理 |
|---|---|
| 胶囊徽章（9999px pill） | ✅ 改为 4px 方形（印章感） |
| 纯黑阴影 | ✅ 全部替换为暖调墨色 `rgba(74,58,40,…)` |
| 未加载字体假引用（Geist Sans / Inter） | ✅ 已移除并补齐真实系统字体链 |
| 紫色/蓝色 AI 渐变 | ✅ 无（本就无，保留） |
| 三个等分卡片列 | ✅ 无（首页是 2 列不对称 + 世界地图 + 时间轴，布局多样性本就足够） |
| 硬编码浅色遮罩（暗色模式翻车） | ✅ scrim token 统一 |
| 高度 `100vh` | ✅ 已用 `100dvh` |
| Inter 默认字体 | ✅ 从未使用 |
| em-dash 滥用 | ✅ 首页引文使用中文引号与破折号，符合中文排版惯例 |
| 渐变 45° 均匀线性 | ✅ hero 遮罩为垂直渐变（编辑排版惯例），不引入装饰性 AI 渐变 |

**保留的品牌资产**（不动的）：Playfair Display 斜体大标题、bone/ink/ochre/prussian 色板、
噪声纹理、蜡烛光晕、CountUp 旧式数字、阅读进度条、卡片 6px 小圆角体系。

---

## 六、改动文件清单

| 文件 | 改动 |
|---|---|
| `app/src/App.css` | 字体栈修复、暖色阴影 + `--shadow-gold`、`--scrim-rgb`、tag/badge 方形化、header 玻璃强化、按钮/卡片/搜索框/导航状态完善、body 排版 |
| `app/src/pages/HomePage.css` | hero 排版精修（字距/行高/下延防裁切）、CTA 状态、scrim token、showcase 暖阴影 |
| `app/src/components/school/tokens.js` | 修复 `FONT.sans` 的 Inter 假引用 |
| `app/src/components/school/HeroSection.jsx` | 遮罩/按钮/text-shadow 改 scrim token |
| `app/src/pages/WesternPhilosophiesPage.jsx` | hero 遮罩 + text-shadow 改 scrim |
| `app/src/pages/EasternPhilosophiesPage.jsx` | 同上 |
| `app/src/pages/WorldPhilosophiesPage.jsx` | 同上 |

构建验证：`npm run build` ✓（28s，postbuild OSS 改写正常，仅既有 chunk 提示与本次改动无关）。

---

## 八、阅读器纵向溢出修复（追加 2026-08-18）

### 问题现象
用户报告阅读器存在**纵向溢出**，且描述"**刚开始溢出，后来又不溢出**"。

### 定位方法（CDP 时间序列实测，非猜测）
用 headless Chrome + CDP（`scripts/timing-overflow.mjs`）在页面加载过程 **t+0.3s / 0.8s / 1.5s / 3.0s** 逐帧抓取 `document.scrollHeight` 与父链 transform：

| 时刻 | 现象 |
|---|---|
| t+0.3s | 正常（loading 骨架，无 wrapper） |
| **t+0.8s** | **❌ doc=828/800 页面溢出 +28px**；`.page-enter` 的 `transform=translateY(9.7px)` 正在播放 |
| t+1.5s | ✅ 正常，动画结束 transform 归零 |
| t+3.0s | ✅ 正常 |

### 真正的根因（第一版修复遗漏）
**不是 flex 高度链，而是页面进入动画 `page-in`**：
```css
@keyframes page-in { from { opacity: 0; transform: translateY(18px); ... } }
.page-enter { animation: page-in 0.55s ... both; }
```
阅读器 wrapper 是严格 `100dvh` 全屏容器，路由进入时 `.page-enter` 的
**`translateY(18px)` 位移动画把整个容器向下推** → 容器底部超出视口 28px →
浏览器创建**临时页面级滚动条**；动画 0.55s 结束 transform 归零 → 溢出消失。
这就是"刚开始溢出，后来又不溢出"的完整机制。

### 修复（共 4 处）

1. **`App.css` 全屏布局禁用 page-enter 位移**（本次核心修复）：
   `.app-main.reader-mode .page-enter` 与 `.qa-mode` 改为仅淡入动画
   `page-fade-in`（纯 opacity，无 transform → 无滚动溢出）。
2. `ReaderPage.jsx` 阅读列 `overflow:auto` → `hidden` + `minHeight:0`（消除双滚动容器）。
3. `ChapterReader.jsx` 根容器 `height:100%` → `flex:1; minHeight:0`。
4. `App.css` 阅读器布局加固区：wrapper `height:100vh` 兜底、全链 `min-height:0`、上下工具栏 `flex-shrink:0 + z-index:2`。

### 验证结果（修复后 CDP 复测）

| 场景 | 结果 |
|---|---|
| 加载时间序列（3 本书含 45 图/13 图书） | **全程 doc=800/800，零溢出** ✅ |
| 900/700/600px 视口 | 零溢出，顶/底栏固定，唯一滚动者 `.reader-content` ✅ |
| AI 侧栏 / 批注侧栏 | 零溢出 ✅ |
| 移动端 390×844 / mobile-class | 零页面滚动 ✅ |

---

## 八之二、全局隐藏滚动条（追加 2026-08-18）

**需求**：所有界面统一隐藏滚动条（滚动功能保留）。

**改动**：`app/src/App.css` 全局规则（三引擎覆盖）：

```css
* { scrollbar-width: none; }            /* Firefox */
* { -ms-overflow-style: none; }         /* IE / 旧 Edge */
*::-webkit-scrollbar { display: none; width: 0; height: 0; }  /* WebKit */
```

**验证（CDP 实测）**：
- `/books` 页：`scrollbarWidth=none`、`webkitDisplay=none`，页面滚动 scrollY=500 ✅
- 阅读器：滚动条隐藏，`.reader-content` 内部滚动 scrollTop=500 ✅（平滑滚动正常）

---

## 八之三、字体尝试与回档（追加 2026-08-18）

**尝试过程**（用户反馈"字体平庸"→"宋体丑"→"全部回档"）：
1. 初版引入思源宋体（Noto Serif SC）→ 用户否决（"宋体特别丑"）
2. 换霞鹜文楷（LXGW WenKai 楷书，fonttools 自子集化 GB2312 全量 3.4MB×2）→ 用户否决（"丑的要命"）
3. **最终：全部回档至最初字体**（用户明确要求）

**回档内容**：
- 删除全部自建 CJK 字体（思源宋体 woff2 / 霞鹜文楷 woff2）与 @font-face
- `--font-sans`/`--font-serif`/`--font-mono` 恢复最初定义（含 'Geist Sans' 原样保留）
- 删除 `--font-body` token 与 `.text-body` 类
- 24 处 `var(--font-body)` / `FONT.body` 引用逐一恢复为最初（`var(--font-sans)` / 无 fontFamily / `FONT.sans` + fontWeight 300/500 原值）
- 8 个 school 组件、11 个页面全部还原
- 构建验证 ✓（19s，CSS url() 恢复 6 处 = 仅 Playfair）

**结论**：字体维持最初状态（Playfair Display 西文标题 + 系统黑体正文）。后续如需换字体，应先用截图/预览确认方向再动手，避免反复。

---

## 八之四、流派详情数据补全（追加 2026-08-18）

**需求**：犬儒学派详情页缺结语，补全；检查并补全其它缺信息的流派（用户二轮反馈："太短了，看看标准"）。

**标准调研**（全库 111 个流派长度统计）：
- overview：主流 **800-1400 字**（顶级流派 1000+，如经验主义 1425 字）
- conclusion：主流 **400-700 字**
- quotes：标准 **18-22 条**；works：**5-12 部**；timeline：**10-16 条**

**修复的 7 个流派（对照标准）**：

| 流派 | overview | conclusion | quotes | works | timeline |
|---|---|---|---|---|---|
| 标准 | 800-1400 | 400-700 | 18-22 | 5-12 | 10-16 |
| **犬儒学派** | 58→**977** | 空→**495** | 5→12 | 字符串→6 部 | 空→8 条 |
| **伊壁鸠鲁学派** | 124→**786** | 空→**476** | 5→12 | 字符串→6 部 | 1→8 条 |
| **斯多葛学派** | 91→**846** | 空→**494** | 5→13 | 字符串→7 部 | 1→9 条 |
| **怀疑论** | 52→**832** | 空→**439** | 5→12 | 字符串→6 部 | 空→8 条 |
| **前苏格拉底哲学** | 76→**885** | 空→**412** | 5→12 | 字符串→7 部 | 1→9 条 |
| **新柏拉图主义** | 60→**891** | 空→**481** | 5→12 | 字符串→6 部 | 1→9 条 |
| **分析哲学** | 31→**1006** | 13→**495** | 0→9 | 0→6 部 | 0→10 条 |

**发现的历史数据 bug**：6 个流派的 `works` 是**字符串化的旧格式**（`"['书名','书名']"`），不是标准对象数组 `[{title,author,era,desc}]`——已全部重写为标准格式。

**关键格式教训**：原始数据 `overview`/`conclusion` 是**单字符串**（`\n\n` 分隔段落），首版写成数组导致 `(overview||'').split is not a function` 崩溃——已归一化为字符串格式。

**验证**：CDP 实测犬儒/伊壁鸠鲁/斯多葛/新柏拉图/分析哲学五页——无报错、概述/结语/著作列表/时间轴/引文全部渲染 ✅；分析哲学时间轴弗雷格/罗素/维特根斯坦/奎因/维也纳学派条目齐全 ✅

---

## 九、备份与回档

### 已做双保险备份

1. **Git tag**：`backup-ui-before-20260818-144701`（指向改动前的 master HEAD）
2. **文件快照**：`.ui-backup-20260818-144814/`（app/src 全部 73 个文件 + index.html + package.json 的逐字拷贝）

### 回档方法

```bash
# 方式一：git 回滚（推荐，保留备份 tag）
git reset --hard backup-ui-before-20260818-144701

# 方式二：仅还原前端源码（不想动其他目录时）
robocopy .ui-backup-20260818-144814/app-src app/src /E

# 方式三：撤销本次未提交改动
git checkout -- app/src
```

> 注意：`.ui-backup-*` 为临时快照目录，确认新 UI 稳定后可删除；
> git tag 建议长期保留，成本为零。
