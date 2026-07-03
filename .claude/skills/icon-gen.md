# Icon Generator Skill

## 一键从 emoji 生成 UI 图标

输入 emoji → 文字模型分析含义 → 自动生成生图 prompt → 生图 → 去背景

## 用法

```bash
cd scripts
python gen_icon_from_emoji.py "🔥"           # 生成 icon-flame.png
python gen_icon_from_emoji.py "🧠" brain     # 指定输出文件名
```

## 流程

1. 将 emoji 发送给 `agnes-2.0-flash`（文字模型）
2. AI 分析 emoji 含义，输出英文 prompt（line-art, monochrome, transparent bg）
3. 将 prompt 发送给 `agnes-image-2.1-flash` 生成 1024×1024 PNG
4. PIL 泛洪填充 + 阈值过滤去掉白色背景

## 输出

- `../icons/icon-{name}.png` — 透明背景的图标

## 依赖

- `requests`, `Pillow`
- API Key 在脚本内（已加入 .gitignore）
