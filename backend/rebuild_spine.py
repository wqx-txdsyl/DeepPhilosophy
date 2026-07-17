import os,sys,hashlib,zipfile,json,re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
sys.path.insert(0,os.path.dirname(__file__))
from build_book_json import is_image, save_as_webp, EXTRACTED_IMG_DIR
os.makedirs(EXTRACTED_IMG_DIR,exist_ok=True)

BOOKS_DIR=r"F:/philosophy"
CDIR="data/book_chapters";DDIR="data/book_detail"
os.makedirs(CDIR,exist_ok=True);os.makedirs(DDIR,exist_ok=True)
SDIR="data/book_summaries.json"
summaries=json.load(open(SDIR,'r',encoding='utf-8')) if os.path.exists(SDIR) else {}

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
                                     'anchor':ce['anchor'],'next_anchor':chapter_entries[ci+1]['anchor'] if ci+1<len(chapter_entries) and chapter_entries[ci+1]['spine_idx']==si else ''})
        # 处理每个章节：完整 spine 文件内容，不切割
        for ch_idx, mc in enumerate(merged_chapters):
            all_html = []
            for si in mc['spine_range']:
                href = spine_hrefs[si]
                if href not in names:
                    candidates=[n for n in names if n.endswith(href.split('/')[-1])]
                    if candidates:href=candidates[0]
                    else:continue
                try:
                    soup=BeautifulSoup(z.read(href).decode('utf-8','ignore'),'html.parser')
                    for t in soup(['script','style','nav','head']):t.decompose()
                    body=soup.find('body') or soup
                    all_html.append(str(body))
                except:pass
            if all_html:
                full = '\n'.join(all_html)
                ch={'title':mc['title'],'index':ch_idx,'content':[{'type':'html','value':full}]}
                chs.append(ch)
                json.dump(ch,open(os.path.join(CDIR,bid,f'{len(chs)-1}.json'),'w',encoding='utf-8'),ensure_ascii=False)
        return chs,toc,cover,images

    # fallback: 无 TOC 时的原始逻辑
    for hi,href in enumerate(spine_hrefs):
            if href not in names:
                candidates=[n for n in names if n.endswith(href.split('/')[-1])]
                if candidates:href=candidates[0]
                else:continue
            try:
                soup=BeautifulSoup(z.read(href).decode('utf-8','ignore'),'html.parser')
                for t in soup(['script','style','nav','head']):t.decompose()
                # 优先用 TOC 标题
                ch_title = toc[hi]._text if hi < len(toc) and hasattr(toc[hi], '_text') else None
                if not ch_title:
                    title_el=soup.find(['h1','h2','h3','title'])
                    ch_title = title_el.get_text().strip()[:80] if title_el else f'第{hi+1}章'
                body=soup.find('body') or soup
                blocks=[]
                for child in body.children if body else []:
                    if isinstance(child,NavigableString):
                        t=str(child).strip()
                        if t:blocks.append({'type':'text','value':t})
                    elif hasattr(child,'name') and child.name in ('p','div','li','blockquote','h1','h2','h3','h4','h5','h6','pre'):
                        t=child.get_text().strip()
                        if t and len(t)>1:blocks.append({'type':'text','value':t})
                    elif hasattr(child,'name') and child.name=='img':
                        src=child.get('src','');fn=Path(src).name if src else ''
                        for k in images:
                            if k.endswith(fn):blocks.append({'type':'image','src':images[k]});break
                if blocks:
                    ch={'title':ch_title,'index':hi,'content':blocks}
                    chs.append(ch)
                    json.dump(ch,open(os.path.join(CDIR,bid,f'{len(chs)-1}.json'),'w',encoding='utf-8'),ensure_ascii=False)
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
            bd=os.path.join(CDIR,bid);os.makedirs(bd,exist_ok=True)
            chs,toc_entries,cover,images=extract(fp,bid)
            title=Path(f).stem;author=rel.split('/')[1].replace('###','').strip() if '/' in rel else ''
            toc_titles = [t._text if hasattr(t,'_text') else str(t) for t in toc_entries]
            meta={'bookId':bid,'title':title,'author':author,'toc':toc_titles,'cover':cover,'chapterCount':len(chs),'chapterTitles':[c['title'] for c in chs]}
            json.dump(meta,open(os.path.join(bd,'meta.json'),'w',encoding='utf-8'),ensure_ascii=False)
            detail={k:meta[k] for k in ['bookId','title','author','cover','toc','chapterCount','chapterTitles']}
            detail['toc']=toc_titles;detail['region']='东方' if '东方' in rel else '西方';detail['file_type']='epub'
            for sk in [f'{title}||{author}',f'{title}||',title]:
                if sk in summaries:s=summaries[sk]
                if s.get('summary'):detail['summary']=s['summary']
                if s.get('tags'):detail['tags']=s['tags'];break
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
