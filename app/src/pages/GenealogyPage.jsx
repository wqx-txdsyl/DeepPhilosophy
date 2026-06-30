/**
 * 哲学之河 — Museum of Philosophy V2
 * PRD-compliant: Cards = museum exhibits. River = timeline structure.
 * Scrolling = travelling upstream through civilization.
 */
import { useState, useEffect, useRef } from 'react';
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

function GenealogyPage() {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [hoveredCard, setHoveredCard] = useState(null);
  const pageRef = useRef(null);
  const [pageHeight, setPageHeight] = useState('100vh');

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });

    // Measure full page height after render
    const measure = () => {
      if (pageRef.current) {
        setPageHeight(pageRef.current.scrollHeight + 'px');
      }
    };
    measure();
    window.addEventListener('resize', measure);
    return () => { window.removeEventListener('scroll', onScroll); window.removeEventListener('resize', measure); };
  }, []);

  return (
    <div ref={pageRef} style={{ background:'#F8F6F2', minHeight:'100vh', fontFamily:'"Playfair Display","PingFang SC",serif', color:'#2A1F1A', position:'relative', overflow:'visible' }}>
      {/* Layer 1: Museum Paper */}
      <div style={{ position:'fixed',inset:0,zIndex:0,pointerEvents:'none',opacity:0.04,
        backgroundImage:'url(/schools/paper_texture.png)',backgroundSize:'400px',mixBlendMode:'multiply' }} />

      {/* Layer 1.5: Ancient Map */}
      <div style={{ position:'fixed',inset:0,zIndex:0,pointerEvents:'none',opacity:0.012,
        backgroundImage:'url(/schools/old_map_texture.png)',backgroundSize:'cover',backgroundPosition:'center',mixBlendMode:'multiply' }} />

      {/* Layer 2: River of Philosophy 2.0 — stretches to full content height, centered per PRD §23 */}
      <div style={{ position:'absolute',top:0,left:0,right:0,zIndex:0,pointerEvents:'none',height:pageHeight,
        display:'flex',justifyContent:'center',alignItems:'flex-start',overflow:'visible' }}>
        <img src="/schools/哲学之河2.0.png" alt="" style={{
          width:'32vw',minWidth:280,maxWidth:420,height:'100%',
          objectFit:'cover',objectPosition:'center',
          opacity:0.35,
          maskImage:'linear-gradient(to right,transparent 0%,rgba(0,0,0,0.6) 15%,rgba(0,0,0,0.8) 50%,rgba(0,0,0,0.6) 85%,transparent 100%)',
          WebkitMaskImage:'linear-gradient(to right,transparent 0%,rgba(0,0,0,0.6) 15%,rgba(0,0,0,0.8) 50%,rgba(0,0,0,0.6) 85%,transparent 100%)'
        }} />
      </div>

      {/* Layer 3: Constellation — Hero background per PRD §12 */}
      <div style={{ position:'absolute',top:0,left:0,right:0,zIndex:0,pointerEvents:'none',height:'85vh',
        backgroundImage:'url(/schools/哲学星图.png)',backgroundSize:'cover',backgroundPosition:'center',opacity:0.35 }} />

      {/* Golden particles */}
      {Array.from({length:5}).map((_,i)=>(<div key={'p'+i} style={{ position:'fixed',left:`${42+Math.random()*16}%`,top:`${Math.random()*100}%`,width:3,height:3,background:'#C4956A',borderRadius:'50%',opacity:0.12,pointerEvents:'none',zIndex:0,animation:`float-up ${8+Math.random()*6}s linear infinite`,animationDelay:`${i*1.5}s` }} />))}

      {/* HERO — Museum Entrance */}
      <section style={{ minHeight:'85vh',display:'flex',flexDirection:'column',justifyContent:'center',alignItems:'center',textAlign:'center',position:'relative',zIndex:1,padding:'60px 32px' }}>
        <div style={{ position:'absolute',top:'50%',left:'50%',transform:'translate(-50%,-50%)',width:'50vw',height:'50vh',background:'radial-gradient(ellipse,rgba(145,118,71,0.05) 0%,transparent 70%)',pointerEvents:'none' }} />
        <p style={{ fontSize:10,fontWeight:400,letterSpacing:'0.32em',textTransform:'uppercase',color:'#917647',marginBottom:28,fontFamily:'var(--font-sans)' }}>Museum of Philosophy</p>
        <h1 style={{ fontSize:'clamp(2.5rem,7vw,5.5rem)',fontWeight:700,fontStyle:'italic',color:'#2A1F1A',letterSpacing:'0.04em',lineHeight:1.1,marginBottom:20 }}>世界哲学谱系</h1>
        <div style={{ width:48,height:1.5,background:'#917647',marginBottom:24,opacity:0.5 }} />
        <p style={{ fontSize:'clamp(0.95rem,1.4vw,1.1rem)',fontWeight:300,color:'#7A6E64',lineHeight:1.9,maxWidth:560 }}>
          从公元前三十世纪至二十一世纪<br />九十七个流派，一部横跨五千年的人类思想史长卷</p>
        <button onClick={()=>document.getElementById('river-start')?.scrollIntoView({behavior:'smooth'})} style={{ marginTop:40,background:'#2A1F1A',color:'#F8F6F2',border:'none',borderRadius:4,padding:'14px 40px',fontSize:14,fontWeight:400,cursor:'pointer',letterSpacing:'0.08em',fontFamily:'var(--font-sans)',transition:'background 0.3s' }}
          onMouseEnter={e=>e.currentTarget.style.background='#917647'} onMouseLeave={e=>e.currentTarget.style.background='#2A1F1A'}>进入博物馆</button>
      </section>

      {/* Breathing space */}
      <div style={{ height:160 }} />

      {/* TIMELINE — Cards docked beside River */}
      <div id="river-start" style={{ position:'relative',zIndex:1,paddingBottom:120,maxWidth:1200,margin:'0 auto',padding:'0 24px' }}>
        {ALL_SCHOOLS.map((school,i) => {
          const isLeft = i%3!==1; const color=REGION_COLORS[school.region]; const isHov=hoveredCard===i;
          const fs=school.tier==='A'?22:school.tier==='B'?17:14; const cw=school.tier==='A'?420:school.tier==='B'?340:280;
          return (
            <div key={i} style={{ display:'flex',justifyContent:isLeft?'flex-start':'flex-end',marginBottom:school.tier==='A'?64:36,position:'relative',alignItems:'center' }}>
              <div style={{ position:'absolute',left:'50%',top:'50%',transform:'translate(-50%,-50%)',width:5,height:5,borderRadius:'50%',background:color,opacity:0.45,zIndex:2 }}>
                <div style={{ position:'absolute',top:'50%',[isLeft?'right':'left']:5,width:`calc(50vw - 140px)`,height:1,background:`linear-gradient(to ${isLeft?'left':'right'},${color}25,transparent)` }} />
              </div>
              <div onMouseEnter={()=>setHoveredCard(i)} onMouseLeave={()=>setHoveredCard(null)} onClick={()=>navigate('/school/'+encodeURIComponent(school.name))}
                style={{ background:'#FDFBF7',border:isHov?`1px solid rgba(145,118,71,0.3)`:'1px solid rgba(145,118,71,0.1)',borderRadius:16,padding:'18px 26px',maxWidth:cw,width:'100%',cursor:'pointer',
                  boxShadow:isHov?'0 8px 28px rgba(0,0,0,0.07)':'0 2px 8px rgba(0,0,0,0.03)',
                  transform:isHov?'translateY(-3px) scale(1.01)':'none',transition:'all 0.5s cubic-bezier(0.25,0.1,0.25,1)',position:'relative',zIndex:isHov?5:1,
                  marginLeft:isLeft?'2%':'auto',marginRight:isLeft?'auto':'2%' }}>
                <div style={{ fontSize:9,fontWeight:400,letterSpacing:'0.14em',textTransform:'uppercase',color,marginBottom:8,fontFamily:'var(--font-sans)' }}>
                  {school.region==='东方'?'Eastern':school.region==='西方'?'Western':'World'} · {school.century}</div>
                <h3 style={{ fontSize:fs,fontWeight:500,color:'#2A1F1A',margin:'0 0 6px',letterSpacing:'0.02em',lineHeight:1.3,fontFamily:'"Playfair Display","PingFang SC",serif' }}>{school.name}</h3>
                <p style={{ fontSize:12,fontWeight:300,color:'#7A6E64',lineHeight:1.7,margin:0,fontFamily:'var(--font-sans)' }}>{school.desc}</p>
                {isHov&&<div style={{ position:'absolute',top:0,left:24,right:24,height:1.5,background:`linear-gradient(to right,transparent,${color}50,transparent)`,borderRadius:2 }} />}
              </div>
            </div>
          );
        })}
      </div>

      {/* FOOTER */}
      <div style={{ textAlign:'center',paddingBottom:80,position:'relative',zIndex:1,display:'flex',justifyContent:'center',gap:48 }}>
        {[{label:'西方哲学传统 →',path:'/western-philosophies',color:REGION_COLORS['西方']},{label:'东方哲学传统 →',path:'/eastern-philosophies',color:REGION_COLORS['东方']},{label:'世界哲学传统 →',path:'/world-philosophies',color:REGION_COLORS['世界']}].map(btn=>(
          <button key={btn.path} onClick={()=>navigate(btn.path)} style={{ background:'none',border:'none',cursor:'pointer',fontFamily:'"Playfair Display",serif',fontSize:15,fontWeight:400,color:btn.color,letterSpacing:'0.04em',padding:'8px 16px',transition:'opacity 0.2s' }}
            onMouseEnter={e=>e.currentTarget.style.opacity='0.6'} onMouseLeave={e=>e.currentTarget.style.opacity='1'}>{btn.label}</button>
        ))}</div>

      <style>{`@keyframes float-up{0%{transform:translateY(100vh);opacity:0}10%{opacity:0.5}90%{opacity:0.1}100%{transform:translateY(-10vh);opacity:0}}`}</style>
    </div>
  );
}

export default GenealogyPage;
