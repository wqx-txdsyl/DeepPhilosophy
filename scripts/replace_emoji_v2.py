"""智能替换：只在 JSX context 中替换 emoji，跳过字符串/模板字面量"""
import re, os

SRC = os.path.join(os.path.dirname(__file__), '..', 'app', 'src')

MAP = {
    '📚':'nav-books','✒️':'nav-authors','🧬':'nav-genealogy','💬':'nav-qa','🎮':'nav-games',
    '☀️':'theme-light','🌙':'theme-dark','💻':'mode-desktop','📱':'mode-mobile',
    '⚙️':'btn-settings','👤':'btn-user','☯':'region-east','☯️':'region-east',
    '🏛':'region-west','🏛️':'region-west','🌍':'region-world','🔍':'icon-search',
    '🏯':'region-east-pagoda','📦':'icon-file-size','📝':'icon-edit','📖':'icon-book-open',
    '💡':'icon-tip','😞':'icon-error','📑':'icon-toc','✕':'icon-close','💾':'icon-save',
    '📋':'icon-clipboard','🗑':'icon-trash','📎':'icon-link','📜':'icon-scroll',
    '✨':'icon-sparkles','🕯️':'icon-candle','🕯':'icon-candle','🔄':'icon-refresh',
    '🧠':'icon-brain','🤪':'icon-crazy','🚀':'icon-rocket','👎':'icon-thumbs-down',
    '🤔':'icon-question','😐':'icon-neutral','👍':'icon-thumbs-up','💯':'icon-perfect',
    '🔥':'icon-flame','🎭':'icon-drama','🌞':'icon-sun','🚧':'icon-lock',
    '☁️':'icon-cloud','☁':'icon-cloud','🔐':'icon-lock-key','✅':'icon-check',
    '🤖':'icon-bot','📅':'icon-calendar','📍':'icon-pin','✍️':'icon-writing',
    '💭':'icon-thinking','🧟':'icon-zombie',
}

SKIP_FILES = {'Icon.jsx', 'generate_icons.py', 'fix_bg.py', 'replace_emoji.py', 'replace_emoji_v2.py'}
IMPORT = "import Icon from "
IMPORT_LINE = "import Icon from '../components/Icon';\n"
COMPONENT_IMPORT = "import Icon from './Icon';\n"

def is_in_string(line, pos):
    """检查 pos 位置是否在字符串字面量内"""
    in_single = False; in_double = False; in_tick = False
    for i, ch in enumerate(line[:pos]):
        if ch == '\\': continue  # skip escapes
        if ch == "'" and not in_double and not in_tick: in_single = not in_single
        elif ch == '"' and not in_single and not in_tick: in_double = not in_double
        elif ch == '`' and not in_single and not in_double: in_tick = not in_tick
    return in_single or in_double or in_tick

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = original = f.read()

    count = 0
    lines = content.split('\n')
    for i, line in enumerate(lines):
        for emoji, name in MAP.items():
            idx = line.find(emoji)
            if idx >= 0:
                if not is_in_string(line, idx):
                    s = 16
                    if name.startswith('btn-') or name.startswith('theme-') or name.startswith('mode-'):
                        s = 18
                    lines[i] = line.replace(emoji, f'<Icon name="{name}" size={{{s}}} />')
                    count += 1
                    break  # 一行只替换一次避免错位

    if count > 0:
        content = '\n'.join(lines)
        # 添加 import
        if 'components/Icon' not in content:
            if '/components/' in filepath:  # components dir
                content = COMPONENT_IMPORT + content
            elif '/pages/' in filepath:  # pages dir
                # 找到最后一个 import 后插入
                import_lines = [j for j, l in enumerate(content.split('\n')) if l.startswith('import ')]
                if import_lines:
                    insert_at = import_lines[-1] + 1
                    lns = content.split('\n')
                    lns.insert(insert_at, IMPORT_LINE.strip())
                    content = '\n'.join(lns)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    return count

total = 0
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in ('node_modules',)]
    for f in files:
        if f.endswith(('.jsx', '.js')) and f not in SKIP_FILES:
            fp = os.path.join(root, f)
            n = replace_in_file(fp)
            if n > 0:
                print(f'  {os.path.relpath(fp, SRC)}: {n}')
                total += n
print(f'Total: {total}')
