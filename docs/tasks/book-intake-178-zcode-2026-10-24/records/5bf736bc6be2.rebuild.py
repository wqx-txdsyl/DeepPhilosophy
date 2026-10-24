# -*- coding: utf-8 -*-
"""重建《作为意志和表象的世界》(5bf736bc6be2) — 63章完整版。

来源（同一"意欲"译本家族，两册合成完整作品）：
  A. 叔本华哲学经典套装（d0c5ade4fcbd 17-23）：生平及哲学/译者的话/英译者序言/卷一~卷四
  B. 作为意欲和表象的世界（第2卷）（e2845fe17764 0-55）：译者序/题词×4/第1-50章/人名索引
现行单章数据40.5万字 ⊆ raw 74.4万字（卷2缺失约34万字，本次补全）。
卷内纯数字块为原书章号 → toc section「第N章」。
"""
import json
import os
import re

BASE = '/Users/sen/Downloads/raw/incoming-codex/_source-assets/local-reader-baseline-20261023'
OUT_DIR = 'backend/data/book_chapters/5bf736bc6be2'
SOURCES = [( 'd0c5ade4fcbd', list(range(17, 24))), ('e2845fe17764', list(range(0, 56)))]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    meta_toc = []
    chapter_titles = []
    sec_total = 0
    idx = 0
    total_chars = 0
    for book, files in SOURCES:
        for fi in files:
            src = json.load(open(f'{BASE}/{book}/{fi}.json', encoding='utf-8'))
            title = src['title'].strip()
            content = [b for b in src['content'] if isinstance(b, dict) and b.get('type') == 'text' and b.get('value')]
            ch = dict(index=idx, title=title, paragraphMode='source', content=content)
            with open(f'{OUT_DIR}/{idx}.json', 'w', encoding='utf-8') as f:
                json.dump(ch, f, ensure_ascii=False, indent=1)
            chapter_titles.append(title)
            meta_toc.append(dict(type='chapter', title=title, index=idx, level=1))
            if title.startswith('卷'):
                for bi, b in enumerate(content):
                    v = b['value'].strip()
                    if re.fullmatch(r'\d{1,2}', v):
                        meta_toc.append(dict(type='section', title=f'第{int(v)}章', index=idx, sec=bi, level=2))
                        sec_total += 1
            total_chars += sum(len(b['value']) for b in content)
            idx += 1

    meta = dict(
        bookId='5bf736bc6be2',
        title='作为意志和表象的世界',
        author='阿图尔·叔本华',
        region='西方',
        chapterCount=idx,
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f'chapters: {idx}, sections: {sec_total}, chars: {total_chars}')
    for t in chapter_titles[:12]:
        print(' -', t)


if __name__ == '__main__':
    main()
