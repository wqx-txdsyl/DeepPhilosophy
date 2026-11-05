"""A source formula cannot silently disappear during note migration."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('note_check', Path(__file__).resolve().parents[1] / 'tools/dp_note_check.py')
note_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(note_check)


@pytest.mark.parametrize('text,images,valid', [
    ('从克卜勒到牛顿。', [{'src': 'fraction.webp'}], False),
    ('从[IMG]到[IMG]。', [{'src': 'fraction.webp'}], False),
    ('从[IMG]到[IMG]。', [{'src': 'first.webp'}, {'src': 'second.webp'}], True),
])
def test_note_images_need_their_source_positions(tmp_path, text, images, valid):
    path = tmp_path / '32.json'
    path.write_text(json.dumps({'index': 32, 'title': '比率', 'content': [{'type': 'text', 'value': '原文{{n:2}}。'}], 'notes': [{'n': 2, 'text': text, 'imgs': images}]}))
    errors, _, _ = note_check.check_chapter(path)
    assert (not errors) == valid


@pytest.mark.parametrize('addendum,valid', [
    ('此字据文渊阁本补。', True),
    ('', False),
    ({'text': '混用对象'}, False),
    ('校记不应渲染成正文引用{{n:1}}。', False),
])
def test_original_note_and_editorial_addendum_remain_separate(tmp_path, addendum, valid):
    path=tmp_path/'0.json'
    path.write_text(json.dumps({'index':0,'content':[{'type':'text','value':'原段{{n:1}}。'}],'notes':[{'n':1,'kind':'recorder','text':'㽦','editorialAddendum':addendum}]}))
    errors,_,_=note_check.check_chapter(path)
    assert (not errors)==valid
