# 交付验证记录

日期：2026-09-23。验证范围为本课程与独立实验项目，未修改生产程序和正式书籍数据。

## 已实际执行

| 检查 | 结果 | 说明 |
|---|---|---|
| 独立 Python 3.12 虚拟环境安装 requirements.txt | 成功 | 未依赖生产环境中偶然存在的包 |
| Python 测试 | 22 passed | 工具边界、引用、图循环、API、事务历史、隔离、失败不保存、HTTP 协议替身、检索练习、记忆与书库适配 |
| JavaScript 测试 | 7 passed | SSE 任意字节切分、中文、CRLF、残帧、HTTP 错误、会话与 invocation 归属 |
| Markdown 本地链接与 Python 代码块语法 | 通过 | 68 个 Python 块含合并版重复项；局部字典条目按片段处理 |
| React npm install / build | 成功 | React 19.2.8、Vite 5.4.0；package-lock.json 已生成 |
| Python / JS 迁移练习与手写 Agent | 成功 | 命令见项目 README |
| 离线评测 runner | 4 / 4 通过 | 只测机械链路，不代表真实模型质量 |
| 真实书库只读抽样 | 3 本首章成功读取 | 当前 books.json 读取到 410 条书目；不代表全部可读或全库审核通过 |
| 浏览器 React 页面 | 成功 | 开发代理连接后端、发送问题、完成状态与来源显示 |
| 浏览器原生 JS 页面 | 成功 | 发送问题、完成状态、材料展开，以及重新打开页面后的历史恢复 |

## 明确没有进行

- 没有读取或使用生产模型密钥，也没有发起真实模型付费调用。
- 没有验证真实模型的工具选择、哲学解释质量或不同供应商全部协议。
- 没有完成现有 PhiAgent 的一比一实现；本次交付是完整学习材料、实验项目和复刻验收方法。
- 没有把没有登录保护的课程实验部署到公网。
- 没有执行生产书库写入、CDN / OSS 同步、git 提交或推送。
- React 客户端完成构建及基础浏览器问答验证，未对全部浏览器、移动设备和所有竞态做端到端覆盖。

## 如何复查

在 project 目录：

```bash
.venv/bin/python -m pytest -q
node --test tests/*.test.mjs
.venv/bin/python -m exercises.evaluate
.venv/bin/python -m exercises.corpus --root /Users/sen/DeepPhilosophy --limit 3
```

在 project/react-web 目录：

```bash
npm ci
npm run build
```

requirements.lock 是新建课程虚拟环境的依赖快照。迁移机器或升级依赖后重新执行上述检查；任何真实模型接入都要另外做协议和质量验收。
