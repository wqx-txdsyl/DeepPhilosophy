# Agnes AI Image（共享：哲人肖像 + 流派背景图）

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_NAME` = 目标名；`ARG_TYPE` = `portrait`(哲人) 或 `school`(流派)；`ARG_DIR` = `philosopher`(portrait) 或 `schools`(school)；`ARG_SIZE` = `1024x1024`(portrait) 或 `2560x1440`(school)
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- Agnes API Key（`scripts/api_keys.json` 的 `agnes` 字段，或 `scripts/gen_school_bg.py` 中硬编码）
- `scripts/gen_portrait.py`（哲人肖像入口）
- `scripts/gen_school_bg.py`（流派背景图入口）
- `scripts/_lib.py`、Pillow

## 入口选择
| 用途 | 脚本 | ARG_DIR |
|------|------|---------|
| 哲人肖像 | `python gen_portrait.py "ARG_NAME"` | `app/public/philosopher` |
| 流派背景 | `python gen_school_bg.py "ARG_NAME"` | `app/public/schools` |

## 状态初始化
> 执行前必须先调用 `TodoWrite`：
- [ ] 步骤 1：API Key 校验（共享）
- [ ] 步骤 2：生成图片（入口脚本）
- [ ] 步骤 3：文件验证（共享）
- [ ] 步骤 4：缩略图（共享）

## 原子步骤

### 步骤 1：API Key 校验（共享）
- **动作**：
```bash
cd scripts && python -c "
import json,os,re; key=''
kp=os.path.join(os.path.dirname(os.path.abspath('.')),'api_keys.json')
if os.path.exists(kp): key=json.load(open(kp)).get('agnes','')
if not key:
    with open('gen_school_bg.py') as f:
        m=re.search(r'API_KEY\s*=\s*\"([^\"]+)\"',f.read())
        if m: key=m.group(1)
assert key, '[SKIPPED:NO_API_KEY]'; print('KEY OK')
"
```
- **补全分支（Remediate）**：无 Key -> 检查 `api_keys.json` 是否包含 `agnes` 字段。

### 步骤 2：生成图片
- **动作**：`cd scripts && python gen_portrait.py "ARG_NAME"`（哲人）或 `python gen_school_bg.py "ARG_NAME"`（流派）
- **门禁验证（Check）**：
```bash
python -c "import os; p='app/public/ARG_DIR/ARG_NAME.jpg'; print(f'GEN OK: {os.path.getsize(p)//1024}KB' if os.path.exists(p) else '[SKIPPED:GEN_FAILED]')"
```
- **补全分支（Remediate）**：生成失败 -> 检查 API 余额/网络，重试 2 次。

### 步骤 3：文件验证（共享）
- **动作**：
```bash
python -c "
import os; from PIL import Image
p='app/public/ARG_DIR/ARG_NAME.jpg'
if not os.path.exists(p): print('[SKIPPED:NO_FILE]'); exit(0)
img=Image.open(p); sz=os.path.getsize(p)
min_w=512 if 'ARG_TYPE'=='portrait' else 1200
assert img.size[0]>=min_w, f'[WARN:TOO_SMALL] {img.size}'
assert sz>=20000, f'[WARN:TOO_SMALL_FILE] {sz}'
print(f'{img.size[0]}x{img.size[1]}, {sz//1024}KB')
"
```

### 步骤 4：缩略图（共享）
- **动作**：
```bash
python -c "
from PIL import Image; import os
p='app/public/ARG_DIR/ARG_NAME.jpg'
if not os.path.exists(p): print('[SKIPPED:NO_FILE]'); exit(0)
os.makedirs('app/public/ARG_DIR/thumb',exist_ok=True)
img=Image.open(p).convert('RGB'); t=img.copy()
ts=(200,200) if 'ARG_TYPE'=='portrait' else (400,300)
t.thumbnail(ts); t.save(f'app/public/ARG_DIR/thumb/ARG_NAME.jpg','JPEG',quality=75)
print('THUMB OK')
"
```
- **门禁验证（Check）**：`python -c "import os; print('THUMB OK' if os.path.exists('app/public/ARG_DIR/thumb/ARG_NAME.jpg') else '[SKIPPED:NO_THUMB]')"`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
- 产物：`app/public/ARG_DIR/ARG_NAME.jpg`, `app/public/ARG_DIR/thumb/ARG_NAME.jpg`
