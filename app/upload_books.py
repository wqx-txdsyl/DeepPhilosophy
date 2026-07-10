import oss2, os

AK_ID = os.environ['ALIYUN_AK_ID']
AK_SECRET = os.environ['ALIYUN_AK_SECRET']
BOOKS_DIR = os.environ.get('BOOKS_DIR', 'F:/philosophy')

auth = oss2.Auth(AK_ID, AK_SECRET)
b = oss2.Bucket(auth, 'oss-cn-shanghai.aliyuncs.com', 'deepphilosophy')
ct_map = {'.pdf': 'application/pdf', '.epub': 'application/epub+zip', '.txt': 'text/plain', '.mobi': 'application/x-mobipocket-ebook'}

count = 0
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext not in ct_map:
            continue
        p = os.path.join(root, f)
        k = p.replace(BOOKS_DIR + '/', '').replace(BOOKS_DIR + '\\', '').replace('\\', '/')
        try:
            b.put_object_from_file(k, p, headers={'Content-Type': ct_map[ext]})
            count += 1
            if count % 20 == 0:
                print(f'  {count} books...')
            if count % 200 == 0:
                print(f'  {count} uploaded')
        except Exception as e:
            print(f'  FAIL {k}: {e}')
print(f'Done: {count} books uploaded')
