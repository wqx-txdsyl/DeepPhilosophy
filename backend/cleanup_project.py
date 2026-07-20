"""项目清理：删除冗余脚本/临时文件，整理目录结构"""
import os, sys, shutil, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def rm(*paths):
    for p in paths:
        fp = os.path.join(ROOT, p)
        if os.path.exists(fp):
            if os.path.isdir(fp): shutil.rmtree(fp)
            else: os.remove(fp)
            print(f'  DEL: {p}')
        else:
            print(f'  N/A: {p}')

print('=== 1. 删除根目录临时文件 ===')
rm('REMOVED_PDFS.txt', 'emoji_inventory.csv', 'wenshuoge_books.json')

print('\n=== 2. 删除 scripts/ 一次性脚本 ===')
scripts_dir = os.path.join(ROOT, 'scripts')
one_offs = [f for f in os.listdir(scripts_dir) if f.startswith('_')]
for f in one_offs:
    rm(f'scripts/{f}')
# Remove archive
rm('scripts/archive', 'scripts/__pycache__', 'scripts/api_keys.json')
# Remove unrelated scripts
rm('scripts/check_faces.py', 'scripts/img_gen.html', 'scripts/compress_images.py',
   'scripts/fix_bg.py', 'scripts/fix_image_names.py', 'scripts/fix_all_images.py',
   'scripts/replace_emoji.py', 'scripts/replace_emoji_v2.py',
   'scripts/cihai_add.py', 'scripts/gen_icon_from_emoji.py',
   'scripts/_gen_east.py', 'scripts/_gen_works.py', 'scripts/_gen_west.py',
   'scripts/_gen_world.py', 'scripts/_gen_philosophy_lyrics.py',
   'scripts/generate_icons.py', 'scripts/_old_school.jsx', 'scripts/_restore_data.jsx',
   'scripts/upload_books.py')

print('\n=== 3. 整理 backend/ 一次性脚本 ===')
rm('backend/fill_1000_bios.py', 'backend/fill_1000_v2.py', 'backend/fill_bio_final.py',
   'backend/fill_bio_prose.py', 'backend/fill_bio_robust.py', 'backend/fill_philosophers.py',
   'backend/fill_philosophers_v2.py', 'backend/fill_short_bios.py', 'backend/find_bad_bios.py',
   'backend/fix_philosophers.py', 'backend/cleanup_philosophers.py',
   'backend/link_philosopher_books.py', 'backend/gen_csv.py',
   'backend/rank_books.py', 'backend/rank_philosophers.py',
   'backend/build_phti_questions.py', 'backend/build_phti_silly.py',
   'backend/build_answer_book.py', 'backend/build_epub_pages.py',
   'backend/build_greek_subs.py', 'backend/build_presocratic.py',
   'backend/build_world_schools.py', 'backend/generate_tags_summaries.py',
   'backend/github_upload.py', 'backend/fetch_philosopher_batch.py',
   'backend/_audit_philosophers.py', 'backend/_audit_schools.py',
   'backend/_batch_add.py', 'backend/_comprehensive_audit.py',
   'backend/_constellation_audit.json', 'backend/_damage_fix.json',
   'backend/_final_audit_images.py', 'backend/_find_missing.py',
   'backend/_quick_fetch.py'
)
# Move scripts to backend
for src, dst in [('scripts/build_and_sync_kb.py', 'backend/build_and_sync_kb.py'),
                  ('scripts/build_knowledge_local.py', 'backend/build_knowledge_local.py'),
                  ('scripts/sync_to_cloud.py', 'backend/sync_to_cloud.py'),
                  ('scripts/generate_catalog.py', 'backend/generate_catalog.py')]:
    sfp = os.path.join(ROOT, src); dfp = os.path.join(ROOT, dst)
    if os.path.exists(sfp):
        shutil.copy2(sfp, dfp)
        os.remove(sfp)
        print(f'  MOVE: {src} -> {dst}')

print('\n=== 4. 清理 backend/data/ 冗余 ===')
rm('backend/data/bad_bios.json', 'backend/data/answer_book.json',
   'backend/data/epub_pages.json')
# Remove stale school JSONs that are also in app/public
school_dir = os.path.join(ROOT, 'backend', 'data')
for f in os.listdir(school_dir):
    if f.startswith('school_') and f.endswith('.json'):
        rm(f'backend/data/{f}')

print('\n=== 5. 清理 app/public/ 冗余 ===')
rm('app/public/books', 'app/public/downloads', 'app/public/epub_pages.json',
   'app/public/vercel.json')

print('\n=== 6. 删除 backend/data/ 中的 raw book dirs ===')
for sub in ['books', 'extracted', 'book_images']:
    rm(f'backend/data/{sub}')

print('\n✓ 清理完成')
