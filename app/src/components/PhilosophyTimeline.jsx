/**
 * 世界哲学时间轴 — 左时间线 + 三列(西方/东方/世界)渐变色
 */
import { useNavigate } from 'react-router-dom';

const ALL_SCHOOLS = [
  // 公元前30世纪
  { century:'公元前30世纪', name:'美索不达米亚哲学', region:'世界', desc:'苏美尔智慧文学追问苦难与秩序——人类最早的哲学追问。' },
  // 公元前15世纪
  { century:'公元前15世纪', name:'印度哲学', region:'世界', desc:'《吠陀》《奥义书》为源头，六派哲学追问解脱。' },
  { century:'公元前15世纪', name:'犹太哲学', region:'世界', desc:'从斐洛到列维纳斯，在雅典与耶路撒冷之间。' },
  // 公元前10世纪
  { century:'公元前10世纪', name:'波斯哲学', region:'世界', desc:'琐罗亚斯德教善恶二元论——两千五百年的连续传统。' },
  // 公元前6世纪
  { century:'公元前6世纪', name:'道家', region:'东方', desc:'道法自然，无为而治——以柔克刚的东方智慧。' },
  { century:'公元前6世纪', name:'儒家', region:'东方', desc:'以仁为核心，以礼为规范——修身齐家治国平天下。' },
  { century:'公元前6世纪', name:'古希腊哲学', region:'西方', desc:'西方哲学总源——以理性思辨取代神话解释。' },
  // 公元前5世纪
  { century:'公元前5世纪', name:'墨家', region:'东方', desc:'兼爱非攻，尚贤节用——先秦最激进的平等主义。' },
  { century:'公元前5世纪', name:'兵家', region:'东方', desc:'知己知彼，不战屈人——冲突的博弈艺术。' },
  // 公元前4世纪
  { century:'公元前4世纪', name:'法家', region:'东方', desc:'以法治国，不别亲疏——制度先于道德。' },
  { century:'公元前4世纪', name:'名家', region:'东方', desc:'白马非马——中国最早的逻辑学与语言哲学。' },
  { century:'公元前4世纪', name:'阴阳家', region:'东方', desc:'阴阳消长，五德终始——宇宙论框架。' },
  // 公元前2世纪
  { century:'公元前2世纪', name:'两汉经学', region:'东方', desc:'通经致用，以经为法——天人感应的政治神学。' },
  // 3世纪
  { century:'3世纪', name:'魏晋玄学', region:'东方', desc:'越名教而任自然——乱世中的精神自由。' },
  // 4世纪
  { century:'4世纪', name:'教父哲学', region:'西方', desc:'以希腊理性为基督教信仰奠基。' },
  // 6世纪
  { century:'6世纪', name:'隋唐佛学', region:'东方', desc:'八宗竞秀，会通中印——佛教中国化。' },
  // 7世纪
  { century:'7世纪', name:'伊斯兰哲学', region:'世界', desc:'凯拉姆与苏非——理性与启示的对话。' },
  { century:'7世纪', name:'阿拉伯哲学', region:'世界', desc:'铿迪、法拉比、阿维森纳——中世纪哲学桥梁。' },
  // 8世纪
  { century:'8世纪', name:'西藏哲学', region:'世界', desc:'宗喀巴体系——藏传佛教中观应成派。' },
  // 11世纪
  { century:'11世纪', name:'宋明理学', region:'东方', desc:'为天地立心，为生民立命。' },
  { century:'11世纪', name:'经院哲学', region:'西方', desc:'以亚里士多德逻辑构建理性圣殿。' },
  { century:'11世纪', name:'唯名论', region:'西方', desc:'共相只是名称不是实在。' },
  // 13世纪
  { century:'13世纪', name:'非洲哲学', region:'世界', desc:'乌班图与去殖民化——口述传统的共同体本体论。' },
  // 15世纪
  { century:'15世纪', name:'拉丁美洲哲学', region:'世界', desc:'从拉斯·卡萨斯到杜塞尔——解放的哲学。' },
  { century:'15世纪', name:'玛雅哲学', region:'世界', desc:'《波波尔·乌》——循环时间观与玉米人。' },
  { century:'15世纪', name:'阿兹特克哲学', region:'世界', desc:'第五太阳纪——花与歌的哲学回应。' },
  // 16世纪
  { century:'16世纪', name:'东南亚哲学', region:'世界', desc:'上座部佛教与本土智慧的交融。' },
  { century:'16世纪', name:'韩国哲学', region:'世界', desc:'性理学与实学——从四端七情到主体思想。' },
  // 17世纪
  { century:'17世纪', name:'明清实学', region:'东方', desc:'经世致用，实事求是。' },
  { century:'17世纪', name:'乾嘉朴学', region:'东方', desc:'无征不信，孤证不立。' },
  { century:'17世纪', name:'理性主义', region:'西方', desc:'以数学公理为范本，从自明原理演绎知识。' },
  { century:'17世纪', name:'经验主义', region:'西方', desc:'一切知识起源于感觉经验。' },
  // 18世纪
  { century:'18世纪', name:'启蒙运动', region:'西方', desc:'敢于运用你自己的理性。' },
  { century:'18世纪', name:'实在论', region:'西方', desc:'存在独立于心灵。' },
  { century:'18世纪', name:'唯心主义', region:'西方', desc:'实在的本质是精神或观念。' },
  { century:'18世纪', name:'自由主义', region:'西方', desc:'个人自由是最高政治价值。' },
  { century:'18世纪', name:'浪漫主义', region:'西方', desc:'以情感和想象反抗启蒙理性。' },
  // 19世纪
  { century:'19世纪', name:'德国古典哲学', region:'西方', desc:'从康德到黑格尔的哲学革命。' },
  { century:'19世纪', name:'功利主义', region:'西方', desc:'最大多数人的最大幸福。' },
  { century:'19世纪', name:'超验主义', region:'西方', desc:'美国精神独立宣言。' },
  { century:'19世纪', name:'实证主义', region:'西方', desc:'只问如何不问为何。' },
  { century:'19世纪', name:'马克思主义', region:'西方', desc:'问题在于改变世界。' },
  { century:'19世纪', name:'生命哲学', region:'西方', desc:'理性不能穷尽生命。' },
  { century:'19世纪', name:'社会学', region:'西方', desc:'追问社会何以可能。' },
  { century:'19世纪', name:'北欧哲学', region:'世界', desc:'克尔凯郭尔的信仰跳跃。' },
  { century:'19世纪', name:'东欧斯拉夫哲学', region:'世界', desc:'索洛维约夫、舍斯托夫——第三条道路。' },
  { century:'19世纪', name:'北美哲学', region:'世界', desc:'实用主义与超验主义——观念投入实践。' },
  // 19世纪末
  { century:'19世纪末', name:'天演论', region:'东方', desc:'物竞天择，适者生存。' },
  { century:'19世纪末', name:'维新派', region:'东方', desc:'变则通，通则久。' },
  // 20世纪初
  { century:'20世纪初', name:'实用主义', region:'西方', desc:'真理即有用，意义在于效果。' },
  { century:'20世纪初', name:'精神分析学', region:'西方', desc:'心灵深处有一个你不知道的你。' },
  { century:'20世纪初', name:'现象学', region:'西方', desc:'回到事物本身。' },
  { century:'20世纪初', name:'存在主义', region:'西方', desc:'存在先于本质。' },
  { century:'20世纪初', name:'分析哲学', region:'西方', desc:'全部哲学就是语言的批判。' },
  { century:'20世纪初', name:'过程哲学', region:'西方', desc:'实在是生成而非存在。' },
  { century:'20世纪初', name:'哲学人类学', region:'西方', desc:'人是什么。' },
  { century:'20世纪初', name:'三民主义', region:'东方', desc:'民族、民权、民生。' },
  { century:'20世纪初', name:'旧民主主义', region:'东方', desc:'探索民主共和道路。' },
  // 20世纪中
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
  // 20世纪末
  { century:'20世纪末', name:'后结构主义', region:'西方', desc:'解构逻各斯中心主义。' },
  { century:'20世纪末', name:'后现代主义', region:'西方', desc:'对宏大叙事的怀疑。' },
  { century:'20世纪末', name:'伦理学', region:'西方', desc:'追问人应该如何生活。' },
  { century:'20世纪末', name:'宗教哲学', region:'西方', desc:'以理性审视信仰。' },
  { century:'20世纪末', name:'女性主义', region:'西方', desc:'个人的即政治的。' },
  { century:'20世纪末', name:'社群主义', region:'西方', desc:'自我镶嵌于共同体之中。' },
  { century:'20世纪末', name:'现代新儒家', region:'东方', desc:'返本开新，内圣外王。' },
  { century:'20世纪末', name:'中国实证哲学', region:'东方', desc:'大胆假设，小心求证。' },
  { century:'20世纪末', name:'马克思主义哲学的中国化与体系化', region:'东方', desc:'实践标准到理论体系。' },
  { century:'20世纪末', name:'蒙古中亚哲学', region:'世界', desc:'萨满传统与长生天。' },
  { century:'20世纪末', name:'澳洲原住民哲学', region:'世界', desc:'梦时代——最古老文明的生命智慧。' },
  // 21世纪
  { century:'21世纪', name:'技术哲学', region:'西方', desc:'技术不是中立的工具。' },
  { century:'21世纪', name:'习近平新时代中国特色社会主义思想', region:'东方', desc:'以人民为中心的发展思想。' },
];

// Region colors
const REGION_COLORS = { '西方': 'var(--ochre)', '东方': 'var(--prussian)', '世界': '#5A8A5A' };

// Group by century
const centuries = [];
let last = '';
for (const s of ALL_SCHOOLS) {
  if (s.century !== last) { last = s.century; centuries.push({ century: last, schools: [] }); }
  centuries[centuries.length-1].schools.push(s);
}

export default function PhilosophyTimeline() {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '48px 24px 40px', position: 'relative' }}>
      <h2 style={{ textAlign:'center', fontFamily:'\"Playfair Display\",serif', fontSize:24, fontWeight:400, color:'var(--ink)', marginBottom:40, letterSpacing:'0.04em' }}>世界哲学时间轴</h2>

      {/* Column headers */}
      <div style={{ display:'flex', marginBottom:24, paddingLeft:120 }}>
        {['东方哲学','西方哲学','世界哲学'].map((r, i) => (
          <div key={r} style={{ flex:1, textAlign:'center' }}>
            <span style={{ fontSize:13, fontWeight:600, color:REGION_COLORS[r==='东方哲学'?'东方':r==='西方哲学'?'西方':'世界'], letterSpacing:'0.06em' }}>
              {r==='东方哲学'?'☯ ':r==='西方哲学'?'🏛 ':'🌍 '}{r}
            </span>
          </div>
        ))}
      </div>

      {/* Timeline */}
      {centuries.map((era, ei) => {
        // Split schools into columns
        const east = era.schools.filter(s => s.region === '东方');
        const west = era.schools.filter(s => s.region === '西方');
        const world = era.schools.filter(s => s.region === '世界');
        const maxRows = Math.max(east.length, west.length, world.length, 1);

        return (
          <div key={ei} style={{ display:'flex', marginBottom:32, position:'relative' }}>
            {/* Century label */}
            <div style={{ width:110, flexShrink:0, paddingTop:8, textAlign:'right', paddingRight:20 }}>
              <div style={{ width:8, height:8, borderRadius:'50%', background:ei===0?'var(--ochre)':'var(--bone)', border:'2px solid var(--ochre)', display:'inline-block', marginBottom:4 }} />
              <div style={{ fontFamily:'\"Playfair Display\",serif', fontSize:11, fontWeight:500, color:'var(--ochre)', letterSpacing:'0.05em' }}>{era.century}</div>
            </div>

            {/* Three columns */}
            {[east, west, world].map((col, ci) => (
              <div key={ci} style={{ flex:1, padding:'0 4px', borderLeft: ci>0?'1px solid var(--border)':'none' }}>
                {Array.from({length: maxRows}).map((_, ri) => {
                  const s = col[ri];
                  if (!s) return <div key={ri} style={{ height:60 }} />;
                  const color = REGION_COLORS[s.region];
                  // Generate gradient based on position in era
                  const opacity = 1 - (ri / maxRows) * 0.3;
                  return (
                    <div key={s.name}
                      onClick={() => navigate('/school/' + encodeURIComponent(s.name))}
                      style={{
                        padding:'4px 8px', marginBottom:2, cursor:'pointer',
                        borderLeft:'3px solid ' + color, opacity,
                        transition:'all 0.2s', background:'transparent',
                        minHeight: ri===col.length-1 ? 'auto' : 56,
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background='var(--card-bg)'; e.currentTarget.style.opacity='1'; }}
                      onMouseLeave={e => { e.currentTarget.style.background='transparent'; e.currentTarget.style.opacity=opacity; }}
                    >
                      <div style={{ fontSize:13, fontWeight:500, color:'var(--ink)', marginBottom:1 }}>{s.name}</div>
                      {s.desc && <div style={{ fontSize:10, color:'var(--text-dim)', lineHeight:1.4, maxHeight:28, overflow:'hidden' }}>{s.desc}</div>}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        );
      })}

      {/* Footer links */}
      <div style={{ textAlign:'center', paddingBottom:32, display:'flex', justifyContent:'center', gap:32, marginTop:24 }}>
        {[
          { label:'西方哲学传统 →', path:'/western-philosophies', color:'var(--ochre)' },
          { label:'东方哲学传统 →', path:'/eastern-philosophies', color:'var(--prussian)' },
          { label:'世界哲学传统 →', path:'/world-philosophies', color:'#5A8A5A' },
        ].map(btn => (
          <button key={btn.path} onClick={() => navigate(btn.path)}
            style={{ background:'none',border:'none',cursor:'pointer',fontFamily:'\"Playfair Display\",serif',fontSize:15,fontWeight:400,color:btn.color,letterSpacing:'0.04em',padding:'8px 16px',transition:'opacity 0.2s' }}
            onMouseEnter={e=>e.currentTarget.style.opacity='0.6'} onMouseLeave={e=>e.currentTarget.style.opacity='1'}>
            {btn.label}
          </button>
        ))}
      </div>
    </div>
  );
}
