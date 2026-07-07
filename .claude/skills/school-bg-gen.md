# School Background Generator（入口 -> agnes-image.md）

> 此文件为瘦入口，共享逻辑见 `agnes-image.md`。

## 变量
- `ARG_NAME` = 流派名
- `ARG_TYPE` = `school`
- `ARG_DIR` = `schools`
- `ARG_SIZE` = `2560x1440`

## 核心执行协议
同 `agnes-image.md` — 顺序执行，每步带检查-补全-验证闭环。

## 前置依赖
同 `agnes-image.md`，额外依赖 `scripts/gen_school_bg.py`

## 原子步骤（入口）
1. **API Key 校验**：同 agnes-image 步骤 1
2. **生成流派背景**：`cd scripts && python gen_school_bg.py "ARG_NAME"`
3. **文件验证**：同 agnes-image 步骤 3（min_w=1200）
4. **转 WebP 并删除原文件**：
```bash
python -c "
from PIL import Image; import os
for ext in ['.jpg','.png']:
    p=f'app/public/schools/ARG_NAME{ext}'
    if os.path.exists(p):
        img=Image.open(p).convert('RGB')
        img.save(f'app/public/schools/ARG_NAME.webp','WEBP',quality=80)
        os.remove(p); print(f'WEBP OK, {ext} deleted'); break
"
```

## 执行报告
格式同 `agnes-image.md`
