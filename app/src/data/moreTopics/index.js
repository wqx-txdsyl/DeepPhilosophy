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

export const ALL_DETAILS = {
  'religion/buddhism': buddhism,
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
