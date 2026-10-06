import pytest
from exercises.advanced import (unique_books, top_k, chunk_text, cosine, rrf,
                                locate_quote, ResearchBudget, MemoryStore)

def test_dedup_and_sort():
    assert unique_books([{'id':'a','v':1},{'id':'a','v':2}]) == [{'id':'a','v':1}]
    assert [x['id'] for x in top_k([{'id':'b','score':1},{'id':'a','score':1}],2)] == ['a','b']
    with pytest.raises(ValueError): top_k([], -1)

def test_chunk_positions_and_overlap():
    text = 'abcdefghij'
    chunks = chunk_text(text, 5, 2)
    assert [x['start'] for x in chunks] == [0, 3, 6]
    assert all(text[x['start']:x['end']] == x['text'] for x in chunks)
    assert chunks[-1]['end'] == len(text)
    assert chunk_text('') == []
    with pytest.raises(ValueError): chunk_text(text, 3, 3)

def test_retrieval_math():
    assert cosine([1,0],[1,0]) == 1
    assert cosine([1,0],[0,1]) == 0
    assert cosine([0,0],[0,1]) == 0
    assert rrf([['a','b'],['b','c']])[0] == 'b'
    assert rrf([['a','a','b']]) == ['a','b']

def test_quote_is_exact():
    source = '自由与责任需要分别讨论。'
    result = locate_quote(source, '责任')
    assert source[result['start']:result['end']] == '责任'
    assert locate_quote(source, '自由不需要责任') is None
    assert locate_quote(source, '') is None

def test_budget_reserves_reads():
    budget = ResearchBudget(search_limit=1, read_limit=1)
    budget.search(['a'])
    with pytest.raises(ValueError): budget.search(['b'])
    with pytest.raises(ValueError): budget.read('unknown')
    budget.read('a')
    with pytest.raises(ValueError): budget.read('a')

def test_memory_is_user_scoped_and_deletable(tmp_path):
    store = MemoryStore(tmp_path / 'memory.sqlite3')
    store.put('alice','style','简短','message-1')
    assert store.get('bob','style') is None
    store.put('bob','style','详细','message-2')
    store.forget('alice','style')
    assert store.get('alice','style') is None
    assert store.get('bob','style') == '详细'
