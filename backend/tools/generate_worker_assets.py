# -*- coding: utf-8 -*-
"""生成 Cloudflare api worker 静态资产（workers/api/src/）：
- books.json: id(md5(rel_path)[:12]) → {oss?, github?, size, ext} 文件直链映射
  （Worker /api/books/{id}/file 用它 302 到 OSS 或代理 GitHub Release，零 Worker 流量优先）
- stats.json: {books, authors, schools} 三数（/api/stats 用）
- admin_stats.json: 访问统计快照（/api/admin/stats 用，DeveloperPage 数字冻结于迁移时刻）

数据源: backend/data/oss_manifest.json + github_manifest.json（key=rel_path, value={url,size}）
        app/public/books.json（book 数）、philosophers.json（作者数）、schools/data/school_*.json（流派数）
        backend/data/admin_stats.json（访问统计）
id 规则与 Render scan_books_oss 一致: hashlib.md5(rel_path.encode()).hexdigest()[:12]

N7（audit 2026-08-18）— 与 app/public/books.json 的关系（非重复副本, 勿混淆）:
  · app/public/books.json  = 前端「书单」: 每本书的标题/作者/chapterCount/封面等元数据列表（list),
      由 backend/tools/dp_sync_books.py 从 backend/data/book_detail 汇总生成, 前端列表/详情页读取;
  · 本脚本生成的 workers/api/src/books.json = 「CDN manifest」: 书 id → OSS/GitHub 文件直链映射（dict),
      由本脚本从 backend/data/oss_manifest.json + github_manifest.json 生成, Worker 直链跳转用。
  两者结构不同（list vs dict）、来源不同（book_detail vs oss/github manifest）、用途不同（书单 vs 直链）。
  改书库后需分别重新生成（dp_sync_books.py + 本脚本）, 互相不覆盖。
"""
import json, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
REPO = os.path.dirname(HERE)  # 仓库根
OUT = os.path.join(REPO, 'workers', 'api', 'src')
os.makedirs(OUT, exist_ok=True)


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def book_id(rel_path):
    return hashlib.md5(rel_path.encode()).hexdigest()[:12]


def build_books():
    oss = load(os.path.join(HERE, 'data', 'oss_manifest.json'))
    gh = load(os.path.join(HERE, 'data', 'github_manifest.json'))
    books = {}
    for rel, v in oss.items():
        if isinstance(v, dict):
            books[book_id(rel)] = {'oss': v['url'], 'size': v.get('size', 0),
                                   'ext': os.path.splitext(rel)[1].lstrip('.').lower()}
    for rel, v in gh.items():
        if isinstance(v, dict):
            bid = book_id(rel)
            e = books.setdefault(bid, {'size': v.get('size', 0),
                                       'ext': os.path.splitext(rel)[1].lstrip('.').lower()})
            e['github'] = v['url']
    return books


def build_stats():
    books = json.load(open(os.path.join(REPO, 'app', 'public', 'books.json'), encoding='utf-8'))
    n_books = len(books) if isinstance(books, list) else len(books.get('books', []))
    # N3（2026-08-18）: 哲学家数统一取 backend/data/philosophers.json（规范源），不再取 app/public 副本
    phis = json.load(open(os.path.join(HERE, 'data', 'philosophers.json'), encoding='utf-8'))
    n_authors = len(phis) if isinstance(phis, list) else len(phis.get('philosophers', phis))
    school_dir = os.path.join(REPO, 'app', 'public', 'schools', 'data')
    n_schools = len([f for f in os.listdir(school_dir) if f.startswith('school_') and f.endswith('.json')])
    return {'books': n_books, 'authors': n_authors, 'schools': n_schools}


if __name__ == '__main__':
    books = build_books()
    stats = build_stats()
    with open(os.path.join(OUT, 'books.json'), 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    # 访问统计快照（开发后台数字冻结；运行时不再更新）
    admin_stats_path = os.path.join(HERE, 'data', 'admin_stats.json')
    if os.path.exists(admin_stats_path):
        with open(admin_stats_path, encoding='utf-8') as f:
            astats = json.load(f)
        with open(os.path.join(OUT, 'admin_stats.json'), 'w', encoding='utf-8') as f:
            json.dump(astats, f, ensure_ascii=False, indent=1)
        print('admin_stats.json 快照:', astats.get('total_visits', 0), '总访问')
    else:
        print('⚠ backend/data/admin_stats.json 不存在，跳过快照')
    n_oss = sum(1 for v in books.values() if 'oss' in v)
    n_gh = sum(1 for v in books.values() if 'github' in v)
    n_both = sum(1 for v in books.values() if 'oss' in v and 'github' in v)
    print('books.json %d 本 (仅oss %d / 仅github %d / 双源 %d)' % (len(books), n_oss - n_both, n_gh - n_both, n_both))
    print('stats.json:', stats)
