"""测试 Agnes AI — DNS 替换 + 模型探测"""
import os, sys, re, json, ssl, socket, io, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 读 key
key_path = os.path.join(os.path.expanduser("~"), ".claude", "skills", "image", "scripts", "vision.py")
API_KEY = None
if os.path.exists(key_path):
    with open(key_path, "r", encoding="utf-8") as f:
        m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
        if m: API_KEY = m.group(1)

HOST = "apihub.agnes-ai.com"
REAL_IP = "104.18.19.62"

# DNS 替换：让 Python 对 apihub.agnes-ai.com 解析到真实 IP
_orig_getaddrinfo = socket.getaddrinfo
def _patched(host, port, family=0, type=0, proto=0, flags=0):
    if host == HOST:
        return _orig_getaddrinfo(REAL_IP, port, family, type, proto, flags)
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _patched

print(f"DNS patch: {HOST} -> {REAL_IP}")

# 探测可用模型
models = ["agnes-2.5-flash", "agnes-2.0-flash", "agnes-1.5-flash", "gpt-4o-mini"]
for model in models:
    payload = {"model": model, "messages": [{"role": "user", "content": "say OK"}], "max_tokens": 10}
    req = urllib.request.Request(
        f"https://{HOST}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            r = json.loads(resp.read().decode("utf-8"))
            if "error" in r:
                print(f"  {model}: ERROR - {r['error'].get('message', r['error'])[:100]}")
            else:
                content = r["choices"][0]["message"]["content"]
                print(f"  {model}: OK -> '{content}'")
                break
    except Exception as e:
        print(f"  {model}: NETWORK FAIL - {e}")
