---
name: add-book
description: Add Book
---
# Add Book

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_PATH` = 书籍路径；`ARG_TITLE` = 书名；`ARG_AUTHOR` = 作者
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- `scripts/add_book.py`（优先）；若不存在则内联 DeepSeek（步骤 2 路径 B）
- DeepSeek API Key、`scripts/_lib.py`

## 状态初始化
> TodoWrite: 步骤1前置检查 步骤2AI生成(A/B) 步骤3摘要循环校验 步骤4写入验证

## 原子步骤

### 步骤 1：前置检查（add_book.py 是否存在）
- **动作**：`test -f scripts/add_book.py && echo "PATH_A" || echo "PATH_B"`
- **门禁验证（Check）**：记录路径选择。

### 步骤 2：AI 生成标签+摘要
- **路径 A（add_book.py 存在）**：`cd scripts && python add_book.py "ARG_PATH"`
- **路径 B（add_book.py 不存在，内联 DeepSeek）**：
```bash
cd scripts && python -c "
import os, sys, re, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd(), '..'))
from _lib import get_deepseek_key, load_json, save_json, ROOT
from openai import OpenAI

client = OpenAI(api_key=get_deepseek_key(), base_url='https://api.deepseek.com')
path = 'ARG_PATH'
title = os.path.splitext(os.path.basename(path))[0]
author = os.path.basename(os.path.dirname(path)).replace('###合集&概述###', '合集&概述')

resp = client.chat.completions.create(
    model='deepseek-chat',
    messages=[{'role': 'user', 'content': f'为《{title}》（{author}著）生成2-5个哲学流派标签和>=300字中文摘要。返回JSON: {{\"tags\": [\"标签1\", \"标签2\"], \"summary\": \"摘要...\"}}'}],
    temperature=0.3, max_tokens=1000
)

text = resp.choices[0].message.content
data = json.loads(re.search(r'\{[\s\S]*\}', text).group(0))
key = f'{title}||{author}'

SUMMARIES_FILE = os.path.join(ROOT, 'backend', 'data', 'book_summaries.json')
summaries = load_json(SUMMARIES_FILE)
summaries[key] = data
save_json(SUMMARIES_FILE, summaries)
print(f'INLINE OK: {len(data[\"tags\"])} tags, {len(data[\"summary\"])} chars')
"
```
- **门禁验证（Check）**：`python -c "import json; d=json.load(open('backend/data/book_summaries.json')); k='ARG_TITLE||ARG_AUTHOR'; assert k in d; print('SAVED')"`

### 步骤 3：摘要循环校验（>=300字）
- **补全分支（Remediate）**：若 `len(summary) < 300`，DeepSeek 扩充（参考 add-author.md 步骤 2 补全分支结构），最多 2 次：
```bash
cd scripts && python -c "
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd(), '..'))
from _lib import get_deepseek_key, load_json, save_json, ROOT
from openai import OpenAI

client = OpenAI(api_key=get_deepseek_key(), base_url='https://api.deepseek.com')
SUMMARIES_FILE = os.path.join(ROOT, 'backend', 'data', 'book_summaries.json')
s = load_json(SUMMARIES_FILE)
key = 'ARG_TITLE||ARG_AUTHOR'

for i in range(2):
    if len(s[key].get('summary', '')) >= 300:
        break
    r = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': f'扩充书籍摘要至>=300字。当前仅{len(s[key].get(\"summary\", \"\"))}字：{s[key][\"summary\"]}'}],
        temperature=0.7, max_tokens=1000
    )
    s[key]['summary'] = r.choices[0].message.content
    save_json(SUMMARIES_FILE, s)

print(f'FINAL: {len(s[key][\"summary\"])} chars')
"
```
- **失败上限**：2 次后 -> `[WARN:SHORT_SUMMARY]`

### 步骤 4：写入验证
- **动作**：`python -c "import json; d=json.load(open('backend/data/book_summaries.json')); k='ARG_TITLE||ARG_AUTHOR'; e=d[k]; assert len(e.get('tags',[]))>=2; assert len(e.get('summary',''))>=300; print('SAVED OK')"`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z（格式 `[SKIPPED:reason]`）
- 路径：PATH_A(add_book.py) 或 PATH_B(inline DeepSeek)
