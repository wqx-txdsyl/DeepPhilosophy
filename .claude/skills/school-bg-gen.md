# School Background Generator Skill

## 流派背景图生成

输入流派名 → 读预训练风格 → AI 生成内容 prompt → 合并生图

## 用法

```bash
cd scripts
python gen_school_bg.py "萨满哲学"
```

## 流程

1. 读 `backend/data/school_style_master.json`（预训练已完成，包含色板/纹理/光线/构图风格）
2. 读 `backend/data/school_{流派名}.json` 的 overview 文本作为上下文
3. 发送给 `agnes-2.0-flash` 生成该流派的视觉内容 prompt
4. 合并 `master style + content prompt` → 最终 prompt
5. `agnes-image-2.1-flash` 生成 1024×768 JPG
6. 自动生成 200×280 缩略图

## 输出

- `app/public/schools/{name}.jpg`
- `app/public/schools/thumb/{name}.jpg`
