"""分析当前书籍：找缺少中译本的西哲著作"""
import os, sys, json, io, urllib.request, urllib.parse, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')
BOOKS_FILE = os.path.join(BASE, 'app', 'public', 'books.json')

PROXY = 'http://127.0.0.1:12450'

with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
    books = json.load(f)

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# 已有书籍名
existing_titles = {b.get('title', '') for b in books}
existing_authors = {b.get('author', '') for b in books}

# 分析还缺哪些著名西哲的中译本
western_philosophers = [
    # (原作者, 代表作, 常见译名)
    ('柏拉图', 'The Republic', '理想国'),
    ('柏拉图', 'Symposium', '会饮篇'),
    ('亚里士多德', 'Nicomachean Ethics', '尼各马可伦理学'),
    ('亚里士多德', 'Metaphysics', '形而上学'),
    ('亚里士多德', 'Politics', '政治学'),
    ('笛卡尔', 'Meditations on First Philosophy', '第一哲学沉思集'),
    ('笛卡尔', 'Discourse on Method', '谈谈方法'),
    ('斯宾诺莎', 'Ethics', '伦理学'),
    ('莱布尼茨', 'Monadology', '单子论'),
    ('洛克', 'An Essay Concerning Human Understanding', '人类理解论'),
    ('贝克莱', 'A Treatise Concerning the Principles of Human Knowledge', '人类知识原理'),
    ('休谟', 'A Treatise of Human Nature', '人性论'),
    ('休谟', 'An Enquiry Concerning Human Understanding', '人类理解研究'),
    ('卢梭', 'The Social Contract', '社会契约论'),
    ('卢梭', 'Discourse on Inequality', '论人类不平等的起源'),
    ('康德', 'Critique of Pure Reason', '纯粹理性批判'),
    ('康德', 'Critique of Practical Reason', '实践理性批判'),
    ('康德', 'Critique of Judgment', '判断力批判'),
    ('黑格尔', 'Phenomenology of Spirit', '精神现象学'),
    ('黑格尔', 'Science of Logic', '逻辑学'),
    ('叔本华', 'The World as Will and Representation', '作为意志和表象的世界'),
    ('尼采', 'Thus Spoke Zarathustra', '查拉图斯特拉如是说'),
    ('尼采', 'Beyond Good and Evil', '善恶的彼岸'),
    ('尼采', 'The Genealogy of Morals', '论道德的谱系'),
    ('克尔凯郭尔', 'Either/Or', '非此即彼'),
    ('克尔凯郭尔', 'Fear and Trembling', '恐惧与战栗'),
    ('密尔', 'On Liberty', '论自由'),
    ('密尔', 'Utilitarianism', '功利主义'),
    ('马克思', 'Das Kapital', '资本论'),
    ('胡塞尔', 'Logical Investigations', '逻辑研究'),
    ('海德格尔', 'Being and Time', '存在与时间'),
    ('萨特', 'Being and Nothingness', '存在与虚无'),
    ('维特根斯坦', 'Tractatus Logico-Philosophicus', '逻辑哲学论'),
    ('维特根斯坦', 'Philosophical Investigations', '哲学研究'),
    ('罗尔斯', 'A Theory of Justice', '正义论'),
    ('福柯', 'Discipline and Punish', '规训与惩罚'),
    ('福柯', 'The Order of Things', '词与物'),
    ('德里达', 'Of Grammatology', '论文字学'),
    ('阿多诺', 'Dialectic of Enlightenment', '启蒙辩证法'),
    ('波普尔', 'The Open Society and Its Enemies', '开放社会及其敌人'),
    ('库恩', 'The Structure of Scientific Revolutions', '科学革命的结构'),
    ('伽达默尔', 'Truth and Method', '真理与方法'),
    ('阿伦特', 'The Human Condition', '人的境况'),
    ('柏格森', 'Creative Evolution', '创造进化论'),
    ('杜威', 'Democracy and Education', '民主主义与教育'),
    ('詹姆斯', 'Pragmatism', '实用主义'),
    ('罗素', 'A History of Western Philosophy', '西方哲学史'),
    ('罗素', 'The Problems of Philosophy', '哲学问题'),
    ('蒯因', 'Word and Object', '语词和对象'),
    ('奥斯汀', 'How to Do Things with Words', '如何以言行事'),
    ('斯特劳森', 'Individuals', '个体'),
    ('普特南', 'Reason, Truth and History', '理性、真理与历史'),
]

# 检查哪些已在库中，哪些缺
have = []
missing = []
for author, en_title, zh_title in western_philosophers:
    if zh_title in existing_titles or en_title in existing_titles:
        have.append((author, zh_title))
    else:
        missing.append((author, zh_title, en_title))

print(f'已有中译本: {len(have)}')
print(f'缺中译本: {len(missing)}')
print()

print('=== 建议补全的中译本 (Z-Library 可找) ===')
for author, zh_title, en_title in missing:
    # 生成 Z-Library 搜索 URL（用户在浏览器打开）
    query = urllib.parse.quote(f'{zh_title} {author}')
    zlib_url = f'https://singlelogin.re/s/?q={query}&languages%5B%5D=chinese'
    print(f'  {author} — 《{zh_title}》')
    print(f'    Z-Lib: {zlib_url}')

print(f'\n共 {len(missing)} 本待补')
print('每条 Z-Lib 链接在浏览器中打开即可搜索下载（需代理）。')
