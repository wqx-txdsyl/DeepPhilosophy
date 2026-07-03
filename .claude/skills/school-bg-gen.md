# School Background Generator Skill

## 流派背景图自动生成

两阶段：预训练风格 → 按需生成

## 阶段 1：预训练（一次性）

```bash
cd scripts
python gen_school_bg.py --train
```

分析 `app/public/schools/` 下最多 15 张背景图，AI 输出 master style prompt 保存到 `backend/data/school_style_master.json`。

## 阶段 2：生成

```bash
python gen_school_bg.py "萨满哲学"
```

1. 读取 master style prompt
2. 流派名发送给 `agnes-2.0-flash`，生成内容 prompt（含该流派的关键象征、景观、时代特征）
3. 合并 `master + content` → 最终 prompt
4. `agnes-image-2.1-flash` 生成 1024×768 JPG
5. 自动生成 200×280 缩略图

## 注意事项

- 预训练只需运行一次
- 生成时 AI 可能因不认识流派而拒绝——需在 prompt 中提供足够上下文
- 输出路径：`app/public/schools/{name}.jpg` + `thumb/{name}.jpg`
- API Key 在脚本内
