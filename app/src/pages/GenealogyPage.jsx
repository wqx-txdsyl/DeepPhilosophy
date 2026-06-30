/**
 * 哲学之河 V4 — Collage Museum
 * School images as backgrounds. Cards = stickers pasted on.
 * Two intertwined curves rotate with scroll.
 */
import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

const ALL_SCHOOLS = [
  { century:'公元前30世纪', name:'古希伯来哲学', region:'世界', desc:'约伯、传道书与智慧文学——信仰、苦难与神圣正义的追问。', tier:'A' },
  { century:'公元前30世纪', name:'古埃及哲学', region:'世界', desc:'玛阿特——宇宙秩序、真理与正义的永恒法则。', tier:'A' },
  { century:'公元前30世纪', name:'美索不达米亚哲学', region:'世界', desc:'苏美尔智慧文学追问苦难与秩序——人类最早的哲学追问。', tier:'A' },
  { century:'公元前15世纪', name:'印度哲学', region:'世界', desc:'《吠陀》《奥义书》为源头，六派哲学追问解脱。', tier:'A' },
  { century:'公元前15世纪', name:'犹太哲学', region:'世界', desc:'从斐洛到列维纳斯——雅典与耶路撒冷之间。', tier:'B' },
  { century:'公元前10世纪', name:'波斯哲学', region:'世界', desc:'琐罗亚斯德教善恶二元论——两千五百年的连续传统。', tier:'B' },
  { century:'公元前6世纪', name:'凯尔特哲学', region:'世界', desc:'德鲁伊传统与凯尔特智慧——自然、灵魂转世与森林中的哲学。', tier:'B' },
  { century:'公元前6世纪', name:'道家', region:'东方', desc:'道法自然，无为而治。', tier:'A' },
  { century:'公元前6世纪', name:'儒家', region:'东方', desc:'以仁为核心，以礼为规范。', tier:'A' },
  { century:'公元前6世纪', name:'古希腊哲学', region:'世界', desc:'西方哲学总源——以理性思辨取代神话解释。', tier:'A' },
  { century:'公元前5世纪', name:'墨家', region:'东方', desc:'兼爱非攻，尚贤节用。', tier:'B' },
  { century:'公元前5世纪', name:'兵家', region:'东方', desc:'知己知彼，不战屈人。', tier:'B' },
  { century:'公元前4世纪', name:'法家', region:'东方', desc:'以法治国，不别亲疏。', tier:'B' },
  { century:'公元前4世纪', name:'名家', region:'东方', desc:'白马非马——中国最早的逻辑学。', tier:'C' },
  { century:'公元前4世纪', name:'阴阳家', region:'东方', desc:'阴阳消长，五德终始。', tier:'C' },
  { century:'公元前1世纪', name:'罗马哲学', region:'世界', desc:'西塞罗、塞内卡、马可·奥勒留——斯多葛与伊壁鸠鲁在帝国的实践。', tier:'A' },
  { century:'公元前2世纪', name:'两汉经学', region:'东方', desc:'通经致用，以经为法。', tier:'B' },
  { century:'3世纪', name:'魏晋玄学', region:'东方', desc:'越名教而任自然。', tier:'B' },
  { century:'4世纪', name:'拜占庭哲学', region:'世界', desc:'东罗马帝国的神学哲学传统——伪狄奥尼修斯与拜占庭智慧。', tier:'B' },
  { century:'4世纪', name:'教父哲学', region:'西方', desc:'以希腊理性为基督教信仰奠基。', tier:'A' },
  { century:'6世纪', name:'隋唐佛学', region:'东方', desc:'八宗竞秀，会通中印。', tier:'A' },
  { century:'7世纪', name:'伊斯兰哲学', region:'世界', desc:'凯拉姆与苏非——理性与启示的对话。', tier:'A' },
  { century:'7世纪', name:'阿拉伯哲学', region:'世界', desc:'铿迪、法拉比、阿维森纳——中世纪哲学桥梁。', tier:'A' },
  { century:'8世纪', name:'西藏哲学', region:'世界', desc:'宗喀巴体系——藏传佛教中观应成派。', tier:'B' },
  { century:'11世纪', name:'宋明理学', region:'东方', desc:'为天地立心，为生民立命。', tier:'A' },
  { century:'11世纪', name:'经院哲学', region:'西方', desc:'以亚里士多德逻辑构建理性圣殿。', tier:'A' },
  { century:'11世纪', name:'唯名论', region:'西方', desc:'共相只是名称不是实在。', tier:'C' },
  { century:'13世纪', name:'印加哲学', region:'世界', desc:'帕查与艾尼——安第斯的宇宙时空与互惠伦理。', tier:'B' },
  { century:'13世纪', name:'非洲哲学', region:'世界', desc:'乌班图与去殖民化。', tier:'A' },
  { century:'15世纪', name:'拉丁美洲哲学', region:'世界', desc:'从拉斯·卡萨斯到杜塞尔——解放的哲学。', tier:'A' },
  { century:'15世纪', name:'玛雅哲学', region:'世界', desc:'《波波尔·乌》——循环时间观与玉米人。', tier:'B' },
  { century:'15世纪', name:'阿兹特克哲学', region:'世界', desc:'第五太阳纪——花与歌的哲学回应。', tier:'B' },
  { century:'16世纪', name:'东南亚哲学', region:'世界', desc:'上座部佛教与本土智慧的交融。', tier:'B' },
  { century:'16世纪', name:'韩国哲学', region:'世界', desc:'性理学与实学——从四端七情到主体思想。', tier:'B' },
  { century:'17世纪', name:'明清实学', region:'东方', desc:'经世致用，实事求是。', tier:'B' },
  { century:'17世纪', name:'乾嘉朴学', region:'东方', desc:'无征不信，孤证不立。', tier:'C' },
  { century:'17世纪', name:'理性主义', region:'西方', desc:'以数学公理为范本。', tier:'A' },
  { century:'17世纪', name:'经验主义', region:'西方', desc:'一切知识起源于感觉经验。', tier:'A' },
  { century:'18世纪', name:'启蒙运动', region:'西方', desc:'敢于运用你自己的理性。', tier:'A' },
  { century:'18世纪', name:'实在论', region:'西方', desc:'存在独立于心灵。', tier:'B' },
  { century:'18世纪', name:'唯心主义', region:'西方', desc:'实在的本质是精神或观念。', tier:'B' },
  { century:'18世纪', name:'自由主义', region:'西方', desc:'个人自由是最高政治价值。', tier:'B' },
  { century:'18世纪', name:'浪漫主义', region:'西方', desc:'以情感和想象反抗启蒙理性。', tier:'C' },
  { century:'19世纪', name:'德国古典哲学', region:'西方', desc:'从康德到黑格尔的哲学革命。', tier:'A' },
  { century:'19世纪', name:'功利主义', region:'西方', desc:'最大多数人的最大幸福。', tier:'B' },
  { century:'19世纪', name:'超验主义', region:'西方', desc:'美国精神独立宣言。', tier:'C' },
  { century:'19世纪', name:'实证主义', region:'西方', desc:'只问如何不问为何。', tier:'B' },
  { century:'19世纪', name:'马克思主义', region:'西方', desc:'问题在于改变世界。', tier:'A' },
  { century:'19世纪', name:'生命哲学', region:'西方', desc:'理性不能穷尽生命。', tier:'C' },
  { century:'19世纪', name:'社会学', region:'西方', desc:'追问社会何以可能。', tier:'B' },
  { century:'19世纪', name:'北欧哲学', region:'世界', desc:'克尔凯郭尔的信仰跳跃。', tier:'B' },
  { century:'19世纪', name:'东欧斯拉夫哲学', region:'世界', desc:'索洛维约夫、舍斯托夫——第三条道路。', tier:'B' },
  { century:'19世纪', name:'北美哲学', region:'世界', desc:'实用主义与超验主义。', tier:'B' },
  { century:'19世纪', name:'黑人哲学', region:'世界', desc:'从废奴运动到黑权运动——双重意识、种族批判与黑人存在主义的全球哲学传统。', tier:'B' },
  { century:'19世纪末', name:'天演论', region:'东方', desc:'物竞天择，适者生存。', tier:'C' },
  { century:'19世纪末', name:'维新派', region:'东方', desc:'变则通，通则久。', tier:'C' },
  { century:'20世纪初', name:'实用主义', region:'西方', desc:'真理即有用，意义在于效果。', tier:'B' },
  { century:'20世纪初', name:'精神分析学', region:'西方', desc:'心灵深处有一个你不知道的你。', tier:'B' },
  { century:'20世纪初', name:'现象学', region:'西方', desc:'回到事物本身。', tier:'A' },
  { century:'20世纪初', name:'存在主义', region:'西方', desc:'存在先于本质。', tier:'A' },
  { century:'20世纪初', name:'分析哲学', region:'西方', desc:'全部哲学就是语言的批判。', tier:'A' },
  { century:'20世纪初', name:'过程哲学', region:'西方', desc:'实在是生成而非存在。', tier:'C' },
  { century:'20世纪初', name:'哲学人类学', region:'西方', desc:'人是什么。', tier:'C' },
  { century:'20世纪初', name:'三民主义', region:'东方', desc:'民族、民权、民生。', tier:'C' },
  { century:'20世纪初', name:'旧民主主义', region:'东方', desc:'探索民主共和道路。', tier:'C' },
  { century:'20世纪', name:'解放哲学', region:'世界', desc:'从解放神学到巴西解放教育学——哲学为被压迫者发声。', tier:'A' },
  { century:'20世纪中', name:'西方马克思主义', region:'西方', desc:'回到黑格尔的马克思。', tier:'B' },
  { century:'20世纪中', name:'法兰克福学派', region:'西方', desc:'工具理性已沦为新的统治形式。', tier:'B' },
  { century:'20世纪中', name:'批判理论', region:'西方', desc:'传统理论描述世界，批判理论旨在解放。', tier:'B' },
  { century:'20世纪中', name:'科学哲学', region:'西方', desc:'科学何以成为科学。', tier:'B' },
  { century:'20世纪中', name:'荒诞哲学', region:'西方', desc:'世界没有意义，但人必须活下去。', tier:'B' },
  { century:'20世纪中', name:'基督教哲学', region:'西方', desc:'信仰在理性中追问自身。', tier:'C' },
  { century:'20世纪中', name:'结构主义', region:'西方', desc:'意义在关系之中。', tier:'B' },
  { century:'20世纪中', name:'政治哲学', region:'西方', desc:'追问正义、权力与自由。', tier:'B' },
  { century:'20世纪中', name:'哲学诠释学', region:'西方', desc:'理解是存在方式。', tier:'C' },
  { century:'20世纪中', name:'毛泽东思想', region:'东方', desc:'实事求是，群众路线。', tier:'B' },
  { century:'20世纪中', name:'中国马克思主义哲学', region:'东方', desc:'辩证唯物主义的中国化。', tier:'B' },
  { century:'20世纪中', name:'新民主主义', region:'东方', desc:'革命分两步走。', tier:'C' },
  { century:'20世纪末', name:'解构主义', region:'西方', desc:'德里达的解构——文字、意义与权力的边缘。', tier:'B' },
  { century:'20世纪末', name:'后结构主义', region:'西方', desc:'解构逻各斯中心主义。', tier:'B' },
  { century:'20世纪末', name:'后现代主义', region:'西方', desc:'对宏大叙事的怀疑。', tier:'B' },
  { century:'20世纪末', name:'伦理学', region:'西方', desc:'追问人应该如何生活。', tier:'B' },
  { century:'20世纪末', name:'环境哲学', region:'世界', desc:'人类与自然的伦理关系——深层生态学、生态女性主义与环境正义。', tier:'B' },
  { century:'20世纪末', name:'宗教哲学', region:'西方', desc:'以理性审视信仰。', tier:'C' },
  { century:'20世纪末', name:'后殖民哲学', region:'世界', desc:'法农、萨义德、斯皮瓦克——殖民经验的哲学批判与去殖民化思想。', tier:'B' },
  { century:'20世纪末', name:'女性主义', region:'西方', desc:'个人的即政治的。', tier:'B' },
  { century:'20世纪末', name:'原住民哲学', region:'世界', desc:'全球原住民的生态智慧与土地伦理——从澳大利亚到亚马逊。', tier:'B' },
  { century:'20世纪末', name:'社群主义', region:'西方', desc:'自我镶嵌于共同体之中。', tier:'C' },
  { century:'20世纪末', name:'现代新儒家', region:'东方', desc:'返本开新，内圣外王。', tier:'B' },
  { century:'20世纪末', name:'中国实证哲学', region:'东方', desc:'大胆假设，小心求证。', tier:'C' },
  { century:'20世纪末', name:'马克思主义哲学的中国化与体系化', region:'东方', desc:'实践标准到理论体系。', tier:'C' },
  { century:'20世纪末', name:'蒙古中亚哲学', region:'世界', desc:'萨满传统与长生天。', tier:'C' },
  { century:'20世纪末', name:'澳洲原住民哲学', region:'世界', desc:'梦时代——最古老文明的生命智慧。', tier:'B' },
  { century:'21世纪', name:'技术哲学', region:'西方', desc:'技术不是中立的工具。', tier:'B' },
  { century:'21世纪', name:'习近平新时代中国特色社会主义思想', region:'东方', desc:'以人民为中心的发展思想。', tier:'C' },
];

const REGION_COLORS = { '西方': '#917647', '东方': '#3A5A7C', '世界': '#5A8A5A' };

// Pre-compute rotation angles per exhibit (deterministic pseudo-random, stable across renders)
const ROTATIONS = ALL_SCHOOLS.map((_, i) => ((i * 7 + 3) % 5 - 2) * 0.8); // -1.6 to +1.6 deg

const ERAS = [
  { name:'Ancient World', title:'远古文明', range:'公元前30世纪 — 公元前10世纪', era:'era_ancient' },
  { name:'Classical Antiquity', title:'古典时代', range:'公元前6世纪 — 4世纪', era:'era_greece' },
  { name:'Middle Ages', title:'中世纪', range:'6世纪 — 16世纪', era:'era_medieval' },
  { name:'Renaissance & Early Modern', title:'文艺复兴与近代', range:'17世纪 — 18世纪', era:'era_renaissance' },
  { name:'Modern Philosophy', title:'现代哲学', range:'19世纪 — 20世纪中', era:'era_modern' },
  { name:'Contemporary', title:'当代', range:'20世纪末 — 21世纪', era:'era_modern' },
];

function getEraIndex(i) {
  const c = ALL_SCHOOLS[i].century;
  if (c.includes('公元前30') || c.includes('公元前15') || c.includes('公元前10')) return 0;
  if (c.includes('公元前6') || c.includes('公元前5') || c.includes('公元前4') || c.includes('公元前2') || c.includes('公元前1') || c === '3世纪' || c === '4世纪') return 1;
  if (c === '6世纪' || c === '7世纪' || c === '8世纪' || c === '11世纪' || c === '13世纪' || c === '15世纪' || c === '16世纪') return 2;
  if (c === '17世纪' || c === '18世纪') return 3;
  if (c.includes('19世纪') || c.includes('20世纪初') || c === '20世纪' || c.includes('20世纪中')) return 4;
  return 5;
}

// --- Sticker Exhibit ---
function Exhibit({ school, index, isLeft, isActive, onClick, onHover, onLeave }) {
  const color = REGION_COLORS[school.region];
  const rot = ROTATIONS[index];
  const tierW = school.tier === 'A' ? 400 : school.tier === 'B' ? 320 : 260;
  const tierF = school.tier === 'A' ? 20 : school.tier === 'B' ? 15 : 13;
  const imgExt = school.name.includes('凯尔特') || school.name.includes('原住民') || school.name.includes('希伯来') || school.name.includes('罗马') || school.name.includes('拜占庭') || school.name.includes('解放') || school.name.includes('后殖民') || school.name.includes('环境') || school.name.includes('解构') || school.name.includes('黑人') || school.name.includes('希腊') ? '.jpg' : '.png';

  return (
    <div style={{
      display:'flex', justifyContent: isLeft ? 'flex-start' : 'flex-end',
      marginBottom: school.tier === 'A' ? 72 : school.tier === 'B' ? 48 : 32,
      paddingLeft: isLeft ? '2%' : 'calc(50% + 40px)',
      paddingRight: isLeft ? 'calc(50% + 40px)' : '2%',
      position:'relative',
    }}>
      {/* Central timeline dot — small, subtle */}
      <div style={{
        position:'absolute', left:'50%', top:'50%', transform:'translate(-50%,-50%)',
        width:5, height:5, borderRadius:'50%', background:color, opacity:0.3, zIndex:2
      }} />

      {/* Sticker card with school image background */}
      <div
        onClick={() => onClick(school.name)}
        onMouseEnter={() => onHover(index)}
        onMouseLeave={onLeave}
        style={{
          maxWidth: tierW, width:'100%', cursor:'pointer',
          borderRadius: 12,
          transform: isActive ? `rotate(${rot * 0.3}deg) scale(1.02)` : `rotate(${rot}deg)`,
          transition: 'all 450ms cubic-bezier(0.33, 0, 0.1, 1)',
          position:'relative', zIndex: isActive ? 5 : 1,
          boxShadow: isActive
            ? '0 4px 16px rgba(42,31,26,0.12), 0 8px 32px rgba(42,31,26,0.06)'
            : '0 1px 4px rgba(42,31,26,0.06)',
          overflow:'hidden',
        }}
      >
        {/* School image background — softened, fully visible */}
        <div style={{
          position:'absolute', inset:0,
          backgroundImage:`url(/schools/${encodeURI(school.name)}${imgExt})`,
          backgroundSize:'cover', backgroundPosition:'center',
          opacity:0.25, filter:'blur(0.5px)',
        }} />

        {/* Text overlay on semi-transparent paper */}
        <div style={{
          position:'relative',
          background: 'linear-gradient(180deg, rgba(252,250,246,0.88) 0%, rgba(248,244,237,0.92) 100%)',
          padding: school.tier === 'A' ? '22px 26px' : '14px 20px',
        }}>
          <div style={{
            fontSize:8, fontWeight:400, letterSpacing:'0.16em', textTransform:'uppercase',
            color, marginBottom: school.tier === 'A' ? 8 : 5,
            fontFamily:'var(--font-sans)', opacity:0.7
          }}>
            {school.region === '东方' ? 'Eastern' : school.region === '西方' ? 'Western' : 'World'}  ·  {school.century}
          </div>
          <h3 style={{
            fontSize:tierF, fontWeight:500, color:'#2A1F1A', margin:'0 0 4px',
            letterSpacing:'0.02em', lineHeight:1.3,
            fontFamily:'"Playfair Display", "PingFang SC", serif'
          }}>{school.name}</h3>
          <p style={{
            fontSize:11, fontWeight:300, color:'#7A6E64', lineHeight:1.7, margin:0,
            fontFamily:'var(--font-sans)'
          }}>{school.desc}</p>
        </div>
      </div>
    </div>
  );
}

// --- Era Chapter Marker ---
function EraMarker({ era }) {
  return (
    <div style={{ textAlign:'center', padding:'100px 24px 64px', position:'relative', zIndex:1 }}>
      <div style={{ width:80, height:1, background:'linear-gradient(to right, transparent, #91764740, transparent)', margin:'0 auto 32px' }} />
      <img src={`/schools/${era.era}.png`} alt="" loading="lazy"
        style={{ height:180, width:'auto', opacity:0.45, marginBottom:24, objectFit:'contain' }} />
      <p style={{ fontSize:10, fontWeight:400, letterSpacing:'0.28em', textTransform:'uppercase', color:'#917647', marginBottom:10, fontFamily:'var(--font-sans)' }}>{era.name}</p>
      <h2 style={{ fontSize:'clamp(1.4rem,2.5vw,1.8rem)', fontWeight:400, color:'#2A1F1A', margin:'0 0 4px', letterSpacing:'0.06em', fontFamily:'"Playfair Display","PingFang SC",serif' }}>{era.title}</h2>
      <p style={{ fontSize:12, fontWeight:300, color:'#A09080', fontFamily:'var(--font-sans)', margin:0 }}>{era.range}</p>
    </div>
  );
}

// --- Double Helix Curves SVG ---
function HelixCurves({ scrollY, totalHeight }) {
  if (totalHeight <= 0) return null;
  // Two sine waves 180° out of phase, rotation driven by scroll
  const rotation = scrollY * 0.03; // degrees
  return (
    <svg
      style={{
        position:'absolute', top:0, left:0, width:'100%', height:totalHeight,
        pointerEvents:'none', zIndex:0, overflow:'visible',
        transform:`rotate(${rotation}deg)`, transformOrigin:'center center',
      }}
      viewBox={`0 0 800 ${totalHeight}`}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id="curveGrad1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#917647" stopOpacity="0" />
          <stop offset="10%" stopColor="#917647" stopOpacity="0.12" />
          <stop offset="50%" stopColor="#917647" stopOpacity="0.18" />
          <stop offset="90%" stopColor="#917647" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#917647" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="curveGrad2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3A5A7C" stopOpacity="0" />
          <stop offset="10%" stopColor="#3A5A7C" stopOpacity="0.10" />
          <stop offset="50%" stopColor="#3A5A7C" stopOpacity="0.16" />
          <stop offset="90%" stopColor="#3A5A7C" stopOpacity="0.10" />
          <stop offset="100%" stopColor="#3A5A7C" stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* Curve 1 — bronze */}
      <path
        d={generateHelixPath(totalHeight, 0, 400, 120)}
        fill="none" stroke="url(#curveGrad1)" strokeWidth="2"
        opacity="0.5"
      />
      {/* Curve 2 — blue, 180° out of phase */}
      <path
        d={generateHelixPath(totalHeight, Math.PI, 400, 120)}
        fill="none" stroke="url(#curveGrad2)" strokeWidth="1.5"
        opacity="0.4"
      />
    </svg>
  );
}

function generateHelixPath(totalHeight, phaseOffset, centerX, amplitude) {
  const steps = Math.ceil(totalHeight / 60);
  let d = `M ${centerX - amplitude * Math.sin(phaseOffset)} 0`;
  for (let i = 0; i < steps; i++) {
    const y0 = i * 60;
    const y1 = (i + 1) * 60;
    const t0 = (y0 / totalHeight) * Math.PI * 16;
    const t1 = (y1 / totalHeight) * Math.PI * 16;
    const x0 = centerX + amplitude * Math.sin(t0 + phaseOffset);
    const x1 = centerX + amplitude * Math.sin(t1 + phaseOffset);
    // Cubic bezier control points for smooth sine wave
    const cp1x = centerX + amplitude * Math.sin(t0 + phaseOffset + 0.5);
    const cp1y = y0 + 30;
    const cp2x = centerX + amplitude * Math.sin(t1 + phaseOffset - 0.5);
    const cp2y = y1 - 30;
    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x1} ${y1}`;
  }
  return d;
}

// --- Main Page ---
export default function GenealogyPage() {
  const navigate = useNavigate();
  const [hoveredIdx, setHoveredIdx] = useState(null);
  const [scrollY, setScrollY] = useState(0);
  const [pageHeight, setPageHeight] = useState(0);
  const pageRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    // Measure page height after render
    const measure = () => {
      if (pageRef.current) setPageHeight(pageRef.current.scrollHeight);
    };
    measure();
    const timer = setInterval(measure, 500);
    return () => { window.removeEventListener('scroll', onScroll); clearInterval(timer); };
  }, []);

  // Era boundaries
  const eraGroups = useMemo(() => {
    const groups = [];
    let cur = -1;
    ALL_SCHOOLS.forEach((s, i) => {
      const ei = getEraIndex(i);
      if (ei !== cur) { cur = ei; groups.push({ era: ERAS[ei], startIdx: i }); }
    });
    return groups;
  }, []);

  return (
    <div ref={pageRef} style={{
      background:'#F4EFE6', minHeight:'100vh',
      fontFamily:'"Playfair Display","PingFang SC",serif', color:'#2A1F1A',
      position:'relative', overflow:'visible'
    }}>

      {/* ══════════ BACKGROUND COLLAGE ══════════ */}
      {/* z:-2  Solid base */}
      <div style={{ position:'fixed', inset:0, zIndex:-2,
        background:'linear-gradient(180deg, #F4EFE6 0%, #EDE5D8 35%, #E8DFD0 65%, #E0D8C8 100%)' }} />

      {/* z:-1  哲学星图 — distant thought-sphere, very faint */}
      <div style={{ position:'fixed', inset:0, zIndex:-1, pointerEvents:'none', opacity:0.08,
        backgroundImage:'url(/gene/哲学星图.png)',
        backgroundSize:'cover', backgroundPosition:'center' }} />

      {/* z:-1  philosophy_symbols — scattered civilization artifacts */}
      <div style={{ position:'fixed', inset:0, zIndex:-1, pointerEvents:'none', opacity:0.06,
        backgroundImage:'url(/gene/philosophy_symbols.png)',
        backgroundSize:'80%', backgroundPosition:'center', backgroundRepeat:'no-repeat' }} />

      {/* z:0  Mountains — top horizon */}
      <div style={{ position:'fixed', top:0, left:0, right:0, height:'45vh', zIndex:0, pointerEvents:'none', opacity:0.22,
        backgroundImage:'url(/gene/terrain/terrain_mountains.png)',
        backgroundSize:'cover', backgroundPosition:'center top' }} />

      {/* z:0  Valley — main river course through center */}
      <div style={{ position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.26,
        backgroundImage:'url(/gene/terrain/terrain_river_valley.png)',
        backgroundSize:'cover', backgroundPosition:'center' }} />

      {/* z:0  Forest — lower left */}
      <div style={{ position:'fixed', bottom:0, left:0, width:'55vw', height:'40vh', zIndex:0, pointerEvents:'none', opacity:0.14,
        backgroundImage:'url(/gene/terrain/terrain_forest.png)',
        backgroundSize:'cover', backgroundPosition:'left bottom' }} />

      {/* z:0  Plateau — lower right */}
      <div style={{ position:'fixed', bottom:0, right:0, width:'50vw', height:'35vh', zIndex:0, pointerEvents:'none', opacity:0.12,
        backgroundImage:'url(/gene/terrain/terrain_plateau.png)',
        backgroundSize:'cover', backgroundPosition:'right bottom' }} />

      {/* z:0  Desert — far bottom horizon */}
      <div style={{ position:'fixed', bottom:0, left:0, right:0, height:'20vh', zIndex:0, pointerEvents:'none', opacity:0.08,
        backgroundImage:'url(/gene/terrain/terrain_desert.png)',
        backgroundSize:'cover', backgroundPosition:'center bottom' }} />

      {/* z:0  Civilization Silhouette — anchors the bottom */}
      <div style={{ position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.13,
        backgroundImage:'url(/gene/civilization_silhouette.png)',
        backgroundSize:'120%', backgroundPosition:'center bottom' }} />

      {/* ══════════ HERO ══════════ */}
      <section style={{ minHeight:'85vh', display:'flex', flexDirection:'column',
        justifyContent:'center', alignItems:'center', textAlign:'center',
        position:'relative', zIndex:1, padding:'60px 32px' }}>
        <div style={{ position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)',
          width:'60vw', height:'50vh',
          background:'radial-gradient(ellipse, rgba(145,118,71,0.05) 0%, transparent 70%)', pointerEvents:'none' }} />
        <p style={{ fontSize:10, fontWeight:400, letterSpacing:'0.32em', textTransform:'uppercase',
          color:'#917647', marginBottom:32, fontFamily:'var(--font-sans)', opacity:0.8 }}>
          Museum of Philosophy  ·  Genealogy Wing</p>
        <h1 style={{ fontSize:'clamp(2.5rem,7vw,5rem)', fontWeight:400, fontStyle:'italic',
          color:'#2A1F1A', letterSpacing:'0.04em', lineHeight:1.15, marginBottom:24,
          fontFamily:'"Playfair Display","PingFang SC",serif' }}>哲学之河</h1>
        <div style={{ width:56, height:1.5, background:'#917647', marginBottom:28, opacity:0.45 }} />
        <p style={{ fontSize:'clamp(0.95rem,1.4vw,1.15rem)', fontWeight:300,
          color:'#8A7E74', lineHeight:2.0, maxWidth:580, fontFamily:'var(--font-sans)' }}>
          从公元前三十世纪至二十一世纪<br />九十五个哲学流派，一部横跨五千年的人类思想史长卷</p>
        <button onClick={() => document.getElementById('museum-gallery')?.scrollIntoView({ behavior:'smooth' })}
          style={{ marginTop:48, background:'none', border:'1px solid rgba(145,118,71,0.2)',
            borderRadius:8, padding:'12px 36px', fontSize:13, fontWeight:300,
            color:'#8A7E74', cursor:'pointer', letterSpacing:'0.08em',
            fontFamily:'var(--font-sans)', transition:'all 400ms ease' }}
          onMouseEnter={e => { e.currentTarget.style.borderColor='rgba(145,118,71,0.5)'; e.currentTarget.style.color='#917647'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor='rgba(145,118,71,0.2)'; e.currentTarget.style.color='#8A7E74'; }}>
          沿河而上  ·  进入展廊</button>
      </section>

      {/* ══════════ GALLERY ══════════ */}
      <div id="museum-gallery" style={{ position:'relative', zIndex:1, paddingBottom:120, maxWidth:1200, margin:'0 auto', padding:'0 24px' }}>
        {/* Double helix curves — positioned behind exhibits */}
        <HelixCurves scrollY={scrollY} totalHeight={pageHeight} />

        <div style={{ height:80 }} />

        {ALL_SCHOOLS.map((school, i) => {
          const eraStart = eraGroups.find(g => g.startIdx === i);
          const isLeft = i % 3 !== 1;
          return (
            <div key={i}>
              {eraStart && <EraMarker era={eraStart.era} />}
              <Exhibit school={school} index={i} isLeft={isLeft}
                isActive={hoveredIdx === i}
                onClick={(name) => navigate('/school/' + encodeURIComponent(name))}
                onHover={setHoveredIdx} onLeave={() => setHoveredIdx(null)} />
            </div>
          );
        })}
        <div style={{ height:120 }} />
      </div>

      {/* ══════════ FOOTER ══════════ */}
      <div style={{ textAlign:'center', paddingBottom:80, position:'relative', zIndex:1,
        display:'flex', justifyContent:'center', gap:48, flexWrap:'wrap' }}>
        {[
          { label:'西方哲学传统', sub:'Western Tradition', path:'/western-philosophies', color:REGION_COLORS['西方'] },
          { label:'东方哲学传统', sub:'Eastern Tradition', path:'/eastern-philosophies', color:REGION_COLORS['东方'] },
          { label:'世界哲学传统', sub:'World Traditions', path:'/world-philosophies', color:REGION_COLORS['世界'] },
        ].map(btn => (
          <button key={btn.path} onClick={() => navigate(btn.path)}
            style={{ background:'none', border:'none', cursor:'pointer', fontFamily:'"Playfair Display",serif',
              fontSize:16, fontWeight:400, color:btn.color, letterSpacing:'0.04em', padding:'12px 20px',
              transition:'all 300ms ease', opacity:0.7 }}
            onMouseEnter={e => { e.currentTarget.style.opacity='1'; e.currentTarget.style.letterSpacing='0.08em'; }}
            onMouseLeave={e => { e.currentTarget.style.opacity='0.7'; e.currentTarget.style.letterSpacing='0.04em'; }}>
            <div style={{ fontSize:10, fontWeight:400, letterSpacing:'0.2em', textTransform:'uppercase', marginBottom:6, opacity:0.6 }}>{btn.sub}</div>
            {btn.label}</button>
        ))}</div>
    </div>
  );
}
