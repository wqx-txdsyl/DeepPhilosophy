# PhiAgent PWA

2026-10-18：PhiAgent 增加同源 PWA 安装能力，入口仍为 `/agent`，未来 Project 共用这一应用身份与安装包。当前 Project 只有设计，未把未实现的项目路由加入快捷方式。

## 交付

- 侧栏“安装 PhiAgent”；支持原生安装提示的浏览器使用其提示，其他浏览器显示菜单安装指引，独立应用窗口内隐藏安装入口。
- 根目录 `manifest.webmanifest`、`sw.js`、`offline.html`；192 与 512 像素图标沿用已有标识，不重新设计品牌。iOS 保留已有 Apple touch icon。
- 离线新打开或刷新时显示连接提示，不假装能够离线生成回复。此前浏览器保存的聊天不因此删除。
- service worker 只缓存离线页、应用图标与实际请求到的公开静态文件。不缓存 API、带 Authorization 的请求、上传、SSE 或带查询参数的资源；导航使用网络并绕过 HTTP 缓存，断网或服务端 5xx 时回到离线页。
- 新 worker 走默认等待周期，不 skipWaiting，不强行刷新正在流式回答的页面。HTML 导航始终走网络，所以重新打开时能取得最新应用资源；所有旧客户端关闭后，新的 worker 才接管并清理自己的旧静态缓存，不清理其他缓存或用户数据。

## 构建与部署

`agent-app/pwa/build-plugin.js` 在 Vite 构建时生成 PWA 资源；版本指纹涵盖输出资源名、worker、manifest、离线页和图标。`scripts/build_phiagent_static.py` 将它们与现有资源一起同步到 `backend/static`，没有新增对 `agent-app/public/` 本地镜像的跟踪。

`backend/main.py` 通过公开的 `/api/pwa/worker` 返回 worker，设置 JavaScript 类型、根作用域及 no-store。该部署的 CDN 会为普通 `.js` 文件强加四小时 TTL，使用这条不缓存的加载路径避免发版后旧 worker 滞留；构建文件仍为 `sw.js`，根路径只用于兼容。manifest 使用 manifest+json 和 no-cache。开发模式不注册 service worker，避免污染 Vite 调试环境。

## 验证与边界

`agent-app/tests/pwa.test.mjs` 覆盖实际图标尺寸、构建变化引起的缓存更新、私有与 API 请求绕过、公开资源缓存、HTML 不落缓存、离线回退和提前捕获安装事件。真实 Chrome 的普通隔离配置检查公开站 manifest、service worker 控制、无安装条件错误和断网导航；仅新建测试浏览器资料，不访问用户现有浏览器账号，也没有替用户向桌面安装应用。

浏览器第一次使用隐私配置会返回 in-incognito，之后以全新普通配置复测通过。Playwright 的 worker 网络模拟需启用 `PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1`；只把页面标为离线而不模拟 worker，会得到错误的测试结果。原型另做桌面、手机和深色检查，证据在 `docs/evidence/pwa-project-2026-10-18/`。

本轮不承诺离线模型、离线私人文档同步、推送通知、后台常驻研究或原生文件系统权限。这些是独立能力，不由“可安装”自动提供。

安装条件与生命周期依据：[MDN 安装条件](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)、[MDN service worker](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers)。菜单指引依据 [Apple iPhone](https://support.apple.com/en-eg/guide/iphone/iphea86e5236/ios) 与 [Apple Mac](https://support.apple.com/en-au/104996)。
