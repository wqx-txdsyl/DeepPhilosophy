"""
从 Project Gutenberg 搜索并下载 EPUB（公共领域）
用法: python download_gutenberg.py --search "理想国" --author "柏拉图"
      python download_gutenberg.py --id 1497 --title "理想国" --author "柏拉图"
"""
import os, sys, io, json, re, hashlib, shutil, urllib.request, urllib.parse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(BASE, '..', 'app', 'public', 'downloads')
os.makedirs(BOOKS_DIR, exist_ok=True)

GUTENDEX_API = 'https://gutendex.com/books'
GUTENBERG_BASE = 'https://www.gutenberg.org'

def search_books(query, lang='zh'):
    """搜索 Gutenberg 书籍"""
    params = urllib.parse.urlencode({'search': query, 'languages': lang})
    url = f'{GUTENDEX_API}?{params}'
    print(f'搜索: {url}')
    req = urllib.request.Request(url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data.get('results', [])

def search_books_all_langs(query):
    """搜索所有语言"""
    params = urllib.parse.urlencode({'search': query})
    url = f'{GUTENDEX_API}?{params}'
    print(f'搜索: {url}')
    req = urllib.request.Request(url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data.get('results', [])

def get_book_formats(book_id):
    """获取书籍的所有下载格式"""
    url = f'{GUTENDEX_API}/{book_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    formats = data.get('formats', {})
    return formats, data

def download_epub(book_id, title, author):
    """下载 EPUB 文件"""
    formats, meta = get_book_formats(book_id)

    # 找 EPUB 链接
    epub_url = None
    for mime, url in formats.items():
        if 'epub' in mime or url.endswith('.epub'):
            epub_url = url
            break

    if not epub_url:
        # 尝试 no-images 版本
        for k, v in formats.items():
            if 'epub' in k.lower():
                epub_url = v
                break

    if not epub_url:
        print(f'  无 EPUB 格式。可用格式: {list(formats.keys())}')
        return None

    # 生成文件名
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:60]
    out_name = f'{safe_title}.epub'
    out_path = os.path.join(BOOKS_DIR, out_name)

    # 下载
    print(f'  下载: {epub_url}')
    req = urllib.request.Request(epub_url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    with open(out_path, 'wb') as f:
        f.write(data)
    sz = len(data) / 1024
    print(f'  保存: {out_path} ({sz:.0f} KB)')

    # 生成 book_id
    book_id = hashlib.md5(data[:1024]).hexdigest()[:12]

    # 复制到 F:/philosophy 对应作者目录
    philo_dir = os.path.join('F:', os.sep, 'philosophy', '西方', author)
    os.makedirs(philo_dir, exist_ok=True)
    philo_path = os.path.join(philo_dir, out_name)
    shutil.copy2(out_path, philo_path)
    print(f'  复制到: {philo_path}')

    return book_id, out_path, philo_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='从 Gutenberg 下载 EPUB')
    parser.add_argument('--id', type=int, help='Gutenberg 书籍 ID')
    parser.add_argument('--search', help='搜索关键词')
    parser.add_argument('--title', help='书名')
    parser.add_argument('--author', help='作者', default='')
    parser.add_argument('--lang', help='语言', default='')
    args = parser.parse_args()

    if args.id:
        # 直接下载指定 ID
        formats, meta = get_book_formats(args.id)
        print(f"标题: {meta.get('title', '?')}")
        print(f"作者: {', '.join(a.get('name','?') for a in meta.get('authors',[]))}")
        print(f"语言: {', '.join(meta.get('languages',[]))}")
        print(f"格式: {list(formats.keys())}")
        title = args.title or meta.get('title', f'book_{args.id}')
        author = args.author or meta.get('authors', [{}])[0].get('name', '')
        book_id, out_path, philo_path = download_epub(args.id, title, author)
        if book_id:
            print(f'\n下载完成! book_id={book_id}')
            print(f'运行: python backend/rebuild_spine.py')
    elif args.search:
        # 搜索
        if args.lang:
            results = search_books(args.search, args.lang)
        else:
            results = search_books_all_langs(args.search)

        print(f'\n找到 {len(results)} 本:')
        for i, r in enumerate(results[:20]):
            title = r.get('title', '?')
            authors = ', '.join(a.get('name', '?') for a in r.get('authors', []))
            langs = ', '.join(r.get('languages', []))
            gid = r.get('id', '?')
            formats = ', '.join(r.get('formats', {}).keys())
            has_epub_flag = any('epub' in k.lower() or v.endswith('.epub') for k, v in r.get('formats', {}).items())
            print(f'  [{i}] [{gid}] {title[:60]} — {authors} ({langs}) {"EPUB" if has_epub_flag else ""}')
    else:
        parser.print_help()
