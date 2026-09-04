# PhiAgent → agent.deepphilosophy.top 部署说明（本地后端 + CF 隧道）

> 状态：**已上线** ✅（2026-08-30 实测 `https://agent.deepphilosophy.top` 前端 + API 全通）。
> 隧道已创建（tunnel id `bbc08110-b3ff-45cc-9902-147bdc612e3f`，CNAME 已绑定），本机直连可用。
> 唯一遗留：Windows 服务安装需管理员权限（见下）。

## 架构

```
浏览器 → https://agent.deepphilosophy.top (Cloudflare Tunnel)
                └─→ 本机 localhost:8011 (FastAPI 统一后端)
                        ├─ /              PhiAgent 前端（backend/static，同源）
                        ├─ /assets /icons /covers.json /covers  静态资源
                        └─ /api/*         全部 API（agent/auth/upload/…）
```

前端 `getApiBase()` 返回空串 = 同源调用，所以前端与 API 都走 8011，无 CORS 问题；后端已把 `https://agent.deepphilosophy.top` 加入 CORS 白名单兜底。

## 已完成的本地侧工作

1. **前端托管**：`scripts/build_phiagent_static.py` 构建 agent-app 并同步 `backend/static/`（gitignore，不入库）。8011 根路径即为 PhiAgent SPA（SPA fallback 已覆盖 `/agent/*` 等路由），`/api/*` 由后端路由处理。
2. **8011 防护**（原有 + 本次补充）：
   - 原有：`auth_required`（Bearer 401）、`agent_guard`/`ai_guard`（令牌桶限流 + 每日配额，匿名 60 次/日、登录 300 次/日，按 `cf-connecting-ip` 计）、`upload_guard`、`require_admin`（ADMIN_PASSWORD + 爆破锁定）
   - 新增（audit 2026-08-30）：`auth_guard` —— `/api/auth/register` 与 `/api/auth/login` 按 IP 限流（10 次/分钟，突发 20）+ 每日配额 30，防暴力破解与注册垃圾；测试见 `tests/test_security.py::test_auth_guard_rate_limit`
   - CORS 白名单加入 `https://agent.deepphilosophy.top` 与 `http://localhost:5201`
3. **自动保持拉起**：既有 `dp_backend_watchdog.py`（hermes，开机自启 vbscript + 每 10s 探活 8011，进程消失自动用 `.venv` 拉起）已验证工作——本次多次重启后端均由它自动拉起（日志：`C:\Users\wqx_0\AppData\Local\hermes\logs\dp_backend_watchdog.log`）。

## 已完成的隧道/域名步骤

```bash
cloudflared tunnel login                                 # ✅ 已执行（cert.pem 已存）
cloudflared tunnel create phiagent                       # ✅ 已执行（id bbc08110-…-147bdc612e3f）
cloudflared tunnel route dns phiagent agent.deepphilosophy.top   # ✅ CNAME 已建
```

配置文件 `C:\Users\wqx_0\.cloudflared\config.yml`（已写好）：

```yaml
tunnel: bbc08110-b3ff-45cc-9902-147bdc612e3f
credentials-file: C:\Users\wqx_0\.cloudflared\bbc08110-….json
protocol: http2
edge:
  - 198.41.192.167:7844
  - 198.41.200.23:7844
ingress:
  - hostname: agent.deepphilosophy.top
    service: http://localhost:8011
  - service: http_status:404
```

> `edge:` 两个真实 IP 是为绕过 SakuraCat 的 fake-ip DNS 写死的；若日后连接异常，用
> `curl "https://dns.alidns.com/resolve?name=region1.v2.argotunnel.com&type=A"` 重新解析更新。

## 最后一步：装 Windows 服务（需管理员 PowerShell）

以**管理员身份**打开 PowerShell，执行：

```powershell
# 1. 把配置/凭证复制到 SYSTEM 账户目录（服务以 LocalSystem 运行，找不到用户目录的配置）
New-Item -ItemType Directory -Force "C:\Windows\System32\config\systemprofile\.cloudflared" | Out-Null
Copy-Item C:\Users\wqx_0\.cloudflared\cert.pem,
          C:\Users\wqx_0\.cloudflared\config.yml,
          C:\Users\wqx_0\.cloudflared\bbc08110-b3ff-45cc-9902-147bdc612e3f.json `
          "C:\Windows\System32\config\systemprofile\.cloudflared\" -Force

# 2. 安装并启动服务（开机自启、崩溃自动重启）
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" service install
Start-Service cloudflared

# 3. 验证
Get-Service cloudflared
curl.exe -s https://agent.deepphilosophy.top/api/health
```

### ⚠️ 已知坑：服务 ImagePath 缺参数（2026-08-30 实测）

本版本 cloudflared 的 tokenless `service install` 注册的服务 ImagePath **只有 exe 没有参数**，
服务一启动就退出（ExitCode 1067）。修法（管理员 PowerShell）：

```powershell
$bin = '"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --config C:\Users\wqx_0\.cloudflared\config.yml run phiagent'
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Cloudflared' -Name ImagePath -Value $bin -Type ExpandString
Start-Service cloudflared
```

> 已修复并实测：服务 Running（PID 随重启变化），停掉手动实例后网站由服务独立接管。
> **重装/升级 cloudflared MSI 后此修复会被覆盖，需要重跑上面三行。**

> 若此前手动跑过 `cloudflared tunnel run`，装完服务后把手动进程关掉即可（同隧道多实例不冲突）。

## ⚠️ SakuraCat（代理）与隧道互斥

**实测结论**（2026-08-30）：SakuraCat 开启 TUN 模式时 cloudflared 必然握手失败
（`TLS handshake with edge error: EOF`，http2/quic、新旧版本、真实 IP 全部复现）；
关闭 SakuraCat 后立即恢复。原因：TUN 劫持 DNS（fake-ip 198.18.x）+ 其转发路径对
cloudflared 的 Go TLS 指纹做了处理。与 GFW 无关——直连（电信家宽）7844 完全畅通。

**共存方案**（任选）：
1. 开着 SakuraCat 时不用隧道（隧道服务会一直重试，关掉 SakuraCat 后 10 秒内自动连上）
2. 在 SakuraCat 的 TUN/规则配置里把 `cloudflared.exe` 加入进程绕过白名单（未验证，可自行尝试）

## 验证（已实测通过）

```bash
curl -s https://agent.deepphilosophy.top/api/health   # {"status":"healthy",...}
curl -s https://agent.deepphilosophy.top/             # <title>PhiAgent · 哲学智能体</title>
```

## 日常

- 前端改代码后：`python scripts/build_phiagent_static.py`（重构建 + 同步 backend/static，静态文件随请求即时生效，无需重启 8011）
- 后端改代码后：杀掉 8011 进程，watchdog 10 秒内自动拉起新代码
- 8011 挂了：watchdog 自动拉起；隧道由 cloudflared 服务守护，两者互不依赖
- `C:\Users\wqx_0\.cloudflared\cloudflared-2024.exe`（排障时下载的旧版）已无用，可删
