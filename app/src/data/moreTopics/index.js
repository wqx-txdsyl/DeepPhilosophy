/**
 * "更多"详情注册表 —— 三级详情页的数据汇总
 * key: `${disciplineId}/${topicId}`，value: 数据模块
 * 数据模块须实现 MythologyDetail 所需的全部字段（schema 见 chineseMythology/index.js）
 */
import { chineseMythology } from './chineseMythology';
import { honghuang } from './honghuang';
import { japanese } from './japanese';
import { greek } from './greek';
import { biblical } from './biblical';
import { egyptian } from './egyptian';
import { indian } from './indian';
import { norse } from './norse';
import { mesopotamian } from './mesopotamian';
import { celtic } from './celtic';
import { roman } from './roman';
import { cthulhu } from './cthulhu';

const christianityHub = {
  id: 'christianity', disciplineId: 'religion', name: '基督教', en: 'Christianity',
  subtitle: '三位一体与道成肉身——尼西亚信经以降的信仰体系，经院哲学的母体。人类最大宗教，从耶路撒冷到全球两千年的传播史。',
  heroImage: '/more/christianity-hero.webp',
  heroQuote: '太初有道，道与神同在，道就是神。',
  heroQuoteSource: '《约翰福音》1:1',
  overviewLead: [
    '基督教不是一套道德教诲，而是一个关于"神成为人"的宣告：拿撒勒人耶稣是道成肉身的上帝，他的死与复活为人类打开了与神和解的门。这个"福音"（好消息）从耶路撒冷的一间小楼出发，三百年后征服了罗马帝国，两千年后成为人类信徒最多的宗教——约24亿人，地球上每三个人中就有一个。',
    '基督教的内核是一组必须"信"才能"是"的宣告——三位一体、道成肉身、死而复活。它继承了希伯来圣经（旧约）与希腊哲学（逻各斯概念）两份遗产，又在耶稣身上宣布"成全"而非"废除"它们。保罗的神学（因信称义）、约翰的神秘主义（道成肉身）、彼得的教团（教会）构成了最初的三个支点。',
    '1054年东西教会大分裂与1517年宗教改革，把基督教分成三大支：东正教守圣像与静默的传统，天主教守彼得的圣统制，新教则把"唯独圣经"变成了一场没有终点的解释学运动。三大支共享同一部圣经、同一次洗礼、同一个复活节的盼望，却在"权威在哪里""如何得救""教会是什么"上给出了截然不同的答案。',
  ],
  keywords: ['三位一体', '道成肉身', '复活', '救赎', '恩典', '因信称义', '原罪', '末世审判', '教会', '圣礼', '福音', '使徒', '旧约', '新约', '十诫', '登山宝训', '弥赛亚', '圣母', '十字架', '洗礼', '圣餐', '尼西亚信经', '使徒信经', '大公会议', '宗教改革', '上帝之城', '自由意志', '预定的恩宠', '大使命', '终末论', '圣像', '隐修传统', '大分裂', '唯独圣经', '普世教会', '爱的诫命'],
  keywordGlosses: {
    '三位一体': '圣父、圣子、圣灵三个位格共享同一本质：一个上帝而非三个神，三个位格而非一个神的三种显现——325年尼西亚与381年君士坦丁堡会议定型的核心教义。',
    '道成肉身': '逻各斯（圣言）成为肉身住在我们中间：《约翰福音》1:14——无限的上帝取了有限的人性（451年迦克墩会议定"神人二性"）。',
    '复活': '耶稣死后第三天复活：基督教信仰的基石——（保罗语：若基督没有复活，我们所传的便是枉然），复活节因此是基督教最古老的节日。',
    '救赎': '上帝通过基督的死与复活把人类从罪与死中救出：代赎-得胜-满足等多种神学模型（Anselm《神为何成人》的经典表述）。',
    '因信称义': '人得救靠信心而非善功：保罗《罗马书》的「义人必因信得生」——路德宗教改革的神学引擎（sola fide）。',
    '原罪': '亚当堕落遗传给全人类的罪性：奥古斯丁-加尔文的严厉版本与东方「祖先罪」的温和版本——「我是在罪孽里生的」（诗篇51）。',
    '恩典': '上帝无条件的白白恩赐：不因人的功德而给——「你们得救是本乎恩，也因着信」（弗2:8），恩典与功德的张力贯穿教会史。',
    '教会': 'ekklesia（蒙召者的聚会）：基督的身体与圣灵的殿——太18:20：哪里有两三个人奉我的名聚会，教会的四标记：唯一、神圣、大公、使徒。',
    '圣礼': '恩典的可感知通道：天主教七件圣事、新教两大圣礼（洗礼-圣餐）——「可见的恩典形式」（奥古斯丁定义）。',
    '洗礼': '入教的门径：水的洗象征与基督同死同活——婴儿洗与成人洗的分野是宗教改革的战场之一。',
    '圣餐': '纪念最后晚餐的礼仪：饼与酒——这是我的身体：变质说（天主教）-合质说（路德）-纪念说（慈运理）的三种解释。',
    '尼西亚信经': '325年尼西亚会议定的信仰告白：圣子与圣父本质相同（homoousios）——反阿里乌主义（子受造论）的胜利（普世教会通用信经）。',
    '大公会议': '普世教会的最高权威 gatherings：尼西亚（325）至梵二（1962-65）共二十一次——圣经加传统的天主教权威结构。',
    '使徒统绪': '主教按手传承追溯至使徒：教职合法性的链条——天主教-东正教坚持，新教多数放弃（人人皆祭司）。',
    '大分裂': '1054年东西教会互相绝罚：罗马（拉丁）与君士坦丁堡（希腊）的千年分裂——和子句（Filioque）-教宗权威-圣像的积累性破裂。',
    '宗教改革': '1517年路德《九十五条论纲》：唯独圣经、唯独恩典、唯独信心、唯独基督、荣耀归神——五个唯独的口号（现代性的宗教引擎之一）。',
    '上帝之城': '奥古斯丁《上帝之城》：两种爱的两种城——历史是上帝之城与地上之城的斗争（西方历史哲学的源头）。',
    '末世审判': '基督再临时的最后审判：义人永生-恶人永罚——「创造天地的主」信经的末段（千禧年主义诸派的分歧点）。',
    '弥赛亚': '受膏者（基督的希伯来语）：犹太期待的君王救主——基督教宣告拿撒勒人耶稣就是弥赛亚（「基督」即希腊语的弥赛亚）。',
    '登山宝训': '《马太福音》5-7章：「八福」与主祷文——「爱仇敌」与「不要为明天忧虑」：基督教伦理的最高峰文本。',
    '十字架': '罗马酷刑具成为基督教的中心符号：林前1:18：十字架的愚拙——耻辱的刑具逆转为得胜的标志（Crux probat omnia）。',
    '圣母马利亚': '耶稣之母：天主教-东正教的高度尊崇（圣母无染原罪-圣母升天教义）与新教的节制（马利亚主义之辩）。',
    '使徒信经': '传为使徒所立的信仰纲要：我信上帝，全能的父——西方教会的洗礼信条（三大信经之一）。',
    '旧约': '希伯来圣经（塔纳赫）：律法-先知-圣文三部分——基督教以「旧」约之名称之（与新约的连续-断裂之争）。',
    '新约': '27卷书：四福音书-使徒行传-书信-启示录——1世纪成书的希腊文文献（基督教的立约文件）。',
    '十诫': '出埃及记20章的十条诫命：从除我以外不可有别神到不可贪恋——犹太-基督教伦理的基石（两块法板的划分诸说）。',
    '大使命': '马太福音28:19-20：去使万民作我的门徒——传教运动的圣经依据（直到世界的末了）。',
    '隐修传统': '沙漠教父-本笃会-熙笃会-加尔默罗会：离开世界以侍奉世界的修道运动——祈祷与劳作（Ora et Labora），中世纪文化的保存者。',
    '圣像': '东正教的图像神学：圣像是可见的不可见者——726-843年的圣像破坏之争（道成肉身使图像成为可能，大马士革的约翰）。',
    '唯独圣经': 'Sola Scriptura：圣经是信仰与生活的最高权威——宗教改革第一原则（传统-教会训导权被降为见证）。',
    '自由意志': '奥古斯丁-伯拉纠之争：得救是否需要人的自由配合——「恩典独作」（monergism）对「协作」（synergism）的千年之争（多特会议1618-19）。',
  },
  branches: [
    { id: 'orthodox', name: '东正教', en: 'Eastern Orthodox', hero: '/more/orthodox-hero.webp',
      desc: '圣像与静默——拜占庭传统的守护者。七次大公会议的正统继承，theosis（神化）作为救赎的终极目标。' },
    { id: 'catholic', name: '天主教', en: 'Roman Catholic', hero: '/more/catholic-hero.webp',
      desc: '彼得之座与圣统制——全球最大的基督教教派，七件圣事与经院哲学的母体。' },
    { id: 'protestant', name: '新教', en: 'Protestantism', hero: '/more/protestant-hero.webp',
      desc: '唯独圣经与因信称义——1517年路德的革命与千万个教派的诞生，现代性的宗教引擎。' },
  ],
  epilogue: '从耶路撒冷的一间小楼到地球上的每一个时区，基督教的故事是「道成肉身」的无尽重演：无限的上帝一次次进入有限的人类语言、文化、艺术与政治。三大分支守着同一本圣经而彼此不同，正如同一株葡萄树的三个枝子朝着不同的阳光生长——尼西亚信经的第一句「我信唯一的天主」仍是它们共同的第一句。',
};

export const ALL_DETAILS = {
  'religion/buddhism': buddhism,
  'religion/christianity': christianityHub,
  'religion/orthodox': orthodox,
  'religion/catholic': catholic,
  'religion/protestant': protestant,
  'religion/islam': islam,
  'religion/hinduism': hinduism,
  'religion/taoism': taoism,
  'mythology/chinese': chineseMythology,
  'mythology/honghuang': honghuang,
  'mythology/japanese': japanese,
  'mythology/greek': greek,
  'mythology/biblical': biblical,
  'mythology/egyptian': egyptian,
  'mythology/indian': indian,
  'mythology/norse': norse,
  'mythology/mesopotamian': mesopotamian,
  'mythology/celtic': celtic,
  'mythology/roman': roman,
  'mythology/cthulhu': cthulhu,
};

import { buddhism } from './religion/buddhism';

import { orthodox } from './religion/orthodox';
import { catholic } from './religion/catholic';
import { protestant } from './religion/protestant';
import { islam } from './religion/islam';
import { hinduism } from './religion/hinduism';
import { taoism } from './religion/taoism';




