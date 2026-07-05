# Add School

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败则重试最多 2 次，仍失败标记 `[SKIPPED:reason]` 并继续。
- **变量替换规则**：`ARG_NAME` = 流派名；`ARG_JSON` = `app/public/schools/school_ARG_NAME.json`；`ARG_IMG` = `app/public/schools/ARG_NAME.jpg`
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- `scripts/add_school.py` `scripts/gen_school_bg.py` `scripts/_normalize_tags.py`
- DeepSeek API Key、Agnes API Key (`scripts/api_keys.json`)
- Node.js (`npx eslint`)

## 状态初始化
> 执行前必须先调用 `TodoWrite`：
- [ ] 步骤 1：数据生成
- [ ] 步骤 2：overview/conclusion 循环校验（>=500字）
- [ ] 步骤 3：图片处理
- [ ] 步骤 4：内联 DATA
- [ ] 步骤 5：ESLint 语法检查
- [ ] 步骤 6：计数更新
- [ ] 步骤 7：构建验证

## 原子步骤

### 步骤 1：数据生成
- **动作**：`cd scripts && python add_school.py "ARG_NAME"`
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/schools/school_ARG_NAME.json'); print('JSON OK')"`
- **补全分支（Remediate）**：失败 -> `cd scripts && python add_school.py "ARG_NAME"` 重试 2 次。

### 步骤 2：overview/conclusion 循环校验（>=500字）
- **门禁验证（Check）**：`python -c "import json; d=json.load(open('app/public/schools/school_ARG_NAME.json')); assert len(d.get('overview',''))>=500; assert len(d.get('conclusion',''))>=500; print('TEXT OK')"`
- **补全分支（Remediate）**：不足 500 字 -> DeepSeek 扩充循环 2 次：
```bash
cd scripts && python -c "
from _lib import get_deepseek_key; from openai import OpenAI
import json; client=OpenAI(api_key=get_deepseek_key(),base_url='https://api.deepseek.com')
p='../app/public/schools/school_ARG_NAME.json'; d=json.load(open(p,encoding='utf-8'))
for field in ['overview','conclusion']:
    for i in range(2):
        if len(d.get(field,''))>=500: break
        r=client.chat.completions.create(model='deepseek-chat',
            messages=[{'role':'user','content':f'扩充以下哲学流派{field}至>=500字：{d[field]}'}],
            temperature=0.7, max_tokens=2000)
        d[field]=r.choices[0].message.content
        json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(f'overview={len(d[\"overview\"])} conclusion={len(d[\"conclusion\"])}')
"
```

### 步骤 3：图片处理
- **动作**：检查 ARG_IMG 是否存在；无则 `cd scripts && python gen_school_bg.py "ARG_NAME"`
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/schools/ARG_NAME.jpg'); assert os.path.exists('app/public/schools/thumb/ARG_NAME.jpg'); print('IMG+THUMB OK')"`
- **补全分支（Remediate）**：
```bash
cd scripts && python gen_school_bg.py "ARG_NAME" || python -c "
from PIL import Image; import os
p='../app/public/schools/ARG_NAME.jpg'
if os.path.exists(p):
    os.makedirs('../app/public/schools/thumb',exist_ok=True)
    img=Image.open(p).convert('RGB'); t=img.copy(); t.thumbnail((400,300))
    t.save('../app/public/schools/thumb/ARG_NAME.jpg','JPEG',quality=80)
    print('THUMB DONE')
"
```

### 步骤 4：内联 DATA
- **动作**：add_school.py 自动注入 SchoolDetailPage + GenealogyPage + WorldMap。
- **门禁验证（Check）**：`python -c "import re; c=open('app/src/pages/SchoolDetailPage.jsx',encoding='utf-8').read(); assert 'ARG_NAME' in c; print('INLINE OK')"`

### 步骤 5：ESLint 语法检查
- **动作**：`cd app && npx eslint src/pages/SchoolDetailPage.jsx --no-error-on-unmatched-pattern 2>&1 | tail -5`
- **门禁验证（Check）**：无 `error` 输出（`warning` 可忽略）。
- **补全分支（Remediate）**：若有 error -> 检查 JSX 中 `{` `}` 配对、引号转义、const 声明顺序。
- **失败上限**：eslint 不可用时跳过，标记 `[SKIPPED:NO_ESLINT]`。

### 步骤 6：计数更新
- **动作**：`cd scripts && python add_school.py --update-counts-only`
- **门禁验证（Check）**：`python -c "import re; c=open('app/src/pages/GenealogyPage.jsx',encoding='utf-8').read(); assert 'ARG_NAME' in c; print('COUNT OK')"`

### 步骤 7：构建验证
- **动作**：`cd app && npm run build`
- **门禁验证（Check）**：`test -f app/dist/index.html && echo "BUILD OK"`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
- 产物：ARG_JSON, ARG_IMG, SchoolDetailPage.jsx（已更新）, GenealogyPage.jsx（已更新）
