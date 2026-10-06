# 第 09 章：从操作 DOM 到 React 状态驱动

## 9.1 React 在解决什么问题

原生 JS 中你要手动让 DOM 与数据同步。React 的核心做法是用组件描述“给定状态应显示什么”，状态改变时重新计算界面。不要在 React 管理的同一区域又手动 append DOM，否则会出现两个事实来源。

组件是返回 JSX 的函数。JSX 是构建工具转换的语法，不是浏览器原生 HTML。props 是父组件传入的数据，state 是组件管理的状态。

```jsx
import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(n => n + 1)}>{count}</button>;
}
```

函数式更新 `n => n + 1` 使用 React 提供的前一状态；异步回调中比依赖旧闭包里的 count 更稳妥。

## 9.2 拆分工作区

完整复刻至少需要 ConversationSidebar、ConversationHeader、MessageList、Composer、AgentSelector、SettingsPanel 和证据面板。组件边界取决于职责和状态关系，不是“每 100 行拆一个文件”。

共享状态提升到共同父组件；只影响局部展示的状态留在局部。输入草稿、生成中状态、历史消息是不同的数据，不应共用一个变量。

## 9.3 消息按 id 更新

```javascript
setMessages(previous => previous.map(message =>
  message.id === targetId
    ? { ...message, content: message.content + chunk }
    : message
));
```

渲染列表用稳定 id 作为 key，不使用数组下标代替会变化的身份。删除第一条后，其他条目的下标会变，React 可能把旧组件状态错误地关联给新消息。

## 9.4 useEffect 与 useRef

Effect 用于同步外部系统，如订阅、加载或清理。渲染函数应尽量纯，不要每次 render 都发请求。

```jsx
const requestRef = useRef(null);
useEffect(() => () => requestRef.current?.abort(), []);
```

这是组件内片段，表示卸载时取消请求。ref 保存跨渲染的可变值，不会因为修改 current 而自动触发重渲染，适合 AbortController、请求编号等运行资源。

开发环境可能额外执行 Effect 的安装与清理来暴露问题，不应靠关掉开发检查掩盖资源泄漏。网络请求要有取消或过期结果保护。

## 9.5 建立显式状态机

一条回答可处于 pending、streaming、completed、failed、cancelled。只有 completed 才能作为可信历史参与后续生成。切换会话不等于取消；删除会话通常应取消它的运行请求并拒绝迟到事件。

更完整的数据结构：

```javascript
const state = {
  conversations: {},
  messagesByConversation: {},
  activeConversationId: null,
  runningByConversation: {},
};
```

设计 reducer：事件先验证目标会话仍存在，再验证 invocation_id 仍匹配，最后更新指定消息。仅依靠“当前选中的会话”会造成串写。

## 9.6 课程 React 版本

`examples/phiagent-lab/react-web/` 提供可构建的 React 基础客户端，复用 SSE 解析器，开发代理连接 8021。它用于验证 React 迁移，不包含完整生产工作区。运行方法见项目 README。

真实仓库阅读：`agent-app/src/pages/AgentPage.jsx` 负责工作区；`data/conversationLogic.js` 管理纯逻辑；`data/generalStream.js` 管理事件归约。先画状态转移，再读实现，避免把所有 useEffect 当作互不相关的补丁。

## 9.7 复刻作业

先做到会话新建、重命名、删除、切换、刷新恢复；再做到两个会话各自生成；最后处理删除中的请求、登出清理和新建草稿身份。

必须通过六个场景：A 流式时切 B；B 新建后 A 完成；A 被删除后迟到事件；同一会话双击发送；停止后重新发送；登出时所有运行请求被终止或失去写入权限。

参考：[React 中文教程](https://zh-hans.react.dev/learn)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](08-promises-fetch-and-streaming.md) · [下一章](10-model-api-protocol.md)
