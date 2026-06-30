/**
 * 哲学之河 V7 — Chessboard on Parchment
 * School cards = image + name + desc. Region + deco tiles interspersed.
 * Parchment background matching other pages. Uses small /schools/ images.
 */
import { useState, useEffect, useMemo } from 'react';
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

const R_COLORS = { '西方': '#917647', '东方': '#3A5A7C', '世界': '#5A8A5A' };

const REGION_MAP = {
  '道家':'china','儒家':'china','墨家':'china','法家':'china','名家':'china','阴阳家':'china','兵家':'china',
  '两汉经学':'china','魏晋玄学':'china','隋唐佛学':'china','宋明理学':'china','明清实学':'china',
  '乾嘉朴学':'china','天演论':'china','维新派':'china','三民主义':'china','旧民主主义':'china',
  '毛泽东思想':'china','中国马克思主义哲学':'china','新民主主义':'china','现代新儒家':'china',
  '中国实证哲学':'china','马克思主义哲学的中国化与体系化':'china','习近平新时代中国特色社会主义思想':'china',
  '古希腊哲学':'greece','教父哲学':'medieval_europe','经院哲学':'medieval_europe','唯名论':'medieval_europe',
  '理性主义':'france','经验主义':'britain','启蒙运动':'enlightenment',
  '德国古典哲学':'germany','马克思主义':'germany','法兰克福学派':'germany',
  '生命哲学':'germany','现象学':'germany','存在主义':'france','解构主义':'france',
  '后结构主义':'france','后现代主义':'france','荒诞哲学':'france',
  '分析哲学':'britain','功利主义':'britain','自由主义':'britain','社会学':'france',
  '西方马克思主义':'germany','批判理论':'germany','哲学诠释学':'germany',
  '北欧哲学':'britain','东欧斯拉夫哲学':'germany','北美哲学':'america',
  '实用主义':'america','超验主义':'america','过程哲学':'america',
  '印度哲学':'india','日本哲学':'japan','韩国哲学':'korea',
  '伊斯兰哲学':'islam','阿拉伯哲学':'islam','波斯哲学':'islam',
  '非洲哲学':'africa','犹太哲学':'islam',
  '拉丁美洲哲学':'latin_america','玛雅哲学':'latin_america','阿兹特克哲学':'latin_america',
  '印加哲学':'latin_america','解放哲学':'latin_america',
  '东南亚哲学':'southeast_asia','西藏哲学':'china',
  '古埃及哲学':'egypt','美索不达米亚哲学':'mesopotamia',
  '罗马哲学':'rome','拜占庭哲学':'rome',
  '古希伯来哲学':'islam','凯尔特哲学':'britain',
  '澳洲原住民哲学':'world_origin','蒙古中亚哲学':'world_origin',
  '原住民哲学':'world_origin','后殖民哲学':'africa','黑人哲学':'africa','环境哲学':'world_origin',
  '实在论':'enlightenment','唯心主义':'germany','浪漫主义':'germany',
  '实证主义':'france','精神分析学':'germany','结构主义':'france',
  '科学哲学':'britain','政治哲学':'enlightenment','伦理学':'enlightenment',
  '基督教哲学':'medieval_europe','宗教哲学':'enlightenment','女性主义':'france',
  '社群主义':'america','技术哲学':'america',
};

const ERAS = [
  { name:'Ancient World', title:'远古文明', range:'公元前30世纪 — 公元前10世纪', era:'era_ancient' },
  { name:'Classical Antiquity', title:'古典时代', range:'公元前6世纪 — 4世纪', era:'era_greece' },
  { name:'Middle Ages', title:'中世纪', range:'6世纪 — 16世纪', era:'era_medieval' },
  { name:'Renaissance & Early Modern', title:'文艺复兴与近代', range:'17世纪 — 18世纪', era:'era_renaissance' },
  { name:'Modern Philosophy', title:'现代哲学', range:'19世纪 — 20世纪中', era:'era_modern' },
  { name:'Contemporary', title:'当代', range:'20世纪末 — 21世纪', era:'era_modern' },
];
function eraIdx(i) {
  const c = ALL_SCHOOLS[i].century;
  if (/公元前(30|15|10)/.test(c)) return 0;
  if (/公元前[65421]|^[34]世纪/.test(c)) return 1;
  if (/^[678]世纪$|^1[1-6]世纪$/.test(c)) return 2;
  if (/^1[78]世纪$/.test(c)) return 3;
  if (/19世纪|20世纪初|^20世纪$|20世纪中/.test(c)) return 4;
  return 5;
}
const IMG_EXT = (n) => (new Set(['凯尔特哲学','原住民哲学','古希伯来哲学','罗马哲学','拜占庭哲学','解放哲学','后殖民哲学','环境哲学','解构主义','黑人哲学','古希腊哲学']).has(n) ? '.jpg' : '.png');

// ─── School Card ───
function SchoolCard({ school, onClick }) {
  const c = R_COLORS[school.region];
  return (
    <div onClick={() => onClick(school.name)} style={{
      cursor:'pointer', borderRadius:10, overflow:'hidden',
      background:'#FDFBF7', border:'1px solid rgba(145,118,71,0.12)',
      boxShadow:'0 1px 4px rgba(42,31,26,0.04)',
      transition:'all 350ms ease',
    }}>
      <img src={`/schools/${encodeURI(school.name)}${IMG_EXT(school.name)}`} alt="" loading="lazy"
        style={{ width:'100%', aspectRatio:'16/10', objectFit:'cover', display:'block', background:'#EDE5D8' }} />
      <div style={{ padding:'14px 18px' }}>
        <div style={{ fontSize:9, fontWeight:400, letterSpacing:'0.12em', textTransform:'uppercase', color:c, marginBottom:6, fontFamily:'var(--font-sans)', opacity:0.8 }}>
          {school.region==='东方'?'Eastern':school.region==='西方'?'Western':'World'} · {school.century}</div>
        <h3 style={{ fontSize:16, fontWeight:500, color:'#2A1F1A', margin:'0 0 4px', lineHeight:1.3,
          fontFamily:'"Playfair Display","PingFang SC",serif' }}>{school.name}</h3>
        <p style={{ fontSize:11, fontWeight:300, color:'#7A6E64', lineHeight:1.6, margin:0, fontFamily:'var(--font-sans)' }}>{school.desc}</p>
      </div>
    </div>
  );
}

// ─── Region Tile ───
function RegionTile({ school }) {
  const r = REGION_MAP[school.name] || 'world_origin';
  return (
    <img src={`/gene/region/${r}.png`} alt="" loading="lazy"
      style={{ width:'100%', aspectRatio:'4/3', objectFit:'cover', display:'block', borderRadius:8, opacity:0.85 }} />
  );
}

// ─── Era Marker ───
function EraMarker({ era }) {
  return (
    <div style={{ textAlign:'center', padding:'36px 16px 20px', gridColumn:'1 / -1' }}>
      <div style={{ width:50, height:1, background:'#91764730', margin:'0 auto 16px' }} />
      <img src={`/gene/${era.era}.png`} alt="" loading="lazy"
        style={{ height:100, width:'auto', margin:'0 auto 12px', display:'block', objectFit:'contain', opacity:0.7 }} />
      <p style={{ fontSize:10, letterSpacing:'0.2em', textTransform:'uppercase', color:'#917647', margin:'0 0 2px', fontFamily:'var(--font-sans)' }}>{era.name}</p>
      <h2 style={{ fontSize:'1.2rem', fontWeight:400, color:'#2A1F1A', margin:'0 0 2px', fontFamily:'"Playfair Display","PingFang SC",serif' }}>{era.title}</h2>
      <p style={{ fontSize:11, color:'#A09080', fontFamily:'var(--font-sans)', margin:0 }}>{era.range}</p>
    </div>
  );
}

// ─── Build chessboard tiles ───
function buildTiles() {
  const tiles = [];
  ALL_SCHOOLS.forEach((s, i) => {
    tiles.push({ type:'school', school:s, idx:i });
    // Intersperse: every 2nd school gets a region tile, every 3rd gets a deco tile
    if (i % 3 === 0) tiles.push({ type:'region', school:s, idx:i });
    if (i % 7 === 3) tiles.push({ type:'deco', src:'/gene/civilization_silhouette.png', idx:i });
    if (i % 11 === 5) tiles.push({ type:'deco', src:'/gene/philosophy_symbols.png', idx:i });
  });
  return tiles;
}

// ─── Page ───
export default function GenealogyPage() {
  const navigate = useNavigate();
  const tiles = useMemo(() => buildTiles(), []);
  const eraGrps = useMemo(() => {
    const g = []; let cur = -1;
    ALL_SCHOOLS.forEach((s, i) => { const ei = eraIdx(i); if (ei !== cur) { cur = ei; g.push({ era: ERAS[ei], startIdx: i }); } });
    return g;
  }, []);

  return (
    <div style={{ background:'#F8F6F2', minHeight:'100vh',
      fontFamily:'"Playfair Display","PingFang SC",serif', color:'#2A1F1A' }}>

      {/* Hero */}
      <section style={{ minHeight:'40vh', display:'flex', flexDirection:'column',
        justifyContent:'center', alignItems:'center', textAlign:'center', padding:'60px 32px' }}>
        <p style={{ fontSize:10, letterSpacing:'0.28em', textTransform:'uppercase', color:'#917647', marginBottom:24, fontFamily:'var(--font-sans)' }}>
          Museum of Philosophy  ·  Genealogy Wing</p>
        <h1 style={{ fontSize:'clamp(2rem,5vw,3.5rem)', fontWeight:400, fontStyle:'italic',
          color:'#2A1F1A', letterSpacing:'0.04em', lineHeight:1.15, marginBottom:20,
          fontFamily:'"Playfair Display","PingFang SC",serif' }}>哲学之河</h1>
        <div style={{ width:40, height:1.5, background:'#917647', marginBottom:20, opacity:0.4 }} />
        <p style={{ fontSize:'0.95rem', fontWeight:300, color:'#8A7E74', lineHeight:2.0, maxWidth:520, fontFamily:'var(--font-sans)' }}>
          九十五个哲学流派，一部横跨五千年的人类思想史长卷</p>
        <button onClick={() => document.getElementById('grid')?.scrollIntoView({ behavior:'smooth' })}
          style={{ marginTop:36, background:'none', border:'1px solid rgba(145,118,71,0.2)',
            borderRadius:6, padding:'10px 28px', fontSize:12, color:'#917647', cursor:'pointer',
            letterSpacing:'0.08em', fontFamily:'var(--font-sans)', transition:'all 300ms ease' }}
          onMouseEnter={e => { e.currentTarget.style.borderColor='#917647'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor='rgba(145,118,71,0.2)'; }}>
          进入展廊</button>
      </section>

      {/* Grid */}
      <div id="grid" style={{ padding:'16px', maxWidth:1400, margin:'0 auto',
        display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(260px, 1fr))', gap:14, alignItems:'start' }}>
        {tiles.map((tile, i) => {
          const eraStart = tile.type === 'school' ? eraGrps.find(g => g.startIdx === tile.idx) : null;
          return (
            <div key={i} style={{ gridColumn: tile.type === 'school' ? 'span 2' : 'span 1' }}>
              {eraStart && <EraMarker era={eraStart.era} />}
              {tile.type === 'school' && <SchoolCard school={tile.school} onClick={(n) => navigate('/school/' + encodeURIComponent(n))} />}
              {tile.type === 'region' && <RegionTile school={tile.school} />}
              {tile.type === 'deco' && <img src={tile.src} alt="" loading="lazy" style={{ width:'100%', height:'100%', objectFit:'cover', borderRadius:8, opacity:0.8 }} />}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div style={{ textAlign:'center', padding:'60px 32px', display:'flex', justifyContent:'center', gap:40, flexWrap:'wrap' }}>
        {[
          { l:'西方哲学', p:'/western-philosophies', c:R_COLORS['西方'] },
          { l:'东方哲学', p:'/eastern-philosophies', c:R_COLORS['东方'] },
          { l:'世界哲学', p:'/world-philosophies', c:R_COLORS['世界'] },
        ].map(b => (
          <button key={b.p} onClick={() => navigate(b.p)}
            style={{ background:'none', border:'1px solid rgba(145,118,71,0.1)', cursor:'pointer',
              fontFamily:'"Playfair Display",serif', fontSize:15, color:b.c, letterSpacing:'0.04em',
              padding:'8px 18px', borderRadius:6, transition:'all 300ms ease', opacity:0.7 }}
            onMouseEnter={e => { e.currentTarget.style.opacity='1'; e.currentTarget.style.borderColor=b.c; }}
            onMouseLeave={e => { e.currentTarget.style.opacity='0.7'; e.currentTarget.style.borderColor='rgba(145,118,71,0.1)'; }}>
            {b.l}</button>
        ))}</div>
    </div>
  );
}
