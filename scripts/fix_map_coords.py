"""用 Agnes 2.0 Flash 图像理解重新定位世界地图坐标"""
import requests, json, re, os

API = "https://apihub.agnes-ai.com/v1/chat/completions"
KEY = "sk-tAli2tVgjAi5VG2zBG3oz4hUefyaqrD6UyjDaIpvhH6SKEAD"
IMG = "https://deepphilosophy-7g7m.onrender.com/schools/%E4%B8%96%E7%95%8C%E5%9C%B0%E5%9B%BE.png"

REGIONS = [
    "中国(东亚)", "日本", "韩国", "印度(南亚)", "西藏", "东南亚",
    "蒙古/中亚", "欧洲", "希腊", "北欧", "凯尔特(爱尔兰/英国)", "罗马(意大利)",
    "东欧/俄罗斯", "伊斯兰(阿拉伯半岛)", "古埃及", "美索不达米亚(伊拉克)",
    "波斯(伊朗)", "犹太(以色列)", "非洲(中部)", "北美(美国/加拿大)",
    "拉丁美洲(巴西/墨西哥)", "玛雅(中美洲)", "阿兹特克(墨西哥)", "澳洲"
]

prompt = f"""Analyze this world map image. For each of these regions, estimate its center position as percentage coordinates (x%, y%) where:
- x=0% is the left edge, x=100% is the right edge
- y=0% is the top edge, y=100% is the bottom edge

Regions to locate:
{chr(10).join(f'- {r}' for r in REGIONS)}

Return ONLY a JSON object like:
{{"中国": {{"x":78,"y":28}}, "日本": {{"x":90,"y":24}}, ...}}
No other text, no markdown, just the JSON object."""

print("Sending image to Agnes 2.0 Flash...")
r = requests.post(API, headers={
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}, json={
    "model": "agnes-2.0-flash",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": IMG}}
        ]
    }],
    "temperature": 0.1,
    "max_tokens": 2048,
}, timeout=120)

if r.status_code != 200:
    print(f"HTTP {r.status_code}: {r.text[:500]}")
    exit(1)

data = r.json()
content = data["choices"][0]["message"]["content"]
print(f"Raw response:\n{content}")

# Extract JSON
json_match = re.search(r'\{[\s\S]*\}', content)
if json_match:
    coords = json.loads(json_match.group())
    print("\n=== Corrected coordinates ===")
    for name, pos in coords.items():
        print(f"  {name}: x={pos['x']}, y={pos['y']}")

    # Save for later use
    with open(os.path.join(os.path.dirname(__file__), '..', 'map_coords_fixed.json'), 'w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)
    print("\nSaved to map_coords_fixed.json")
else:
    print("Could not extract JSON from response")
