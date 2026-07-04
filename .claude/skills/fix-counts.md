# Fix Philosophy Counts Skill

## 修正所有页面的流派数量

当流派数量发生变化时，需要同步更新以下 **6 个页面** 中的数据，确保一致性。

## 涉及的页面和数据

| 页面 | 文件 | 需要修正的内容 |
|------|------|---------------|
| **HomePage** | `app/src/pages/HomePage.jsx` | ① `useState(103)` — schoolCount 初始值<br>② `西方 41 流派` — 西方流派数<br>③ `东方 24 流派` — 东方流派数<br>④ `世界 38 流派` — 世界流派数 |
| **WesternPhilosophiesPage** | `app/src/pages/WesternPhilosophiesPage.jsx` | `四十一个流派` — 西方流派数（中文数字） |
| **EasternPhilosophiesPage** | `app/src/pages/EasternPhilosophiesPage.jsx` | `二十四个流派` — 东方流派数（中文数字） |
| **WorldPhilosophiesPage** | `app/src/pages/WorldPhilosophiesPage.jsx` | 如有计数需更新（当前无硬编码计数） |
| **GenealogyPage** | `app/src/pages/GenealogyPage.jsx` | `103个哲学流派` — 页脚总计数 |
| **SettingsPage** | `app/src/pages/SettingsPage.jsx` | ① `schools: 103` — useState fallback<br>② `Math.max(103, ...)` — API fallback |

## 计数规则

- **总流派数** = `data:` 条目数（不含 `_json:` 的 subschool）
- **西方流派数** = region 为 "西方" 的 `data:` 条目数
- **东方流派数** = region 为 "东方" 的 `data:` 条目数
- **世界流派数** = 总流派数 − 西方流派数 − 东方流派数
- **subschool**（`_json:` 条目）**不计入**任何计数

## 自动化脚本

```bash
cd scripts
python add_school.py --update-counts-only
```

脚本 `add_school.py` 的 `update_counts()` 函数会自动：
1. 扫描 `SchoolDetailPage.jsx` 的 `SCHOOL_MAP`
2. 统计 `data:` 条目总数及各 region 分布
3. 更新 HomePage、SettingsPage、GenealogyPage 的计数

## 手动检查清单

每次增删流派后，必须确认以下各处一致：

- [ ] `HomePage.jsx` — useState 初始值、三区域计数
- [ ] `HomePage.jsx` — 底部三区域快捷链接的计数
- [ ] `EasternPhilosophiesPage.jsx` — 标题下副标题的计数
- [ ] `WesternPhilosophiesPage.jsx` — 标题下副标题的计数
- [ ] `GenealogyPage.jsx` — 页脚"XXX个哲学流派"
- [ ] `SettingsPage.jsx` — useState fallback 和 Math.max fallback

## 中文数字对照

| 数字 | 中文 | 数字 | 中文 |
|------|------|------|------|
| 20 | 二十 | 30 | 三十 |
| 21 | 二十一 | 38 | 三十八 |
| 22 | 二十二 | 41 | 四十一 |
| 23 | 二十三 | 42 | 四十二 |
| 24 | 二十四 | 43 | 四十三 |
| 25 | 二十五 | 103 | 一百零三 |
