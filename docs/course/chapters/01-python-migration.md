# 第 01 章：从 C++ / Java 迁移到 Python

## 本章完成后

你能准确预测列表、字典、参数和返回值的变化，不再靠不断运行来猜引用语义；能写清楚一个带验证的检索函数。

## 1.1 名字绑定对象

Python 的变量名绑定对象；赋值通常不会复制对象。你可以用 Java 对象引用帮助理解，但 Python 中整数、函数、类本身也是对象。

完整脚本，可保存为 `exercises/bindings.py`：

```python
original = [{"title": "自由"}]
alias = original
shallow = original.copy()
alias.append({"title": "知识"})
shallow[0]["title"] = "自由与责任"
print(len(original))       # 2
print(len(shallow))        # 1
print(original[0]["title"])  # 自由与责任
```

`copy()` 只复制外层列表，内部字典仍共享。Agent 状态、对话历史和缓存最容易在这里发生串改。需要隔离时优先明确创建新的数据结构；深拷贝适合一些场景，但对网络客户端、锁等对象并不适用。

## 1.2 常用容器的选择

| Python | 可以借用的旧知识 | 常见用途 |
|---|---|---|
| `list` | Java ArrayList、C++ vector | 有序消息历史 |
| `dict` | Map / unordered_map | 工具注册表、按 id 查资料 |
| `set` | Set | 去重后的来源 id |
| `tuple` | 固定位置的组合值 | 返回两项结果、可哈希键的一部分 |
| `dataclass` | 简化的数据对象 | 内部配置和领域数据 |
| Pydantic Model | 带校验的 DTO | 网络输入、工具参数 |

`dict` 保留插入顺序，但你仍不应把“第几个字段”当业务身份。书籍、消息和证据都应该有明确 id。

## 1.3 真值、缺失与默认值

`None`、`False`、数字零、空字符串和空容器在条件判断中都是假。`value or default` 会把它们全部替换。如果 `0` 是合法章节编号，这可能造成错误。

```python
chapter_index = 0
bad = chapter_index or 1
correct = 1 if chapter_index is None else chapter_index
print(bad, correct)  # 1 0
```

区别还包括：字典没有这个键、键值为 `None`、键值为空字符串。这三种情况在协议中可能意味着不同事情，不要在清洗时随便合并。

## 1.4 函数与类型注解

```python
def search_titles(query: str, titles: list[str], limit: int = 3) -> list[str]:
    if not query.strip():
        raise ValueError("查询不能为空")
    if limit < 1:
        raise ValueError("limit 必须大于零")
    matches = [title for title in titles if query.casefold() in title.casefold()]
    return matches[:limit]

print(search_titles("自由", ["论自由", "知识论", "自由与责任"]))
```

注解不会自动阻止你传入错误类型。静态检查器能提前发现一些错误，Pydantic 可在运行时验证输入，函数本身也可以主动检查。把类型注解当成“自动生效的 Java 类型系统”会漏掉网络边界问题。

## 1.5 可变默认参数

错误示例：

```python
def remember(item, history=[]):
    history.append(item)
    return history
```

默认列表在函数定义时创建，后续调用共享它。改为：

```python
def remember(item, history=None):
    if history is None:
        history = []
    history.append(item)
    return history
```

同样要注意类属性：把用户历史放在类级列表里，会让实例共享数据。Agent 服务中的“上一位用户说了什么”不能依赖这种共享对象。

## 1.6 推导式、生成器与可读性

`[f(x) for x in values]` 立即构造列表；`(f(x) for x in values)` 产生迭代器，按需计算。大书库扫描适合迭代，网络输出适合生成器。不要为了“Pythonic”把三层条件塞进一行；调试边界代码时，清楚的循环通常更好。

```python
def chunks(text: str, size: int):
    if size <= 0:
        raise ValueError("size 必须为正数")
    for start in range(0, len(text), size):
        yield text[start:start + size]

print(list(chunks("自由与责任", 2)))
```

这里按字符切分，不是按模型 token 切分；后面做 RAG 时还要维护原文位置。

## 1.7 练习

A. 写 `unique_books(records)`：按 id 去重，保留第一次出现顺序。

B. 写 `top_k(scores, k)`：分数降序，同分按 id 排序；拒绝负数 k。

C. 解释 `is` 与 `==`：前者比较是否为同一对象，后者比较值。不要用 `is` 判断用户字符串是否等于 `"general"`。

D. 给 A 写三个测试：重复 id、空列表、同 id 不同标题。你要先明确冲突策略，再写代码。

验收：可以用一句话解释每一次复制、每一次原地修改和每一个默认值。基础参考：[Python 数据结构](https://docs.python.org/zh-cn/3/tutorial/datastructures.html)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](00-learning-map-and-environment.md) · [下一章](02-python-engineering.md)
