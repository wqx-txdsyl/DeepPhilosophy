# 第 26 章：Python 进阶补课——类、装饰器、协议和上下文管理器

本章建议在第 02 章后学习；先走主线时也可以在完成实验项目后回来。目标是让你能读懂真实后端中大量“基础语法之外”的代码。

## 26.1 Python 的类与 Java 的差异

```python
from dataclasses import dataclass, field

@dataclass
class Conversation:
    id: str
    messages: list[dict] = field(default_factory=list)

    def append(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

first = Conversation("a")
second = Conversation("b")
first.append("user", "自由")
assert second.messages == []
```

self 是显式接收实例的参数。dataclass 生成初始化和比较等常见方法，但不是输入验证框架。default_factory 每个实例创建一个列表，避免共享默认容器。

Python 没有以 Java 同样方式执行的 private 访问修饰符。下划线是约定，双下划线涉及名称改写，不能拿它当安全边界。权限必须在实际访问路径上检查。

## 26.2 Duck typing 与 Protocol

你不一定需要让所有模型继承一个巨大基类，只要它们满足所需接口即可。Protocol 可以把这个约定写给类型检查器。

```python
from typing import Protocol, AsyncIterator

class Model(Protocol):
    async def decide(self, messages: list[dict], tools: list[dict]) -> dict: ...
    def stream(self, messages: list[dict]) -> AsyncIterator[str]: ...
```

这里 stream 的协议声明使用普通 def 返回异步迭代器，因为调用异步生成器函数得到的正是异步迭代器，而不是需要先 await 才得到的结果。实现中 `async def` 搭配 yield 产生该对象。

Protocol 帮助静态检查，不会自动验证来自网络的 JSON。内部接口约束与外部数据验证要同时存在。

## 26.3 装饰器其实是函数变换

```python
from functools import wraps
import time


def timed(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            print(function.__name__, time.perf_counter() - start)
    return wrapper

@timed
def add(a, b):
    return a + b

print(add(2, 3))
```

`@timed` 大致等价于 `add = timed(add)`。wraps 保留函数名和一些元数据。FastAPI 的路由装饰器与工具注册装饰器，也可以从“接收函数并注册或包装”的角度理解。

这个 timed 只适用于同步函数；直接包 async 函数只会测到创建协程的时间。异步装饰器需要 async wrapper 并 await 被包装调用。这是很好的迁移练习。

## 26.4 上下文管理器保证清理

```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    print("获取资源")
    try:
        yield "resource"
    finally:
        print("释放资源")

with managed_resource() as value:
    print(value)
```

with 会在离开代码块时执行清理，即使中间抛异常。异步资源使用 asynccontextmanager 与 async with。课程 app 的 lifespan 正是管理应用级资源的边界。

## 26.5 泛型、TypedDict 与运行时验证

TypedDict 描述字典字段，普通 dict 仍然是实际运行对象。dataclass 表达内部数据实体，Pydantic 处理校验与序列化，Protocol 描述对象接口。它们不是相互替代品。

选择标准：数据从不可信外部进入时做 Pydantic 校验；内部稳定记录可以 dataclass；已有字典协议可用 TypedDict；可替换服务用 Protocol。不要为了类型“看起来高级”引入三层无用包装。

## 26.6 包、入口与依赖管理

把代码放进包，通过 `python -m package.module` 执行，保证导入路径清楚。直接运行深层文件可能导致相对导入失败。长期维护项目可引入 pyproject.toml、可编辑安装、格式化与静态检查；先让这些工具服务于可读和可靠，而非制造复杂仪式。

依赖分直接依赖与传递依赖。固定直接版本不等于完全锁定环境，课程额外保存独立环境的 requirements.lock。安装 lock 后仍要运行测试，因为系统、Python 小版本和底层库可能变化。

## 26.7 作业

实现 async_timed 装饰器；给 Model 加 Protocol 类型；把 ResearchBudget 改为冻结配置加可变运行状态两个对象。写测试证明两个请求不会共享计数器。

最终答辩：为什么让引擎依赖一个 Model 协议，比在每个节点直接构造供应商 SDK 更容易测试和迁移？

<!-- NAV -->

[课程目录](../README.md) · [上一章](25-official-sources.md) · [下一章](27-javascript-typescript.md)
