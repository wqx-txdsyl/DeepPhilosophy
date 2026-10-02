"""Keep the canonical catalog check independent of the retired Android mirror."""
import importlib.util
import json
import hashlib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'dp_consistency_check.py'


def checker(tmp_path):
    spec = importlib.util.spec_from_file_location('catalog_consistency', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.BASE = str(tmp_path)
    public = tmp_path / 'app' / 'public'
    (public / 'book_detail').mkdir(parents=True)
    book = {'id': 'fixture', 'title': 'Fixture', 'author': 'Author', 'file_type': 'epub', 'chapterCount': 1}
    (public / 'books.json').write_text(json.dumps([book]))
    (public / 'book_detail' / 'fixture.json').write_text(json.dumps(book))
    chapters = tmp_path / 'backend' / 'data' / 'book_chapters' / 'fixture'
    chapters.mkdir(parents=True)
    (chapters / 'meta.json').write_text(json.dumps({'chapterCount': 1}))
    return module, book, chapters


def test_missing_retired_mirror_is_not_an_error(tmp_path):
    module, _, _ = checker(tmp_path)
    module.main()


def test_present_mirror_is_still_checked(tmp_path):
    module, book, _ = checker(tmp_path)
    mirror = tmp_path / 'app' / 'src' / 'assets' / 'books.json'
    mirror.parent.mkdir(parents=True)
    mirror.write_text(json.dumps([{**book, 'chapterCount': 2}]))
    with pytest.raises(SystemExit) as error:
        module.main()
    assert error.value.code == 1


def test_missing_canonical_chapter_meta_remains_an_error(tmp_path):
    module, _, chapters = checker(tmp_path)
    (chapters / 'meta.json').unlink()
    with pytest.raises(SystemExit) as error:
        module.main()
    assert error.value.code == 1


def lfs_pointer(payload):
    return ('version https://git-lfs.github.com/spec/v1\n'
            f'oid sha256:{hashlib.sha256(payload).hexdigest()}\n'
            f'size {len(payload)}\n').encode()


def test_lfs_metadata_is_restored_before_validation(tmp_path, monkeypatch):
    module, book, _ = checker(tmp_path)
    payload = json.dumps([book]).encode()
    path = tmp_path / 'app' / 'public' / 'books.json'
    path.write_bytes(lfs_pointer(payload))
    calls = []

    def smudge(command, **kwargs):
        calls.append(command)
        assert kwargs['env']['GIT_LFS_SKIP_SMUDGE'] == '0'
        return module.subprocess.CompletedProcess(command, 0, payload, b'')

    monkeypatch.setattr(module.subprocess, 'run', smudge)
    module.main()
    assert calls == [['git', 'lfs', 'smudge']]
    assert json.loads(path.read_text()) == [book]


def test_bad_lfs_download_does_not_replace_canonical_pointer(tmp_path, monkeypatch):
    module, book, _ = checker(tmp_path)
    path = tmp_path / 'app' / 'public' / 'books.json'
    pointer = lfs_pointer(json.dumps([book]).encode())
    path.write_bytes(pointer)
    monkeypatch.setattr(module.subprocess, 'run', lambda command, **kwargs: module.subprocess.CompletedProcess(command, 0, b'corrupt response', b''))
    with pytest.raises(ValueError, match='could not be restored'):
        module.main()
    assert path.read_bytes() == pointer
