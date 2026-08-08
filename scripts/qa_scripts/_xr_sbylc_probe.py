# -*- coding: utf-8 -*-
"""#118 思辨与立场 probe：EPUB spine 138 文件标题树 + 字数 + img 数（人工核对用）"""
import json, os, re, zipfile, hashlib
from bs4 import BeautifulSoup

EPUB = 'F:/philosophy/西方/理查德·保罗/思辨与立场：生活中无处不在的批判性思维工具.epub'
BID = '9fb1dbc22de1'

z = zipfile.ZipFile(EPUB)
opf = z.read('OEBPS/content.opf').decode('utf-8', 'ignore')
manif = {}
for m in re.finditer(r'<item[^>]*?/?>', opf):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf)

# 图片映射
def is_image(n):
    fn = n.split('/')[-1].lower()
    return fn.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')) and '__MACOSX' not in n

images = {}
for n in z.namelist():
    if is_image(n):
        data = z.read(n)
        ih = hashlib.md5(data).hexdigest()[:10]
        images[n.split('/')[-1]] = f'/api/books/{BID}/image/{BID}_{ih}.webp'

def clean_title(t):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return t

total_chars = 0
for rid in spine:
    href = manif.get(rid)
    if not href:
        print('?? no href for', rid)
        continue
    raw = z.read('OEBPS/' + href).decode('utf-8', 'ignore')
    soup = BeautifulSoup(raw, 'html.parser')
    # h 标题树（按出现顺序）
    heads = [(el.name, clean_title(el.get_text())) for el in soup.find_all(['h1', 'h2', 'h3', 'h4'])]
    txt = clean_title(soup.get_text())
    imgs = soup.find_all('img')
    # 正文长度（去标题去图注？粗略：全部文本）
    body = soup.body if soup.body else soup
    nchars = len(re.sub(r'\s+', '', body.get_text() or ''))
    total_chars += nchars
    head_str = ' | '.join(f'{n}:{t[:30]}' for n, t in heads) if heads else '(无h标题)'
    print(f'{href[-13:-5]} {nchars:6d} img:{len(imgs)} {head_str}')
print('总字符(含全部文本):', total_chars)
