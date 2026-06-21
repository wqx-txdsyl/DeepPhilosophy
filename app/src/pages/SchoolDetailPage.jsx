/**
 * 流派详情页 — 滚轮下翻式，5面内容
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';

// ——— 古希腊哲学硬编码数据 ———
const GREEK_DATA = {
  name: '古希腊哲学',
  quote: '"认识你自己。"',
  quoteAuthor: '苏格拉底',
  subtitle: '西方哲学的总源，理性精神的第一次觉醒',
  overview: `古希腊哲学是西方哲学的源头，始于公元前6世纪的米利都学派，终于公元6世纪雅典学园的关闭。它以理性思辨取代神话解释，首次追问万物的本原（arche）、存在的本质与善的生活。

其核心命题贯穿千年：泰勒斯以"水"开启自然哲学；赫拉克利特与巴门尼德在流变与永恒之间开辟辩证传统；苏格拉底将哲学从天上拉回人间，以对话探寻德性与真理；柏拉图以理念论构建理性王国；亚里士多德以经验与逻辑奠定科学基石。晚期希腊哲学中，伊壁鸠鲁学派、斯多葛学派与怀疑论三足鼎立，将哲学转化为生活的技艺与心灵的救助。

古希腊哲学下属主要流派：米利都学派、埃利亚学派、原子论、智者学派、柏拉图学派（学园派）、亚里士多德学派（逍遥学派）、伊壁鸠鲁学派、斯多葛学派、怀疑论（皮浪主义）、犬儒学派、新柏拉图主义。`,

  thinkers: [
    { name:'泰勒斯', sub:'米利都学派', era:'约前624-前546', influence:8, key:'水是万物的本原', works:['论自然[已佚失]'] },
    { name:'阿那克西曼德', sub:'米利都学派', era:'约前610-前546', influence:7, key:'无定者（apeiron）', works:['论自然[已佚失]'] },
    { name:'阿那克西美尼', sub:'米利都学派', era:'约前585-前525', influence:6, key:'气为本原', works:['论自然[已佚失]'] },
    { name:'赫拉克利特', sub:'前苏格拉底', era:'约前535-前475', influence:9, key:'万物皆流，逻各斯', works:['论自然[残篇]'] },
    { name:'巴门尼德', sub:'埃利亚学派', era:'约前515-前450', influence:9, key:'存在者存在', works:['论自然[残篇]'] },
    { name:'恩培多克勒', sub:'多元论', era:'约前490-前430', influence:7, key:'四根说', works:['论自然[残篇]','净化篇[残篇]'] },
    { name:'苏格拉底', sub:'古希腊哲学', era:'约前470-前399', influence:10, key:'认识你自己', works:['柏拉图对话集'] },
    { name:'柏拉图', sub:'柏拉图学派', era:'约前427-前347', influence:10, key:'理念论', works:['理想国','柏拉图对话集'] },
    { name:'第欧根尼', sub:'犬儒学派', era:'约前412-前323', influence:6, key:'回归自然', works:['共和国[残篇]'] },
    { name:'亚里士多德', sub:'逍遥学派', era:'前384-前322', influence:10, key:'实体与范畴', works:['形而上学','尼各马可伦理学','政治学','工具论'] },
    { name:'皮浪', sub:'怀疑论', era:'约前360-前270', influence:7, key:'悬搁判断', works:['皮浪学说概要'] },
    { name:'伊壁鸠鲁', sub:'伊壁鸠鲁学派', era:'前341-前270', influence:8, key:'快乐即至善', works:['论自然','准则学','快乐主义'] },
    { name:'西塞罗', sub:'斯多葛学派', era:'前106-前43', influence:7, key:'自然法与德性', works:['论义务','论共和国','论法律'] },
    { name:'爱比克泰德', sub:'斯多葛学派', era:'约55-135', influence:8, key:'可控与不可控', works:['哲学谈话录','手册','论说集'] },
    { name:'马可·奥勒留', sub:'斯多葛学派', era:'121-180', influence:8, key:'顺应自然', works:['沉思录'] },
    { name:'普罗提诺', sub:'新柏拉图主义', era:'204-270', influence:8, key:'太一流溢说', works:['九章集'] },
  ],

  relations: [
    { from:'泰勒斯', to:'阿那克西曼德', type:'师生' },
    { from:'阿那克西曼德', to:'阿那克西美尼', type:'师生' },
    { from:'赫拉克利特', to:'巴门尼德', type:'对立' },
    { from:'巴门尼德', to:'恩培多克勒', type:'影响' },
    { from:'苏格拉底', to:'柏拉图', type:'师生' },
    { from:'柏拉图', to:'亚里士多德', type:'师生' },
    { from:'苏格拉底', to:'第欧根尼', type:'影响' },
    { from:'柏拉图', to:'普罗提诺', type:'继承' },
    { from:'亚里士多德', to:'伊壁鸠鲁', type:'对立' },
    { from:'伊壁鸠鲁', to:'西塞罗', type:'对立' },
    { from:'西塞罗', to:'爱比克泰德', type:'继承' },
    { from:'爱比克泰德', to:'马可·奥勒留', type:'影响' },
    { from:'皮浪', to:'伊壁鸠鲁', type:'对立' },
    { from:'皮浪', to:'西塞罗', type:'影响' },
  ],

  timeline: [
    { year:'约前624', event:'泰勒斯出生', detail:'米利都学派创始人，西方哲学之父', type:'birth' },
    { year:'约前585', event:'泰勒斯预言日食', detail:'以理性解释自然现象，标志神话思维的终结', type:'event' },
    { year:'约前546', event:'泰勒斯逝世', detail:'米利都学派由阿那克西曼德继承发展', type:'death' },
    { year:'约前500', event:'赫拉克利特提出"逻各斯"', detail:'万物皆流，对立统一，逻各斯即宇宙理性法则', type:'idea' },
    { year:'约前480', event:'巴门尼德著《论自然》', detail:'首次提出"存在"概念，区分真理之路与意见之路', type:'book' },
    { year:'约前399', event:'苏格拉底被判死刑', detail:'以"不义之生不如死"的从容赴死，成为哲学殉道者', type:'death' },
    { year:'约前387', event:'柏拉图创立雅典学园', detail:'西方第一所高等学府，门口刻有"不懂几何者不得入内"', type:'event' },
    { year:'约前380', event:'柏拉图著《理想国》', detail:'构建理念论体系，描绘哲人王的理想城邦蓝图', type:'book' },
    { year:'约前335', event:'亚里士多德创立吕克昂学园', detail:'逍遥学派诞生，经验观察与逻辑分类并重', type:'event' },
    { year:'约前330', event:'亚里士多德著《形而上学》', detail:'奠定实体论、四因说、范畴论，系统化古希腊哲学成就', type:'book' },
    { year:'约前306', event:'伊壁鸠鲁创立"花园"学派', detail:'以追求心灵宁静为至善，最早接纳女性和奴隶', type:'event' },
    { year:'约前300', event:'斯多葛学派创立', detail:'芝诺在雅典画廊讲学，以顺应自然为德性核心', type:'event' },
    { year:'约前270', event:'伊壁鸠鲁逝世', detail:'享乐主义伦理学影响罗马，原子论思想影响近代科学', type:'death' },
    { year:'约前155', event:'雅典三哲使团访罗马', detail:'学院派、斯多葛派、逍遥派代表将希腊哲学引入罗马', type:'event' },
    { year:'135', event:'爱比克泰德逝世', detail:'奴隶出身的斯多葛哲人，教导"可控与不可控"的智慧', type:'death' },
    { year:'180', event:'马可·奥勒留逝世', detail:'最后一位斯多葛贤君，《沉思录》成为古典哲学绝唱', type:'death' },
    { year:'270', event:'普罗提诺逝世', detail:'新柏拉图主义完成对古希腊哲学的总结与神秘化升华', type:'death' },
    { year:'529', event:'雅典学园被关闭', detail:'查士丁尼大帝禁绝异教哲学，古希腊千年传统就此终结', type:'event' },
  ],

  conclusion: `古希腊哲学是西方思想永不枯竭的源泉。从米利都的星空到雅典的广场，从对"万物本原"的朴素追问到对"善的生活"的精微思辨，这千年旅程塑造了理性、自由与德性这三个西方文明最核心的价值。

每一个后继时代都不断回到古希腊——中世纪在亚里士多德身上找到神学的架构，文艺复兴在柏拉图身上找到人文的光辉，启蒙时代在斯多葛身上找到自由的锚点。正如怀特海所言，整个西方哲学不过是"对柏拉图的一系列脚注"。

古希腊哲学教导我们：哲学不是书本上的学问，而是生活的方式——是苏格拉底在审判席上的从容，是第欧根尼对亚历山大大帝说的"请别挡住我的阳光"，是爱比克泰德在锁链中写下的"人不是被事物所困扰，而是被对事物的看法所困扰"。`,
  closingQuote: '"令我们不安的不是现实，而是我们对现实的看法。 — 爱比克泰德',
};



const SUB_SCHOOL_DATA = {};

// Sub-schools will show filtered Greek thinkers
const PATRISTIC_DATA = {
  name: "教父哲学",
  quote: "信仰寻求理解。",
  quoteAuthor: "奥古斯丁",
  subtitle: "以希腊理性为基督教信仰奠基的第一座神学大厦",
  overview: `教父哲学（Patristic Philosophy）是公元2至8世纪基督教神学家（教父们）以希腊哲学为工具系统阐述基督教教义的哲学运动。它横跨希腊与拉丁两大传统，历经护教时期、亚历山大里亚学派、卡帕多西亚三杰和拉丁教父的黄金时代，将柏拉图主义、斯多葛主义和新柏拉图主义的哲学概念引入神学，为三位一体、道成肉身、自由意志与恩典、原罪与救赎等核心教义提供了形而上学基础。

希腊教父以亚历山大里亚学派为中心。查士丁（殉道者查士丁）首次以"逻各斯"概念诠释基督——基督即希腊哲学所追寻的终极逻各斯的道成肉身，开创了"基督教哲学"的传统。伊里奈乌以"同归于一"（recapitulation）教义驳斥诺斯替主义——基督作为新亚当，将人类全部生命阶段重新"总结"在祂的顺服之中。克莱门特主张"哲学是希腊人通向基督的训蒙师"，将希腊哲学定位为基督教信仰的预备课程。奥里根以新柏拉图主义构建了第一个系统化的基督教神学体系，其寓意解经法和"永恒出生"概念影响了后世所有教父。阿塔纳修在尼西亚公会议中捍卫"本质同一"（homoousios），其"上帝成为人，为使人成为神"成为东方神学的经典表述。

卡帕多西亚三杰——巴西尔、纳西盎的格列高利与尼撒的格列高利——代表希腊教父的巅峰。他们以精微的哲学辨析区分了ousia（本质）与hypostasis（位格），为三位一体教义奠定了不可动摇的术语基础。纳西盎的格列高利开创否定神学进路，尼撒的格列高利以灵魂论与自由意志论被后世称为"教父中的教父"。

拉丁教父更关注人的罪、恩典与救赎。德尔图良以"雅典与耶路撒冷有何相干？"质疑哲学对信仰的侵蚀，却发明了"三位一体"（trinitas）和"位格"（persona）等拉丁神学术语，为西方神学语言奠基。安布罗斯将斯多葛伦理学转化为基督教道德体系，其讲道直接促成了奥古斯丁的皈依。哲罗姆以"武加大译本"（Vulgate）为拉丁西方提供了统一的圣经文本。奥古斯丁站在所有这些传统的交汇点上，以柏拉图主义和新柏拉图主义为框架，在《忏悔录》《上帝之城》《论三位一体》中建立了统治西方神学千年的体系——原罪、恩典、自由意志、历史神学、两城说，无一不经由他而成为西方思想的基石。`,
  thinkers: [
    { name:"查士丁（殉道者）", sub:"希腊教父", era:"约100-165", influence:8, key:"基督即逻各斯", works:["护教篇","与特里丰对话录"] },
    { name:"伊里奈乌", sub:"希腊教父", era:"约125-202", influence:8, key:"同归于一（recapitulation）", works:["反异端论","使徒讲道明证"] },
    { name:"克莱门特", sub:"希腊教父", era:"约150-215", influence:7, key:"哲学是训蒙师", works:["杂缀集","劝勉希腊人","导师基督"] },
    { name:"奥里根", sub:"希腊教父", era:"185-254", influence:9, key:"第一个系统神学", works:["论第一原理","驳凯尔苏斯","六文本合参"] },
    { name:"阿塔纳修", sub:"希腊教父", era:"约296-373", influence:9, key:"上帝成为人，为使人成为神", works:["论道成肉身","反阿里乌派演讲"] },
    { name:"巴西尔", sub:"卡帕多西亚教父", era:"约330-379", influence:8, key:"ousia与hypostasis的区分", works:["论圣灵","驳尤诺米","隐修规则"] },
    { name:"纳西盎的格列高利", sub:"卡帕多西亚教父", era:"约329-390", influence:8, key:"否定神学", works:["神学演讲","诗篇"] },
    { name:"尼撒的格列高利", sub:"卡帕多西亚教父", era:"约335-395", influence:9, key:"灵魂论与自由意志", works:["论灵魂与复活","大教理问答","论人的造成"] },
    { name:"德尔图良", sub:"拉丁教父", era:"约160-225", influence:8, key:"惟其不可能我才相信", works:["护教篇","论灵魂","驳帕克西亚"] },
    { name:"安布罗斯", sub:"拉丁教父", era:"约339-397", influence:8, key:"基督教伦理学奠基", works:["论神职人员的职责","论信仰","论圣灵"] },
    { name:"哲罗姆", sub:"拉丁教父", era:"约347-420", influence:7, key:"武加大译本", works:["武加大译本","名人传","书信集"] },
    { name:"奥古斯丁", sub:"拉丁教父", era:"354-430", influence:10, key:"信仰寻求理解", works:["忏悔录","上帝之城","论三位一体","论自由意志"] },
  ],
  relations: [
    { from:"查士丁（殉道者）", to:"伊里奈乌", type:"影响" },
    { from:"伊里奈乌", to:"克莱门特", type:"影响" },
    { from:"克莱门特", to:"奥里根", type:"师生" },
    { from:"奥里根", to:"阿塔纳修", type:"影响" },
    { from:"奥里根", to:"巴西尔", type:"影响" },
    { from:"阿塔纳修", to:"巴西尔", type:"继承" },
    { from:"巴西尔", to:"纳西盎的格列高利", type:"友谊" },
    { from:"巴西尔", to:"尼撒的格列高利", type:"师生" },
    { from:"克莱门特", to:"德尔图良", type:"对立" },
    { from:"德尔图良", to:"奥古斯丁", type:"影响" },
    { from:"安布罗斯", to:"奥古斯丁", type:"师生" },
    { from:"哲罗姆", to:"奥古斯丁", type:"对话" },
    { from:"奥里根", to:"奥古斯丁", type:"影响" },
  ],
  timeline: [
    { year:"约150", event:"查士丁著《护教篇》", detail:"首次以希腊哲学为基督教辩护，提出基督即逻各斯的道成肉身，开创基督教哲学传统", type:"book" },
    { year:"约165", event:"查士丁在罗马殉道", detail:"因拒绝向罗马神祇献祭被斩首，以哲学家的身份为信仰献出生命", type:"death" },
    { year:"约180", event:"伊里奈乌著《反异端论》", detail:"系统驳斥诺斯替主义，提出'同归于一'教义——基督作为新亚当总结人类全部历史", type:"book" },
    { year:"约190", event:"克莱门特执掌亚历山大里亚教理学校", detail:"将希腊哲学定位为'训蒙师'，构建以神学为顶的知识金字塔", type:"event" },
    { year:"约200", event:"德尔图良活跃于迦太基", detail:"发明trinitas（三位一体）、persona（位格）等拉丁术语，奠定西方神学语言", type:"event" },
    { year:"约220", event:"奥里根著《论第一原理》", detail:"以新柏拉图主义构建第一个基督教系统神学——上帝、宇宙、自由意志与灵魂回归", type:"book" },
    { year:"254", event:"奥里根在迫害中逝世", detail:"德西乌斯迫害中被捕受酷刑，几年后伤重不治，其思想影响却刚刚开始", type:"death" },
    { year:"325", event:"尼西亚公会议召开", detail:"阿塔纳修作为执事参与，确立homoousios（本质同一）——子与父同质而非受造", type:"event" },
    { year:"约328", event:"阿塔纳修著《论道成肉身》", detail:"'上帝成为人，为使人成为神'——道成肉身作为神化（theosis）的根基", type:"book" },
    { year:"约370", event:"巴西尔著《论圣灵》", detail:"明确区分ousia（本质）与hypostasis（位格），为三一神学奠定精确术语", type:"book" },
    { year:"约380", event:"纳西盎的格列高利著《神学演讲》", detail:"以否定神学进路捍卫三位一体——上帝的本质不可知，唯有在道成肉身中启示", type:"book" },
    { year:"374", event:"安布罗斯成为米兰主教", detail:"由未受洗的罗马总督到主教仅8天，以行政才能与希腊学问服务于拉丁教会", type:"event" },
    { year:"386", event:"奥古斯丁在米兰花园皈依", detail:"在安布罗斯讲道与普罗提诺著作双重影响下，从摩尼教徒转向基督教", type:"event" },
    { year:"约391", event:"安布罗斯著《论神职人员的职责》", detail:"以斯多葛伦理学为框架，建立第一个系统的基督教道德神学体系", type:"book" },
    { year:"397", event:"奥古斯丁著《忏悔录》", detail:"西方第一部自传体哲学著作，在时间与永恒、记忆与自我之间追问灵魂的归宿", type:"book" },
    { year:"约405", event:"哲罗姆完成武加大译本", detail:"以希伯来原文为基础重译拉丁圣经，此后千年成为西方教会唯一权威文本", type:"book" },
    { year:"413", event:"奥古斯丁著《上帝之城》", detail:"罗马陷落后为基督教辩护——区分地上之城与上帝之城，开创基督教历史哲学", type:"book" },
    { year:"430", event:"奥古斯丁逝世", detail:"汪达尔人围攻希波城之际，教父哲学黄金时代终结，中世纪千年神学的大门随之打开", type:"death" },
  ],
  conclusion: `教父哲学是希腊智慧与基督信仰之间最深刻的一次相遇。从查士丁在罗马以哲学家身份为基督教辩护，到伊里奈乌以"同归于一"驳斥诺斯替的宇宙神话；从奥里根以新柏拉图主义构建第一个神学大全，到阿塔纳修以一生五次流放捍卫"本质同一"；从卡帕多西亚三杰以ousia与hypostasis的精微辨析为三一神学立定范式，到德尔图良以悖论式的激情发明拉丁神学的全部基本语汇——这些教父们以从希腊哲学中继承的全部概念工具，去追问那些无法被任何哲学完全容纳的奥秘：三位一体、道成肉身、恩典与自由。

他们有时失败——奥里根因过于柏拉图化而被后世谴责，德尔图良因过于反哲学而被哲学遗忘。但他们共同完成了西方思想史上最壮丽的事业之一：将耶路撒冷的信仰翻译为雅典的语言，从而让信仰成为可以思辨、可以追问、可以在理性中生长的活的思想。奥古斯丁站在这一传统的终点，以《忏悔录》的自我追问和《上帝之城》的历史神学，为古代世界画上句号，也为中世纪的千年神学打开大门。`,
  closingQuote: "我们的心灵永不安宁，直到在你之中得到安息。 — 奥古斯丁《忏悔录》",
};

const SUB_COLORS = {
  '米利都学派':'#C4956A','前苏格拉底':'#B8875E','埃利亚学派':'#AC7A52',
  '多元论':'#A06D46','古希腊哲学':'#94603A','柏拉图学派':'#88532E',
  '犬儒学派':'#7C4622','逍遥学派':'#703916','怀疑论':'#642C0A',
  '伊壁鸠鲁学派':'#6B3820','斯多葛学派':'#3A5A7C','新柏拉图主义':'#2E4A6A',
  '希腊教父':'#8B4513','卡帕多西亚教父':'#6A2E4A','拉丁教父':'#3A5A7C',
};

// —— 古希腊哲学下属流派卡片 ——
const GREEK_SUB_SCHOOLS = [
  { name:'米利都学派', era:'前6世纪', desc:'西方哲学的第一个学派，以自然哲学追问万物的物质本原（arche）。泰勒斯提出"水"，阿那克西曼德提出"无定者"，阿那克西美尼提出"气"，开创了以理性而非神话解释自然的传统。' },
  { name:'埃利亚学派', era:'前5世纪', desc:'巴门尼德及其追随者建立的思辨学派，首次区分"存在"与"非存在"，坚持"存在者存在，非存在者不存在"的逻辑原则。以严格的逻辑推理论证世界的永恒不变性，否定感官经验的有效性，奠定了西方形而上学的理性主义基础。' },
  { name:'智者学派', era:'前5世纪', desc:'以普罗泰戈拉和高尔吉亚为代表的职业教师群体，宣称"人是万物的尺度"，强调修辞术与辩论技巧，将哲学关注从自然哲学转向人与社会。他们对传统宗教与道德持怀疑态度，为希腊民主政治提供教育支撑。' },
  { name:'柏拉图学派（学园派）', era:'前4世纪-前1世纪', desc:'柏拉图于前387年创立的雅典学园延续约900年。以理念论为核心，主张真实世界是永恒不变的理念世界，可感世界只是其模仿。中期学园转向怀疑论，新学园派在批判斯多葛中发展。' },
  { name:'亚里士多德学派（逍遥学派）', era:'前4世纪-3世纪', desc:'亚里士多德在吕克昂学园边散步边讲学，故名"逍遥"。以经验观察与逻辑分析并重，构建了涵盖形而上学、物理学、伦理学、政治学、逻辑学的百科全书式体系。提出实体论、四因说与中庸之道。' },
  { name:'伊壁鸠鲁学派', era:'前4世纪-4世纪', desc:'伊壁鸠鲁在雅典的"花园"中创立，以追求心灵宁静（ataraxia）为人生至善。继承德谟克利特的原子论，认为诸神不干预人世，死亡是原子的消散无需恐惧。是最早接纳女性和奴隶的哲学共同体。' },
  { name:'斯多葛学派', era:'前3世纪-2世纪', desc:'芝诺在雅典画廊（stoa）创立，历经早期、中期、罗马时期三个阶段。主张顺应自然（逻各斯）生活，严格区分可控与不可控之事，强调内在德性是唯一真正的善。塞涅卡、爱比克泰德、马可·奥勒留为罗马斯多葛三杰。' },
  { name:'怀疑论（皮浪主义）', era:'前4世纪-3世纪', desc:'皮浪创立，主张对一切判断"悬搁"（epoche），认为任何命题都可以找到同等的反命题，因此应放弃追求确定知识，以达心灵宁静。影响了中期学园派，后通过恩披里柯的著作影响了近代哲学。' },
  { name:'犬儒学派', era:'前4世纪-5世纪', desc:'安提斯泰尼创立，第欧根尼为最著名代表。主张摒弃社会习俗与物质欲望，回归"自然"生活。第欧根尼以木桶为家，以极端简朴的行为挑战社会规范，其"世界公民"（kosmopolites）概念影响了斯多葛学派。' },
  { name:'新柏拉图主义', era:'3世纪-6世纪', desc:'普罗提诺在前3世纪整合柏拉图、亚里士多德与斯多葛思想，创立"太一流溢说"——太一派生出理智（Nous）、理智派生出灵魂（Psyche），灵魂下降为物质世界。人的使命是通过哲学沉思回归太一。深刻影响了早期基督教神学。' },
];

// —— 教父哲学下属流派卡片 ——
const PATRISTIC_SUB_SCHOOLS = [
  { name:'希腊教父', era:'2世纪-8世纪', desc:'以亚历山大里亚教理学校为中心，用希腊文写作，深受柏拉图和新柏拉图主义影响。注重三位一体的形而上学思辨、逻各斯基督论、以及理性与信仰关系的探讨。核心关切：上帝的本质是什么？逻各斯如何道成肉身？查士丁、克莱门特、奥里根、阿塔纳修为其代表。' },
  { name:'卡帕多西亚教父', era:'4世纪', desc:'希腊教父的巅峰，巴西尔、纳西盎的格列高利与尼撒的格列高利并称"卡帕多西亚三杰"。以精微的哲学辨析区分ousia（共同本质）与hypostasis（独立位格），为尼西亚三位一体正统奠定了不可动摇的术语基础。将灵修体验与哲学思辨深度融合，开创否定神学进路。' },
  { name:'拉丁教父', era:'2世纪-5世纪', desc:'以迦太基、米兰和希波为中心，用拉丁文写作，更受斯多葛学派和罗马法律精神影响。侧重人的罪、恩典与救赎、自由意志、教会权威与伦理实践。德尔图良发明了拉丁神学的基本语汇，安布罗斯建立基督教伦理学，奥古斯丁完成对整个古代哲学的基督教综合。' },
];

// —— 古希腊哲学辞海 ——
const GREEK_CIHAI = [
  { word:'Arche（本原）', def:'万物所从出又复归于它的终极元素或第一原理。泰勒斯以"水"、阿那克西曼德以"无定者"为 arche。', source:'亚里士多德《形而上学》卷一' },
  { word:'Logos（逻各斯）', def:'宇宙的理性法则与秩序。赫拉克利特首次以 logos 指称万物运行的内在规律，后为斯多葛学派发展为宇宙理性。', source:'赫拉克利特《论自然》残篇 DK22B1' },
  { word:'Eidos（理念/形式）', def:'柏拉图哲学核心概念，指超越可感世界的永恒不变的真正实在。具体事物因"分有"理念而存在，因"模仿"理念而有性质。', source:'柏拉图《理想国》卷六-卷七' },
  { word:'Aletheia（真理/无蔽）', def:'海德格尔追溯的古希腊原初真理概念。本意为"去蔽"或"无遮蔽状态"（a-lethe），指存在者从隐藏中显现出来的过程，而非后世命题与事实的符合。', source:'海德格尔《存在与时间》§44' },
  { word:'Ousia（实体）', def:'亚里士多德形而上学核心范畴，指"是其所是"的最根本存在。第一实体是个别具体事物，第二实体是种和属。', source:'亚里士多德《范畴篇》第5章' },
  { word:'Physis（自然/本性）', def:'万物按其自身本性的生长与显现。前苏格拉底哲学家以 physis 为研究对象，追问"按本性而论，事物究竟是什么"。', source:'亚里士多德《物理学》卷二' },
  { word:'Arete（德性/卓越）', def:'事物实现其本质功能的优秀品质。人的德性即灵魂合乎理性的活动。苏格拉底以"德性即知识"开启西方伦理学传统。', source:'亚里士多德《尼各马可伦理学》' },
  { word:'Eudaimonia（幸福/至善）', def:'古希腊伦理学的终极目标，不是主观的快乐感受，而是灵魂合乎完满德性的活动。亚里士多德称之为"灵魂合乎逻各斯的现实活动"。', source:'亚里士多德《尼各马可伦理学》卷一' },
  { word:'Ataraxia（心灵宁静）', def:'伊壁鸠鲁学派和怀疑论追求的最高境界：灵魂免于纷扰、身体免受痛苦的安宁状态。通过哲学理性消解对死亡和诸神的恐惧而获得。', source:'伊壁鸠鲁《致梅诺凯奥斯信》' },
  { word:'Apologia（申辩）', def:'苏格拉底在雅典法庭上的自我辩护。他不以乞求宽恕为策略，而是以"未经审视的人生不值得过"为哲学使命宣言，选择死亡而不放弃哲学。', source:'柏拉图《苏格拉底的申辩》' },
  { word:'四因说', def:'亚里士多德解释事物存在与变化的四种原因：质料因（由什么构成）、形式因（是什么）、动力因（谁使之运动）、目的因（为了什么）。', source:'亚里士多德《物理学》卷二·3' },
  { word:'中庸之道（Mesotes）', def:'亚里士多德伦理学的核心原则：德性是两种极端之间的中道。勇敢是鲁莽与怯懦的中道，慷慨是挥霍与吝啬的中道。', source:'亚里士多德《尼各马可伦理学》卷二' },
  { word:'认识你自己（Gnothi seauton）', def:'德尔斐神庙铭文，苏格拉底将其作为哲学第一原则。真正的智慧始于对自身无知的承认——"我只知道我一无所知"。', source:'柏拉图《苏格拉底的申辩》21d' },
  { word:'洞穴喻', def:'柏拉图《理想国》中的著名寓言。人类如同被锁在洞穴中的囚徒，只能看到墙上的影子（可感世界），哲学的任务是挣脱锁链、走出洞穴、看见太阳（理念/善）。', source:'柏拉图《理想国》卷七 514a-517a' },
  { word:'太一（To Hen）', def:'普罗提诺哲学中的最高本原，超越一切存在和思想，不可言说、不可界定。万物由太一通过"流溢"逐级派生：太一→理智→灵魂→物质世界。', source:'普罗提诺《九章集》卷五' },
  { word:'Demiurge（造物匠）', def:'柏拉图《蒂迈欧篇》中的神圣工匠，以理念为蓝本、以混沌物质为材料，创造了有序的宇宙。不是从无中创造（creatio ex nihilo），而是赋予原始混沌以秩序。', source:'柏拉图《蒂迈欧篇》28a-30c' },
  { word:'辩证法（Dialektike）', def:'柏拉图理解为"理念的科学"，即通过纯粹理性从假设上升到无假设的第一原理的能力。亚里士多德视之为从普遍接受的意见出发的推理方法。苏格拉底的"诘问法"是其雏形。', source:'柏拉图《理想国》卷六 511b' },
  { word:'自然法（Lex Naturalis）', def:'斯多葛学派认为宇宙由理性（Logos）支配，存在一种普遍的、永恒的、基于自然理性的法律。西塞罗将这一概念系统化：真正的法律是与自然相一致的正当理性。', source:'西塞罗《论共和国》卷三·22' },
  { word:'悬搁判断（Epoche）', def:'皮浪怀疑论的核心方法：对一切命题"既不肯定也不否定"，停止做出任何判断。目的是通过放弃对确定知识的追求而获得内心的宁静。', source:'塞克斯都·恩披里柯《皮浪学说概要》' },
  { word:'Maieutike（精神助产术）', def:'苏格拉底自称继承母亲助产士的职业，以问答法帮助对方"生出"心中已有的真理。承认无知（反讽）→提问诘难（驳斥）→引出真知（助产）。', source:'柏拉图《泰阿泰德篇》149a-151d' },
  { word:'万物皆流（Panta rhei）', def:'赫拉克利特名言："人不能两次踏入同一条河流"。强调宇宙万物的永恒变化与流动，同时在这流变背后存在不变的逻各斯。', source:'柏拉图《克拉底鲁篇》402a 引述' },
  { word:'人是万物的尺度', def:'智者普罗泰戈拉的名言，意为人（个体感知）是判断一切存在与不存在的标准。开创了西方相对主义和人文主义的先河。', source:'柏拉图《泰阿泰德篇》152a' },
  { word:'不义之生不如死', def:'苏格拉底在审判后的名言。当朋友提议越狱时，他拒绝逃跑——宁可承受不正义的死刑，也不做不正义的事。以生命为哲学殉道。', source:'柏拉图《克里同篇》' },
  { word:'Kosmos（宇宙/秩序）', def:'希腊人用 kosmos 指称有序、和谐的整体。前苏格拉底哲学家关注 kosmos 的物质构成，柏拉图用 demiurge 解释其秩序来源，斯多葛用 logos 贯穿宇宙。', source:'柯克&拉文《前苏格拉底哲学家》' },
  { word:'Dike（正义）', def:'起初指宇宙秩序的"方式"或"常规"，前苏格拉底哲学家将其自然化为宇宙法则。柏拉图在《理想国》中将正义定义为"各司其职"——灵魂三部分的和谐。', source:'柏拉图《理想国》卷四' },
  { word:'Aporia（疑难/困境）', def:'苏格拉底对话中，对话者常常陷入"不知如何前进"的困境。亚里士多德认为哲学始于 aporia——正是疑难推动思想前进。', source:'亚里士多德《形而上学》卷三' },
  { word:'Theoria（沉思/理论）', def:'古希腊哲学中最高的生活方式。不是为实用目的的知识，而是"为了知识本身"的纯粹沉思。亚里士多德称 theoria 是最接近神的生活。', source:'亚里士多德《尼各马可伦理学》卷十·7' },
  { word:'Prohairesis（选择/意愿）', def:'爱比克泰德斯多葛哲学核心概念：人唯一真正自由的是"选择"——即对表象的判断与回应。所有外在之物非我们所能控制，唯有 prohairesis 是属己的。', source:'爱比克泰德《手册》§1' },
  { word:'鸿蒙（Chaos）', def:'赫西俄德《神谱》中最初的存在："最先产生的是 Chaos"。希腊哲学从此神话概念出发，追问秩序如何从鸿蒙中产生——此即 kosmos 的诞生。', source:'赫西俄德《神谱》116行' },
  { word:'Elenchos（辩驳/检验）', def:'苏格拉底的核心方法：通过系统性的提问揭示对方信念中的矛盾，使之认识到自己的无知。不是为了驳倒对方，而是共同探寻真理。', source:'弗拉斯托斯《苏格拉底的辩驳法》' },
];

// —— 教父哲学辞海 ——
const PATRISTIC_CIHAI = [
  { word:'Logos（逻各斯）', def:'教父哲学核心概念。查士丁首次将希腊哲学的逻各斯与基督等同——基督即神圣逻各斯的道成肉身。逻各斯是上帝与人之间的中保，希腊哲学中"逻各斯的种子"（logoi spermatikoi）散布于一切真理之中。', source:'查士丁《护教篇》；约翰福音 1:1' },
  { word:'三位一体（Trinity）', def:'基督教核心教义：独一上帝以父、子、圣灵三个位格（hypostasis）永恒存在，共享同一本质（ousia）。德尔图良首创拉丁词 trinitas。卡帕多西亚教父以一ousia三维hypostasis的公式奠定了精确术语基础。', source:'德尔图良《驳帕克西亚》；巴西尔《书信》236' },
  { word:'Homoousios（本质同一）', def:'尼西亚公会议（325年）确立的核心术语，意为"与父同质"。阿塔纳修以一生五次流放捍卫此词——子不是受造物，而是与父共享同一神圣本质。此词成为区分正统与阿里乌异端的试金石。', source:'尼西亚信经（325）；阿塔纳修《反阿里乌派演讲》' },
  { word:'Hypostasis（位格）', def:'指三位一体中每一个独立的位格存在——父、子、圣灵各有其独特的位格属性（idiomata），分别以非受生、受生、发出为特征。卡帕多西亚教父将其与ousia严格区分：ousia回答"是什么"，hypostasis回答"是谁"。', source:'巴西尔《书信》236；纳西盎的格列高利《神学演讲》' },
  { word:'道成肉身（Incarnation）', def:'永恒的神圣逻各斯在历史中"取肉身而成为人"——耶稣基督同时是完全的神与完全的人。阿塔纳修论证：只有创造者亲自进入受造物，才能修复被罪败坏的人性。"上帝成为人，为使人成为神"。', source:'阿塔纳修《论道成肉身》；约翰福音 1:14' },
  { word:'同归于一（Recapitulation）', def:'伊里奈乌的核心神学概念（希腊文 anakephalaiōsis）。基督作为"新亚当"将人类全部生命阶段重新"总结"在祂的顺服之中——亚当在树前的悖逆被基督在十字架上的顺服逆转，人类历史被重新纳入上帝的救赎计划。', source:'伊里奈乌《反异端论》卷三·18；以弗所书 1:10' },
  { word:'神化（Theosis）', def:'东方教父神学的核心救赎论概念：人通过恩典被提升参与神圣生命，成为"有份于神性的人"（彼得后书1:4）。不是人变为上帝（本质上的），而是人因恩典分享神圣属性——如不朽、圣洁、爱。', source:'阿塔纳修《论道成肉身》54；尼撒的格列高利《大教理问答》' },
  { word:'寓意解经（Allegoria）', def:'奥里根系统发展的释经方法：经文除了字面意义外，还有更深层的属灵意义。如同人由身体、灵魂、精神构成，经文也有字义、道德义、奥秘义三层。这一方法深刻影响了整个中世纪解经传统。', source:'奥里根《论第一原理》卷四；《驳凯尔苏斯》' },
  { word:'原罪（Original Sin）', def:'人类从亚当继承的堕落状态与罪性。东方教父更强调整体人性的朽坏与死亡（"祖传之罪"），西方教父（奥古斯丁）更强调罪责的遗传和意志的捆绑。此差异深刻塑造了东西方神学的不同走向。', source:'奥古斯丁《论自由意志》；尼撒的格列高利《论人的造成》' },
  { word:'恩典（Grace）', def:'上帝非受造的能量与恩赐，使堕落人类得以恢复与上帝的交通并走向神化。奥古斯丁在与伯拉纠的论战中强调恩典的绝对优先性——人的意志若无恩典先行，无法转向善。东方教父更强调整合恩典与人的自由协作（synergeia）。', source:'奥古斯丁《论恩典与自由意志》；巴西尔《论圣灵》' },
  { word:'上帝之城（Civitas Dei）', def:'奥古斯丁历史神学的核心概念。人类历史中并存两座城：地上之城（以自爱为基础）和上帝之城（以上帝之爱为基础）。地上之城的命运是审判与毁灭，上帝之城的命运是永恒安息。罗马的陷落只是地上之城命运的缩影。', source:'奥古斯丁《上帝之城》卷十一-卷二十二' },
  { word:'信仰寻求理解（Fides quaerens intellectum）', def:'奥古斯丁（后由安瑟伦发扬）的认知原则：信仰是理解的起点而非终点——"我相信，为要理解"（credo ut intelligam）。理性不是信仰的敌人，而是信仰在恩典光照下的深化。信仰提供前提，理解使信仰丰满。', source:'奥古斯丁《论三位一体》；安瑟伦《宣讲》' },
  { word:'惟其不可能我才相信（Credo quia absurdum）', def:'德尔图良的悖论式宣言（常被概括为此形式）。原文为"上帝之子死了，这正因为是荒谬的所以才可信；他被埋葬又复活了，这正因为是不可能的所以才确定"。表达信仰超越理性计算的极限，而非简单的反智主义。', source:'德尔图良《论基督的肉身》第5章' },
  { word:'自由意志（Liberum Arbitrium）', def:'教父哲学的核心辩论之一。奥古斯丁早期强调意志的自由选择能力，晚期在与伯拉纠的论战中强调原罪对意志的捆绑——若无恩典先行，意志只能选择恶。东方教父（尼撒的格列高利）更强调整体意志在恩典中的成长与完善。', source:'奥古斯丁《论自由意志》；尼撒的格列高利《论灵魂与复活》' },
  { word:'否定神学（Apophatic Theology）', def:'纳西盎的格列高利开创的神学方法：上帝的本质超越一切概念和语言，我们只能"不是"什么来逼近祂，而非"是"什么来定义祂。摩西在西奈山上进入的黑暗正是上帝不可知的象征。后世经由伪狄奥尼修斯影响了整个神秘主义传统。', source:'纳西盎的格列高利《神学演讲》二·3' },
  { word:'Ousia（本质/实体）', def:'指三位一体中共同的神性本质。卡帕多西亚教父将其与hypostasis严格区分——ousia是共相（父、子、圣灵共有的神性），hypostasis是殊相（每一个位格不可通约的独特性）。三位格共享一个不可分割的神圣本质。', source:'巴西尔《书信》214；纳西盎的格列高利《神学演讲》三' },
  { word:'永恒出生（Eternal Generation）', def:'奥里根首创的神学概念：子不是"在某个时间点"被父创造，而是从永恒中就从父"出生"——如同太阳与光芒的关系，光芒与太阳同时存在。这一概念为尼西亚信经的"受生而非受造"奠定了理论基础。', source:'奥里根《论第一原理》卷一·2；尼西亚信经' },
  { word:'Perichoresis（相互寓居）', def:'三位一体中父、子、圣灵相互"内住"的关系——每一个位格完全地在其他位格之中，却不相混淆。约翰福音14:11"我在父里面，父在我里面"是其圣经基础。卡帕多西亚教父以此概念捍卫三位格的不可分离性。', source:'纳西盎的格列高利《书信》101；约翰福音 14:11' },
  { word:'训蒙师（Paidagogos）', def:'克莱门特的核心隐喻（取自加拉太书3:24"律法是训蒙师"）。希腊哲学对于希腊人如同旧约律法对于犹太人——都是上帝用来预备人心、引导他们走向基督的"训蒙师"。哲学不是信仰的敌人，而是其预备课程。', source:'克莱门特《杂缀集》卷一·5；加拉太书 3:24' },
  { word:'两城说', def:'奥古斯丁在《上帝之城》中提出的历史神学框架。人类被两种爱划分为两座城：爱自己以至于轻视上帝者构成地上之城（civitas terrena），爱上帝以至于忘却自己者构成上帝之城（civitas Dei）。历史即两座城的交织与分离。', source:'奥古斯丁《上帝之城》卷十四·28' },
  { word:'Oikonomia（经世）', def:'希腊教父用以指称上帝在救赎历史中的计划与安排——区别于theologia（上帝自身的永恒内在生命）。三位一体在经世中的显现（子道成肉身，灵被差遣）真实反映内在三一的关系，而非仅仅是"面具"的变换。', source:'巴西尔《论圣灵》；以弗所书 1:10' },
  { word:'恶是善的缺乏（Privatio Boni）', def:'奥古斯丁（继承普罗提诺）对恶的经典定义：恶不是一种实体或本性，而是善的缺乏（privatio boni）。如同失明不是一种东西而是视力的缺失。这一概念解决了"善的上帝为何创造恶"的神正论难题——上帝并未创造恶，恶是自由意志对善的背离。', source:'奥古斯丁《忏悔录》卷七·12；《上帝之城》卷十一·9' },
  { word:'Apologia（护教）', def:'教父哲学的发端文体。2世纪教父们以希腊哲学的形式和论证方式为基督教辩护，回应异教知识分子的批评——基督教不是"无神论"（因不拜偶像），不是迷信，而是"真正的哲学"。查士丁和德尔图良的同名著作《护教篇》是这一文体的经典。', source:'查士丁《护教篇》；德尔图良《护教篇》' },
];

function SchoolDetailPage() {
  const { name } = useParams();
  const navigate = useNavigate();
  const data = name === '教父哲学' ? PATRISTIC_DATA : GREEK_DATA;
  const subSchools = name === '教父哲学' ? PATRISTIC_SUB_SCHOOLS : GREEK_SUB_SCHOOLS;
  const cihai = name === '教父哲学' ? PATRISTIC_CIHAI : GREEK_CIHAI;
  const heroImage = name === '教父哲学' ? 'url(/schools/patristic.jpg)' : 'url(/schools/greek.jpg)';
  const [hovered, setHovered] = useState(null);

  // Pre-calculate nebula positions — wide spread, Fibonacci-like golden angle
  const thinkers = data.thinkers.map((t, i) => {
    const total = data.thinkers.length;
    const goldenAngle = Math.PI * (3 - Math.sqrt(5)); // ~137.5 degrees in radians
    const radius = 140 + (i / total) * 200 + (i % 3) * 40;
    const angle = i * goldenAngle * 2.2;
    const cx = 400, cy = 280;
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius * 0.7;
    return { ...t, _x: Math.max(50, Math.min(750, x)), _y: Math.max(50, Math.min(560, y)) };
  });

  return (
    <div style={{ background: 'var(--bg)', color: 'var(--text)', fontFamily: '"Playfair Display","PingFang SC",serif' }}>

      {/* ====== Section 1: Hero with Raphael's School of Athens ====== */}
      <div style={{
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
        justifyContent: 'center', alignItems: 'center', textAlign: 'center',
        padding: '40px 32px', position: 'relative', overflow: 'hidden',
        backgroundImage: heroImage,
        backgroundSize: 'cover', backgroundPosition: 'center',
      }}>
        {/* Dark elegant overlay */}
        <div style={{ position: 'absolute', inset: 0, background: 'rgba(244,240,235,0.75)' }} />

        <div style={{ position: 'absolute', top: 16, left: 16 }}>
          <button className="btn btn-secondary" style={{ padding:'4px 10px',fontSize:12 }}
            onClick={() => navigate('/genealogy')}>← 谱系</button>
        </div>
        <p style={{ fontSize: 14, color: 'var(--ochre)', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 16, position: 'relative' }}>
          {data.subtitle}
        </p>
        <h1 style={{ fontSize: 56, fontWeight: 700, fontStyle: 'italic', color: 'var(--ink)', margin: '0 0 16px', position: 'relative', textShadow: '2px 2px 0 rgba(196,149,106,0.15)' }}>
          {data.name}
        </h1>
        <div style={{ width: 80, height: 3, background: 'var(--ochre)', margin: '16px 0 28px' }} />
        <blockquote style={{
          fontSize: 22, fontStyle: 'italic', color: 'var(--text-dim)',
          maxWidth: 560, lineHeight: 1.8, margin: '0 0 12px', position: 'relative',
        }}>
          {data.quote}
        </blockquote>
        <p style={{ fontSize: 14, color: 'var(--ochre)', fontWeight: 500 }}>— {data.quoteAuthor}</p>
        <div style={{ position: 'absolute', bottom: 40, animation: 'pulse 1.5s infinite' }}>
          <span style={{ fontSize: 24, color: 'var(--border)' }}>↓</span>
        </div>
      </div>

      {/* ====== Section 2: Overview ====== */}
      <div style={{
        minHeight: '100vh', padding: '60px 40px', maxWidth: 800, margin: '0 auto',
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 24 }}>
          核心思想与流派脉络
        </h2>
        <div style={{ fontSize: 16, lineHeight: 2.0, color: 'var(--text)', whiteSpace: 'pre-line', marginBottom: 40 }}>
          {data.overview}
        </div>

        {/* Sub-school cards */}
        <h3 style={{ fontSize: 20, fontWeight: 600, color: 'var(--ochre)', marginBottom: 20 }}>下属流派</h3>
        {subSchools.map(sub => (
          <div key={sub.name} style={{
            background: 'rgba(237,231,221,0.95)', borderRadius: 10, padding: '16px 20px',
            marginBottom: 14, borderLeft: '3px solid var(--ochre)',
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6 }}>
              <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--ink)', margin: 0 }}>{sub.name}</h4>
              <span style={{ fontSize: 12, color: 'var(--ochre)' }}>{sub.era}</span>
            </div>
            <p style={{ fontSize: 14, color: 'var(--text-dim)', lineHeight: 1.8, margin: 0 }}>{sub.desc}</p>
          </div>
        ))}
      </div>

      {/* ====== Section 3: Star Constellation ====== */}
      <div style={{
        minHeight: '100vh', padding: '40px 20px', position: 'relative',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 30 }}>
          思想星丛
        </h2>

        {/* Constellation canvas */}
        <div style={{
          width: '100%', maxWidth: 850, height: 600, margin: '0 auto',
          position: 'relative', overflow: 'hidden',
        }}>
          {/* Background nebula glow */}
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 50%, rgba(196,149,106,0.06) 0%, transparent 70%)' }} />

          {/* SVG lines */}
          <svg style={{ position: 'absolute', top:0, left:0, width:'100%', height:'100%' }}>
            {data.relations.map((r, i) => {
              const from = thinkers.find(t => t.name === r.from);
              const to = thinkers.find(t => t.name === r.to);
              if (!from || !to) return null;
              return (
                <g key={i}>
                  <line x1={from._x} y1={from._y} x2={to._x} y2={to._y}
                    stroke={r.type==='师生'?'var(--ochre)':r.type==='对立'?'#A06050':r.type==='继承'?'var(--prussian)':'#999'}
                    strokeWidth={1} strokeDasharray={r.type==='对立'?'6,4':''} opacity={0.35} />
                  <text x={(from._x+to._x)/2} y={(from._y+to._y)/2-6}
                    fontSize={8} fill="var(--text-dim)" textAnchor="middle" fontStyle="italic" opacity={0.6}>
                    {r.type}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Thinker dots — nebula positions */}
          {thinkers.map((t, i) => {
            const px = t._x, py = t._y;
            const size = 16 + t.influence * 4;
            const isHovered = hovered === t.name;
            const showBelow = py < 100; // near top: tooltip below
            return (
              <div key={t.name} style={{
                position: 'absolute', left: px, top: py,
                transform: 'translate(-50%, -50%)',
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                cursor: 'pointer', zIndex: isHovered ? 10 : 1,
              }}
              onMouseEnter={() => setHovered(t.name)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => navigate(`/author/${encodeURIComponent(t.name)}`)}
              >
                <div style={{
                  width: size, height: size, borderRadius: '50%',
                  background: `radial-gradient(circle at 35% 35%, ${SUB_COLORS[t.sub] || 'var(--ochre)'}dd, ${SUB_COLORS[t.sub] || 'var(--ochre)'})`,
                  boxShadow: isHovered ? `0 0 24px ${SUB_COLORS[t.sub] || 'var(--ochre)'}80` : '0 1px 4px rgba(0,0,0,0.08)',
                  transition: 'all 0.4s cubic-bezier(0.4,0,0.2,1)',
                  transform: isHovered ? 'scale(1.4)' : 'scale(1)',
                }} />
                <span style={{
                  fontSize: 10, color: 'var(--ink)', marginTop: 4,
                  fontWeight: isHovered ? 600 : 400,
                  maxWidth: 80, textAlign: 'center', lineHeight: 1.2,
                  transition: 'all 0.3s',
                }}>
                  {t.name}
                </span>
                {isHovered && (
                  <div style={{
                    position: 'absolute',
                    top: showBelow ? size + 22 : 'auto',
                    bottom: showBelow ? 'auto' : size + 22,
                    left: '50%', transform: 'translateX(-50%)',
                    background: 'rgba(248,244,238,0.98)', border: '1px solid var(--border)',
                    borderRadius: 8, padding: '6px 12px', whiteSpace: 'nowrap', zIndex: 30,
                    boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
                  }}>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{t.sub} · {t.era}</div>
                    <div style={{ fontSize: 12, color: 'var(--ochre)', fontStyle: 'italic' }}>"{t.key}"</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ====== Section 4: Timeline ====== */}
      <div style={{
        minHeight: '100vh', padding: '60px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'center',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 40, textAlign: 'center' }}>
          思想史时间轴
        </h2>

        <div style={{ position: 'relative', maxWidth: 900, margin: '0 auto' }}>
          {/* Central vertical line */}
          <div style={{
            position: 'absolute', left: '50%', top: 0, bottom: 0, width: 3,
            background: 'var(--ink)', opacity: 0.2, transform: 'translateX(-50%)',
          }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
            {data.timeline.map((ev, i) => {
              const isLeft = i % 2 === 0;
              const colors = { birth:'#C4956A', death:'#8B5A5A', book:'#3A5A7C', idea:'#5A8A5A', event:'#C4956A' };
              const icons = { birth:'✦', death:'†', book:'¶', idea:'§', event:'○' };
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', position: 'relative', height: 80,
                }}>
                  {/* Left spacer or card */}
                  <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', paddingRight: 30 }}>
                    {isLeft && (
                      <div style={{
                        maxWidth: 340, background: 'rgba(237,231,221,0.95)', borderRadius: 10,
                        padding: '10px 16px', borderLeft: `3px solid ${colors[ev.type]}`,
                      }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', marginBottom: 2 }}>{ev.event}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-dim)', lineHeight: 1.5 }}>{ev.detail}</div>
                      </div>
                    )}
                  </div>
                  {/* Dot + year on axis */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 80, flexShrink: 0 }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: colors[ev.type], border: '2px solid var(--bg)', zIndex: 1 }} />
                    <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--ochre)', marginTop: 4, textAlign: 'center' }}>{ev.year}</span>
                  </div>
                  {/* Right card */}
                  <div style={{ flex: 1, paddingLeft: 30 }}>
                    {!isLeft && (
                      <div style={{
                        maxWidth: 340, background: 'rgba(237,231,221,0.95)', borderRadius: 10,
                        padding: '10px 16px', borderLeft: `3px solid ${colors[ev.type]}`,
                      }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', marginBottom: 2 }}>{ev.event}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-dim)', lineHeight: 1.5 }}>{ev.detail}</div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ====== Section 5: Word Sea 辞海 ====== */}
      <div style={{
        minHeight: '100vh', padding: '60px 30px', display: 'flex', flexDirection: 'column', justifyContent: 'center',
        maxWidth: 900, margin: '0 auto',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 12, textAlign: 'center' }}>
          辞海
        </h2>
        <p style={{ fontSize: 13, color: 'var(--text-dim)', textAlign: 'center', marginBottom: 32 }}>
          悬停词语查看释义与出处
        </p>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
          {cihai.map((item, i) => {
            const sizes = [14,15,16,17,18,14,15,16,14,17,15,16,18,14,15,16,17,14,15,16,14,15,16,17,18,14,15,16,14,15];
            const size = sizes[i % sizes.length];
            return (
              <span key={i} style={{
                fontSize: size, fontWeight: size > 16 ? 600 : 400,
                color: hovered === item.word ? 'var(--ochre)' : 'var(--ink)',
                opacity: hovered === item.word ? 1 : 0.75,
                padding: '4px 10px', cursor: 'pointer',
                transition: 'all 0.25s', position: 'relative',
                fontFamily: size > 16 ? '"Playfair Display",serif' : 'inherit',
                transform: hovered === item.word ? 'scale(1.15)' : 'scale(1)',
              }}
              onMouseEnter={() => setHovered(item.word)}
              onMouseLeave={() => setHovered(null)}
              >
                {item.word}
                {hovered === item.word && (
                  <div style={{
                    position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)',
                    background: 'rgba(248,244,238,0.98)', border: '1px solid var(--border)',
                    borderRadius: 10, padding: '14px 20px', zIndex: 30, width: 320,
                    boxShadow: '0 6px 30px rgba(0,0,0,0.15)',
                    marginBottom: 10,
                  }}>
                    <div style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text)', marginBottom: 8 }}>
                      {item.def}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--ochre)', fontStyle: 'italic', borderTop: '1px solid var(--border)', paddingTop: 6 }}>
                      {item.source}
                    </div>
                  </div>
                )}
              </span>
            );
          })}
        </div>
      </div>

      {/* ====== Section 6: Conclusion ====== */}
      <div style={{
        minHeight: '100vh', padding: '60px 40px', maxWidth: 720, margin: '0 auto',
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 28 }}>
          结语
        </h2>
        <div style={{ fontSize: 16, lineHeight: 2.2, color: 'var(--text)', whiteSpace: 'pre-line' }}>
          {data.conclusion}
        </div>
        <div style={{ width: 40, height: 2, background: 'var(--ochre)', margin: '32px 0 20px' }} />
        <blockquote style={{
          fontSize: 18, fontStyle: 'italic', color: 'var(--ochre)',
          borderLeft: '3px solid var(--ochre)', paddingLeft: 16, lineHeight: 1.8,
        }}>
          {data.closingQuote}
        </blockquote>
        <div style={{ textAlign: 'center', marginTop: 40 }}>
          <button className="btn btn-primary" style={{ padding: '10px 28px' }}
            onClick={() => navigate('/genealogy')}>
            ← 返回谱系
          </button>
        </div>
      </div>
    </div>
  );
}

export default SchoolDetailPage;
