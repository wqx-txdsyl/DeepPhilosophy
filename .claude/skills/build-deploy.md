# Build & Deploy Skill

## 构建

```bash
cd app && npm run build
rm -rf ../backend/app-dist && cp -r dist ../backend/app-dist
```

## 部署

推送到 `master` → Render 自动部署。

## 本地开发

```bash
cd app && npm run dev          # http://localhost:5173
cd backend && pip install -r requirements.txt
KNOWLEDGE_DIR=F:/philosophy python main.py  # http://localhost:8000
```

## 新增哲学家

```bash
cd scripts && python add_author.py "哲学家名"
```

## 新增流派

```bash
cd scripts && python add_school.py "流派名"
```

## 批量入库

```bash
cd scripts && python _batch_add.py --apply
```

## 图片

```bash
cd scripts && python fetch_philosopher_batch.py --skip-existing
python check_faces.py --fix
python gen_portrait.py          # AI 兜底
```

## 标签修复

```bash
cd scripts && python _comprehensive_audit.py
```

## 本地检查

```bash
cd scripts && python check_faces.py
# 启动后端验证 API
cd ../backend && KNOWLEDGE_DIR=$(pwd)/data python main.py
curl http://localhost:8000/api/health
```
