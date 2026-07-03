"""将前端源码中的 emoji 替换为 <Icon> 组件"""
import re, os

SRC = os.path.join(os.path.dirname(__file__), '..', 'app', 'src')

# emoji → (icon_name, size)
MAP = {
    # 导航
    '📚': ('nav-books', 16),
    '✒️': ('nav-authors', 16),
    '🧬': ('nav-genealogy', 16),
    '💬': ('nav-qa', 16),
    '🎮': ('nav-games', 16),
    # 主题
    '☀️': ('theme-light', 18),
    '🌙': ('theme-dark', 18),
    '💻': ('mode-desktop', 18),
    '📱': ('mode-mobile', 18),
    # 按钮
    '⚙️': ('btn-settings', 18),
    '👤': ('btn-user', 18),
    # 区域
    '☯': ('region-east', 16),
    '☯️': ('region-east', 16),
    '🏛': ('region-west', 16),
    '🏛️': ('region-west', 16),
    '🌍': ('region-world', 16),
    # 图标
    '🔍': ('icon-search', 16),
    '🏯': ('region-east-pagoda', 16),
    '📦': ('icon-file-size', 16),
    '📝': ('icon-edit', 16),
    '📖': ('icon-book-open', 16),
    '💡': ('icon-tip', 16),
    '😞': ('icon-error', 16),
    '📑': ('icon-toc', 16),
    '✕': ('icon-close', 16),
    '✗': ('icon-close', 16),
    '💾': ('icon-save', 16),
    '📋': ('icon-clipboard', 16),
    '🗑': ('icon-trash', 16),
    '📎': ('icon-link', 16),
    '📜': ('icon-scroll', 16),
    '✨': ('icon-sparkles', 16),
    '🕯️': ('icon-candle', 16),
    '🕯': ('icon-candle', 16),
    '🔄': ('icon-refresh', 16),
    '🧠': ('icon-brain', 16),
    '🤪': ('icon-crazy', 16),
    '🚀': ('icon-rocket', 16),
    '👎': ('icon-thumbs-down', 16),
    '🤔': ('icon-question', 16),
    '😐': ('icon-neutral', 16),
    '👍': ('icon-thumbs-up', 16),
    '💯': ('icon-perfect', 16),
    '🔥': ('icon-flame', 16),
    '🎭': ('icon-drama', 16),
    '🌞': ('icon-sun', 16),
    '🚧': ('icon-lock', 16),
    '☁️': ('icon-cloud', 16),
    '☁': ('icon-cloud', 16),
    '🔐': ('icon-lock-key', 16),
    '✅': ('icon-check', 16),
    '🤖': ('icon-bot', 16),
    '📅': ('icon-calendar', 16),
    '📍': ('icon-pin', 16),
    '✍️': ('icon-writing', 16),
    '💭': ('icon-thinking', 16),
    '🧟': ('icon-zombie', 16),
    # 保留：→ ❌ 非 emoji，是箭头
}

IMPORT_LINE = "import Icon from './components/Icon';\n"
ICON_IMPORT = "import Icon from "

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    count = 0

    for emoji, (name, size) in MAP.items():
        if name == 'nav-books' or name == 'nav-authors' or name == 'nav-genealogy' or name == 'nav-qa' or name == 'nav-games':
            s = 16
        elif name in ('btn-user', 'btn-settings', 'theme-light', 'theme-dark', 'mode-desktop', 'mode-mobile'):
            s = 18
        else:
            s = size

        replacement = f'<Icon name="{name}" size={s} />'
        # 避免替换 import 语句和已存在的 Icon 调用
        # 简单策略：只替换不在 import 行和已有 Icon 标签中的 emoji
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if ICON_IMPORT in line or '<Icon name=' in line:
                new_lines.append(line)
                continue
            before = line
            line = line.replace(emoji, replacement)
            if line != before:
                count += 1
            new_lines.append(line)
        content = '\n'.join(new_lines)

    # 添加 Icon import（如果还没有且有替换）
    if count > 0 and ICON_IMPORT not in original:
        # 找到最后一个 import 行
        lines = content.split('\n')
        last_import = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') and 'from' in line:
                last_import = i
        # 找到 import 块结束
        for i in range(last_import + 1, len(lines)):
            if not lines[i].strip() or lines[i].strip().startswith('//') or lines[i].strip().startswith('/*'):
                continue
            if not lines[i].startswith('import '):
                last_import = i - 1
                break
        lines.insert(last_import + 1, IMPORT_LINE.strip())
        content = '\n'.join(lines)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return count
    return 0

# 扫描所有 JSX 文件
total = 0
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in ('node_modules',)]
    for f in files:
        if f.endswith(('.jsx', '.js')) and f not in ('Icon.jsx',):
            fp = os.path.join(root, f)
            n = replace_in_file(fp)
            if n > 0:
                rel = os.path.relpath(fp, SRC)
                print(f'  {rel}: {n} replacements')
                total += n

print(f'\nTotal: {total} emoji replacements')
