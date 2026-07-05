# Local Check

## 核心执行协议（覆盖默认行为）
- **模式**：顺序执行，每步带"检查-补全-验证"闭环。
- **遇缺失处理**：**禁止终止**。补全失败则重试最多 2 次，仍失败标记并继续执行后续步骤。

## 状态初始化
> 执行前必须先调用 `TodoWrite`：
- [ ] 步骤 1：构建
- [ ] 步骤 2：哲人图片（599 张）
- [ ] 步骤 3：流派背景图（SCHOOL_MAP 全覆盖）
- [ ] 步骤 4：死代码检查
- [ ] 步骤 5：API 响应
- [ ] 步骤 6：文件大小

## 原子步骤

### 步骤 1：构建
- **动作**：`cd app && npm run build && rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist`
- **门禁验证（Check）**：`test -f app/dist/index.html && test -f backend/app-dist/index.html && echo "BUILD OK"`
- **补全分支（Remediate）**：构建失败 → 检查 CSS 语法错误 → 修复后重试。

### 步骤 2：哲人图片
- **动作**：
```bash
python -c "
import os, json
with open('backend/data/philosophers.json') as f: philo=json.load(f)
imgs=set(os.path.splitext(f)[0] for f in os.listdir('app/public/philosopher') if f.endswith('.jpg'))
m=[n for n in philo if n.replace('/','-').replace(':','：') not in imgs]
print(f'{len(philo)} philosophers, {len(imgs)} images, {len(m)} missing')
if m: print('MISSING:', m[:5])
"
```
- **补全分支（Remediate）**：有缺图 → `python fetch_philosopher_batch.py --skip-existing`，仍缺则 `python gen_portrait.py` AI 兜底。

### 步骤 3：流派背景图
- **动作**：
```bash
python -c "
import os, re
with open('app/src/pages/SchoolDetailPage.jsx',encoding='utf-8') as f:
    refs=set(re.findall(r\"bg:'url\(/schools/([^)]+)\)'\",f.read()))
imgs=set(f for f in os.listdir('app/public/schools') if f.endswith('.jpg'))
m=refs-imgs; print(f'{len(refs)} refs, {len(imgs)} imgs, {len(m)} missing')
if m: print(m)
"
```
- **补全分支（Remediate）**：缺背景图 → 检查文件名是否匹配（中文 vs 英文）。

### 步骤 4：死代码
- **动作**：
```bash
test -f app/src/pages/_new_schools_data.jsx && echo "DEAD" || echo "OK"
ls app/public/schools/school_*.json 2>/dev/null && echo "DEAD JSONs" || echo "OK"
```

### 步骤 5：API 响应
- **动作**：
```bash
cd backend && python main.py & sleep 4
for ep in /api/health /api/books /api/authors; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$ep")
    echo "$ep: $code"
done
kill %1 2>/dev/null
```

### 步骤 6：文件大小
- **动作**：`wc -c < app/src/pages/SchoolDetailPage.jsx`
- **门禁验证（Check）**：≥ 2000000 bytes。

## 执行报告（必须输出）
```
成功项: X 条 | 补全项: Y 条 | 失败跳过项: Z 条
ISSUES: N (0 = CLEAN)
```
