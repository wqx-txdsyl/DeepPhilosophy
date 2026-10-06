# 第 07 章：让 JavaScript 有一个可以操作的界面

## 7.1 HTML 描述结构

一个最小聊天界面需要标题、消息区域、输入框、提交按钮和状态区域。HTML 标签表达内容角色；CSS 决定视觉；JS 决定行为。

```html
<form id="chat">
  <label for="question">你的问题</label>
  <textarea id="question" required></textarea>
  <button type="submit">发送</button>
</form>
<section id="messages" aria-live="polite"></section>
```

label 与输入框关联，form 提供提交语义，aria-live 帮助辅助技术知道区域变化。不要全部用 div 模拟按钮；原生元素已经处理了一部分键盘和可访问性行为。

## 7.2 DOM 是浏览器内存中的树

```javascript
const form = document.querySelector('#chat');
form.addEventListener('submit', event => {
  event.preventDefault();
  const text = document.querySelector('#question').value.trim();
  const bubble = document.createElement('p');
  bubble.textContent = text;
  document.querySelector('#messages').append(bubble);
});
```

表单默认会提交并导航，preventDefault 阻止这个默认行为。你写的回调随后自行调用 API。查询元素应等 DOM 创建后再执行；模块脚本默认具有延后执行特征。

## 7.3 textContent 与 innerHTML

模型输出和用户输入都可能包含 HTML 字符。`textContent` 将它们作为文字展示；`innerHTML` 会解析标记，可能引入脚本或危险链接等问题。课程基础界面故意用纯文本。

完整产品需要 Markdown 时，应选择经过维护的渲染器，禁用或净化原始 HTML，并对白名单链接协议做检查。不要认为“是模型生成的”就可信。

## 7.4 CSS 的最小知识体系

选择器定位元素；盒模型包含内容、内边距、边框、外边距；布局常用 Flexbox 和 Grid。`box-sizing: border-box` 使宽度计算包含内边距与边框，更容易控制表单尺寸。

```css
* { box-sizing: border-box; }
main { max-width: 860px; margin: 40px auto; padding: 0 24px; }
.actions { display: flex; gap: 12px; }
textarea { width: 100%; font: inherit; }
.message { white-space: pre-wrap; overflow-wrap: anywhere; }
```

`white-space: pre-wrap` 保留换行又允许折行；`overflow-wrap` 防止长字符串撑破布局。移动端不靠固定大宽度，而靠 max-width、百分比和媒体查询。

## 7.5 浏览器开发者工具

Elements 看实际 DOM 和 CSS；Console 看 JS 异常；Network 看请求路径、状态、响应头和内容；Application 看 localStorage。学习时每一个“按钮没反应”都先分层检查：事件是否触发？fetch 是否发出？HTTP 是否成功？响应是否被解析？DOM 是否被更新？

localStorage 保存字符串，在同一 origin 下持久存在。不同端口的存储隔离；无痕模式、清理网站数据等操作也会影响它。它适合一些本地偏好，不是服务端权限来源。

## 7.6 练习

在课程 `web/` 页面对照找到表单、消息、状态、材料面板。复制到自己的练习目录，先移除网络请求，只显示用户消息，再逐步接回接口。

加入“输入为空时禁用按钮”，并确保键盘提交也经过同样校验。加入 600px 以下的布局规则。故意输入 `<img src=x onerror=alert(1)>`，页面应显示文本而不执行代码。

验收：你能独立做出静态聊天页面，并用开发者工具定位元素与请求。参考：[MDN Web 学习入口](https://developer.mozilla.org/zh-CN/docs/Learn_web_development)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](06-javascript-migration.md) · [下一章](08-promises-fetch-and-streaming.md)
