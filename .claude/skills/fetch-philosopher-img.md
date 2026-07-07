# Fetch Philosopher Image

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败重试 2 次，仍失败标记 `[SKIPPED:reason]`。
- **变量替换规则**：`ARG_NAME` = 哲人名；`ARG_SAFE` = `ARG_NAME.replace('/','-').replace(':','：')`；`ARG_FILE` = `app/public/philosopher/ARG_SAFE.webp`
- **标记格式**：`[SKIPPED:reason]` / `[WARN:reason]`

## 前置依赖
- `scripts/fetch_philosopher_img.py`（Wikipedia + Commons）
- `scripts/gen_portrait.py`（AI 兜底）、Pillow

## 状态初始化
> TodoWrite: 步骤1 Wikipedia搜图 步骤2 Commons备用 步骤3 下载保存 步骤4 转WebP删原文件 步骤5 终局自检

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
python -c "import os; from PIL import Image; p='ARG_FILE'; j=p.replace('.webp','.jpg'); fp=p if os.path.exists(p) else j; assert os.path.exists(fp); img=Image.open(fp); sz=os.path.getsize(fp); assert sz>=20000; print(f'OK: {img.size[0]}x{img.size[1]}, {sz//1024}KB')"
```
- **补全分支（Remediate）**：文件 < 20KB -> 重新下载 2 次。

### 步骤 4：转 WebP 并删除原文件
- **动作**：
```bash
python -c "
from PIL import Image; import os
p='ARG_FILE'
for ext in ['.jpg','.png']:
    fp=p.replace('.jpg',ext).replace('.png',ext)
    if os.path.exists(fp):
        img=Image.open(fp).convert('RGB')
        webp=fp.replace(ext,'.webp')
        img.save(webp,'WEBP',quality=80)
        os.remove(fp)
        print(f'WEBP OK ({os.path.getsize(webp)//1024}KB), {ext} deleted')
        break
else:
    print('[SKIPPED:NO_IMG]')
"
```

### 步骤 5：终局自检
- **动作**：`python -c "import os; w='ARG_FILE'.replace('.jpg','.webp'); print(f'WEBP:{\"OK\" if os.path.exists(w) else \"MISSING\"}')"`

## 执行报告（必须输出）
- 成功项：X | 补全项：Y | 失败跳过项：Z
- 产物：ARG_FILE (webp)
