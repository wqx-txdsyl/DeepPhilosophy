/**
 * 印度教 — 宗教体系详情数据
 */
export const hinduism = {
  id: 'hinduism', disciplineId: 'religion', name: '印度教', en: 'Hinduism',
  subtitle: '从吠陀祭祀到吠檀多不二论——达摩、业报与解脱的永恒循环，人类最古老的活宗教。',
  heroImage: '/more/hinduism-hero.webp',
  heroQuote: '梵我合一。',
  heroQuoteSource: '奥义书',
  meta: [
    { label: '信徒', value: '约12亿' }, { label: '经典', value: '吠陀·奥义书·薄伽梵歌' },
    { label: '主神', value: '梵天·毗湿奴·湿婆' }, { label: '核心', value: '达摩·业报·解脱' },
  ],
  overview: {
    lead: [
      '印度教不是"一个宗教"而是一个"宗教生态圈"：没有创始人、没有统一教义、没有教会——只有一套共通的框架（吠陀权威、种姓、业报轮回、解脱目标）在这框架下容纳几乎任何形式的信仰与实践。',
      '它的文献层深不见底：吠陀四部、奥义书一百零八部、两大史诗百万颂、十八部往世书——每一层都在前一层之上添砖而不删除前一层。',
      '印度教对哲学的最大贡献是"梵我合一"：宇宙终极实在是"梵"（不可言说），而人的内核"阿特曼"与之本质相同——"你即是它"。不二论说这是唯一真相；有形论说这是需要修行的目标。',
    ],
    sections: [
      { title: '种姓制度与业报', paras: ['印度教社会以种姓（Varna：婆罗门/刹帝利/吠舍/首陀罗）为基础，业报轮回为神学根据：你的出生是你前世行为的结果。现代印度宪法已废除种姓歧视但社会惯性仍在。'] },
      { title: '三大主神与化身', paras: ['梵天（创造）、毗湿奴（维护）、湿婆（毁灭/再生）。毗湿奴十大化身各对应一次"神对世界的干预"。湿婆坦达瓦之舞即宇宙的生灭节律。'] },
    ],
  },
  lineage: {
    intro: '从吠陀时代到现代——印度教的传承是一部不断吸收与包容的历史。',
    events: [
      { period: '前1500', title: '吠陀时代', source: '《梨俱吠陀》', glyph: '吠', color: '#a77c4f', major: true, cue: '口传千年的颂神诗集' },
      { period: '前800-500', title: '奥义书时代', source: '《奥义书》', glyph: '奥', major: true, cue: '哲学转向：从祭祀到梵我' },
      { period: '前400-400', title: '史诗时代', source: '《摩诃婆罗多》《罗摩衍那》', glyph: '史', major: true, cue: '两大史诗编纂' },
      { period: '300-1500', title: '往世书与巴克提运动', source: '十八部往世书', glyph: '往', cue: '神话百科与虔信运动' },
      { period: '788-820', title: '商羯罗不二论', source: '《梵经注》', glyph: '商', major: true, cue: '吠檀多不二论哲学巅峰' },
      { period: '19世纪', title: '印度教改革', source: '罗易·辨喜·甘地', glyph: '辨', cue: '面对殖民与现代性的自我更新' },
    ],
  },
  doctrines: {
    intro: '印度教教义以解脱为终极目标、以达摩为日常准则——核心概念构成一套完整的存在论与解脱论。',
    items: [
      { name: '梵', sanskrit: 'Brahman', explanation: '宇宙终极实在：无形、无属性、不可言说。', significance: '吠檀多哲学的至高概念。' },
      { name: '阿特曼', sanskrit: 'Atman', explanation: '个体灵魂内核——与梵本质相同。', significance: '梵我合一是奥义书核心命题。' },
      { name: '达摩', sanskrit: 'Dharma', explanation: '法、正道、各安其位的天职。', significance: '印度伦理总纲。' },
      { name: '业报', sanskrit: 'Karma', explanation: '身口意三业跨生死结果——没有随机事件。', significance: '印度宇宙观的因果律。' },
      { name: '轮回', sanskrit: 'Samsara', explanation: '生死流转的巨轮。', significance: '解脱是唯一的出口。' },
      { name: '解脱', sanskrit: 'Moksha', explanation: '从轮回中彻底自由——与梵合一。', significance: '印度教终极目标。' },
      { name: '不二论', sanskrit: 'Advaita', explanation: '商羯罗：梵与阿特曼不二——世界是摩耶（幻）。', significance: '吠檀多哲学巅峰。' },
      { name: '瑜伽', sanskrit: 'Yoga', explanation: '与"合一"同义——帕坦伽利八支瑜伽路线图。', significance: '身心转化的技术体系。' },
      { name: '萨克蒂', sanskrit: 'Shakti', explanation: '宇宙能量女性面——杜尔迦、迦梨、拉克什米皆为显化。', significance: '女神传统的本体论。' },
      { name: '薄伽梵歌的无执之行', sanskrit: 'Nishkama Karma', explanation: '你有权行动，无权执于结果——行动义务与结果解脱的二分。', significance: '印度伦理学最高公式。' },
    ],
  },
  scriptures: {
    intro: '印度教经典体量是所有宗教中最庞大的。',
    items: [
      { name: '《梨俱吠陀》', era: '前1500年口传', type: '颂神诗集', significance: '十颂1028首——人类最古老的宗教诗歌集。' },
      { name: '《奥义书》', era: '前800-前300', type: '哲学终章', significance: '一百零八部——梵我合一的思辨总集。' },
      { name: '《薄伽梵歌》', era: '前2世纪', type: '十八章讲道', significance: '印度教的新约——克里希那在战场上的讲道。' },
      { name: '《摩诃婆罗多》', era: '前400-400', type: '世界最长史诗', significance: '十万颂——"这里有的，别处也有"。' },
      { name: '《罗摩衍那》', era: '前3世纪', type: '最初之诗', significance: '罗摩救悉多的理想君王叙事。' },
    ],
  },
  rituals: {
    intro: '印度教的仪式构成一套"生活即宗教"的体系。',
    items: [
      { name: '普迦（Puja）', description: '向神像献花灯香食——最日常的礼拜形式。', purpose: '与神建立日常关系。' },
      { name: '瑜伽', description: '八支瑜伽：从禁制到三摩地。', purpose: '身心转化的技术体系。' },
      { name: '恒河沐浴', description: '在恒河中沐浴以洗去罪业。', purpose: '圣河的净化力量。' },
      { name: '火祭（Yajna）', description: '以火为中介将祭品送往诸神。', purpose: '火是神与人之间的使者。' },
      { name: '排灯节', description: '以灯火庆祝光明战胜黑暗。', purpose: '年度光之庆典。' },
      { name: '火葬', description: '死后火葬、骨灰撒入恒河。', purpose: '死亡是灵魂的一次换衣。' },
    ],
  },
  branches: {
    intro: '印度教四大宗派，共同以吠陀为最高权威。',
    items: [
      { name: '湿婆派', era: '远古', coreBelief: '湿婆为至高神。', regions: '南印度、克什米尔', distinction: '克什米尔不二论尤为深刻。' },
      { name: '毗湿奴派', era: '远古', coreBelief: '毗湿奴为至高神，虔信为核心。', regions: '北印度', distinction: '印度教最大宗派。' },
      { name: '萨克蒂派', era: '远古', coreBelief: '女神为至高存在。', regions: '孟加拉', distinction: '女神力量的崇拜。' },
      { name: 'smarta传统', era: '古典', coreBelief: '五神同等崇拜。', regions: '南印度婆罗门', distinction: '多元主义的古典范本。' },
    ],
  },
  bridges: {
    intro: '印度教与哲学的勾连是最深的——吠檀多与奥义书本身就是哲学文本。',
    items: [
      { religion: '梵我合一', philosophy: '吠檀多不二论', note: '商羯罗：世界是摩耶（幻），唯有梵是真。', links: [] },
      { religion: '业报与轮回', philosophy: '叔本华与康德', note: '叔本华以印度教业报观对照康德道德律。', links: [] },
      { religion: '瑜伽', philosophy: '身心哲学与当代科学', note: '帕坦伽利瑜伽的冥想技术被现代神经科学验证。', links: [] },
      { religion: '薄伽梵歌的无执之行', philosophy: '义务论与行动哲学', note: '你有权行动，无权执于结果。', links: [] },
    ],
  },
  keywords: ['梵', '阿特曼', '达摩', '业报', '轮回', '解脱', '瑜伽', '不二论', '商羯罗', '薄伽梵歌', '摩诃婆罗多', '种姓', '萨克蒂', '林伽', '恒河', '排灯节', '奥义书', '吠陀', '毗湿奴', '湿婆'],
  keywordGlosses: {
    '梵': '宇宙终极实在——无形无属性不可言说。', '阿特曼': '个体灵魂内核——与梵本质相同。',
    '达摩': '法、正道、天职。', '业报': '身口意三业跨生死结果。',
    '轮回': '生死流转的巨轮。', '解脱': '从轮回中彻底自由。',
    '瑜伽': '与合一同义——身心转化的技术。', '不二论': '梵与阿特曼不二——商羯罗哲学。',
    '商羯罗': '吠檀多不二论的哲学巅峰。', '薄伽梵歌': '克里希那在战场上的十八章讲道。',
    '摩诃婆罗多': '十万颂的世界最长史诗。', '种姓': 'Varna/Jati——印度教的社会分层。',
    '萨克蒂': '宇宙能量的女性面。', '林伽': '湿婆的无相之柱形圣物。',
    '恒河': '自天而降经湿婆发间缓流的圣河。', '排灯节': '光明战胜黑暗的年度庆典。',
    '奥义书': '吠陀文献的哲学终章。', '吠陀': '四部最古老圣典。',
    '毗湿奴': '维护之神，十大化身。', '湿婆': '毁灭与再生之神，舞王。',
  },
  keywordTargets: {
    '梵': {'sec': 'sec-doctrine'}, '阿特曼': {'sec': 'sec-doctrine'}, '达摩': {'sec': 'sec-doctrine'},
    '业报': {'sec': 'sec-doctrine'}, '轮回': {'sec': 'sec-doctrine'}, '解脱': {'sec': 'sec-doctrine'},
    '瑜伽': {'sec': 'sec-ritual'}, '不二论': {'sec': 'sec-doctrine'}, '商羯罗': {'sec': 'sec-strata'},
    '薄伽梵歌': {'sec': 'sec-scripture'}, '摩诃婆罗多': {'sec': 'sec-strata'}, '种姓': {'sec': 'sec-overview'},
    '萨克蒂': {'sec': 'sec-pantheon'}, '林伽': {'sec': 'sec-ritual'}, '恒河': {'sec': 'sec-ritual'},
    '排灯节': {'sec': 'sec-ritual'}, '奥义书': {'sec': 'sec-scripture'}, '吠陀': {'sec': 'sec-scripture'},
    '毗湿奴': {'sec': 'sec-pantheon'}, '湿婆': {'sec': 'sec-pantheon'},
  },
  crossLinks: {
    schools: ['吠檀多哲学'], authors: [],
    books: [
      { title: '《薄伽梵歌》', note: '站内未收录' },
      { title: '《奥义书》', note: '站内未收录' },
      { title: '《瑜伽经》', note: '站内未收录' },
    ],
  },
  epilogue: '印度教不提供结局——创造之后是毁灭，毁灭之后又是创造。湿婆的舞跳了四十三亿年还没停。所谓解脱，只是观众席上的那个位置。',
};
