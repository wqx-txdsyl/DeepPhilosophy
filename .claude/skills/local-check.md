# Local Check Skill — 推送前本地验证

每次 `npm run build` 后、`git push` 前执行。

## 检查清单

### 1. 构建产物完整性
```bash
# dist 必须有 index.html
test -f app/dist/index.html || echo "MISSING: index.html"

# 核心 chunk 必须存在
ls app/dist/assets/index-*.js >/dev/null 2>&1 || echo "MISSING: main JS bundle"
ls app/dist/assets/vendor-react-*.js >/dev/null 2>&1 || echo "MISSING: vendor-react"

# 图片目录非空
test $(ls app/dist/philosopher/*.jpg 2>/dev/null | wc -l) -gt 300 || echo "WARN: <300 philosopher images"
test $(ls app/dist/schools/*.jpg 2>/dev/null | wc -l) -gt 50 || echo "WARN: <50 school images"
```

### 2. 后端 API 响应
```bash
# 启动服务器（后台），等待就绪后测试
cd backend && python main.py &
sleep 4

# 核心 API
curl -s -o /dev/null -w "books: %{http_code}\n" http://localhost:8000/api/books
curl -s -o /dev/null -w "authors: %{http_code}\n" http://localhost:8000/api/authors
curl -s -o /dev/null -w "stats: %{http_code}\n" http://localhost:8000/api/stats
curl -s -o /dev/null -w "health: %{http_code}\n" http://localhost:8000/api/health
```

### 3. 哲学家数据完整性
```bash
python -c "
import json
with open('backend/data/philosophers.json') as f:
    p = json.load(f)
print(f'Philosophers: {len(p)}')
# 检查必需字段
missing = [n for n, d in p.items() if not d.get('era') or not d.get('school')]
if missing:
    print(f'WARN: {len(missing)} philosophers missing era/school')
# 检查图片
import os
imgs = set(f.replace('.jpg','') for f in os.listdir('app/public/philosopher') if f.endswith('.jpg'))
no_img = [n for n in p if n.replace('/','-').replace(':','：') not in imgs]
if no_img:
    print(f'MISSING IMAGES: {len(no_img)}')
    for n in no_img[:10]: print(f'  - {n}')
else:
    print('All philosophers have images')
"
```

### 4. 学校图片 + 引用一致性
```bash
python -c "
import os, re
# 检查 SchoolDetailPage 引用的图片是否都存在
with open('app/src/pages/SchoolDetailPage.jsx', 'r') as f:
    content = f.read()
refs = set(re.findall(r\"bg:'url\(/schools/([^)]+)\)'\", content))
imgs = set(f for f in os.listdir('app/public/schools') if f.endswith('.jpg'))
missing = refs - imgs
if missing:
    print(f'MISSING school images: {len(missing)}')
    for m in missing: print(f'  - {m}')
else:
    print(f'All {len(refs)} school bg references have images')
# 检查 GenealogyPage IMG_MAP
with open('app/src/pages/GenealogyPage.jsx', 'r') as f:
    g = f.read()
map_refs = set(re.findall(r\"'([^']+)'\", g.split('IMG_MAP')[1].split('};')[0]))
for m in map_refs:
    if m + '.jpg' not in imgs:
        print(f'Genealogy IMG_MAP miss: {m}')
"
```

### 5. 死代码检查
```bash
# 不应存在的文件
test -f app/src/pages/_new_schools_data.jsx && echo "DEAD: _new_schools_data.jsx still exists!"
ls app/public/schools/school_*.json 2>/dev/null && echo "DEAD: school JSON files still exist (inline data used instead)"
```

### 6. 文件大小检查
```bash
# SchoolDetailPage 应该是 2.5MB 左右（含 inline data）
SZ=$(wc -c < app/src/pages/SchoolDetailPage.jsx)
if [ $SZ -lt 2000000 ]; then echo "WARN: SchoolDetailPage too small ($SZ bytes, expected ~2.5MB)"; fi

# 哲学家图片不应有过小的文件
python -c "
import os
tiny = [(f, os.path.getsize(os.path.join('app/public/philosopher',f))//1024) for f in os.listdir('app/public/philosopher') if f.endswith('.jpg') and os.path.getsize(os.path.join('app/public/philosopher',f)) < 5000]
if tiny: print(f'{len(tiny)} tiny philosopher images (<5KB)')
"
```

### 7. 服务器停止
```bash
# 杀掉测试服务器
kill $(lsof -ti:8000) 2>/dev/null
```

## 通过标准
- 所有 API 返回 200
- 0 个哲学家缺图
- 0 个学校 bg 引用缺图
- 0 个死代码文件
- SchoolDetailPage > 2MB（inlined data intact）
