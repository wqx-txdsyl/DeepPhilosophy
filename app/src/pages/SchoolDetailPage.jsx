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

const SUB_COLORS = {
  '米利都学派':'#C4956A','前苏格拉底':'#B8875E','埃利亚学派':'#AC7A52',
  '多元论':'#A06D46','古希腊哲学':'#94603A','柏拉图学派':'#88532E',
  '犬儒学派':'#7C4622','逍遥学派':'#703916','怀疑论':'#642C0A',
  '伊壁鸠鲁学派':'#6B3820','斯多葛学派':'#3A5A7C','新柏拉图主义':'#2E4A6A',
};

const EPISTEMOLOGY_DATA = {
  name: '认识论',
  quote: '"我思故我在。"',
  quoteAuthor: '笛卡尔',
  subtitle: '关于知识本身的知识，追问认知的边界与根基',
  overview: `认识论（Epistemology）是哲学的核心分支之一，研究知识的本质、来源、范围和证成。希腊词 episteme（知识）与 logos（理论）的组合，直译为"关于知识的理论"。

其核心问题贯穿两千年：什么是知识？柏拉图在《泰阿泰德篇》中首次系统探讨，提出"知识是证成的真信念"（JTB）的经典定义，直到盖梯尔在1963年用反例撼动了这一传统。知识的来源是理性还是经验？理性主义（笛卡尔、莱布尼茨）主张天赋观念与演绎推理，经验主义（洛克、贝克莱、休谟）坚称一切知识来源于感官经验。康德以"先天综合判断"完成哥白尼式革命：心灵主动构造经验对象。我们能知道什么？怀疑论从皮浪到休谟不断挑战知识的确定性。20世纪的分析认识论以语言分析为工具，自然化认识论（蒯因）将知识问题纳入心理学和进化论。

认识论下属主要流派：理性主义、经验主义、先验唯心论（康德批判哲学）、实用主义（皮尔士、詹姆斯、杜威）、现象学认识论（胡塞尔）、分析认识论（罗素、艾耶尔、盖梯尔）、自然化认识论（蒯因）、社会认识论。`,

  thinkers: [
    { name:'柏拉图', sub:'古希腊认识论', era:'前427-前347', influence:9, key:'知识是证成的真信念', works:['泰阿泰德篇','理想国','美诺篇'] },
    { name:'亚里士多德', sub:'古希腊认识论', era:'前384-前322', influence:8, key:'经验归纳与演绎推理', works:['后分析篇','论灵魂'] },
    { name:'皮浪', sub:'怀疑论', era:'前360-前270', influence:7, key:'悬搁一切判断', works:['皮浪学说概要'] },
    { name:'勒内·笛卡尔', sub:'理性主义', era:'1596-1650', influence:10, key:'我思故我在', works:['第一哲学沉思集','方法论'] },
    { name:'巴鲁赫·斯宾诺莎', sub:'理性主义', era:'1632-1677', influence:9, key:'几何学式的知识体系', works:['伦理学'] },
    { name:'戈特弗里德·威廉·莱布尼茨', sub:'理性主义', era:'1646-1716', influence:8, key:'充足理由律与单子论', works:['单子论','人类理智新论'] },
    { name:'约翰·洛克', sub:'经验主义', era:'1632-1704', influence:10, key:'心灵如白板', works:['人类理解论'] },
    { name:'乔治·贝克莱', sub:'经验主义', era:'1685-1753', influence:8, key:'存在即被感知', works:['人类知识原理'] },
    { name:'大卫·休谟', sub:'经验主义', era:'1711-1776', influence:10, key:'因果只是习惯联想', works:['人性论','人类理解研究'] },
    { name:'伊曼努尔·康德', sub:'先验唯心论', era:'1724-1804', influence:10, key:'人为自然立法', works:['纯粹理性批判'] },
    { name:'查尔斯·桑德斯·皮尔士', sub:'实用主义', era:'1839-1914', influence:8, key:'信念是行动的习惯', works:['皮尔斯文选'] },
    { name:'威廉·詹姆斯', sub:'实用主义', era:'1842-1910', influence:8, key:'真理即有用', works:['心理学原理','宗教经验种种'] },
    { name:'埃德蒙德·胡塞尔', sub:'现象学', era:'1859-1938', influence:9, key:'回到事物本身', works:['逻辑研究','纯粹现象学通论'] },
    { name:'伯特兰·罗素', sub:'分析认识论', era:'1872-1970', influence:9, key:'亲知知识与描述知识', works:['哲学问题','人类的知识'] },
    { name:'路德维希·维特根斯坦', sub:'分析认识论', era:'1889-1951', influence:10, key:'语言的界限即世界的界限', works:['逻辑哲学论','哲学研究'] },
    { name:'威拉德·蒯因', sub:'自然化认识论', era:'1908-2000', influence:9, key:'认识论是心理学的一章', works:['语词和对象','从逻辑的观点看'] },
  ],
  relations: [
    { from:'柏拉图', to:'亚里士多德', type:'师生' },
    { from:'柏拉图', to:'皮浪', type:'影响' },
    { from:'亚里士多德', to:'洛克', type:'影响' },
    { from:'笛卡尔', to:'斯宾诺莎', type:'影响' },
    { from:'笛卡尔', to:'莱布尼茨', type:'影响' },
    { from:'笛卡尔', to:'洛克', type:'对立' },
    { from:'洛克', to:'贝克莱', type:'继承' },
    { from:'贝克莱', to:'休谟', type:'影响' },
    { from:'休谟', to:'康德', type:'影响' },
    { from:'康德', to:'胡塞尔', type:'影响' },
    { from:'皮尔士', to:'詹姆斯', type:'影响' },
    { from:'詹姆斯', to:'蒯因', type:'继承' },
    { from:'罗素', to:'维特根斯坦', type:'师生' },
    { from:'休谟', to:'罗素', type:'影响' },
    { from:'康德', to:'皮尔士', type:'影响' },
  ],
  timeline: [
    { year:'前375', event:'柏拉图著《泰阿泰德篇》', detail:'西方哲学史上第一篇系统探讨"什么是知识"的著作，提出JTB经典定义', type:'book' },
    { year:'前350', event:'亚里士多德著《后分析篇》', detail:'建立三段论演绎体系，提出"科学知识始于第一原理"', type:'book' },
    { year:'1641', event:'笛卡尔著《第一哲学沉思集》', detail:'以普遍怀疑为方法，确立"我思故我在"为知识不可动摇的基础', type:'book' },
    { year:'1689', event:'洛克著《人类理解论》', detail:'系统批判天赋观念论，提出心灵白板说，奠定英国经验主义基石', type:'book' },
    { year:'1710', event:'贝克莱著《人类知识原理》', detail:'将经验主义推向极端——存在即被感知，物质实体不存在', type:'book' },
    { year:'1748', event:'休谟著《人类理解研究》', detail:'以怀疑论摧毁因果必然性，将康德从"独断论的睡梦"中唤醒', type:'book' },
    { year:'1781', event:'康德著《纯粹理性批判》', detail:'哥白尼式革命——知识是先天形式与后天经验的综合，划定理性边界', type:'book' },
    { year:'1878', event:'皮尔士发表"如何使我们的观念清晰"', detail:'提出实用主义的意义理论，实用主义认识论正式诞生', type:'idea' },
    { year:'1900', event:'胡塞尔著《逻辑研究》', detail:'创立现象学方法，以"回到事物本身"超越经验-理性的对立', type:'book' },
    { year:'1912', event:'罗素著《哲学问题》', detail:'以分析哲学方法重新处理认识论，提出亲知知识与描述知识的区分', type:'book' },
    { year:'1921', event:'维特根斯坦著《逻辑哲学论》', detail:'以语言批判解决哲学问题，宣称"语言的界限即世界的界限"', type:'book' },
    { year:'1963', event:'盖梯尔发表3页短文', detail:'以反例摧毁JTB经典知识定义，引发分析认识论半个世纪的知识定义之争', type:'event' },
    { year:'1969', event:'蒯因发表"自然化的认识论"', detail:'主张认识论应成为心理学与进化论的一章，不再追求先验的第一哲学', type:'idea' },
  ],
  conclusion: `认识论是哲学永远的自我反省——知识对知识自身的审视。从柏拉图的洞穴到笛卡尔的炉边，从休谟的怀疑到康德的批判，从盖梯尔的三个反例到蒯因的自然化转向，这场追问从未停歇。

它教导我们：知识的边界不是封闭的围墙，而是不断扩展的地平线。每一次对"什么是知识"的追问，都是对人类理性的再校准。认识论既是最抽象的哲学分支，也是最切己的——因为"我们如何知道"这个问题，决定了我们如何生活、如何判断、如何与世界相处。

在信息爆炸的当代，认识论的意义前所未有地迫切：当"后真相"与"另类事实"泛滥，对知识标准的坚守就是对抗思想混乱的灯塔。`,
  closingQuote: '"有两种东西，我对它们的思考越是深沉和持久，它们在我心灵中唤起的惊奇和敬畏就会日新月异——我头顶的星空和我心中的道德法则。" — 康德',
};

function SchoolDetailPage() {
  const { name } = useParams();
  const navigate = useNavigate();
  const data = name === '认识论' ? EPISTEMOLOGY_DATA : GREEK_DATA;
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
        backgroundImage: 'url(/schools/greek.jpg)',
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
        {name === '认识论' ? [
          { name:'理性主义', era:'17-18世纪', desc:'以笛卡尔、斯宾诺莎、莱布尼茨为代表，主张真正的知识来源于理性直觉和演绎推理，而非感官经验。笛卡尔以"我思故我在"为第一原理，试图以数学方法重建全部知识体系。莱布尼茨区分了"理性的真理"与"事实的真理"。理性主义对天赋观念的坚持激发了洛克等经验主义者的系统反驳。' },
          { name:'经验主义', era:'17-18世纪', desc:'洛克、贝克莱、休谟为代表的英国认识论传统，主张一切知识最终来源于感官经验。洛克提出"心灵如白板"（tabula rasa），否定天赋观念。贝克莱将经验主义推向唯心论——物即感知的集合（esse est percipi）。休谟以最彻底的怀疑论解构了因果必然性与自我同一性，将康德从"独断论的睡梦"中惊醒。' },
          { name:'先验唯心论（批判哲学）', era:'18世纪末', desc:'康德在《纯粹理性批判》中完成的"哥白尼式革命"。他超越理性主义与经验主义的对立，提出知识由先天形式（时空与范畴）与后天经验共同构成——"思维无内容是空的，直观无概念是盲的"。现象界可知、物自体不可知，为理性划定了边界。' },
          { name:'实用主义', era:'19世纪末-20世纪', desc:'皮尔士创立、詹姆斯推广、杜威发展的美国哲学传统。以"皮尔士原则"为核心：概念的意义在于其可设想的实际效果。真理不是对实在的静态反映，而是在实践中被验证、修正的动态过程。杜威将认识论改造为"探究理论"（theory of inquiry），弥合了知识与行动的裂隙。' },
          { name:'现象学认识论', era:'20世纪初', desc:'胡塞尔以"回到事物本身"（Zu den Sachen selbst）为口号，创立现象学方法。通过"悬置"自然态度和"本质还原"，揭示意识如何构造其对象。意向性（Intentionalität）概念——一切意识都是"关于某物的意识"——突破了主客二元论，深刻影响了海德格尔、梅洛-庞蒂和萨特。' },
          { name:'分析认识论', era:'20世纪', desc:'罗素、摩尔开启的分析哲学传统以语言分析和逻辑澄清为工具重新处理认识论问题。罗素区分"亲知知识"（by acquaintance）与"描述知识"（by description）。盖梯尔1963年以短短3页论文摧毁了JTB经典知识定义，引发持续至今的"盖梯尔问题"研究。知识论（Theory of Knowledge）成为分析哲学中最活跃的领域之一。' },
          { name:'自然化认识论', era:'20世纪后半叶', desc:'蒯因在1969年提出"自然化的认识论"（Epistemology Naturalized），主张认识论不应再追求先验的第一哲学地位，而应成为心理学和进化论的一章——研究人类作为自然生物如何从感官刺激中构建出关于世界的理论。这一激进主张深刻重塑了当代认识论的版图。' },
        ] : [
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
        ].map(sub => (
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
          {(name === '认识论' ? [
            { word:'JTB（证成的真信念）', def:'柏拉图在《泰阿泰德篇》中提出的经典知识定义：知识是"证成的真信念"（Justified True Belief）。一个人知道P，当且仅当（1）P是真的，（2）他相信P，（3）他有充分的理由相信P。这个定义统治了认识论两千多年，直到盖梯尔1963年用反例证明JTB不是知识的充分条件。', source:'柏拉图《泰阿泰德篇》201c-210a' },
            { word:'盖梯尔问题', def:'1963年，埃德蒙·盖梯尔发表了一篇仅3页的短文，用两个精巧的反例证明：JTB不是知识的充分条件——一个人可以有证成的真信念，但仍然不是知识。这引发了持续至今的"知识定义之争"，催生了可靠主义（reliabilism）、因果理论、德性认识论等众多解决方案。', source:'盖梯尔"证成的真信念是知识吗？"（1963）' },
            { word:'Cogito ergo sum（我思故我在）', def:'笛卡尔以普遍怀疑为方法，发现唯一不可怀疑的是"我正在思考"这一事实本身——因为即使怀疑"我在思考"这个行为本身也是思考。由此确立了一个不可动摇的阿基米德点：自我的存在是直接自明的知识。这成为理性主义认识论的基石。', source:'笛卡尔《第一哲学沉思集》第二沉思' },
            { word:'Tabula Rasa（白板说）', def:'洛克在《人类理解论》中批判天赋观念论，提出人的心灵出生时如同一块白板（tabula rasa），没有任何先天观念。一切知识都来源于经验——外部经验（感觉）与内部经验（反省）。这一隐喻成为经验主义认识论的核心信条。', source:'洛克《人类理解论》卷二·第1章' },
            { word:'先天综合判断', def:'康德的认识论核心概念。"先天"（a priori）指独立于经验且必然为真，"综合"指谓词不在主词概念之中（增加新知识）。"先天综合判断如何可能？"是《纯粹理性批判》的总问题。数学（7+5=12）和自然科学的基本原理都是先天综合判断。', source:'康德《纯粹理性批判》导言' },
            { word:'物自体（Ding an sich）', def:'康德认识论的关键区分：人类只能认识"现象"（Phenomena），即经过先天形式（时空、范畴）加工后的经验对象。"物自体"（Noumena）是独立于人类认识形式而存在的客观实在本身——它存在，但我们永远无法认识它。理性一旦试图超越现象界去认识物自体，就会陷入"二律背反"。', source:'康德《纯粹理性批判》先验辩证论' },
            { word:'现象学还原（Epoche）', def:'胡塞尔从古希腊怀疑论借用的术语重新定义为现象学方法的第一步：将关于外部世界存在的"自然态度""放入括号"（悬搁），不否认也不肯定其存在，而是专注于意识如何构造其对象的纯粹描述。通过还原，我们回到"事物本身"——即意识中显现的对象。', source:'胡塞尔《纯粹现象学通论》§31-32' },
            { word:'意向性（Intentionalität）', def:'胡塞尔从布伦塔诺那里继承的核心概念：一切意识都是"关于某物的意识"。意识的本质特性就是指向对象——思考总是思考什么，感知总是感知什么。意向性打破了近代认识论中主客二元对立的基本预设，为现象学认识论奠基。', source:'胡塞尔《逻辑研究》卷五' },
            { word:'亲知知识与描述知识', def:'罗素在《哲学问题》中提出的经典区分：亲知知识（knowledge by acquaintance）是对感觉材料、记忆、内省和共相的直接意识，无需推论；描述知识（knowledge by description）是通过限定描述词（"那个如此这般的东西"）间接得知。一切知识最终必须奠基在亲知之上。', source:'罗素《哲学问题》第5章' },
            { word:'皮尔士原则（实用主义准则）', def:'皮尔士提出的意义理论核心："考虑一下，我们设想我们概念的对象具有什么样的、可以设想到的实际效果——那么，我们关于这些效果的概念，就是我们关于该对象的全部概念。"一个概念的意义，就在于它可能产生的所有实际效果的总和。', source:'皮尔士"如何使我们的观念清晰"（1878）' },
            { word:'自然化的认识论', def:'蒯因在1969年同名论文中主张：认识论不应再追求笛卡尔式的先验第一哲学地位，而应成为"心理学的一章，从而是自然科学的一章"。人类如何从贫乏的感官输入产生出丰富的科学理论，这本身就是一个经验科学问题。', source:'蒯因"自然化的认识论"（1969）' },
            { word:'可靠主义（Reliabilism）', def:'对盖梯尔问题的主要解决方案之一。知识不是证成的真信念，而是由可靠的认知过程产生的真信念。只要信念的形成过程（如视觉感知、记忆、推理）在现实中是可靠的，即使主体不能提供证成理由，也可以拥有知识。', source:'戈德曼"什么是证成的信念？"（1979）' },
            { word:'感觉材料（Sense Data）', def:'20世纪早期分析认识论的核心概念。当我们感知一个物体（如一个苹果）时，我们直接意识到的是"感觉材料"——颜色斑块、形状、质感等——而非物体本身。从感觉材料到物理对象的推论是认识论的一个基本难题。', source:'摩尔"对常识的辩护"（1925）、罗素《哲学问题》' },
            { word:'摩尔的常识哲学', def:'G.E.摩尔以"举起双手"的著名论证捍卫常识知识："我知道这是一只手，这也是一只手"——对外部世界存在的常识信念比任何怀疑论的论证都更确定。挑战怀疑论者：你确定你怀疑我有一只手的前提，比我确定我有一只手更确定吗？', source:'摩尔"对外部世界的证明"（1939）' },
            { word:'语言游戏与家族相似', def:'维特根斯坦后期哲学的核心概念。"知识"、"确定性"、"怀疑"这些词的意义不在于指称某个本质，而在于它们在各种"语言游戏"中的用法。"我知道"在不同语境中做不同的事——确认、保证、排除怀疑。"家族相似"取代了本质主义的定义方式。', source:'维特根斯坦《哲学研究》§65-71' },
            { word:'心灵白板', def:'洛克对天赋观念论的批判：人的心灵出生时如同一块白板，没有任何先天观念或原则。一切知识都来自经验——外部经验（感觉）和内部经验（反省）。这彻底改变了认识论的方向：问题从"理性中有何先天知识"变为"心灵如何从简单观念构建出复杂知识体系"。', source:'洛克《人类理解论》1690年' },
            { word:'充足理由律', def:'莱布尼茨提出的两大推理原则之一（另一为矛盾律）："没有任何事实是真实的或存在的，没有任何陈述是正确的，除非有一个充足理由说明它为什么是这样而不是那样。"这既是形而上学原则，也是认识论原则——一切知识都应该有充分的根据。', source:'莱布尼茨《单子论》§31-32' },
            { word:'二律背反', def:'康德指出，当理性试图超越经验界限去认识总体性对象（如宇宙是否有开端、是否有自由意志）时，会陷入"二律背反"——正题和反题都可以得到同等有力的证明。这恰恰证明了理性不能认识物自体，只能停留在现象界。', source:'康德《纯粹理性批判》先验辩证论·二律背反' },
            { word:'归纳问题', def:'休谟提出的经典问题：我们如何证成从"过去太阳每天升起"到"明天太阳也将升起"的推论？归纳推理的可靠性不能诉诸逻辑（不是必然的），也不能诉诸经验（因为那正是在使用归纳来证成归纳）——这就是"休谟问题"，也是现代认识论的核心难题之一。', source:'休谟《人类理解研究》§4-5' },
            { word:'本我、自我与超我', def:'虽主要属于精神分析，但弗洛伊德的这三重人格结构深刻影响了认识论中的主体性问题：认识主体不再是笛卡尔的透明自我意识，而是受无意识欲望支配的复杂心理系统。"理性化"可能是无意识冲动的伪装，这动摇了纯粹理性主体的认识论预设。', source:'弗洛伊德《自我与本我》1923年' },
            { word:'范式与不可通约性', def:'库恩的科学哲学对认识论产生了深远影响。科学知识不是累积式的进步，而是通过"范式转换"——从牛顿力学到相对论——断裂式地变迁。不同范式之间"不可通约"（incommensurable），因为它们对"什么是好的解释"有不同的标准。', source:'库恩《科学革命的结构》1962年' },
            { word:'德性认识论', def:'20世纪末新兴的认识论路径。与其问"什么使得一个信念是证成的"，不如问"什么使得一个认知者是优秀的认知者"。将认识论的重心从信念评价转向认知者的智识德性——开明、细致、理智的勇气等。这种"德性转向"将伦理学与认识论融合。', source:'索萨《德性认识论》（1991）、扎格泽波斯基（1996）' },
            { word:'缸中之脑', def:'普特南提出的怀疑论思想实验：假设一个大脑被放在营养缸中，连接到超级计算机，计算机向大脑输入与真实世界完全相同的电信号——这个大脑能否知道自己不是"缸中之脑"？这是笛卡尔恶魔假设的现代版本，直指外部世界知识的可能性这一根本难题。', source:'普特南《理性、真理与历史》1981年' },
            { word:'直观无概念则盲', def:'康德名言"思维无内容是空的，直观无概念是盲的"体现了其认识论核心洞见：知识既需要感官直观提供经验材料，也需要知性概念赋予材料以形式和意义。两者缺一不可——这是对理性主义（有概念无直观）与经验主义（有直观无概念）的双重超越。', source:'康德《纯粹理性批判》A51/B75' },
            { word:'分析-综合区分', def:'分析命题（"所有单身汉都是未婚的"）的谓词已包含在主词概念之中，其真理仅取决于语词意义；综合命题（"这张桌子是棕色的"）的谓词增加了新信息，其真理取决于世界的事实。蒯因在"经验论的两个教条"中论证这一区分本身就是一个无法证成的经验论教条。', source:'蒯因"经验论的两个教条"（1951）' },
            { word:'我思（Cogito）', def:'笛卡尔的方法论怀疑的终点。即便恶魔在欺骗我的一切感知和思想，"我被欺骗"这个事实本身就预设了"我存在"。这是理性能够达到的第一个确定的、不可动摇的知识——自我的存在是直接自明的。', source:'笛卡尔《第一哲学沉思集》1641年' },
            { word:'确证的整体论', def:'蒯因指出，我们的知识体系不是单个命题面对经验的检验，而是"整个科学像一个力场"——只有边缘（最接近经验的命题）才直接接触经验数据，核心的逻辑和数学原理因远离经验而被间接确证。任何一个命题都可以在任何经验面前被坚持，只要我们对体系的其他部分做出足够大的调整。', source:'蒯因"经验论的两个教条"（1951）' },
            { word:'知识论证（黑白玛丽）', def:'杰克逊提出的思想实验：玛丽是一位从小被关在黑白房间里的天才神经科学家，她知道关于颜色视觉的一切物理知识——光波、视网膜、神经元。当她第一次走出房间看到红色时，她学到了新东西吗？如果答案是肯定的，那么物理主义关于知识就错了——存在不可还原为物理事实的"现象知识"。', source:'杰克逊"副现象的感受质"（1982）' },
            { word:'现象知识 vs 物理知识', def:'关于意识经验"是什么感觉"的知识（如看见红色的感受）是一种不同于物理事实知识的"现象知识"或"感受质知识"。即便掌握了所有物理事实，也无法推出"看见红色是什么感觉"——这构成了对物理主义的严重挑战。', source:'内格尔"做一只蝙蝠是什么感觉？"（1974）' },
          ] : [
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
          ].map((item, i) => {
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
