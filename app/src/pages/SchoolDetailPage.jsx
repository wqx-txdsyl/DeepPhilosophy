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
    { year:'约前624', event:'泰勒斯出生', type:'birth' },
    { year:'约前585', event:'泰勒斯预言日食', type:'event' },
    { year:'约前546', event:'泰勒斯逝世；阿那克西曼德活跃', type:'death' },
    { year:'约前500', event:'赫拉克利特提出"逻各斯"概念', type:'idea' },
    { year:'约前480', event:'巴门尼德著《论自然》', type:'book' },
    { year:'约前399', event:'苏格拉底被判死刑', type:'death' },
    { year:'约前387', event:'柏拉图创立雅典学园', type:'event' },
    { year:'约前380', event:'柏拉图著《理想国》', type:'book' },
    { year:'约前335', event:'亚里士多德创立吕克昂学园', type:'event' },
    { year:'约前330', event:'亚里士多德著《形而上学》《尼各马可伦理学》', type:'book' },
    { year:'约前306', event:'伊壁鸠鲁创立"花园"学派', type:'event' },
    { year:'约前300', event:'斯多葛学派在雅典画廊创立', type:'event' },
    { year:'约前270', event:'伊壁鸠鲁逝世', type:'death' },
    { year:'约前155', event:'雅典三哲使团访罗马，希腊哲学传入罗马', type:'event' },
    { year:'约135', event:'爱比克泰德逝世', type:'death' },
    { year:'180', event:'马可·奥勒留逝世；斯多葛帝国时代终结', type:'death' },
    { year:'270', event:'普罗提诺逝世；新柏拉图主义为基督教神学铺路', type:'death' },
    { year:'529', event:'查士丁尼关闭雅典学园，古希腊哲学终结', type:'event' },
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

function SchoolDetailPage() {
  const { name } = useParams();
  const navigate = useNavigate();
  const data = GREEK_DATA; // 未来根据 name 动态加载
  const [hovered, setHovered] = useState(null);

  return (
    <div style={{ background: 'var(--bg)', color: 'var(--text)', fontFamily: '"Playfair Display","PingFang SC",serif' }}>

      {/* ====== Section 1: Hero ====== */}
      <div style={{
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
        justifyContent: 'center', alignItems: 'center', textAlign: 'center',
        padding: '40px 32px', position: 'relative',
        background: 'linear-gradient(135deg, #F4F0EB 0%, #E8E0D5 25%, #EDE7DD 50%, #F0E8DC 75%, #F4F0EB 100%)',
        overflow: 'hidden',
      }}>
        {/* Decorative elements */}
        <div style={{ position: 'absolute', top: -80, right: -60, width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(196,149,106,0.08) 0%, transparent 70%)' }} />
        <div style={{ position: 'absolute', bottom: -40, left: -40, width: 250, height: 250, borderRadius: '50%', background: 'radial-gradient(circle, rgba(58,90,124,0.06) 0%, transparent 70%)' }} />
        {/* Greek key pattern hint */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: 'repeating-linear-gradient(90deg, var(--ochre) 0px, var(--ochre) 12px, transparent 12px, transparent 20px)', opacity: 0.3 }} />
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 4, background: 'repeating-linear-gradient(90deg, var(--ochre) 0px, var(--ochre) 12px, transparent 12px, transparent 20px)', opacity: 0.3 }} />
        <div style={{ position: 'absolute', top: 4, bottom: 4, left: 0, width: 4, background: 'repeating-linear-gradient(0deg, var(--ochre) 0px, var(--ochre) 12px, transparent 12px, transparent 20px)', opacity: 0.3 }} />
        <div style={{ position: 'absolute', top: 4, bottom: 4, right: 0, width: 4, background: 'repeating-linear-gradient(0deg, var(--ochre) 0px, var(--ochre) 12px, transparent 12px, transparent 20px)', opacity: 0.3 }} />

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
        <div style={{ fontSize: 16, lineHeight: 2.0, color: 'var(--text)', whiteSpace: 'pre-line' }}>
          {data.overview}
        </div>
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
          width: '100%', maxWidth: 750, height: 550,
          position: 'relative', overflow: 'hidden',
        }}>
          {/* SVG lines */}
          <svg style={{ position: 'absolute', top:0, left:0, width:'100%', height:'100%' }}>
            {data.relations.map((r, i) => {
              const from = data.thinkers.find(t => t.name === r.from);
              const to = data.thinkers.find(t => t.name === r.to);
              if (!from || !to) return null;
              const fi = data.thinkers.indexOf(from);
              const ti = data.thinkers.indexOf(to);
              const fx = 90 + (fi % 4) * 170;
              const fy = 90 + Math.floor(fi / 4) * 120;
              const tx = 90 + (ti % 4) * 170;
              const ty = 90 + Math.floor(ti / 4) * 120;
              return (
                <g key={i}>
                  <line x1={fx} y1={fy} x2={tx} y2={ty}
                    stroke={r.type==='师生'?'var(--ochre)':r.type==='对立'?'#A06050':r.type==='继承'?'var(--prussian)':'#999'}
                    strokeWidth={1.2} strokeDasharray={r.type==='对立'?'5,4':''} opacity={0.4} />
                  <text x={(fx+tx)/2} y={(fy+ty)/2-6}
                    fontSize={9} fill="var(--text-dim)" textAnchor="middle" fontStyle="italic">
                    {r.type}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Thinker dots + labels */}
          {data.thinkers.map((t, i) => {
            const col = Math.floor(i / 4);
            const row = i % 4;
            const x = 90 + row * 170;
            const y = 90 + col * 120;
            const size = 18 + t.influence * 4;
            const isHovered = hovered === t.name;
            return (
              <div key={t.name} style={{
                position: 'absolute', left: x, top: y,
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
                  background: `radial-gradient(circle at 35% 35%, ${SUB_COLORS[t.sub]}dd, ${SUB_COLORS[t.sub]})`,
                  boxShadow: isHovered ? `0 0 20px ${SUB_COLORS[t.sub]}60` : '0 2px 6px rgba(0,0,0,0.1)',
                  transition: 'all 0.3s',
                  transform: isHovered ? 'scale(1.3)' : 'scale(1)',
                  animation: `pulse 3s ease-in-out ${i * 0.2}s infinite`,
                }} />
                <span style={{
                  fontSize: 10, color: 'var(--ink)', marginTop: 4,
                  fontWeight: isHovered ? 600 : 400,
                  maxWidth: 80, textAlign: 'center',
                  transition: 'all 0.3s',
                }}>
                  {t.name}
                </span>
                {isHovered && (
                  <div style={{
                    position: 'absolute', top: -60, left: '50%', transform: 'translateX(-50%)',
                    background: 'var(--primary)', border: '1px solid var(--border)',
                    borderRadius: 8, padding: '8px 14px', whiteSpace: 'nowrap',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
                  }}>
                    <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{t.sub} · {t.era}</div>
                    <div style={{ fontSize: 12, color: 'var(--ochre)', fontStyle: 'italic', marginTop: 2 }}>"{t.key}"</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ====== Section 4: Timeline ====== */}
      <div style={{
        minHeight: '100vh', padding: '40px 0', display: 'flex', flexDirection: 'column', justifyContent: 'center',
      }}>
        <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 32, paddingLeft: 40 }}>
          思想史时间轴
        </h2>

        {/* Horizontal scroll timeline */}
        <div style={{
          display: 'flex', overflowX: 'auto', gap: 0,
          padding: '40px 60px 40px 40px',
          position: 'relative',
        }}>
          {/* Horizontal line */}
          <div style={{
            position: 'absolute', top: 75, left: 60, right: 60, height: 2,
            background: 'var(--border)',
          }} />

          {data.timeline.map((ev, i) => {
            const isUp = i % 2 === 0;
            const icon = ev.type==='birth'?'👶':ev.type==='death'?'✝️':ev.type==='book'?'📖':ev.type==='idea'?'💡':'📜';
            const dotColor = ev.type==='birth'?'var(--ochre)':ev.type==='death'?'#A04040':ev.type==='book'?'var(--prussian)':ev.type==='idea'?'var(--success)':'var(--border)';
            return (
              <div key={i} style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                minWidth: 140, position: 'relative', flexShrink: 0,
              }}>
                {/* Content above/below */}
                <div style={{
                  height: 70, display: 'flex', flexDirection: 'column',
                  justifyContent: isUp ? 'flex-end' : 'flex-start',
                  textAlign: 'center', padding: '0 4px',
                  order: isUp ? 0 : 2,
                }}>
                  <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{ev.event}</span>
                </div>
                {/* Dot */}
                <div style={{
                  width: 14, height: 14, borderRadius: '50%', background: dotColor,
                  border: '2px solid var(--bg)', zIndex: 1,
                  order: 1,
                }} />
                {/* Year */}
                <div style={{
                  fontSize: 11, fontWeight: 600, color: 'var(--ochre)',
                  marginTop: 4, order: 3, textAlign: 'center',
                }}>
                  {ev.year}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ====== Section 5: Conclusion ====== */}
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
