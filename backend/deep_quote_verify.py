"""Deterministic quote lookup and context read in a specifically identified book."""
import re, hashlib
from urllib.parse import quote
from deep_agent_tools import _required_text, _book_lookup, _chapters, _material_role
from routes import agent_core as core
from routes.agent_tools_retrieval import _cite_label


def verify_quote(args):
    identifier,error=_required_text(args,'book_id')
    if error:return error
    quotation=args.get('quote')
    if not isinstance(quotation,str) or not quotation.strip() or len(quotation)>2000:
        return {'error':'INVALID_QUOTATION','message':'quote须为1至2000字符的原句。'}
    quotation=quotation.strip()
    book,error=_book_lookup(identifier)
    if error:return error
    bid=book['id'];meta=core.chapter_meta(bid) or {};chapters=list(_chapters(book))
    if not chapters or not any(text.strip() for _,_,text in chapters):
        return {'error':'NO_LOCAL_TEXT','book_id':bid,'book_title':book.get('title'),'message':'书目存在，但没有可核验的本地正文，不能判定原句存在或不存在。'}
    limit=core._int_arg(args,'limit',3,1,5);matches=[];count=0;unreadable=[]
    for idx,title,text in chapters:
        if not text.strip():unreadable.append(idx);continue
        locations=[(m.start(),m.end(),'exact') for m in re.finditer(re.escape(quotation),text)]
        if not locations:
            needle=''.join(quotation.split())
            positions=[i for i,c in enumerate(text) if not c.isspace()]
            compact=''.join(text[i] for i in positions)
            locations=[(positions[m.start()],positions[m.end()-1]+1,'whitespace_only') for m in re.finditer(re.escape(needle),compact)] if needle else []
        count+=len(locations)
        for start,end,mode in locations:
            role=_material_role(book['title'],title)
            priority={'UNCLASSIFIED':0,'EDITORIAL_CANDIDATE':1,'PARATEXT_CANDIDATE':2,'COMMENTARY_CANDIDATE':3}[role]
            if len(matches)>=limit and priority>=matches[-1]['_priority']:break
            left=max(0,start-200);right=min(len(text),end+240)
            matches.append({'book_id':bid,'book_title':book['title'],'author':book.get('author',''),
                'chapter_idx':idx,'title':title,'citation_label':_cite_label(book['title'],title),
                'matched_text':text[start:end],'match_start':start,'match_end':end,'match_mode':mode,
                'text':text[left:right],'excerpt_start':left,'excerpt_end':right,'chapter_text_length':len(text),
                'material_role':role,'role_basis':'title_heuristic_not_academic_review','_priority':priority,
                'reader_coordinate_valid':idx<int(meta.get('chapterCount') or 0),'evidence_scope':'verified_quote_context'})
            matches.sort(key=lambda m:m['_priority'])
            matches=matches[:limit]
    texts = {idx:text for idx,_,text in chapters}
    for match in matches:
        match.pop('_priority',None)
        match.update(chapter_content_sha256=hashlib.sha256(texts[match['chapter_idx']].encode()).hexdigest(),
                     text_origin='normalized_library_text',layout_verified=False)
        if match['reader_coordinate_valid']:
            match['reader_url']=f'https://deepphilosophy.top/reader/{quote(bid,safe="")}?ch={match["chapter_idx"]}'
            match['reader_url_scope']='chapter'
    return {'book_id':bid,'book_title':book['title'],'quote':quotation,'found':count>0,'match_count':count,
        'verification_status':'matched_in_this_library' if count else 'not_matched_in_this_library',
        'author_attribution_verdict':'requires_context' if count else 'undetermined',
        'matches':matches,'matches_omitted':max(0,count-len(matches)),
        'coverage':{'scope':'present_local_chapter_files','unit':'本库文本单元，可含序言和目录，不等于传统篇章数','searched_chapters':len(chapters),'unreadable_indices':unreadable,
                    'declared_chapters':meta.get('chapterCount'),'directory_consistent':{i for i,_,_ in chapters}==set(range(int(meta.get('chapterCount') or 0)))},
        'note':'仅核对本库现有版本，不作语义近似替代。whitespace_only只忽略排版空白，matched_text保留实际原文。程序扫描报告的范围，但模型只读到了matches.text给出的上下文。命中不自动证明说话者就是作者；请区分正文、对话角色与译注。未命中不能排除标点、异写、译本或未收录部分，也不支持未经核验的词源或年代断言。'}
