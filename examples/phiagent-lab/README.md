# PhiAgent Lab：课程的可运行实验项目

这是完整复刻课程的基础实验与参考练习，不是已完成的生产 PhiAgent。主课程见 [docs/course](../../docs/course/README.md)，完整验收见 [毕业清单](../../docs/course/graduation-checklist.md)。

## 启动原生 JavaScript 版本

在本目录运行，要求 Python 3.12：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn phiagent_lab.app:app --host 127.0.0.1 --port 8021
```

打开 `http://127.0.0.1:8021`。默认 mock 模式，输入“自由与责任有什么关系？”。三个内置材料都是原创教学概述，不是哲学家原文。MockModel 固定演示工具流程，不测试模型理解能力。

Windows 可直接使用 `.venv\Scripts\python.exe` 运行 pip 与 uvicorn，无需激活脚本。

## React 版本

保持上面的 Python 服务运行，另开终端：

```bash
cd react-web
npm ci
npm run dev
```

打开 `http://127.0.0.1:5178`。此版本用于学习 React 状态、请求取消和流式更新；刷新后创建新会话。完整会话列表与恢复是第 09 章作业。`npm run build` 验证生产构建；dist 的正式托管需要自行配置 `/api` 反向代理，Vite 开发代理不会随构建自动上线。

## 终端与独立练习

从本项目根目录运行：

```bash
python -m phiagent_lab.cli
python -m exercises.migration
python -m exercises.manual_agent
python -m exercises.evaluate
node exercises/migration.mjs
```

真实书库的只读抽样（此路径按你自己的仓库调整）：

```bash
python -m exercises.corpus --root /Users/sen/DeepPhilosophy --limit 3
```

## 验证

```bash
python -m pytest -q
node --test tests/*.test.mjs
```

`requirements.txt` 固定直接依赖；`requirements.lock` 是独立课程环境实际安装的传递依赖快照，可用 `python -m pip install -r requirements.lock` 复现该环境。跨平台仍可能有底层包差异。

## 真实模型

必须显式设置 `PHI_MODE=real`、`PHI_MODEL`、`PHI_API_KEY`，可选 `PHI_API_BASE`。详细步骤见第 10 章。默认 DeepSeek 基础地址，普通非思考模式，最终回答消费真实上游流；兼容服务可能需要不同配置或适配器修改。课程交付只进行了离线与协议替身验证，没有使用真实密钥或付费生成。

## 能力边界

已实现：两个工具、参数校验、有界 LangGraph 循环、SSE、原生 JS 与 React 客户端、取消、SQLite 成功历史、基础引用 id 检查、离线和真实 HTTP 适配接口、测试。

独立练习实现但未接入主图：融合排序、文本分块、逐字定位、用户范围记忆、研究预算、真实书库只读适配器。

完整产品仍需按课程实现：身份与权限、所有工具与人格、向量索引、完整引用支持关系、长任务恢复、研究服务、多会话同步、上传与产物、生产部署等。实验服务没有认证，只适合绑定回环地址的单人学习环境。

流中的 token 是待校验显示；done 才表示校验与保存完成。引用校验不等于语义正确。历史保存最近完整问答，上下文按条数截断，没有完整 token 预算或摘要。进程内同会话并发保护不适用于多 worker。当前基础流未加入生产心跳。
