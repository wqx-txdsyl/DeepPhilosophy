"""Nested source notes require a valid path from an actual body call."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('note_check_graph', Path(__file__).resolve().parents[1] / 'tools/dp_note_check.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def check(tmp_path, notes, body='原段{{n:11}}。'):
    path = tmp_path / '0.json'
    path.write_text(json.dumps({'index': 0, 'content': [{'type': 'text', 'value': body}], 'notes': notes}))
    return checker.check_chapter(path)


def test_a_real_body_root_reaches_nested_notes_through_valid_utf16_links(tmp_path):
    errors, warnings, info = check(tmp_path, [
        {'n': 11, 'text': '𝛂见[99]。', 'crossRefs': [{'n': 29, 'start': 3, 'end': 7, 'superscript': True}]},
        {'n': 29, 'text': '参见[7]。', 'crossRefs': [{'n': 42, 'start': 2, 'end': 5}]},
        {'n': 42, 'text': '原版的注中注。'},
    ])
    assert not errors and not warnings
    assert any('可达2条' in item for item in info)


def test_unrooted_cycles_and_self_links_cannot_hide_orphan_notes(tmp_path):
    _, warnings, _ = check(tmp_path, [
        {'n': 11, 'text': '正文所引。'},
        {'n': 29, 'text': '[42]', 'crossRefs': [{'n': 42, 'start': 0, 'end': 4}]},
        {'n': 42, 'text': '[29]', 'crossRefs': [{'n': 29, 'start': 0, 'end': 4}]},
        {'n': 99, 'text': '[99]', 'crossRefs': [{'n': 99, 'start': 0, 'end': 4}]},
    ])
    assert len(warnings) == 3
    assert all(any(f'注{n}:' in w for w in warnings) for n in [29, 42, 99])


@pytest.mark.parametrize('ref', [
    {'n': 29, 'start': 0, 'end': 2},  # incomplete printed label
    {'n': 29, 'start': 0, 'end': 99},  # out of bounds
    {'n': 29, 'start': 0, 'end': 4, 'superscript': 'yes'},
    {'n': 999, 'start': 0, 'end': 4},  # missing destination
])
def test_an_invalid_edge_cannot_suppress_the_unreachable_warning(tmp_path, ref):
    errors, warnings, _ = check(tmp_path, [
        {'n': 11, 'text': '[29]', 'crossRefs': [ref]}, {'n': 29, 'text': '无其他入口。'},
    ])
    assert errors
    assert any('注29:' in warning for warning in warnings)


def test_overlapping_second_link_does_not_create_reachability(tmp_path):
    errors, warnings, _ = check(tmp_path, [
        {'n': 11, 'text': '[29]', 'crossRefs': [
            {'n': 29, 'start': 0, 'end': 4}, {'n': 42, 'start': 0, 'end': 4},
        ]}, {'n': 29, 'text': '可达。'}, {'n': 42, 'text': '不可达。'},
    ])
    assert any('重叠' in error for error in errors)
    assert len(warnings) == 1 and '注42:' in warnings[0]
