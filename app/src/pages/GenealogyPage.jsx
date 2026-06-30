/**
 * 哲学之河 — Museum of Philosophy V3
 * VIS Part 05 Compliant: River = Timeline. Exhibits = Museum artifacts.
 * Scrolling = walking upstream through 5000 years of human thought.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
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
const REGION_GRADIENTS = {
  '西方': 'linear-gradient(135deg, rgba(145,118,71,0.12), rgba(145,118,71,0.04))',
  '东方': 'linear-gradient(135deg, rgba(58,90,124,0.10), rgba(58,90,124,0.03))',
  '世界': 'linear-gradient(135deg, rgba(90,138,90,0.10), rgba(90,138,90,0.03))',
};

// --- Museum Era Chapters (VIS §5.6) ---
const ERAS = [
  { name:'Ancient World', title:'远古文明', range:'公元前30世纪 — 公元前10世纪', era:'era_ancient' },
  { name:'Classical Antiquity', title:'古典时代', range:'公元前6世纪 — 4世纪', era:'era_greece' },
  { name:'Middle Ages', title:'中世纪', range:'6世纪 — 16世纪', era:'era_medieval' },
  { name:'Renaissance & Early Modern', title:'文艺复兴与近代', range:'17世纪 — 18世纪', era:'era_renaissance' },
  { name:'Modern Philosophy', title:'现代哲学', range:'19世纪 — 20世纪中', era:'era_modern' },
  { name:'Contemporary', title:'当代', range:'20世纪末 — 21世纪', era:'era_modern' },
];

// Map each school index to its era index
function getEraIndex(i) {
  const s = ALL_SCHOOLS[i];
  const c = s.century;
  if (c.includes('公元前30') || c.includes('公元前15') || c.includes('公元前10')) return 0;
  if (c.includes('公元前6') || c.includes('公元前5') || c.includes('公元前4') || c.includes('公元前2') || c.includes('公元前1') || c === '3世纪' || c === '4世纪') return 1;
  if (c === '6世纪' || c === '7世纪' || c === '8世纪' || c === '11世纪' || c === '13世纪' || c === '15世纪' || c === '16世纪') return 2;
  if (c === '17世纪' || c === '18世纪') return 3;
  if (c.includes('19世纪') || c.includes('20世纪初') || c === '20世纪' || c.includes('20世纪中')) return 4;
  return 5;
}

// --- Exhibit Component (VIS §13.4) ---
function Exhibit({ school, index, isLeft, isActive, onClick, onHover, onLeave }) {
  const color = REGION_COLORS[school.region];
  const tierSize = school.tier === 'A' ? 'exhibit-major' : school.tier === 'B' ? 'exhibit-standard' : 'exhibit-minor';
  const tierW = school.tier === 'A' ? 420 : school.tier === 'B' ? 340 : 270;
  const tierF = school.tier === 'A' ? 22 : school.tier === 'B' ? 16 : 14;

  return (
    <div className={`exhibit ${tierSize}`} style={{
      display:'flex', justifyContent: isLeft ? 'flex-start' : 'flex-end',
      marginBottom: school.tier === 'A' ? 80 : school.tier === 'B' ? 56 : 36,
      paddingLeft: isLeft ? 0 : 'calc(50% + 60px)',
      paddingRight: isLeft ? 'calc(50% + 60px)' : 0,
      position:'relative',
    }}>
      {/* River connector — subtle, no dots, no lines (VIS §5.2) */}
      <div style={{
        position:'absolute', left:'50%', top:'50%', transform:'translate(-50%,-50%)',
        width:6, height:6, borderRadius:'50%', background:color, opacity:0.35, zIndex:2,
        boxShadow:`0 0 12px ${color}20`
      }} />

      {/* Exhibit artifact (VIS §7.2: museum display case) */}
      <div
        onClick={() => onClick(school.name)}
        onMouseEnter={() => onHover(index)}
        onMouseLeave={onLeave}
        style={{
          background: isActive
            ? 'linear-gradient(180deg, rgba(253,251,247,0.98) 0%, rgba(248,244,237,0.96) 100%)'
            : 'linear-gradient(180deg, rgba(252,250,246,0.94) 0%, rgba(246,242,234,0.92) 100%)',
          border: isActive
            ? `1px solid rgba(145,118,71,0.28)`
            : '1px solid rgba(145,118,71,0.08)',
          borderRadius: 16,
          padding: school.tier === 'A' ? '24px 30px' : '16px 24px',
          maxWidth: tierW,
          width:'100%',
          cursor:'pointer',
          boxShadow: isActive
            ? '0 8px 32px rgba(42,31,26,0.06), 0 2px 4px rgba(42,31,26,0.03)'
            : '0 1px 3px rgba(42,31,26,0.02)',
          transform: isActive ? 'translateY(-2px) scale(1.01)' : 'none',
          transition: 'all 500ms cubic-bezier(0.33, 0, 0.1, 1)',
          position:'relative', zIndex: isActive ? 5 : 1,
        }}
      >
        {/* Top accent line on hover */}
        {isActive && (
          <div style={{
            position:'absolute', top:0, left:24, right:24, height:1.5,
            background:`linear-gradient(to right, transparent, ${color}40, transparent)`, borderRadius:2
          }} />
        )}

        {/* Region + Century annotation */}
        <div style={{
          fontSize:9, fontWeight:400, letterSpacing:'0.16em', textTransform:'uppercase',
          color, marginBottom: school.tier === 'A' ? 10 : 7,
          fontFamily:'var(--font-sans)', opacity:0.8
        }}>
          {school.region === '东方' ? 'Eastern' : school.region === '西方' ? 'Western' : 'World'}  ·  {school.century}
        </div>

        {/* School name */}
        <h3 style={{
          fontSize:tierF, fontWeight:500, color:'#2A1F1A', margin:'0 0 6px',
          letterSpacing:'0.02em', lineHeight:1.3,
          fontFamily:'"Playfair Display", "PingFang SC", serif'
        }}>{school.name}</h3>

        {/* Description */}
        <p style={{
          fontSize:12, fontWeight:300, color:'#7A6E64', lineHeight:1.8, margin:0,
          fontFamily:'var(--font-sans)'
        }}>{school.desc}</p>
      </div>
    </div>
  );
}

// --- Era Chapter Marker (VIS §5.7) ---
function EraMarker({ era, isVisible }) {
  return (
    <div style={{
      textAlign:'center', padding:'120px 24px 80px', position:'relative', zIndex:1,
      opacity: isVisible ? 1 : 0.3,
      transition: 'opacity 800ms ease',
    }}>
      <div style={{
        width:80, height:1, background:'linear-gradient(to right, transparent, #91764740, transparent)',
        margin:'0 auto 36px'
      }} />
      <img
        src={`/schools/${era.era}.png`}
        alt=""
        loading="lazy"
        style={{
          height:180, width:'auto', opacity:0.35, marginBottom:28,
          filter:'saturate(0.7) brightness(1.05)',
          objectFit:'contain'
        }}
      />
      <p style={{
        fontSize:10, fontWeight:400, letterSpacing:'0.28em', textTransform:'uppercase',
        color:'#917647', marginBottom:12, fontFamily:'var(--font-sans)'
      }}>{era.name}</p>
      <h2 style={{
        fontSize:'clamp(1.5rem,3vw,2rem)', fontWeight:400, color:'#2A1F1A',
        margin:'0 0 6px', letterSpacing:'0.06em',
        fontFamily:'"Playfair Display", "PingFang SC", serif'
      }}>{era.title}</h2>
      <p style={{
        fontSize:13, fontWeight:300, color:'#A09080', fontFamily:'var(--font-sans)', margin:0
      }}>{era.range}</p>
    </div>
  );
}

// --- Museum Gallery (main page) ---
export default function GenealogyPage() {
  const navigate = useNavigate();
  const [hoveredIdx, setHoveredIdx] = useState(null);
  const [scrollY, setScrollY] = useState(0);
  const pageRef = useRef(null);

  // Scroll tracking
  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Precompute era boundaries
  const eraGroups = [];
  let currentEra = -1;
  ALL_SCHOOLS.forEach((s, i) => {
    const ei = getEraIndex(i);
    if (ei !== currentEra) {
      currentEra = ei;
      eraGroups.push({ era: ERAS[ei], startIdx: i });
    }
  });

  return (
    <div ref={pageRef} style={{
      background:'#F4EFE6', minHeight:'100vh',
      fontFamily:'"Playfair Display","PingFang SC",serif', color:'#2A1F1A',
      position:'relative', overflow:'visible'
    }}>

      {/* ══════════ LAYER 1: Paper Texture ══════════ */}
      <div style={{
        position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.12,
        backgroundImage:'url(/gene/textures/texture_parchment.png)',
        backgroundSize:'400px', mixBlendMode:'multiply'
      }} />

      {/* ══════════ LAYER 2: Old Map Texture ══════════ */}
      <div style={{
        position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.08,
        backgroundImage:'url(/gene/textures/texture_old_map.png)',
        backgroundSize:'cover', backgroundPosition:'center', mixBlendMode:'multiply'
      }} />

      {/* ══════════ LAYER 3: Terrain — valley landscape ══════════ */}
      <div style={{
        position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.22,
        backgroundImage:'url(/gene/terrain/terrain_river_valley.png)',
        backgroundSize:'cover', backgroundPosition:'center',
        mixBlendMode:'multiply',
        maskImage:'linear-gradient(to bottom, black 0%, black 85%, transparent 100%)',
        WebkitMaskImage:'linear-gradient(to bottom, black 0%, black 85%, transparent 100%)'
      }} />

      {/* ══════════ LAYER 4: Civilization Silhouette ══════════ */}
      <div style={{
        position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.10,
        backgroundImage:'url(/gene/civilization_silhouette.png)',
        backgroundSize:'120%', backgroundPosition:'center bottom',
        mixBlendMode:'multiply',
        maskImage:'linear-gradient(to top, black 30%, transparent 100%)',
        WebkitMaskImage:'linear-gradient(to top, black 30%, transparent 100%)'
      }} />

      {/* ══════════ LAYER 5: River of Philosophy — central spine ══════════ */}
      <div style={{
        position:'fixed', top:0, bottom:0, left:'50%', transform:'translateX(-50%)',
        width:'clamp(260px, 30vw, 400px)', zIndex:0, pointerEvents:'none'
      }}>
        <img src={"/gene/river/" + encodeURI("哲学之河2.0.png")} alt="" style={{
          width:'100%', height:'100%',
          objectFit:'cover', objectPosition:'center',
          opacity:0.45,
          maskImage:'linear-gradient(to right, transparent 0%, rgba(0,0,0,0.6) 10%, rgba(0,0,0,0.85) 50%, rgba(0,0,0,0.6) 90%, transparent 100%)',
          WebkitMaskImage:'linear-gradient(to right, transparent 0%, rgba(0,0,0,0.6) 10%, rgba(0,0,0,0.85) 50%, rgba(0,0,0,0.6) 90%, transparent 100%)'
        }} />
      </div>

      {/* ══════════ LAYER 6: Atmosphere — Mist ══════════ */}
      <div style={{
        position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.14,
        backgroundImage:'url(/gene/atmosphere/effect_mist.png)',
        backgroundSize:'cover', backgroundPosition:'center',
        mixBlendMode:'screen'
      }} />

      {/* ══════════ LAYER 7: Golden Dust ══════════ */}
      <div style={{
        position:'fixed', inset:0, zIndex:0, pointerEvents:'none', opacity:0.07,
        backgroundImage:'url(/gene/gold_particles.png)',
        backgroundSize:'cover', backgroundPosition:'center',
        animation:'museum-drift 60s linear infinite',
        mixBlendMode:'screen'
      }} />

      {/* ══════════ LAYER 8: God Rays — Hero only ══════════ */}
      <div style={{
        position:'absolute', top:0, left:0, right:0, height:'100vh', zIndex:0, pointerEvents:'none',
        opacity:0.12,
        backgroundImage:'url(/gene/atmosphere/effect_god_rays.png)',
        backgroundSize:'cover', backgroundPosition:'center top',
        mixBlendMode:'screen'
      }} />

      {/* ══════════ HERO — Museum Entrance (VIS §4.2, §5.3) ══════════ */}
      <section style={{
        minHeight:'90vh', display:'flex', flexDirection:'column',
        justifyContent:'center', alignItems:'center', textAlign:'center',
        position:'relative', zIndex:1, padding:'60px 32px'
      }}>
        {/* Warm glow behind hero */}
        <div style={{
          position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)',
          width:'60vw', height:'50vh',
          background:'radial-gradient(ellipse, rgba(145,118,71,0.06) 0%, transparent 70%)',
          pointerEvents:'none'
        }} />

        <p style={{
          fontSize:10, fontWeight:400, letterSpacing:'0.32em', textTransform:'uppercase',
          color:'#917647', marginBottom:32, fontFamily:'var(--font-sans)', opacity:0.85
        }}>Museum of Philosophy  ·  Genealogy Wing</p>

        <h1 style={{
          fontSize:'clamp(2.5rem, 7vw, 5rem)', fontWeight:400, fontStyle:'italic',
          color:'#2A1F1A', letterSpacing:'0.04em', lineHeight:1.15, marginBottom:24,
          fontFamily:'"Playfair Display", "PingFang SC", serif'
        }}>哲学之河</h1>

        <div style={{ width:56, height:1.5, background:'#917647', marginBottom:28, opacity:0.45 }} />

        <p style={{
          fontSize:'clamp(0.95rem, 1.4vw, 1.15rem)', fontWeight:300,
          color:'#8A7E74', lineHeight:2.0, maxWidth:580,
          fontFamily:'var(--font-sans)'
        }}>
          从公元前三十世纪至二十一世纪<br />
          九十五个哲学流派，一部横跨五千年的人类思想史长卷
        </p>

        <p style={{
          fontSize:'clamp(0.85rem, 1.1vw, 0.95rem)', fontWeight:300,
          color:'#A09080', lineHeight:2.0, maxWidth:540, marginTop:16,
          fontFamily:'var(--font-sans)', fontStyle:'italic'
        }}>
          哲学不是孤立的学派。<br />
          思想如河流——起源、分流、汇合、消失、复兴。
        </p>

        {/* Scroll invitation — museum annotation style (VIS §4.8) */}
        <button
          onClick={() => document.getElementById('museum-gallery')?.scrollIntoView({ behavior:'smooth' })}
          style={{
            marginTop:48, background:'none', border:'1px solid rgba(145,118,71,0.2)',
            borderRadius:8, padding:'12px 36px', fontSize:13, fontWeight:300,
            color:'#8A7E74', cursor:'pointer', letterSpacing:'0.08em',
            fontFamily:'var(--font-sans)', transition:'all 400ms ease'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = 'rgba(145,118,71,0.5)';
            e.currentTarget.style.color = '#917647';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = 'rgba(145,118,71,0.2)';
            e.currentTarget.style.color = '#8A7E74';
          }}
        >
          沿河而上  ·  进入展廊
        </button>
      </section>

      {/* ══════════ MUSEUM GALLERY — River Timeline (VIS §5) ══════════ */}
      <div id="museum-gallery" style={{
        position:'relative', zIndex:1, paddingBottom:120,
        maxWidth:1280, margin:'0 auto', padding:'0 24px'
      }}>
        {/* Civilization breathing space before exhibits */}
        <div style={{ height:120 }} />

        {ALL_SCHOOLS.map((school, i) => {
          // Check if this is an era boundary
          const eraStart = eraGroups.find(g => g.startIdx === i);
          const isEraBoundary = !!eraStart;
          const isLeft = i % 3 !== 1; // Natural staggering — never mechanical L/R/L/R

          return (
            <div key={i}>
              {/* Era chapter marker (VIS §5.7) */}
              {isEraBoundary && (
                <EraMarker era={eraStart.era} isVisible={true} />
              )}

              {/* Exhibit */}
              <Exhibit
                school={school}
                index={i}
                isLeft={isLeft}
                isActive={hoveredIdx === i}
                onClick={(name) => navigate('/school/' + encodeURIComponent(name))}
                onHover={setHoveredIdx}
                onLeave={() => setHoveredIdx(null)}
              />
            </div>
          );
        })}

        {/* Closing breathing space */}
        <div style={{ height:160 }} />
      </div>

      {/* ══════════ FOOTER — Continue Journey (VIS §5.17) ══════════ */}
      <div style={{
        textAlign:'center', paddingBottom:80, position:'relative', zIndex:1,
        display:'flex', justifyContent:'center', gap:56, flexWrap:'wrap'
      }}>
        {[
          { label:'西方哲学传统', sub:'Western Tradition', path:'/western-philosophies', color:REGION_COLORS['西方'] },
          { label:'东方哲学传统', sub:'Eastern Tradition', path:'/eastern-philosophies', color:REGION_COLORS['东方'] },
          { label:'世界哲学传统', sub:'World Traditions', path:'/world-philosophies', color:REGION_COLORS['世界'] },
        ].map(btn => (
          <button key={btn.path}
            onClick={() => navigate(btn.path)}
            style={{
              background:'none', border:'none', cursor:'pointer',
              fontFamily:'"Playfair Display",serif', fontSize:16, fontWeight:400,
              color:btn.color, letterSpacing:'0.04em',
              padding:'12px 20px', transition:'all 300ms ease',
              opacity:0.75
            }}
            onMouseEnter={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.letterSpacing = '0.08em'; }}
            onMouseLeave={e => { e.currentTarget.style.opacity = '0.75'; e.currentTarget.style.letterSpacing = '0.04em'; }}
          >
            <div style={{ fontSize:10, fontWeight:400, letterSpacing:'0.2em', textTransform:'uppercase', marginBottom:6, opacity:0.6 }}>{btn.sub}</div>
            {btn.label}
          </button>
        ))}
      </div>

      {/* ══════════ ANIMATIONS ══════════ */}
      <style>{`
        @keyframes museum-drift {
          0% { transform: translate(0, 0); }
          25% { transform: translate(-1%, 0.5%); }
          50% { transform: translate(0, 1%); }
          75% { transform: translate(1%, 0.5%); }
          100% { transform: translate(0, 0); }
        }
        .exhibit { transition: opacity 600ms ease; }
      `}</style>
    </div>
  );
}
