/**
 * 哲学掠影 — Editorial Layout System
 * National Geographic × Phaidon art book style.
 * 10 hand-crafted layout blocks, cycled for curated rhythm.
 */
import { useMemo, useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function useFadeIn() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold:0.1, rootMargin:'-30px 0px' });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, visible];
}

const ALL_SCHOOLS = [
  { century:'公元前30世纪', name:'古希伯来哲学', region:'世界', desc:'约伯、传道书与智慧文学——信仰、苦难与神圣正义的追问。' },
  { century:'公元前30世纪', name:'古埃及哲学', region:'世界', desc:'玛阿特——宇宙秩序、真理与正义的永恒法则。' },
  { century:'公元前30世纪', name:'美索不达米亚哲学', region:'世界', desc:'苏美尔智慧文学追问苦难与秩序——人类最早的哲学追问。' },
  { century:'公元前15世纪', name:'印度哲学', region:'世界', desc:'《吠陀》《奥义书》为源头，六派哲学追问解脱。' },
  { century:'公元前15世纪', name:'犹太哲学', region:'世界', desc:'从斐洛到列维纳斯——雅典与耶路撒冷之间。' },
  { century:'公元前10世纪', name:'波斯哲学', region:'世界', desc:'琐罗亚斯德教善恶二元论——两千五百年的连续传统。' },
  { century:'公元前6世纪', name:'凯尔特哲学', region:'世界', desc:'德鲁伊传统与凯尔特智慧——自然、灵魂转世与森林中的哲学。' },
  { century:'公元前6世纪', name:'道家', region:'东方', desc:'道法自然，无为而治。' },
  { century:'公元前6世纪', name:'儒家', region:'东方', desc:'以仁为核心，以礼为规范。' },
  { century:'公元前6世纪', name:'古希腊哲学', region:'世界', desc:'西方哲学总源——以理性思辨取代神话解释。' },
  { century:'公元前5世纪', name:'墨家', region:'东方', desc:'兼爱非攻，尚贤节用。' },
  { century:'公元前5世纪', name:'兵家', region:'东方', desc:'知己知彼，不战屈人。' },
  { century:'公元前4世纪', name:'法家', region:'东方', desc:'以法治国，不别亲疏。' },
  { century:'公元前4世纪', name:'名家', region:'东方', desc:'白马非马——中国最早的逻辑学。' },
  { century:'公元前4世纪', name:'阴阳家', region:'东方', desc:'阴阳消长，五德终始。' },
  { century:'公元前1世纪', name:'罗马哲学', region:'世界', desc:'西塞罗、塞内卡、马可·奥勒留——斯多葛与伊壁鸠鲁在帝国的实践。' },
  { century:'公元前2世纪', name:'两汉经学', region:'东方', desc:'通经致用，以经为法。' },
  { century:'3世纪', name:'魏晋玄学', region:'东方', desc:'越名教而任自然。' },
  { century:'4世纪', name:'拜占庭哲学', region:'世界', desc:'东罗马帝国的神学哲学传统——伪狄奥尼修斯与拜占庭智慧。' },
  { century:'4世纪', name:'教父哲学', region:'西方', desc:'以希腊理性为基督教信仰奠基。' },
  { century:'6世纪', name:'隋唐佛学', region:'东方', desc:'八宗竞秀，会通中印。' },
  { century:'7世纪', name:'伊斯兰哲学', region:'世界', desc:'凯拉姆与苏非——理性与启示的对话。' },
  { century:'7世纪', name:'阿拉伯哲学', region:'世界', desc:'铿迪、法拉比、阿维森纳——中世纪哲学桥梁。' },
  { century:'8世纪', name:'西藏哲学', region:'世界', desc:'宗喀巴体系——藏传佛教中观应成派。' },
  { century:'11世纪', name:'宋明理学', region:'东方', desc:'为天地立心，为生民立命。' },
  { century:'11世纪', name:'经院哲学', region:'西方', desc:'以亚里士多德逻辑构建理性圣殿。' },
  { century:'11世纪', name:'唯名论', region:'西方', desc:'共相只是名称不是实在。' },
  { century:'13世纪', name:'印加哲学', region:'世界', desc:'帕查与艾尼——安第斯的宇宙时空与互惠伦理。' },
  { century:'13世纪', name:'非洲哲学', region:'世界', desc:'乌班图与去殖民化。' },
  { century:'15世纪', name:'拉丁美洲哲学', region:'世界', desc:'从拉斯·卡萨斯到杜塞尔——解放的哲学。' },
  { century:'15世纪', name:'玛雅哲学', region:'世界', desc:'《波波尔·乌》——循环时间观与玉米人。' },
  { century:'15世纪', name:'阿兹特克哲学', region:'世界', desc:'第五太阳纪——花与歌的哲学回应。' },
  { century:'16世纪', name:'东南亚哲学', region:'世界', desc:'上座部佛教与本土智慧的交融。' },
  { century:'16世纪', name:'韩国哲学', region:'世界', desc:'性理学与实学——从四端七情到主体思想。' },
  { century:'17世纪', name:'明清实学', region:'东方', desc:'经世致用，实事求是。' },
  { century:'17世纪', name:'乾嘉朴学', region:'东方', desc:'无征不信，孤证不立。' },
  { century:'17世纪', name:'理性主义', region:'西方', desc:'以数学公理为范本。' },
  { century:'17世纪', name:'经验主义', region:'西方', desc:'一切知识起源于感觉经验。' },
  { century:'18世纪', name:'启蒙运动', region:'西方', desc:'敢于运用你自己的理性。' },
  { century:'18世纪', name:'实在论', region:'西方', desc:'存在独立于心灵。' },
  { century:'18世纪', name:'唯心主义', region:'西方', desc:'实在的本质是精神或观念。' },
  { century:'18世纪', name:'自由主义', region:'西方', desc:'个人自由是最高政治价值。' },
  { century:'18世纪', name:'浪漫主义', region:'西方', desc:'以情感和想象反抗启蒙理性。' },
  { century:'19世纪', name:'德国古典哲学', region:'西方', desc:'从康德到黑格尔的哲学革命。' },
  { century:'19世纪', name:'功利主义', region:'西方', desc:'最大多数人的最大幸福。' },
  { century:'19世纪', name:'超验主义', region:'西方', desc:'美国精神独立宣言。' },
  { century:'19世纪', name:'实证主义', region:'西方', desc:'只问如何不问为何。' },
  { century:'19世纪', name:'马克思主义', region:'西方', desc:'问题在于改变世界。' },
  { century:'19世纪', name:'生命哲学', region:'西方', desc:'理性不能穷尽生命。' },
  { century:'19世纪', name:'社会学', region:'西方', desc:'追问社会何以可能。' },
  { century:'19世纪', name:'北欧哲学', region:'世界', desc:'克尔凯郭尔的信仰跳跃。' },
  { century:'19世纪', name:'东欧斯拉夫哲学', region:'世界', desc:'索洛维约夫、舍斯托夫——第三条道路。' },
  { century:'19世纪', name:'北美哲学', region:'世界', desc:'实用主义与超验主义。' },
  { century:'19世纪', name:'黑人哲学', region:'世界', desc:'从废奴运动到黑权运动——双重意识、种族批判与黑人存在主义的全球哲学传统。' },
  { century:'19世纪末', name:'天演论', region:'东方', desc:'物竞天择，适者生存。' },
  { century:'19世纪末', name:'维新派', region:'东方', desc:'变则通，通则久。' },
  { century:'20世纪初', name:'实用主义', region:'西方', desc:'真理即有用，意义在于效果。' },
  { century:'20世纪初', name:'精神分析学', region:'西方', desc:'心灵深处有一个你不知道的你。' },
  { century:'20世纪初', name:'现象学', region:'西方', desc:'回到事物本身。' },
  { century:'20世纪初', name:'存在主义', region:'西方', desc:'存在先于本质。' },
  { century:'20世纪初', name:'分析哲学', region:'西方', desc:'全部哲学就是语言的批判。' },
  { century:'20世纪初', name:'过程哲学', region:'西方', desc:'实在是生成而非存在。' },
  { century:'20世纪初', name:'哲学人类学', region:'西方', desc:'人是什么。' },
  { century:'20世纪初', name:'三民主义', region:'东方', desc:'民族、民权、民生。' },
  { century:'20世纪初', name:'旧民主主义', region:'东方', desc:'探索民主共和道路。' },
  { century:'20世纪', name:'解放哲学', region:'世界', desc:'从解放神学到巴西解放教育学——哲学为被压迫者发声。' },
  { century:'20世纪中', name:'西方马克思主义', region:'西方', desc:'回到黑格尔的马克思。' },
  { century:'20世纪中', name:'法兰克福学派', region:'西方', desc:'工具理性已沦为新的统治形式。' },
  { century:'20世纪中', name:'批判理论', region:'西方', desc:'传统理论描述世界，批判理论旨在解放。' },
  { century:'20世纪中', name:'科学哲学', region:'西方', desc:'科学何以成为科学。' },
  { century:'20世纪中', name:'荒诞哲学', region:'西方', desc:'世界没有意义，但人必须活下去。' },
  { century:'20世纪中', name:'基督教哲学', region:'西方', desc:'信仰在理性中追问自身。' },
  { century:'20世纪中', name:'结构主义', region:'西方', desc:'意义在关系之中。' },
  { century:'20世纪中', name:'政治哲学', region:'西方', desc:'追问正义、权力与自由。' },
  { century:'20世纪中', name:'哲学诠释学', region:'西方', desc:'理解是存在方式。' },
  { century:'20世纪中', name:'毛泽东思想', region:'东方', desc:'实事求是，群众路线。' },
  { century:'20世纪中', name:'中国马克思主义哲学', region:'东方', desc:'辩证唯物主义的中国化。' },
  { century:'20世纪中', name:'新民主主义', region:'东方', desc:'革命分两步走。' },
  { century:'20世纪末', name:'解构主义', region:'西方', desc:'德里达的解构——文字、意义与权力的边缘。' },
  { century:'20世纪末', name:'后结构主义', region:'西方', desc:'解构逻各斯中心主义。' },
  { century:'20世纪末', name:'后现代主义', region:'西方', desc:'对宏大叙事的怀疑。' },
  { century:'20世纪末', name:'伦理学', region:'西方', desc:'追问人应该如何生活。' },
  { century:'20世纪末', name:'环境哲学', region:'世界', desc:'人类与自然的伦理关系——深层生态学、生态女性主义与环境正义。' },
  { century:'20世纪末', name:'宗教哲学', region:'西方', desc:'以理性审视信仰。' },
  { century:'20世纪末', name:'后殖民哲学', region:'世界', desc:'法农、萨义德、斯皮瓦克——殖民经验的哲学批判与去殖民化思想。' },
  { century:'20世纪末', name:'女性主义', region:'西方', desc:'个人的即政治的。' },
  { century:'20世纪末', name:'原住民哲学', region:'世界', desc:'全球原住民的生态智慧与土地伦理——从澳大利亚到亚马逊。' },
  { century:'20世纪末', name:'社群主义', region:'西方', desc:'自我镶嵌于共同体之中。' },
  { century:'20世纪末', name:'现代新儒家', region:'东方', desc:'返本开新，内圣外王。' },
  { century:'20世纪末', name:'中国实证哲学', region:'东方', desc:'大胆假设，小心求证。' },
  { century:'20世纪末', name:'马克思主义哲学的中国化与体系化', region:'东方', desc:'实践标准到理论体系。' },
  { century:'20世纪末', name:'蒙古中亚哲学', region:'世界', desc:'萨满传统与长生天。' },
  { century:'20世纪末', name:'澳洲原住民哲学', region:'世界', desc:'梦时代——最古老文明的生命智慧。' },
  { century:'21世纪', name:'技术哲学', region:'西方', desc:'技术不是中立的工具。' },
  { century:'21世纪', name:'习近平新时代中国特色社会主义思想', region:'东方', desc:'以人民为中心的发展思想。' },
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
const REGION_NAME = { china:'中国哲学',greece:'古希腊',rome:'罗马',medieval_europe:'中世纪欧洲',enlightenment:'启蒙时代',france:'法国哲学',britain:'英国哲学',germany:'德国哲学',america:'美洲哲学',india:'印度哲学',japan:'日本哲学',korea:'韩国哲学',islam:'伊斯兰世界',africa:'非洲哲学',latin_america:'拉丁美洲',egypt:'古埃及',mesopotamia:'美索不达米亚',southeast_asia:'东南亚',renaissance:'文艺复兴',world_origin:'世界传统' };

const ERAS = [
  { n:'Ancient World', t:'远古文明', r:'公元前30世纪 — 公元前10世纪', e:'era_ancient' },
  { n:'Classical Antiquity', t:'古典时代', r:'公元前6世纪 — 4世纪', e:'era_greece' },
  { n:'Middle Ages', t:'中世纪', r:'6世纪 — 16世纪', e:'era_medieval' },
  { n:'Renaissance & Early Modern', t:'文艺复兴与近代', r:'17世纪 — 18世纪', e:'era_renaissance' },
  { n:'Modern Philosophy', t:'现代哲学', r:'19世纪 — 20世纪中', e:'era_modern' },
  { n:'Contemporary', t:'当代', r:'20世纪末 — 21世纪', e:null },
];
function getEraIdx(century) {
  if (/公元前(30|15|10)/.test(century)) return 0;
  if (/公元前[65421]|^[34]世纪/.test(century)) return 1;
  if (/^[678]世纪$|^1[1-6]世纪$/.test(century)) return 2;
  if (/^1[78]世纪$/.test(century)) return 3;
  if (/19世纪|20世纪初|^20世纪$|20世纪中/.test(century)) return 4;
  return 5;
}

const PNG_SCHOOLS = new Set([
  '东欧斯拉夫哲学','伊壁鸠鲁学派','前苏格拉底哲学','北欧哲学','北美哲学',
  '印加哲学','古埃及哲学','新柏拉图主义','澳洲原住民哲学','犬儒学派',
  '玛雅哲学','美索不达米亚哲学','蒙古中亚哲学','西藏哲学','阿兹特克哲学','韩国哲学',
]);
const imgUrl = (name) => `/schools/${encodeURI(name)}${PNG_SCHOOLS.has(name)?'.png':'.jpg'}`;

// ─── 10 Editorial Layout Blocks ───
// Each block takes an array of schools and a block index for variation.
// Returns a flex/grid layout of image cards.

function SchoolImg({ school, w, h }) {
  const nav = useNavigate();
  const [ref, visible] = useFadeIn();
  return (
    <div ref={ref} onClick={() => nav('/school/' + encodeURIComponent(school.name))}
      style={{ width:w, flexShrink:0, borderRadius:4, overflow:'hidden', position:'relative', backgroundColor:'#E8E0D4', cursor:'pointer',
      opacity:visible?1:0, transform:visible?'translateY(0)':'translateY(24px)',
      transition:'opacity 0.6s ease, transform 0.6s ease' }}>
      <img src={imgUrl(school.name)} alt={school.name} loading="lazy"
        style={{ width:'100%', height:h||'auto', objectFit:'cover', display:'block' }}
        onError={(e) => { e.currentTarget.style.display='none'; }} />
      <div style={{ position:'absolute', bottom:0, left:0, right:0,
        background:'linear-gradient(transparent 30%, rgba(0,0,0,0.65))', padding:'24px 12px 8px' }}>
        <div style={{ fontSize:12, fontWeight:600, color:'#fff', lineHeight:1.2,
          fontFamily:'"Playfair Display","PingFang SC",serif' }}>{school.name}</div>
        <div style={{ fontSize:9, color:'rgba(255,255,255,0.7)', marginTop:2, fontFamily:'var(--font-sans)' }}>{school.century}</div>
      </div>
    </div>
  );
}

// Block A: 1 large left + 2 small stacked right
function BlockA({ schools }) {
  const [a,b,c] = schools;
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      {a && <SchoolImg school={a} w={380} />}
      <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
        {b && <SchoolImg school={b} w={200} />}
        {c && <SchoolImg school={c} w={200} />}
      </div>
    </div>
  );
}

// Block B: 2 equal side by side
function BlockB({ schools }) {
  const [a,b] = schools;
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      {a && <SchoolImg school={a} w={290} />}
      {b && <SchoolImg school={b} w={290} />}
    </div>
  );
}

// Block C: 1 wide panorama
function BlockC({ schools }) {
  const [a] = schools;
  return (
    <div style={{ display:'flex', justifyContent:'center' }}>
      {a && <SchoolImg school={a} w={600} />}
    </div>
  );
}

// Block D: 3 equal in a row
function BlockD({ schools }) {
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      {schools.slice(0,3).map((s,i) => <SchoolImg key={i} school={s} w={200} />)}
    </div>
  );
}

// Block E: 1 tall + 1 wide
function BlockE({ schools }) {
  const [a,b] = schools;
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      {a && <SchoolImg school={a} w={240} />}
      {b && <SchoolImg school={b} w={340} />}
    </div>
  );
}

// Block F: 2 small + 1 medium
function BlockF({ schools }) {
  const [a,b,c] = schools;
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
        {a && <SchoolImg school={a} w={180} />}
        {b && <SchoolImg school={b} w={180} />}
      </div>
      {c && <SchoolImg school={c} w={300} />}
    </div>
  );
}

// Block G: 4 in a square
function BlockG({ schools }) {
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
        {schools.slice(0,2).map((s,i) => <SchoolImg key={i} school={s} w={200} />)}
      </div>
      <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
        {schools.slice(2,4).map((s,i) => <SchoolImg key={i} school={s} w={200} />)}
      </div>
    </div>
  );
}

// Block H: 1 extra large hero
function BlockH({ schools }) {
  const [a] = schools;
  return (
    <div style={{ display:'flex', justifyContent:'center' }}>
      {a && <SchoolImg school={a} w={600} />}
    </div>
  );
}

// Block I: offset — 1 large right + 1 small left-top
function BlockI({ schools }) {
  const [a,b] = schools;
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      <div style={{ paddingTop:60 }}>
        {a && <SchoolImg school={a} w={200} />}
      </div>
      {b && <SchoolImg school={b} w={380} />}
    </div>
  );
}

// Block J: 3 in staircase
function BlockJ({ schools }) {
  return (
    <div style={{ display:'flex', gap:10, justifyContent:'center', alignItems:'flex-start' }}>
      {schools.slice(0,3).map((s,i) => (
        <div key={i} style={{ paddingTop: i*50 }}>
          <SchoolImg school={s} w={190} />
        </div>
      ))}
    </div>
  );
}

const BLOCKS = [BlockA, BlockB, BlockC, BlockD, BlockE, BlockF, BlockG, BlockH, BlockI, BlockJ];

// ─── Build page structure: eras → regions → schools → blocks ───
function buildChapters() {
  const chapters = [];
  let eraIdx = -1;

  for (let i = 0; i < ALL_SCHOOLS.length; i++) {
    const s = ALL_SCHOOLS[i];
    const ei = getEraIdx(s.century);
    const r = REGION_OF[s.name] || 'world_origin';

    // New era
    if (ei !== eraIdx) {
      eraIdx = ei;
      const era = ERAS[ei];
      chapters.push({ type:'era', era, regions:[] });
    }

    const chapter = chapters[chapters.length-1];
    // Find or create region within this era
    let region = chapter.regions.find(rg => rg.key === r);
    if (!region) {
      region = { key:r, name:REGION_NAME[r]||r, schools:[] };
      chapter.regions.push(region);
    }
    region.schools.push(s);
  }
  return chapters;
}

// Chunk schools into groups of 2-4 for blocks
function chunkSchools(schools) {
  const chunks = [];
  const pattern = [2, 3, 2, 4, 2, 3, 1, 2, 3, 2];
  let pi = 0, i = 0;
  while (i < schools.length) {
    const size = pattern[pi % pattern.length];
    chunks.push(schools.slice(i, i + size));
    i += size;
    pi++;
  }
  return chunks;
}

// ─── Components ───

function EraCover({ era }) {
  return (
    <section style={{ padding:'80px 24px 40px', textAlign:'center', maxWidth:1000, margin:'0 auto' }}>
      {era.e && (
        <img src={`/gene/${era.e}.png`} alt="" style={{ height:56, width:'auto', opacity:0.5, marginBottom:8 }} />
      )}
      <div style={{ marginTop:40 }}>
        <div style={{ fontSize:10, letterSpacing:'0.24em', textTransform:'uppercase', color:'#917647', fontFamily:'var(--font-sans)', marginBottom:8 }}>{era.n}</div>
        <h2 style={{ fontSize:'clamp(1.8rem,4vw,2.6rem)', fontWeight:400, color:'#2A1F1A', margin:'0 0 8px',
          fontFamily:'"Playfair Display","PingFang SC",serif' }}>{era.t}</h2>
        <div style={{ fontSize:13, color:'#A09080', fontFamily:'var(--font-sans)' }}>{era.r}</div>
      </div>
    </section>
  );
}

function RegionIntro({ region }) {
  const [ref, visible] = useFadeIn();
  return (
    <section ref={ref} style={{ padding:'60px 24px 20px', textAlign:'center', maxWidth:800, margin:'0 auto',
      opacity:visible?1:0, transform:visible?'translateY(0)':'translateY(20px)',
      transition:'opacity 0.6s ease, transform 0.6s ease' }}>
      <img src={`/gene/region/${region.key}.png`} alt="" style={{ width:'100%', maxHeight:320, objectFit:'cover', borderRadius:4, opacity:0.85 }}
        onError={(e) => { e.currentTarget.style.display='none'; }} />
      <h3 style={{ marginTop:28, fontSize:20, fontWeight:400, color:'#2A1F1A',
        fontFamily:'"Playfair Display","PingFang SC",serif' }}>{region.name}</h3>
    </section>
  );
}

function SchoolBlock({ schools, blockIdx }) {
  const Block = BLOCKS[blockIdx % BLOCKS.length];
  return (
    <div style={{ padding:'16px 0' }}>
      <Block schools={schools} />
    </div>
  );
}

// ─── Page ───
export default function GenealogyPage() {
  const nav = useNavigate();
  const chapters = useMemo(() => buildChapters(), []);

  return (
    <div style={{ background:'#F8F6F2', minHeight:'100vh',
      fontFamily:'"Playfair Display","PingFang SC",serif', color:'#2A1F1A' }}>

      {/* ══════════ MASTHEAD ══════════ */}
      <section style={{ padding:'56px 32px 32px', textAlign:'center' }}>
        <p style={{ fontSize:10, letterSpacing:'0.28em', textTransform:'uppercase', color:'#917647', marginBottom:20, fontFamily:'var(--font-sans)' }}>
          Museum of Philosophy</p>
        <h1 style={{ fontSize:'clamp(2rem,5vw,3.2rem)', fontWeight:400, fontStyle:'italic',
          color:'#2A1F1A', letterSpacing:'0.06em', lineHeight:1.15,
          fontFamily:'"Playfair Display","PingFang SC",serif' }}>哲学掠影</h1>
        <div style={{ width:32, height:1, background:'#917647', margin:'14px auto', opacity:0.35 }} />
        <p style={{ fontSize:'0.85rem', fontWeight:300, color:'#8A7E74', fontFamily:'var(--font-sans)' }}>
          一部按照时间顺序翻阅的世界哲学图录</p>
      </section>

      {/* ══════════ CHAPTERS ══════════ */}
      {chapters.map((ch, ci) => (
        <div key={ci}>
          <EraCover era={ch.era} />

          {ch.regions.map((region, ri) => {
            const chunks = chunkSchools(region.schools);
            return (
              <div key={ri}>
                <RegionIntro region={region} />

                <div style={{ maxWidth:900, margin:'0 auto', padding:'0 16px' }}>
                  {chunks.map((chunk, bi) => (
                    <SchoolBlock key={bi} schools={chunk} blockIdx={ci*10 + ri*5 + bi} />
                  ))}
                </div>

                {/* Inter-region breathing space */}
                <div style={{ height:60 }} />
              </div>
            );
          })}

          {/* Inter-era breathing space */}
          <div style={{ height:80 }} />
        </div>
      ))}

      {/* ══════════ COLOPHON ══════════ */}
      <div style={{ textAlign:'center', padding:'80px 32px', borderTop:'1px solid rgba(145,118,71,0.08)' }}>
        <p style={{ fontSize:12, color:'#A09080', fontFamily:'var(--font-sans)', margin:0 }}>
          九十五个哲学流派 · 一部横跨五千年的人类思想史图录</p>
        <div style={{ display:'flex', justifyContent:'center', gap:32, marginTop:32 }}>
          {[
            { l:'西方哲学', p:'/western-philosophies' },
            { l:'东方哲学', p:'/eastern-philosophies' },
            { l:'世界哲学', p:'/world-philosophies' },
          ].map(b => (
            <button key={b.p} onClick={() => nav(b.p)}
              style={{ background:'none', border:'1px solid rgba(145,118,71,0.10)', cursor:'pointer',
                fontFamily:'"Playfair Display",serif', fontSize:13, color:'#917647', padding:'6px 16px',
                borderRadius:4, transition:'all 300ms ease', opacity:0.7 }}
              onMouseEnter={e => { e.currentTarget.style.opacity='1'; e.currentTarget.style.borderColor='#917647'; }}
              onMouseLeave={e => { e.currentTarget.style.opacity='0.7'; e.currentTarget.style.borderColor='rgba(145,118,71,0.10)'; }}>
              {b.l}</button>
          ))}</div>
      </div>
    </div>
  );
}
