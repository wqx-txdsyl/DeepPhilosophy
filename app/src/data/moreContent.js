/**
 * 更多 — 学科数据（神话/宗教/心理/社会/历史/政治）
 * 三级结构：/more（学科索引）→ /more/:discipline（学科）→ /more/:discipline/:topic（详情）
 * color 取自站内既有的低饱和手稿色系（badge 世界/西方/东方 + 流派卡用色）
 */
export const DISCIPLINES = [
  {
    id: 'mythology',
    code: 'My',
    name: '神话',
    en: 'Mythology',
    color: '#A86B3C',
    desc: '哲学从神话中分娩——前苏格拉底诸贤正是以"祛魅"神话开启思辨；而神话从未退场，它沉淀为文学、心理学与流行文化中最深的集体潜意识。',
    topics: [
      { id: 'chinese', heroImage: '/more/chinese-hero.webp', name: '中国神话', note: '盘古开天、女娲造人——《山海经》《楚辞》《淮南子》中的诸神碎片与民间信仰的层累' },
      { id: 'honghuang', heroImage: '/more/honghuang-hero.webp', name: '洪荒流', note: '网络文学的神话宇宙重构：从鸿钧讲道、巫妖大战到封神演义的当代创世谱系' },
      { id: 'japanese', heroImage: '/more/japanese-hero.webp', name: '日本神话', note: '伊邪那岐生成列岛，天照隐入岩户——《古事记》神代卷与神道想象的源头' },
      { id: 'biblical', heroImage: '/more/biblical-hero.webp', name: '圣经神话', note: '创世、堕落、大洪水与巴别塔——塑造了半个世界想象力的原型文本' },
      { id: 'greek', heroImage: '/more/greek-hero.webp', name: '希腊神话', note: '奥林匹斯神系与英雄史诗——从赫西俄德《神谱》到西方文艺的永恒母题' },
      { id: 'egyptian', heroImage: '/more/egyptian-hero.webp', name: '埃及神话', note: '拉神夜巡冥河，奥西里斯死而复生——玛阿特秩序与永恒来世的宇宙论' },
      { id: 'indian', heroImage: '/more/indian-hero.webp', name: '印度神话', note: '梵天、毗湿奴与湿婆的循环宇宙——《摩诃婆罗多》《往世书》的神系迷宫' },
      { id: 'norse', heroImage: '/more/norse-hero.webp', name: '日耳曼神话', note: '奥丁自缢献祭求取卢恩，世界树与诸神黄昏——冰与火的北欧命运观' },
      { id: 'mesopotamian', heroImage: '/more/mesopotamian-hero.webp', name: '美索不达米亚神话', note: '吉尔伽美什求不朽，《埃努玛·埃利什》以马尔杜克创世——最古老的史诗现场' },
      { id: 'celtic', heroImage: '/more/celtic-hero.webp', name: '凯尔特神话', note: '德鲁伊、图哈德达南与芬恩传奇——欧洲最古老的口传灵性传统' },
      { id: 'roman', heroImage: '/more/roman-hero.webp', name: '罗马神话', note: '希腊神系的罗马变奏——朱庇特、玛尔斯与维吉尔笔下的埃涅阿斯' },
      { id: 'cthulhu', heroImage: '/more/cthulhu-hero.webp', name: '克苏鲁神话', note: '洛夫克拉夫特的宇宙恐怖——在不可名状的旧日支配者面前重学人类的谦卑' },
    ],
  },
  {
    id: 'religion',
    code: 'Re',
    name: '宗教',
    en: 'Religion',
    color: '#6B3FA0',
    desc: '信仰与理性两千年的对话——中世纪经院哲学、佛教因明与道教玄学，皆是哲学与宗教互相成就的现场；不了解宗教，就读不懂一半的哲学史。',
    topics: [
      { id: 'buddhism', heroImage: '/more/buddhism-hero.webp', name: '佛教', note: '四圣谛、缘起与性空——从释迦牟尼的觉悟到大小乘论师们的因明思辨' },
      { id: 'christianity', heroImage: '/more/catholic-hero.webp', name: '基督教', note: '三位一体与道成肉身——尼西亚信经以降的信仰体系，经院哲学的母体',
        children: ['东正教', '天主教', '新教'] },
      { id: 'orthodox', hidden: true, heroImage: '/more/orthodox-hero.webp', name: '东正教', note: '圣像与静默——拜占庭传统的守护者，七次大公会议的正统继承' },
      { id: 'catholic', hidden: true, heroImage: '/more/catholic-hero.webp', name: '天主教', note: '彼得之座与圣统制——从君士坦丁到宗教改革前的西方信仰中枢' },
      { id: 'protestant', hidden: true, heroImage: '/more/protestant-hero.webp', name: '新教', note: '唯独圣经与因信称义——1517年路德的革命与千万个教派的诞生' },
      { id: 'islam', heroImage: '/more/islam-hero.webp', name: '伊斯兰教', note: '五功六信与认主独一——凯拉姆思辨神学、苏非神秘主义与教法传统' },
      { id: 'hinduism', heroImage: '/more/hinduism-hero.webp', name: '印度教', note: '从吠陀祭祀到吠檀多不二论——达摩、业报与解脱的永恒循环' },
      { id: 'taoism', heroImage: '/more/taoism-hero.webp', name: '道教', note: '道法自然与长生久视——从老庄哲学到丹道、符箓与宫观丛林的演化' },
    ],
  },
  {
    id: 'literature',
    code: 'Li',
    name: '文学',
    en: 'Literature',
    desc: '文学是哲学的叙事化——从史诗到小说，从悲剧到诗歌，文学用形象回答哲学用概念追问的问题。',
    topics: [
      { id: 'classical-chinese', name: '中国古典文学', note: '从诗经楚辞到唐诗宋词——中国文学三千年的审美传统' },
      { id: 'western-classics', name: '西方经典文学', note: '从荷马史诗到现代主义——西方文学的宏大叙事传统' },
      { id: 'russian-lit', name: '俄国文学', note: '从普希金到陀思妥耶夫斯基——俄国文学的灵魂拷问传统' },
      { id: 'latin-american', name: '拉美文学', note: '从博尔赫斯到马尔克斯——魔幻现实主义的拉美 explosion' },
      { id: 'japanese-lit', name: '日本文学', note: '从源氏物语到村上春树——日本文学的物哀与孤独' },
      { id: 'comparative', name: '比较文学', note: '跨越语言与文明的文学对话——影响研究·平行研究·译介学' },
    ],
  },
  {
    id: 'psychology',
    code: 'Ps',
    name: '心理',
    en: 'Psychology',
    color: '#3A5A7C',
    desc: '哲学的现代分流——意识、自我与无意识的问题，从洛克的经验论、叔本华的意志出发，一路走进了实验室与诊疗室；每座心理学流派脚下都埋着一部哲学前史。',
    topics: [
      { id: 'structuralism', name: '构造主义/结构主义', note: '冯特与铁钦纳——以内省法把意识拆解为感觉元素的第一座实验室' },
      { id: 'functionalism', name: '机能主义', note: '詹姆斯与杜威——不问意识"是什么"，只问它"有什么用"，与实用主义合流' },
      { id: 'behaviorism', name: '行为主义', note: '华生与斯金纳——刺激-反应的黑箱心理学，把意识逐出科学二十余年' },
      { id: 'psychoanalysis', name: '精神分析', note: '弗洛伊德与荣格——无意识、梦与力比多；叔本华与尼采的意志论是它的哲学先声，与哲学流派的勾连最深', philosophyLink: true },
      { id: 'humanistic', name: '人本主义心理学', note: '马斯洛与罗杰斯——需要层次与自我实现，与存在主义共振的"第三势力"' },
      { id: 'cognitive', name: '认知心理学', note: '信息加工的革命——把心智重新请回实验室，视心灵为计算系统' },
      { id: 'neuroscience', name: '生理心理学/认知神经科学', note: '从神经元到意识——心智的生物学基础，与心身问题正面相撞' },
      { id: 'evolutionary', name: '进化心理学', note: '自然选择塑造的心智模块——更新世草原上进化出的现代头脑' },
      { id: 'cultural', name: '文化心理学/跨文化心理学', note: '心智是文化的产物——独立我与互依我，心理学的人类学转向' },
      { id: 'positive', name: '积极心理学', note: '塞利格曼——从治愈疾病到建构幸福，亚里士多德幸福论的实验回归' },
      { id: 'postmodern', name: '后现代心理学/社会建构论', note: '心理话语本身即建构——自我是被叙述出来的，与后现代哲学同气连枝' },
    ],
  },
  {
    id: 'sociology',
    code: 'So',
    name: '社会学',
    en: 'Sociology',
    color: '#4A7A4A',
    desc: '从共同体到社会——孔德、马克思与韦伯都先是哲学家；社会学的每个大问题：秩序何以可能、个体与结构、现代性的命运，都仍是哲学问题。',
    planned: true,
    seeds: ['古典三大家：马克思 · 涂尔干 · 韦伯', '孔德与实证主义', '符号互动论', '结构功能主义', '批判理论与公共领域', '齐美尔与形式社会学'],
  },
  {
    id: 'history',
    code: 'Hi',
    name: '历史学',
    en: 'History',
    color: '#9B3A3A',
    desc: '一切思想都有时间性——思辨的历史哲学追问人类是否有方向，分析的历史哲学追问历史叙述是否为真；哲学与历史在此互为镜像。',
    planned: true,
    seeds: ['希罗多德与修昔底德', '兰克与客观主义史学', '思辨历史哲学：康德 · 黑格尔 · 马克思', '年鉴学派', '分析历史哲学：狄尔泰 · 柯林武德', '汤因比与文明形态学'],
  },
  {
    id: 'politics',
    code: 'Po',
    name: '政治学',
    en: 'Political Science',
    color: '#3A7B8C',
    desc: '城邦与正义——从柏拉图《理想国》到罗尔斯《正义论》，政治学是哲学最古老的应用现场：权力如何正当、自由与平等如何两全。',
    planned: true,
    seeds: ['理想国与哲学王', '马基雅维利的转向', '社会契约论：霍布斯 · 洛克 · 卢梭', '密尔与自由主义', '汉娜·阿伦特与极权主义', '罗尔斯《正义论》'],
  },
];

export function getDiscipline(id) {
  return DISCIPLINES.find(d => d.id === id);
}

export function getTopic(disciplineId, topicId) {
  const d = getDiscipline(disciplineId);
  if (!d) return null;
  const topic = d.topics?.find(t => t.id === topicId);
  return topic ? { ...topic, discipline: d } : null;
}
