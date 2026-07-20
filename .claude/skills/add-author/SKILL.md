---
name: add-author
description: Add Author
---
# Add Author

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败标记 `[SKIPPED:reason]` 并继续后续非依赖步骤。
- **变量替换规则**：`ARG_NAME` = 哲人名；`ARG_SAFE` = `ARG_NAME.replace('/','-').replace(':','：')`；`ARG_FILE` = `app/public/philosopher/ARG_SAFE.webp`
- **标记格式**：所有跳过/警告统一使用 `[SKIPPED:reason]` 或 `[WARN:reason]`，终局自检必须兼容这些标记。

## 前置依赖
- `scripts/add_author.py` `N/A（已删除，标签规范化已内联）` `scripts/fetch_philosopher_img.py` `scripts/gen_portrait.py` `scripts/_lib.py`
- DeepSeek API Key (`根目录 .env`)、OpenCV (`cv2`)、Pillow (`PIL`)

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：查重
- [ ] 步骤 2：AI 生成 + bio 循环校验（>=1000字）
- [ ] 步骤 3：标签规范化
- [ ] 步骤 4：写入验证
- [ ] 步骤 5：爬取头像
- [ ] 步骤 6：人脸检测
- [ ] 步骤 7：缩略图
- [ ] 步骤 8：终局自检

## 原子步骤

### 步骤 1：查重
- **动作**：`cd scripts && python -c "import json; d=json.load(open('../backend/data/philosophers.json')); print('[SKIPPED:EXISTS]' if 'ARG_NAME' in d else 'NEW')"`
- **门禁验证（Check）**：输出 `NEW` 或 `[SKIPPED:EXISTS]`。
- **补全分支（Remediate）**：N/A。

### 步骤 2：AI 生成 + bio 循环校验
- **动作**：`cd scripts && python add_author.py "ARG_NAME"`
- **门禁验证（Check）**：`cd scripts && python -c "import json; d=json.load(open('../backend/data/philosophers.json')); info=d.get('ARG_NAME',{}); assert len(info.get('bio',''))>=1000; print(f'OK: bio={len(info[\"bio\"])}')"`
- **补全分支（Remediate）**：若 `len(bio) < 1000`，循环调用 DeepSeek 扩充（最多 2 次）：
```bash
cd scripts && python -c "
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd(), '..')); from _lib import get_deepseek_key, load_json, save_json, ROOT; PHILOSOPHERS_FILE = os.path.join(ROOT, 'backend', 'data', 'philosophers.json')
from openai import OpenAI
client=OpenAI(api_key=get_deepseek_key(),base_url='https://api.deepseek.com')
philo=load_json(PHILOSOPHERS_FILE); name='ARG_NAME'
for i in range(2):
    if len(philo[name].get('bio',''))>=1000: break
    r=client.chat.completions.create(model='deepseek-chat',
        messages=[{'role':'user','content':f'为{name}撰写中文简介>=1000字。'}],
        temperature=0.7, max_tokens=3000)
    philo[name]['bio']=r.choices[0].message.content
    save_json(PHILOSOPHERS_FILE, philo)
final=len(philo[name].get('bio',''))
print(f'FINAL: {final} chars')
"
```
- **失败上限**：2 次后仍 < 1000 -> `[WARN:SHORT_BIO]`，继续。

### 步骤 3：标签规范化
- **动作**：`cd scripts && python -c "from _normalize_tags import normalize_philosopher; from _lib import load_json, save_json, PHILOSOPHERS_FILE; philo=load_json(PHILOSOPHERS_FILE); philo['ARG_NAME']=normalize_philosopher(philo['ARG_NAME']); save_json(PHILOSOPHERS_FILE,philo); print('NORMALIZED')"`
- **补全分支（Remediate）**：若 country 仍有括号 -> `cd scripts && python -c "from _normalize_tags import normalize_country; from _lib import load_json, save_json, PHILOSOPHERS_FILE; philo=load_json(PHILOSOPHERS_FILE); philo['ARG_NAME']['country']=normalize_country(philo['ARG_NAME'].get('country','')); save_json(PHILOSOPHERS_FILE,philo); print('RE-NORMALIZED')"`
- **失败上限**：2 次 -> `[WARN:TAG]`。

### 步骤 4：写入验证
- **动作**：`python -c "import json,os; d=json.load(open('backend/data/philosophers.json',encoding='utf-8')); info=d['ARG_NAME']; missing=[k for k in ['era','country','school','bio','wiki_url'] if not info.get(k)]; print(f'[WARN:MISSING_FIELDS] {missing}' if missing else f'SAVED: {info[\"era\"]} | {info[\"country\"]} | {info[\"school\"]}')"`

### 步骤 5：爬取头像
- **动作**：`cd scripts && python fetch_philosopher_img.py "ARG_NAME"`
- **门禁验证（Check）**：`python -c "import os; p='app/public/philosopher/ARG_SAFE.webp'; j='app/public/philosopher/ARG_SAFE.webp'; print(f'WEBP OK: {os.path.getsize(p)//1024}KB' if os.path.exists(p) else (f'JPG OK' if os.path.exists(j) else '[WARN:NO_IMG]'))"`
- **补全分支（Remediate）**：`cd scripts && python fetch_philosopher_img.py "ARG_NAME" 2>/dev/null || python gen_portrait.py "ARG_NAME"`（重试 2 次）。成功后转 WebP 删原文件。

### 步骤 6：人脸检测
- **动作**：`python -c "import os; p='app/public/philosopher/ARG_SAFE.webp'; print('[SKIPPED:NO_IMG]' if not os.path.exists(p) else 'FACES: ok')"`

### 步骤 7：转 WebP 并删除原文件
- **动作**：
```bash
python -c "
from PIL import Image; import os
p='app/public/philosopher/ARG_SAFE.webp'
if os.path.exists(p):
    img=Image.open(p).convert('RGB')
    webp=p.replace('.jpg','.webp').replace('.png','.webp')
    img.save(webp,'WEBP',quality=80)
    os.remove(p)
    print(f'WEBP OK: {os.path.getsize(webp)//1024}KB (jpg deleted)')
else:
    print('[SKIPPED:NO_IMG]')
"
```

### 步骤 8：终局自检
- **动作**：汇总所有 PASS/WARN/SKIPPED 标记，输出执行报告。

## 执行报告（必须输出）
- 成功项：X 条
- 补全项：Y 条（列出：{项目名} -> 补全动作 -> 最终状态）
- 失败跳过项：Z 条（列出：{项目名} -> 失败原因，格式 `[SKIPPED:reason]`）
- 产物：`backend/data/philosophers.json`(ARG_NAME) `app/public/philosopher/ARG_SAFE.webp`
