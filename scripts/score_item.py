"""AI 评分——哲学家或书籍的五维度评分"""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 读 .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    for line in open(env_path, encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not API_KEY:
    print('No DEEPSEEK_API_KEY'); sys.exit(1)

import urllib.request

dimensions_phil = ['思想深度','历史影响力','学术地位','原创性','传播广度']
dimensions_book = ['思想深度','历史影响力','学术地位','原创性','可读性']

def score_item(name, item_type='philosopher', extra=''):
    dims = dimensions_phil if item_type == 'philosopher' else dimensions_book
    prompt = f"""你是一位哲学史教授。请对以下{'哲学家' if item_type=='philosopher' else '哲学著作'}按5个维度打分(1-10整数)：
维度：{', '.join(dims)}
{'哲学家' if item_type=='philosopher' else '书籍'}：{name}{'（'+extra+'）' if extra else ''}
只返回 JSON 数组，如：[8,9,7,8,6]。不要解释。"""

    payload = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.3, 'max_tokens': 200,
        'response_format': {'type': 'json_object'},
    }
    req = urllib.request.Request(
        'https://api.deepseek.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode('utf-8'))
        content = r['choices'][0]['message']['content'].strip()
        scores = json.loads(content)
        if isinstance(scores, dict):
            scores = list(scores.values())[0] if list(scores.values()) else []
        # 加权综合分
        if item_type == 'philosopher':
            composite = round(scores[0]*1.2 + scores[1]*1.3 + scores[2]*1.0 + scores[3]*1.1 + scores[4]*0.4, 1)
        else:
            composite = round(scores[0]*1.2 + scores[1]*1.3 + scores[2]*1.0 + scores[3]*1.1 + scores[4]*0.4, 1)
        return {'scores': scores, 'rank': composite}

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('name', help='名称')
    p.add_argument('--type', default='philosopher', choices=['philosopher','book'])
    p.add_argument('--extra', default='', help='额外信息（年代/作者等）')
    args = p.parse_args()
    result = score_item(args.name, args.type, args.extra)
    print(json.dumps(result, ensure_ascii=False))
