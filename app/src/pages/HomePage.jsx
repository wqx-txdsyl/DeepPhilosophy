/**
 * 谱系 —— 垂直时间轴，每行一个大流派卡片
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import DAILY_QUOTES from '../data/dailyQuotes';

const WESTERN_TIMELINE = [
  { century: '公元前6世纪', schools: ['古希腊哲学'] },
  { century: '公元前3世纪', schools: ['斯多葛学派','怀疑论'] },
  { century: '4世纪', schools: ['教父哲学'] },
  { century: '11世纪', schools: ['经院哲学','唯名论'] },
  { century: '17世纪', schools: ['理性主义', '经验主义'] },
  { century: '18世纪', schools: ['启蒙运动', '实在论', '唯心主义', '自由主义', '浪漫主义'] },
  { century: '19世纪', schools: ['德国古典哲学', '功利主义', '超验主义', '实证主义', '马克思主义', '生命哲学', '社会学'] },
  { century: '20世纪初', schools: ['实用主义', '精神分析学', '现象学', '存在主义', '分析哲学', '过程哲学', '哲学人类学'] },
  { century: '20世纪中', schools: ['西方马克思主义', '法兰克福学派', '批判理论', '科学哲学', '荒诞哲学', '基督教哲学', '结构主义', '政治哲学', '哲学诠释学'] },
  { century: '20世纪末', schools: ['后结构主义', '后现代主义', '伦理学', '宗教哲学', '女性主义', '社群主义'] },
  { century: '21世纪', schools: ['技术哲学'] },
];

const SCHOOL_DESCRIPTIONS = {
  '古希腊哲学':'西方哲学的总源——以理性思辨取代神话解释，首次追问万物的本原、存在的本质与善的生活。',
  '教父哲学':'以希腊理性为基督教信仰奠基——教父们将耶路撒冷的信仰翻译为雅典的语言。',
  '经院哲学':'以亚里士多德的逻辑为基督教构建理性圣殿——信仰寻求理解，恩典成全自然。',
  '理性主义':'以数学公理为范本，以天赋观念为起点，从自明第一原理演绎出全部知识体系。',
  '经验主义':'一切知识起源于感觉经验——心灵如白纸，无经验则无观念。',
  '启蒙运动':'敢于运用你自己的理性——以理性之光驱散迷信与专制，相信进步、自由与人性尊严。',
  '实在论':'存在独立于心灵——无论是柏拉图的理念、亚里士多德的实体还是常识的物质世界。',
  '唯心主义':'实在的本质是精神或观念——存在即被感知，或世界是绝对精神的自我展开。',
  '自由主义':'个人自由是最高政治价值——限制权力、保护权利、宽容多元。',
  '浪漫主义':'以情感和想象反抗启蒙理性的冰冷——自然、天才、个体性与无限渴望。',
  '德国古典哲学':'从康德到黑格尔的哲学革命——以批判、体系和辩证法将理性推到历史的顶点。',
  '功利主义':'最大多数人的最大幸福——道德行为的对错以其产生的快乐或痛苦为唯一判准。',
  '超验主义':'美国的精神独立宣言——人人心中皆有与宇宙直接沟通的神性火花。',
  '实证主义':'以自然科学为一切知识的典范——拒斥形而上学，只问"如何"不问"为何"。',
  '马克思主义':'哲学家们只是解释了世界，问题在于改变世界——历史唯物主义与阶级斗争。',
  '生命哲学':'理性不能穷尽生命——以直觉、绵延与意志理解比理智更深层的生命冲动。',
  '社会学':'以科学方法追问社会何以可能——从分工、失范到官僚制的理性牢笼。',
  '实用主义':'真理即有用，意义在于效果——以行动后果检验观念的真值。',
  '精神分析学':'心灵深处有一个你不知道的你——无意识、欲望与压抑塑造了我们的全部。',
  '现象学':'回到事物本身——悬搁自然态度，描述意识给予经验的结构。',
  '存在主义':'存在先于本质——人被抛入自由之中，必须亲自赋予生命以意义。',
  '分析哲学':'全部哲学就是语言的批判——以逻辑分析澄清概念、消解假问题。',
  '过程哲学':'实在是生成而非存在——宇宙在创造性进展中不断向新质跃迁。',
  '哲学人类学':'人是什么——以哲学整合生物学、心理学与社会学对人的认识。',
  '西方马克思主义':'回到黑格尔的马克思——以文化批判和意识形态理论补充经济分析。',
  '法兰克福学派':'批判理论——工具理性已沦为新的统治形式，启蒙必须反思其自身的辩证法。',
  '批判理论':'传统的理论描述世界，批判的理论旨在解放——揭示权力、知识与意识形态的纠缠。',
  '科学哲学':'科学何以成为科学——从逻辑实证主义到范式革命与方法论的无政府主义。',
  '荒诞哲学':'世界没有意义，但人必须活下去——以反抗、自由与激情回应荒诞。',
  '基督教哲学':'信仰在理性中追问自身——从新托马斯主义到后自由主义神学的哲学反思。',
  '结构主义':'意义不在事物内部而在关系之中——语言、神话与无意识皆由深层结构支配。',
  '政治哲学':'追问正义、权力与自由的根基——从社会契约到分配正义与承认的政治。',
  '哲学诠释学':'理解不是方法而是存在方式——视域融合、效果历史与语言的对话本性。',
  '后结构主义':'解构逻各斯中心主义——差异、延异与权力微观物理学。',
  '后现代主义':'对宏大叙事的怀疑——真理、主体与历史都是语言的建构。',
  '伦理学':'追问人应该如何生活——从德性、义务到效用与关怀。',
  '宗教哲学':'以理性审视信仰——上帝存在的证明、恶的问题与宗教多元论。',
  '女性主义':'个人的即政治的——揭示性别作为权力结构的哲学根基。',
  '社群主义':'自我镶嵌于共同体之中——正义、善与归属不可分离。',
  '技术哲学':'技术不是中立的工具——它重塑了人的存在方式与世界的关系。',
  '斯多葛学派':'控制可控的，接受不可控的——困扰人的不是事物而是人对事物的看法。',
  '怀疑论':'悬搁判断以获得心灵的宁静——对一切教条保持彻底的审慎。',
  '唯名论':'共相只是名称不是实在——只有个别事物真实存在。',
};

const SCHOOL_COLORS = (() => {
  const base = [];
  // 43 Western schools: warm bronze -> cool blue gradient
  for (let i = 0; i < 43; i++) {
    const t = i / 42;
    const r = Math.round(196 - t * 180);
    const g = Math.round(149 - t * 70);
    const b = Math.round(106 + t * 30);
    const toHex = n => n.toString(16).padStart(2,'0');
    base.push('#' + toHex(r) + toHex(g) + toHex(b));
  }
  return base;
})();

// ——— 东方哲学 ———
const EASTERN_TIMELINE = [
  { century: '公元前6世纪', schools: ['道家','儒家'] },
  { century: '公元前5世纪', schools: ['墨家','兵家'] },
  { century: '公元前4世纪', schools: ['法家','名家','阴阳家'] },
  { century: '公元前2世纪', schools: ['两汉经学'] },
  { century: '3世纪', schools: ['魏晋玄学'] },
  { century: '6世纪', schools: ['隋唐佛学'] },
  { century: '11世纪', schools: ['宋明理学'] },
  { century: '17世纪', schools: ['明清实学','乾嘉朴学'] },
  { century: '19世纪末', schools: ['天演论','维新派'] },
  { century: '20世纪初', schools: ['三民主义','旧民主主义'] },
  { century: '20世纪中', schools: ['毛泽东思想','中国马克思主义哲学','新民主主义'] },
  { century: '20世纪末', schools: ['现代新儒家','中国实证哲学','马克思主义哲学的中国化与体系化'] },
  { century: '21世纪', schools: ['习近平新时代中国特色社会主义思想'] },
];

const EASTERN_DESCRIPTIONS = {
  '儒家':'以仁为核心，以礼为规范——修身齐家治国平天下，两千年来塑造了东亚文明的精神底色。',
  '道家':'道法自然，无为而治——以柔克刚的智慧，在文明的对立面为心灵保留一片返璞归真的天地。',
  '墨家':'兼爱非攻，尚贤节用——以普遍之爱与逻辑理性，发出先秦最激进的平等主义呼声。',
  '法家':'以法治国，不别亲疏——制度先于道德，法律面前人人平等，为大一统帝国奠定制度哲学。',
  '名家':'白马非马，离坚白——中国最早的逻辑学与语言哲学，以概念辨析与悖论追问名与实的边界。',
  '阴阳家':'阴阳消长，五德终始——以宇宙论框架将自然、历史与政治纳入统一的运转法则。',
  '兵家':'知己知彼，不战屈人——将冲突升华为博弈的艺术，以最小代价达成最大目标的智慧。',
  '两汉经学':'通经致用，以经为法——今文以微言大义构建天人感应的政治神学，古文以训诂考据守护经典本义。',
  '魏晋玄学':'越名教而任自然——以老庄注解为表，以人格解放为里，在乱世中为个体心灵开辟自由的精神空间。',
  '隋唐佛学':'八宗竞秀，会通中印——天台之圆融、唯识之精密、华严之无尽、禅宗之顿悟，佛教在中国完成最深刻的本土化创造。',
  '宋明理学':'为天地立心，为生民立命——以天理为宇宙与道德的共同根基，在佛道冲击后重建儒家的形而上学体系。气学、理学、心学三家鼎立。',
  '明清实学':'经世致用，实事求是——以批判空疏理学为旗帜，将学术重心从心性玄谈转向国计民生与实测之学。',
  '乾嘉朴学':'无征不信，孤证不立——以训诂考据校勘为方法，将语言学与历史学提升为严谨的实证科学。',
  '天演论':'物竞天择，适者生存——严复以《天演论》震醒甲午之后整整一代知识分子：不变则亡。',
  '维新派':'变则通，通则久——康梁借今文经改制传统为政治变革提供哲学合法性，探索中国政治转型的第一条道路。',
  '三民主义':'民族、民权、民生——孙中山以兼容中西的理论框架为现代中国提供第一个系统化的建国哲学方案。',
  '旧民主主义':'旧民主主义革命时期的政治哲学——以三民主义为核心，探索资产阶级民主共和道路，从兴中会到同盟会再到辛亥革命的理论演进。',
  '毛泽东思想':'实事求是，群众路线——将马克思主义普遍原理与中国革命具体实践相结合，从《实践论》《矛盾论》到农村包围城市，奠定了马克思主义中国化的理论与实践的基石。',
  '新民主主义':'新民主主义革命理论——毛泽东系统阐述中国革命分两步走，各革命阶级联合专政，建设民族的科学的大众的新文化。',
  '中国马克思主义哲学':'辩证唯物主义与历史唯物主义在中国的传播、研究与体系化——从革命指南发展为学科体系和教科书体系，成为当代中国哲学的基本范式。',
  '现代新儒家':'返本开新，内圣外王——熊十力、牟宗三、唐君毅等以儒家心性之学为根基，与康德、黑格尔展开深度对话，寻求中国传统智慧的现代转型。',
  '中国实证哲学':'大胆假设，小心求证——胡适将杜威实验主义引入中国，以科学方法整理国故，开辟中国现代学术的新范式。',
  '马克思主义哲学的中国化与体系化':'从实践标准到特色社会主义理论体系的哲学基础——马克思主义哲学在中国制度实践与理论创新的双轮驱动下，不断生成新的理论形态。',
  '习近平新时代中国特色社会主义思想':'以人民为中心的发展思想——将马克思主义基本原理与新时代中国具体实际相结合，系统回应了坚持和发展什么样的中国特色社会主义这一重大时代课题。',
};

const EASTERN_COLORS = (() => {
  const base = [];
  for (let i = 0; i < 24; i++) {
    const t = i / 23;
    const r = Math.round(196 - t * 150);
    const g = Math.round(106 - t * 25);
    const b = Math.round(106 + t * 15);
    const toHex = n => n.toString(16).padStart(2,'0');
    base.push('#' + toHex(r) + toHex(g) + toHex(b));
  }
  return base;
})();


function HomePage() {
  const navigate = useNavigate();
  const [schoolData, setSchoolData] = useState({});
  const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem('dp_token'));
  const [username, setUsername] = useState(localStorage.getItem('dp_username') || '');

  useEffect(() => {
    fetch(`${getApiBase()}/api/authors`, { signal: AbortSignal.timeout(10000) })
      .then(r => r.json())
      .then(d => {
        const map = {};
        (d.authors || []).forEach(a => {
          const raw = a.school || '';
          if (!raw) return;
          raw.replace('、','/').replace('，','/').replace(',','/').split('/').forEach(s => {
            s = s.trim();
            if (!s || s.length < 2) return;
            // Normalize to big schools
            const normMap = {
              '存在主义先驱':'存在主义','存在哲学':'存在主义','文学哲学':'存在主义',
              '柏拉图主义':'古希腊哲学','逍遥学派':'古希腊哲学','伊壁鸠鲁主义':'古希腊哲学',
              '米利都学派':'古希腊哲学','埃利亚派':'古希腊哲学','前苏格拉底':'古希腊哲学',
              '古代哲学':'古希腊哲学','犬儒学派':'古希腊哲学','自然哲学':'古希腊哲学',
              '新柏拉图主义':'古希腊哲学','折衷主义':'古希腊哲学','元素论':'古希腊哲学',
              '斯多葛派':'斯多葛学派','斯多葛主义':'斯多葛学派','晚期斯多亚':'斯多葛学派',
              '批判哲学':'德国古典哲学','德国唯心论':'德国古典哲学','唯意志论':'德国古典哲学','悲观主义哲学':'德国古典哲学',
              '交往理论':'法兰克福学派','文化批评':'法兰克福学派','法兰克福学派（批判理论）':'法兰克福学派',
              '结构马克思主义':'马克思主义','政治经济学':'政治哲学','宗教社会学':'社会学',
              '现实主义政治哲学':'政治哲学','文艺复兴人文主义':'启蒙运动','逻辑实证主义':'实证主义',
              '启蒙哲学':'启蒙运动','启蒙思想':'启蒙运动','苏格兰启蒙':'启蒙运动','人文主义':'启蒙运动',
              '精神分析':'精神分析学','分析心理学':'精神分析学','心理治疗':'精神分析学',
              '逻辑原子主义':'分析哲学','逻辑实用主义':'分析哲学','逻辑实证':'分析哲学',
              '日常语言':'分析哲学','语言哲学':'分析哲学',
              '形式社会学':'社会学','社会心理学':'社会学','群体心理学':'社会学','社会达尔文':'社会学',
              '激进平等':'政治哲学','责任伦理':'政治哲学','社会契约论':'政治哲学','古典经济学':'政治哲学',
              '德性伦理':'伦理学','批判理性主义':'科学哲学',
              '解释学':'现象学','身体哲学':'现象学','意向性':'现象学',
              '常识实在论':'实在论','人本唯物论':'实在论','机械唯物主义':'实在论',
              '结构语言学':'结构主义','进步教育':'实用主义','新实用主义':'实用主义',
              '荒诞文学':'荒诞哲学','浪漫主义先驱':'浪漫主义',
              '近代哲学之父':'近代哲学','有机体哲学':'过程哲学',
              '后现代哲学':'后现代主义','解构主义':'后现代主义',
              '绝对唯心主义':'唯心主义','历史唯物主义':'马克思主义',
              '文化霸权理论':'西方马克思主义',
            };
            const big = normMap[s] || s;
            if (!map[big]) map[big] = { authors: [], keywords: new Set(), books: [] };
            if (!map[big].authors.includes(a.name)) {
              map[big].authors.push(a.name);
              map[big].books.push(...(a.books || []));
            }
            if (a.era) map[big].keywords.add(a.era.split('-')[0].replace(/[^0-9]/g,'') + '年代');
            if (a.country) map[big].keywords.add(a.country.split('/')[0]);
          });
        });
        setSchoolData(map);
      }).catch(() => {});
  }, []);

  const scrollToTimeline = () => {
    document.getElementById('home-content')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="page-container" style={{ paddingBottom: 0, margin: 0 }}>

      {/* Floating nav bar — matching header layout */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
        display: 'flex', alignItems: 'center',
        padding: '16px 20px',
      }}>
        <h1 onClick={() => navigate('/')} style={{
          fontFamily: '"Playfair Display","PingFang SC",serif',
          fontSize: 16, fontWeight: 400, fontStyle: 'italic',
          color: 'var(--ink)', cursor: 'pointer',
          margin: 0, marginRight: 4, letterSpacing: '0.03em',
        }}>DeepPhilosophy</h1>
        <span style={{ display: 'flex', gap: 0, marginRight: 'auto', marginLeft: -2 }}>
          {[
            { label: '📚', text: '书籍', path: '/books' },
            { label: '✒️', text: '哲人', path: '/authors' },
            { label: '🧬', text: '谱系', path: '/genealogy' },
            { label: '💬', text: '问答', path: '/qa' },
            { label: '🎮', text: '游戏', path: '/games' },
          ].map(item => (
            <button key={item.path} onClick={() => navigate(item.path)}
              className="nav-btn"
              style={{ flexDirection: 'row', gap: 3, fontSize: 12, padding: '4px 8px' }}>
              <span style={{ fontSize: 15 }}>{item.label}</span>
              <span>{item.text}</span>
            </button>
          ))}
        </span>
      </nav>

      {/* Floating login/user button — right side */}
      <button onClick={() => navigate('/profile')} style={{
        position: 'fixed', top: 18, right: 20, zIndex: 1000,
        fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 500,
        color: 'var(--ink)', background: 'rgba(244,240,235,0.7)', backdropFilter: 'blur(8px)',
        border: '1px solid var(--border)', borderRadius: 4, padding: '8px 18px',
        cursor: 'pointer', letterSpacing: '0.04em', transition: 'all 0.25s'
      }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(244,240,235,0.9)'; e.currentTarget.style.borderColor = 'var(--ochre)'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(244,240,235,0.7)'; e.currentTarget.style.borderColor = 'var(--border)'; }}>
        {loggedIn && username ? '👤 ' + username : '登录 / 注册'}
      </button>

      {/* ══════════ HERO — full screen, world philosophy background ══════════ */}
      <section style={{
        minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center',
        alignItems: 'center', textAlign: 'center', padding: '80px 32px',
        position: 'relative', overflow: 'hidden',
        backgroundImage: 'url(/schools/世界哲学总览.jpg)', backgroundSize: 'cover', backgroundPosition: 'center',
      }}>
        <div style={{ position: 'absolute', inset: 0,
          background: 'linear-gradient(to top, rgba(244,240,235,0.88) 0%, rgba(244,240,235,0.5) 40%, rgba(244,240,235,0.2) 100%)' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 600, letterSpacing: '0.28em', textTransform: 'uppercase', color: 'var(--ochre)', margin: '0 0 24px' }}>
            Philosophical Genealogy
          </p>
          <h1 style={{ fontFamily: '"Playfair Display","PingFang SC",serif', fontSize: 'clamp(3rem, 9vw, 7rem)', fontWeight: 400, fontStyle: 'italic', color: 'var(--ink)', letterSpacing: '0.04em', lineHeight: 1.1, margin: '0 0 20px' }}>
            DeepPhilosophy
          </h1>
          <div style={{ width: 60, height: 1.5, background: 'var(--ochre)', margin: '0 auto 24px', opacity: 0.7 }} />
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'clamp(1rem, 1.5vw, 1.2rem)', fontWeight: 500, color: 'var(--ink)', lineHeight: 1.8, maxWidth: 520, margin: '0 auto 36px', textShadow: '0 0 40px rgba(244,240,235,0.8)' }}>
            从公元前六世纪至二十一世纪<br />七十六个流派，一部横跨两千五百年的思想史长卷
          </p>
          <button onClick={scrollToTimeline} style={{
            fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 500, letterSpacing: '0.08em',
            color: '#fff', background: 'var(--ink)', border: 'none', borderRadius: 4,
            padding: '14px 36px', cursor: 'pointer', transition: 'all 0.25s'
          }}
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--ochre)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'var(--ink)'; }}>
            开始探索 ↓
          </button>
        </div>
        <div style={{ position: 'absolute', bottom: 36, opacity: 0.4 }}>
          <span style={{ fontSize: 20, color: 'var(--text-dim)' }}>↓</span>
        </div>
      </section>

      {/* ══════════ DAILY QUOTE ══════════ */}
      {(() => {
        // quotes loaded from DAILY_QUOTES
        const q = DAILY_QUOTES[Math.floor(Math.random() * DAILY_QUOTES.length)];
        return (
          <section style={{ padding: '80px 32px', textAlign: 'center', background: 'var(--card-bg)', maxWidth: '100%' }}>
            <div style={{ maxWidth: 680, margin: '0 auto' }}>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: 10, fontWeight: 500, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--fade)', marginBottom: 20 }}>Daily Quote</p>
              <p style={{ fontFamily: '"Playfair Display",serif', fontStyle: 'italic', fontSize: 'clamp(1.3rem, 2.5vw, 1.8rem)', color: 'var(--text-dim)', lineHeight: 1.8, fontWeight: 300, margin: '0 0 16px' }}>
                &ldquo;{q.text}&rdquo;
              </p>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--ochre)', fontWeight: 500 }}>&mdash; {q.author}</p>
            </div>
          </section>
        );
      })()}

      {/* ══════════ NUMBERS ══════════ */}
      <section style={{ padding: '48px 32px', maxWidth: 800, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 48, flexWrap: 'wrap', textAlign: 'center' }}>
          {[{ num: '305', label: '哲学著作' }, { num: '355', label: '哲学家' }, { num: '76', label: '哲学流派' }].map(s => (
            <div key={s.label}>
              <p style={{ fontFamily: '"Playfair Display",serif', fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 400, color: 'var(--ink)', margin: '0 0 4px' }}>{s.num}</p>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-dim)', fontWeight: 300, letterSpacing: '0.06em', margin: 0 }}>{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════ THREE ENTRY CARDS ══════════ */}
      <section id="home-content" style={{ padding: '64px 32px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24 }}>
          {[
            { title: '西方哲学', count: '43 流派', desc: '从古希腊到后现代，理性、存在与语言的探索', path: '/western-philosophies', color: 'var(--ochre)' },
            { title: '东方哲学', count: '24 流派', desc: '儒道墨法至当代，两千五百年不断的思想脉络', path: '/eastern-philosophies', color: 'var(--prussian)' },
            { title: '世界哲学', count: '9 流派', desc: '印度、日本、伊斯兰、非洲…全球哲学版图', path: '/world-philosophies', color: '#5A8A5A' },
          ].map(card => (
            <div key={card.title} onClick={() => navigate(card.path)} style={{
              padding: '36px 28px', cursor: 'pointer', borderBottom: '2px solid var(--border)',
              transition: 'all 0.3s', background: 'transparent'
            }}
              onMouseEnter={e => { e.currentTarget.style.borderBottomColor = card.color; e.currentTarget.style.background = 'var(--card-bg)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderBottomColor = 'var(--border)'; e.currentTarget.style.background = 'transparent'; }}>
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: card.color }}>{card.count}</span>
              <h2 style={{ fontFamily: '"Playfair Display",serif', fontSize: 28, fontWeight: 400, color: 'var(--ink)', margin: '8px 0 8px', letterSpacing: '0.03em' }}>{card.title}</h2>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 300, color: 'var(--text-dim)', lineHeight: 1.7, margin: 0 }}>{card.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════ BOOKS + AUTHORS SHOWCASE ══════════ */}
      <section style={{ padding: '48px 32px 64px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 32 }}>
          <div onClick={() => navigate('/books')} style={{ cursor: 'pointer', padding: '28px 24px', borderBottom: '2px solid var(--border)', transition: 'all 0.3s' }}
            onMouseEnter={e => { e.currentTarget.style.borderBottomColor = 'var(--ochre)'; e.currentTarget.style.background = 'var(--card-bg)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderBottomColor = 'var(--border)'; e.currentTarget.style.background = 'transparent'; }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--ochre)' }}>Library</span>
            <h2 style={{ fontFamily: '"Playfair Display",serif', fontSize: 24, fontWeight: 400, color: 'var(--ink)', margin: '6px 0 8px', letterSpacing: '0.03em' }}>305 部哲学著作</h2>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 300, color: 'var(--text-dim)', lineHeight: 1.7, margin: 0 }}>PDF · EPUB · TXT 三格式，涵盖古希腊至当代的中西方哲学经典。支持在线阅读、AI批注与笔记。</p>
          </div>
          <div onClick={() => navigate('/authors')} style={{ cursor: 'pointer', padding: '28px 24px', borderBottom: '2px solid var(--border)', transition: 'all 0.3s' }}
            onMouseEnter={e => { e.currentTarget.style.borderBottomColor = 'var(--prussian)'; e.currentTarget.style.background = 'var(--card-bg)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderBottomColor = 'var(--border)'; e.currentTarget.style.background = 'transparent'; }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--prussian)' }}>Philosophers</span>
            <h2 style={{ fontFamily: '"Playfair Display",serif', fontSize: 24, fontWeight: 400, color: 'var(--ink)', margin: '6px 0 8px', letterSpacing: '0.03em' }}>355 位哲学家</h2>
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 300, color: 'var(--text-dim)', lineHeight: 1.7, margin: 0 }}>从柏拉图到尼采，从孔子到牟宗三。每位哲学家配备千字思想剖析与Wikipedia链接。</p>
          </div>
        </div>
      </section>

      {/* ══════════ TIMELINE — dual-sided ══════════ */}
      <div id="genealogy-timeline" style={{ maxWidth: '100%', margin: '0 auto', position: 'relative', padding: '48px 24px 40px' }}>
        <h2 style={{ textAlign: 'center', fontFamily: '"Playfair Display",serif', fontSize: 24, fontWeight: 400, color: 'var(--ink)', marginBottom: 40, letterSpacing: '0.04em' }}>思想史时间轴</h2>
        <div style={{ position: 'absolute', left: '50%', top: 120, bottom: 40, width: 1,
          background: 'linear-gradient(to bottom, transparent 0%, var(--border) 10%, var(--border) 90%, transparent 100%)',
          transform: 'translateX(-50%)' }} />

        {(() => {
          const allEras = [];
          const eastMap = {}, westMap = {};
          EASTERN_TIMELINE.forEach(e => { eastMap[e.century] = e.schools; });
          WESTERN_TIMELINE.forEach(e => { westMap[e.century] = e.schools; });
          const centuries = [...new Set([...Object.keys(eastMap), ...Object.keys(westMap)])];
          centuries.sort((a,b) => {
            const parse = (s) => {
              const bce = s.includes('公元前');
              const nums = s.match(/\d+/g);
              const n = nums ? parseInt(nums[0]) : 0;
              let sub = 0;
              if (s.includes('初')) sub = 0;
              else if (s.includes('中')) sub = 1;
              else if (s.includes('末')) sub = 2;
              return { bce, n, sub };
            };
            const pa = parse(a), pb = parse(b);
            if (pa.bce && !pb.bce) return -1;
            if (!pa.bce && pb.bce) return 1;
            if (pa.bce && pb.bce) return pb.n - pa.n || pa.sub - pb.sub;
            return pa.n - pb.n || pa.sub - pb.sub;
          });
          centuries.forEach(c => { allEras.push({ century: c, east: eastMap[c] || [], west: westMap[c] || [] }); });
          let eastIdx = 0, westIdx = 0;

          return allEras.map((era, eraIdx) => {
            const hasEast = era.east.length > 0, hasWest = era.west.length > 0;
            return (
              <div key={eraIdx} style={{ display: 'flex', marginBottom: 48, position: 'relative' }}>
                <div style={{ flex: 1, paddingRight: 28, display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                  {hasEast && era.east.map((school, si) => {
                    const color = EASTERN_COLORS[(eastIdx + si) % EASTERN_COLORS.length];
                    return (
                      <div key={school} onClick={() => navigate('/school/' + encodeURIComponent(school))}
                        style={{ maxWidth: 360, marginBottom: 8, cursor: 'pointer', textAlign: 'right', padding: '12px 18px', borderRight: '3px solid ' + color, transition: 'all 0.25s', background: 'transparent' }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'var(--card-bg)'; }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
                        <h3 style={{ fontFamily: '"Playfair Display","PingFang SC",serif', fontSize: 16, fontWeight: 500, color: 'var(--ink)', margin: '0 0 3px', letterSpacing: '0.03em' }}>{school}</h3>
                        {EASTERN_DESCRIPTIONS[school] && <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: 300, color: 'var(--text-dim)', margin: 0, lineHeight: 1.6 }}>{EASTERN_DESCRIPTIONS[school]}</p>}
                      </div>
                    );
                  })}
                  {hasEast && (() => { eastIdx += era.east.length; })()}
                </div>
                <div style={{ width: 56, flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', zIndex: 2, background: 'var(--bone)', border: '2px solid var(--ochre)' }} />
                  <span style={{ fontFamily: '"Playfair Display",serif', fontSize: 11, fontWeight: 500, color: 'var(--ochre)', marginTop: 8, textAlign: 'center', whiteSpace: 'nowrap', letterSpacing: '0.05em' }}>{era.century}</span>
                </div>
                <div style={{ flex: 1, paddingLeft: 28 }}>
                  {hasWest && era.west.map((school, si) => {
                    const color = SCHOOL_COLORS[(westIdx + si) % SCHOOL_COLORS.length];
                    return (
                      <div key={school} onClick={() => navigate('/school/' + encodeURIComponent(school))}
                        style={{ maxWidth: 360, marginBottom: 8, cursor: 'pointer', padding: '12px 18px', borderLeft: '3px solid ' + color, transition: 'all 0.25s', background: 'transparent' }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'var(--card-bg)'; }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
                        <h3 style={{ fontFamily: '"Playfair Display","PingFang SC",serif', fontSize: 16, fontWeight: 500, color: 'var(--ink)', margin: '0 0 3px', letterSpacing: '0.03em' }}>{school}</h3>
                        {SCHOOL_DESCRIPTIONS[school] && <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: 300, color: 'var(--text-dim)', margin: 0, lineHeight: 1.6 }}>{SCHOOL_DESCRIPTIONS[school]}</p>}
                      </div>
                    );
                  })}
                  {hasWest && (() => { westIdx += era.west.length; })()}
                </div>
              </div>
            );
          });
        })()}
      </div>

      {/* ══════════ FOOTER ══════════ */}
      <div style={{ textAlign: 'center', paddingBottom: 40 }}>
        <button onClick={() => navigate('/world-philosophies')} style={{
          fontFamily: '"Playfair Display",serif', fontSize: 15, fontWeight: 400, color: 'var(--ochre)', letterSpacing: '0.04em',
          background: 'none', border: 'none', cursor: 'pointer', padding: '8px 16px', transition: 'opacity 0.2s'
        }}
          onMouseEnter={e => e.currentTarget.style.opacity = '0.6'}
          onMouseLeave={e => e.currentTarget.style.opacity = '1'}>
          世界哲学传统 →
        </button>
      </div>
    </div>
  );
}

export default HomePage;