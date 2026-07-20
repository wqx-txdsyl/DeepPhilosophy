"""Health check and stats routes"""
import os
from datetime import datetime
from fastapi import APIRouter
from services.book_scanner import scan_books, is_valid_author

router = APIRouter()

@router.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.2.0", "timestamp": datetime.now().isoformat()}

@router.get("/api/stats")
async def get_stats():
    books = scan_books()
    authors_set = set()
    for b in books:
        author = b.get("author", "")
        if author and "合集" not in author and "概述" not in author:
            authors_set.add(author)
    import config
    knowledge_dir = config.KNOWLEDGE_DIR
    if os.path.isdir(knowledge_dir):
        for region_name in ["东方", "西方"]:
            region_path = os.path.join(knowledge_dir, region_name)
            if os.path.isdir(region_path):
                for author_dir in os.listdir(region_path):
                    author_clean = author_dir.replace("###合集&概述###", "合集&概述")
                    if author_clean and "合集" not in author_clean and author_clean not in authors_set:
                        authors_set.add(author_clean)
    from db import PHILOSOPHER_COUNT, PHILOSOPHERS
    philosopher_count = max(len(authors_set), PHILOSOPHER_COUNT)
    philosopher_count = max(philosopher_count, len(authors_set | set(PHILOSOPHERS.keys())))
    school_names = set()
    for sub in ["static/schools", "data"]:
        d = os.path.join(os.path.dirname(os.path.dirname(__file__)), sub)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.startswith("school_") and f.endswith(".json"):
                    school_names.add(f)
    return {"books": len(books), "authors": philosopher_count, "schools": len(school_names)}
