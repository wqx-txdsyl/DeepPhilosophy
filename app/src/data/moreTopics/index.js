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
  branches: [
    { id: 'orthodox', name: '东正教', en: 'Eastern Orthodox', hero: '/more/orthodox-hero.webp',
      desc: '圣像与静默——拜占庭传统的守护者。七次大公会议的正统继承，theosis（神化）作为救赎的终极目标。' },
    { id: 'catholic', name: '天主教', en: 'Roman Catholic', hero: '/more/catholic-hero.webp',
      desc: '彼得之座与圣统制——全球最大的基督教教派，七件圣事与经院哲学的母体。' },
    { id: 'protestant', name: '新教', en: 'Protestantism', hero: '/more/protestant-hero.webp',
      desc: '唯独圣经与因信称义——1517年路德的革命与千万个教派的诞生，现代性的宗教引擎。' },
  ],
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




