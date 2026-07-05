# Check Philosopher Images — 全量哲人图片审计+修复

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。步骤 1-5 完成后若列表非空，自动回到步骤 1 重走一轮。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_LIST` = `scripts/_missing_imgs.txt`（缺失列表文件）
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]` / `[DELETED:reason]`

## 前置依赖
- `scripts/check_faces.py`（OpenCV 人脸检测）
- `scripts/_ai_verify_images.py`（Agnes AI 识图验证）
- `scripts/fetch_philosopher_img.py`（Wikipedia + Commons 爬图）
- `scripts/fetch_philosopher_batch.py`（批量爬图）
- `scripts/gen_portrait.py`（AI 生成兜底）
- `scripts/_lib.py`、DeepSeek API Key、Agnes API Key
- OpenCV (`cv2`)、Pillow (`PIL`)

## 状态初始化
> TodoWrite:
- [ ] 步骤 1：扫描缺失 — 找出无图片的哲人，写入 ARG_LIST
- [ ] 步骤 2：双重验证 — OpenCV 人脸 + Agnes AI 识图，剔除建筑物/书影/地图/非肖像
- [ ] 步骤 3：重新爬取 — Wikipedia -> Commons，生成缩略图
- [ ] 步骤 4：重检 — 清空列表，重走步骤 1-2
- [ ] 步骤 5：AI 兜底 — 列表仍非空时，DeepSeek 生 prompt + Agnes 生图

## 原子步骤

### 步骤 1：扫描缺失
- **动作**：
```bash
cd scripts && python -c "
import os, json
with open('../backend/data/philosophers.json',encoding='utf-8') as f: philo=json.load(f)
imgs=set(os.path.splitext(f)[0] for f in os.listdir('../app/public/philosopher') if f.endswith('.jpg'))
missing=[n for n in philo if n.replace('/','-').replace(':','：') not in imgs]
with open('_missing_imgs.txt','w',encoding='utf-8') as f:
    for m in sorted(missing): f.write(m+'\\n')
    f.write(f'\\nTotal: {len(missing)}\\n')
print(f'Philosophers: {len(philo)}, Images: {len(imgs)}, Missing: {len(missing)}')
if missing: print(f'First 10: {missing[:10]}')
"
```
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('scripts/_missing_imgs.txt'); print('LIST CREATED')"`
- **补全分支（Remediate）**：文件写入失败 -> 检查磁盘空间，重试 2 次。

### 步骤 2：双重验证（OpenCV + Agnes AI）
- **动作（Phase A：OpenCV 人脸检测）**：
```bash
cd scripts && PYTHONIOENCODING=utf-8 python check_faces.py 2>&1 | tee _face_check_result.txt
```
- **门禁验证（Check）**：提取无人脸列表：
```bash
cd scripts && python -c "
import re
with open('_face_check_result.txt',encoding='utf-8') as f: text=f.read()
noface=re.findall(r'NOFACE\s+(.+)',text)
print(f'OpenCV NOFACE: {len(noface)}')
if noface:
    with open('_noface_list.txt','w',encoding='utf-8') as f:
        for n in noface: f.write(n.strip()+'\\n')
"
```
- **动作（Phase B：Agnes AI 识图验证 — 仅对 OpenCV 无人脸的图片）**：
```bash
cd scripts && python -c "
import os, json, requests, time

# Load API key
kp=os.path.join(os.path.dirname(os.path.abspath('.')),'api_keys.json')
key=''
if os.path.exists(kp): key=json.load(open(kp)).get('agnes','')
if not key:
    import re
    with open('gen_school_bg.py') as f:
        m=re.search(r'API_KEY\\s*=\\s*\\\"([^\\\"]+)\\\"',f.read())
        if m: key=m.group(1)
assert key, 'NO API KEY'

# Load noface list
noface=[]
if os.path.exists('_noface_list.txt'):
    with open('_noface_list.txt',encoding='utf-8') as f:
        noface=[l.strip() for l in f if l.strip()]

# Load philosophers for era/school context
with open('../backend/data/philosophers.json',encoding='utf-8') as f:
    philo=json.load(f)

AGNES_API='https://apihub.agnes-ai.com/v1/chat/completions'
BASE_URL='https://deepphilosophy-7g7m.onrender.com/philosopher'

bad_images=[]  # 建筑物/书影/地图/非肖像
statue_images=[]  # 雕塑（保留）
ok_images=[]  # 可能是真人照片/画像，只是 OpenCV 没检测到

for i, name in enumerate(noface):
    safe=name.replace('/','-').replace(':','：')
    img_path=f'../app/public/philosopher/{safe}.jpg'
    if not os.path.exists(img_path): continue
    
    url=BASE_URL+'/'+requests.utils.quote(safe+'.jpg')
    info=philo.get(name,{})
    era=info.get('era','')
    prompt=f'''Look at this image. Answer EXACTLY ONE WORD from these choices: PORTRAIT, STATUE, BUILDING, BOOK, MAP, OTHER.
PORTRAIT = a photograph, painting, drawing, or artistic depiction of a PERSON (the philosopher).
STATUE = a sculpture, bust, or 3D monument of the philosopher.
BUILDING = a building, temple, church, architecture.
BOOK = a book cover, manuscript, or text page.
MAP = a map, chart, or geographic image.
OTHER = anything else (landscape, abstract, group photo where philosopher cannot be identified).
The philosopher is {name} ({era}).'''
    
    try:
        r=requests.post(AGNES_API,
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},
            json={'model':'agnes-2.0-flash','messages':[{'role':'user','content':[
                {'type':'text','text':prompt},
                {'type':'image_url','image_url':{'url':url}}
            ]}],'temperature':0.1,'max_tokens':20},
            timeout=30)
        result=r.json()['choices'][0]['message']['content'].strip().upper()
        print(f'[{i+1}/{len(noface)}] {name}: {result}')
        
        if 'PORTRAIT' in result:
            ok_images.append(name)
        elif 'STATUE' in result:
            statue_images.append(name)
        else:  # BUILDING, BOOK, MAP, OTHER
            bad_images.append(name)
            # Delete bad image + thumb
            os.remove(img_path)
            thumb=f'../app/public/philosopher/thumb/{safe}.jpg'
            if os.path.exists(thumb): os.remove(thumb)
            print(f'  [DELETED:AI_CLASSIFIED_AS_{result}]')
    except Exception as e:
        print(f'  [SKIPPED:AI_ERROR] {e}')
        statue_images.append(name)  # Keep on error (conservative)
    time.sleep(0.3)

# Merge bad images into missing list
missing=[]
if os.path.exists('_missing_imgs.txt'):
    with open('_missing_imgs.txt',encoding='utf-8') as f:
        missing=[l.strip() for l in f if l.strip() and not l.startswith('Total')]
all_missing=sorted(set(missing+bad_images))
with open('_missing_imgs.txt','w',encoding='utf-8') as f:
    for m in all_missing: f.write(m+'\\n')
    f.write(f'\\nTotal: {len(all_missing)}\\n')

print(f'\\nRESULTS: OK(PORTRAIT)={len(ok_images)} STATUE(KEEP)={len(statue_images)} BAD(DELETED)={len(bad_images)}')
print(f'FINAL MISSING LIST: {len(all_missing)}')
"
```
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('scripts/_missing_imgs.txt'); print('AUDIT COMPLETE')"`
- **补全分支（Remediate）**：AI API 失败 -> 仅依赖 OpenCV 结果，保留所有 `NOFACE` 图片（不过度删除），标记 `[SKIPPED:AI_DOWN]`。
- **失败上限**：AI 连续失败 5 次 -> 终止 Phase B，标记 `[SKIPPED:AI_UNREACHABLE]`，保留 Phase A 结果。

### 步骤 3：重新爬取
- **动作**：
```bash
cd scripts && python -c "
import os
# Count missing
with open('_missing_imgs.txt',encoding='utf-8') as f:
    missing=[l.strip() for l in f if l.strip() and not l.startswith('Total')]
print(f'To fetch: {len(missing)}')

# Batch fetch
import subprocess, sys
success=0; failed=0
for i,name in enumerate(missing):
    r=subprocess.run([sys.executable,'fetch_philosopher_img.py',name],capture_output=True,text=True,timeout=60)
    if '已保存' in (r.stdout or ''):
        success+=1
    else:
        failed+=1
print(f'Fetched: {success} OK, {failed} FAIL')
"
```
- **门禁验证（Check）**：重新统计缺失数量。
- **补全分支（Remediate）**：爬取失败的 -> Wikipedia 重试 2 次，仍失败进入步骤 5 AI 兜底。

### 步骤 4：重检（清空列表，重走 1-2）
- **动作**：回到步骤 1 重新扫描缺失 -> 步骤 2 双重验证新爬的图片。
- **门禁验证（Check）**：
```bash
cd scripts && python -c "
with open('_missing_imgs.txt',encoding='utf-8') as f:
    missing=[l.strip() for l in f if l.strip() and not l.startswith('Total')]
print(f'REMAINING MISSING: {len(missing)}')
for m in missing: print(f'  {m}')
"
```
- **补全分支（Remediate）**：列表为空 -> 跳到执行报告。列表非空 -> 进入步骤 5。

### 步骤 5：AI 兜底（DeepSeek 文字 prompt + Agnes 生图）
- **动作**：
```bash
cd scripts && python -c "
import os, json, requests, time

# Load API keys
kp=os.path.join(os.path.dirname(os.path.abspath('.')),'api_keys.json')
keys={}
if os.path.exists(kp): keys=json.load(open(kp))
AGNES_KEY=keys.get('agnes','')
DEEPSEEK_KEY=keys.get('deepseek','')
if not AGNES_KEY:
    import re
    with open('gen_school_bg.py') as f:
        m=re.search(r'API_KEY\\s*=\\s*\\\"([^\\\"]+)\\\"',f.read())
        if m: AGNES_KEY=m.group(1)

# Load remaining missing
with open('_missing_imgs.txt',encoding='utf-8') as f:
    missing=[l.strip() for l in f if l.strip() and not l.startswith('Total')]
print(f'AI fallback for {len(missing)} philosophers')

# Load philosophers for context
with open('../backend/data/philosophers.json',encoding='utf-8') as f:
    philo=json.load(f)

from openai import OpenAI
ds_client=OpenAI(api_key=DEEPSEEK_KEY,base_url='https://api.deepseek.com')
IMG_API='https://apihub.agnes-ai.com/v1/images/generations'
PHILO_DIR='../app/public/philosopher'
THUMB_DIR=os.path.join(PHILO_DIR,'thumb')
os.makedirs(THUMB_DIR,exist_ok=True)

for i,name in enumerate(missing):
    safe=name.replace('/','-').replace(':','：')
    info=philo.get(name,{})
    era=info.get('era',''); school=info.get('school',''); country=info.get('country','')

    print(f'[{i+1}/{len(missing)}] {name} ({era} {school} {country})')

    # Step A: DeepSeek generates image prompt
    prompt_resp=ds_client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role':'user','content':f'为哲学家{name}（{era}，{school}，{country}）生成一个AI图片prompt。该prompt用于生成古典水墨风格哲人肖像。输出纯prompt文字，不要额外说明。'}],
        temperature=0.7, max_tokens=200
    )
    img_prompt=prompt_resp.choices[0].message.content.strip()

    # Step B: Agnes generates image
    try:
        r=requests.post(IMG_API,
            headers={'Authorization':f'Bearer {AGNES_KEY}','Content-Type':'application/json'},
            json={'model':'agnes-image-2.1-flash','prompt':img_prompt,'n':1,'size':'1024x1024'},
            timeout=60)
        data=r.json()
        if 'data' in data and data['data']:
            img_url=data['data'][0].get('url','')
            if img_url:
                from PIL import Image; from io import BytesIO
                img_data=requests.get(img_url,timeout=30).content
                img=Image.open(BytesIO(img_data)).convert('RGB')
                img_path=os.path.join(PHILO_DIR,f'{safe}.jpg')
                img.save(img_path,'JPEG',quality=92)
                t=img.copy(); t.thumbnail((200,200))
                t.save(os.path.join(THUMB_DIR,f'{safe}.jpg'),'JPEG',quality=75)
                print(f'  AI GENERATED: {img.size[0]}x{img.size[1]}')
            else:
                print(f'  [SKIPPED:NO_IMG_URL]')
        else:
            print(f'  [SKIPPED:API_ERROR] {str(data)[:100]}')
    except Exception as e:
        print(f'  [SKIPPED:GEN_ERROR] {e}')
    time.sleep(1.5)

# Final count
imgs=set(os.path.splitext(f)[0] for f in os.listdir(PHILO_DIR) if f.endswith('.jpg'))
still_missing=[n for n in philo if n.replace('/','-').replace(':','：') not in imgs]
with open('_missing_imgs.txt','w',encoding='utf-8') as f:
    for m in sorted(still_missing): f.write(m+'\\n')
    f.write(f'\\nTotal: {len(still_missing)}\\n')
print(f'FINAL: {len(philo)} philosophers, {len(imgs)} images, {len(still_missing)} still missing')
"
```
- **门禁验证（Check）**：最终缺失数。
- **补全分支（Remediate）**：如仍有缺失 -> 标记 `[SKIPPED:NO_GEN_CAPACITY]`，需手动处理。
- **失败上限**：2 次后 -> 标记 `[SKIPPED:AI_FALLBACK_EXHAUSTED]`。

## 执行报告（必须输出）
```
第一轮：
  步骤1 缺失: X 人
  步骤2 OpenCV NOFACE: Y 人, Agnes BAD: Z 人 (已删除)
  步骤3 爬取成功: A 人, 失败: B 人
  步骤4 重检后仍缺失: C 人
  步骤5 AI 兜底: D 人
最终缺失: E 人 (0 = CLEAN)

产物: scripts/_missing_imgs.txt, scripts/_noface_list.txt
```
