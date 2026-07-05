# Add Book

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败才报错并**回滚/标记**（而非直接退出）。

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：路径解析 — 验证文件存在
- [ ] 步骤 2：AI 生成 — 标签 + 摘要
- [ ] 步骤 3：摘要循环校验 — len >= 300
- [ ] 步骤 4：写入验证 — book_summaries.json

## 原子步骤

### 步骤 1：路径解析
- **动作**：
```bash
python -c "import os,sys; p=sys.argv[1]; assert os.path.exists(p); print(f'OK: {os.path.getsize(p)} bytes')" "ARG_PATH"
```
- **门禁验证（Check）**：输出 `OK: N bytes`。
- **补全分支（Remediate）**：文件不存在 → 检查路径拼写，最多 2 次。失败则标记 `SKIP`。

### 步骤 2：AI 生成标签+摘要
- **动作**：
```bash
cd scripts && python add_book.py "ARG_PATH"
```
- **门禁验证（Check）**：
```bash
python -c "import json; c=json.load(open('backend/data/book_summaries.json')); k='TITLE||AUTHOR'; assert k in c; e=c[k]; print(f'TAGS:{len(e.get(\"tags\",[]))} SUMMARY:{len(e.get(\"summary\",\"\"))}')"
```
- **补全分支（Remediate）**：生成失败 → 重试 DeepSeek API 调用，最多 2 次。

### 步骤 3：摘要循环校验（>=300字）
- **动作**：若 len(summary) < 300，循环补全：
```bash
cd scripts && python -c "
from _lib import get_deepseek_key, load_json, save_json; from openai import OpenAI
client=OpenAI(api_key=get_deepseek_key(),base_url='https://api.deepseek.com')
s=load_json('../backend/data/book_summaries.json'); k='TITLE||AUTHOR'
for i in range(2):
    if len(s[k].get('summary',''))>=300: break
    r=client.chat.completions.create(model='deepseek-chat',
        messages=[{'role':'user','content':f'为《TITLE》撰写中文摘要，必须>=300字。当前仅{len(s[k].get(\"summary\",\"\"))}字。'}],
        temperature=0.7, max_tokens=1000)
    s[k]['summary']=r.choices[0].message.content
    save_json('../backend/data/book_summaries.json',s)
print(f'FINAL: {len(s[k][\"summary\"])} chars')
"
```
- **门禁验证（Check）**：len >= 300。
- **失败上限**：2 次后标记 `WARN:SHORT_SUMMARY`。

### 步骤 4：写入验证
- **动作**：
```bash
python -c "import json,os; p='backend/data/book_summaries.json'; d=json.load(open(p)); k='TITLE||AUTHOR'; e=d[k]; assert len(e.get('tags',[]))>=2; assert len(e.get('summary',''))>=300; print('SAVED OK')"
```

## 执行报告（必须输出）
- 成功项：X 条
- 补全项：Y 条（列出：{项目名} -> 补全动作 -> 最终状态）
- 失败跳过项：Z 条（列出：{项目名} -> 失败原因）
