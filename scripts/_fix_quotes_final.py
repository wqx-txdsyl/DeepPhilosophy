"""Fix all CSS var quote conflicts in SchoolDetailPage.jsx."""
import re

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"

with open(TARGET, 'r', encoding='utf-8') as f:
    c = f.read()

# The problem: inside single-quoted JS strings, CSS var functions have extra single quotes
# e.g.: 'linear-gradient(..., 'var(--gold)', ...)'
# The fix: remove single quotes around all var(--xxx) inside style strings

css_vars = ['gold', 'font-serif', 'font-sans', 'text-primary', 'text-secondary', 'text-muted']

fixes = 0
for var in css_vars:
    # Pattern 1: , 'var(--xxx)',
    pattern1 = ", '" + "var(--" + var + ")" + "', "
    repl1 = ", var(--" + var + "), "
    if pattern1 in c:
        c = c.replace(pattern1, repl1)
        fixes += 1

    # Pattern 2: , 'var(--xxx)')
    pattern2 = ", '" + "var(--" + var + ")')"
    repl2 = ", var(--" + var + "))"
    if pattern2 in c:
        c = c.replace(pattern2, repl2)
        fixes += 1

    # Pattern 3: ('var(--xxx)',
    pattern3 = "('" + "var(--" + var + ")', "
    repl3 = "(var(--" + var + "), "
    if pattern3 in c:
        c = c.replace(pattern3, repl3)
        fixes += 1

print(f"Fixed {fixes} CSS var quote issues")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(c)
print(f"Written: {len(c)} bytes")
