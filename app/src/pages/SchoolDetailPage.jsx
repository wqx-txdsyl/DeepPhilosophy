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
const SUB_COLORS = {
  '米利都学派':'#C4956A','前苏格拉底':'#B8875E','埃利亚学派':'#AC7A52',
  '多元论':'#A06D46','古希腊哲学':'#94603A','柏拉图学派':'#88532E',
  '犬儒学派':'#7C4622','逍遥学派':'#703916','怀疑论':'#642C0A',
  '伊壁鸠鲁学派':'#6B3820','斯多葛学派':'#3A5A7C','新柏拉图主义':'#2E4A6A',
};

function SchoolDetailPage() {
  const { name } = useParams();
  const navigate = useNavigate();
  // Sub-school filter: only apply if name is a known sub-school
  const subNames = [...new Set(GREEK_DATA.thinkers.map(t => t.sub))];
  const isSubSchool = subNames.includes(name);
  const data = isSubSchool ? {
    ...GREEK_DATA,
    name,
    thinkers: GREEK_DATA.thinkers.filter(t => t.sub === name),
    relations: GREEK_DATA.relations.filter(r =>
      GREEK_DATA.thinkers.find(t => t.name === r.from && t.sub === name) &&
      GREEK_DATA.thinkers.find(t => t.name === r.to && t.sub === name)
    ),
  } : GREEK_DATA;
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
        {[
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
          <div key={sub.name} onClick={() => navigate(`/school/${encodeURIComponent(sub.name)}`)} style={{
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
          {[
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
