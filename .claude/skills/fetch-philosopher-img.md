# Fetch Philosopher Image

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_NAME` = 哲人名；`ARG_SAFE` = `ARG_NAME.replace('/','-').replace(':','：')`；`ARG_FILE` = `app/public/philosopher/ARG_SAFE.jpg`
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- `scripts/fetch_philosopher_img.py`（Wikipedia + Commons）
- `scripts/gen_portrait.py`（AI 兜底）、Pillow

## 状态初始化
> TodoWrite: 步骤1 Wikipedia搜图 步骤2 Commons备用 步骤3 下载保存 步骤4 缩略图 步骤5 终局自检

## 原子步骤

### 步骤 1：Wikipedia 搜图
- **动作**：`cd scripts && python fetch_philosopher_img.py "ARG_NAME"`
- **门禁验证（Check）**：`python -c "import os; p='app/public/philosopher/ARG_SAFE.jpg'; print('FOUND' if os.path.exists(p) else 'NOT FOUND - trying Commons')"`

### 步骤 2：Commons 备用
- **动作**：脚本内自动 fallback。
- **补全分支（Remediate）**：Commons 也无图 -> `cd scripts && python gen_portrait.py "ARG_NAME"` AI 兜底。
- **失败上限**：AI 兜底也失败 -> `[SKIPPED:NO_IMG]`。

### 步骤 3：下载保存
- **门禁验证（Check）**：
```bash
python -c "import os; from PIL import Image; p='ARG_FILE'; assert os.path.exists(p); img=Image.open(p); sz=os.path.getsize(p); assert sz>=20000; print(f'OK: {img.size[0]}x{img.size[1]}, {sz//1024}KB')"
```
- **补全分支（Remediate）**：文件 < 20KB -> 重新下载 2 次。

### 步骤 4：缩略图
- **动作**：
```bash
python -c "from PIL import Image; import os; p='ARG_FILE'; os.path.exists(p) and (os.makedirs('app/public/philosopher/thumb',exist_ok=True), t:=Image.open(p).convert('RGB').copy(), t.thumbnail((200,200)), t.save('app/public/philosopher/thumb/ARG_SAFE.jpg','JPEG',quality=75), print('THUMB OK')) or print('[SKIPPED:NO_IMG]')"
```

### 步骤 5：终局自检
- **动作**：`python -c "import os; p='ARG_FILE'; t='app/public/philosopher/thumb/ARG_SAFE.jpg'; print(f'IMG:{\"OK\" if os.path.exists(p) else \"MISSING\"} THUMB:{\"OK\" if os.path.exists(t) else \"MISSING\"}')"`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z
- 产物：ARG_FILE, app/public/philosopher/thumb/ARG_SAFE.jpg
