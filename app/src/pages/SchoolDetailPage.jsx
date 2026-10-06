/**
 * 流派详情页 — 滚轮下翻式，数据按需从 JSON 加载
 * 所有流派数据存储在 /public/schools/data/school_*.json
 */
import { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import HeroSection from '../components/school/HeroSection';
import OverviewSection from '../components/school/OverviewSection';
import ConstellationMap from '../components/school/ConstellationMap';
import TimelineSection from '../components/school/TimelineSection';
import GlossaryCloud from '../components/school/GlossaryCloud';
import QuotesGallery from '../components/school/QuotesGallery';
import WorksList from '../components/school/WorksList';
import EpilogueSection from '../components/school/EpilogueSection';
import SubSchoolsSection from '../components/school/SubSchoolsSection';
import { normalizeSchool, buildSchoolReferences, fetchSchoolJSON } from '../data/schoolContent';
import './SchoolDetailPage.css';

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
  '印加哲学':{_json:'school_印加哲学.json',bg:'url(/schools/印加哲学.webp)'},
  '古希腊哲学':{_json:'school_古希腊哲学.json',bg:'url(/schools/古希腊哲学.webp)'},
  '伊壁鸠鲁学派':{_json:'school_伊壁鸠鲁学派.json',bg:'url(/schools/伊壁鸠鲁学派.webp)'},
  '新柏拉图主义':{_json:'school_新柏拉图主义.json',bg:'url(/schools/新柏拉图主义.webp)'},
  '前苏格拉底哲学':{_json:'school_前苏格拉底哲学.json',bg:'url(/schools/前苏格拉底哲学.webp)'},
  '犬儒学派':{_json:'school_犬儒学派.json',bg:'url(/schools/犬儒学派.webp)'},
  '斯多葛学派':{_json:'school_斯多葛学派.json',bg:'url(/schools/斯多葛学派.webp)'},
  '怀疑论':{_json:'school_怀疑论.json',bg:'url(/schools/怀疑论.webp)'},
  '教父哲学':{_json:'school_教父哲学.json',bg:'url(/schools/教父哲学.webp)'},
  '经院哲学':{_json:'school_经院哲学.json',bg:'url(/schools/经院哲学.webp)'},
  '理性主义':{_json:'school_理性主义.json',bg:'url(/schools/理性主义.webp)'},
  '经验主义':{_json:'school_经验主义.json',bg:'url(/schools/经验主义.webp)'},
  '启蒙运动':{_json:'school_启蒙运动.json',bg:'url(/schools/启蒙运动.webp)'},
  '实在论':{_json:'school_实在论.json',bg:'url(/schools/实在论.webp)'},
  '唯心主义':{_json:'school_唯心主义.json',bg:'url(/schools/唯心主义.webp)'},
  '自由主义':{_json:'school_自由主义.json',bg:'url(/schools/自由主义.webp)'},
  '浪漫主义':{_json:'school_浪漫主义.json',bg:'url(/schools/浪漫主义.webp)'},
  '女性主义':{_json:'school_女性主义.json',bg:'url(/schools/女性主义.webp)'},
  '德国古典哲学':{_json:'school_德国古典哲学.json',bg:'url(/schools/德国古典哲学.webp)'},
  '生命哲学':{_json:'school_生命哲学.json',bg:'url(/schools/生命哲学.webp)'},
  '马克思主义':{_json:'school_马克思主义.json',bg:'url(/schools/马克思主义.webp)'},
  '存在主义':{_json:'school_存在主义.json',bg:'url(/schools/存在主义.webp)'},
  '精神分析学':{_json:'school_精神分析学.json',bg:'url(/schools/精神分析学.webp)'},
  '结构主义':{_json:'school_结构主义.json',bg:'url(/schools/结构主义.webp)'},
  '现象学':{_json:'school_现象学.json',bg:'url(/schools/现象学.webp)'},
  '分析哲学':{_json:'school_分析哲学.json',bg:'url(/schools/分析哲学.webp)'},
  '法兰克福学派':{_json:'school_法兰克福学派.json',bg:'url(/schools/法兰克福学派.webp)'},
  '荒诞哲学':{_json:'school_荒诞哲学.json',bg:'url(/schools/荒诞哲学.webp)'},
  '后结构主义':{_json:'school_后结构主义.json',bg:'url(/schools/后结构主义.webp)'},
  '功利主义':{_json:'school_功利主义.json',bg:'url(/schools/功利主义.webp)'},
  '超验主义':{_json:'school_超验主义.json',bg:'url(/schools/超验主义.webp)'},
  '实证主义':{_json:'school_实证主义.json',bg:'url(/schools/实证主义.webp)'},
  '社会学':{_json:'school_社会学.json',bg:'url(/schools/社会学.webp)'},
  '实用主义':{_json:'school_实用主义.json',bg:'url(/schools/实用主义.webp)'},
  '过程哲学':{_json:'school_过程哲学.json',bg:'url(/schools/过程哲学.webp)'},
  '哲学人类学':{_json:'school_哲学人类学.json',bg:'url(/schools/哲学人类学.webp)'},
  '科学哲学':{_json:'school_科学哲学.json',bg:'url(/schools/科学哲学.webp)'},
  '西方马克思主义':{_json:'school_西方马克思主义.json',bg:'url(/schools/西方马克思主义.webp)'},
  '政治哲学':{_json:'school_政治哲学.json',bg:'url(/schools/政治哲学.webp)'},
  '伦理学':{_json:'school_伦理学.json',bg:'url(/schools/伦理学.webp)'},
  '基督教哲学':{_json:'school_基督教哲学.json',bg:'url(/schools/基督教哲学.webp)'},
  '哲学诠释学':{_json:'school_哲学诠释学.json',bg:'url(/schools/哲学诠释学.webp)'},
  '后现代主义':{_json:'school_后现代主义.json',bg:'url(/schools/后现代主义.webp)'},
  '唯名论':{_json:'school_唯名论.json',bg:'url(/schools/唯名论.webp)'},
  '批判理论':{_json:'school_批判理论.json',bg:'url(/schools/批判理论.webp)'},
  '社群主义':{_json:'school_社群主义.json',bg:'url(/schools/社群主义.webp)'},
  '技术哲学':{_json:'school_技术哲学.json',bg:'url(/schools/技术哲学.webp)'},
  '宗教哲学':{_json:'school_宗教哲学.json',bg:'url(/schools/宗教哲学.webp)'},
  '儒家':{_json:'school_儒家.json',bg:'url(/schools/儒家.webp)'},
  '道家':{_json:'school_道家.json',bg:'url(/schools/道家.webp)'},
  '墨家':{_json:'school_墨家.json',bg:'url(/schools/墨家.webp)'},
  '法家':{_json:'school_法家.json',bg:'url(/schools/法家.webp)'},
  '名家':{_json:'school_名家.json',bg:'url(/schools/名家.webp)'},
  '阴阳家':{_json:'school_阴阳家.json',bg:'url(/schools/阴阳家.webp)'},
  '兵家':{_json:'school_兵家.json',bg:'url(/schools/兵家.webp)'},
  '两汉经学':{_json:'school_两汉经学.json',bg:'url(/schools/两汉经学.webp)'},
  '魏晋玄学':{_json:'school_魏晋玄学.json',bg:'url(/schools/魏晋玄学.webp)'},
  '隋唐佛学':{_json:'school_隋唐佛学.json',bg:'url(/schools/隋唐佛学.webp)'},
  '宋明理学':{_json:'school_宋明理学.json',bg:'url(/schools/宋明理学.webp)'},
  '明清实学':{_json:'school_明清实学.json',bg:'url(/schools/明清实学.webp)'},
  '乾嘉朴学':{_json:'school_乾嘉朴学.json',bg:'url(/schools/乾嘉朴学.webp)'},
  '天演论':{_json:'school_天演论.json',bg:'url(/schools/天演论.webp)'},
  '维新派':{_json:'school_维新派.json',bg:'url(/schools/维新派.webp)'},
  '三民主义':{_json:'school_三民主义.json',bg:'url(/schools/三民主义.webp)'},
  '毛泽东思想':{_json:'school_毛泽东思想.json',bg:'url(/schools/毛泽东思想.webp)'},
  '中国马克思主义哲学':{_json:'school_中国马克思主义哲学.json',bg:'url(/schools/中国马克思主义哲学.webp)'},
  '现代新儒家':{_json:'school_现代新儒家.json',bg:'url(/schools/现代新儒家.webp)'},
  '中国实证哲学':{_json:'school_中国实证哲学.json',bg:'url(/schools/中国实证哲学.webp)'},
  '马克思主义哲学的中国化与体系化':{_json:'school_马克思主义哲学的中国化与体系化.json',bg:'url(/schools/马克思主义哲学的中国化与体系化.webp)'},
  '习近平新时代中国特色社会主义思想':{_json:'school_习近平新时代中国特色社会主义思想.json',bg:'url(/schools/习近平新时代中国特色社会主义思想.webp)'},
  '印度哲学':{_json:'school_印度哲学.json',bg:'url(/schools/印度哲学.webp)'},
  '日本哲学':{_json:'school_日本哲学.json',bg:'url(/schools/日本哲学.webp)'},
  '伊斯兰哲学':{_json:'school_伊斯兰哲学.json',bg:'url(/schools/伊斯兰哲学.webp)'},
  '非洲哲学':{_json:'school_非洲哲学.json',bg:'url(/schools/非洲哲学.webp)'},
  '犹太哲学':{_json:'school_犹太哲学.json',bg:'url(/schools/犹太哲学.webp)'},
  '波斯哲学':{_json:'school_波斯哲学.json',bg:'url(/schools/波斯哲学.webp)'},
  '拉丁美洲哲学':{_json:'school_拉丁美洲哲学.json',bg:'url(/schools/拉丁美洲哲学.webp)'},
  '东南亚哲学':{_json:'school_东南亚哲学.json',bg:'url(/schools/东南亚哲学.webp)'},
  '阿拉伯哲学':{_json:'school_阿拉伯哲学.json',bg:'url(/schools/阿拉伯哲学.webp)'},
  '新民主主义':{_json:'school_新民主主义.json',bg:'url(/schools/新民主主义.webp)'},
  '旧民主主义':{_json:'school_旧民主主义.json',bg:'url(/schools/旧民主主义.webp)'},
  '韩国哲学':{_json:'school_韩国哲学.json',bg:'url(/schools/韩国哲学.webp)'},
  '西藏哲学':{_json:'school_西藏哲学.json',bg:'url(/schools/西藏哲学.webp)'},
  '北欧哲学':{_json:'school_北欧哲学.json',bg:'url(/schools/北欧哲学.webp)'},
  '玛雅哲学':{_json:'school_玛雅哲学.json',bg:'url(/schools/玛雅哲学.webp)'},
  '阿兹特克哲学':{_json:'school_阿兹特克哲学.json',bg:'url(/schools/阿兹特克哲学.webp)'},
  '澳洲原住民哲学':{_json:'school_澳洲原住民哲学.json',bg:'url(/schools/澳洲原住民哲学.webp)'},
  '蒙古中亚哲学':{_json:'school_蒙古中亚哲学.json',bg:'url(/schools/蒙古中亚哲学.webp)'},
  '东欧斯拉夫哲学':{_json:'school_东欧斯拉夫哲学.json',bg:'url(/schools/东欧斯拉夫哲学.webp)'},
  '北美哲学':{_json:'school_北美哲学.json',bg:'url(/schools/北美哲学.webp)'},
  '美索不达米亚哲学':{_json:'school_美索不达米亚哲学.json',bg:'url(/schools/美索不达米亚哲学.webp)'},
  '古埃及哲学':{_json:'school_古埃及哲学.json',bg:'url(/schools/古埃及哲学.webp)'},
  '古希伯来哲学':{_json:'school_古希伯来哲学.json',bg:'url(/schools/古希伯来哲学.webp)'},
  '凯尔特哲学':{_json:'school_凯尔特哲学.json',bg:'url(/schools/凯尔特哲学.webp)'},
  '罗马哲学':{_json:'school_罗马哲学.json',bg:'url(/schools/罗马哲学.webp)'},
  '拜占庭哲学':{_json:'school_拜占庭哲学.json',bg:'url(/schools/拜占庭哲学.webp)'},
  '解放哲学':{_json:'school_解放哲学.json',bg:'url(/schools/解放哲学.webp)'},
  '后殖民哲学':{_json:'school_后殖民哲学.json',bg:'url(/schools/后殖民哲学.webp)'},
  '原住民哲学':{_json:'school_原住民哲学.json',bg:'url(/schools/原住民哲学.webp)'},
  '环境哲学':{_json:'school_环境哲学.json',bg:'url(/schools/环境哲学.webp)'},
  '解构主义':{_json:'school_解构主义.json',bg:'url(/schools/解构主义.webp)'},
  '黑人哲学':{_json:'school_黑人哲学.json',bg:'url(/schools/黑人哲学.webp)'},
  '哲学入词':{_json:'school_哲学入词.json',bg:'url(/schools/哲学入词.webp)'},
  '贝叶斯主义':{_json:'school_贝叶斯主义.json',bg:'url(/schools/贝叶斯主义.webp)'},
  '人工智能哲学':{_json:'school_人工智能哲学.json',bg:'url(/schools/人工智能哲学.webp)'},
  // ── 2026-10 内容扩充批次（59 包 + N组）──
  '认识论':{_json:'school_认识论.json',bg:'url(/schools/认识论.webp)'},
  '形而上学':{_json:'school_形而上学.json',bg:'url(/schools/形而上学.webp)'},
  '逻辑与逻辑哲学':{_json:'school_逻辑与逻辑哲学.json',bg:'url(/schools/逻辑与逻辑哲学.webp)'},
  '心灵哲学':{_json:'school_心灵哲学.json',bg:'url(/schools/心灵哲学.webp)'},
  '语言哲学':{_json:'school_语言哲学.json',bg:'url(/schools/语言哲学.webp)'},
  '美学':{_json:'school_美学.json',bg:'url(/schools/美学.webp)'},
  '佛教哲学':{_json:'school_佛教哲学.json',bg:'url(/schools/佛教哲学.webp)'},
  '道教哲学':{_json:'school_道教哲学.json',bg:'url(/schools/道教哲学.webp)'},
  '正理派':{_json:'school_正理派.json',bg:'url(/schools/正理派.webp)'},
  '胜论派':{_json:'school_胜论派.json',bg:'url(/schools/胜论派.webp)'},
  '弥曼差派':{_json:'school_弥曼差派.json',bg:'url(/schools/弥曼差派.webp)'},
  '吠檀多':{_json:'school_吠檀多.json',bg:'url(/schools/吠檀多.webp)'},
  '二元论吠檀多':{_json:'school_二元论吠檀多.json',bg:'url(/schools/二元论吠檀多.webp)'},
  '耆那教哲学':{_json:'school_耆那教哲学.json',bg:'url(/schools/耆那教哲学.webp)'},
  '顺世论':{_json:'school_顺世论.json',bg:'url(/schools/顺世论.webp)'},
  '早期佛教思想':{_json:'school_早期佛教思想.json',bg:'url(/schools/早期佛教思想.webp)'},
  '中观':{_json:'school_中观.json',bg:'url(/schools/中观.webp)'},
  '唯识':{_json:'school_唯识.json',bg:'url(/schools/唯识.webp)'},
  '佛教逻辑与认识论':{_json:'school_佛教逻辑与认识论.json',bg:'url(/schools/佛教逻辑与认识论.webp)'},
  '天台宗思想':{_json:'school_天台宗思想.json',bg:'url(/schools/天台宗思想.webp)'},
  '华严宗思想':{_json:'school_华严宗思想.json',bg:'url(/schools/华严宗思想.webp)'},
  '禅宗思想':{_json:'school_禅宗思想.json',bg:'url(/schools/禅宗思想.webp)'},
  '宁玛派思想':{_json:'school_宁玛派思想.json',bg:'url(/schools/宁玛派思想.webp)'},
  '萨迦派思想':{_json:'school_萨迦派思想.json',bg:'url(/schools/萨迦派思想.webp)'},
  '阿毗达磨思想':{_json:'school_阿毗达磨思想.json',bg:'url(/schools/阿毗达磨思想.webp)'},
  '净土思想':{_json:'school_净土思想.json',bg:'url(/schools/净土思想.webp)'},
  '京都学派':{_json:'school_京都学派.json',bg:'url(/schools/京都学派.webp)'},
  '非洲智者哲学':{_json:'school_非洲智者哲学.json',bg:'url(/schools/非洲智者哲学.webp)'},
  '柏拉图主义':{_json:'school_柏拉图主义.json',bg:'url(/schools/柏拉图主义.webp)'},
  '亚里士多德学派（逍遥学派）':{_json:'school_亚里士多德学派（逍遥学派）.json',bg:'url(/schools/亚里士多德学派（逍遥学派）.webp)'},
  '程朱理学':{_json:'school_程朱理学.json',bg:'url(/schools/程朱理学.webp)'},
  '陆王心学':{_json:'school_陆王心学.json',bg:'url(/schools/陆王心学.webp)'},
  '不二论吠檀多':{_json:'school_不二论吠檀多.json',bg:'url(/schools/不二论吠檀多.webp)'},
  '逻辑经验主义':{_json:'school_逻辑经验主义.json',bg:'url(/schools/逻辑经验主义.webp)'},
  '日常语言哲学':{_json:'school_日常语言哲学.json',bg:'url(/schools/日常语言哲学.webp)'},
  '德性伦理学':{_json:'school_德性伦理学.json',bg:'url(/schools/德性伦理学.webp)'},
  '义务论伦理学':{_json:'school_义务论伦理学.json',bg:'url(/schools/义务论伦理学.webp)'},
  '关怀伦理学':{_json:'school_关怀伦理学.json',bg:'url(/schools/关怀伦理学.webp)'},
  '唯物主义':{_json:'school_唯物主义.json',bg:'url(/schools/唯物主义.webp)'},
  '自然主义':{_json:'school_自然主义.json',bg:'url(/schools/自然主义.webp)'},
  '一元论':{_json:'school_一元论.json',bg:'url(/schools/一元论.webp)'},
  '二元论':{_json:'school_二元论.json',bg:'url(/schools/二元论.webp)'},
  '法哲学':{_json:'school_法哲学.json',bg:'url(/schools/法哲学.webp)'},
  '历史哲学':{_json:'school_历史哲学.json',bg:'url(/schools/历史哲学.webp)'},
  '教育哲学':{_json:'school_教育哲学.json',bg:'url(/schools/教育哲学.webp)'},
  '数学哲学':{_json:'school_数学哲学.json',bg:'url(/schools/数学哲学.webp)'},
  '行动哲学':{_json:'school_行动哲学.json',bg:'url(/schools/行动哲学.webp)'},
  '社会认识论':{_json:'school_社会认识论.json',bg:'url(/schools/社会认识论.webp)'},
  '元伦理学':{_json:'school_元伦理学.json',bg:'url(/schools/元伦理学.webp)'},
  '共和主义':{_json:'school_共和主义.json',bg:'url(/schools/共和主义.webp)'},
  '保守主义':{_json:'school_保守主义.json',bg:'url(/schools/保守主义.webp)'},
  '无政府主义':{_json:'school_无政府主义.json',bg:'url(/schools/无政府主义.webp)'},
  '道德实在论':{_json:'school_道德实在论.json',bg:'url(/schools/道德实在论.webp)'},
  '泛非主义思想':{_json:'school_泛非主义思想.json',bg:'url(/schools/泛非主义思想.webp)'},
  '托马斯主义':{_json:'school_托马斯主义.json',bg:'url(/schools/托马斯主义.webp)'},
  '文艺复兴人文主义':{_json:'school_文艺复兴人文主义.json',bg:'url(/schools/文艺复兴人文主义.webp)'},
  '新康德主义':{_json:'school_新康德主义.json',bg:'url(/schools/新康德主义.webp)'},
  '杂家':{_json:'school_杂家.json',bg:'url(/schools/杂家.webp)'},
  '纵横家':{_json:'school_纵横家.json',bg:'url(/schools/纵横家.webp)'},
  '后室哲学':{_json:'school_后室哲学.json',bg:'url(/schools/后室哲学.webp)'},
  '奶龙哲学':{_json:'school_奶龙哲学.json',bg:'url(/schools/奶龙哲学.webp)'},
  '自然哲学':{_json:'school_自然哲学.json',bg:'url(/schools/自然哲学.webp)'},
  '宇宙宗教观':{_json:'school_宇宙宗教观.json',bg:'url(/schools/宇宙宗教观.webp)'},
  '克苏鲁宇宙观':{_json:'school_克苏鲁宇宙观.json',bg:'url(/schools/克苏鲁宇宙观.webp)'},
  '萨满哲学':{_json:'school_萨满哲学.json',bg:'url(/schools/萨满哲学.webp)'},
  '北极原住民哲学':{_json:'school_北极原住民哲学.json',bg:'url(/schools/北极原住民哲学.webp)'},
  '南岛哲学':{_json:'school_南岛哲学.json',bg:'url(/schools/南岛哲学.webp)'},
  '高加索哲学':{_json:'school_高加索哲学.json',bg:'url(/schools/高加索哲学.webp)'},
  '高加索-草原哲学':{_json:'school_高加索草原哲学.json',bg:'url(/schools/高加索-草原哲学.webp)'},
  '太平洋原住民哲学':{_json:'school_太平洋原住民哲学.json',bg:'url(/schools/太平洋原住民哲学.webp)'},
};

const EMPTY_CATALOG = { books: [], philosophers: [], schools: [], branches: {} };

function goToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
}

export default function SchoolDetailPage() {
  const { name } = useParams();
  const location = useLocation();
  const [loaded, setLoaded] = useState(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [conceptRequest, setConceptRequest] = useState(0);
  const data = loaded?.data;
  const references = useMemo(() => buildSchoolReferences(loaded?.catalog || EMPTY_CATALOG), [loaded?.catalog]);
  useSEO(data?.name || name, data?.subtitle || `${name}的核心思想、人物、历史与原典`);

  useEffect(() => {
    const controller = new AbortController();
    const direct = SCHOOL_MAP[name];
    async function load() {
      const [catalog, directData] = await Promise.all([
        fetchSchoolJSON('/schools/catalog.json', controller.signal).catch(() => EMPTY_CATALOG),
        direct ? fetchSchoolJSON('/schools/data/' + direct._json, controller.signal) : Promise.resolve(null),
      ]);
      const parent = !direct && catalog.branches?.[name]?.[0];
      const item = catalog.schools.find(school => school.name === (parent || name));
      if (!directData && !item) throw new Error('School not found');
      const raw = directData || await fetchSchoolJSON('/schools/data/' + item.detailFile, controller.signal);
      if (!raw?.name || typeof raw.overview !== 'string') throw new Error('Invalid school data');
      if (!controller.signal.aborted) {
        setLoaded({ data: normalizeSchool(raw), catalog, image: item?.image || direct?.bg?.replace(/^url\(|\)$/g, ''), branch: parent ? name : null });
        setError(false);
      }
    }
    load().catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [name, retry]);

  useEffect(() => {
    if (loaded?.branch) requestAnimationFrame(() => goToSection('school-branches'));
  }, [loaded?.branch]);

  // 深链定位：/school/:name#school-quotes 等锚点在资料载入后自动滚动（星图节点跳转依赖此行为）
  useEffect(() => {
    if (!loaded) return;
    const hash = location.hash?.slice(1);
    if (hash && document.getElementById(hash)) {
      const timer = setTimeout(() => goToSection(hash), 60);
      return () => clearTimeout(timer);
    }
  }, [loaded, location.hash]);

  if (error) return <div className="school-detail school-status"><h1>{name}</h1><p>暂时无法载入这一流派的资料。</p><button type="button" onClick={() => { setError(false); setRetry(value => value + 1); }}>重新载入</button><Link to="/genealogy">返回谱系 →</Link></div>;
  if (!data) return <div className="school-detail school-status" role="status"><p className="school-kicker">DEEP PHILOSOPHY</p><h1>{name}</h1><p>正在载入流派资料…</p></div>;

  function openPerson(person) { setSelectedPerson(person); goToSection('school-graph'); }
  function openConcept(concept) { setSelectedConcept(concept); setConceptRequest(value => value + 1); goToSection('school-concepts'); }
  function locatePerson(person) {
    const event = [...document.querySelectorAll('#school-timeline [data-person]')].find(node => node.dataset.person === person);
    if (event) event.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' });
    else goToSection('school-timeline');
  }
  const chapters = [
    ['school-overview', '简介', true], ['school-branches', '子流派', data.subSchools.length], ['school-graph', '星图', data.thinkers.length || data.relations.length],
    ['school-timeline', '时间轴', data.timeline.length], ['school-concepts', '词海', data.cihai.length], ['school-quotes', '金句', data.quotes.length],
    ['school-works', '典籍', data.works.length], ['school-conclusion', '结语', data.conclusion],
  ].filter(([, , visible]) => visible);
  return <div className="school-detail">
    <HeroSection name={data.name} subtitle={data.subtitle} quote={data.quote} quoteAuthor={data.quoteAuthor} quoteKind={data.quoteKind} heroImage={loaded.image} englishName={ENG_NAMES[data.name]} />
    <div className="school-reading" id="school-content">
      <nav className="school-chapter-nav" aria-label="流派章节">{chapters.map(([id, label], index) => <a key={id} href={`#${id}`} onClick={event => { event.preventDefault(); goToSection(id); }}><small>{['I','II','III','IV','V','VI','VII','VIII'][index]}</small>{label}</a>)}</nav>
      {loaded.branch && <p className="school-branch-context">正在{data.name}中阅读“{loaded.branch}”。<Link to={`/school/${encodeURIComponent(data.name)}`}>查看所属流派</Link></p>}
      <OverviewSection overview={data.overview} />
      <SubSchoolsSection key={loaded.branch || data.name} schoolName={data.name} subSchools={data.subSchools} thinkers={data.thinkers} cihai={data.cihai} references={references} initialBranch={loaded.branch} onSelectPerson={openPerson} onSelectConcept={openConcept} />
      <div id="school-graph" className="school-module-anchor"><ConstellationMap thinkers={data.thinkers} relations={data.relations} cihai={data.cihai} references={references} selectedPerson={selectedPerson || data.thinkers[0]?.name} onSelectPerson={setSelectedPerson} onSelectConcept={openConcept} onLocatePerson={locatePerson} /></div>
      <div id="school-timeline" className="school-module-anchor"><TimelineSection timeline={data.timeline} thinkers={data.thinkers} cihai={data.cihai} references={references} onSelectPerson={openPerson} onSelectConcept={openConcept} /></div>
      <div id="school-concepts" className="school-module-anchor"><GlossaryCloud key={conceptRequest} cihai={data.cihai} references={references} selectedConcept={selectedConcept} onSelectConcept={setSelectedConcept} /></div>
      <div id="school-quotes" className="school-module-anchor"><QuotesGallery quotes={data.quotes} /></div>
      <WorksList works={data.works} references={references} />
      <EpilogueSection conclusion={data.conclusion} closingQuote={data.closingQuote} closingQuoteAuthor={data.closingQuoteAuthor} closingQuoteKind={data.closingQuoteKind} image={loaded.image} />
      {data.sources.length > 0 && <section className="school-sources" aria-labelledby="school-sources-title"><h2 id="school-sources-title">参考资料</h2><ul>{data.sources.map((source, i) => <li key={`${source.url}-${i}`}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗</a></li>)}</ul></section>}
      <footer className="school-footer"><span>DeepPhilosophy</span><Link to="/genealogy">继续探索思想谱系 →</Link></footer>
    </div>
  </div>;
}
