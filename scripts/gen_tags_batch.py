"""为新书批量生成标签 + 摘要"""
import os, sys, json, io, re, time, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_FILE = os.path.join(BASE, 'app', 'public', 'books.json')
DETAIL_DIR = os.path.join(BASE, 'app', 'public', 'book_detail')

env_path = os.path.join(BASE, '.env')
for line in open(env_path, encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())
API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

KNOWN_TAGS = [
    "古希腊哲学","教父哲学","经院哲学","唯名论","理性主义","经验主义","启蒙运动",
    "实在论","唯心主义","自由主义","浪漫主义","德国古典哲学","功利主义","超验主义",
    "实证主义","马克思主义","生命哲学","社会学","实用主义","精神分析学","现象学",
    "存在主义","分析哲学","过程哲学","哲学人类学","西方马克思主义","法兰克福学派",
    "批判理论","科学哲学","荒诞哲学","基督教哲学","结构主义","政治哲学","哲学诠释学",
    "解构主义","后结构主义","后现代主义","伦理学","宗教哲学","女性主义","社群主义",
    "技术哲学","斯多葛学派","怀疑论","儒家","道家","墨家","法家","名家","阴阳家",
    "兵家","两汉经学","魏晋玄学","隋唐佛学","宋明理学","明清实学","乾嘉朴学",
    "天演论","维新派","三民主义","毛泽东思想","现代新儒家","印度哲学","日本哲学",
    "韩国哲学","伊斯兰哲学","阿拉伯哲学","非洲哲学","拉丁美洲哲学"
]

os.makedirs(DETAIL_DIR, exist_ok=True)

with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
    books = json.load(f)

# 找需要生成标签的书：tags 为空 或 没有 book_detail
todo = []
for b in books:
    bid = b['id']
    detail_file = os.path.join(DETAIL_DIR, bid + '.json')
    has_detail = os.path.exists(detail_file)
    has_tags = len(b.get('tags', [])) > 0
    if not has_tags or not has_detail:
        todo.append(b)

print('Need tags: {}'.format(len(todo)))
if not todo:
    print('All done!')
    sys.exit(0)

success = 0
for i, b in enumerate(todo, 1):
    title = b['title']
    author = b['author']
    region = b['region']
    bid = b['id']
    idx = '[{}/{}]'.format(i, len(todo))

    prompt = '你是一个哲学文献专家。请为以下书籍生成标签和摘要：\n\n'
    prompt += '书名：《' + title + '》\n'
    prompt += '作者：' + author + '\n'
    prompt += '所属传统：' + region + '哲学\n\n'
    prompt += '要求：\n'
    prompt += '1. 标签：从已知标签列表中选择2-5个最匹配的。已知标签：' + ', '.join(KNOWN_TAGS) + '。\n'
    prompt += '2. 摘要：>=200字，涵盖主题、核心思想。连贯散文，禁止分条列点。\n\n'
    prompt += '输出JSON：{"tags":["标签1","标签2"],"summary":"摘要内容"}'

    payload = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.5, 'max_tokens': 1500,
        'response_format': {'type': 'json_object'}
    }

    try:
        req = urllib.request.Request('https://api.deepseek.com/v1/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY})
        with urllib.request.urlopen(req, timeout=60) as resp:
            r = json.loads(resp.read().decode('utf-8'))
        content = json.loads(r['choices'][0]['message']['content'])
        tags = content.get('tags', [])
        summary = content.get('summary', '')

        # 更新 books.json
        b['tags'] = tags

        # 写入 book_detail
        detail_file = os.path.join(DETAIL_DIR, bid + '.json')
        detail = {
            'bookId': bid, 'title': title, 'author': author,
            'region': region, 'tags': tags, 'summary': summary,
        }
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(detail, f, ensure_ascii=False, indent=2)

        success += 1
        print('  {} {} tags={} ({})'.format(idx, title[:30], tags, len(summary)))

    except Exception as e:
        print('  {} {} FAIL: {}'.format(idx, title[:30], e))

    time.sleep(0.3)

    # 每 20 本保存 books.json
    if i % 20 == 0:
        with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(books, f, ensure_ascii=False, indent=2)

with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print('\nDone: {}/{}'.format(success, len(todo)))
