# DeepPhilosophy 云端部署完整指南

## 原理

```
手机 App ──→ https://deepphilosophy.onrender.com (Render 免费)
                │
                ├── /api/books, /api/authors ... → Render 本地计算
                ├── /api/books/{id}/file ──→ Cloudflare R2 (预签名URL, 10GB免费)
                └── 摘要/标签缓存 → Render 盘内 (几百KB)
```

把 `F:/philosophy`（4.3GB）上传到 R2，后端从 R2 读文件列表 + 生成下载链接。本地开发照旧读本地文件。

---

## 一、创建 Cloudflare R2 存储桶

1. 打开 https://dash.cloudflare.com/sign-up 注册（免费）
2. 左侧菜单 → **R2** → **Create bucket**
3. 名称 `deepphilosophy-books`，区域选 **APAC**
4. 记下 **Account ID**（Dashboard 顶部 URL 里那串 hex，如 `abc123...`）
5. 进入 **R2** → **Manage R2 API Tokens** → **Create API Token**
   - 权限：**Object Read & Write**
   - 指定桶：`deepphilosophy-books`
   - 创建后**立即复制** Access Key ID 和 Secret Access Key（只显示一次！）

---

## 二、上传书籍到 R2

```bash
# 安装 AWS CLI
winget install Amazon.AWSCLI

# 配置（用上一步的 Key）
aws configure
# AWS Access Key ID: <你的Access Key ID>
# AWS Secret Access Key: <你的Secret Access Key>
# Default region name: auto
# Default output format: json

# 上传全部书籍（用你实际的 Account ID 替换）
aws s3 sync F:/philosophy s3://deepphilosophy-books/books/ \
  --endpoint-url https://<账户ID>.r2.cloudflarestorage.com

# 验证
aws s3 ls s3://deepphilosophy-books/books/东方/ --endpoint-url https://<账户ID>.r2.cloudflarestorage.com
aws s3 ls s3://deepphilosophy-books/books/西方/ --endpoint-url https://<账户ID>.r2.cloudflarestorage.com
```

---

## 三、修改后端代码

### 3.1 安装依赖

```bash
pip install boto3
```

并在 `backend/requirements.txt` 追加一行 `boto3`。

### 3.2 backend/config.py — 追加以下内容

```python
# ============================================================
# Cloudflare R2 云存储配置
# ============================================================
USE_R2 = os.getenv("USE_R2", "False").lower() in ("true", "1", "yes")

R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY", "")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_BUCKET = os.getenv("R2_BUCKET", "deepphilosophy-books")
```

### 3.3 backend/.env — 追加

```env
USE_R2=true
R2_ACCESS_KEY=<你的Access Key ID>
R2_SECRET_KEY=<你的Secret Access Key>
R2_ENDPOINT=https://<账户ID>.r2.cloudflarestorage.com
R2_BUCKET=deepphilosophy-books
```

### 3.4 backend/main.py — 完整的修改

**文件开头 import 区追加：**

```python
import boto3
from botocore.config import Config as BotoConfig
```

**在 `import config` 之后、`from auth import ...` 之前加入 R2 客户端：**

```python
_r2_client = None

def _get_r2_client():
    """懒加载 R2 客户端"""
    global _r2_client
    if _r2_client is None and config.USE_R2:
        _r2_client = boto3.client(
            's3',
            aws_access_key_id=config.R2_ACCESS_KEY,
            aws_secret_access_key=config.R2_SECRET_KEY,
            endpoint_url=config.R2_ENDPOINT,
            config=BotoConfig(
                region_name='auto',
                signature_version='s3v4',
            ),
        )
    return _r2_client
```

**替换 `scan_books()` 函数：**

```python
def scan_books() -> list[dict]:
    """扫描书籍目录 —— 本地或 R2 自动切换"""
    if config.USE_R2:
        return _scan_books_r2()
    return _scan_books_local()


def _scan_books_r2() -> list[dict]:
    """从 Cloudflare R2 列出所有书籍"""
    TITLE_FIXES = {"SZ": "S/Z"}
    client = _get_r2_client()
    books = []
    seen_authors = set()

    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=config.R2_BUCKET, Prefix='books/'):
        for obj in page.get('Contents', []):
            key = obj['Key']  # e.g. books/西方/柏拉图/理想国.pdf
            filename = key.rsplit('/', 1)[-1]
            ext = Path(filename).suffix.lower()
            if ext not in ('.pdf', '.epub', '.txt', '.md'):
                continue

            # 解析路径: books/region/author/title.ext
            parts = key.replace('books/', '', 1).split('/')
            if len(parts) < 3:
                continue
            region = parts[0]
            author = parts[1].replace('###合集&概述###', '合集&概述')
            title = Path(parts[-1]).stem
            title = TITLE_FIXES.get(title, title)

            file_id = hashlib.md5(key.encode()).hexdigest()[:12]
            seen_authors.add(author)

            tags = _classify_book(title, author, region)
            books.append({
                "id": file_id,
                "title": title,
                "author": author,
                "region": region,
                "file_type": ext.replace('.', ''),
                "file_size": obj['Size'],
                "status": "pending" if ext == '.txt' else "available",
                "path": key.replace('books/', '', 1),
                "tags": tags,
                "updated_at": obj['LastModified'].strftime('%Y-%m-%dT%H:%M:%S'),
            })

    # 补充目录存在但无文件的作者（占位）
    all_authors = set()
    prefix_len = len('books/')
    paginator2 = client.get_paginator('list_objects_v2')
    for page in paginator2.paginate(Bucket=config.R2_BUCKET, Prefix='books/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            p = prefix['Prefix'][prefix_len:]  # e.g. 西方/ or 西方/柏拉图/
            parts = p.rstrip('/').split('/')
            if len(parts) == 2:
                region_name = parts[0]
                author_dir = parts[1]
                author_clean = author_dir.replace('###合集&概述###', '合集&概述')
                if author_clean not in seen_authors and author_clean:
                    seen_authors.add(author_clean)
                    pfx = hashlib.md5(author_dir.encode()).hexdigest()[:12]
                    books.append({
                        "id": pfx,
                        "title": f"（待收录：{author_clean}）",
                        "author": author_clean,
                        "region": region_name,
                        "file_type": "txt",
                        "file_size": 0,
                        "status": "pending",
                        "path": f"{region_name}/{author_dir}/",
                        "tags": ["待收录"],
                        "updated_at": datetime.now().isoformat(),
                    })

    # 附加缓存关键词和标签
    kw_cache = {}
    if os.path.exists(_BOOKS_CACHE_PATH):
        try:
            with open(_BOOKS_CACHE_PATH, 'r', encoding='utf-8') as f:
                kw_cache = json.load(f)
        except Exception:
            pass
    summary_cache = _load_summaries_cache()
    for b in books:
        key = b["title"] + "||" + b["author"]
        b["keywords"] = kw_cache.get(key, [])
        if key in summary_cache and summary_cache[key].get("tags"):
            cached_tags = summary_cache[key]["tags"]
            for t in cached_tags:
                if t not in b["tags"]:
                    b["tags"].append(t)

    return sorted(books, key=lambda b: (_book_sort_key(b), b["region"], b["author"], b["title"]))


def _scan_books_local() -> list[dict]:
    """本地扫描（原 scan_books 逻辑，重命名）"""
    TITLE_FIXES = {"SZ": "S/Z"}
    books = []
    knowledge_dir = config.KNOWLEDGE_DIR
    if not os.path.exists(knowledge_dir):
        return books

    for root, dirs, files in os.walk(knowledge_dir):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext not in (".pdf", ".epub", ".txt", ".md"):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, knowledge_dir)
            parts = rel_path.replace("\\", "/").split("/")
            region = parts[0] if len(parts) > 0 else "未知"
            author = parts[1] if len(parts) > 1 else "未知"
            author_clean = author.replace("###合集&概述###", "合集&概述")
            title = Path(f).stem
            title = TITLE_FIXES.get(title, title)
            file_id = hashlib.md5(rel_path.encode()).hexdigest()[:12]
            tags = _classify_book(title, author_clean, region)
            books.append({
                "id": file_id, "title": title, "author": author_clean,
                "region": region, "file_type": ext.replace(".", ""),
                "file_size": os.path.getsize(full_path),
                "status": "pending" if ext == ".txt" else "available",
                "path": rel_path.replace("\\", "/"), "tags": tags,
                "updated_at": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat(),
            })

    seen_authors = {b["author"] for b in books}
    for region_name in ["东方", "西方"]:
        region_path = os.path.join(knowledge_dir, region_name)
        if not os.path.isdir(region_path):
            continue
        for author_dir in os.listdir(region_path):
            author_full = os.path.join(region_path, author_dir)
            if not os.path.isdir(author_full):
                continue
            author_clean = author_dir.replace("###合集&概述###", "合集&概述")
            if author_clean in seen_authors:
                continue
            has_files = any(
                os.path.splitext(f)[1].lower() in ('.pdf', '.epub', '.txt', '.md')
                for f in os.listdir(author_full)
            )
            if has_files:
                continue
            seen_authors.add(author_clean)
            pfx = hashlib.md5(author_dir.encode()).hexdigest()[:12]
            books.append({
                "id": pfx,
                "title": f"（待收录：{author_clean}）",
                "author": author_clean,
                "region": region_name,
                "file_type": "txt", "file_size": 0, "status": "pending",
                "path": f"{region_name}/{author_dir}/",
                "tags": ["待收录"],
                "updated_at": datetime.now().isoformat(),
            })

    kw_cache = {}
    if os.path.exists(_BOOKS_CACHE_PATH):
        try:
            with open(_BOOKS_CACHE_PATH, 'r', encoding='utf-8') as f:
                kw_cache = json.load(f)
        except Exception:
            pass
    summary_cache = _load_summaries_cache()
    for b in books:
        key = b["title"] + "||" + b["author"]
        b["keywords"] = kw_cache.get(key, [])
        if key in summary_cache and summary_cache[key].get("tags"):
            cached_tags = summary_cache[key]["tags"]
            for t in cached_tags:
                if t not in b["tags"]:
                    b["tags"].append(t)
    return sorted(books, key=lambda b: (_book_sort_key(b), b["region"], b["author"], b["title"]))
```

**替换 `/api/books/{book_id}/file` 端点：**

```python
@app.get("/api/books/{book_id}/file")
async def download_book(book_id: str):
    """下载/流式传输书籍文件 —— R2 模式返回预签名 URL，本地模式返回文件流"""
    books = scan_books()
    book = None
    for b in books:
        if b["id"] == book_id:
            book = b
            break
    if not book:
        raise HTTPException(status_code=404, detail="书籍未找到")

    if config.USE_R2:
        # R2 模式：生成 1 小时有效的预签名下载 URL，浏览器直接跳转
        client = _get_r2_client()
        r2_key = 'books/' + book["path"]
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': config.R2_BUCKET, 'Key': r2_key},
            ExpiresIn=3600,
        )
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url)
    else:
        # 本地模式：流式返回文件
        file_path = os.path.join(config.KNOWLEDGE_DIR, book["path"])
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        ext = Path(file_path).suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".epub": "application/epub+zip",
            ".txt": "text/plain",
            ".md": "text/markdown",
        }
        return FileResponse(
            file_path,
            media_type=mime_map.get(ext, "application/octet-stream"),
            filename=book["title"] + ext,
        )
```

---

## 四、部署到 Render

### 4.1 设置环境变量

在 Render Dashboard → Web Service → **Environment**，添加：

| Key | Value |
|-----|-------|
| `USE_R2` | `true` |
| `R2_ACCESS_KEY` | 你的 Access Key ID |
| `R2_SECRET_KEY` | 你的 Secret Access Key |
| `R2_ENDPOINT` | `https://<账户ID>.r2.cloudflarestorage.com` |
| `R2_BUCKET` | `deepphilosophy-books` |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek Key |

### 4.2 推送代码

```bash
cd C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy
git add .
git commit -m "feat: cloud storage via Cloudflare R2"
git push origin main
```

Render 自动检测 push 并重新部署。

---

## 五、App 连接

Android / Web App 设置中，API 地址填 Render 地址（如 `https://deepphilosophy.onrender.com`）。

`app/.env`:
```
VITE_API_URL=https://deepphilosophy.onrender.com
```

---

## 六、本地开发 vs 云端

开发时 `USE_R2=false`（或不设），后端照旧读 `F:/philosophy`。部署时 Render 环境变量设 `USE_R2=true` 即切到 R2。

```bash
# 本地开发
cd C:\dp\backend && KNOWLEDGE_DIR=F:/philosophy python main.py

# 测试 R2 模式（本地模拟云端）
USE_R2=true R2_ACCESS_KEY=xxx R2_SECRET_KEY=xxx R2_ENDPOINT=xxx python main.py
```

---

## 七、费用

| 服务 | 免费额度 | 用量 | 月费 |
|------|----------|------|:---:|
| Render Web Service | 750h | 全月 | $0 |
| R2 存储 | 10 GB | ~4.3 GB | $0 |
| R2 A 类操作（list/write） | 100 万次 | 极少 | $0 |
| R2 B 类操作（read） | 1000 万次 | 极少 | $0 |
| **合计** | | | **$0** |

---

## 八、常见问题

**Q: R2 被墙怎么办？**
给 R2 桶绑自定义域名（Cloudflare Dashboard → R2 → Settings → Custom Domains），Cloudflare 免费提供 CDN。

**Q: PDF 太大（有些 > 100MB），下载慢？**
预签名 URL 让浏览器直连 R2，不经过 Render 中转。速度取决于用户到 Cloudflare 节点的延迟。

**Q: 更新书籍需要重新部署吗？**
不需要。R2 里新增/替换文件即可，`scan_books()` 每次请求都重新列出 R2 对象。

**Q: 摘要缓存、用户数据库在哪？**
这些在 Render 的 1GB 持久盘内（`backend/data/`），不在 R2。很小，几百 KB 到几 MB。
