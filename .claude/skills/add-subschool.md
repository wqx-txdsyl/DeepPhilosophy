# Add Sub-School Skill

## 一键新增下属流派（sub-school）

```
输入下属流派名 → DeepSeek生成数据 → 图片处理 → JSON复制到public → SCHOOL_MAP注入 → 更新父流派sub_schools
```

与 `add_school` 的区别：
- **不插入** world-philosophies / genealogy / timeline / worldmap
- **不更新** 主页流派计数（subschool 不计入总数）
- SCHOOL_MAP 使用 `_json` 动态加载（不内联 DATA）

## 用法

```bash
cd scripts
python add_subschool.py "下属流派名" "父流派名"
```

示例：
```bash
python add_subschool.py "伊壁鸠鲁学派" "古希腊哲学"
```

## 自动完成

| 步骤 | 说明 |
|------|------|
| 数据生成 | 流派 JSON 不存在时，DeepSeek 自动生成（概述/结语/思想家/著作/术语/名言/时间轴） |
| closingQuote 补全 | 若 DeepSeek 遗漏 closingQuote，自动取 quotes 最后一条生成（格式：`名言。——作者`） |
| 图片处理 | 生成 200×280 缩略图 |
| JSON 复制 | 将 JSON 复制到 `app/public/schools/` 供前端动态加载 |
| SCHOOL_MAP 注入 | 在父流派条目后添加 `_json` 引用条目 |
| 父流派更新 | 更新父流派的 `sub_schools` 字段及对应的 `_SUB_SCHOOLS` 数组 |

## 完成后手动

```bash
cd app && npm run build
rm -rf ../backend/app-dist ../backend/static && cp -r dist ../backend/app-dist && cp -r dist ../backend/static
git add -A && git commit -m "feat: 新增下属流派" && git push
```

## 依赖

- DeepSeek API（生成流派数据）：key 在 `scripts/api_keys.json`
- Python: `requests`, `Pillow`
