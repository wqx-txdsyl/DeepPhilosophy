"""Extract all quotes from SchoolDetailPage into a JS module."""
import re

with open(r"DeepPhilosophy/app/src/pages/SchoolDetailPage.jsx", "r", encoding="utf-8") as f:
    c = f.read()

all_quotes = re.findall(r'"text":\s*[`"]([^`"]+)[`"],\s*"author":\s*[`"]([^`"]+)[`"]', c)

seen = set()
unique = []
for t, a in all_quotes:
    t = t.strip()
    if t not in seen and len(t) > 6:
        seen.add(t)
        unique.append({"text": t, "author": a.strip()})

print(f"Unique quotes: {len(unique)}")

with open(r"DeepPhilosophy/app/src/data/dailyQuotes.js", "w", encoding="utf-8") as f:
    f.write("const DAILY_QUOTES = [\n")
    for q in unique:
        text = q["text"].replace("\\", "\\\\").replace("'", "\\'")
        author = q["author"].replace("\\", "\\\\").replace("'", "\\'")
        f.write(f"  {{ text: '{text}', author: '{author}' }},\n")
    f.write("];\n\nexport default DAILY_QUOTES;\n")

print(f"Written {len(unique)} quotes")
