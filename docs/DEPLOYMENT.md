# DeepPhilosophy 全站部署架构（2026-09-06 Mac 版）

> 写给接手者：读完这一篇就能回答「网站是怎么跑起来的、每个域名指向哪里、改了代码要发布到哪里」。
> 机器迁移史：~~Windows（wqx_0）~~ → **本机 Mac**（2026-09-06 起，PhiAgent 后端 + agent 隧道已迁至本机）。
> 旧版 Windows 迁移说明存档于 [PhiAgent_agent_deploy.md](PhiAgent_agent_deploy.md)（已过时，仅作历史参考）。

---

## 0. 一张图看懂

```
                        ┌──────────────────────────────────────────────┐
                        │                 Cloudflare                   │
                        │        Zone: deepphilosophy.top              │
                        └──────────────────────────────────────────────┘

 ① 平台主站（阅读器）
 浏览器 ──→ deepphilosophy.top ──→ Cloudflare Pages（app/ 构建产物，自定义域）
                │
                ├─ 章节内容 ──→ jsDelivr CDN（读 GitHub 仓库 backend/data/book_chapters/，按 commit 引脚）
                │             └→ 国内直连兜底：阿里云 OSS（dp_sync_oss_chapters.py 同步）
                ├─ 书内图片 ──→ OSS CDN deepphilosophy.oss-cn-shanghai.aliyuncs.com
                └─ /api/*  ──→ Cloudflare Workers（deepphilosophy-auth + deepphilosophy-api，D1 数据库）

 ② PhiAgent 智能体
 浏览器 ──→ agent.deepphilosophy.top ──→ Cloudflare Tunnel「phiagent-mac」
                └─→ 本机 Mac localhost:8011（FastAPI 统一后端，launchd 常驻）
                     ├─ /            PhiAgent 前端 SPA（backend/static/，同源托管）
                     └─ /api/*       智能体 + 平台 API（同后端单进程）
```

**两套后端并存，互不相干**：
- 平台主站 `deepphilosophy.top/api/*` → **Cloudflare Workers**（云端，无服务器）
- PhiAgent `agent.deepphilosophy.top`（全部流量）→ **本机 Mac :8011**（经隧道回源）

---

## 1. 域名与 DNS（Cloudflare Zone: deepphilosophy.top）

| 名称 | 类型 | 指向 | 代理状态 | 用途 |
|---|---|---|---|---|
| `deepphilosophy.top` | A | 104.21.92.157 / 172.67.195.106（Cloudflare 边缘，橙云扁平化） | 🟠 橙云 | 平台主站前端（Pages 自定义域） |
| `deepphilosophy.top/api/*` | Workers Route | `deepphilosophy-api` worker（见 wrangler.toml） | — | 平台 API（`/api/auth/*` 由 auth worker 优先接管） |
| `agent.deepphilosophy.top` | CNAME | `613c3390-250f-41ee-a46c-b31f7663f8df.cfargotunnel.com` | 🟠 橙云 | PhiAgent 前端+后端（→ 本机隧道） |
| `www` | — | 未配置 | — | 不存在，访问 www 无解析 |
| `api.deepphilosophy.top` | — | 不存在 | — | 平台 API 不走子域，走主域路径路由 |

> ⚠️ **本机查 DNS 的坑**：Mac 上有 Clash fake-ip（`dig` 返回 `198.18.x.x` 是假地址）。
> 查真实 DNS 用 DoH：
> ```bash
> curl "https://dns.alidns.com/resolve?name=agent.deepphilosophy.top&type=A"
> ```

### CNAME 的实际意义
`agent.deepphilosophy.top` 的 CNAME 目标是**隧道 ID**，不是某台机器的 IP。谁在本机跑
`cloudflared tunnel run phiagent-mac`（凭证匹配 `613c3390-…json`），公网流量就进谁的机器。
换机器 = 新建/复用隧道 + `tunnel route dns` 把 CNAME 改指新隧道 ID，一分钟完成切换。

---

## 2. 组件清单（谁在哪、怎么动）

### 2.1 GitHub 仓库 `wqx-txdsyl/DeepPhilosophy`
- **双主线**：`master` = 平台主线（CF Pages 从它构建）；`refactor/phiagent-main-agent-orchestration` = PhiAgent 主线（**永不 merge master**，见 HANDOVER 文档）。
- `backend/data/book_chapters/` 是章节内容的**唯一 git 跟踪源**。jsDelivr 按 commit 读它：
  `https://cdn.jsdelivr.net/gh/wqx-txdsyl/DeepPhilosophy@<commit>`（`app/src/pages/ReaderPage.jsx:26`，commit 由构建注入的 `dp-commit` meta 决定）。
- GitHub Actions：`consistency-check.yml`（push master 时跑元数据一致性 + backend pytest 门禁）。
- 章节数据 push 后 jsDelivr 才有新内容 → **章节改动必须 push**。

### 2.2 Cloudflare Pages —— 平台前端
- 构建根 `app/`，push `master` 自动 `npm run build`，生产域 `deepphilosophy.top`（构建预览域 `deepphilosophy.pages.dev`）。
- postbuild 注入 `__COMMIT_HASH__` / `<meta name="dp-commit">`，章节 CDN 引脚随构建自动更新。
- **改了前端引用的静态资源后**还需抓取构建产物上 OSS：
  ```bash
  python backend/tools/dp_grab_cf_assets.py https://deepphilosophy.pages.dev --upload
  python backend/tools/dp_sync_oss_static.py
  ```

### 2.3 Cloudflare Workers —— 平台生产 API（主体）
- `workers/auth` → worker `deepphilosophy-auth`，route `deepphilosophy.top/api/auth/*`（登录注册 JWT）
- `workers/api`  → worker `deepphilosophy-api`，route `deepphilosophy.top/api/*`（AI 流式/问答/历史/笔记/文件 302）
- 数据库：D1 `deepphilosophy-db`（id `7db39390-6088-4cf5-a283-4697fc876091`），schema 见 [DATABASE.md](DATABASE.md)
- 密钥全部走 `wrangler secret put`（JWT_SECRET 双 worker **必须同值**；DEEPSEEK_API_KEY；ADMIN_PASSWORD），`wrangler.toml` 里只留明文可公开 vars
- 部署：`cd workers/api && wrangler deploy`（auth 同理）
- 健康检查：`https://deepphilosophy.top/api/health`

### 2.4 Cloudflare Tunnel —— PhiAgent 后端 = 本机 Mac ★
- 隧道名 `phiagent-mac`，id `613c3390-250f-41ee-a46c-b31f7663f8df`（2026-09-06 创建）
- 本机凭证：`~/.cloudflared/cert.pem`（账号授权）+ `~/.cloudflared/613c3390-….json`（隧道凭证，**勿入库勿外传**）
- 路由配置 `~/.cloudflared/config.yml`：
  ```yaml
  tunnel: 613c3390-250f-41ee-a46c-b31f7663f8df
  credentials-file: /Users/sen/.cloudflared/613c3390-250f-41ee-a46c-b31f7663f8df.json
  ingress:
    - hostname: agent.deepphilosophy.top
      service: http://localhost:8011
    - service: http_status:404
  ```
- 协议 QUIC，在 Clash TUN/fake-ip 环境**实测直通正常**（旧 Windows 文档里写死 edge IP 的绕过手段本机不需要；若日后连不上再按旧文档用 DoH 重解析 edge 写死）
- 旧 Windows 隧道 `phiagent`（id `bbc08110-b3ff-45cc-9902-147bdc612e3f`）**已无流量**（CNAME 已改指新隧道），账号里还挂着；确认不要后可 `cloudflared tunnel delete phiagent` 清理

### 2.5 阿里云 OSS
- Bucket：`deepphilosophy`（`oss-cn-shanghai`），即 `deepphilosophy.oss-cn-shanghai.aliyuncs.com`
- 内容：书内图片 `book_images/`、封面、CF Pages 构建产物镜像（jsDelivr 的国内直连兜底）
- 关键脚本：`dp_grab_cf_assets.py`（抓 CF 产物）→ `dp_sync_oss_static.py`（传 OSS）；`dp_sync_oss_chapters.py [bid]`（**章节上线双轨**，漏跑则国内阅读器 404）
- 凭证在根 `.env`（OSS_ACCESS_KEY / OSS_SECRET_KEY / OSS_BUCKET / OSS_ENDPOINT）

### 2.6 Cloudflare R2（可选书籍存储后端）
- Bucket `deepphilosophy-books`；`backend/services/book_scanner.py` 支持 local/OSS/GitHub/R2 四种存储后端，由 `.env` 开关（USE_OSS / R2_* 变量）决定。本机默认读本地 `backend/data/book_chapters/`。

### 2.7 本地开发端口（不对外）
| 端口 | 服务 | 启动 |
|---|---|---|
| 8011 | 统一后端（生产常驻，launchd） | `launchctl` 自动；手动 `cd backend && python main.py` |
| 5173 | 平台前端 dev | `cd app && npm run dev`（/api 代理 → 8011） |
| 5201 | PhiAgent 前端 dev | `cd agent-app && npm run dev`（/api 代理 → 8011） |

---

## 3. 本机 Mac 常驻服务（launchd，开机自启 + 崩溃自动拉起）

两个 LaunchAgent，plist 落盘在 `~/Library/LaunchAgents/`：

| Label | plist | 作用 |
|---|---|---|
| `com.deepphilosophy.backend` | `com.deepphilosophy.backend.plist` | 用 `.venv/bin/python main.py` 跑 8011（cwd=backend，SERVER_PORT=8011） |
| `com.deepphilosophy.tunnel` | `com.deepphilosophy.tunnel.plist` | `cloudflared tunnel run phiagent-mac`（代理公网流量进 8011） |

两者均为 `RunAtLoad`（登录即启）+ `KeepAlive`（进程退出 10s 内自动拉起）。**登录 Mac 即全站自动恢复**，无需手动操作。

### 常用命令
```bash
# 看状态（第一列是 PID，带 "-" 表示没在跑）
launchctl list | grep deepphilosophy

# 改完代码重启后端（杀掉后 KeepAlive 自动拉起新的）
launchctl kickstart -k gui/$(id -u)/com.deepphilosophy.backend

# 停止/卸载（KeepAlive 会杀不死进程，必须先 unload）
launchctl unload ~/Library/LaunchAgents/com.deepphilosophy.backend.plist
launchctl unload ~/Library/LaunchAgents/com.deepphilosophy.tunnel.plist

# 重新加载（改了 plist 后）
launchctl unload … && launchctl load ~/Library/LaunchAgents/com.deepphilosophy.*.plist

# 日志（stdout / stderr 分开）
tail -f backend/data/logs/backend.launchd.err.log   # 后端
tail -f backend/data/logs/tunnel.launchd.err.log    # 隧道
```

### 后端托管的 PhiAgent 前端
8011 根路径直接服务 SPA（`backend/static/`，gitignore 本地产物）。改了 `agent-app/` 后重建：
```bash
python scripts/build_phiagent_static.py   # npm build agent-app → 同步 backend/static/
```
隧道是实时的，重建完刷新网页即生效，无需任何"部署"动作。

### 后端关键配置（根 `.env`）
`SERVER_PORT=8011`；AI key（DEEPSEEK/ZHIPU/AGNES）；OSS/R2 凭证；`ADMIN_PASSWORD`（管理接口）。
CORS 白名单已含 `https://agent.deepphilosophy.top` 与 `http://localhost:5201`（同源调用其实用不到）。

---

## 4. 发布手册（改了什么 → 走什么管线）

| 改动 | 操作 | 生效路径 |
|---|---|---|
| 平台前端 `app/src` | push `master` | CF Pages 自动构建，1-2 分钟 |
| 章节内容 `backend/data/book_chapters` | 双写同步 → push → `dp_sync_oss_chapters.py [bid]` | jsDelivr（海外）+ OSS（国内直连）双轨，**漏跑 OSS 国内 404** |
| 书籍元数据 `books.json` / `book_detail/` | push `master`（+ 必要时 OSS 双轨） | Pages 构建带走 |
| Workers `workers/` | `cd workers/xxx && wrangler deploy` | 立即 |
| PhiAgent 前端 `agent-app/` | `python scripts/build_phiagent_static.py` | 立即（8011 同源，隧道实时） |
| PhiAgent 后端 `backend/` | `launchctl kickstart -k gui/$(id -u)/com.deepphilosophy.backend` | 立即 |
| AIAuthor 六库 `data/ai_author/` | 仅本地文件，无需部署 | 8011 直接读 |

---

## 5. 验证清单（部署后/开机后各跑一遍）

```bash
# 1. 本机后端
curl -s http://localhost:8011/api/health            # {"status":"healthy",...}

# 2. 公网隧道链路
curl -s https://agent.deepphilosophy.top/api/health # 应与本机返回一致
curl -s -o /dev/null -w "%{http_code}\n" https://agent.deepphilosophy.top/            # 200 SPA
curl -s -o /dev/null -w "%{http_code}\n" https://agent.deepphilosophy.top/api/agent/tools  # 200

# 3. 平台生产 API（Workers，与隧道无关）
curl -s https://deepphilosophy.top/api/health       # 200

# 4. 隧道连接状态
grep "Registered tunnel connection" backend/data/logs/tunnel.launchd.err.log | tail -4
```

## 6. 故障排查速查

| 症状 | 先查 | 处理 |
|---|---|---|
| agent 域名 530/超时 | `launchctl list \| grep deepphilosophy` 两个 PID 都在？ | 隧道挂了 → 看 `tunnel.launchd.err.log`；后端挂了 → 看 `backend.launchd.err.log`；KeepAlive 都会自动拉起，偶发抖动等 10s |
| 后端反复重启 | `backend.launchd.err.log` | 常见为依赖/`.env` 问题；手动 `cd backend && python main.py` 复现 |
| `dig` 查 DNS 得 198.18.x.x | — | Clash fake-ip，不是故障；用 DoH 查真实记录（见 §1） |
| 隧道连不上边缘（QUIC 失败） | `tunnel.launchd.err.log` 有无 `Registered tunnel connection` | 本机 Clash 下 QUIC 直通正常；若异常，按旧文档 `PhiAgent_agent_deploy.md` 用 DoH 解析 `region1.v2.argotunnel.com` 写死 `edge:` 到 config.yml |
| 国内阅读器章节 404 | 是否跑了 `dp_sync_oss_chapters.py` | 补跑即可 |
| 平台 API 挂 | `https://deepphilosophy.top/api/health` | 与本机无关，查 Workers（`wrangler tail`）/ D1 |

## 7. Render 状态

**已完全退役（2026-08-11）**，无任何流量指向。仓库内见到 onrender/Render 引用一律清理。当前架构里没有传统服务器：平台 API = Workers（云），PhiAgent = 本机隧道。

## 8. 安全要点

- `~/.cloudflared/cert.pem` 与 `613c3390-….json` 是**账号级凭证**（0600 权限），泄露 = 任何人可把 agent 域名指到自己的机器；切勿入库、切勿外传
- 8011 对公网暴露的防护（`backend/guard.py`）：Bearer 鉴权 + 令牌桶限流 + 每日配额 + 注册/登录按 IP 限流 + admin 爆破锁定
- `.env`（含全部密钥）已 gitignore；Workers 密钥走 `wrangler secret`
- 隧道只暴露 `agent.deepphilosophy.top` 一个主机名，其余请求 404（config.yml 最后一条 ingress）
