/**
 * 道教 — 宗教体系详情数据
 */
export const taoism = {
  id: 'taoism', disciplineId: 'religion', name: '道教', en: 'Taoism',
  subtitle: '道法自然与长生久视——从老庄哲学到丹道、符箓与宫观丛林的演化，中国本土唯一成体系的宗教。',
  heroImage: '/more/taoism-hero.webp',
  heroQuote: '人法地，地法天，天法道，道法自然。',
  heroQuoteSource: '《道德经》第二十五章',
  meta: [
    { label: '起源', value: '东汉·张道陵创教' }, { label: '哲学源头', value: '老子·庄子' },
    { label: '信徒', value: '约2亿（中国民间）' }, { label: '两大传统', value: '哲学道家·宗教道教' },
  ],
  overview: {
    lead: [
      '道教是中国唯一成体系的本土宗教，但它有双重身份：哲学道家以老庄为代表是一种哲学；宗教道教以张道陵创教为标志是一种有神职、有宫观、有神谱的宗教。两者是并行交错两千年的双螺旋。',
      '道教的核心关切是"长生"——不是死后升天而是肉身不老。这决定了它的全部技术方向：炼丹、吐纳、导引、房中、辟谷、存思。道教不追求"死后好"而追求"不死"——这是它与世界各宗教最根本的区别。',
      '道教的"道"与基督教的"上帝"完全不同：道不是人格神而是规律，不是"创造的主体"而是"运行的法则"。"道法自然"的"自然"不是"大自然"而是"自己如此"——道不统治世界，道只是世界运行的方式。',
    ],
    sections: [
      { title: '哲学道家 vs 宗教道教', paras: [
        '道家以老庄为核心追问"道是什么如何与道合一"——这是一套哲学。道教以张道陵的五斗米道为起点追问"如何长生不死"——这是一套宗教技术。两者的桥梁是"修炼"：哲学的坐忘与宗教的存思在技术层面连续。但哲学批判宗教（庄子的坐忘不是烧丹炼汞），宗教则尊老子为太上老君（哲学被神格化）。',
      ]},
      { title: '道教的分层光谱', paras: [
        '道教从最"迷信"到最"哲学"分层折叠：民间道教（地方神符箓驱邪）→ 教团道教（天师道上清派灵宝派）→ 内丹道教（全真派内丹学）→ 哲学道教（老庄）——每一层在实践中并存。三教合一不是理念而是实践：道教神谱里有玉皇大帝、慈航道人、关公、妈祖。',
      ]},
    ],
  },
  lineage: {
    intro: '道教传承从老子的哲学种子到张道陵的宗教创教再到全真与正一两大派的分化。',
    events: [
      { period: '前6世纪', title: '老子著道德经', source: '传说', glyph: '老', color: '#a77c4f', major: true, cue: '五千言奠定道家哲学基石' },
      { period: '前4世纪', title: '庄子', source: '《庄子》三十三篇', glyph: '庄', major: true, cue: '道家哲学诗意化巅峰' },
      { period: '142', title: '张道陵创五斗米道', source: '鹤鸣山', glyph: '张', color: '#a77c4f', major: true, cue: '道教作为宗教的起点·天师道' },
      { period: '365', title: '上清派杨羲降真', source: '茅山', glyph: '上', major: true, cue: '上清经系·存思传统的确立' },
      { period: '420-589', title: '陆修静与陶弘景', source: '南朝道教改革', glyph: '陆', major: true, cue: '道教仪轨系统化·茅山宗' },
      { period: '7世纪', title: '唐代崇道', source: '李唐尊老子为祖', glyph: '唐', major: true, cue: '道教成为国教地位' },
      { period: '1113-1170', title: '王重阳创全真道', source: '金·活死人墓', glyph: '王', major: true, color: '#738e9a', cue: '全真七子·内丹革命·出家丛林制度' },
      { period: '1224', title: '丘处机西游成吉思汗', source: '《长春真人西游记》', glyph: '丘', major: true, color: '#778e6a', major: true, cue: '全真道大兴' },
      { period: '明清', title: '正一与全真两派格局', source: '——', glyph: '两', cue: '正一与全真两大道派格局定型' },
    ],
  },
  doctrines: {
    intro: '道教教义从哲学到宗教技术层层展开。',
    items: [
      { name: '道', sanskrit: 'Tao', explanation: '不可定义的终极实在："道可道非常道"。', significance: '道教哲学最高概念。' },
      { name: '无为', sanskrit: 'Wu wei', explanation: '不是不做而是不强行做——"为无为则无不治"。', significance: '道家政治哲学与修行原则。' },
      { name: '自然', sanskrit: 'Ziran', explanation: '"自己如此"——万物按其本性运行。', significance: '道法的终极标准。' },
      { name: '阴阳', sanskrit: 'Yin-Yang', explanation: '宇宙两种基本力：阴与阳互根互用此消彼长。', significance: '道教宇宙论的二元结构。' },
      { name: '精气神', sanskrit: '——', explanation: '精（生命物质）、气（生命能量）、神（生命精神）——内丹修炼的三大原料。', significance: '道教人体观核心。' },
      { name: '内丹', sanskrit: '——', explanation: '以身体为炉鼎以精气神为药物在体内炼丹——金丹不是外物而是内在觉悟状态。', significance: '唐宋后道教修行主流技术。' },
      { name: '符箓', sanskrit: '——', explanation: '朱笔符文与咒语——天师道核心法术用于驱邪治病祈福。', significance: '正一道核心宗教技术。' },
      { name: '三清', sanskrit: '——', explanation: '玉清元始天尊、上清灵宝天尊、太清道德天尊——道教神谱最高三位。', significance: '道教神谱的顶端。' },
      { name: '坐忘', sanskrit: '——', explanation: '堕肢体黜聪明离形去知同于大通——通过放下一切意识活动而与道合一。', significance: '道家哲学的禅定。' },
      { name: '心斋', sanskrit: '——', explanation: '唯道集虚虚者心斋也——以虚空之心聆听道的声音。', significance: '与坐忘并列为道家修心两大法门。' },
    ],
  },
  scriptures: {
    intro: '道教经典浩如烟海——《道藏》收录一千四百余种著作。',
    items: [
      { name: '《道德经》', era: '前6-4世纪·老子', type: '哲学道教根本经典', significance: '五千言的万经之王——被翻译成最多语言的中国书籍。' },
      { name: '《庄子》', era: '前4世纪', type: '哲学道教巅峰之作', significance: '三十三篇——汪洋恣肆的哲学寓言集。' },
      { name: '《太平经》', era: '东汉', type: '道教第一部经', significance: '道教最早的大型经书——太平理想的宗教表达。' },
      { name: '《周易参同契》', era: '东汉·魏伯阳', type: '内丹学奠基之作', significance: '万古丹经王——以内丹术语解读周易与炼丹。' },
      { name: '《黄庭经》', era: '魏晋', type: '上清派核心经典', significance: '以身体为黄庭内观身中诸神。' },
      { name: '《度人经》', era: '东晋', type: '灵宝派核心经典', significance: '仙道贵生无量度人。' },
      { name: '《悟真篇》', era: '宋·张伯端', type: '内丹南宗经典', significance: '与参同契并列为内丹双璧。' },
      { name: '《云笈七签》', era: '宋·张君房', type: '道教类书', significance: '道教小百科——从道藏精选的百二十卷。' },
      { name: '《道藏》', era: '明正统十年(1445)', type: '道教全书总集', significance: '一千四百余种著作——今日研究道教的最重要文献来源。' },
    ],
  },
  rituals: {
    intro: '道教的仪式以科仪为框架——每场法事都是精确的动作咒语符箓音乐编排。',
    items: [
      { name: '斋醮科仪', description: '道教最大仪式体系：设坛上香诵经步罡踏斗上表——为亡者超度为国祈福为个人禳灾。', purpose: '与神灵沟通的正式渠道。' },
      { name: '符箓', description: '朱笔符文配合咒语与手诀——用于驱邪治病镇宅。', purpose: '正一道核心宗教技术。' },
      { name: '内丹修炼', description: '以精气神为药物以身体为炉鼎以周天运转炼内丹。', purpose: '道教的冥想技术与生命科学。' },
      { name: '太极拳', description: '以柔克刚的武术——张三丰创太极拳的传说将道教哲学与武术合流。', purpose: '道教哲学的具象化。' },
      { name: '堪舆（风水）', description: '阴阳宅的选址与布局之术。', purpose: '道教的环境神学。' },
      { name: '扶乩', description: '以乩笔在沙盘上书写神灵启示。', purpose: '神人沟通的技术性方案。' },
    ],
  },
  branches: {
    intro: '道教有正一与全真两大传统以及众多民间派别。',
    items: [
      { name: '正一道（天师道）', era: '142张道陵创', coreBelief: '以符箓斋醮为主，可娶妻生子居家修行——天师世代以张家血统传承。', regions: '江西龙虎山、茅山、全国', distinction: '正一道士可娶妻生子吃荤——道教中的在家传统。' },
      { name: '全真道', era: '1167王重阳创', coreBelief: '以内丹修炼为核心出家住观素食独身——全真意为保全真性。', regions: '北京白云观、陕西重阳宫、全国', distinction: '全真七子各创一派（龙门派最大）——道教的禅宗。' },
      { name: '上清派（茅山宗）', era: '东晋杨羲', coreBelief: '以存思内观身中诸神与诵经为核心。', regions: '茅山', distinction: '最文学化的教派。' },
      { name: '灵宝派', era: '东晋葛巢甫', coreBelief: '以灵宝经为核心强调普度众生。', regions: '江西閤皂山', distinction: '道教最完整的仪式体系。' },
    ],
  },
  bridges: {
    intro: '道教与哲学的勾连最自然——因为它本身就是中国哲学的重要源头之一。',
    items: [
      { religion: '无为', philosophy: '政治哲学的最小政府', note: '汉初黄老之治的文景之治——道家的无为被实践为中国历史上最好的治理时期之一。', links: [{ type: 'author', name: '老子' }] },
      { religion: '道与语言', philosophy: '维特根斯坦与不可言说', note: '道可道非常道与维特根斯坦对于不可说的保持沉默——两种文明在同一处碰头。', links: [] },
      { religion: '庄子蝴蝶', philosophy: '认识论与梦境', note: '不知周之梦为蝴蝶与蝴蝶之梦为周与——庄子以蝴蝶论梦比笛卡尔的恶魔早两千年。', links: [{ type: 'author', name: '庄子' }] },
      { religion: '内丹与身体', philosophy: '身体现象学', note: '内丹学把身体视为炉鼎——精气神的转化是一套完整的身体现象学。', links: [] },
      { religion: '道法自然', philosophy: '深层生态学', note: '道法自然与深层生态学的自然有内在价值——道教是最早的生态哲学之一。', links: [] },
    ],
  },
  keywords: ['道', '无为', '自然', '阴阳', '精气神', '内丹', '符箓', '三清', '洞天福地', '坐忘', '心斋', '道德经', '庄子', '张道陵', '全真道', '正一道', '茅山', '太极拳', '道藏', '云笈七签'],
  keywordGlosses: {
    '道': '不可定义的终极实在——万物的本源与运行的法则。', '无为': '不是不做而是不强行做。',
    '自然': '自己如此——万物按其本性运行。', '阴阳': '宇宙两种基本力互根互用。',
    '精气神': '生命三宝——内丹修炼的三大原料。', '内丹': '以身体为炉鼎炼精气神。',
    '符箓': '朱笔符文与咒语——正一道核心法术。', '三清': '道教神谱最高三位。',
    '洞天福地': '三十六洞天七十二福地。', '坐忘': '堕肢体黜聪明离形去知。',
    '心斋': '唯道集虚——以虚空之心聆听道的声音。', '道德经': '五千言的万经之王。',
    '庄子': '三十三篇哲学寓言集。', '张道陵': '东汉创五斗米道——道教起点。',
    '全真道': '王重阳创——内丹为核心的出家宗派。', '正一道': '张道陵创——可娶妻的符箓道派。',
    '茅山': '上清派祖庭——存思传统的中心。', '太极拳': '以柔克刚的武术。',
    '道藏': '明正统十年编——一千四百余种道教著作总集。', '云笈七签': '宋张君房编——道教类书精选。',
  },
  keywordTargets: {
    '道': {'sec': 'sec-doctrine'}, '无为': {'sec': 'sec-doctrine'}, '自然': {'sec': 'sec-doctrine'},
    '阴阳': {'sec': 'sec-doctrine'}, '精气神': {'sec': 'sec-doctrine'}, '内丹': {'sec': 'sec-ritual'},
    '符箓': {'sec': 'sec-ritual'}, '三清': {'sec': 'sec-pantheon'}, '洞天福地': {'sec': 'sec-overview'},
    '坐忘': {'sec': 'sec-doctrine'}, '心斋': {'sec': 'sec-doctrine'}, '道德经': {'sec': 'sec-scripture'},
    '庄子': {'sec': 'sec-scripture'}, '张道陵': {'sec': 'sec-lineage'}, '全真道': {'sec': 'sec-branch'},
    '正一道': {'sec': 'sec-branch'}, '茅山': {'sec': 'sec-branch'}, '太极拳': {'sec': 'sec-ritual'},
    '道藏': {'sec': 'sec-scripture'}, '云笈七签': {'sec': 'sec-scripture'},
  },
  crossLinks: {
    schools: ['道家'], authors: ['老子', '庄子'],
    books: [
      { title: '《道德经》', note: '陈鼓应注译通行' },
      { title: '《庄子》', note: '郭象注本通行' },
      { title: '《道藏》', note: '明正统道藏' },
    ],
  },
  epilogue: '道教最深的智慧不是告诉你该做什么，而是告诉你不该强行做什么。无为不是躺平——是一种对何时出手何时等待的精准感知。道法自然的自然最终指向的不是山川草木而是你自己的本性。',
};
