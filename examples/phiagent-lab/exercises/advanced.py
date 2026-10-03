"""Reference answers for retrieval, evidence, budgets, and user-scoped memory."""
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import math
import sqlite3

def unique_books(records):
    seen, output = set(), []
    for record in records:
        if record['id'] not in seen:
            seen.add(record['id'])
            output.append(dict(record))
    return output

def top_k(scores, k):
    if k < 0:
        raise ValueError('k must be nonnegative')
    return sorted(scores, key=lambda row: (-row['score'], row['id']))[:k]

def chunk_text(text, size=200, overlap=30):
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError('require size > overlap >= 0')
    result = []
    for start in range(0, len(text), size - overlap):
        end = min(start + size, len(text))
        result.append({'start': start, 'end': end, 'text': text[start:end]})
        if end == len(text):
            break
    return result

def cosine(a, b):
    if len(a) != len(b):
        raise ValueError('dimension mismatch')
    length = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    return sum(x*y for x, y in zip(a, b)) / length if length else 0.0

def rrf(rankings, k=60):
    if k <= 0:
        raise ValueError('k must be positive')
    scores = defaultdict(float)
    for ranking in rankings:
        seen = set()
        for rank, item_id in enumerate(ranking, 1):
            if item_id not in seen:
                scores[item_id] += 1 / (k + rank)
                seen.add(item_id)
    return sorted(scores, key=lambda item_id: (-scores[item_id], item_id))

def locate_quote(source, quote):
    if not quote:
        return None
    start = source.find(quote)
    if start < 0:
        return None
    return {'start': start, 'end': start + len(quote), 'text': source[start:start + len(quote)],
            'source_hash': hashlib.sha256(source.encode()).hexdigest()}

@dataclass
class ResearchBudget:
    search_limit: int = 2
    read_limit: int = 3
    searches: int = 0
    reads: int = 0
    located: set[str] = field(default_factory=set)

    def search(self, found_ids):
        if self.searches >= self.search_limit:
            raise ValueError('search budget exhausted')
        self.searches += 1
        self.located.update(found_ids)

    def read(self, source_id):
        if source_id not in self.located:
            raise ValueError('source has not been located')
        if self.reads >= self.read_limit:
            raise ValueError('read budget exhausted')
        self.reads += 1

class MemoryStore:
    """Callers must provide server-authenticated user_id, not client assertions."""
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS memories (
                user_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
                source_message_id TEXT NOT NULL,
                PRIMARY KEY(user_id, key))''')

    def connect(self):
        return sqlite3.connect(self.path)

    def put(self, user_id, key, value, source_message_id):
        with self.connect() as db:
            db.execute('''INSERT INTO memories VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, key) DO UPDATE SET
                value=excluded.value, source_message_id=excluded.source_message_id''',
                (user_id, key, value, source_message_id))

    def get(self, user_id, key):
        with self.connect() as db:
            row = db.execute('SELECT value FROM memories WHERE user_id=? AND key=?', (user_id, key)).fetchone()
        return row[0] if row else None

    def forget(self, user_id, key):
        with self.connect() as db:
            db.execute('DELETE FROM memories WHERE user_id=? AND key=?', (user_id, key))
