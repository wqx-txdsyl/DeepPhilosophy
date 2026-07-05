# Fetch Philosopher Image

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。必须调用对应补全函数/脚本，补全后重新验证。补全失败则重试最多 2 次，仍失败才报错并**回滚/标记**（而非直接退出）。

## 状态初始化
> 执行前必须先调用 `TodoWrite`，勾选状态实时更新：
- [ ] 步骤 1：Wikipedia 搜图
- [ ] 步骤 2：Commons 备用
- [ ] 步骤 3：下载保存
- [ ] 步骤 4：缩略图
- [ ] 步骤 5：终局自检

## 原子步骤

### 步骤 1：Wikipedia 搜图
- **动作**：
```bash
cd scripts && python fetch_philosopher_img.py "ARG_NAME"
```
- **门禁验证（Check）**：
```bash
python -c "import os; p='app/public/philosopher/ARG_NAME.jpg'; print('FOUND' if os.path.exists(p) else 'NOT FOUND')"
```
- **补全分支（Remediate）**：若 `NOT FOUND` → 进入步骤 2 Commons 备用。

### 步骤 2：Commons 备用
- **动作**：脚本内自动 fallback 到 Wikimedia Commons。
- **门禁验证（Check）**：同上，检查文件是否已存在。
- **补全分支（Remediate）**：Commons 也无图 → `python gen_portrait.py "ARG_NAME"` AI 生成兜底。
- **失败上限**：AI 兜底也失败 → 标记 `WARN:NO_IMG`，继续。

### 步骤 3：下载保存
- **动作**：
```bash
python -c "
import os; from PIL import Image
p='app/public/philosopher/ARG_NAME.jpg'
assert os.path.exists(p), 'NOT FOUND'
img=Image.open(p); sz=os.path.getsize(p)
assert sz>=20000, f'TOO SMALL: {sz}'
print(f'OK: {img.size[0]}x{img.size[1]}, {sz//1024}KB')
"
```
- **补全分支（Remediate）**：文件 < 20KB → 重新下载，最多 2 次。

### 步骤 4：缩略图
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
- **补全分支（Remediate）**：重试 2 次。

### 步骤 5：终局自检
- **动作**：
```bash
python -c "
import os; p='app/public/philosopher/ARG_NAME.jpg'; t='app/public/philosopher/thumb/ARG_NAME.jpg'
checks=[('image',os.path.exists(p) and os.path.getsize(p)>=20000),('thumb',os.path.exists(t))]
for n,ok in checks: print(f'  [{\"PASS\" if ok else \"WARN\"}] {n}')
"
```

## 执行报告（必须输出）
```
成功项: X 条 | 补全项: Y 条 | 失败跳过项: Z 条
产物: app/public/philosopher/ARG_NAME.jpg, app/public/philosopher/thumb/ARG_NAME.jpg
```
