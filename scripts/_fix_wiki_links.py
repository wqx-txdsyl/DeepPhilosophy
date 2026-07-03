"""
Verify and fix Wikipedia links for all philosophers.
Chinese name -> correct English Wikipedia URL.
"""
import ast, json, urllib.request, time, re, os, sys

DB_PATH = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\backend\philosophers_db.py"

with open(DB_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

with open(DB_PATH + ".wiki_bak", 'w', encoding='utf-8') as f:
    f.write(content)

# Parse
dict_start = content.find('PHILOSOPHERS = {')
dict_text = content[dict_start:]
depth = 0; end = 0
for i, c in enumerate(dict_text):
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0: end = i + 1; break
tree = ast.parse(dict_text[:end])
philosophers = ast.literal_eval(tree.body[0].value)

print(f"Found {len(philosophers)} philosophers\n")

# Known Chinese->English Wikipedia mappings
WIKI_MAP = {
    # Greek
    "柏拉图": "Plato", "亚里士多德": "Aristotle", "苏格拉底": "Socrates",
    "伊壁鸠鲁": "Epicurus", "赫拉克利特": "Heraclitus", "巴门尼德": "Parmenides",
    "毕达哥拉斯": "Pythagoras", "普罗提诺": "Plotinus", "第欧根尼": "Diogenes",
    "泰勒斯": "Thales", "芝诺": "Zeno_of_Citium", "恩培多克勒": "Empedocles",
    "阿那克西曼德": "Anaximander", "阿那克萨戈拉": "Anaxagoras",
    "皮浪": "Pyrrho", "塞克斯都·恩披里柯": "Sextus_Empiricus",
    "普罗泰戈拉": "Protagoras", "高尔吉亚": "Gorgias",
    # German
    "康德": "Immanuel_Kant", "黑格尔": "Georg_Wilhelm_Friedrich_Hegel",
    "叔本华": "Arthur_Schopenhauer", "尼采": "Friedrich_Nietzsche",
    "海德格尔": "Martin_Heidegger", "胡塞尔": "Edmund_Husserl",
    "莱布尼茨": "Gottfried_Wilhelm_Leibniz", "费希特": "Johann_Gottlieb_Fichte",
    "谢林": "Friedrich_Wilhelm_Joseph_Schelling", "费尔巴哈": "Ludwig_Feuerbach",
    "伽达默尔": "Hans-Georg_Gadamer", "哈贝马斯": "Jurgen_Habermas",
    "阿多诺": "Theodor_W._Adorno", "霍克海默": "Max_Horkheimer",
    "马尔库塞": "Herbert_Marcuse", "本雅明": "Walter_Benjamin",
    "狄尔泰": "Wilhelm_Dilthey", "雅斯贝尔斯": "Karl_Jaspers",
    "弗雷格": "Gottlob_Frege", "卡尔纳普": "Rudolf_Carnap",
    "卡西尔": "Ernst_Cassirer", "舍勒": "Max_Scheler",
    "文德尔班": "Wilhelm_Windelband", "李凯尔特": "Heinrich_Rickert",
    "沃尔夫": "Christian_Wolff_(philosopher)",
    "奥卡姆的威廉": "William_of_Ockham",
    # French
    "笛卡尔": "Rene_Descartes", "卢梭": "Jean-Jacques_Rousseau",
    "萨特": "Jean-Paul_Sartre", "加缪": "Albert_Camus",
    "柏格森": "Henri_Bergson", "福柯": "Michel_Foucault",
    "德里达": "Jacques_Derrida", "德勒兹": "Gilles_Deleuze",
    "梅洛-庞蒂": "Maurice_Merleau-Ponty", "利科": "Paul_Ricoeur",
    "波伏娃": "Simone_de_Beauvoir", "孔德": "Auguste_Comte",
    "涂尔干": "Emile_Durkheim", "巴什拉": "Gaston_Bachelard",
    "利奥塔": "Jean-Francois_Lyotard", "鲍德里亚": "Jean_Baudrillard",
    "巴塔耶": "Georges_Bataille", "列维纳斯": "Emmanuel_Levinas",
    "伏尔泰": "Voltaire", "孟德斯鸠": "Montesquieu", "狄德罗": "Denis_Diderot",
    "帕斯卡": "Blaise_Pascal",
    # British/American
    "洛克": "John_Locke", "休谟": "David_Hume", "贝克莱": "George_Berkeley",
    "霍布斯": "Thomas_Hobbes", "培根": "Francis_Bacon", "密尔": "John_Stuart_Mill",
    "边沁": "Jeremy_Bentham", "罗素": "Bertrand_Russell",
    "摩尔": "G._E._Moore", "赖尔": "Gilbert_Ryle", "奥斯汀": "J._L._Austin",
    "罗尔斯": "John_Rawls", "诺齐克": "Robert_Nozick",
    "麦金太尔": "Alasdair_MacIntyre", "泰勒": "Charles_Taylor_(philosopher)",
    "桑德尔": "Michael_Sandel", "伯林": "Isaiah_Berlin",
    "威廉·詹姆士": "William_James", "杜威": "John_Dewey",
    "皮尔士": "Charles_Sanders_Peirce", "罗蒂": "Richard_Rorty",
    "普特南": "Hilary_Putnam", "塞尔": "John_Searle",
    "怀特海": "Alfred_North_Whitehead", "奎因": "Willard_Van_Orman_Quine",
    "库恩": "Thomas_Kuhn", "波普尔": "Karl_Popper",
    "费耶阿本德": "Paul_Feyerabend", "拉卡托斯": "Imre_Lakatos",
    "斯宾塞": "Herbert_Spencer", "亚当·斯密": "Adam_Smith",
    "亚当·弗格森": "Adam_Ferguson", "米尔恩": "Alan_Milne",
    # Italian/Spanish/Latin
    "阿奎那": "Thomas_Aquinas", "马基雅维利": "Niccolo_Machiavelli",
    "维柯": "Giambattista_Vico", "克罗齐": "Benedetto_Croce",
    "葛兰西": "Antonio_Gramsci", "安瑟伦": "Anselm_of_Canterbury",
    "奥古斯丁": "Augustine_of_Hippo", "布鲁诺": "Giordano_Bruno",
    "斐洛": "Philo_of_Alexandria",
    # Russian/Dutch/Others
    "斯宾诺莎": "Baruch_Spinoza", "维特根斯坦": "Ludwig_Wittgenstein",
    "克尔凯郭尔": "Soren_Kierkegaard", "波普": "Karl_Popper",
    "陀思妥耶夫斯基": "Fyodor_Dostoevsky", "托尔斯泰": "Leo_Tolstoy",
    "舍斯托夫": "Lev_Shestov", "巴赫金": "Mikhail_Bakhtin",
    "索洛维约夫": "Vladimir_Solovyov_(philosopher)",
    "埃吕尔": "Jacques_Ellul", "斯蒂格勒": "Bernard_Stiegler",
    "伊利格瑞": "Luce_Irigaray", "巴特勒": "Judith_Butler",
    "克里斯蒂娃": "Julia_Kristeva", "西克苏": "Helene_Cixous",
    # Marxists
    "马克思": "Karl_Marx", "恩格斯": "Friedrich_Engels",
    "列宁": "Vladimir_Lenin", "卢卡奇": "Gyorgy_Lukacs",
    "阿尔都塞": "Louis_Althusser", "马尔库塞": "Herbert_Marcuse",
    # Chinese
    "孔子": "Confucius", "老子": "Laozi", "庄子": "Zhuangzi_(book)",
    "孟子": "Mencius", "荀子": "Xunzi_(philosopher)", "韩非": "Han_Fei",
    "墨子": "Mozi", "王阳明": "Wang_Yangming", "朱熹": "Zhu_Xi",
    "慧能": "Huineng", "董仲舒": "Dong_Zhongshu",
    "商鞅": "Shang_Yang", "公孙龙": "Gongsun_Long",
    "周敦颐": "Zhou_Dunyi", "程颢": "Cheng_Hao", "程颐": "Cheng_Yi",
    "张载": "Zhang_Zai", "陆九渊": "Lu_Jiuyuan",
    # Indian
    "龙树": "Nagarjuna", "世亲": "Vasubandhu", "商羯罗": "Adi_Shankara",
    # Islamic
    "伊本·西那": "Avicenna", "阿威罗伊": "Averroes",
    "伊本·赫勒敦": "Ibn_Khaldun", "安萨里": "Al-Ghazali",
    # Freud/Jung/Lacan
    "弗洛伊德": "Sigmund_Freud", "荣格": "Carl_Jung", "拉康": "Jacques_Lacan",
    "弗洛姆": "Erich_Fromm",
    # Others
    "索绪尔": "Ferdinand_de_Saussure", "列维-斯特劳斯": "Claude_Levi-Strauss",
    "韦伯": "Max_Weber", "熊彼特": "Joseph_Schumpeter",
    "沃斯通克拉夫特": "Mary_Wollstonecraft",
}

fixed = 0
not_found = []
for name, info in philosophers.items():
    english_name = WIKI_MAP.get(name)
    if english_name:
        new_url = f"https://en.wikipedia.org/wiki/{english_name}"
        if info['wiki_url'] != new_url:
            info['wiki_url'] = new_url
            fixed += 1
    else:
        not_found.append(name)
        # Fallback: try URL-encoded Chinese name
        info['wiki_url'] = f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}"

print(f"Fixed: {fixed} wiki URLs")
print(f"\nNo mapping (using fallback): {len(not_found)}")
for n in not_found:
    print(f"  - {n} → https://en.wikipedia.org/wiki/{n.replace(' ', '_')}")

# Also verify a few key URLs actually work
print("\n=== Verifying key URLs ===")
test_names = ["Plato", "Confucius", "Immanuel_Kant", "Laozi", "Avicenna"]
for name in test_names:
    url = f"https://en.wikipedia.org/wiki/{name}"
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  {url} → {resp.status}")
    except Exception as e:
        print(f"  {url} → ERROR: {str(e)[:60]}")

# Rebuild the dict in content
# (philosophers dict is already updated in-memory, write back)

# Build new dict string
lines = ['PHILOSOPHERS = {']
for name, info in philosophers.items():
    bio = info['bio'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    lines.append(f'    "{name}": {{')
    lines.append(f'        "era": "{info["era"]}",')
    lines.append(f'        "country": "{info["country"]}",')
    lines.append(f'        "school": "{info["school"]}",')
    lines.append(f'        "bio": "{bio}",')
    lines.append(f'        "wiki_url": "{info["wiki_url"]}",')
    lines.append(f'    }},')
lines.append('}')

new_dict = '\n'.join(lines)

# Find and replace in content
old_start = content.find('PHILOSOPHERS = {')
depth = 0
old_end = old_start
for i in range(content.find('{', old_start), len(content)):
    if content[i] == '{': depth += 1
    elif content[i] == '}':
        depth -= 1
        if depth == 0: old_end = i + 1; break

content = content[:old_start] + new_dict + content[old_end:]

with open(DB_PATH, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"\nWritten: {len(content)} bytes. DONE!")
