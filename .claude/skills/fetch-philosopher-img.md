# Fetch Philosopher Image Skill

## 爬取哲学家无水印照片

输入哲学家名 → Wikipedia 信息框搜图 → Wikimedia Commons 备用 → 下载保存 + 缩略图

## 用法

```bash
cd scripts
python fetch_philosopher_img.py "哲学家名"
```

示例：
```bash
python fetch_philosopher_img.py "孔子"
python fetch_philosopher_img.py "Immanuel Kant"
python fetch_philosopher_img.py "亚里士多德"
```

## 流程

| 步骤 | 说明 |
|------|------|
| Wikipedia 搜图 | 通过 Wikipedia API 查找哲学家页面的信息框（infobox）主图 → 获取 800px 缩略图 URL |
| Commons 备用 | 若 Wikipedia 无图，搜索 Wikimedia Commons → 筛选 JPG/PNG（>50KB, <10MB） → 优先竖版人像 |
| 下载保存 | 下载原图 → 转 JPG 保存至 `app/public/philosopher/{name}.jpg` |
| 缩略图 | 自动生成 200×280 缩略图 → `app/public/philosopher/thumb/{name}.jpg` |

## 特点

- **无水印**：Wikipedia/Commons 图片均为 CC/公有领域，无水印
- **去重**：若图片已存在则跳过
- **安全命名**：自动处理文件名中的特殊字符

## 输出

- `app/public/philosopher/{哲学家名}.jpg` — 原图（JPEG 92% 质量）
- `app/public/philosopher/thumb/{哲学家名}.jpg` — 缩略图（200×280）

## 依赖

- Python: `requests`, `Pillow`
- 无需 API Key（使用 Wikipedia / Wikimedia Commons 公开 API）

## 注意事项

- Wikipedia 中文站图片资源较少，英文名搜索命中率更高
- 部分哲学家可能没有 CC-licensed 照片（尤其是 20 世纪以后仍在版权保护期的）
- 如两个来源均无图，脚本会提示手动获取的 URL
