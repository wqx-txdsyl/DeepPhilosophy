# Add Book

## 核心执行协议
- **模式**：顺序执行，每步带检查-补全-验证闭环。
- **变量替换规则**：ARG_PATH/ARG_TITLE/ARG_AUTHOR
- **标记格式**：[SKIPPED:reason] / [WARN:reason]

## 前置依赖
- scripts/add_book.py（优先）；若不存在则内联 DeepSeek（步骤 2 路径 B）
- DeepSeek API Key, scripts/_lib.py

## 状态初始化
> TodoWrite: 步骤1前置检查 步骤2AI生成(A/B路径) 步骤3摘要循环校验 步骤4写入验证

## 原子步骤

### 步骤 1：前置检查
- **动作**：test -f scripts/add_book.py && echo PATH_A || echo PATH_B

### 步骤 2：AI 生成
- **路径 A**：cd scripts && python add_book.py ARG_PATH
- **路径 B（内联 DeepSeek）**：


### 步骤 3：摘要循环校验（>=300字）
- **补全分支**：len<300 -> DeepSeek 扩充 2 次 -> [WARN:SHORT_SUMMARY]

### 步骤 4：写入验证
- **动作**：python -c "import json; d=json.load(open("backend/data/book_summaries.json")); k="ARG_TITLE||ARG_AUTHOR"; assert len(d[k].get("tags",[]))>=2; assert len(d[k].get("summary",""))>=300; print("OK")"

## 执行报告
- 成功项/补全项/失败跳过项
- 路径：PATH_A 或 PATH_B