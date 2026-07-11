"""
修复星丛作者映射：
1. 提取 SchoolDetailPage 中所有 thinker 名字
2. 与 philosophers_db 匹配译名
3. 补全缺失的哲学家
4. 生成更新后的 philosophers_db.py 和 NAME_ALIASES
"""
import os, sys, re, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # ============ Step 1: Extract thinkers from SchoolDetailPage ============
    school_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'app', 'src', 'pages', 'SchoolDetailPage.jsx'
    )
    with open(school_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract all thinker names from thinkers: [...] arrays
    thinker_pattern = r"thinkers:\s*\[([\s\S]*?)\]"
    name_pattern = r"name:\s*'([^']+)'"
    all_thinkers = set()
    for match in re.finditer(thinker_pattern, content):
        for name_match in re.finditer(name_pattern, match.group(1)):
            all_thinkers.add(name_match.group(1))

    # Also get from relations arrays
    rel_name_pattern = r"(?:from|to):\s*'([^']+)'"
    for block in content.split('relations:'):
        for name_match in re.finditer(rel_name_pattern, block):
            all_thinkers.add(name_match.group(1))

    # Clean up: remove parenthetical stage markers, split combined names
    cleaned_thinkers = set()
    for name in all_thinkers:
        name = name.strip()
        # Skip empty
        if not name or len(name) < 2:
            continue
        # Split combined entries like "阿多诺与霍克海默"
        if '与' in name and len(name) > 6:
            for part in name.split('与'):
                cleaned_thinkers.add(part.strip())
        else:
            # Remove parenthetical modifiers
            name = re.sub(r'\(.*?\)', '', name)
            name = re.sub(r'（.*?）', '', name)
            name = name.replace('早期', '').replace('后期', '').replace('晚期', '').strip()
            if len(name) >= 2:
                cleaned_thinkers.add(name)

    print(f"从星丛提取到 {len(all_thinkers)} 个原始名字 -> 清洗后 {len(cleaned_thinkers)} 个")

    # ============ Step 2: Load philosophers_db ============
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophers_db.py')

    # Read current module
    import philosophers_db
    existing_philosophers = dict(philosophers_db.PHILOSOPHERS)
    existing_aliases = dict(philosophers_db.NAME_ALIASES)
    print(f"当前数据库: {len(existing_philosophers)} 位哲学家, {len(existing_aliases)} 个别名")

    # ============ Step 3: Match thinkers to philosophers ============
    unmatched = []
    matched = {}
    used_aliases = dict(existing_aliases)

    for thinker in sorted(cleaned_thinkers):
        # Try existing get_philosopher_info
        info = philosophers_db.get_philosopher_info(thinker)
        if info:
            matched[thinker] = 'exact_or_fuzzy'
            continue

        # Try more aggressive fuzzy matching
        found = False
        for ph_name in existing_philosophers:
            # Check if thinker is a known variant
            if len(thinker) >= 4 and len(ph_name) >= 4:
                # Check character overlap
                thinker_set = set(thinker)
                ph_set = set(ph_name)
                overlap = thinker_set & ph_set
                if len(overlap) >= min(len(thinker_set), len(ph_set)) * 0.6:
                    # High overlap - likely same person
                    if thinker not in used_aliases and thinker != ph_name:
                        used_aliases[thinker] = ph_name
                        matched[thinker] = f'alias->{ph_name}'
                        found = True
                        break

        if not found:
            unmatched.append(thinker)

    print(f"匹配成功: {len(matched)} 个")
    print(f"未匹配(需新建): {len(unmatched)} 个")
    if unmatched:
        for t in unmatched[:30]:
            print(f"  - {t}")
        if len(unmatched) > 30:
            print(f"  ... 还有 {len(unmatched)-30} 个")

    # ============ Step 4: Check which unmatched are already book authors ============
    # Load book authors from summaries cache
    summaries_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'book_summaries.json')
    book_authors = set()
    if os.path.exists(summaries_path):
        with open(summaries_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        for key in summaries:
            if '||' in key:
                author = key.split('||')[1]
                if author and author not in ('合集&概述', '合集', '概述'):
                    book_authors.add(author)
    print(f"\n书籍作者数: {len(book_authors)}")

    # ============ Step 5: Generate new philosopher entries ============
    new_entries = {}

    for thinker in unmatched:
        # Check if this thinker exists as a book author
        if thinker in book_authors:
            new_entries[thinker] = {
                "era": "",
                "country": "",
                "school": "",
                "bio": f"{thinker}的著作收录于本馆。",
                "wiki_url": f"https://en.wikipedia.org/wiki/{thinker}",
            }

    print(f"从书籍作者匹配到 {len(new_entries)} 位新哲学家")

    # ============ Step 6: Write updated philosophers_db ============
    # Read the current file
    with open(db_path, 'r', encoding='utf-8') as f:
        db_content = f.read()

    # Build new PHILOSOPHERS entries as Python code
    new_entries_code = []
    for name, info in sorted(new_entries.items()):
        entry = f'''
    "{name}": {{
        "era": "{info['era']}",
        "country": "{info['country']}",
        "school": "{info['school']}",
        "bio": "{info['bio']}",
        "wiki_url": "{info['wiki_url']}",
    }},'''
        new_entries_code.append(entry)

    # Find insertion point: right before the NAME_ALIASES or at end of PHILOSOPHERS dict
    # Find the last "}}" in PHILOSOPHERS dict
    ph_end = db_content.find('\n\n# ============================================================\n# 姓名别名')
    if ph_end < 0:
        ph_end = db_content.find('\n\nNAME_ALIASES')

    if ph_end > 0:
        # Insert before aliases section
        new_code = ''.join(new_entries_code)
        db_content = db_content[:ph_end] + '\n    # --- 从星丛补全 ---' + new_code + '\n' + db_content[ph_end:]
        print(f"将在 philosophers_db.py 中插入 {len(new_entries)} 条新条目")
    else:
        print("错误: 找不到 NAME_ALIASES 位置")

    # Update NAME_ALIASES
    new_alias_code = []
    for alias, target in sorted(used_aliases.items()):
        if alias not in existing_aliases and alias != target:
            new_alias_code.append(f'    "{alias}": "{target}",\n')

    if new_alias_code:
        # Find NAME_ALIASES dict and append
        alias_pos = db_content.find('NAME_ALIASES = {')
        if alias_pos > 0:
            insert_pos = db_content.find('{', alias_pos) + 1
            db_content = db_content[:insert_pos+1] + '\n    # --- 星丛别名补全 ---\n' + ''.join(new_alias_code) + db_content[insert_pos+1:]
            print(f"将添加 {len(new_alias_code)} 个别名")
    else:
        print("没有新别名需要添加")

    # Write updated file
    with open(db_path + '.new', 'w', encoding='utf-8') as f:
        f.write(db_content)
    print(f"\n新文件写入: {db_path}.new")
    print(f"请检查后手动替换原文件: mv {db_path}.new {db_path}")

    # ============ Step 7: Generate unmatched report ============
    still_unmatched = [t for t in unmatched if t not in new_entries]
    if still_unmatched:
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'unmatched_thinkers.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(sorted(still_unmatched), f, ensure_ascii=False, indent=2)
        print(f"\n还有 {len(still_unmatched)} 个思考者未匹配（非书籍作者），已保存到 unmatched_thinkers.json")

    # Stats
    print(f"\n=== 总结 ===")
    print(f"原始哲学家: {len(existing_philosophers)}")
    print(f"新增别名: {len(new_alias_code)}")
    print(f"新增哲学家: {len(new_entries)}")
    print(f"最终总数: {len(existing_philosophers) + len(new_entries)}")
    print(f"总别名数: {len(used_aliases)}")

if __name__ == '__main__':
    main()
