# Add School Skill

## 一键新增哲学流派

```
输入流派名 → DeepSeek生成数据 → 图片改名 → 内联DATA → 谱系页 → 地图定位 → 计数更新
```

## 用法

```bash
cd scripts
python add_school.py "流派名"
```

## 自动完成

| 步骤 | 说明 |
|------|------|
| 数据生成 | 流派 JSON 不存在时，DeepSeek 自动生成全部内容（概述/结语/思想家/著作/术语/名言/时间轴） |
| 图片处理 | 中文→英文文件名，生成 200×280 缩略图 |
| 内联 DATA | 生成 JS const → 注入 SchoolDetailPage + ENG_NAMES |
| 分页插入 | WorldPhilosophiesPage 按时间顺序插入 |
| 谱系插入 | GenealogyPage ALL_SCHOOLS + IMG_MAP + PhilosophyTimeline |
| 地图定位 | 地区性世界流派 → Agnes 识图定位 → WorldMap 添加光点 |
| 计数更新 | HomePage/Settings/Genealogy 流派数自动更新 |

## 完成后手动

```bash
cd app && npm run build
rm -rf ../backend/app-dist ../backend/static && cp -r dist ../backend/app-dist && cp -r dist ../backend/static
git add -A && git commit -m "feat: 新增流派" && git push
```

## 依赖

- DeepSeek API（生成流派数据）：key 在 `scripts/api_keys.json`
- Agnes API（图像识别定位）：key 同上
- Python: `requests`, `Pillow`
