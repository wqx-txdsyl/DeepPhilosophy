"""批量生成书籍摘要和标签（DeepSeek API）"""
import json, os, sys, io, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
BOOKS_PATH = os.path.join(BASE, '..', 'app', 'public', 'books.json')
DETAIL_DIR = os.path.join(BASE, 'data', 'book_detail')

# API config
def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(BASE)), '.env')
    if os.path.exists(env_path):
        for line in open(env_path, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
API_URL = os.environ.get('DP_API_URL', 'https://api.deepseek.com').rstrip('/')
if not API_KEY:
    print('No DEEPSEEK_API_KEY')
    sys.exit(1)

books = json.load(open(BOOKS_PATH, 'r', encoding='utf-8'))

# Only process books without summary in detail
to_process = []
for b in books:
    dp = os.path.join(DETAIL_DIR, f'{b["id"]}.json')
    if os.path.exists(dp):
        d = json.load(open(dp, 'r', encoding='utf-8'))
        if not d.get('summary') or len(d.get('summary', '')) < 50:
            to_process.append(b)
    else:
        to_process.append(b)

print(f'Need summaries: {len(to_process)}/{len(books)}')

PROMPT = """你是哲学史专家。为以下书籍生成标签和摘要。返回 JSON 对象，格式：
{"书名": {"tags": ["标签1","标签2","标签3"], "summary": "300字以上的中文内容摘要..."}, ...}
标签选3-5个，涵盖流派/时代/主题。摘要300-500字。只返回 JSON，不要解释。"""

BATCH = 10

for bi in range(0, len(to_process), BATCH):
    batch = to_process[bi:bi+BATCH]
    lines = '\n'.join(f'- {b["title"]}（{b.get("author","")}）' for b in batch)

    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': PROMPT},
            {'role': 'user', 'content': f'请为以下书籍生成标签和摘要：\n\n{lines}'},
        ],
        'temperature': 0.3, 'max_tokens': 8192,
        'response_format': {'type': 'json_object'},
    }

    req = urllib.request.Request(
        f'{API_URL}/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'},
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                content = result['choices'][0]['message']['content'].strip()
                if content.startswith('```'): content = content.split('\n',1)[1].rsplit('```',1)[0]
                data = json.loads(content)

                saved = 0
                for b in batch:
                    info = data.get(b['title'])
                    if not info:
                        # Fuzzy match
                        for k, v in data.items():
                            if b['title'][:4] in k or k[:4] in b['title']:
                                info = v; break
                    if info:
                        dp = os.path.join(DETAIL_DIR, f'{b["id"]}.json')
                        if os.path.exists(dp):
                            d = json.load(open(dp, 'r', encoding='utf-8'))
                            d['summary'] = info.get('summary', '')
                            d['tags'] = info.get('tags', [])
                            json.dump(d, open(dp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
                            saved += 1

                print(f'  batch {bi//BATCH+1}: {saved}/{len(batch)} summaries')
                break
        except Exception as e:
            print(f'  batch {bi//BATCH+1} attempt {attempt+1}: {e}')
            time.sleep(3)

    if bi + BATCH < len(to_process):
        time.sleep(1)

# Also update books.json with tags from detail
for b in books:
    dp = os.path.join(DETAIL_DIR, f'{b["id"]}.json')
    if os.path.exists(dp):
        d = json.load(open(dp, 'r', encoding='utf-8'))
        if d.get('tags'):
            b['tags'] = d['tags']
        if d.get('summary'):
            b['summary'] = d['summary']

json.dump(books, open(BOOKS_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'Updated books.json with tags/summaries')
print('Done')
