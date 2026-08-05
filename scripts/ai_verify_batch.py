"""Agnes AI 分批肖像验证 — 可断点续跑"""
import os, sys, json, io, base64, urllib.request, re, time
import requests as req_lib
# 复用 Session 避免每次 TLS 握手压垮代理
SESSION = req_lib.Session()
SESSION.headers.update({'Content-Type': 'application/json'})

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')
PROGRESS_FILE = os.path.join(BASE, 'scripts', '_ai_batch_progress.json')
REPORT_FILE = os.path.join(BASE, 'scripts', '_ai_verify_report.json')

key_path = os.path.join(os.path.expanduser('~'), '.claude', 'skills', 'image', 'scripts', 'vision.py')
with open(key_path, 'r', encoding='utf-8') as f:
    m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
    API_KEY = m.group(1)

MODEL = 'agnes-2.0-flash'
BATCH = 50  # 每批 50 张

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# 构建待检列表
all_images = []
for name, data in philosophers.items():
    if not isinstance(data, dict): continue
    safe = name.replace('/', '-').replace('\\', '-').replace(':', '-')
    for ext in ['.jpg', '.png', '.webp']:
        fp = os.path.join(IMG_DIR, safe + ext)
        if os.path.exists(fp):
            all_images.append((name, fp, data))
            break

# 加载已有进度
done = set()
mismatches = []
total_tokens = 0
errors_prev = set()  # 之前出错的，需重新验证
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        prog = json.load(f)
    done = set(prog.get('done', []))
    mismatches = prog.get('mismatches', [])
    total_tokens = prog.get('tokens', 0)
    errors_prev = set(prog.get('errors', []))
    # 把之前出错的从 done 里移除，重新验证
    done -= errors_prev
    print(f'[续跑] 已完成 {len(done)} 张, 已发现 {len(mismatches)} 误配')
    if errors_prev:
        print(f'[续跑] 重试 {len(errors_prev)} 个之前出错的')

pending = [(n, p, d) for n, p, d in all_images if n not in done]
print(f'待检: {len(pending)} 张 (共 {len(all_images)})')

for batch_start in range(0, len(pending), BATCH):
    batch = pending[batch_start:batch_start + BATCH]
    batch_num = batch_start // BATCH + 1
    total_batches = (len(pending) + BATCH - 1) // BATCH
    print(f'\n--- 批次 {batch_num}/{total_batches} ({len(batch)} 张) ---')

    # 收集本轮出错的名字
    batch_errors = []

    for i, (name, img_path, data) in enumerate(batch):
        done_count = len(done) + i + 1
        total = len(all_images)
        # 重试循环（最多 3 次）
        for retry in range(3):
            try:
                # 读取并压缩大图（超过 500KB 的压缩）
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()
                if len(img_bytes) > 500 * 1024:
                    from PIL import Image as PILImage
                    import io as pil_io
                    im = PILImage.open(pil_io.BytesIO(img_bytes))
                    w, h = im.size
                    if w * h > 800 * 800:
                        im.thumbnail((600, 600), PILImage.LANCZOS)
                    buf = pil_io.BytesIO()
                    fmt = 'JPEG' if ext in ('.jpg', '.jpeg') else 'PNG' if ext == '.png' else 'WebP'
                    im.save(buf, format=fmt, quality=75)
                    img_bytes = buf.getvalue()
                b64 = base64.b64encode(img_bytes).decode('utf-8')
                ext = os.path.splitext(img_path)[1].lower()
                mime = 'image/webp' if ext == '.webp' else 'image/jpeg' if ext in ('.jpg','.jpeg') else 'image/png'
                img_uri = f'data:{mime};base64,{b64}'

                prompt = (
                    f'Verify: Is this image a plausible portrait of philosopher "{name}"? '
                    f'Era: {data.get("era","?")}. Region: {data.get("region","?")}. '
                    f'Rules: sculptures/paintings/busts OK for pre-modern. Photos OK for 1900+. '
                    f'Flag MISMATCH: wrong era style, wrong ethnicity, not a person, obviously wrong person. '
                    f'Reply: MATCH or MISMATCH + brief reason in Chinese.'
                )

                payload = {
                    'model': MODEL,
                    'messages': [{'role': 'user', 'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': img_uri}}
                    ]}],
                    'temperature': 0.3, 'max_tokens': 200
                }
                resp = SESSION.post(
                    'https://apihub.agnes-ai.com/v1/chat/completions',
                    json=payload,
                    headers={'Authorization': f'Bearer {API_KEY}'},
                    timeout=90
                )
                r = resp.json()

                if 'error' in r:
                    err_msg = r['error'].get('message', str(r['error']))
                    if 'rate' in err_msg.lower() or '503' in str(r.get('error',{})):
                        wait = (retry + 1) * 5
                        print(f'  [{done_count}/{total}] RATE {name}: 等{wait}s...', flush=True)
                        time.sleep(wait)
                        continue
                    print(f'  [{done_count}/{total}] API_ERR {name}: {err_msg[:60]}', flush=True)
                    break

                reply = r['choices'][0]['message']['content'].strip()
                tokens = r.get('usage', {}).get('total_tokens', 0)
                total_tokens += tokens
                done.add(name)

                if reply.upper().startswith('MISMATCH'):
                    mismatches.append({'name': name, 'reason': reply, 'file': os.path.basename(img_path)})
                    print(f'  [{done_count}/{total}] MISMATCH {name}: {reply[9:].strip()[:80]}', flush=True)
                else:
                    print(f'  [{done_count}/{total}] OK {name}', flush=True)
                break  # success, exit retry loop

            except req_lib.HTTPError as e:
                code = e.response.status_code
                if code in (429, 503, 502):
                    wait = (retry + 1) * 5
                    print(f'  [{done_count}/{total}] HTTP{code} {name}: 等{wait}s...', flush=True)
                    time.sleep(wait)
                else:
                    print(f'  [{done_count}/{total}] HTTP{code} {name}: 跳过', flush=True)
                    break
            except Exception as e:
                err_str = str(e)
                if '10054' in err_str or '10053' in err_str or 'timeout' in err_str.lower() or 'reset' in err_str.lower():
                    wait = (retry + 1) * 3
                    print(f'  [{done_count}/{total}] NET {name}: 等{wait}s重试({retry+1}/3)...', flush=True)
                    time.sleep(wait)
                elif 'Remote end closed' in err_str or 'closed connection' in err_str.lower():
                    wait = (retry + 1) * 8  # 更长的等待
                    print(f'  [{done_count}/{total}] CLOSE {name}: 等{wait}s重试({retry+1}/3)...', flush=True)
                    time.sleep(wait)
                elif retry < 2:
                    time.sleep(2)
                else:
                    print(f'  [{done_count}/{total}] FAIL {name}: {err_str[:60]}', flush=True)
                    batch_errors.append(name)
        time.sleep(0.1)

    # 每批保存
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'done': sorted(done), 'mismatches': mismatches,
            'tokens': total_tokens, 'total': len(all_images),
            'errors': sorted(errors_prev | set(batch_errors)),
        }, f, ensure_ascii=False, indent=2)

    matched = len(done) - len(mismatches)
    print(f'  进度: {len(done)}/{len(all_images)} | 误配: {len(mismatches)} | 正确: {matched} | tokens: {total_tokens}')
    time.sleep(0.5)  # 批次间休息

# 最终报告
with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    json.dump({'total': len(all_images), 'mismatches': mismatches, 'tokens': total_tokens}, f, ensure_ascii=False, indent=2)

print(f'\n=== 验证完成 ===')
print(f'MISMATCH: {len(mismatches)}/{len(all_images)}')
for m in mismatches:
    print(f'  {m["name"]}: {m["reason"][:100]}')
