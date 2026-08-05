"""从 EPUB 提取章节——保留原始 HTML 内容"""
import zipfile, os, json, re, sys, hashlib
from pathlib import Path
from bs4 import BeautifulSoup

def extract_one(epub_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(epub_path, 'r') as z:
        names = z.namelist()
        rootfile = None
        for n in names:
            if n.endswith('container.xml'):
                c = z.read(n).decode('utf-8', errors='ignore')
                m = re.search(r'full-path="([^"]+)"', c)
                if m: rootfile = m.group(1)
                break
        if not rootfile:
            for n in names:
                if n.endswith('.opf'): rootfile = n; break
        if not rootfile: return False, 'no opf'

        opf_dir = str(Path(rootfile).parent) if '/' in rootfile else ''
        opf = BeautifulSoup(z.read(rootfile).decode('utf-8', errors='ignore'), 'xml')

        items = {}
        for it in opf.find_all('item'):
            iid, href = it.get('id', ''), it.get('href', '')
            if iid and href:
                full = str(Path(opf_dir) / href).replace('\\', '/') if opf_dir else href
                items[iid] = full

        spine_hrefs = []
        for ref in opf.find_all('itemref'):
            iid = ref.get('idref', '')
            if iid in items and items[iid] not in spine_hrefs:
                spine_hrefs.append(items[iid])

        # 读 NCX 获取真实章节标题
        toc_entries = []
        for it in opf.find_all('item'):
            if it.get('media-type') == 'application/x-dtbncx+xml':
                ncx_href = it.get('href', '')
                ncx_path = str(Path(opf_dir) / ncx_href).replace('\\', '/') if opf_dir else ncx_href
                if ncx_path in names:
                    try:
                        ncx = BeautifulSoup(z.read(ncx_path).decode('utf-8', errors='ignore'), 'xml')
                        for np in ncx.find_all('navPoint'):
                            lab = np.find('navLabel')
                            c = np.find('content')
                            if lab and c:
                                toc_entries.append({
                                    'title': lab.text.strip(),
                                    'src': c.get('src', '')
                                })
                    except:
                        pass
                break

        if not spine_hrefs:
            spine_hrefs = sorted([n for n in names if n.endswith(('.xhtml','.html','.htm')) and '/nav' not in n.lower()])
        if not spine_hrefs: return False, 'no spine'

        title_el = opf.find('dc:title')
        title = title_el.get_text().strip() if title_el else Path(epub_path).stem

        # 用 NCX 标题映射 spine
        from urllib.parse import unquote
        spine_titles = {}
        for te in toc_entries:
            src_file = te['src'].split('#')[0] if te['src'] else ''
            src_decoded = unquote(src_file)
            for si, sh in enumerate(spine_hrefs):
                if src_file and (sh.endswith(src_file.split('/')[-1]) or sh.endswith(src_decoded.split('/')[-1])):
                    spine_titles[si] = te['title']
                    break

        chapter_idx = 0
        for href in spine_hrefs:
            if href not in names: continue
            raw_html = z.read(href).decode('utf-8', errors='ignore')
            soup = BeautifulSoup(raw_html, 'html.parser')

            body = soup.find('body')
            if not body: continue

            for tag in body.find_all(['script', 'style']):
                tag.decompose()
            body_html = str(body)

            # 优先 NCX 标题，回退 HTML 标题
            ch_title = spine_titles.get(chapter_idx)
            if not ch_title:
                for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'title']):
                    t = h.get_text().strip()
                    if not t or len(t) < 2: continue
                    if re.match(r'^[0-9a-fA-F]{4,}$', t): continue
                    if re.match(r'^[a-zA-Z0-9_\-\.]+$', t) and len(t) > 10: continue
                    if t in ('文硕阁', '目录', '封面', 'Cover', '未知', '书名', '版权', '版权页', '版权信息'): continue
                    # 如果跟书名一样，跳过（有些 EPUB 每章 h1 都是书名）
                    if t == title or title in t[:len(title)]: continue
                    ch_title = t[:80]; break
            if not ch_title:
                ch_title = '第{}章'.format(chapter_idx + 1)

            ch = {'title': ch_title, 'index': chapter_idx, 'content': [{'type': 'html', 'value': body_html}]}
            with open(os.path.join(output_dir, '{}.json'.format(chapter_idx)), 'w', encoding='utf-8') as f:
                json.dump(ch, f, ensure_ascii=False)
            chapter_idx += 1

        # 从章节文件收集标题
        ch_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.json') and f != 'meta.json'],
                          key=lambda x: int(x.replace('.json', '')))
        ch_titles = []
        for cf in ch_files:
            with open(os.path.join(output_dir, cf), 'r', encoding='utf-8') as f:
                ch_titles.append(json.load(f).get('title', '?'))

        meta = {
            'bookId': os.path.basename(output_dir), 'title': title,
            'chapterCount': chapter_idx, 'chapterTitles': ch_titles,
        }
        with open(os.path.join(output_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False)
        return True, chapter_idx

if __name__ == '__main__':
    ok, info = extract_one(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'test_chapters')
    print('OK: {} chapters'.format(info) if ok else 'FAIL: ' + info)
