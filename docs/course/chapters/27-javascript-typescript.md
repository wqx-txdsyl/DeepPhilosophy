# 第 27 章：用纯函数解决前端竞态，再引入 TypeScript

本章在第 09 章后学习。我们不靠添加更多布尔值修补竞态，而是建立明确的事件归属。

## 27.1 可运行的 reducer

保存到 `exercises/ownership.mjs` 的实现已经随课程提供，其核心规则如下：

```javascript
export function reduceEvent(state, event) {
  const run = state.runs[event.conversationId];
  if (!state.conversations[event.conversationId]) return state;
  if (!run || run.id !== event.invocationId) return state;
  if (run.status !== 'streaming') return state;
  if (event.type === 'token') {
    return {...state, runs: {...state.runs,
      [event.conversationId]: {...run, text: run.text + event.text}}};
  }
  if (event.type === 'done') {
    return {...state, runs: {...state.runs,
      [event.conversationId]: {...run, text: event.text, status: 'completed'}}};
  }
  return state;
}
```

纯函数不发请求、不操作 DOM、不读全局 currentConversation。输入完全决定输出，因此能用几十行测试覆盖大量 UI 时序。

## 27.2 为什么 invocation_id 必须独立

用户在 A 会话点击停止后立刻重新发送。两个请求属于同一个 conversation_id，可能还复用同一个回答位置，但运行编号不同。旧请求的迟到 token 必须被拒绝，不能追加到新回答中。

同样，完成状态之后到达的重复 token 也不能继续修改已完成答案。done 携带权威完整文本，可以纠正丢帧或累计显示差异，但它的归属必须先验证。

## 27.3 React 如何接入

使用 useReducer 管理状态。请求开始时产生并保存 invocation_id；每个流事件加上发起时冻结的身份，再 dispatch。activeConversationId 只决定显示哪份数据，不决定数据写入哪里。

AbortController 可以保存在 ref 的 Map 中：key 为 invocation_id。删除会话时取消相关请求，并先从 state 移除会话；这样迟到事件即使到达也会被 reducer 拒绝。

## 27.4 JavaScript 的内存与清理

事件监听器、定时器、未关闭的 reader 和 Map 中的旧 controller 会延长对象生命周期。组件卸载时清理，执行完成时删除运行对象。闭包捕获一大份历史可能让它在请求结束前无法释放。

浏览器内存管理是自动的，但可达对象不会因为你“不再关心”就立即消失。你熟悉的资源生命周期思维仍然有用，只是具体工具变成了 effect cleanup、AbortController 和 finally。

## 27.5 TypeScript 的适用位置

TypeScript 在构建阶段检查类型，运行时仍是 JavaScript。它不能替你验证服务端 JSON，外部输入仍需解析与校验。

类型草图：

```typescript
type StreamEvent =
  | { type: 'token'; conversationId: string; invocationId: string; text: string }
  | { type: 'done'; conversationId: string; invocationId: string; text: string }
  | { type: 'error'; conversationId: string; invocationId: string; message: string };
```

按 type 分支后，编译器知道哪些字段可用。这叫可辨识联合，很适合事件协议。比一个所有字段都 optional 的“大对象”更容易防错。

可以先用 JSDoc 给 JS 文件加类型，再迁移少量 `.ts/.tsx`。不要一边迁移语言一边重写全部状态逻辑，否则很难判断错误来自哪里。

## 27.6 CSS 与用户体验的进阶验收

测试窄屏、长回答、长链接、代码块、键盘发送、中文输入法组合输入、低速网络和失败提示。自动滚动要尊重用户正在向上阅读；新 token 到来不应强行把用户拉回底部。

流式渲染每字更新可能造成频繁重绘，可按时间窗口批量刷新，但必须在 done 时补齐剩余内容。优化之前用浏览器性能工具观察，而不是猜测 React 一定慢。

## 27.7 作业

运行 `node --test tests/ownership.test.mjs`。再新增 failed 和 cancelled 事件，确保两者之后的 token 都不能修改答案。把 reducer 接进你的完整会话工作区，并删除依赖“当前选中会话”的写入逻辑。

<!-- NAV -->

[课程目录](../README.md) · [上一章](26-python-architecture.md) · [下一章](28-requirements-to-features.md)
