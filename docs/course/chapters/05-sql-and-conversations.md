# 第 05 章：数据库、事务与对话记忆

## 5.1 三个不同问题

聊天记录回答“用户和系统说过什么”；模型上下文回答“这一轮把什么发送给模型”；长期记忆回答“哪些经过选择的信息应影响未来会话”。它们可以相互关联，但不能当成同一张无限增长的消息表。

实验数据库保存成功完成的 user/assistant 成对消息；送给模型时只取最近 12 条。这是便于学习的截断策略，不具备完整摘要、token 预算或长期记忆能力。

## 5.2 看懂 SQLite

SQLite 是进程内数据库，不需要独立数据库服务器。SQL 的核心概念可以迁移到 PostgreSQL 等系统，但并发、类型与部署语义仍需重新验证。

```sql
CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  conversation TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL
);
CREATE INDEX by_conversation ON messages(conversation, id);
```

索引让“按会话查最新消息”更有效。它需要存储空间并增加写入开销，不是每个字段都应该加索引。

## 5.3 参数化查询

Python 局部片段：

```python
rows = db.execute(
    "SELECT role, content FROM messages WHERE conversation=? ORDER BY id DESC LIMIT ?",
    (conversation_id, 12),
).fetchall()
```

不要用字符串拼接把用户输入塞进 SQL。占位符负责将数据作为值处理；它不是 SQL 语法的一部分。表名等结构性内容不能用相同方式随意参数化，需要白名单。

## 5.4 原子性：一轮对话一起保存

如果先保存用户消息，再保存回答时崩溃，历史中会留下未配对消息。实验把两条插入放进一个事务：成功一起提交，失败一起回滚。

生产系统也可以在开始时保存用户消息，但需要显式状态：pending、streaming、completed、failed、cancelled。那是更完整的产品设计，不能仅靠“消息列表里最后一条是谁”推断。

## 5.5 ID 设计

至少区分 user_id、conversation_id、message_id、invocation_id。用户拥有会话，会话包含消息，单条生成可能重试多次，每次执行有自己的 invocation。幂等键要说明作用域，例如 `(user_id, client_request_id)` 唯一。

客户端重试一次 POST 不应意外生成两次付费请求。生产接口先检查请求 id 是否已有成功结果，再决定复用、返回处理中或启动新执行。

## 5.6 并发与隔离

实验用进程内 active 集合限制同一会话同时生成两次。它只适合单进程课程服务；启动多个 worker 后，每个进程有自己的集合，这个保护就失效。完整复刻应在数据库中建立运行租约或使用具有原子操作的共享存储。

多用户查询应带用户条件：

```sql
SELECT id FROM conversations WHERE id = ? AND user_id = ?;
```

即使 UUID 难猜，也不是授权机制。第 20 章会继续构建认证和归属检查。

## 5.7 练习

1. 重启服务，证明历史仍存在。
2. 模拟保存第二条消息失败，证明事务没有只留下第一条。
3. 两个不同会话使用同样的问题，证明读取结果相互隔离。
4. 为消息增加 created_at；为数据库迁移增加版本记录，而不是每次删表重建。

验收：能说清哪些状态存在内存、哪些在磁盘、哪些只在浏览器里，以及进程重启后各自会怎样。参考：[Python sqlite3](https://docs.python.org/zh-cn/3/library/sqlite3.html)。

<!-- NAV -->

[课程目录](../README.md) · [上一章](04-http-and-fastapi.md) · [下一章](06-javascript-migration.md)
