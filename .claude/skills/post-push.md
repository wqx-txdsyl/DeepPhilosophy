# Post-Push Cleanup Skill

## 推送后例行维护

每次 `git push` 后执行，确保项目文档和代码整洁。

## 执行清单

### 1. Skill 文件检查

确认每个 `.claude/skills/*.md` 都有对应的可执行脚本，且文档描述与实际功能一致：

| Skill | 脚本 | 状态检查 |
|-------|------|---------|
| add-author | `scripts/add_author.py` | 生成数据→爬图→人脸检测→缩略图 |
| add-book | `scripts/add_book.py` | |
| add-school | `scripts/add_school.py` | 生成→内联→谱系→地图→计数 |
| add-subschool | `scripts/add_subschool.py` | 生成→_json→父流派更新 |
| fetch-philosopher-img | `scripts/fetch_philosopher_img.py` | Wikipedia→Commons→下载 |
| fix-counts | `scripts/add_school.py update_counts()` | 自动扫描 SCHOOL_MAP |
| school-bg-gen | `scripts/gen_school_bg.py` | Agnes AI 生成背景图 |
| icon-gen | `scripts/gen_icon_from_emoji.py` | |
| post-push | (本文件) | |

### 2. README 更新

检查以下数字是否与实际一致：
- [ ] 版本号
- [ ] 流派总数（当前：103，subschool 不计入）
- [ ] 哲人总数（当前：599）
- [ ] 东西世三区域计数
- [ ] `philosophers.json` 条目数
- [ ] `name_aliases.json` 条目数
- [ ] 新增的页面/组件是否已列入架构图

### 3. 冗余文件清理

```bash
# 检查 scripts/ 下是否有遗留的临时/一次性脚本
cd scripts
ls _* 2>/dev/null          # 以下划线开头的临时文件
ls *.log *.txt 2>/dev/null # 运行时日志/数据

# 常见需清理：
#   _batch_fetch.log        # 批量爬取日志
#   _batch_philosophers*.txt # 临时名单
#   _fix_*.py, _gen_*.py    # 一次性修复/生成脚本
#   _missing_*.txt          # 审计中间文件
```

### 4. 项目文件整理

- [ ] `app/public/philosopher/` 头像数与哲人数一致（当前 599/599）
- [ ] `app/public/schools/` 流派背景图完整
- [ ] `backend/data/` 无孤立 JSON 文件
- [ ] `.gitignore` 排除临时文件（*.log, _*.txt 等）

### 5. 关键数据一致性

运行快速审计：
```bash
# 流派计数
grep -c "'[^']*': {" app/src/pages/SchoolDetailPage.jsx

# 哲人计数  
python -c "import json; print(len(json.load(open('backend/data/philosophers.json'))))"

# 头像计数
ls app/public/philosopher/*.jpg | wc -l
```

### 6. 提交

```bash
git add -A
git commit -m "chore: post-push cleanup (update README, remove temp files)"
git push
```
