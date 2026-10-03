# 第 03 章：async / await，真正理解服务为什么会卡住

## 3.1 async 不等于新线程

同步函数调用会等待结果。`async def` 定义协程函数，调用后获得协程对象，需要 `await` 或调度任务才会执行。事件循环在等待网络、计时等可挂起操作时运行其他任务。

你可以把 Java Future 当作部分参照，但 Python 的协程不会因为加了 `async` 就让 CPU 密集计算自动并行。把十万页 PDF 解析塞进协程里，仍然可能阻塞整个事件循环。

完整脚本：

```python
import asyncio
import time

async def read_source(name, delay):
    await asyncio.sleep(delay)
    return name

async def main():
    start = time.perf_counter()
    values = await asyncio.gather(read_source("A", 0.2), read_source("B", 0.2))
    print(values, round(time.perf_counter() - start, 1))

asyncio.run(main())
```

耗时大约 0.2 秒加调度开销，不是 0.4 秒。把 `await asyncio.sleep` 改成 `time.sleep`，观察为何两项串行阻塞。

## 3.2 能并行与不能并行

同时搜索两位哲学家的资料，可以并行；先搜索书籍再读取搜索得到的章节，是依赖关系，不能先发出未知章节请求。为并行而并行只会制造错误。

大量独立请求要限制并发：

```python
sem = asyncio.Semaphore(3)

async def bounded_fetch(client, url):
    async with sem:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
```

这是局部片段，需要传入 `httpx.AsyncClient`。Semaphore 限制同一进程内同时进入代码段的任务数；不是账户配额，也不是跨机器的全局限制。

## 3.3 超时与取消

```python
async def run_with_deadline(operation):
    async with asyncio.timeout(10):
        return await operation()
```

超时后应释放连接和锁。`finally` 用于无论成功失败都执行的清理，`async with` 用于异步资源生命周期。用户点击停止，前端 AbortController 中断请求，服务端要允许取消传播到模型调用。

不要捕获取消后继续生成。实验项目明确重新抛出 `asyncio.CancelledError`。生产系统中，还要考虑代理断连检测延迟，以及外部供应商是否真正停止计费。

## 3.4 阻塞库怎么办

SQLite 标准接口、某些文件读取和旧 HTTP 库是同步的。短操作可以放进 `asyncio.to_thread` 避免阻塞事件循环；大量 CPU 工作则考虑进程或专门任务队列。

注意：取消 `to_thread` 的等待，不保证正在执行的线程立即停止。数据库写入可能在客户端断开后完成。因此“用户点停止”与“数据库一定未写入”不是完全等价的承诺。实验前端提示刷新核对保存状态；生产系统需要服务端任务状态和幂等请求 id。

## 3.5 两种生成器

普通生成器 `yield` 一项后暂停。异步生成器在此基础上允许等待：

```python
async def count_events():
    for i in range(3):
        await asyncio.sleep(0.1)
        yield {"index": i}
```

消费它要用 `async for`。FastAPI 的 StreamingResponse 可以逐步消费生成器，LangGraph 也可以逐步发出状态事件。这就是“边做边显示”的基础。

## 3.6 练习与验收

1. 写两个模拟来源，一个 0.1 秒成功，一个 0.3 秒失败；比较 gather 默认行为和 `return_exceptions=True`。
2. 用 `TaskGroup` 重写，解释一个子任务失败后其他任务如何取消。
3. 设计“最多同时运行 2 个检索”的实验，打印当前活动数量，断言它从未超过 2。
4. 在等待期间取消任务，证明 finally 执行了。

你应能解释：为什么网络服务适合异步、为什么 OCR 不会因 async 自动加速、为什么取消不等于事务回滚。参考：[Python asyncio](https://docs.python.org/zh-cn/3/library/asyncio.html)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](02-python-engineering.md) · [下一章](04-http-and-fastapi.md)
