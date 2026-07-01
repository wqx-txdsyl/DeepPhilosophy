/**
 * 哲学掠影 — Editorial Layout
 */
import { useMemo, useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function useFade() {
  const ref = useRef(null); const [on, setOn] = useState(false);
  useEffect(() => { const el = ref.current; if (!el) return; const o = new IntersectionObserver(([e]) => { if (e.isIntersecting) setOn(true); }, { threshold: 0.05 }); o.observe(el); return () => o.disconnect(); }, []);
  return [ref, on];
}

// Only load image when within 300px of viewport
function LazyImg({ src, alt, style, ph }) {
  const ref = useRef(null); const [loaded, setLoaded] = useState(false);
  useEffect(() => { const el = ref.current; if (!el) return; const o = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setLoaded(true); o.disconnect(); } }, { rootMargin: '800px' }); o.observe(el); return () => o.disconnect(); }, []);
  if (loaded) return <img ref={ref} src={src} alt={alt} style={style} />;
  const h = ph || 150;
  return <div ref={ref} style={{...style, height:h, minHeight:h, background:'#E8E0D4'}} />;
}
function FadeWrap({ children, style }) {
  const [ref, on] = useFade();
  return <div ref={ref} style={{ opacity:on?1:0, transform:on?'translateY(0)':'translateY(16px)', transition:'opacity 0.5s ease, transform 0.5s ease', ...style }}>{children}</div>;
}

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
  { century:'16世纪', name:'日本哲学', region:'世界', desc:'融合神道、佛教与儒学——京都学派以绝对无与场所逻辑贡献世界哲学。', tier:'A' },
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

const REGION_OF = {
  '道家':'china','儒家':'china','墨家':'china','法家':'china','名家':'china','阴阳家':'china','兵家':'china',
  '两汉经学':'china','魏晋玄学':'china','隋唐佛学':'china','宋明理学':'china','明清实学':'china','乾嘉朴学':'china',
  '天演论':'china','维新派':'china','三民主义':'china','旧民主主义':'china','毛泽东思想':'china',
  '中国马克思主义哲学':'china','新民主主义':'china','现代新儒家':'china','中国实证哲学':'china',
  '马克思主义哲学的中国化与体系化':'china','习近平新时代中国特色社会主义思想':'china','西藏哲学':'china',
  '古希腊哲学':'greece','罗马哲学':'rome','拜占庭哲学':'rome',
  '教父哲学':'medieval_europe','经院哲学':'medieval_europe','唯名论':'medieval_europe','基督教哲学':'medieval_europe',
  '启蒙运动':'enlightenment','实在论':'enlightenment','政治哲学':'enlightenment','伦理学':'enlightenment','宗教哲学':'enlightenment',
  '理性主义':'france','社会学':'france','实证主义':'france','存在主义':'france','结构主义':'france',
  '解构主义':'france','后结构主义':'france','后现代主义':'france','女性主义':'france','荒诞哲学':'france',
  '经验主义':'britain','自由主义':'britain','功利主义':'britain','分析哲学':'britain','科学哲学':'britain','北欧哲学':'britain','凯尔特哲学':'britain',
  '唯心主义':'germany','浪漫主义':'germany','德国古典哲学':'germany','马克思主义':'germany','生命哲学':'germany',
  '现象学':'germany','精神分析学':'germany','西方马克思主义':'germany','法兰克福学派':'germany','批判理论':'germany',
  '哲学人类学':'germany','哲学诠释学':'germany','东欧斯拉夫哲学':'germany',
  '北美哲学':'america','实用主义':'america','超验主义':'america','过程哲学':'america','社群主义':'america','技术哲学':'america',
  '印度哲学':'india','日本哲学':'japan','韩国哲学':'korea','东南亚哲学':'southeast_asia',
  '伊斯兰哲学':'islam','阿拉伯哲学':'islam','波斯哲学':'islam','犹太哲学':'islam','古希伯来哲学':'islam',
  '非洲哲学':'africa','后殖民哲学':'africa','黑人哲学':'africa',
  '拉丁美洲哲学':'latin_america','玛雅哲学':'latin_america','阿兹特克哲学':'latin_america','印加哲学':'latin_america','解放哲学':'latin_america',
  '古埃及哲学':'egypt','美索不达米亚哲学':'mesopotamia',
  '澳洲原住民哲学':'world_origin','蒙古中亚哲学':'world_origin','原住民哲学':'world_origin','环境哲学':'world_origin',
};
const REGION_NAME = { china:'中国哲学',greece:'古希腊',rome:'罗马',medieval_europe:'中世纪欧洲',enlightenment:'启蒙时代',france:'法国哲学',britain:'英国哲学',germany:'德国哲学',america:'美洲哲学',india:'印度哲学',japan:'日本哲学',korea:'韩国哲学',islam:'伊斯兰世界',africa:'非洲哲学',latin_america:'拉丁美洲',egypt:'古埃及',mesopotamia:'美索不达米亚',southeast_asia:'东南亚',world_origin:'世界传统' };

const ERAS = [
  { n:'Ancient World', t:'远古文明', r:'公元前30世纪 — 公元前10世纪', e:'era_ancient' },
  { n:'Classical Antiquity', t:'古典时代', r:'公元前6世纪 — 4世纪', e:'era_greece' },
  { n:'Middle Ages', t:'中世纪', r:'6世纪 — 16世纪', e:'era_medieval' },
  { n:'Renaissance & Early Modern', t:'文艺复兴与近代', r:'17世纪 — 18世纪', e:'era_renaissance' },
  { n:'Modern Philosophy', t:'现代哲学', r:'19世纪 — 20世纪中', e:'era_modern' },
  { n:'Contemporary', t:'当代', r:'20世纪末 — 21世纪', e:null },
];
function getEraIdx(c) {
  if (/公元前(30|15|10)/.test(c)) return 0; if (/公元前[65421]|^[34]世纪/.test(c)) return 1;
  if (/^[678]世纪$|^1[1-6]世纪$/.test(c)) return 2; if (/^1[78]世纪$/.test(c)) return 3;
  if (/19世纪|20世纪初|^20世纪$|20世纪中/.test(c)) return 4; return 5;
}

function imgUrl(name) { return `/schools/${encodeURI(name)}.jpg`; }

const tierW = (s) => s.tier === 'A' ? 400 : s.tier === 'B' ? 280 : 200;

// ─── School Card ───
function SchoolImg({ school, w }) {
  const nav = useNavigate();
  const [ref, on] = useFade();
  return (
    <div ref={ref} onClick={() => nav('/school/' + encodeURIComponent(school.name))}
      style={{ width:w, minHeight:100, cursor:'pointer', flexShrink:0, borderRadius:4, overflow:'hidden', position:'relative', backgroundColor:'#E8E0D4',
        opacity:on?1:0, transform:on?'translateY(0)':'translateY(16px)',
        transition:'opacity 0.5s ease, transform 0.5s ease' }}>
      <LazyImg src={imgUrl(school.name)} alt={school.name}
        style={{ width:'100%', height:'auto', display:'block' }} />
      <div style={{ position:'absolute', bottom:0, left:0, right:0,
        background:'linear-gradient(transparent 30%, rgba(0,0,0,0.65))', padding:'24px 12px 8px' }}>
        <div style={{ fontSize:12, fontWeight:600, color:'#fff', lineHeight:1.2,
          fontFamily:'"Playfair Display","PingFang SC",serif' }}>{school.name}</div>
        <div style={{ fontSize:9, color:'rgba(255,255,255,0.7)', marginTop:2, fontFamily:'var(--font-sans)' }}>{school.century}</div>
      </div>
    </div>
  );
}

// ─── Shared styles (avoids {{ JSX parse issues in compact blocks) ───
const $flex = {display:'flex',gap:10,justifyContent:'center',alignItems:'flex-start'};
const $col = {display:'flex',flexDirection:'column',gap:10};
const $cen = {display:'flex',justifyContent:'center'};
const $pad = (n) => ({paddingTop:n});

function BlockA({s}){const[a,b,c]=s;return(<div style={$flex}>{a&&<SchoolImg school={a} w={tierW(a)}/>}<div style={$col}>{b&&<SchoolImg school={b} w={tierW(b)}/>}{c&&<SchoolImg school={c} w={tierW(c)}/>}</div></div>)}
function BlockB({s}){const[a,b]=s;const w=Math.max(tierW(a||{}),tierW(b||{}),280);return(<div style={$flex}>{a&&<SchoolImg school={a} w={w}/>}{b&&<SchoolImg school={b} w={w}/>}</div>)}
function BlockC({s}){const[a]=s;return(<div style={$cen}>{a&&<SchoolImg school={a} w={Math.min(tierW(a)*1.5,600)}/>}</div>)}
function BlockD({s}){return(<div style={$flex}>{s.slice(0,3).map((x,i)=><SchoolImg key={i} school={x} w={tierW(x)}/>)}</div>)}
function BlockE({s}){const[a,b]=s;return(<div style={$flex}>{a&&<SchoolImg school={a} w={tierW(a)}/>}{b&&<SchoolImg school={b} w={tierW(b)}/>}</div>)}
function BlockF({s}){const[a,b,c]=s;return(<div style={$flex}><div style={$col}>{a&&<SchoolImg school={a} w={tierW(a)}/>}{b&&<SchoolImg school={b} w={tierW(b)}/>}</div>{c&&<SchoolImg school={c} w={tierW(c)}/>}</div>)}
function BlockG({s}){return(<div style={$flex}><div style={$col}>{s.slice(0,2).map((x,i)=><SchoolImg key={i} school={x} w={tierW(x)}/>)}</div><div style={$col}>{s.slice(2,4).map((x,i)=><SchoolImg key={i} school={x} w={tierW(x)}/>)}</div></div>)}
function BlockH({s}){const[a]=s;return(<div style={$cen}>{a&&<SchoolImg school={a} w={Math.min(tierW(a)*1.3,560)}/>}</div>)}
function BlockI({s}){const[a,b]=s;return(<div style={$flex}><div style={$pad(60)}>{a&&<SchoolImg school={a} w={tierW(a)}/>}</div>{b&&<SchoolImg school={b} w={tierW(b)}/>}</div>)}
function BlockJ({s}){return(<div style={$flex}>{s.slice(0,3).map((x,i)=>(<div key={i} style={$pad(i*50)}><SchoolImg school={x} w={tierW(x)}/></div>))}</div>)}
const BLOCKS=[BlockA,BlockB,BlockC,BlockD,BlockE,BlockF,BlockG,BlockH,BlockI,BlockJ];

// ─── Chapter structure ───
function buildChapters() {
  const chapters = []; let eraIdx = -1;
  for (let i = 0; i < ALL_SCHOOLS.length; i++) {
    const s = ALL_SCHOOLS[i]; const ei = getEraIdx(s.century); const r = REGION_OF[s.name] || 'world_origin';
    if (ei !== eraIdx) { eraIdx = ei; chapters.push({ type:'era', era:ERAS[ei], regions:[] }); }
    const ch = chapters[chapters.length-1];
    let region = ch.regions.find(rg => rg.key === r);
    if (!region) { region = { key:r, name:REGION_NAME[r]||r, schools:[] }; ch.regions.push(region); }
    region.schools.push(s);
  }
  return chapters;
}
function chunkSchools(schools) {
  const chunks = []; const pattern = [2,3,2,4,2,3,1,2,3,2]; let pi=0,i=0;
  while (i<schools.length) { const sz=pattern[pi%pattern.length]; chunks.push(schools.slice(i,i+sz)); i+=sz; pi++; }
  return chunks;
}

// ─── Page ───
export default function GenealogyPage() {
  const nav = useNavigate();
  const chapters = useMemo(() => buildChapters(), []);

  return (
    <div style={{ background:'#F8F6F2', minHeight:'100vh', fontFamily:'"Playfair Display","PingFang SC",serif', color:'#2A1F1A' }}>
      <section style={{ padding:'56px 32px 32px', textAlign:'center' }}>
        <p style={{ fontSize:10, letterSpacing:'0.28em', textTransform:'uppercase', color:'#917647', marginBottom:20, fontFamily:'var(--font-sans)' }}>Museum of Philosophy</p>
        <h1 style={{ fontSize:'clamp(2rem,5vw,3.2rem)', fontWeight:400, fontStyle:'italic', color:'#2A1F1A', letterSpacing:'0.06em', lineHeight:1.15, fontFamily:'"Playfair Display","PingFang SC",serif' }}>哲学掠影</h1>
        <div style={{ width:32, height:1, background:'#917647', margin:'14px auto', opacity:0.35 }} />
        <p style={{ fontSize:'0.85rem', fontWeight:300, color:'#8A7E74', fontFamily:'var(--font-sans)' }}>思想如河流，起源、分流、汇合、消失、复兴——五千年人类追问的视觉编年史</p>
      </section>
      {chapters.map((ch, ci) => (
        <div key={ci}>
          <section style={{ padding:'80px 24px 40px', textAlign:'center', maxWidth:1000, margin:'0 auto' }}>
            {ch.era.e && <LazyImg src={`/gene/${ch.era.e}.png`} alt="" style={{ height:100, width:'auto', opacity:0.55, marginBottom:8 }} />}
            <div style={{ marginTop:40 }}>
              <div style={{ fontSize:10, letterSpacing:'0.24em', textTransform:'uppercase', color:'#917647', fontFamily:'var(--font-sans)', marginBottom:8 }}>{ch.era.n}</div>
              <h2 style={{ fontSize:'clamp(1.8rem,4vw,2.6rem)', fontWeight:400, color:'#2A1F1A', margin:'0 0 8px', fontFamily:'"Playfair Display","PingFang SC",serif' }}>{ch.era.t}</h2>
              <div style={{ fontSize:13, color:'#A09080', fontFamily:'var(--font-sans)' }}>{ch.era.r}</div>
            </div>
          </section>
          {ch.regions.map((region, ri) => {
            const chunks = chunkSchools(region.schools);
            return (
              <FadeWrap key={ri}>
                <section style={{ padding:'60px 24px 20px', textAlign:'center', maxWidth:800, margin:'0 auto' }}>
                  <LazyImg src={`/gene/region/${region.key}.jpg`} alt="" style={{ width:'100%', maxHeight:320, objectFit:'cover', borderRadius:4, opacity:0.85 }} />
                  <h3 style={{ marginTop:28, fontSize:20, fontWeight:400, color:'#2A1F1A', fontFamily:'"Playfair Display","PingFang SC",serif' }}>{region.name}</h3>
                </section>
                <div style={{ maxWidth:900, margin:'0 auto', padding:'0 16px' }}>
                  {chunks.map((chunk, bi) => {
                    const Block = BLOCKS[(ci*10+ri*5+bi) % BLOCKS.length];
                    return <div key={bi} style={{ padding:'16px 0' }}><Block s={chunk} /></div>;
                  })}
                </div>
                <div style={{ height:60 }} />
              </FadeWrap>
            );
          })}
          <div style={{ height:80 }} />
        </div>
      ))}
      <div style={{ textAlign:'center', padding:'80px 32px', borderTop:'1px solid rgba(145,118,71,0.08)' }}>
        <p style={{ fontSize:12, color:'#A09080', fontFamily:'var(--font-sans)', margin:0 }}>九十五个哲学流派 · 一部横跨五千年的人类思想史图录</p>
        <div style={{ display:'flex', justifyContent:'center', gap:32, marginTop:32 }}>
          {[{ l:'西方哲学', p:'/western-philosophies' },{ l:'东方哲学', p:'/eastern-philosophies' },{ l:'世界哲学', p:'/world-philosophies' }].map(b => (
            <button key={b.p} onClick={() => nav(b.p)} style={{ background:'none', border:'1px solid rgba(145,118,71,0.10)', cursor:'pointer', fontFamily:'"Playfair Display",serif', fontSize:13, color:'#917647', padding:'6px 16px', borderRadius:4, transition:'all 300ms ease', opacity:0.7 }}
              onMouseEnter={e=>{e.currentTarget.style.opacity='1';e.currentTarget.style.borderColor='#917647';}} onMouseLeave={e=>{e.currentTarget.style.opacity='0.7';e.currentTarget.style.borderColor='rgba(145,118,71,0.10)';}}>{b.l}</button>
          ))}</div>
      </div>
    </div>
  );
}
