# 第 04 章：从 Java Controller 到 FastAPI 后端

## 4.1 先把 HTTP 看成一个函数边界

请求包括方法、路径、请求头和请求体；响应包括状态码、响应头和响应体。浏览器与服务端不能直接共享内存，数据必须序列化。

`GET /api/passages/demo-freedom` 表示读取；`POST /api/chat` 表示提交一次处理请求。GET 参数通常在路径或查询字符串，POST 的结构化输入常用 JSON。GET 不适合触发有副作用的写入。

常见状态码：200 成功、400 请求格式或业务输入错误、401 未认证、403 无权限、404 不存在、409 状态冲突、422 输入校验失败、429 限流、500 服务内部错误。FastAPI 对请求模型校验失败通常返回 422。

## 4.2 写第一个独立接口

完整脚本，保存为项目根目录的 `hello_api.py`：

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class Question(BaseModel):
    text: str = Field(min_length=1, max_length=200)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/echo")
def echo(body: Question):
    return {"received": body.text, "length": len(body.text)}
```

运行 `python -m uvicorn hello_api:app --port 8022`。`hello_api:app` 是“模块名:对象名”，不是文件路径。

```bash
curl -X POST http://127.0.0.1:8022/echo -H 'Content-Type: application/json' -d '{"text":"自由是什么"}'
```

发送空字符串，观察 422 的 JSON 错误。然后把 JSON 的 `text` 改成不存在的字段，观察必填校验。你现在已经有一个可验证的 DTO 边界。

## 4.3 路径参数、查询参数与请求体

```python
@app.get("/books/{book_id}")
def get_book(book_id: str, include_toc: bool = False):
    return {"book_id": book_id, "include_toc": include_toc}
```

访问 `/books/abc?include_toc=true`。你会发现类型来自函数签名。Pydantic 还允许自动类型转换；对于工具执行等严格边界，项目使用 `strict=True`，故意拒绝字符串形式的数字。

不要把“是合法字符串”误认为“有权读取这个资源”。UUID 校验只检查形式；真实多用户系统还必须检查归属。

## 4.4 依赖注入与生命周期

你在 Java 中可能习惯容器注入数据库连接。FastAPI 的 `Depends` 用于复用身份验证、连接获取等逻辑。应用启动时初始化资源、关闭时清理资源，可以使用 lifespan。

实验 `create_app(model=None, db_path=None)` 允许测试传入替身模型和临时数据库。这样同一套接口可以连接真实服务，也可以在离线测试中运行。这比在测试里修改全局变量更可控。

## 4.5 前后端同源与 CORS

协议、主机、端口共同定义 origin。`localhost:5173` 和 `localhost:8021` 不同源。浏览器会实施跨源访问规则；命令行 curl 不受相同限制。

实验原生页面与 API 同由 8021 提供，避免一开始被 CORS 干扰。React 开发使用 Vite proxy 把 `/api` 转发到 Python。生产中明确配置允许来源和凭证策略，不能把开放 CORS 当作身份认证。

## 4.6 阅读课程路由

打开 `phiagent_lab/app.py`，按顺序找到：ChatRequest、create_app、lifespan、health、history、passage、chat、静态文件挂载。解释为什么 `/` 静态挂载放在 API 路由之后；路由匹配顺序可能让过早挂载吞掉后续请求。

## 4.7 练习

增加 `/api/search?q=自由`，调用已有检索函数，空白查询应返回明确错误。不要在路由里重写搜索算法。

写四个测试：合法查询、空白查询、未知材料、过长输入。HTTP 测试使用 TestClient，它不要求启动真实端口。参考：[FastAPI 用户指南](https://fastapi.tiangolo.com/zh/tutorial/)、[测试指南](https://fastapi.tiangolo.com/tutorial/testing/)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](03-async-and-lifecycle.md) · [下一章](05-sql-and-conversations.md)
