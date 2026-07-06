/**
 * 流派详情页 — 滚轮下翻式，数据按需从 JSON 加载
 * 所有流派数据存储在 /public/schools/data/school_*.json
 */
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import { useSEO } from '../utils/seo';
import HeroSection from '../components/school/HeroSection';
import OverviewSection from '../components/school/OverviewSection';
import ConstellationMap from '../components/school/ConstellationMap';
import TimelineSection from '../components/school/TimelineSection';
import GlossaryCloud from '../components/school/GlossaryCloud';
import QuotesGallery from '../components/school/QuotesGallery';
import WorksList from '../components/school/WorksList';
import EpilogueSection from '../components/school/EpilogueSection';

// ─── 子流派颜色映射（静态资源，体积小，保留内联） ───
const SUB_COLORS = {
  '米利都学派':'#C4956A','前苏格拉底':'#B8875E','埃利亚学派':'#AC7A52','多元论':'#A06D46',
  '古希腊哲学':'#94603A','柏拉图学派':'#88532E','犬儒学派':'#7C4622','逍遥学派':'#703916',
  '怀疑论':'#642C0A','伊壁鸠鲁学派':'#6B3820','斯多葛学派':'#3A5A7C','新柏拉图主义':'#2E4A6A',
  '希腊教父':'#8B4513','卡帕多西亚教父':'#6A2E4A','拉丁教父':'#3A5A7C',
  '早期经院哲学':'#8B6914','盛期经院哲学':'#C4956A','晚期经院哲学':'#5A4A7C','阿拉伯-犹太传入':'#3A6A5C',
  '法国笛卡尔学派':'#4A3A5C','荷兰斯宾诺莎主义':'#5C3A3A','德国莱布尼茨-沃尔夫体系':'#3A4A6C','笛卡尔主义的扩展与批判':'#5C5A3A',
  '英国经验论奠基':'#4A5C6C','唯心论转向':'#6A4A3C','苏格兰启蒙与怀疑论':'#2A5C4A','法国经验论':'#5C3A5A','晚期发展':'#3A5C5C',
  '法国启蒙运动':'#8B4513','德国启蒙运动':'#3A5A7C','苏格兰启蒙运动':'#2A6A4A','苏格兰常识学派':'#5A4A3C','法国唯物论':'#6A3A3A',
  '20世纪实在论':'#3A5A6C','主观唯心主义':'#6A4A5C','先验唯心主义':'#3A5A6C','德国唯心主义':'#4A3A6A','绝对唯心主义':'#5A2A4C','意志唯心主义':'#3A3A5A',
  '古典自由主义':'#3A6A7C','后革命自由主义':'#5A4A3C','德国自由主义':'#4A5A3C',
  '浪漫主义先驱':'#5C3A3A','表现主义与历史主义':'#4A5C3A','古典-浪漫的张力':'#6A5A2A','耶拿浪漫派':'#3A4A6C',
  '自由女性主义':'#5A3A6C','存在主义女性主义':'#4A3A5C','激进女性主义':'#6C3A3A','交叉性女性主义':'#3A5C4A','后现代女性主义':'#3A4A6C','法国女性主义':'#5C4A3A','关怀伦理学':'#3A6A5C',
  '个体心理学':'#4A6A5C','互文性':'#5A4A6C','从结构到后结构':'#6A5A4A','伦理现象学':'#4A5A6C','信仰哲学':'#5C4A5A','先验现象学':'#3A6A5C','分析心理学':'#6A3A5A',
  '列宁主义':'#5A6A3A','前驱':'#3A5A6C','反启蒙':'#6C5A3A','发生学结构主义':'#4A3A6C','叙事学':'#5A3A4C','后拉康精神分析':'#3A4A6C','后现代状况':'#6A4A4A',
  '启蒙与德国哲学':'#4A5C3A','哲学人类学':'#5C3A5C','哲学诠释学':'#3A5C6A','基督教存在主义':'#5A3A3A','女性主义后结构':'#4A6A4A',
  '存在主义之父':'#6A4A6A','存在主义先驱':'#3A6A6A','存在主义现象学':'#5A5A3A','存在主义神学':'#4A4A6C','存在主义精神分析':'#6A6A3A','存在主义荒诞':'#3A5A5A',
  '存在哲学':'#5C4A4A','存在的悲剧感':'#4A6A3A','宗教存在主义':'#6A3A4A','宗教荒诞':'#3A4A5A','实用主义/生命哲学':'#5A6A5A',
  '客体关系学派':'#4A3A5A','差异哲学':'#6A5A5C','常识哲学':'#2A5A4A','康德主义传播':'#5A2A5A','弗洛伊德-马克思主义':'#4A5A2A','意志哲学':'#2A4A5A',
  '批判哲学':'#5A4A2A','拟像理论':'#4A2A5A','政治现象学':'#2A5A5A','文化形态学':'#5A5A2A','文化精神分析':'#3A3A6A','文学先驱':'#6A3A3A',
  '日常语言哲学':'#3A6A3A','权力谱系学':'#2A4A6A','法兰克福学派':'#6A2A4A','法国存在主义':'#4A2A6A','现象学伦理学':'#6A4A2A','现象学存在主义':'#5C6A3A',
  '现象学美学':'#6A3A6C','生命哲学先驱':'#3A6C5A','生命哲学社会学':'#5A3C6A','生命现象学':'#6C5A3C','生命理性主义':'#3C6A5A','直觉与绵延':'#4C5A6C',
  '符号学/文化批评':'#6C4A5A','第一代':'#4A6A5C','第三代':'#5A4A6C','第二代':'#6A5A4A','精神分析后结构':'#4A5A6C','精神分裂分析':'#5C4A5A',
  '精神科学':'#3A6A5C','经典精神分析':'#6A3A5A','经典马克思主义':'#5A6A3A','结构主义精神分析':'#3A5A6C','结构主义诗学':'#6C5A3A','结构人类学':'#4A3A6C',
  '结构语义学':'#5A3A4C','结构语言学':'#3A4A6C','结构马克思主义':'#6A4A4A','自我心理学':'#4A5C3A','自然主义':'#5C3A5C','荒诞哲学':'#3A5C6A',
  '荒诞戏剧':'#5A3A3A','荒诞文学':'#4A6A4A','西方马克思主义':'#6A4A6A','解构主义':'#3A6A6A','诗人哲学家':'#5A5A3A','诠释学现象学':'#4A4A6C',
  '语言游戏':'#6A6A3A','身体现象学':'#3A5A5A','过程哲学':'#5C4A4A','逻辑分析':'#4A6A3A','逻辑原子主义':'#6A3A4A','逻辑图像论':'#3A4A5A',
  '逻辑实证主义':'#5A6A5A','青年黑格尔派':'#4A3A5A','革命马克思主义':'#6A5A5C','马克思主义左翼':'#2A5A4A',
  '义务论':'#4E6E6E','人本实用主义':'#5E6E7E','偏好功利主义':'#4E8E5A','先导':'#7E4E6E','公民共和主义':'#5E6E5A','共和主义':'#7E5E5E',
  '内在实在论':'#5A6E6E','制度人类学':'#6E7E4E','功利主义':'#6E6E6E','历史主义':'#4E6E5E','叙事诠释学':'#6A5E5E','古代怀疑论':'#5E5A6E',
  '古典功利主义':'#6B8E5A','后殖民批判':'#4E5A6E','后现代知识论':'#6A5A6E','唯名论':'#5E5E5A','商议民主':'#5E7E5E','复合平等':'#6E6E5A',
  '媒介理论':'#6E5E6A','实用主义宗教哲学':'#6A5A5A','实证主义社会学':'#5E4A7E','对话人类学':'#5E4E7E','工具主义':'#7E5A6E','希望哲学':'#4E4E7E',
  '弗洛伊德马克思主义':'#7E4E7E','形式社会学':'#7E5E4A','德性传统':'#6E5A6E','德性伦理学':'#6E6E4E','批判传统':'#8B4513','批判理性主义':'#6E5E4E',
  '批判社会学':'#5E7E4A','技术史':'#5A4E6E','技术批判理论':'#4E6E5A','技术现象学':'#4A5E6E','技术自主论':'#6E4A5E','政治功利主义':'#7E6B5A',
  '政治社会学':'#7E4A5E','教父哲学':'#5A5A7E','文化人类学':'#4E5E6E','文化批判':'#7E7E4E','文艺复兴怀疑论':'#6E6E5A','新实用主义':'#6E7E5A',
  '方法论无政府主义':'#5E4E6E','方法论的怀疑':'#6E5A5E','早期斯多葛':'#4E6E5A','普遍诠释学':'#5E5E6A','本体论诠释学':'#5E6A5E',
  '本真性伦理':'#5A6E6E','极端唯名论':'#5A5E5E','概念论':'#5E5A5E','此性论':'#5A5E5A','法国实证主义':'#5A6E7E','现象学人类学':'#4E6E7E',
  '理解社会学':'#4A7E5E','生命哲学':'#6E4E7E','研究纲领':'#4E5E5E','社会学实证主义':'#7E6E4A','社会实用主义':'#7E6E5A','社群主义':'#5A4E7E',
  '符号人类学':'#7E4E5E','符号社会':'#5A6A6E','经院哲学':'#7E5A5A','经验批判主义':'#4E5E8E','经验论怀疑论':'#5A6E5A','罗马斯多葛':'#6E5A4E',
  '自由主义':'#4E7E7E','自由至上主义':'#7E4E5A','观念功利主义':'#5A7E6B','规则功利主义':'#5A7E4E','规定主义':'#6E8E4A','证明传统':'#5A5A5A',
  '超验主义':'#4A6E8E','过程生态学':'#5E7E4E','过程社会学':'#4A5E7E','过程神学':'#4E7E6E','进化实证主义':'#6E4A5E','逻辑实用主义':'#6E5A7E',
  '逻辑经验主义':'#5E5E4E','道德情感论':'#6E4E6E','霸权理论':'#4E7E4E','黑格尔马克思主义':'#7E4E4E',
  '三民主义创始人':'#6E4A3A','三民主义右翼':'#A04A6E','三民主义实践':'#4AB88A','三民主义理论家':'#5E3C8B','中国化开创者':'#3A65B0','中国哲学与马克思主义':'#4A8AD4',
  '习行派':'#3A7AC4','今文经学':'#4AB88A','体系化先驱':'#4A6EA0','元康玄学':'#6E4A8B','先秦道家':'#5A4A7E','党建理论':'#653AB0','关学':'#4A8B6E',
  '兵家':'#8A4AD4','兵家始祖':'#3A9B7A','净土宗':'#3A7AC4','创立者':'#3A7AC4','前期墨家':'#4A6EA0','前期法家':'#4A6EA0','华严宗':'#4A8B6E',
  '古史辨':'#6E4A3A','古文经学':'#D4884A','史学与新儒家':'#6E3A5A','合同异派':'#B03A65','名家':'#6E4A8B','名家先驱':'#C43A8B','吴派':'#7E4A6E',
  '哲学派':'#3A7AC4','哲学观念改革':'#3A5A6E','唯物主义':'#4A8B6E','墨家创始人':'#4A6EA0','墨辩':'#3C5E6B','大众哲学':'#7A3AC4','天台宗':'#B0653A',
  '实验主义':'#8B3C5E','律宗':'#4A8AD4','心学':'#3A8B65','思想史':'#3A7AC4','批判派':'#3A9B7A','文化哲学':'#4A6E5A','新唯识论':'#653AB0',
  '新理学':'#3A7AC4','智慧说':'#6E4A3A','正始玄学':'#4A8AD4','毛泽东思想创立者':'#4AB88A','民生主义理论家':'#3A9B7A','法家先驱':'#D4884A',
  '法家集大成':'#6E3A5A','法相唯识宗':'#4A5A6E','洛学':'#4A5A6E','理学先驱':'#4A8B6E','皖派':'#6E4A8B','禅宗':'#3C5E6B','禅宗北宗':'#8B5E3C',
  '离坚白派':'#653AB0','科学方法论':'#3A6E6E','科学派':'#8B5E3C','科学社':'#6E3A5A','秦代法家':'#A04A6E','秦墨':'#7A3AC4','竹林玄学':'#C47A3A',
  '经世派':'#4A6E5A','经济思想':'#4AB88A','统一战线':'#4A5A6E','继承与发展':'#3A6E6E','维新启蒙':'#5A4A7E','维新实践':'#3C5E6B',
  '维新激进派':'#3A65B0','维新理论家':'#5A4A7E','维新领袖':'#4A5A6E','综合创新':'#B03A65','综合经学':'#3A9B7A','进化论传播者':'#3A5A6E',
  '进化论信仰者':'#3A65B0','进化论应用者':'#3A8B65','进化论翻译者':'#7A3AC4','道家创始人':'#C47A3A','道德的形而上学':'#A0624A','闽学':'#3A8B65',
  '阴阳家':'#3A5A6E','阴阳家创始人':'#7E5A4A','马克思主义哲学传播者':'#653AB0','马克思主义哲学史':'#C47A3A','魏晋玄学':'#C47A3A',
  '黄老道家':'#3C5E6B','19世纪独立与认同哲学':'#A0624A','20世纪初文化民族主义':'#4AB88A','20世纪美洲哲学史':'#6E4A3A',
  '20世纪解放哲学':'#3A7AC4','亚历山大里亚学派':'#A04A6E','京都学派':'#4A8B6E','伊斯兰哲学/法尔萨法':'#C47A3A',
  '伊斯法罕学派/存在论':'#A0624A','伦理哲学':'#4A8B6E','佛教中观派':'#4A5A6E','佛教唯识派':'#C43A8B','光照哲学/神秘主义':'#4A6E5A',
  '凯拉姆与苏非主义':'#653AB0','前伊斯兰时期/琐罗亚斯德教':'#3C5E6B','印尼女性主义哲学':'#D44A9B','印尼本土哲学':'#D44A9B',
  '历史哲学':'#5E3C8B','吠檀多派不二论':'#8B3C5E','存在主义/对话哲学':'#7E4A6E','巴比伦学派':'#8B5E3C','批判教育学与解放实践':'#4A8AD4',
  '政治哲学/泛非主义':'#3C6B5E','数论派':'#A0624A','曹洞宗':'#4A8B6E','概念去殖民化':'#3A6E6E','殖民时期辩护神学':'#3A5A6E',
  '法尔萨法中期':'#6E3A5A','法尔萨法后期':'#6E4A3A','法尔萨法早期':'#4A6E5A','法尔萨法鼎盛':'#4A5A6E','泰国佛教社会主义':'#3C6B5E',
  '潘查希拉思想':'#4A6EA0','犹太亚里士多德主义':'#3A65B0','犹太启蒙运动':'#5A7E4A','现象学/伦理哲学':'#4A6E5A',
  '理性主义/医学哲学':'#B03A65','理性主义/泛神论':'#4AB88A','瑜伽派':'#3C5E6B','真言宗':'#D44A9B','耆那教':'#4A8B6E','苏非主义':'#6E4A3A',
  '菲律宾启蒙哲学':'#4A8B6E','认同哲学/批判哲学':'#5E3C8B','越南儒家政治哲学':'#7E4A6E','适足经济哲学':'#8B5E3C','部族文化哲学':'#B03A65',
  '黑人性运动':'#653AB0','两汉经学':'#3A5A9B','儒家创始人':'#7E4A6E','先秦儒家':'#C43A8B','思孟学派':'#3A5A9B','现代新儒家':'#5A4A7E',
  '程朱理学':'#A04A6E','陆王心学':'#3A7B5A',
};

// ─── 英文名映射 ───
const ENG_NAMES = {
  '三民主义':'THREE PRINCIPLES','东南亚哲学':'SOUTHEAST ASIAN PHILOSOPHY','两汉经学':'HAN DYNASTY CLASSICS',
  '中国实证哲学':'CHINESE POSITIVISM','中国马克思主义哲学':'CHINESE MARXIST PHILOSOPHY',
  '习近平新时代中国特色社会主义思想':'XI JINPING THOUGHT','乾嘉朴学':'QIAN-JIA EVIDENTIAL SCHOLARSHIP',
  '伊斯兰哲学':'ISLAMIC-ARABIC PHILOSOPHY','伦理学':'ETHICS','儒家':'CONFUCIANISM','兵家':'MILITARY PHILOSOPHY',
  '分析哲学':'ANALYTIC PHILOSOPHY','功利主义':'UTILITARIANISM','印度哲学':'INDIAN PHILOSOPHY',
  '古希腊哲学':'ANCIENT GREEK PHILOSOPHY','名家':'SCHOOL OF NAMES','后现代主义':'POSTMODERNISM',
  '后结构主义':'POST-STRUCTURALISM','启蒙运动':'ENLIGHTENMENT','哲学人类学':'PHILOSOPHICAL ANTHROPOLOGY',
  '哲学诠释学':'HERMENEUTICS','唯名论':'NOMINALISM','唯心主义':'IDEALISM','基督教哲学':'CHRISTIAN PHILOSOPHY',
  '墨家':'MOHISM','天演论':'TIANYANLUN (EVOLUTIONISM)','女性主义':'FEMINISM','存在主义':'EXISTENTIALISM',
  '宋明理学':'NEO-CONFUCIANISM','宗教哲学':'PHILOSOPHY OF RELIGION','实在论':'REALISM','实用主义':'PRAGMATISM',
  '实证主义':'POSITIVISM','德国古典哲学':'GERMAN IDEALISM','批判理论':'CRITICAL THEORY',
  '技术哲学':'PHILOSOPHY OF TECHNOLOGY','拉丁美洲哲学':'LATIN AMERICAN PHILOSOPHY','政治哲学':'POLITICAL PHILOSOPHY',
  '教父哲学':'PATRISTIC PHILOSOPHY','日本哲学':'JAPANESE PHILOSOPHY','明清实学':'MING-QING PRAGMATISM',
  '毛泽东思想':'MAO ZEDONG THOUGHT','法兰克福学派':'FRANKFURT SCHOOL','法家':'LEGALISM',
  '波斯哲学':'PERSIAN PHILOSOPHY','浪漫主义':'ROMANTICISM','犹太哲学':'JEWISH PHILOSOPHY',
  '现代新儒家':'NEW CONFUCIANISM','现象学':'PHENOMENOLOGY','理性主义':'RATIONALISM',
  '生命哲学':'PHILOSOPHY OF LIFE','社会学':'SOCIOLOGY','社群主义':'COMMUNITARIANISM',
  '科学哲学':'PHILOSOPHY OF SCIENCE','精神分析学':'PSYCHOANALYSIS','经院哲学':'SCHOLASTICISM',
  '经验主义':'EMPIRICISM','结构主义':'STRUCTURALISM','维新派':'REFORMIST PHILOSOPHY','自由主义':'LIBERALISM',
  '荒诞哲学':'ABSURDISM','西方马克思主义':'WESTERN MARXISM','超验主义':'TRANSCENDENTALISM',
  '过程哲学':'PROCESS PHILOSOPHY','道家':'TAOISM','阴阳家':'YIN-YANG SCHOOL','隋唐佛学':'SUI-TANG BUDDHISM',
  '非洲哲学':'AFRICAN PHILOSOPHY','马克思主义':'MARXISM','马克思主义哲学的中国化与体系化':'SINICIZATION OF MARXIST PHILOSOPHY',
  '魏晋玄学':'WEI-JIN METAPHYSICS','韩国哲学':'KOREAN PHILOSOPHY','西藏哲学':'TIBETAN PHILOSOPHY',
  '北欧哲学':'NORDIC PHILOSOPHY','玛雅哲学':'MAYAN PHILOSOPHY','阿兹特克哲学':'AZTEC PHILOSOPHY',
  '澳洲原住民哲学':'AUSTRALIAN ABORIGINAL PHILOSOPHY','蒙古中亚哲学':'MONGOLIAN & CENTRAL ASIAN PHILOSOPHY',
  '东欧斯拉夫哲学':'EASTERN EUROPEAN & SLAVIC PHILOSOPHY','北美哲学':'NORTH AMERICAN PHILOSOPHY',
  '美索不达米亚哲学':'MESOPOTAMIAN PHILOSOPHY','印加哲学':'INCA PHILOSOPHY',
  '古埃及哲学':'ANCIENT EGYPTIAN PHILOSOPHY','古希伯来哲学':'ANCIENT HEBREW PHILOSOPHY',
  '凯尔特哲学':'CELTIC PHILOSOPHY','罗马哲学':'ROMAN PHILOSOPHY','拜占庭哲学':'BYZANTINE PHILOSOPHY',
  '解放哲学':'LIBERATION PHILOSOPHY','后殖民哲学':'POSTCOLONIAL PHILOSOPHY','原住民哲学':'INDIGENOUS PHILOSOPHY',
  '环境哲学':'ENVIRONMENTAL PHILOSOPHY','解构主义':'DECONSTRUCTION','黑人哲学':'BLACK PHILOSOPHY',
  '哲学入词':'Philosophical Lyricism','贝叶斯主义':'Bayesian Philosophy',
  '人工智能哲学':'Philosophy of Artificial Intelligence','萨满哲学':'SHAMANIC PHILOSOPHY',
  '北极原住民哲学':'ARCTIC INDIGENOUS PHILOSOPHY','南岛哲学':'AUSTRONESIAN PHILOSOPHY',
  '高加索哲学':'CAUCASIAN PHILOSOPHY','高加索-草原哲学':'CAUCASIAN-STEPPE PHILOSOPHY',
  '太平洋原住民哲学':'PACIFIC INDIGENOUS PHILOSOPHY','斯多葛学派':'STOICISM',
  '伊壁鸠鲁学派':'EPICUREANISM','新柏拉图主义':'NEOPLATONISM','前苏格拉底哲学':'PRESOCRATIC PHILOSOPHY',
  '犬儒学派':'CYNICISM','旧民主主义':'OLD DEMOCRATIC REVOLUTION PHILOSOPHY','新民主主义':'NEW DEMOCRACY THEORY',
  '怀疑论':'SKEPTICISM',
};

// ─── School → data mapping (all loaded from JSON on demand) ───
const SCHOOL_MAP = {
  '印加哲学':{_json:'school_印加哲学.json',bg:'url(/schools/印加哲学.jpg)'},
  '古希腊哲学':{_json:'school_古希腊哲学.json',bg:'url(/schools/古希腊哲学.jpg)'},
  '伊壁鸠鲁学派':{_json:'school_伊壁鸠鲁学派.json',bg:'url(/schools/伊壁鸠鲁学派.jpg)'},
  '新柏拉图主义':{_json:'school_新柏拉图主义.json',bg:'url(/schools/新柏拉图主义.jpg)'},
  '前苏格拉底哲学':{_json:'school_前苏格拉底哲学.json',bg:'url(/schools/前苏格拉底哲学.jpg)'},
  '犬儒学派':{_json:'school_犬儒学派.json',bg:'url(/schools/犬儒学派.jpg)'},
  '斯多葛学派':{_json:'school_斯多葛学派.json',bg:'url(/schools/斯多葛学派.jpg)'},
  '怀疑论':{_json:'school_怀疑论.json',bg:'url(/schools/怀疑论.jpg)'},
  '教父哲学':{_json:'school_教父哲学.json',bg:'url(/schools/教父哲学.jpg)'},
  '经院哲学':{_json:'school_经院哲学.json',bg:'url(/schools/经院哲学.jpg)'},
  '理性主义':{_json:'school_理性主义.json',bg:'url(/schools/理性主义.jpg)'},
  '经验主义':{_json:'school_经验主义.json',bg:'url(/schools/经验主义.jpg)'},
  '启蒙运动':{_json:'school_启蒙运动.json',bg:'url(/schools/启蒙运动.jpg)'},
  '实在论':{_json:'school_实在论.json',bg:'url(/schools/实在论.jpg)'},
  '唯心主义':{_json:'school_唯心主义.json',bg:'url(/schools/唯心主义.jpg)'},
  '自由主义':{_json:'school_自由主义.json',bg:'url(/schools/自由主义.jpg)'},
  '浪漫主义':{_json:'school_浪漫主义.json',bg:'url(/schools/浪漫主义.jpg)'},
  '女性主义':{_json:'school_女性主义.json',bg:'url(/schools/女性主义.jpg)'},
  '德国古典哲学':{_json:'school_德国古典哲学.json',bg:'url(/schools/德国古典哲学.jpg)'},
  '生命哲学':{_json:'school_生命哲学.json',bg:'url(/schools/生命哲学.jpg)'},
  '马克思主义':{_json:'school_马克思主义.json',bg:'url(/schools/马克思主义.jpg)'},
  '存在主义':{_json:'school_存在主义.json',bg:'url(/schools/存在主义.jpg)'},
  '精神分析学':{_json:'school_精神分析学.json',bg:'url(/schools/精神分析学.jpg)'},
  '结构主义':{_json:'school_结构主义.json',bg:'url(/schools/结构主义.jpg)'},
  '现象学':{_json:'school_现象学.json',bg:'url(/schools/现象学.jpg)'},
  '分析哲学':{_json:'school_分析哲学.json',bg:'url(/schools/分析哲学.jpg)'},
  '法兰克福学派':{_json:'school_法兰克福学派.json',bg:'url(/schools/法兰克福学派.jpg)'},
  '荒诞哲学':{_json:'school_荒诞哲学.json',bg:'url(/schools/荒诞哲学.jpg)'},
  '后结构主义':{_json:'school_后结构主义.json',bg:'url(/schools/后结构主义.jpg)'},
  '功利主义':{_json:'school_功利主义.json',bg:'url(/schools/功利主义.jpg)'},
  '超验主义':{_json:'school_超验主义.json',bg:'url(/schools/超验主义.jpg)'},
  '实证主义':{_json:'school_实证主义.json',bg:'url(/schools/实证主义.jpg)'},
  '社会学':{_json:'school_社会学.json',bg:'url(/schools/社会学.jpg)'},
  '实用主义':{_json:'school_实用主义.json',bg:'url(/schools/实用主义.jpg)'},
  '过程哲学':{_json:'school_过程哲学.json',bg:'url(/schools/过程哲学.jpg)'},
  '哲学人类学':{_json:'school_哲学人类学.json',bg:'url(/schools/哲学人类学.jpg)'},
  '科学哲学':{_json:'school_科学哲学.json',bg:'url(/schools/科学哲学.jpg)'},
  '西方马克思主义':{_json:'school_西方马克思主义.json',bg:'url(/schools/西方马克思主义.jpg)'},
  '政治哲学':{_json:'school_政治哲学.json',bg:'url(/schools/政治哲学.jpg)'},
  '伦理学':{_json:'school_伦理学.json',bg:'url(/schools/伦理学.jpg)'},
  '基督教哲学':{_json:'school_基督教哲学.json',bg:'url(/schools/基督教哲学.jpg)'},
  '哲学诠释学':{_json:'school_哲学诠释学.json',bg:'url(/schools/哲学诠释学.jpg)'},
  '后现代主义':{_json:'school_后现代主义.json',bg:'url(/schools/后现代主义.jpg)'},
  '唯名论':{_json:'school_唯名论.json',bg:'url(/schools/唯名论.jpg)'},
  '批判理论':{_json:'school_批判理论.json',bg:'url(/schools/批判理论.jpg)'},
  '社群主义':{_json:'school_社群主义.json',bg:'url(/schools/社群主义.jpg)'},
  '技术哲学':{_json:'school_技术哲学.json',bg:'url(/schools/技术哲学.jpg)'},
  '宗教哲学':{_json:'school_宗教哲学.json',bg:'url(/schools/宗教哲学.jpg)'},
  '儒家':{_json:'school_儒家.json',bg:'url(/schools/儒家.jpg)'},
  '道家':{_json:'school_道家.json',bg:'url(/schools/道家.jpg)'},
  '墨家':{_json:'school_墨家.json',bg:'url(/schools/墨家.jpg)'},
  '法家':{_json:'school_法家.json',bg:'url(/schools/法家.jpg)'},
  '名家':{_json:'school_名家.json',bg:'url(/schools/名家.jpg)'},
  '阴阳家':{_json:'school_阴阳家.json',bg:'url(/schools/阴阳家.jpg)'},
  '兵家':{_json:'school_兵家.json',bg:'url(/schools/兵家.jpg)'},
  '两汉经学':{_json:'school_两汉经学.json',bg:'url(/schools/两汉经学.jpg)'},
  '魏晋玄学':{_json:'school_魏晋玄学.json',bg:'url(/schools/魏晋玄学.jpg)'},
  '隋唐佛学':{_json:'school_隋唐佛学.json',bg:'url(/schools/隋唐佛学.jpg)'},
  '宋明理学':{_json:'school_宋明理学.json',bg:'url(/schools/宋明理学.jpg)'},
  '明清实学':{_json:'school_明清实学.json',bg:'url(/schools/明清实学.jpg)'},
  '乾嘉朴学':{_json:'school_乾嘉朴学.json',bg:'url(/schools/乾嘉朴学.jpg)'},
  '天演论':{_json:'school_天演论.json',bg:'url(/schools/天演论.jpg)'},
  '维新派':{_json:'school_维新派.json',bg:'url(/schools/维新派.jpg)'},
  '三民主义':{_json:'school_三民主义.json',bg:'url(/schools/三民主义.jpg)'},
  '毛泽东思想':{_json:'school_毛泽东思想.json',bg:'url(/schools/毛泽东思想.jpg)'},
  '中国马克思主义哲学':{_json:'school_中国马克思主义哲学.json',bg:'url(/schools/中国马克思主义哲学.jpg)'},
  '现代新儒家':{_json:'school_现代新儒家.json',bg:'url(/schools/现代新儒家.jpg)'},
  '中国实证哲学':{_json:'school_中国实证哲学.json',bg:'url(/schools/中国实证哲学.jpg)'},
  '马克思主义哲学的中国化与体系化':{_json:'school_马克思主义哲学的中国化与体系化.json',bg:'url(/schools/马克思主义哲学的中国化与体系化.jpg)'},
  '习近平新时代中国特色社会主义思想':{_json:'school_习近平新时代中国特色社会主义思想.json',bg:'url(/schools/习近平新时代中国特色社会主义思想.jpg)'},
  '印度哲学':{_json:'school_印度哲学.json',bg:'url(/schools/印度哲学.jpg)'},
  '日本哲学':{_json:'school_日本哲学.json',bg:'url(/schools/日本哲学.jpg)'},
  '伊斯兰哲学':{_json:'school_伊斯兰哲学.json',bg:'url(/schools/伊斯兰哲学.jpg)'},
  '非洲哲学':{_json:'school_非洲哲学.json',bg:'url(/schools/非洲哲学.jpg)'},
  '犹太哲学':{_json:'school_犹太哲学.json',bg:'url(/schools/犹太哲学.jpg)'},
  '波斯哲学':{_json:'school_波斯哲学.json',bg:'url(/schools/波斯哲学.jpg)'},
  '拉丁美洲哲学':{_json:'school_拉丁美洲哲学.json',bg:'url(/schools/拉丁美洲哲学.jpg)'},
  '东南亚哲学':{_json:'school_东南亚哲学.json',bg:'url(/schools/东南亚哲学.jpg)'},
  '阿拉伯哲学':{_json:'school_阿拉伯哲学.json',bg:'url(/schools/阿拉伯哲学.jpg)'},
  '新民主主义':{_json:'school_新民主主义.json',bg:'url(/schools/新民主主义.jpg)'},
  '旧民主主义':{_json:'school_旧民主主义.json',bg:'url(/schools/旧民主主义.jpg)'},
  '韩国哲学':{_json:'school_韩国哲学.json',bg:'url(/schools/韩国哲学.jpg)'},
  '西藏哲学':{_json:'school_西藏哲学.json',bg:'url(/schools/西藏哲学.jpg)'},
  '北欧哲学':{_json:'school_北欧哲学.json',bg:'url(/schools/北欧哲学.jpg)'},
  '玛雅哲学':{_json:'school_玛雅哲学.json',bg:'url(/schools/玛雅哲学.jpg)'},
  '阿兹特克哲学':{_json:'school_阿兹特克哲学.json',bg:'url(/schools/阿兹特克哲学.jpg)'},
  '澳洲原住民哲学':{_json:'school_澳洲原住民哲学.json',bg:'url(/schools/澳洲原住民哲学.jpg)'},
  '蒙古中亚哲学':{_json:'school_蒙古中亚哲学.json',bg:'url(/schools/蒙古中亚哲学.jpg)'},
  '东欧斯拉夫哲学':{_json:'school_东欧斯拉夫哲学.json',bg:'url(/schools/东欧斯拉夫哲学.jpg)'},
  '北美哲学':{_json:'school_北美哲学.json',bg:'url(/schools/北美哲学.jpg)'},
  '美索不达米亚哲学':{_json:'school_美索不达米亚哲学.json',bg:'url(/schools/美索不达米亚哲学.jpg)'},
  '古埃及哲学':{_json:'school_古埃及哲学.json',bg:'url(/schools/古埃及哲学.jpg)'},
  '古希伯来哲学':{_json:'school_古希伯来哲学.json',bg:'url(/schools/古希伯来哲学.jpg)'},
  '凯尔特哲学':{_json:'school_凯尔特哲学.json',bg:'url(/schools/凯尔特哲学.jpg)'},
  '罗马哲学':{_json:'school_罗马哲学.json',bg:'url(/schools/罗马哲学.jpg)'},
  '拜占庭哲学':{_json:'school_拜占庭哲学.json',bg:'url(/schools/拜占庭哲学.jpg)'},
  '解放哲学':{_json:'school_解放哲学.json',bg:'url(/schools/解放哲学.jpg)'},
  '后殖民哲学':{_json:'school_后殖民哲学.json',bg:'url(/schools/后殖民哲学.jpg)'},
  '原住民哲学':{_json:'school_原住民哲学.json',bg:'url(/schools/原住民哲学.jpg)'},
  '环境哲学':{_json:'school_环境哲学.json',bg:'url(/schools/环境哲学.jpg)'},
  '解构主义':{_json:'school_解构主义.json',bg:'url(/schools/解构主义.jpg)'},
  '黑人哲学':{_json:'school_黑人哲学.json',bg:'url(/schools/黑人哲学.jpg)'},
  '哲学入词':{_json:'school_哲学入词.json',bg:'url(/schools/哲学入词.png)'},
  '贝叶斯主义':{_json:'school_贝叶斯主义.json',bg:'url(/schools/贝叶斯主义_bayes.jpg)'},
  '人工智能哲学':{_json:'school_人工智能哲学.json',bg:'url(/schools/人工智能哲学_v2.jpg)'},
  '萨满哲学':{_json:'school_萨满哲学.json',bg:'url(/schools/shaman.jpg)'},
  '北极原住民哲学':{_json:'school_北极原住民哲学.json',bg:'url(/schools/arctic.jpg)'},
  '南岛哲学':{_json:'school_南岛哲学.json',bg:'url(/schools/austronesian.jpg)'},
  '高加索哲学':{_json:'school_高加索哲学.json',bg:'url(/schools/caucasus.jpg)'},
  '高加索-草原哲学':{_json:'school_高加索草原哲学.json',bg:'url(/schools/caucasus-steppe.jpg)'},
  '太平洋原住民哲学':{_json:'school_太平洋原住民哲学.json',bg:'url(/schools/pacific.jpg)'},
};

// ─── 动画包裹 ───
function FadeSection({ children, style }) {
  const ref = useRef(null); const [on, setOn] = useState(false);
  useEffect(() => { const el = ref.current; if (!el) return; const o = new IntersectionObserver(([e]) => { if (e.isIntersecting) setOn(true); }, { threshold:0.05 }); o.observe(el); return () => o.disconnect(); }, []);
  return <div ref={ref} style={{ opacity:on?1:0, transform:on?'translateY(0)':'translateY(20px)', transition:'opacity 0.6s ease, transform 0.6s ease', ...style }}>{children}</div>;
}

export default function SchoolDetailPage() {
  const { name } = useParams();
  const navigate = useNavigate();

  const m = SCHOOL_MAP[name] || {};
  const [dynamicData, setDynamicData] = useState(null);
  const [loadError, setLoadError] = useState(false);

  // SEO
  useSEO(data?.name || name, data?.subtitle || `探索${name}哲学流派的核心思想与代表人物`);

  // Load school data from JSON on demand
  useEffect(() => {
    setDynamicData(null);
    setLoadError(false);
    if (m._json) {
      fetch('/schools/data/' + m._json)
        .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(d => setDynamicData(d))
        .catch(() => setLoadError(true));
    }
  }, [name]);

  const data = dynamicData || null;
  const heroImage = m.bg || 'url(/schools/default.jpg)';

  // Auto-generate subColors from thinkers
  const subColors = (() => {
    const sc = {};
    if (data?.thinkers) {
      data.thinkers.forEach(t => {
        if (t.sub) {
          t.sub.split(/[/,，、;；]/).forEach(s => {
            s = s.trim().replace(/[（(].*[)）]/g, '');
            if (s && !sc[s]) {
              const hash = s.split('').reduce((a,c) => a + c.charCodeAt(0), 0);
              const h = (hash * 137) % 360;
              sc[s] = 'hsl(' + h + ',50%,55%)';
            }
          });
        }
      });
    }
    return sc;
  })();

  // ─── Radial force-directed layout for thinkers constellation ───
  const thinkers = (() => {
    const ts = data?.thinkers;
    if (!ts?.length) return [];
    const rels = data?.relations || [];
    const cx = 400, cy = 280;
    const getR = (t) => { const inf = t.influence || 5; const base = inf >= 10 ? 28 : inf >= 9 ? 24 : inf >= 8 ? 20 : inf >= 7 ? 17 : 14; return base + 14; };

    const adj = {}; ts.forEach(t => { adj[t.name] = []; });
    rels.forEach(r => { if (adj[r.from] && adj[r.to]) { adj[r.from].push(r.to); adj[r.to].push(r.from); } });

    const sorted = [...ts].sort((a, b) => (b.influence || 5) - (a.influence || 5));
    const center = sorted[0];
    if (!center) return ts.map(t => ({...t, _x:cx, _y:cy}));

    const layers = {}; const visited = new Set(); const queue = [{ name: center.name, layer: 0 }];
    visited.add(center.name);
    while (queue.length) {
      const { name: cn, layer } = queue.shift();
      if (!layers[layer]) layers[layer] = [];
      layers[layer].push(cn);
      (adj[cn] || []).forEach(nb => { if (!visited.has(nb)) { visited.add(nb); queue.push({ name: nb, layer: layer + 1 }); } });
    }
    ts.forEach(t => { if (!visited.has(t.name)) { if (!layers[99]) layers[99] = []; layers[99].push(t.name); } });

    const positions = {}; const layerKeys = Object.keys(layers).map(Number).sort((a, b) => a - b);
    const maxLayer = Math.max(...layerKeys, 1);
    positions[center.name] = { _x: cx, _y: cy };

    layerKeys.forEach(layer => {
      if (layer === 0) return;
      const names = layers[layer] || [];
      const layerRadius = 70 + (layer / maxLayer) * 240;
      const count = names.length;

      names.forEach((nm, i) => {
        const parents = rels.filter(r => r.from === nm || r.to === nm).map(r => r.from === nm ? r.to : r.from).filter(p => positions[p]);
        let angle;
        if (parents.length > 0) {
          const sumAngle = parents.reduce((s, p) => { const dx = positions[p]._x - cx, dy = positions[p]._y - cy; return s + Math.atan2(dy, dx); }, 0);
          angle = sumAngle / parents.length + (i - count / 2) * 1.2;
        } else {
          angle = (i / Math.max(count, 1)) * Math.PI * 2 + layer * 0.4;
        }
        let px = cx + Math.cos(angle) * layerRadius, py = cy + Math.sin(angle) * layerRadius * 0.7;
        let attempts = 0, overlap = true;
        while (overlap && attempts < 50) {
          overlap = false;
          for (const pName in positions) {
            const dx2 = px - positions[pName]._x, dy2 = py - positions[pName]._y;
            const dist = Math.sqrt(dx2*dx2 + dy2*dy2);
            const t1 = ts.find(x => x.name === nm), t2 = ts.find(x => x.name === pName);
            const minD = getR(t1) + getR(t2) + 12;
            if (dist < minD) { overlap = true; const pushAngle = Math.atan2(dy2, dx2); px += Math.cos(pushAngle)*14; py += Math.sin(pushAngle)*14; break; }
          }
          px = Math.max(60, Math.min(740, px)); py = Math.max(45, Math.min(515, py));
          attempts++;
        }
        positions[nm] = { _x: px, _y: py };
      });
    });

    return ts.map(t => ({
      ...t,
      _x: (positions[t.name] || { _x: cx + (Math.random()-0.5)*300 })._x,
      _y: (positions[t.name] || { _y: cy + (Math.random()-0.5)*200 })._y,
    }));
  })();

  // Loading state
  if (m._json && !data && !loadError) {
    return (
      <div style={{ background:'var(--bg)', minHeight:'100vh', display:'flex', justifyContent:'center', alignItems:'center' }}>
        <div className="loading">加载流派数据...</div>
      </div>
    );
  }

  // Coming soon / not found
  if (!m._json || (loadError && !data)) {
    return (
      <div style={{ background:'var(--bg)', minHeight:'100vh', display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'center', textAlign:'center', padding:'60px 32px' }}>
        <p style={{ fontSize:10, letterSpacing:'0.24em', textTransform:'uppercase', color:'var(--ochre)', marginBottom:24, fontFamily:'var(--font-sans)' }}>Coming Soon</p>
        <h1 style={{ fontSize:'clamp(2rem,5vw,3rem)', fontWeight:400, color:'var(--ink)', letterSpacing:'0.04em', marginBottom:16, fontFamily:'"Playfair Display","PingFang SC",serif' }}>{name}</h1>
        <div style={{ width:32, height:1.5, background:'var(--ochre)', marginBottom:20, opacity:0.4 }} />
        <p style={{ fontSize:'1rem', fontWeight:300, color:'var(--text-dim)', lineHeight:2.0, maxWidth:500, fontFamily:'var(--font-sans)' }}>该流派详情页正在建设中，敬请期待。</p>
        <button onClick={() => window.history.back()} style={{ marginTop:32, background:'none', border:'1px solid rgba(145,118,71,0.2)', borderRadius:6, padding:'10px 28px', fontSize:13, color:'var(--ochre)', cursor:'pointer', letterSpacing:'0.06em', fontFamily:'var(--font-sans)' }}>← 返回</button>
      </div>
    );
  }

  const subSchools = data.subSchools || {};
  const cihai = data.cihai || [];

  return (
    <div style={{ background: 'var(--bg)', color: 'var(--text)', fontFamily: '"Playfair Display","PingFang SC",serif' }}>
      <HeroSection name={data.name} subtitle={data.subtitle} quote={data.quote} quoteAuthor={data.quoteAuthor} heroImage={heroImage} englishName={ENG_NAMES[data.name]} />
      <div id="school-content">
      <FadeSection><OverviewSection overview={data.overview} subSchools={subSchools} /></FadeSection>
      <FadeSection><ConstellationMap thinkers={thinkers} relations={data.relations} SUB_COLORS={{...SUB_COLORS, ...subColors}} /></FadeSection>
      <FadeSection><TimelineSection timeline={data.timeline} /></FadeSection>
      <FadeSection><GlossaryCloud cihai={cihai} /></FadeSection>
      <FadeSection><QuotesGallery quotes={data.quotes} /></FadeSection>
      <FadeSection><WorksList works={data.works} /></FadeSection>
      <FadeSection><EpilogueSection conclusion={data.conclusion} closingQuote={data.closingQuote} closingQuoteAuthor={data.closingQuoteAuthor} /></FadeSection>
      </div>
    </div>
  );
}
