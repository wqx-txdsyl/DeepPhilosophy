# 第 08 章：Promise、fetch 和不会丢字的流式聊天

## 8.1 事件循环如何影响你的代码

Promise 表示未来可能成功或失败的结果。async 函数总是返回 Promise；await 暂停当前 async 函数的后续执行，而不是锁住浏览器所有工作。

```javascript
console.log('A');
Promise.resolve().then(() => console.log('B'));
console.log('C');
```

输出 A、C、B。回调进入微任务队列，要等当前同步代码执行完。循环中反复同步修改页面，不等于浏览器会每次立即绘制。

## 8.2 fetch 不会因为所有 HTTP 错误都自动 reject

```javascript
async function health() {
  const response = await fetch('/api/health');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await response.json();
}
```

网络失败通常会 reject，但 404、422、500 等 HTTP 响应仍需检查 response.ok。另一个常见错误是忘记 await response.json()，把 Promise 当成数据对象。

## 8.3 SSE 的帧边界

实验协议每个事件写成：

```text
data: {"type":"token","text":"自由"}

data: {"type":"done","text":"完整回答"}

```

空行终止一帧。TCP、HTTP 或浏览器读取到的 chunk 都不保证恰好是一帧。一次 read 可能只有半个 JSON，也可能包含多个事件，UTF-8 的一个汉字还可能跨字节块。

所以解析分两层：TextDecoder 负责跨字节块解码；字符串缓冲区负责按空行分帧；最后才对完整 data 内容 JSON.parse。课程 `web/sse.mjs` 是完整实现，请逐行阅读。

`TextDecoder.decode(value, {stream:true})` 暂存不完整字符，结束时再 decode() 刷出剩余状态。每次 read 都创建新解码器可能丢字。支持 CRLF 也很重要，不能只依赖一种换行方式。

## 8.4 为什么采用 fetch 而不是 EventSource

浏览器 EventSource 很适合标准 GET 事件订阅。聊天接口需要 POST 请求体和可控请求头，课程使用 fetch 的响应流。自动重连并不是所有聊天请求都能直接使用：重发 POST 可能重复付费生成，需要幂等设计。

SSE 是单向服务端推送，客户端仍可通过普通 HTTP 发请求。实时双向协作或语音可以考虑 WebSocket，但普通文字聊天不必先引入它。

## 8.5 事件是一个产品协议

课程事件包含 start、status、tool、source、token、done、error。token 是暂时显示的文字；done 表示回答经过课程的基础校验并且已保存。连接正常 EOF 不等于业务成功，因为断线时也可能看见流结束。

当服务端已经发送 200 和部分流之后，发生错误不能再把 HTTP 状态改为 500，应发送 error 事件。UI 收到 error 必须标记本轮失败，不能把半截内容当作成功历史。

## 8.6 取消与竞态

```javascript
const controller = new AbortController();
fetch('/api/chat', { method: 'POST', signal: controller.signal });
controller.abort();
```

这是局部演示，真实请求还需要 JSON 请求体。`abort()` 中断客户端等待，服务端也应传播取消；但服务端可能已在取消前提交结果。产品需要刷新核对，或者查询 invocation 状态。

完整工作区不能只用一个“当前回答字符串”。必须把事件绑定到发起时的 conversation_id、message_id 和 invocation_id。用户切到 B 会话后，A 的迟到 token 仍只能写入 A。

## 8.7 练习与验收

运行 `node --test tests/sse.test.mjs`。这个测试把中文事件逐字节拆开，验证不会乱码。再添加随机分块、多 data 行、空心跳和中途 EOF 测试。

手动模拟：开始生成 → 切换会话 → 删除原会话 → 旧请求返回。写出每个状态应如何处理。第 09 章把这个过程迁移到 React。

参考：[MDN 可读流](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](07-html-and-css.md) · [下一章](09-react-workspace.md)
