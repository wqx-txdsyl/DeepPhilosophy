# 第 06 章：JavaScript 从零学，但利用你的 Java / C++ 基础

## 6.1 先拆开语言与运行环境

JavaScript 是语言；浏览器提供 DOM、fetch 和页面事件；Node.js 提供文件系统、进程等服务端能力。同一语言在不同环境可用的 API 不同。Node 能运行算法练习，不代表能直接访问 `document`。

创建 `exercises/hello.mjs`，写 `console.log("你好，JavaScript");`，在项目根目录运行 `node exercises/hello.mjs`。`.mjs` 明确采用 ES Module，后面可以直接使用 import/export。

JavaScript 与 Java 名字相近，但它没有 Java 的同一套类、类型、线程和内存模型。语法相似处可以迁移，运行机制必须重新建立。

## 6.2 let、const 与动态类型

```javascript
let count = 1;
count = 2;
const book = { title: '自由', tags: [] };
book.tags.push('伦理学');
console.log(book);
```

`const` 限制绑定重新赋值，不会冻结对象。`book = {}` 会报错，`book.title = '知识'` 可以。通常优先 const，需要重新绑定时才用 let；入门阶段不使用有函数作用域和提升细节的 var。

数字通常是 IEEE 754 双精度，超大整数不能随意用 Number 保存，数据库长整数 id 可用字符串传输。`0.1 + 0.2` 的结果也体现浮点精度限制，与你熟悉的浮点数问题同源。

## 6.3 null、undefined 与默认值

`undefined` 常表示未赋值或属性不存在；`null` 是显式空值。优先用严格比较 `===`，避免 `==` 的隐式转换。

```javascript
console.log(0 === '0'); // false
const index = 0;
console.log(index || 1); // 1
console.log(index ?? 1); // 0
```

`??` 仅在 null 或 undefined 时取默认值。`?.` 是可选链：`response.user?.name` 在 user 缺失时返回 undefined，而不是报错。它能处理“可选字段”，不能替代必须字段的验证。

## 6.4 对象、数组和解构

```javascript
const message = { id: 'm1', role: 'user', content: '自由是什么？' };
const { role, content } = message;
const updated = { ...message, content: '责任是什么？' };
const messages = [message];
const next = [...messages, updated];
console.log(role, content, messages.length, next.length);
```

展开语法是浅复制，与 Python 外层复制一样，内部对象仍可能共享。React 中更新状态通常要生成新的对象引用，但不代表每次都需要深拷贝整个数据库。

数组的 `map` 产生映射结果，`filter` 产生筛选结果，`find` 返回第一个匹配元素或 undefined。熟悉 Java Stream 可以帮助理解用途，但它们的执行机制并不完全一样。

```javascript
const books = [{ id: 1, readable: true }, { id: 2, readable: false }];
const ids = books.filter(book => book.readable).map(book => book.id);
console.log(ids); // [1]
```

## 6.5 函数、闭包与 this

函数可以当作值传递。闭包捕获外层变量：

```javascript
function makeCounter() {
  let count = 0;
  return () => ++count;
}
const next = makeCounter();
console.log(next(), next()); // 1 2
```

箭头函数没有自己的 this；普通函数的 this 与调用方式有关。前端初学时可以先使用模块函数和箭头回调，等需要面向对象 API 时再系统学习原型和 this 绑定。不要把 Java 成员方法的规则直接套到回调上。

## 6.6 模块边界

`export function search(){}` 声明具名导出，另一个文件用 `import { search } from './search.mjs'`。默认导出用 `export default`，导入时不带花括号。混用最常导致“模块没有这个导出”的错误。

浏览器原生模块通常要提供能访问到的明确路径；Vite 可以帮助解析包和构建资源，但它没有改变 JS 本身的变量和异步语义。

## 6.7 练习

把 Python 去重函数翻译成 JS。再写 `appendToken(messages, id, chunk)`：返回新数组，只更新指定 id 的消息，不修改原数组。

先用 console.log 观察对象是否共享，再用 Node assert 断言旧消息没有变化。验收：你能解释 const 不等于不可变、展开不是深拷贝、null 和 undefined 的区别。参考：[MDN JavaScript 学习区](https://developer.mozilla.org/zh-CN/docs/Learn_web_development/Core/Scripting)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](05-sql-and-conversations.md) · [下一章](07-html-and-css.md)
