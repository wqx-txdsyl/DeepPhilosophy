/**
 * 中国神话 — 详情数据组装（模块入口）
 * 神谱图节点为 17 位核心神祇；全部词条 100 位按 category 在"神祇名册"分组展示
 */
import { overview } from './overview';
import { cosmogony } from './cosmogony';
import { DEITIES_CORE } from './deities.core';
import { DEITIES_EXPANDED } from './deities.expanded';
import { MOTIFS_A } from './motifs.a';
import { MOTIFS_B } from './motifs.b';
import { strata } from './strata';
import { bridges } from './bridges';
import { keywords, crossLinks, epilogue, keywordGlosses } from './misc';
import { DEITY_ICONS } from './deityIcons';

/* 幽灵大字：每幕/每则母题的核心概念词 */
const ACT_FOCUS = {
  '混沌如鸡子': '混沌', '阴阳剖判': '阴阳', '垂死化身': '化身',
  '抟土造人': '造人', '天柱折': '触山', '炼石补天': '补天',
};
const MOTIF_FOCUS = {
  jueditiantong: '天梯', jianmu: '建木', xiheyuri: '浴日', changxiyuyue: '浴月',
  zhulongsi: '昼夜', duanao: '四极',
  shiri: '十日', hongshui: '洪水', nvba: '旱魃', guixu: '归墟', longbo: '钓鳌', kuaefushan: '负山',
  shejiuri: '射日', zhuliuhai: '六害', kuafuzhuri: '逐日', jingweitianhai: '填海',
  xingtianwuganqi: '干戚', gunxixirang: '息壤', yudaojiushui: '疏导', yusan: '家门',
  tangdaosanglin: '桑林', yishehebo: '河伯',
  niulangzhinv: '鹊桥', changebengyue: '奔月', xiangfeileizhu: '泪竹', wushanyunyu: '云雨',
  tushanjiuwei: '九尾', xiaoshinongyu: '凤台', yuexialaoren: '赤绳',
  gunhuaxiong: '黄熊', nvwachang: '化育', changehuachan: '化蟾', wangdihuajuan: '化鹃',
  matouniang: '蚕马', hankouxiangsi: '相思', qimushi: '石破',
  kunlunxuanpu: '悬圃', penglai: '三山', buzhoushan: '天柱', fusang: '扶桑',
  yaochi: '瑶池', qingqiu: '狐国', ruoshui: '弱水', guyeshan: '极北',
  cangjiezizhiye: '天雨粟', kuigu: '雷鼓', nvwasheng: '笙簧', yaozaoqi: '手谈', ningfengzi: '窑变',
  youduitubo: '幽都', taishanzhigui: '岱山', hunpoeryuan: '魂魄', busiyao: '不死', mengpotang: '忘川',
  xuanniaoshengshang: '玄鸟', jiangyuanlvji: '履迹', huaxulfuji: '雷泽',
  panhuxinnv: '盘瓠', linjunyanshen: '白虎',
  banquanzhizhan: '阪泉', zhuluzhizhan: '涿鹿', yidaixiazheng: '代夏',
};
/* 文献题字与四大支柱 */
const STRATA_GLYPH = {
  '《诗经》《尚书》': '颂', '《左传》《国语》': '笔', '《山海经》': '山',
  '《楚辞》天问 · 九歌': '问', '《穆天子传》': '穆', '《吕氏春秋》《韩非子》': '辩',
  '《淮南子》': '补', '《史记》': '史', '《风俗通义》': '俗', '《搜神记》': '搜',
  '《述异记》': '异', '《酉阳杂俎》': '酉', '《太平御览》《太平广记》': '集',
  '《封神演义》': '封', '古史辨与袁珂体系': '辨',
};
const STRATA_MAJOR = new Set(['《山海经》', '《楚辞》天问 · 九歌', '《淮南子》', '《封神演义》']);
const ERA_COLOR = era =>
  /^(西周|春秋|战国)/.test(era) ? '#a77c4f'
    : /^(西汉|东汉)/.test(era) ? '#a98e53'
      : /^(东晋|南朝)/.test(era) ? '#738e9a'
        : /^唐/.test(era) ? '#ad7770'
          : /^宋/.test(era) ? '#778e6a'
            : '#92819d';

export const chineseMythology = {
  id: 'chinese',
  disciplineId: 'mythology',
  name: '中国神话',
  en: 'Chinese Mythology',
  subtitle: '没有《神谱》，也没有荷马——华夏诸神散落在《山海经》的奇兽、《楚辞》的神游与民间的香火里，如星斗散落于夜空。',
  heroImage: '/more/chinese-hero.webp',
  heroQuote: '遂古之初，谁传道之？',
  heroQuoteAuthor: '屈原《天问》',
  watermarkGlyph: '神',
  meta: [
    { label: '文明圈', value: '东亚 · 华夏' },
    { label: '文献跨度', value: '西周 — 明清' },
    { label: '收录神祇', value: '100 位' },
    { label: '母题', value: '62 则' },
    { label: '综述', value: '约五千字' },
  ],

  overview,
  cosmogony: {
    ...cosmogony,
    acts: cosmogony.acts.map(a => ({ ...a, focus: ACT_FOCUS[a.act] || a.act.slice(0, 2) })),
  },

  pantheon: {
    intro: '图谱列出十七位核心神祇与主要关系；全部一百位神祇按类别收于下方名册。点击任一星位或名册词条，展开完整条目。金实线为亲缘，陶色虚线为战争，点线为天命与信物。',
    tiers: [
      { name: '创世层', note: '开天辟地与人类始源' },
      { name: '天帝层', note: '两套并行的帝系' },
      { name: '自然层', note: '日月山川的人格化' },
      { name: '英雄层', note: '灾难面前的抗争者' },
    ],
    nodes: [
      { id: 'pangu', name: '盘古', tier: 0, x: 500, y: 66, domain: '创世 · 开天辟地', caption: '身化万物的牺牲神' },
      { id: 'nuwa', name: '女娲', tier: 0, x: 300, y: 66, domain: '创世 · 造人补天', caption: '抟黄土、炼石，第二次创世者' },
      { id: 'fuxi', name: '伏羲', tier: 0, x: 700, y: 66, domain: '文化 · 画八卦', caption: '与女娲并称，人首蛇身' },
      { id: 'dijun', name: '帝俊', tier: 1, x: 200, y: 226, domain: '天帝 · 山海经体系', caption: '十日与十二月之父' },
      { id: 'zhuanxu', name: '颛顼', tier: 1, x: 390, y: 226, domain: '天帝 · 绝地天通', caption: '断绝天梯的北方之帝' },
      { id: 'huangdi', name: '黄帝', tier: 1, x: 590, y: 226, domain: '天帝 · 中央之帝', caption: '涿鹿败蚩尤，人文初祖' },
      { id: 'yandi', name: '炎帝', tier: 1, x: 790, y: 226, domain: '农神 · 火德', caption: '尝百草；阪泉之后与黄帝合流' },
      { id: 'xihe', name: '羲和', tier: 2, x: 150, y: 386, domain: '日神', caption: '生十日，浴日于甘渊' },
      { id: 'changxi', name: '常羲', tier: 2, x: 320, y: 386, domain: '月神', caption: '生十二月，浴月于方泽' },
      { id: 'xiwangmu', name: '西王母', tier: 2, x: 600, y: 386, domain: '刑杀 · 长生', caption: '豹尾虎齿，掌不死之药' },
      { id: 'bingyi', name: '河伯', tier: 2, x: 790, y: 386, domain: '黄河之神', caption: '乘两龙，遨游九河' },
      { id: 'houyi', name: '后羿', tier: 3, x: 120, y: 546, domain: '英雄 · 射日', caption: '射九日、诛六害' },
      { id: 'dayu', name: '大禹', tier: 3, x: 285, y: 546, domain: '治水 · 定九州', caption: '改堵为疏，三过家门而不入' },
      { id: 'chiyou', name: '蚩尤', tier: 3, x: 450, y: 546, domain: '战神 · 兵主', caption: '铜头铁额，涿鹿的失败者' },
      { id: 'kuafu', name: '夸父', tier: 3, x: 615, y: 546, domain: '逐日者', caption: '道渴而死，弃杖化邓林' },
      { id: 'jingwei', name: '精卫', tier: 3, x: 770, y: 546, domain: '填海之鸟', caption: '炎帝少女，衔石填海' },
      { id: 'xingtian', name: '刑天', tier: 3, x: 925, y: 546, domain: '断首战神', caption: '以乳为目，操干戚以舞' },
    ],
    edges: [
      { from: 'nuwa', to: 'fuxi', label: '兄妹 · 夫妇', type: 'kin' },
      { from: 'huangdi', to: 'yandi', label: '阪泉之战', type: 'war' },
      { from: 'huangdi', to: 'chiyou', label: '涿鹿之战', type: 'war' },
      { from: 'huangdi', to: 'xingtian', label: '争帝', type: 'war' },
      { from: 'dijun', to: 'xihe', label: '帝妻 · 生十日', type: 'kin' },
      { from: 'dijun', to: 'changxi', label: '帝妻 · 生十二月', type: 'kin' },
      { from: 'dijun', to: 'houyi', label: '赐彤弓 · 命射日', type: 'mandate' },
      { from: 'yandi', to: 'jingwei', label: '父女', type: 'kin' },
      { from: 'yandi', to: 'chiyou', label: '部众 · 后裔', type: 'kin' },
      { from: 'houyi', to: 'xiwangmu', label: '请不死之药', type: 'mandate' },
      { from: 'houyi', to: 'bingyi', label: '射眇左目', type: 'war' },
      { from: 'huangdi', to: 'zhuanxu', label: '祖孙', type: 'kin' },
    ],
    note: '本图为示意性重构——不同文献的帝系互相冲突（帝俊与黄帝两套体系在《山海经》内部并存），这正是中国神话碎片化的证据。绘制版神谱图可后续替换。',
  },

  deityCategories: [
    { id: 'creation', name: '创世与始源', note: '开天、造人与宇宙的原初力量' },
    { id: 'sovereign', name: '天帝与帝系', note: '帝俊与黄帝两套并行体系，及五帝圣王' },
    { id: 'celestial', name: '日月星辰风雨', note: '天体的家宅化：生、浴、驾、御' },
    { id: 'terrain', name: '山川海渎', note: '昆仑门卫、河洛神女与幽冥前身的土地' },
    { id: 'direction', name: '五方五行', note: '四季的颜色：青、赤、白、黑、黄' },
    { id: 'culture', name: '文化英雄与始祖', note: '文明的每一步都记在一位"氏"的名下' },
    { id: 'hero', name: '英雄与抗争者', note: '灾难面前的行动者与殉道者' },
    { id: 'calamity', name: '凶神与灾异', note: '四凶与六害：被英雄清剿的清单' },
    { id: 'beast', name: '灵兽与异兽', note: '瑞与兆：动物作为预兆与行政' },
    { id: 'netherworld', name: '幽冥与死后', note: '从泰山府君到孟婆汤的死后世界' },
    { id: 'literary', name: '小说造神与后期演化', note: '层累的最后一层：印刷术造的神' },
  ],
  deities: [...DEITIES_CORE, ...DEITIES_EXPANDED].map(x => ({ ...x, icon: x.icon || DEITY_ICONS[x.id] || null })),

  motifs: {
    intro: '六十二则母题，按十类组织。每一则都是"故事 → 母题 → 哲学勾连"的三段式：一个神话故事之所以值得讲第二遍，是因为它回答了一个哲学问题。',
    categories: [
      { id: 'creation', name: '创世与秩序' },
      { id: 'calamity', name: '灾异与救世' },
      { id: 'hero', name: '英雄与抗争' },
      { id: 'love', name: '爱情与婚姻' },
      { id: 'transformation', name: '变形' },
      { id: 'geography', name: '地理与仙境' },
      { id: 'artifact', name: '器物与发明' },
      { id: 'nether', name: '幽冥与生死' },
      { id: 'origin', name: '感生与族源' },
      { id: 'war', name: '战争与权秩' },
    ],
    items: [...MOTIFS_A, ...MOTIFS_B].map(m => ({ ...m, focus: MOTIF_FOCUS[m.id] || m.name.slice(0, 2) })),
  },

  strata: {
    ...strata,
    items: strata.items.map(s => ({ ...s, glyph: STRATA_GLYPH[s.source] || s.source[1], major: STRATA_MAJOR.has(s.source), color: ERA_COLOR(s.era) })),
  },
  bridges,
  keywords,
  keywordGlosses,
  keywordTargets: {
    昆仑: { sec: 'sec-motifs', motif: 'kunlunxuanpu' }, 蓬莱: { sec: 'sec-motifs', motif: 'penglai' },
    归墟: { sec: 'sec-motifs', motif: 'guixu' }, 建木: { sec: 'sec-motifs', motif: 'jianmu' },
    扶桑: { sec: 'sec-motifs', motif: 'fusang' }, 不周山: { sec: 'sec-motifs', motif: 'buzhoushan' },
    瑶池: { sec: 'sec-motifs', motif: 'yaochi' }, 青丘: { sec: 'sec-motifs', motif: 'qingqiu' },
    弱水: { sec: 'sec-motifs', motif: 'ruoshui' }, 绝地天通: { sec: 'sec-motifs', motif: 'jueditiantong' },
    三皇五帝: { sec: 'sec-pantheon' }, 四凶: { sec: 'sec-pantheon' },
    感生: { sec: 'sec-motifs', motif: 'xuanniaoshengshang' }, 层累: { sec: 'sec-strata' },
    神话历史化: { sec: 'sec-overview' }, 巫史传统: { sec: 'sec-bridges' },
    萨满: { sec: 'sec-overview' }, 傩: { sec: 'sec-overview' },
    玄鸟: { sec: 'sec-motifs', motif: 'xuanniaoshengshang' }, 息壤: { sec: 'sec-motifs', motif: 'gunxixirang' },
    洪水: { sec: 'sec-motifs', motif: 'hongshui' }, 不死药: { sec: 'sec-motifs', motif: 'busiyao' },
    金乌: { sec: 'sec-motifs', motif: 'shejiuri' }, 蟾宫: { sec: 'sec-motifs', motif: 'changehuachan' },
    天问: { sec: 'sec-strata' }, 九歌: { sec: 'sec-strata' }, 志怪: { sec: 'sec-strata' },
    仙话: { sec: 'sec-pantheon' }, 妖怪: { sec: 'sec-pantheon' }, 封神: { sec: 'sec-strata' },
    洪荒流: { sec: 'sec-overview' }, 图腾: { sec: 'sec-pantheon' },
    灾异: { sec: 'sec-pantheon' }, 祥瑞: { sec: 'sec-pantheon' }, 门神: { sec: 'sec-pantheon' },
    创世: { sec: 'sec-cosmogony' }, 变形: { sec: 'sec-motifs' },
    治水: { sec: 'sec-motifs', motif: 'yudaojiushui' },
  },
  crossLinks,
  epilogue,
};

