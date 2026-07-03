"""Check democracy data for syntax issues."""
import re

with open(r"DeepPhilosophy/app/src/pages/SchoolDetailPage.jsx", "r", encoding="utf-8") as f:
    c = f.read()

for var in ["OLD_DEMOCRACY", "NEW_DEMOCRACY"]:
    idx = c.find(f"const {var}_DATA")
    end = c.find(f"const {var}_CIHAI", idx)
    if idx < 0:
        print(f"{var}: NOT FOUND")
        continue
    block = c[idx:end]

    # Count backticks - should be even
    bt = block.count("`")
    print(f"{var}: {bt} backticks ({'OK' if bt % 2 == 0 else 'ODD!'})")

    # Check for unescaped ${
    ds_count = block.count("${")
    esc_count = block.count("\\${")
    if ds_count > esc_count:
        print(f"  UNESCAPED ${{ found! {ds_count} vs {esc_count} escaped")

    # Check each backtick string for issues
    strings = re.findall(r"`([^`]*)`", block)
    for i, s in enumerate(strings):
        if "`" in s:
            print(f"  String {i}: contains literal backtick")
        if "${" in s and "\\${" not in s.replace("${", "DOLLARBRACE"):
            print(f"  String {i}: unescaped ${{ in: {s[:80]}...")

    # Also check for quote field specifically
    quote_m = re.search(r"quote:\s*`([^`]+)`", block)
    if quote_m:
        print(f"  quote: OK ({len(quote_m.group(1))} chars)")

    print()
