import json
import pytest
from exercises.corpus import CorpusRepository

def test_readonly_corpus_adapter(tmp_path):
    public = tmp_path / 'app/public'
    public.mkdir(parents=True)
    book_id = '0123456789ab'
    (public/'books.json').write_text(json.dumps([{'id':book_id,'title':'测试书'}]))
    folder = tmp_path/'backend/data/book_chapters'/book_id
    folder.mkdir(parents=True)
    source = {'index':0,'title':'第一章','content':[{'type':'text','value':'正文'}]}
    path = folder/'0.json'
    path.write_text(json.dumps(source))
    original = path.read_bytes()
    repo = CorpusRepository(tmp_path)
    assert repo.read_chapter(book_id,0)['blocks'][0]['text'] == '正文'
    assert path.read_bytes() == original
    with pytest.raises(ValueError): repo.read_chapter('../bad',0)
    with pytest.raises(ValueError): repo.read_chapter(book_id,-1)
    with pytest.raises(ValueError): repo.read_chapter(book_id,True)
    path.write_text('[]')
    with pytest.raises(ValueError): repo.read_chapter(book_id,0)
