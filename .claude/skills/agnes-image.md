# Agnes AI Image

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败才报错并**回滚/标记**（而非直接退出）。

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：API Key 校验
- [ ] 步骤 2：生成图片（gen_portrait / gen_school_bg）
- [ ] 步骤 3：文件验证（存在 + 尺寸 + 大小）
- [ ] 步骤 4：缩略图

## 原子步骤

### 步骤 1：API Key 校验
- **动作**：
```bash
cd scripts && python -c "
import json,os,re; key=''
if os.path.exists('api_keys.json'): key=json.load(open('api_keys.json')).get('agnes','')
if not key:
    with open('gen_school_bg.py') as f:
        m=re.search(r'API_KEY\s*=\s*\"([^\"]+)\"',f.read())
        if m: key=m.group(1)
assert key, 'API KEY MISSING'; print('KEY OK')
"
```
- **门禁验证（Check）**：`KEY OK`。
- **补全分支（Remediate）**：无 Key -> 检查 api_keys.json 或 gen_school_bg.py。

### 步骤 2：生成图片
- **动作**：`cd scripts && python gen_portrait.py "ARG_NAME"` 或 `python gen_school_bg.py "ARG_SCHOOL"`
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/TARGET_DIR/ARG_NAME.jpg'); print(f'GEN OK: {os.path.getsize(\"app/public/TARGET_DIR/ARG_NAME.jpg\")//1024}KB')"`
- **补全分支（Remediate）**：生成失败 -> 检查 API 余额/网络，重试最多 2 次。

### 步骤 3：文件验证
- **动作**：
```bash
python -c "import os; from PIL import Image; p='app/public/TARGET_DIR/ARG_NAME.jpg'; img=Image.open(p); assert img.size[0]>=512; assert os.path.getsize(p)>=20000; print(f'{img.size[0]}x{img.size[1]}, {os.path.getsize(p)//1024}KB')"
```
- **补全分支（Remediate）**：尺寸不足 -> 重新生成，指定更大 size 参数。

### 步骤 4：缩略图
- **动作**：标准 400x300 thumb 生成脚本。
- **门禁验证（Check）**：`python -c "import os; assert os.path.exists('app/public/TARGET_DIR/thumb/ARG_NAME.jpg'); print('THUMB OK')"`

## 执行报告（必须输出）
- 成功项：X 条 | 补全项：Y 条 | 失败跳过项：Z 条
