---
name: fix-counts
description: 修正统计数据——同步 HomePage + README + 各页面计数
---

## 检查项

### 1. 实际数据统计
```bash
python -c "
import json, os
books=json.load(open('app/public/books.json','r',encoding='utf-8'))
philo=json.load(open('app/public/philosophers.json','r',encoding='utf-8'))
epubs=sum(1 for b in books if b.get('file_type')=='epub')
txts=sum(1 for b in books if b.get('file_type')=='txt')
east=sum(1 for p in philo.values() if p.get('region')=='东方')
west=sum(1 for p in philo.values() if p.get('region')=='西方')
world=sum(1 for p in philo.values() if p.get('region')=='世界')
print(f'books:{len(books)}(EPUB:{epubs}+TXT:{txts}) philosophers:{len(philo)}(东{east}/西{west}/世{world})')
"
```

### 2. 更新 README.md 数据
将步骤1的结果更新到 README 的统计数据

### 3. 更新 HomePage 默认值
更新 `app/src/pages/HomePage.jsx` 中 `useState` 的默认数值

### 4. 验证
```bash
cd app && npm run build
```
