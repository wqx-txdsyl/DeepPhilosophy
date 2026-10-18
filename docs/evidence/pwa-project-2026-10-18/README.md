# PWA 与 Project 设计 · 2026-10-18

本轮上线的是 PhiAgent 的 PWA 能力。Project 仍是设计：没有创建虚假的生产入口、项目保存或真人协作服务。

## PWA

前端完整测试与构建通过。新 `pwa.test.mjs` 检查 manifest、真实 192/512 图标、worker 更新指纹、私有/API/SSE 绕过、公开资源缓存与离线页，并验证安装事件能在账户页面挂载之前捕获。部署脚本同步根资源；公开站的 `/api/pwa/worker` 使用 JavaScript、根作用域和 no-store，manifest 使用 manifest+json 和 no-cache。

真实 Chrome 使用全新测试资料，未接触现有用户浏览器资料，也未真正向用户桌面安装应用。检查 manifest 无解析错误、安装条件错误列表为空、worker 接管以及断网新导航的离线回退。恢复联网后检查缓存 URL，没有 `/api/` 记录。结果在 `browser-checks.json`，截图 `pwa-offline.png`。

初次以隐私浏览器上下文检查时，浏览器只报告 in-incognito；改用全新普通资料后通过。Playwright 1.56.1 对 worker 的网络模拟默认关闭，须启用 `PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1`；否则页面离线但 worker 仍可联网，不能据此认定离线回退失败。测试资料在结束时删除。

没有宣称已实际安装到 iPhone/Android/Safari，或实现离线模型、推送、后台常驻任务和离线私人项目同步。原生安装仍由用户在自己的浏览器中选择。

检查发现该部署的 CDN 会为普通 `.js` 文件加四小时缓存，即使 origin 返回 no-cache。最终改用公开的无扩展名 API 加载 worker，真实公开响应已确认 no-store；没有只在本地设置 header 就宣称解决。见 `public-headers.json`。

## Project

设计合同为 `docs/ui/chat-project-design.md`，原有草案同步更新 Chat / Project 顶层分区及 41 个入口。

`project-prototype.html` 保存本轮交互原型的静态源快照，原始对话内源及指纹见 `prototype-source.json`。使用示例项目和明确标识的模拟发言，不执行 API，不发送真人邀请，不将示例反馈当作真实观察。原型中的“采纳”只修改预览。

在真实浏览器测试并检查桌面、手机与深色显示：

- 对话可带入项目，仍标明讨论来源。
- 研究、研讨、实践使用同一项目，打开不同对象。
- 已变动的原文不会被旧修改建议覆盖；不同对象各自记录版本。
- 分歧可留存而不强迫形成共识；空反馈不会产生调查结果。
- 手机可以切换工作对象与讨论，无横向溢出。
- 回答者切换与输入有效；修复预览宿主状态回传导致输入焦点丢失、旧回答者状态复写的问题。

截图是交互后的预览状态，不是已上线 Project 的截图。浏览器运行没有脚本异常。未来工程仍需项目级所有权、持久材料、文稿版本、任务续接与真人成员权限；不能把原型的本地交互当作这些能力已经完成。
