"""Source mathematics must survive notes, pictures and UTF-16 offsets intact."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('source_style_note_check', Path(__file__).resolve().parents[1] / 'tools/dp_note_check.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def check(tmp_path, styles, *, mode='source', note_styles=None):
    data = {'index': 0, 'paragraphMode': mode, 'content': [{
        'type': 'text', 'value': '𝛂P{{n:1}}[IMG]Q', 'inlineStyles': styles,
        'imgs': [{'src': '/api/books/demo/image/original.png'}],
    }], 'notes': [
        {'n': 1, 'text': 'klP见[9]。', 'inlineStyles': note_styles or [],
         'crossRefs': [{'n': 2, 'start': 4, 'end': 7}]},
        {'n': 2, 'text': '原版的第二层注释。'},
    ]}
    path = tmp_path / '0.json'
    path.write_text(json.dumps(data, ensure_ascii=False))
    return checker.check_chapter(path)


def test_source_math_and_nested_note_link_have_separate_utf16_ranges(tmp_path):
    errors, warnings, _ = check(tmp_path, [
        {'start': 2, 'end': 3, 'kind': 'sup'}, {'start': 15, 'end': 16, 'kind': 'sub'},
    ], note_styles=[{'start': 2, 'end': 3, 'kind': 'sub'}])
    assert not errors and not warnings


@pytest.mark.parametrize('kind', ['strong', 'em'])
def test_source_emphasis_can_surround_but_not_cover_a_note(tmp_path, kind):
    errors, warnings, _ = check(tmp_path, [
        {'start': 2, 'end': 3, 'kind': kind},
        {'start': 15, 'end': 16, 'kind': kind},
    ])
    assert not errors and not warnings
    errors, _, _ = check(tmp_path, [{'start': 2, 'end': 10, 'kind': kind}])
    assert any('覆盖注号' in e for e in errors)


@pytest.mark.parametrize('styles', [
    [{'start': 1, 'end': 2, 'kind': 'sub'}],  # splits the astral character
    [{'start': 2, 'end': 17, 'kind': 'sub'}],
    [{'start': -1, 'end': 1, 'kind': 'sup'}],
    [{'start': True, 'end': 3, 'kind': 'sup'}],
    [{'start': 2, 'end': 3, 'kind': 'script'}],
    [{'start': 3, 'end': 5, 'kind': 'sup'}],  # inside {{n:1}}
    [{'start': 10, 'end': 15, 'kind': 'sub'}],  # covers an image
    [{'start': 2, 'end': 3, 'kind': 'sub'}, {'start': 2, 'end': 3, 'kind': 'sup'}],
])
def test_invalid_source_style_cannot_pass_the_note_contract(tmp_path, styles):
    errors, _, _ = check(tmp_path, styles)
    assert any('inlineStyles' in e for e in errors)


def test_math_style_cannot_swallow_a_real_note_cross_reference(tmp_path):
    errors, _, _ = check(tmp_path, [], note_styles=[{'start': 4, 'end': 7, 'kind': 'sub'}])
    assert any('覆盖注号' in e for e in errors)


def test_ocr_reflow_cannot_use_original_source_character_offsets(tmp_path):
    errors, _, _ = check(tmp_path, [{'start': 2, 'end': 3, 'kind': 'sub'}], mode='ocr')
    assert any('保留源段落' in e for e in errors)
