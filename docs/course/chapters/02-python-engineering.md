# 第 02 章：把 Python 脚本写成可维护程序

## 2.1 模块如何替代“大文件”

Python 文件是模块，带 `__init__.py` 的目录可以作为常规包。`import` 会执行模块顶层代码，然后缓存模块对象。于是“导入一个模块就发网络请求、启动线程、读巨大数据库”会让测试难以控制。

实验项目分层：

```text
phiagent_lab/
  library.py   数据与工具，尽量独立于网络
  model.py     外部模型适配器
  engine.py    状态与流程
  store.py     持久化
  app.py       HTTP 边界
  cli.py       终端入口
```

你可以把这些理解为 Java 的 package 分层。区别是 Python 不要求一个类一个文件，也不需要为了命名空间把所有函数包进工具类。

## 2.2 使用 pathlib 和明确的数据根目录

当前工作目录会随着启动位置改变，`open("data.json")` 很容易读取错地方。

```python
from pathlib import Path
HERE = Path(__file__).resolve().parent
file_path = HERE / "example.json"
```

若在现有 DeepPhilosophy 工具里开发，应遵守该仓库既有路径规范；课程的独立包使用自己的项目根目录。不要为了统一风格而移动生产数据。

`Path.resolve()` 解决规范路径，但它不会自动完成授权。用户给出的 `../../secret` 即使被解析为绝对路径，仍可能指向不该读的文件。安全方式是按已知 id 在注册表查询，而非把用户字符串直接拼成文件路径。

## 2.3 JSON 是边界，不是 Python 对象的镜像

JSON 支持对象、数组、字符串、数字、布尔、null，不支持 Python 集合、函数或数据库连接。`json.dumps` 把 Python 数据转成文本，`json.loads` 反过来。

```python
import json
payload = {"title": "论自由", "readable": True, "year": None}
text = json.dumps(payload, ensure_ascii=False)
again = json.loads(text)
assert again == payload
```

`ensure_ascii=False` 保留可读中文，不改变数据语义。网络传输仍应使用 UTF-8。遇到字符串中有引号、换行时，让 JSON 库转义，不要手工拼接 JSON。

## 2.4 异常应该在哪一层处理

工具层发现材料不存在，可以抛 `ValueError`；HTTP 层把它变成 404；Agent 工具层则可以把它变成 `{"error":"材料不存在"}` 交回模型。相同底层错误，在不同调用场景需要不同响应。

```python
def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

try:
    print(divide(1, 0))
except ValueError as exc:
    print("输入问题：", exc)
```

不要到处 `except Exception: pass`。那会把数据库损坏、程序缺陷和用户错误全部变成“没有结果”。最外层可以捕获未处理异常并生成请求编号，详细内部原因保留在受控日志中。

## 2.5 调试的顺序

先复现，再缩小输入，再检查边界值，最后改代码。`print(type(value), repr(value))` 比只打印值更容易发现“字符串 3”和“整数 3”的区别。`breakpoint()` 可启动交互调试：`n` 单步、`s` 进入函数、`p variable` 看值、`c` 继续。

日志应记录事件、时长、请求编号、错误类型。避免把密钥、整本书、完整私人会话直接打印出来。教学项目错误响应给请求编号，方便把浏览器和服务端对应起来。

## 2.6 测试为什么必须与依赖分开

如果检索测试必须调用付费 API，那么网络抖动就会冒充代码错误。实验中的 `MockModel` 用相同接口替换真实模型，你可以单独证明工具调用协议是否正确。真实模型质量需要另外的评测集，不能用这个替身证明。

运行课程测试：

```bash
python -m pytest -q
```

你应能分清：语法错误、导入错误、断言失败、外部服务错误。这四类问题的修复位置不同。

## 2.7 练习

把第 01 章的去重函数移入 `exercises/book_utils.py`，另一个文件导入它。故意制造循环导入，再画依赖图，找出应该移动到公共模块的数据结构。

给 `read_passage` 写失败测试：未知 id 必须失败，不能悄悄返回第一条材料。验收时只看测试能否抓住你故意加入的错误，不能只看“测试全部绿色”。

<!-- NAV -->

[课程目录](../README.md) · [上一章](01-python-migration.md) · [下一章](03-async-and-lifecycle.md)
