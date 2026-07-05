# Add Author

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败才报错并**回滚/标记**（而非直接退出）。
- **禁止**：禁止合并步骤、禁止猜测文件路径。

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：查重
- [ ] 步骤 2：AI 生成 + bio 循环校验
- [ ] 步骤 3：标签规范化
- [ ] 步骤 4：写入验证
- [ ] 步骤 5：爬取头像
- [ ] 步骤 6：人脸检测
- [ ] 步骤 7：缩略图
- [ ] 步骤 8：终局自检

## 原子步骤

### 步骤 1：查重
- **动作**：
```bash
cd scripts && python -c "
import json; d=json.load(open('../backend/data/philosophers.json'))
assert 'ARG_NAME' not in d, 'EXISTS'; print('NEW')
"
```
- **门禁验证（Check）**：输出 `NEW`
- **补全分支（Remediate）**：N/A（如已存在则跳过，标记 `EXISTS`）
- **通过条件**：输出 `NEW` 或标记 `SKIPPED:EXISTS`

### 步骤 2：AI 生成 + bio 循环校验
- **动作**：
```bash
cd scripts && python add_author.py "ARG_NAME"
```
- **门禁验证（Check）**：
```bash
python -c "
import json
d=json.load(open('../backend/data/philosophers.json'))
info=d.get('ARG_NAME',{})
bio=info.get('bio','')
assert len(bio)>=1000, f'BIO SHORT: {len(bio)}'
print(f'OK: bio={len(bio)}')
"
```
- **补全分支（Remediate）**：若 `len(bio) < 1000`，调用 DeepSeek 扩充，最多重试 2 次：
```bash
cd scripts && python -c "
from _lib import get_deepseek_key, load_json, save_json, PHILOSOPHERS_FILE
from openai import OpenAI
client=OpenAI(api_key=get_deepseek_key(),base_url='https://api.deepseek.com')
philo=load_json(PHILOSOPHERS_FILE); name='ARG_NAME'
for i in range(2):
    if len(philo[name].get('bio',''))>=1000: break
    r=client.chat.completions.create(model='deepseek-chat',
        messages=[{'role':'user','content':f'为{name}撰写中文简介≥1000字。涵盖生平/思想/著作/影响。纯文本。'}],
        temperature=0.7, max_tokens=3000)
    philo[name]['bio']=r.choices[0].message.content
    save_json(PHILOSOPHERS_FILE, philo)
print(f'FINAL BIO: {len(philo[name][\"bio\"])} chars')
"
```
- **失败上限**：2 次补全后仍 < 1000 字 → 标记 `WARN:SHORT_BIO`，继续执行。

### 步骤 3：标签规范化
- **动作**：
```bash
cd scripts && python -c "
from _normalize_tags import normalize_philosopher
from _lib import load_json, save_json, PHILOSOPHERS_FILE
philo=load_json(PHILOSOPHERS_FILE)
philo['ARG_NAME']=normalize_philosopher(philo['ARG_NAME'])
save_json(PHILOSOPHERS_FILE,philo)
print('NORMALIZED')
"
```
- **门禁验证（Check）**：country 不含 `（）` 括号，school 不含废弃组合标签。
- **补全分支（Remediate）**：手动修正 `_normalize_tags.py` 的 MERGE_MAP。
- **失败上限**：2 次 → 标记 `WARN:TAG`。

### 步骤 4：写入验证
- **动作**：
```bash
python -c "
import json, os
p='backend/data/philosophers.json'; assert os.path.exists(p)
d=json.load(open(p)); info=d['ARG_NAME']
for k in ['era','country','school','bio','wiki_url']:
    assert info.get(k), f'MISSING {k}'
print(f'SAVED: {info[\"era\"]} | {info[\"country\"]} | {info[\"school\"]}')
"
```
- **门禁验证（Check）**：全部字段非空。
- **补全分支（Remediate）**：缺失字段调用 DeepSeek 补齐。

### 步骤 5：爬取头像
- **动作**：
```bash
cd scripts && python fetch_philosopher_img.py "ARG_NAME"
```
- **门禁验证（Check）**：
```bash
python -c "import os; p='app/public/philosopher/ARG_NAME.jpg'; assert os.path.exists(p); assert os.path.getsize(p)>20000; print(f'IMG: {os.path.getsize(p)//1024}KB')"
```
- **补全分支（Remediate）**：重试 Wikipedia→Commons 最多 2 次，仍失败则 `python gen_portrait.py "ARG_NAME"` AI 兜底。
- **失败上限**：AI 兜底也失败 → 标记 `WARN:NO_IMG`。

### 步骤 6：人脸检测
- **动作**：
```bash
cd scripts && python -c "
import cv2, numpy; from PIL import Image
p='../app/public/philosopher/ARG_NAME.jpg'
img=cv2.cvtColor(numpy.array(Image.open(p).convert('RGB')),cv2.COLOR_RGB2BGR)
face=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
print(f'FACES: {len(face.detectMultiScale(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY),1.1,5,minSize=(60,60)))}')
"
```
- **门禁验证（Check）**：输出 `FACES: N`（N≥0 即可，古代画像可能为 0）。
- **补全分支（Remediate）**：N/A（非阻塞步骤）。

### 步骤 7：缩略图
- **动作**：
```bash
python -c "
from PIL import Image; import os
os.makedirs('app/public/philosopher/thumb',exist_ok=True)
img=Image.open('app/public/philosopher/ARG_NAME.jpg').convert('RGB')
t=img.copy(); t.thumbnail((200,200))
t.save('app/public/philosopher/thumb/ARG_NAME.jpg','JPEG',quality=75)
"
```
- **门禁验证（Check）**：
```bash
python -c "import os; assert os.path.exists('app/public/philosopher/thumb/ARG_NAME.jpg'); print('THUMB OK')"
```
- **补全分支（Remediate）**：重试 2 次，从原图重新生成。

### 步骤 8：终局自检
- **动作**：
```bash
python -c "
import json, os
d=json.load(open('backend/data/philosophers.json'))
info=d['ARG_NAME']
checks=[('philosophers.json',True),('era',bool(info.get('era'))),('country',bool(info.get('country'))),
        ('school',bool(info.get('school'))),('bio>=1000',len(info.get('bio',''))>=1000),
        ('wiki_url',bool(info.get('wiki_url'))),('image',os.path.exists('app/public/philosopher/ARG_NAME.jpg')),
        ('thumb',os.path.exists('app/public/philosopher/thumb/ARG_NAME.jpg'))]
for n,ok in checks: print(f'  [{\"PASS\" if ok else \"WARN\"}] {n}')
"
```

## 执行报告（必须输出）
```
成功项: X 条
补全项: Y 条（{项目名} → {补全动作} → {最终状态}）
失败跳过项: Z 条（{项目名} → {失败原因}）
产物: backend/data/philosophers.json, app/public/philosopher/ARG_NAME.jpg
```
