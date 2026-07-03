"""Expand CIHAI and quotes for democracy schools via API."""
import json, urllib.request, re, os

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py'), 'r', encoding='utf-8') as f:
    API_KEY = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"
with open(TARGET, 'r', encoding='utf-8') as f:
    c = f.read()

def call(sp, up, mt=4000):
    d = json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":sp},{"role":"user","content":up}],"temperature":0.7,"max_tokens":mt}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions",data=d,
        headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?","",raw).rstrip("```").strip()
    return json.loads(raw)

def esc(s):
    if not isinstance(s,str): return str(s)
    return s.replace("\\","\\\\").replace('"','\\"')

SP = "你是中国哲学教授。输出严格JSON，不要markdown。"

for var, name in [("OLD_DEMOCRACY","旧民主主义"),("NEW_DEMOCRACY","新民主主义")]:
    # CIHAI
    data = call(SP, f'请为{name}列出20个核心术语。格式：{{"cihai":[{{"word":"术语","def":"50-80字解释","source":"出处"}}]}}。必须20条。')
    entries = data.get("cihai",[])[:20]
    js = "[" + ",".join([f'{{"word": "{esc(e.get("word",""))}", "def": "{esc(e.get("def",""))}", "source": "{esc(e.get("source",""))}"}}' for e in entries]) + "]"
    old = c.find(f"const {var}_CIHAI")
    old_end = c.find("];", old) + 2
    c = c[:old] + f"const {var}_CIHAI = {js};" + c[old_end:]
    print(f"{name} CIHAI: {len(entries)}")

    # Quotes
    data2 = call(SP, f'请列出{name}时期18-20条名言。格式：{{"quotes":[{{"text":"引文","author":"作者","exp":"50-80字阐释"}}]}}。必须18条以上。')
    entries2 = data2.get("quotes",[])[:20]
    js2 = "[" + ",".join([f'{{"text": "{esc(e.get("text",""))}", "author": "{esc(e.get("author",""))}", "exp": "{esc(e.get("exp",""))}"}}' for e in entries2]) + "]"
    d_idx = c.find(f"const {var}_DATA")
    d_end = c.find(f"const {var}_CIHAI", d_idx)
    block = c[d_idx:d_end]
    qm = re.search(r"quotes:\s*\[.*?\]", block, re.DOTALL)
    if qm:
        block = block.replace(qm.group(0), f"quotes: {js2}")
        c = c[:d_idx] + block + c[d_end:]
    print(f"{name} Quotes: {len(entries2)}")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(c)
print(f"Done: {len(c)} bytes")
