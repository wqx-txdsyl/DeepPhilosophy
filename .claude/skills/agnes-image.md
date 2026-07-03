# Agnes AI 图像生成与识别

## 概述

使用 Sapiens AI 的 Agnes 模型进行文生图和图像理解。API Key 存储在 `scripts/` 下的脚本中（已加入 `.gitignore`，不会提交）。

---

## API 信息

| 项目 | 值 |
|------|-----|
| Base URL | `https://apihub.agnes-ai.com` |
| 图像生成模型 | `agnes-image-2.1-flash` |
| 语言+视觉模型 | `agnes-2.0-flash` |
| 生图端点 | `POST /v1/images/generations` |
| 聊天/识图端点 | `POST /v1/chat/completions` |
| 当前价格 | $0/张（生图），$0/1M tokens（语言） |

---

## 脚本工具

### 1. 本地文生图工具
**文件**: `scripts/img_gen.html`
- 浏览器打开即可使用
- 输入 prompt 和尺寸 → 生成图片
- API Key 已预填在密码框中
- 历史记录自动保存到 localStorage

### 2. 批量生成 icon
**文件**: `scripts/generate_icons.py`
- 从 CSV `emoji_inventory.csv` 读取 icon 列表
- 批量调用 Agnes Image API 生成 78 个图标
- 自动去除白色背景（PIL 泛洪填充）
- 支持断点续传（已生成的跳过）

```bash
cd scripts
python generate_icons.py              # 生成全部 78 个
python generate_icons.py nav-books    # 只生成指定
```

### 3. 图像背景修复
**文件**: `scripts/fix_bg.py`
- 泛洪填充 + 像素阈值双重去背景
- 阈值 r+g+b > 300，二遍扫描覆盖内部封闭区域

```bash
python fix_bg.py
```

### 4. AI 视觉定位世界地图坐标
**文件**: `scripts/fix_map_coords.py`
- 将世界地图图片发送给 Agnes 2.0 Flash
- AI 分析图片并返回各地区的百分比坐标
- 输出 `map_coords_fixed.json`

---

## API 调用示例

### 文生图（URL 输出）
```python
import requests

r = requests.post(
    "https://apihub.agnes-ai.com/v1/images/generations",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "agnes-image-2.1-flash",
        "prompt": "...",
        "size": "1024x1024",
        "extra_body": {"response_format": "url"}
    }
)
url = r.json()["data"][0]["url"]
```

### 文生图（Base64 输出）
```python
json={
    "model": "agnes-image-2.1-flash",
    "prompt": "...",
    "size": "1024x1024",
    "return_base64": True
}
b64 = r.json()["data"][0]["b64_json"]
```

### 图像理解
```python
r = requests.post(
    "https://apihub.agnes-ai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "agnes-2.0-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "描述这张图片"},
                {"type": "image_url", "image_url": {"url": "https://example.com/img.jpg"}}
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 2048
    }
)
result = r.json()["choices"][0]["message"]["content"]
```

---

## 注意事项

1. **API Key 保密**：Key 存储在脚本文件中，通过 `.gitignore` 防止提交
2. **`response_format` 必须在 `extra_body` 内**：不要放在请求顶层
3. **中文 prompt 效果差**：icon 生成使用英文 prompt
4. **生成图片有白底**：用 `fix_bg.py` 去背景，阈值 r+g+b > 300
5. **URL 中的图片需公网可访问**：本地图片需先上传或用 data URI

---

## 项目使用记录

| 用途 | 脚本 | 结果 |
|------|------|------|
| 78 个 UI icon | `generate_icons.py` | `app/public/icons/` |
| 世界地图坐标修正 | `fix_map_coords.py` | WorldMap.jsx 坐标 |
| 本地测试生图 | `img_gen.html` | 浏览器工具 |
| 背景清理 | `fix_bg.py` | 泛洪填充 + 阈值过滤 |
