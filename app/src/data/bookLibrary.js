/** Library facets describe works, not author membership. Preserve all source tags. */
const facet = (id, label, tags) => ({ id, label, tags: tags.split('|') });
export const BOOK_TOPICS = [
  facet('life','存在与人生','存在主义|生存哲学|存在哲学|荒诞哲学|荒谬哲学|荒诞|虚无主义|生命哲学|悲观主义|人生哲学|生活哲学|生活智慧|人生智慧|幸福哲学|幸福论|幸福|人生意义|生命意义|死亡哲学|命运哲学|自由意志|修身养性|修身实践|处世智慧|正念|哲学实践|行走哲学|意义治疗|心灵成长|生活指导|人生|当下体验|生活'),
  facet('ethics','伦理与政治','伦理学|伦理|道德哲学|道德心理学|道德基础|德性伦理|德性伦理学|元伦理学|政治哲学|政治神学|法哲学|法学哲学|自由主义|社群主义|女性主义|女权主义|功利主义|后果主义|正义理论|分配正义|社会契约|社会契约论|民主理论|极权主义|共和主义|国家理论|三权分立|个人自由|自然法传统|古典政治哲学|军事哲学|战略思想|兵法|仁政|修身养性|道德批判'),
  facet('knowledge','知识与语言','认识论|知识论|语言哲学|逻辑哲学|逻辑学|逻辑|逻辑主义|经验主义|经验论|英国经验论|理性主义|怀疑论|分析哲学|言语行为理论|符号学|修辞学|心灵哲学|意识哲学|意识分析|意向性理论|认知哲学|认知科学|思维方法|思维训练|批判性思维|思维谬误|社会认识论|方法论|知觉哲学|现象学|数学哲学'),
  facet('being','存在与自然','形而上学|本体论|自然哲学|宇宙论|宇宙观|泛神论|唯心主义|唯心论|先验唯心论|唯物主义|人本学唯物主义|辩证唯物主义|过程哲学|机体哲学|阴阳五行|身心关系|时间哲学|绝对同一性|自然主义'),
  facet('faith','宗教与信仰','宗教哲学|神学|基督教哲学|教父哲学|经院哲学|佛学|佛教|佛教哲学|禅宗|神秘主义|宗教批判|无神论|宗教宽容|理性与信仰|灵性|宗教社会学'),
  facet('society','社会与文化','社会哲学|社会学|社会学哲学|社会心理学|历史哲学|历史唯物主义|政治经济学|古典经济学|马克思主义|马克思主义哲学|西方马克思主义|批判理论|法兰克福学派|文化批判|文化哲学|文化研究|现代性|现代性批判|社会批判|社会批判理论|人类学|人类学哲学|形式社会学|知识社会学|跨文化|跨文化哲学|比较哲学|中西比较|东西方哲学|大众心理学|群体心理学|精神分析|精神分析学|分析心理学|教育哲学|教育|儿童哲学'),
  facet('science','科学与技术','科学哲学|科学史|技术哲学|媒介哲学|媒介批判|数字时代|传播学|大众传媒|电视文化|技术理性批判|认知科学|神经科学|进化论|进化论哲学|进化心理学|实证主义|逻辑实证主义|批判理性主义|证伪主义|范式理论|认识论无政府主义|决策科学'),
  facet('art','艺术与审美','美学|文学哲学|文学与哲学|文学理论|古典文论|文学批评|文学|法国文学|俄国文学|现代主义|哲学小说|小说|电影|浪漫主义|修辞学|笔记小说|讽刺哲学'),
  facet('history','哲学史与导论','哲学史|思想史|西方哲学史|哲学通史|通史|哲学导论|哲学入门|入门读物|入门|通识|通识教育|通识读物|百科全书|辞典|工具书|西方现代哲学|思想启蒙'),
];
export const BOOK_TRADITIONS = [
  facet('confucian','儒家','儒家|儒家思想'),facet('neo-confucian','宋明理学与心学','宋明理学|心学'),facet('new-confucian','现代新儒家','新儒家|现代新儒家'),facet('daoist','道家','道家|道家哲学'),facet('buddhist','佛教思想','佛学|佛教|佛教哲学|禅宗'),facet('legalist','法家','法家'),
  facet('platonist','柏拉图主义','柏拉图主义|新柏拉图主义'),facet('stoic','斯多葛学派','斯多葛学派|斯多葛主义|斯多葛'),facet('epicurean','伊壁鸠鲁学派','伊壁鸠鲁学派'),facet('cynic','犬儒学派','犬儒学派'),facet('skeptic','怀疑论','怀疑论'),facet('christian','基督教哲学','基督教哲学|教父哲学|经院哲学'),
  facet('rationalist','理性主义','理性主义'),facet('empiricist','经验主义','经验主义|经验论|英国经验论'),facet('idealism','德国古典哲学','德国古典哲学|德国唯心论'),facet('phenomenology','现象学','现象学|知觉现象学'),facet('existential','存在主义','存在主义|存在哲学|生存哲学'),facet('absurd','荒诞哲学','荒诞哲学|荒谬哲学'),facet('analytic','分析哲学','分析哲学|后分析哲学'),facet('pragmatist','实用主义','实用主义|新实用主义'),
  facet('marxist','马克思主义','马克思主义|马克思主义哲学'),facet('western-marxist','西方马克思主义','西方马克思主义'),facet('critical','批判理论','批判理论|法兰克福学派'),facet('psychoanalytic','精神分析','精神分析|精神分析学|精神分析哲学|分析心理学'),facet('structural','结构主义','结构主义'),facet('poststructural','后结构主义与解构','后结构主义|解构主义'),facet('hermeneutic','诠释学','诠释学|解释学|哲学诠释学'),facet('feminist','女性主义','女性主义|女权主义'),facet('utilitarian','功利主义','功利主义'),facet('liberal','自由主义','自由主义'),facet('communitarian','社群主义','社群主义'),facet('positivist','实证主义','实证主义|逻辑实证主义'),facet('process','过程哲学','过程哲学'),facet('transcendental','超验主义','超验主义'),
];
export const BOOK_FORMS = [
  {id:'intro',label:'入门与通识',tags:['入门','哲学入门','哲学导论','通识','通识教育','通识读物','入门读物','教材','公开课','通俗哲学','趣味哲学','图解'],title:/哲学[课小]|哲学导论|哲学入门|讲义|十二讲|二十一讲|给青年人|第一本哲学书|哲学100问/},
  {id:'history',label:'哲学史',tags:['哲学史','西方哲学史','思想史','通史','哲学通史'],title:/哲学.*史|佛教史|思想简史/},
  {id:'collection',label:'全集与选集',tags:['全集','全集/选集'],title:/全集|文集|作品集|著作集|套装|合集|选集|文选/},
  {id:'commentary',label:'注释与研究',tags:['经典注译','经典注释','注释','经典解读','解读'],title:/注释|今注今译|句读|释义|导读|解读|集注/},
  {id:'biography',label:'传记与回忆',tags:['传记','思想传记','自传'],title:/传：|传$|忏悔录|回忆录/},
  {id:'dialogue',label:'对话与书信',tags:['对话','对话录','对话体','访谈'],title:/对话|谈话录|书简|书信|通信|访谈|对谈/},
  {id:'essay',label:'随笔与格言',tags:['哲学随笔','格言','对话/语录'],title:/随笔|语录|手记|札记|沉思录|思想录|论语|单行道|散文|菜根谭|呻吟语/},
  {id:'literature',label:'文学作品',tags:['哲学小说','笔记小说','小说'],title:/罪与罚|卡拉马佐夫|地下室手记|局外人|鼠疫|城堡|变形记|悉达多|戏剧卷|小说卷|苏菲的世界|当尼采哭泣|世界尽头的咖啡馆|老实人|天真汉|查第格|狄俄尼索斯颂歌/},
  {id:'reference',label:'辞典与工具书',tags:['辞典','工具书','百科全书'],title:/辞典|词典|百科全书/},
  {id:'treatise',label:'专题著作',tags:['专著'],title:null},
  
];
export const BOOK_REGIONS=[{id:'east',label:'东方思想'},{id:'west',label:'西方思想'},{id:'cross',label:'跨文化与比较'},{id:'other',label:'其他范围'}];
const TOPIC_ADDITIONS = {
  "ea6f47b169f0": ["life", "being"],
  "c3c401982587": ["life", "being"],
  "309de54e4392": [
    "knowledge",
    "ethics",
    "art"
  ],
  "d54981640212": [
    "history",
    "ethics"
  ],
  "e74dc59d508e": [
    "being",
    "knowledge",
    "ethics"
  ],
  "35279e2e439d": [
    "being",
    "knowledge",
    "ethics"
  ],
  "6ef2f18cfdc9": [
    "being",
    "life",
    "ethics"
  ],
  "dd8853676655": [
    "being",
    "life",
    "ethics"
  ],
  "10e1874c2255": [
    "knowledge",
    "ethics",
    "art"
  ],
  "bedc9c78dfdf": [
    "life",
    "ethics"
  ],
  "390398aff8d0": [
    "knowledge",
    "ethics",
    "art"
  ],
  "cba9d40254dc": [
    "history",
    "ethics"
  ],
  "178e7d06d42d": [
    "knowledge",
    "ethics"
  ],
  "960c47f35066": [
    "society",
    "ethics"
  ],
  "08e055841182": [
    "knowledge"
  ],
  "a2931a891bf9": [
    "faith",
    "life"
  ],
  "bbac1be0bb4b": [
    "being",
    "knowledge",
    "society"
  ],
  "60eed962806b": [
    "society",
    "ethics"
  ],
  "8eb18c6de2bc": [
    "society",
    "ethics"
  ],
  "909e887aac01": [
    "ethics",
    "life"
  ],
  "5ed9d54539e1": [
    "society"
  ],
  "9efee732eaff": [
    "knowledge"
  ],
  "87bfe5b27ca1": [
    "society",
    "knowledge"
  ],
  "5bd87e283d16": [
    "being",
    "society"
  ],
  "9dc98919ade8": [
    "faith",
    "life"
  ],
  "95dc5ef91f2c": [
    "knowledge",
    "society"
  ],
  "88dc7d5961df": [
    "history",
    "society"
  ],
  "e2845fe17764": [
    "being",
    "life"
  ],
  "39cd5aab287c": [
    "knowledge",
    "art"
  ],
  "301890458a11": [
    "art",
    "knowledge"
  ],
  "00fadd7de47c": [
    "history",
    "life"
  ],
  "29b3de571c12": [
    "art",
    "life"
  ],
  "cd1c72bf7f81": [
    "art"
  ],
  "f8d52df0f555": [
    "history"
  ],
  "3138fe5c9f12": [
    "society"
  ],
  "dcead00ff195": [
    "society",
    "ethics"
  ],
  "30f6adc65ee2": [
    "knowledge"
  ],
  "e6c890fcd84e": [
    "knowledge"
  ],
  "a10a36861e51": [
    "knowledge",
    "history"
  ],
  "81548bf7104f": [
    "knowledge"
  ],
  "d0c5ade4fcbd": [
    "being",
    "life"
  ],
  "4c5aaf145298": [
    "ethics",
    "life"
  ],
  "02b0e5227f7b": [
    "being"
  ],
  "d8bcc10d42ff": [
    "knowledge",
    "being"
  ],
  "219b862077e1": [
    "history",
    "faith"
  ],
  "1f6fe151032b": [
    "ethics"
  ],
  "55591ecdf7e9": [
    "science",
    "knowledge"
  ],
  "d0e4041355ed": [
    "history",
    "knowledge"
  ],
  "921c1dcbdd17": [
    "life"
  ],
  "d3f79625368c": [
    "ethics",
    "life"
  ],
  "4a7829907f07": [
    "history",
    "knowledge"
  ],
  "b7959caca36d": [
    "ethics",
    "life"
  ],
  "e863b4cca50d": [
    "life",
    "ethics"
  ]
};
const matching=(definitions,tags)=>definitions.filter(f=>f.tags.some(t=>tags.includes(t))).map(f=>f.id);
export function classifyBook(book){
  const tags=(book.tags||[]).filter(t=>typeof t==='string');
  let topics=[...new Set([...matching(BOOK_TOPICS,tags),...(TOPIC_ADDITIONS[book.id]||[])])],traditions=matching(BOOK_TRADITIONS,tags);
  if (book.id === 'e1fabd8e802c') topics = ['being','faith']; // 阿奎那《论存在者与本质》并非存在主义作品。
  const forms=BOOK_FORMS.filter(f=>f.tags.some(t=>tags.includes(t))||f.title?.test(book.title||'')).map(f=>f.id);
  if (/最伟大的思想家|牛津通识读本/.test(book.title||'') || book.id === 'd54981640212') forms.push('intro');
  if (book.id === 'e1fabd8e802c') { traditions.splice(0,traditions.length,'christian'); }
  const regions=[book.region==='东方'?'east':book.region==='西方'?'west':'other'];
  if(tags.some(t=>['比较哲学','中西比较','跨文化','跨文化哲学','东西方哲学'].includes(t)))regions.push('cross');
  return {topics,traditions,forms:forms.length?[...new Set(forms)]:['treatise'],regions,readable:Number(book.chapterCount)>0&&book.file_type!=='txt'};
}
export function prepareLibrary(books){return books.map(book=>({...book,facets:classifyBook(book),searchText:[book.title,book.author,...(book.tags||[])].join(' ').normalize('NFKC').toLocaleLowerCase()}));}
export function filterLibrary(books,f={}){const q=(f.q||'').normalize('NFKC').toLocaleLowerCase().trim();return books.filter(b=>(!q||b.searchText.includes(q))&&(!f.topic||b.facets.topics.includes(f.topic))&&(!f.tradition||b.facets.traditions.includes(f.tradition))&&(!f.region||b.facets.regions.includes(f.region))&&(!f.form||b.facets.forms.includes(f.form))&&(!f.readable||b.facets.readable));}
export function sortLibrary(books,order='curated'){return [...books].sort((a,b)=>order==='title'?a.title.localeCompare(b.title,'zh-CN'):order==='author'?a.author.localeCompare(b.author,'zh-CN')||a.title.localeCompare(b.title,'zh-CN'):(b.rank||0)-(a.rank||0)||a.title.localeCompare(b.title,'zh-CN'));}
