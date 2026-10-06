# 第一课：不改生产系统，亲手增加一个工具

这是一堂可以直接跟做的实践课。目标：理解工具注册、模型可见定义和程序执行的区别。工作目录是课程 `examples/phiagent-lab/`。

## 第一步：先预测

我们要增加 list_passages，返回所有教学材料的 id 和 title，不读取全文。你先写下：这个工具需要哪些参数？返回什么？结果能不能算作已经读过全文？

参考答案：不需要参数；返回材料目录；目录不是全文证据，因此不能加入 evidence。

## 第二步：写输入模型

在课程 `phiagent_lab/library.py` 的参数模型区域加入：

```python
class ListArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

空模型并不是不验证，它会拒绝多余字段。这样模型不能悄悄传入 path 或 user_id 等工具未定义的参数。

## 第三步：写函数并注册

在 REGISTRY 定义之前加入：

```python
def list_passages():
    return [{"id": item["id"], "title": item["title"]}
            for item in PASSAGES.values()]
```

然后在 REGISTRY 字典里增加一项：

```python
"list_passages": (ListArgs, list_passages, "列出教学材料目录，不返回正文。"),
```

这里是局部编辑，不要把整个现有字典替换成只有这一项。

## 第四步：直接验证执行

在课程项目根目录执行：

```bash
python -c 'from phiagent_lab.library import execute_tool; print(execute_tool("list_passages", {}))'
```

预期得到三条记录，每条只有 id 与 title。再传 `{"path":"secret"}`，应该校验失败。注意：这是你直接调用执行器，不代表模型已经选择了新工具。

## 第五步：验证工具定义

```bash
python -c 'from phiagent_lab.library import tool_specs; print([x["function"]["name"] for x in tool_specs()])'
```

预期列表里有 list_passages。你现在完成了“把能力暴露给模型”的步骤。

## 第六步：添加测试

在 `tests/test_project.py` 中加入：

```python
def test_list_passages_contract():
    result = execute_tool("list_passages", {})
    assert len(result) == 3
    assert all(set(item) == {"id", "title"} for item in result)
    with pytest.raises(ValueError):
        execute_tool("list_passages", {"path": "secret"})
```

现有文件已导入 pytest 和 execute_tool。运行 `python -m pytest -q`。故意把函数返回改成包含正文，测试应失败，证明测试在保护目录契约。

## 第七步：让模型真正调用

离线 MockModel 是固定脚本，不会自动理解新增工具。为了验证链路，你可以写一个专门测试替身：第一次决定调用 list_passages，收到结果后结束。这证明系统能处理新工具。

真实模型模式则根据工具描述和用户问题自主选择。用“列出你能查询的教学材料”作为测试问题，检查实际 tool_calls。如果没有调用，不能伪造日志，应分析描述、提示词与模型能力。

## 第八步：解释与迁移

请用自己的话回答：

1. 为什么登记了工具，不等于工具已经执行？
2. 为什么目录不该进入全文证据集合？
3. 为什么不让模型自由传文件路径？
4. 如果未来目录来自数据库，应该改函数、执行器还是整个引擎？

你能独立答出并完成测试，就已经开始以可迁移的方式开发 Agent。下一课再把这个目录显示为前端卡片，并处理空结果和错误状态。
