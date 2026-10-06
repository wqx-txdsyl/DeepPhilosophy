"""Audit real catalogue→chapter→excerpt coordinates without modifying the corpus."""
import argparse,json,sys,time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.backend.resolve()))
    import deep_agent_tools as deep
    from routes import agent_core as core
    started=time.monotonic();issues=[];reader_issues=[];count=0
    for book in core.get_books():
        rows=[];offset=0
        while True:
            result=deep.get_book_detail({'book_id':book['id'],'limit':40,'offset':offset})
            rows+=result.get('chapters',[])
            if not result.get('has_more'):break
            offset=result['next_offset']
        folder=core.CHAPTERS_DIR/book['id']
        actual={int(p.stem):p for p in folder.glob('*.json') if p.stem.isdecimal() and p.stem==str(int(p.stem))}
        declared=(core.chapter_meta(book['id']) or {}).get('chapterCount',0)
        for index in actual:
            if index>=int(declared or 0):reader_issues.append({'book_id':book['id'],'index':index,'kind':'OUTSIDE_WEBSITE_CHAPTER_RANGE'})
        if {r['index'] for r in rows}!=set(actual):issues.append({'book_id':book['id'],'kind':'INDEX_SET_MISMATCH','returned':[r['index'] for r in rows],'actual':sorted(actual)})
        for row in rows:
            count+=1;p=actual.get(row['index'])
            if not p:continue
            try:source=json.loads(p.read_text())
            except ValueError:continue
            if row['title']!=source.get('title',''):issues.append({'book_id':book['id'],'index':row['index'],'kind':'TITLE_MISMATCH'})
    cases=[('analects_exact',{'query':'人不知而不愠','author':'孔子'}),
           ('kant_phrase',{'query':'知性为自然立法','book_id':'8c0c6955c793'}),
           ('hume_phrase',{'query':'因果必然性','author':'休谟'}),
           ('kant_multi',{'query':'自然立法 知性 规律','book_id':'8c0c6955c793'}),
           ('aristotle_friendship',{'query':'友爱 有用','author':'亚里士多德'}),
           ('fabricated',{'query':'阿布拉卡达不存在的哲学概念','author':'康德'})]
    searches=[]
    for cid,query in cases:
        start=time.monotonic();found=deep.search_books({**query,'limit':3});hits=[]
        for hit in found.get('results',[]):
            if not hit.get('read_args'):continue
            read=deep.get_chapter(hit['read_args'])
            source=core.read_chapter(hit['book_id'],hit['chapter_idx'])
            valid=bool(source and not read.get('error') and read.get('text')==source['text'][read['excerpt_start']:read['excerpt_end']])
            hits.append({'book_id':hit['book_id'],'book':hit.get('book_title'),'chapter':hit.get('chapter_title'),'index':hit['chapter_idx'],
                         'author':hit.get('author'),'match_type':hit.get('match_type'),'read_roundtrip_exact':valid,'snippet':hit.get('snippet')})
        searches.append({'id':cid,'query':query,'method':found.get('method'),'hits':hits,'seconds':round(time.monotonic()-start,3)})
    receipt={'books':len(core.get_books()),'directory_entries':count,'issues':issues,'reader_issues':reader_issues,'queries':searches,'seconds':round(time.monotonic()-started,3)}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps({'books':receipt['books'],'entries':count,'directory_issues':len(issues),'query_hits':{q['id']:len(q['hits']) for q in searches},'seconds':receipt['seconds']},ensure_ascii=False))

if __name__=='__main__':main()
