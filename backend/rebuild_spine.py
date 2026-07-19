import os,sys,hashlib,zipfile,json,re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
# 修复 Windows GBK 编码问题
if sys.platform == 'win32':
    import io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0,os.path.dirname(__file__))
from build_book_json import is_image, save_as_webp, EXTRACTED_IMG_DIR
os.makedirs(EXTRACTED_IMG_DIR,exist_ok=True)

BOOKS_DIR=r"F:/philosophy"
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CDIR=os.path.join(BASE_DIR,"data/book_chapters");DDIR=os.path.join(BASE_DIR,"data/book_detail")
os.makedirs(CDIR,exist_ok=True);os.makedirs(DDIR,exist_ok=True)
SDIR="data/book_summaries.json"
summaries=json.load(open(SDIR,'r',encoding='utf-8')) if os.path.exists(SDIR) else {}

def _body_to_blocks(body, images):
    """将 BeautifulSoup body 转为结构化块列表 [{type:'text'/'image', ...}]
    遍历所有后代节点：文本叶子 → {type:'text'}，图片 → {type:'image'}
    段落级标签 (<p><div><h1>...<li><br>) 之间自动切分为独立文本块。
    """
    BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                  'li', 'blockquote', 'pre', 'section', 'article', 'br', 'hr'}
    blocks = []
    def _flush_text():
        nonlocal pending
        if pending:
            blocks.append({'type': 'text', 'value': pending.strip()})
            pending = ''
    pending = ''
    for el in body.descendants:
        if el.name in ('script', 'style', 'nav', 'head', 'title'):
            continue
        # 段落级标签 → 切分文本块
        if el.name in BLOCK_TAGS:
            _flush_text()
            continue
        # 图片
        if el.name in ('img', 'image'):
            _flush_text()
            src = ''
            for attr in ('src', 'href', 'xlink:href', '{http://www.w3.org/1999/xlink}href'):
                v = el.get(attr, '')
                if v: src = v; break
            if src:
                blocks.append({'type': 'image', 'src': src, 'alt': el.get('alt', '') or ''})
            continue
        # 文本叶子
        if isinstance(el, NavigableString):
            text = el.strip()
            # 中文单字术语（心、虑、知）和引号（「」）都是核心内容，不能丢弃
            if text:
                if pending:
                    pending += text if text in '，。；：！？、' '「」『』""''（）' else ' ' + text
                else:
                    pending = text
    _flush_text()
    return blocks

def _rewrite_img_src(el, images):
    """将元素的图片引用从 EPUB 内部路径替换为 API 路径。
    支持 src / href / xlink:href 属性。
    """
    for attr in ('src', 'href', 'xlink:href', '{http://www.w3.org/1999/xlink}href'):
        val = el.get(attr, '')
        if not val or val.startswith(('/api/', '/covers/', 'http://', 'https://', 'data:', '#')):
            continue
        fn = Path(val).name
        if fn in images:
            el[attr] = images[fn]; return
        for k in images:
            if k.endswith(fn) or fn.endswith(k):
                el[attr] = images[k]; return

def extract(fp,bid):
    chs=[];toc=[];cover=None;images={};spine_hrefs=[]
    with zipfile.ZipFile(fp) as z:
        names=z.namelist()
        for n in names:
            if is_image(n) and '__MACOSX' not in n:
                try:
                    data=z.read(n);fn=Path(n).name;ih=hashlib.md5(data).hexdigest()[:10]
                    ofn=f'{bid}_{ih}.webp';op=os.path.join(EXTRACTED_IMG_DIR,ofn)
                    if not os.path.exists(op):save_as_webp(data,op)
                    images[fn]=f'/api/books/{bid}/image/{ofn}'
                    if 'cover' in fn.lower() and not cover:cover=images[fn]
                except:pass
        rootfile=None
        for n in names:
            if n.endswith('container.xml'):
                c=z.read(n).decode('utf-8','ignore')
                m=re.search(r'full-path="([^"]+)"',c)
                if m:rootfile=m.group(1)
                break
        if not rootfile:
            for n in names:
                if n.endswith('.opf'):rootfile=n;break
        opf_dir=str(Path(rootfile).parent) if rootfile and '/' in rootfile else ''
        if rootfile and rootfile in names:
            opf=BeautifulSoup(z.read(rootfile).decode('utf-8','ignore'),'xml')
            items={}
            for it in opf.find_all('item'):
                iid=it.get('id','');href=it.get('href','')
                if iid and href:
                    full=str(Path(opf_dir)/href).replace('\\','/') if opf_dir else href
                    items[iid]=full
            for ref in opf.find_all('itemref'):
                iid=ref.get('idref','')
                if iid in items and items[iid] not in spine_hrefs:
                    spine_hrefs.append(items[iid])
            for it in opf.find_all('item'):
                if it.get('media-type')=='application/x-dtbncx+xml':
                    ncx_href=it.get('href','')
                    ncx_path=str(Path(opf_dir)/ncx_href).replace('\\','/') if opf_dir else ncx_href
                    if ncx_path in names:
                        try:
                            ncx=BeautifulSoup(z.read(ncx_path).decode('utf-8','ignore'),'xml')
                            for np in ncx.find_all('navPoint'):
                                lab=np.find('navLabel');c=np.find('content')
                                if lab and c:
                                    src_val = c.get('src','')
                                    toc.append(type('TocEntry',(),{'_text':lab.text.strip(),'_src':src_val})())
                        except:pass
                    break
        if not spine_hrefs:
            spine_hrefs=sorted([n for n in names if n.endswith(('.xhtml','.html','.htm')) and '/nav' not in n.lower()])
        # NCX → 章节：记录每个条目的完整 src（含锚点）
        chapter_entries = []
        if toc:
            for t in toc:
                full_src = t._src if hasattr(t,'_src') else ''
                src_file = full_src.split('#')[0] if full_src else ''
                anchor = full_src.split('#')[1] if '#' in full_src else ''
                ch_title = t._text if hasattr(t,'_text') else ''
                spine_idx = None
                for si, sh in enumerate(spine_hrefs):
                    if src_file and sh.endswith(src_file.split('/')[-1]):
                        spine_idx = si; break
                chapter_entries.append({'title':ch_title,'spine_idx':spine_idx,'anchor':anchor,'full_src':full_src})
        if not chapter_entries:
            chapter_entries = [{'title':f'第{i+1}章','spine_idx':i,'anchor':''} for i in range(len(spine_hrefs))]
        # 每章内容：spine_range + 锚点切割
        merged_chapters = []
        for ci, ce in enumerate(chapter_entries):
            si = ce['spine_idx']
            if si is None: continue
            next_si = len(spine_hrefs)
            for cj in range(ci+1, len(chapter_entries)):
                ns = chapter_entries[cj]['spine_idx']
                if ns is not None and ns > si: next_si = ns; break
            merged_chapters.append({'title':ce['title'],'spine_range':list(range(si,next_si)),
                                     'anchor':ce['anchor']})
        # 处理每个章节：提取为结构化 {type:'text'/'image'} 块
        for ch_idx, mc in enumerate(merged_chapters):
            all_blocks = []
            for si in mc['spine_range']:
                href = spine_hrefs[si]
                if href not in names:
                    candidates=[n for n in names if n.endswith(href.split('/')[-1])]
                    if candidates:href=candidates[0]
                    else:continue
                try:
                    soup=BeautifulSoup(z.read(href).decode('utf-8','ignore'),'html.parser')
                    for t in soup(['script','style','nav','head']):t.decompose()
                    # 重写图片引用：EPUB 内部路径 → API 路径（原地修改 soup）
                    for tag in soup.find_all(['img','image']):
                        _rewrite_img_src(tag, images)
                    for tag in soup.find_all(attrs={'src': True}):
                        if tag.name not in ('img','image'):
                            _rewrite_img_src(tag, images)
                    body=soup.find('body') or soup
                    all_blocks.extend(_body_to_blocks(body, images))
                except:pass
            if all_blocks:
                first_spine = spine_hrefs[mc['spine_range'][0]] if mc['spine_range'] else ''
                ch={'title':mc['title'],'index':ch_idx,'content':all_blocks,'_spine_file':first_spine}
                chs.append(ch)
        # 后处理：合并分组标题页（spine 文件名是下一章的前缀，如 _00003 → _00003_0001）
        merged = []
        i = 0
        while i < len(chs):
            ch = chs[i]
            # 用 spine_range 的第一个 spine 文件名做前缀匹配
            should_merge = False
            if i+1 < len(chs) and ch.get('_spine_file') and chs[i+1].get('_spine_file'):
                curr_fn = os.path.splitext(ch['_spine_file'])[0]  # 去掉扩展名
                next_fn = os.path.splitext(chs[i+1]['_spine_file'])[0]
                # 当前文件名是下一个的前缀（如 _00003 是 _00003_0001 的前缀）
                if next_fn.startswith(curr_fn) and next_fn != curr_fn:
                    should_merge = True
            if should_merge:
                next_ch = chs[i+1]
                next_ch['title'] = ch['title'] + ' — ' + next_ch['title']
                next_ch['content'] = ch['content'] + next_ch['content']
                i += 1
            else:
                merged.append(ch)
            i += 1
        # 写入文件（重新编号 index 以匹配新顺序）
        for new_idx, ch in enumerate(merged):
            ch['index'] = new_idx
            ch.pop('_spine_file', None)
            json.dump(ch,open(os.path.join(CDIR,bid,f'{new_idx}.json'),'w',encoding='utf-8'),ensure_ascii=False)
        chs = merged
        return chs,toc,cover,images

    # fallback: 无 TOC 时的原始逻辑（同样输出结构化块）
    for hi,href in enumerate(spine_hrefs):
            if href not in names:
                candidates=[n for n in names if n.endswith(href.split('/')[-1])]
                if candidates:href=candidates[0]
                else:continue
            try:
                soup=BeautifulSoup(z.read(href).decode('utf-8','ignore'),'html.parser')
                for t in soup(['script','style','nav','head']):t.decompose()
                for tag in soup.find_all(['img','image']):
                    _rewrite_img_src(tag, images)
                ch_title = toc[hi]._text if hi < len(toc) and hasattr(toc[hi], '_text') else None
                if not ch_title:
                    title_el=soup.find(['h1','h2','h3','title'])
                    ch_title = title_el.get_text().strip()[:80] if title_el else f'第{hi+1}章'
                body=soup.find('body') or soup
                blocks=_body_to_blocks(body, images)
                if blocks:
                    idx = len(chs)
                    ch={'title':ch_title,'index':idx,'content':blocks,'_spine_file':href}
                    chs.append(ch)
                    json.dump(ch,open(os.path.join(CDIR,bid,f'{idx}.json'),'w',encoding='utf-8'),ensure_ascii=False)
            except:pass
    return chs,toc,cover,images

def process_non_epub(fp, rel, bid, ext):
    """为 PDF/TXT 创建基础 detail JSON"""
    title = Path(fp).stem
    author = rel.split('/')[1].replace('###','').strip() if '/' in rel else ''
    detail = {'bookId':bid,'title':title,'author':author,'cover':None,'toc':[],'chapterCount':0,'chapterTitles':[],
              'region':'东方' if '东方' in rel else '西方','file_type':ext}
    # 补标签和简介
    for sk in [f'{title}||{author}',f'{title}||',title]:
        if sk in summaries:
            s=summaries[sk]
            if s.get('summary'):detail['summary']=s['summary']
            if s.get('tags'):detail['tags']=s['tags']
            break
    json.dump(detail,open(os.path.join(DDIR,f'{bid}.json'),'w',encoding='utf-8'),ensure_ascii=False)
    return detail

count=0
for root,dirs,files in os.walk(BOOKS_DIR):
    for f in sorted(files):
        ext = Path(f).suffix.lower()
        fp=os.path.join(root,f);rel=os.path.relpath(fp,BOOKS_DIR).replace('\\','/');bid=hashlib.md5(rel.encode()).hexdigest()[:12]
        if ext == '.epub':
            bd=os.path.join(CDIR,bid)
            # 清理旧章节文件，避免残留
            if os.path.exists(bd):
                import shutil; shutil.rmtree(bd)
            os.makedirs(bd,exist_ok=True)
            chs,toc_entries,cover,images=extract(fp,bid)
            title=Path(f).stem;author=rel.split('/')[1].replace('###','').strip() if '/' in rel else ''
            toc_titles = [t._text if hasattr(t,'_text') else str(t) for t in toc_entries]
            meta={'bookId':bid,'title':title,'author':author,'toc':toc_titles,'cover':cover,'chapterCount':len(chs),'chapterTitles':[c['title'] for c in chs]}
            json.dump(meta,open(os.path.join(bd,'meta.json'),'w',encoding='utf-8'),ensure_ascii=False)
            detail={k:meta[k] for k in ['bookId','title','author','cover','toc','chapterCount','chapterTitles']}
            detail['toc']=toc_titles;detail['region']='东方' if '东方' in rel else '西方';detail['file_type']='epub'
            for sk in [f'{title}||{author}',f'{title}||',title]:
                s = summaries.get(sk)
                if s and s.get('summary'):detail['summary']=s['summary']
                if s and s.get('tags'):detail['tags']=s['tags'];break
            json.dump(detail,open(os.path.join(DDIR,f'{bid}.json'),'w',encoding='utf-8'),ensure_ascii=False)
            sz=sum(os.path.getsize(os.path.join(bd,x)) for x in os.listdir(bd))
            print(f'[{count+1}] {f[:40]}... spine:{len(chs)}章 {sz//1024}KB')
        elif ext in ('.pdf','.txt'):
            detail=process_non_epub(fp,rel,bid,ext.replace('.',''))
            dp = os.path.join(DDIR, f'{bid}.json')
            print(f'[{count+1}] {f[:40]}... {ext} detail:{os.path.getsize(dp)}B')
        else:
            continue
        count+=1
print(f'Done: {count}')
