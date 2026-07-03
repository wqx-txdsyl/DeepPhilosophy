"""Generate works/timeline/quotes for democracy schools in correct format."""
import json, urllib.request, re, os

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py'), 'r', encoding='utf-8') as f:
    API_KEY = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"
with open(TARGET, 'r', encoding='utf-8') as f:
    c = f.read()

SP = "你是中国哲学教授。输出严格JSON，不要markdown。"
SCHOOLS = [("旧民主主义", "OLD_DEMOCRACY"), ("新民主主义", "NEW_DEMOCRACY")]

for name, var in SCHOOLS:
    # Generate works
    up = f'请列出"{name}"时期最重要的6-8部著作或文献。格式：{{"works":[{{"title":"书名","author":"作者","era":"年代","desc":"50-80字简介"}}]}}。书名不加《》。'
    d = json.dumps({"model": "deepseek-chat", "messages": [{"role": "system", "content": SP}, {"role": "user", "content": up}], "temperature": 0.7, "max_tokens": 2000}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?", "", raw).rstrip("```").strip()
    works_data = json.loads(raw)

    # Generate quotes
    up2 = f'请列出"{name}"时期最具代表性的18-20条名言或语录。格式：{{"quotes":[{{"text":"引文","author":"作者","exp":"50字阐释"}}]}}'
    d2 = json.dumps({"model": "deepseek-chat", "messages": [{"role": "system", "content": SP}, {"role": "user", "content": up2}], "temperature": 0.7, "max_tokens": 3000}).encode()
    r2 = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d2,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r2, timeout=120) as resp2:
        raw2 = json.loads(resp2.read().decode())["choices"][0]["message"]["content"]
    raw2 = raw2.strip()
    if raw2.startswith("```"): raw2 = re.sub(r"^```\w*\n?", "", raw2).rstrip("```").strip()
    quotes_data = json.loads(raw2)

    # Escape strings for JS
    def esc(s):
        if not isinstance(s, str): return str(s)
        return s.replace("\\", "\\\\").replace('"', '\\"')

    # Build works JS array
    works_entries = []
    for w in works_data.get("works", []):
        works_entries.append(
            '{"title": "' + esc(w["title"]) + '", "author": "' + esc(w.get("author", "")) + '", "era": "' + esc(w.get("era", "")) + '", "desc": "' + esc(w.get("desc", "")) + '"}'
        )
    works_js = "works:[" + ",".join(works_entries) + "]"

    # Build quotes JS array
    quotes_entries = []
    for q in quotes_data.get("quotes", []):
        quotes_entries.append(
            '{"text": "' + esc(q["text"]) + '", "author": "' + esc(q.get("author", "")) + '", "exp": "' + esc(q.get("exp", "")) + '"}'
        )
    quotes_js = "quotes:[" + ",".join(quotes_entries) + "]"

    # Replace in file
    idx = c.find(f"const {var}_DATA")
    end = c.find(f"const {var}_CIHAI", idx)
    block = c[idx:end]

    import re
    # Replace works
    wm = re.search(r"works:\[.*?\]", block, re.DOTALL)
    if wm:
        block = block.replace(wm.group(0), works_js)
    # Replace quotes
    qm = re.search(r"quotes:\[.*?\]", block, re.DOTALL)
    if qm:
        block = block.replace(qm.group(0), quotes_js)

    c = c[:idx] + block + c[end:]
    print(f"{name}: {len(works_data.get('works',[]))} works, {len(quotes_data.get('quotes',[]))} quotes")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")
