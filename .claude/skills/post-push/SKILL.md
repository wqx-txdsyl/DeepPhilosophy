---
name: post-push
description: 推送后检查——数据计数→封面完整性→章节同步→books.json有效性
---

## 检查项

### 1. 数据计数
```bash
python -c "import json;b=json.load(open('app/public/books.json','r',encoding='utf-8'));p=json.load(open('app/public/philosophers.json','r',encoding='utf-8'));print(f'books:{len(b)} philosophers:{len(p)}')"
```

### 2. 封面完整性
```bash
python -c "import json,os;c=json.load(open('app/public/covers.json','r',encoding='utf-8'));missing=[bid for bid,url in c.items() if not os.path.exists('app/public/'+url.lstrip('/'))];print(f'covers_missing:{len(missing)}')"
```

### 3. 哲学家头像
```bash
python -c "import os;p=json.load(open('app/public/philosophers.json','r',encoding='utf-8'));imgs=set(os.path.splitext(f)[0] for f in os.listdir('app/public/philosopher') if f.endswith('.webp'));m=[n for n in p if n.replace('/','-').replace(':','：') not in imgs];print(f'missing_imgs:{len(m)}')"
```

### 4. books.json 与 book_detail 一致性
```bash
python -c "import json,os;b=json.load(open('app/public/books.json','r',encoding='utf-8'));details=set(f.replace('.json','') for f in os.listdir('app/public/book_detail') if f.endswith('.json'));orphans=[x['id'] for x in b if x['id'] not in details];print(f'orphan_details:{len(orphans)}')"
```

### 5. 章节数据存在性
```bash
python -c "import os;chapters=os.listdir('backend/data/book_chapters');print(f'chapter_dirs:{len(chapters)}')"
```
