import sqlite3
from pathlib import Path

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, conversation TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS by_conversation ON messages(conversation, id)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def history(self, conversation, limit=12):
        with self.connect() as db:
            rows = db.execute(
                "SELECT role, content FROM messages WHERE conversation=? ORDER BY id DESC LIMIT ?",
                (conversation, limit),
            ).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

    def save_turn(self, conversation, question, answer):
        with self.connect() as db:
            db.executemany("INSERT INTO messages(conversation, role, content) VALUES (?, ?, ?)",
                           [(conversation, "user", question), (conversation, "assistant", answer)])
