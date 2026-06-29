"""Build Greek sub-schools: 伊壁鸠鲁学派, 犬儒学派, 新柏拉图主义"""
import json, os

schools = {}

schools['伊壁鸠鲁学派'] = {
    "name": "伊壁鸠鲁学派", "subtitle": "快乐即至善——花园中的哲学",
    "overview": "伊壁鸠鲁学派由伊壁鸠鲁于公元前307年在雅典创立，因其在花园中讲学而被称为花园哲学。该学派以追求心灵宁静（ataraxia）为人生至善，继承并改造了德谟克利特的原子论，认为诸神不干预人世、死亡是原子的消散无需恐惧。是最早接纳女性和奴隶的哲学共同体，其伦理学以快乐为核心——但不是纵欲，而是通过理性计算达到身体无痛苦、灵魂无纷扰的状态。延续约600年，深刻影响了卢克莱修、伽森狄和近代功利主义。",
    "quote": "死亡与我们无关——因为当我们存在时，死亡尚未到来；当死亡到来时，我们已不存在。", "quoteAuthor": "伊壁鸠鲁",
    "timeline": [
        {"year":"前341","event":"伊壁鸠鲁诞生","detail":"生于萨摩斯岛。","type":"birth"},
        {"year":"前307","event":"创立花园学派","detail":"在雅典购置花园建立哲学共同体。","type":"event"},
        {"year":"前270","event":"伊壁鸠鲁去世","detail":"临终仍写信安慰弟子。","type":"event"},
        {"year":"约前50","event":"卢克莱修著物性论","detail":"以拉丁史诗推广伊壁鸠鲁哲学。","type":"book"},
    ],
    "thinkers": [
        {"name":"伊壁鸠鲁","sub":"花园学派","era":"前341-前270","influence":9,"key":"快乐即至善","works":["论自然","致美诺西斯的信"]},
        {"name":"卢克莱修","sub":"罗马伊壁鸠鲁派","era":"约前99-前55","influence":8,"key":"物性论","works":["物性论"]},
    ],
    "relations": [{"from":"伊壁鸠鲁","to":"德谟克利特","label":"继承原子论"},{"from":"伊壁鸠鲁","to":"卢克莱修","label":"思想传承"}],
    "cihai": [
        {"word":"Ataraxia","def":"心灵宁静——伊壁鸠鲁伦理学的终极目标。","source":"伊壁鸠鲁《致美诺西斯的信》"},
        {"word":"Tetrapharmakos","def":"四药方：不惧神、不畏死、善易得、恶可忍。","source":"菲洛德穆残篇"},
    ],
    "quotes": [{"text":"死亡与我们无关。","author":"伊壁鸠鲁","exp":"消除死亡恐惧的经典论证。"}],
    "works": [{"title":"物性论","author":"卢克莱修","era":"约前50","desc":"拉丁史诗系统阐述原子论与伊壁鸠鲁伦理学。"}],
    "conclusion": "伊壁鸠鲁学派证明哲学可以是一种生活方式——不是书斋中的玄思，而是对恐惧的治愈和对宁静的追求。",
    "closingQuote": "死亡与我们无关。——伊壁鸠鲁",
}

schools['犬儒学派'] = {
    "name": "犬儒学派", "subtitle": "摒弃世俗，回归自然",
    "overview": "犬儒学派由安提斯泰尼于公元前4世纪创立于雅典，第欧根尼为其最著名代表。学派名称源自希腊语kynikos（狗一样的），因其成员摒弃社会习俗、追求极端简朴的生活方式而得名。第欧根尼以木桶为家，在正午举灯寻找真正的人，对亚历山大大帝说别挡我晒太阳。犬儒学派对斯多葛学派产生深远影响，其世界公民概念成为后世普世主义的思想源泉。",
    "quote": "别挡我晒太阳。", "quoteAuthor": "第欧根尼（对亚历山大大帝）",
    "timeline": [
        {"year":"约前444","event":"安提斯泰尼诞生","detail":"苏格拉底弟子，犬儒学派创立者。","type":"birth"},
        {"year":"约前412","event":"第欧根尼诞生","detail":"犬儒学派最著名代表。","type":"birth"},
        {"year":"约前336","event":"第欧根尼与亚历山大相遇","detail":"对大帝说：别挡我晒太阳。","type":"event"},
    ],
    "thinkers": [
        {"name":"安提斯泰尼","sub":"犬儒学派创立者","era":"约前444-前365","influence":8,"key":"德性即自足","works":["赫拉克勒斯对话录[残篇]"]},
        {"name":"第欧根尼","sub":"犬儒学派","era":"约前412-前323","influence":9,"key":"回归自然","works":["共和国[残篇]"]},
    ],
    "relations": [{"from":"苏格拉底","to":"安提斯泰尼","label":"师承"},{"from":"安提斯泰尼","to":"第欧根尼","label":"师生"}],
    "cihai": [
        {"word":"Kynikos","def":"犬儒学派的名称来源，指像狗一样无视社会礼仪地生活。","source":"第欧根尼·拉尔修《名哲言行录》"},
        {"word":"Kosmopolites","def":"世界公民——第欧根尼提出，不属于任何城邦而属于整个世界。","source":"第欧根尼·拉尔修《名哲言行录》"},
    ],
    "quotes": [{"text":"别挡我晒太阳。","author":"第欧根尼","exp":"对权力和财富的终极蔑视。"}],
    "works": [{"title":"名哲言行录","author":"第欧根尼·拉尔修","era":"约3世纪","desc":"保存了犬儒学派主要思想与轶事。"}],
    "conclusion": "犬儒学派以最激进的方式追问：什么是真正值得过的生活？答案是——按照自然，而非按照习俗。",
    "closingQuote": "别挡我晒太阳。——第欧根尼",
}

schools['新柏拉图主义'] = {
    "name": "新柏拉图主义", "subtitle": "太一流溢——归向至善",
    "overview": "新柏拉图主义是公元3世纪由普罗提诺创立的哲学学派，整合了柏拉图、亚里士多德与斯多葛思想。核心学说是太一流溢说——太一超越一切存在，从中流溢出理智、理智流溢出灵魂、灵魂下降为物质世界。人的使命是通过哲学沉思逆转下降之路回归太一。深刻影响了奥古斯丁的基督教神学、伊斯兰哲学和中世纪神秘主义，是古代哲学的最后辉煌。",
    "quote": "太一超越一切存在。", "quoteAuthor": "普罗提诺《九章集》",
    "timeline": [
        {"year":"204","event":"普罗提诺诞生","detail":"生于埃及吕科波利斯。","type":"birth"},
        {"year":"244","event":"普罗提诺赴罗马","detail":"建立哲学学校。","type":"event"},
        {"year":"约300","event":"波菲利编纂九章集","detail":"54篇论文编为6组9篇。","type":"book"},
        {"year":"529","event":"雅典学园关闭","detail":"新柏拉图主义作为独立学派终结。","type":"event"},
    ],
    "thinkers": [
        {"name":"普罗提诺","sub":"新柏拉图主义创立者","era":"204-270","influence":10,"key":"太一流溢说","works":["九章集"]},
        {"name":"波菲利","sub":"新柏拉图主义","era":"约234-305","influence":8,"key":"范畴篇导论","works":["普罗提诺生平"]},
        {"name":"普罗克洛","sub":"雅典新柏拉图主义","era":"412-485","influence":8,"key":"神学要义","works":["神学要义"]},
    ],
    "relations": [{"from":"柏拉图","to":"普罗提诺","label":"思想源头"},{"from":"普罗提诺","to":"波菲利","label":"师生"},{"from":"普罗提诺","to":"奥古斯丁","label":"影响基督教神学"}],
    "cihai": [
        {"word":"太一(To Hen)","def":"新柏拉图主义最高本原，超越存在与思想。","source":"普罗提诺《九章集》"},
        {"word":"流溢(Emanation)","def":"太一不损耗自身而产生万物的过程。","source":"普罗提诺《九章集》"},
        {"word":"Nous(理智)","def":"从太一流溢出的第二层实在。","source":"普罗提诺《九章集》"},
    ],
    "quotes": [{"text":"太一超越一切存在。","author":"普罗提诺","exp":"表达了超越性的极致。"}],
    "works": [{"title":"九章集","author":"普罗提诺","era":"约270","desc":"波菲利编纂的54篇论文。"}],
    "conclusion": "新柏拉图主义是古代哲学的集大成者——用希腊哲学的理性语言表达了人类对超越性的永恒渴望。",
    "closingQuote": "努力将你内心的神归还给宇宙中的神。——普罗提诺遗言",
}

for name, data in schools.items():
    for d in ['data', '../app/public/schools']:
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, f'school_{name}.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'{name}: OK')

print('All 3 created')
