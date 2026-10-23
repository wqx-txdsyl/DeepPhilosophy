"""Reject chapter blocks that currently crash the reader despite valid JSON/toc."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.mark.parametrize('block,valid', [
    ({'value': '1874年9—10月'}, False),
    ({'type': 'paragraph', 'value': '遗留正文'}, False),
    ({'type': 'text', 'value': '1874年9—10月'}, True),
    ({'type': 'html', 'value': '<p>资料表</p>'}, True),
    ({'type': 'image', 'src': '/api/books/demo/image/figure.png'}, True),
])
def test_complete_book_check_rejects_unrenderable_block(tmp_path, block, valid):
    tool = Path(__file__).resolve().parents[1] / 'tools/verify_book.py'
    copied_tool = tmp_path / 'backend/tools/verify_book.py'
    copied_tool.parent.mkdir(parents=True)
    shutil.copy2(tool, copied_tool)
    meta = {
        'title': '结构回归样本', 'author': '测试', 'chapterCount': 1,
        'chapterTitles': ['附录'],
        'toc': [{'type': 'chapter', 'title': '附录', 'index': 0}],
    }
    for prefix in ['backend/data/book_chapters/demo', 'app/public/backend/data/book_chapters/demo']:
        folder = tmp_path / prefix
        folder.mkdir(parents=True)
        (folder / 'meta.json').write_text(json.dumps(meta))
        (folder / '0.json').write_text(json.dumps({'index': 0, 'title': '附录', 'content': [block]}))
    details = tmp_path / 'app/public/book_detail'
    details.mkdir()
    (details / 'demo.json').write_text(json.dumps(meta))
    (tmp_path / 'app/public/books.json').write_text(json.dumps([{'id': 'demo', 'chapterCount': 1}]))
    result = subprocess.run([sys.executable, str(copied_tool), 'demo'], capture_output=True, text=True)
    assert (result.returncode == 0) == valid, result.stdout + result.stderr
    if not valid:
        assert '正文块具有阅读器支持的类型' in result.stdout
        assert '缺少或未知块类型' in result.stdout
