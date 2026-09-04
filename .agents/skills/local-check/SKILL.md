---
name: local-check
description: 本地完整性检查——数据文件/图片/JSON/构建
---

## 检查项

### 1. 核心 JSON 可读
```bash
python -c "import json;json.load(open('app/public/books.json','r',encoding='utf-8'));json.load(open('app/public/philosophers.json','r',encoding='utf-8'));print('JSONs OK')"
```

### 2. 哲学家头像完整
```bash
python -c "import os,json;p=json.load(open('app/public/philosophers.json','r',encoding='utf-8'));imgs=set(os.path.splitext(f)[0] for f in os.listdir('app/public/philosopher') if f.endswith('.webp'));missing=[n for n in p if n.replace('/','-').replace(':','：') not in imgs];print(f'missing:{len(missing)}' if missing else 'ALL_OK')"
```

### 3. 流派图片完整
```bash
python -c "import os,re;c=open('app/src/pages/SchoolDetailPage.jsx',encoding='utf-8').read();import re;refs=set(re.findall(r\"url\(/schools/([^)]+)\)\",c));imgs=set(f for f in os.listdir('app/public/schools') if f.endswith('.webp'));m=refs-imgs;print(f'missing_bg:{len(m)}' if m else 'ALL_OK')"
```

### 4. book_detail 与 books.json 一致
```bash
python -c "import json,os;b=json.load(open('app/public/books.json','r',encoding='utf-8'));ids=[x['id'] for x in b];details=[f.replace('.json','') for f in os.listdir('app/public/book_detail') if f.endswith('.json')];print(f'books:{len(ids)} details:{len(details)} mismatch:{len(set(ids)-set(details))}')"
```

### 5. 构建测试
```bash
cd app && npm run build
```
