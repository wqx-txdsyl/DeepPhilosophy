"""Read-only adapter for DeepPhilosophy. Does not modify chapters or indexes."""
import argparse
import hashlib
import json
from pathlib import Path
import re

class CorpusRepository:
    def __init__(self, root):
        self.root = Path(root).resolve()
        rows = json.loads((self.root / 'app/public/books.json').read_text(encoding='utf-8'))
        if not isinstance(rows, list):
            raise ValueError('books.json must be a list')
        self.books = {str(row['id']): row for row in rows}
        self.chapters = (self.root / 'backend/data/book_chapters').resolve()

    def list_books(self):
        return list(self.books.values())

    def get_book(self, book_id):
        if book_id not in self.books or not re.fullmatch(r'[0-9a-f]{10,16}', book_id):
            raise ValueError('unknown book id')
        return dict(self.books[book_id])

    def read_chapter(self, book_id, chapter_index):
        book = self.get_book(book_id)
        if type(chapter_index) is not int or chapter_index < 0:
            raise ValueError('invalid chapter index')
        path = (self.chapters / book_id / f'{chapter_index}.json').resolve()
        if not path.is_relative_to(self.chapters):
            raise ValueError('chapter outside corpus')
        row = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(row, dict) or row.get('index') != chapter_index or not isinstance(row.get('content'), list):
            raise ValueError('invalid chapter format')
        blocks = []
        for index, block in enumerate(row['content']):
            if not isinstance(block, dict):
                raise ValueError('invalid block format')
            if block.get('type') != 'text':
                continue
            text = block.get('value')
            if not isinstance(text, str):
                raise ValueError('text block must contain string value')
            blocks.append({'id':f'{book_id}-{chapter_index}-{index}', 'book_id':book_id,
                           'chapter_index':chapter_index, 'block_index':index, 'text':text,
                           'content_hash':hashlib.sha256(text.encode()).hexdigest()})
        return {'book':book.get('title'), 'title':row.get('title'), 'blocks':blocks}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, help='DeepPhilosophy repository root')
    parser.add_argument('--limit', type=int, default=3)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    repository = CorpusRepository(args.root)
    report = []
    for book in repository.list_books():
        if len(report) >= args.limit:
            break
        path = repository.chapters / str(book['id']) / '0.json'
        if not path.is_file():
            continue
        try:
            chapter = repository.read_chapter(str(book['id']), 0)
            report.append({'book_id':book['id'], 'title':book.get('title'),
                           'blocks':len(chapter['blocks']), 'status':'read'})
        except (ValueError, OSError) as exc:
            report.append({'book_id':book['id'], 'status':'error', 'error_type':type(exc).__name__})
    print(json.dumps({'scope':'sample only, not a full corpus audit', 'books':len(repository.books),
                      'sample':report}, ensure_ascii=False, indent=2))
    if not report or any(row['status'] != 'read' for row in report):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
