/**
 * 哲学之河 — Genealogy Redesigned
 * The River of Philosophy as the structural skeleton of the page.
 * Museum-quality cards + parallax + atmosphere transitions + golden particles.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

// ============================================================
// School data — all 84 schools with century, region, description
// ============================================================
const ALL_SCHOOLS = [
  { century:'公元前30世纪', name:'美索不达米亚哲学', region:'世界', desc:'苏美尔智慧文学追问苦难与秩序——人类最早的哲学追问。' },
  { century:'公元前15世纪', name:'印度哲学', region:'世界', desc:'《吠陀》《奥义书》为源头，六派哲学追问解脱。' },
  { century:'公元前15世纪', name:'犹太哲学', region:'世界', desc:'从斐洛到列维纳斯——雅典与耶路撒冷之间。' },
  { century:'公元前10世纪', name:'波斯哲学', region:'世界', desc:'琐罗亚斯德教善恶二元论——两千五百年的连续传统。' },
  { century:'公元前6世纪', name:'道家', region:'东方', desc:'道法自然，无为而治。' },
  { century:'公元前6世纪', name:'儒家', region:'东方', desc:'以仁为核心，以礼为规范。' },
  { century:'公元前6世纪', name:'古希腊哲学', region:'西方', desc:'西方哲学总源——以理性思辨取代神话解释。' },
  { century:'公元前5世纪', name:'墨家', region:'东方', desc:'兼爱非攻，尚贤节用。' },
  { century:'公元前5世纪', name:'兵家', region:'东方', desc:'知己知彼，不战屈人。' },
  { century:'公元前4世纪', name:'法家', region:'东方', desc:'以法治国，不别亲疏。' },
  { century:'公元前4世纪', name:'名家', region:'东方', desc:'白马非马——中国最早的逻辑学。' },
  { century:'公元前4世纪', name:'阴阳家', region:'东方', desc:'阴阳消长，五德终始。' },
  { century:'公元前2世纪', name:'两汉经学', region:'东方', desc:'通经致用，以经为法。' },
  { century:'3世纪', name:'魏晋玄学', region:'东方', desc:'越名教而任自然。' },
  { century:'4世纪', name:'教父哲学', region:'西方', desc:'以希腊理性为基督教信仰奠基。' },
  { century:'6世纪', name:'隋唐佛学', region:'东方', desc:'八宗竞秀，会通中印。' },
  { century:'7世纪', name:'伊斯兰哲学', region:'世界', desc:'凯拉姆与苏非——理性与启示的对话。' },
  { century:'7世纪', name:'阿拉伯哲学', region:'世界', desc:'铿迪、法拉比、阿维森纳——中世纪哲学桥梁。' },
  { century:'8世纪', name:'西藏哲学', region:'世界', desc:'宗喀巴体系——藏传佛教中观应成派。' },
  { century:'11世纪', name:'宋明理学', region:'东方', desc:'为天地立心，为生民立命。' },
  { century:'11世纪', name:'经院哲学', region:'西方', desc:'以亚里士多德逻辑构建理性圣殿。' },
  { century:'11世纪', name:'唯名论', region:'西方', desc:'共相只是名称不是实在。' },
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
  { century:'21世纪', name:'技术哲学', region:'西方', desc:'技术不是中立的工具。' },
  { century:'21世纪', name:'习近平新时代中国特色社会主义思想', region:'东方', desc:'以人民为中心的发展思想。' },
];

const REGION_COLORS = { '西方': '#C4956A', '东方': '#3A5A7C', '世界': '#5A8A5A' };
const REGION_LABELS = { '西方': 'Western', '东方': 'Eastern', '世界': 'World' };

// ============================================================
// Main Component
// ============================================================
function GenealogyPage() {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [hoveredCard, setHoveredCard] = useState(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Calculate river opacity based on scroll position
  const getRiverOpacity = (index, total) => {
    const pct = index / total;
    // The river fades in and out — strongest at hero, fading through timeline
    return 0.03 + 0.12 * Math.sin(pct * Math.PI * 2.5) * (1 - pct * 0.7);
  };

  return (
    <div ref={containerRef} style={{
      background: '#F8F6F2',
      minHeight: '100vh',
      fontFamily: '"Playfair Display", "PingFang SC", serif',
      color: '#3A2E28',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* ================================================ */}
      {/* RIVER LAYER — the artwork as structural skeleton */}
      {/* ================================================ */}
      <div style={{
        position: 'fixed',
        top: 0, left: '50%', transform: 'translateX(-50%)',
        width: '30%', minWidth: 300, maxWidth: 500,
        height: '100vh', zIndex: 0,
        pointerEvents: 'none',
      }}>
        <img src="/schools/哲学之河.png" alt=""
          style={{
            width: '100%', height: '200%',
            objectFit: 'cover', objectPosition: 'center top',
            transform: `translateY(${-scrollY * 0.4}px)`,
            opacity: 0.15,
            maskImage: 'linear-gradient(to right, transparent 0%, black 30%, black 70%, transparent 100%)',
            WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 30%, black 70%, transparent 100%)',
          }} />
      </div>

      {/* ================================================ */}
      {/* HERO — River begins here */}
      {/* ================================================ */}
      <section style={{
        minHeight: '80vh', display: 'flex', flexDirection: 'column', justifyContent: 'center',
        alignItems: 'center', textAlign: 'center', position: 'relative', zIndex: 1,
        padding: '60px 32px',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'radial-gradient(ellipse at 50% 40%, rgba(196,149,106,0.06) 0%, transparent 70%)',
        }} />
        <p style={{
          fontSize: 11, fontWeight: 500, letterSpacing: '0.28em', textTransform: 'uppercase',
          color: '#C4956A', marginBottom: 24, fontFamily: 'var(--font-sans)',
        }}>The River of Philosophy</p>
        <h1 style={{
          fontSize: 'clamp(2.5rem, 6vw, 5rem)', fontWeight: 400, fontStyle: 'italic',
          color: '#2A1F1A', letterSpacing: '0.03em', lineHeight: 1.15, marginBottom: 16,
        }}>哲学之河</h1>
        <div style={{ width: 60, height: 1.5, background: '#C4956A', marginBottom: 20, opacity: 0.6 }} />
        <p style={{
          fontSize: 'clamp(1rem, 1.6vw, 1.2rem)', fontWeight: 400, color: '#6B5E53',
          lineHeight: 1.8, maxWidth: 560,
        }}>
          从公元前三十世纪至二十一世纪<br />
          八十四个流派，一部横跨五千年的人类思想史长卷
        </p>
        <button onClick={() => {
          document.getElementById('river-start')?.scrollIntoView({ behavior: 'smooth' });
        }} style={{
          marginTop: 36, background: '#2A1F1A', color: '#F8F6F2', border: 'none',
          borderRadius: 4, padding: '14px 36px', fontSize: 14, fontWeight: 500,
          cursor: 'pointer', letterSpacing: '0.06em', fontFamily: 'var(--font-sans)',
          transition: 'all 0.3s',
        }}
          onMouseEnter={e => e.currentTarget.style.background = '#C4956A'}
          onMouseLeave={e => e.currentTarget.style.background = '#2A1F1A'}>
          开始探索 ↓
        </button>
      </section>

      {/* ================================================ */}
      {/* TIMELINE CARDS — docking beside the river */}
      {/* ================================================ */}
      <div id="river-start" style={{ position: 'relative', zIndex: 1, paddingBottom: 80 }}>
        {ALL_SCHOOLS.map((school, i) => {
          const isLeft = i % 3 === 0 || i % 3 === 2;
          const isWorld = school.region === '世界';
          const color = REGION_COLORS[school.region];
          const riverOpacity = getRiverOpacity(i, ALL_SCHOOLS.length);
          const isHovered = hoveredCard === i;

          return (
            <div key={i} style={{
              position: 'relative',
              display: 'flex',
              justifyContent: isLeft ? 'flex-start' : 'flex-end',
              paddingLeft: isLeft ? '5%' : '55%',
              paddingRight: isLeft ? '55%' : '5%',
              marginBottom: isWorld ? 48 : 24,
              zIndex: 1,
            }}>
              {/* River connector — thin elegant line */}
              <div style={{
                position: 'absolute',
                left: '50%', top: '50%',
                width: isLeft ? 'calc(50% - 5%)' : 'calc(50% - 5%)',
                height: 1,
                background: `linear-gradient(to ${isLeft ? 'right' : 'left'}, transparent, ${color}40)`,
                transform: 'translateY(-50%)',
                [isLeft ? 'right' : 'left']: '50%',
              }} />

              {/* Century badge on river */}
              <div style={{
                position: 'absolute',
                left: '50%', top: '50%',
                transform: 'translate(-50%, -50%)',
                zIndex: 2,
              }}>
                <div style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: color, opacity: 0.6 + riverOpacity * 3,
                }} />
              </div>

              {/* Card */}
              <div
                onMouseEnter={() => setHoveredCard(i)}
                onMouseLeave={() => setHoveredCard(null)}
                onClick={() => navigate('/school/' + encodeURIComponent(school.name))}
                style={{
                  background: isHovered ? '#FFFFFF' : '#FBFAF7',
                  border: isHovered ? `1px solid ${color}60` : '1px solid #E8E3DA',
                  borderRadius: 12,
                  padding: '16px 22px',
                  maxWidth: 420, width: '100%',
                  cursor: 'pointer',
                  boxShadow: isHovered
                    ? `0 8px 24px rgba(0,0,0,0.08), 0 0 0 1px ${color}30`
                    : '0 1px 3px rgba(0,0,0,0.04)',
                  transition: 'all 0.35s cubic-bezier(0.25, 0.1, 0.25, 1)',
                  position: 'relative',
                  zIndex: isHovered ? 5 : 1,
                }}
              >
                {/* Century label */}
                <div style={{
                  fontSize: 9, fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase',
                  color, marginBottom: 6, fontFamily: 'var(--font-sans)',
                }}>
                  {REGION_LABELS[school.region]} · {school.century}
                </div>

                {/* School name */}
                <h3 style={{
                  fontSize: 18, fontWeight: 500, color: '#2A1F1A',
                  margin: '0 0 6px', letterSpacing: '0.02em',
                  fontFamily: '"Playfair Display", "PingFang SC", serif',
                }}>
                  {school.name}
                </h3>

                {/* Description */}
                <p style={{
                  fontSize: 12, fontWeight: 300, color: '#8B7E74',
                  lineHeight: 1.6, margin: 0,
                  fontFamily: 'var(--font-sans)',
                }}>
                  {school.desc}
                </p>

                {/* Gold accent on hover */}
                {isHovered && (
                  <div style={{
                    position: 'absolute', top: -1, left: 20, right: 20, height: 2,
                    background: `linear-gradient(to right, transparent, ${color}80, transparent)`,
                    borderRadius: 2,
                  }} />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* ================================================ */}
      {/* FOOTER */}
      {/* ================================================ */}
      <div style={{
        textAlign: 'center', paddingBottom: 60, position: 'relative', zIndex: 1,
        display: 'flex', justifyContent: 'center', gap: 40,
      }}>
        {[
          { label: '西方哲学传统 →', path: '/western-philosophies', color: REGION_COLORS['西方'] },
          { label: '东方哲学传统 →', path: '/eastern-philosophies', color: REGION_COLORS['东方'] },
          { label: '世界哲学传统 →', path: '/world-philosophies', color: REGION_COLORS['世界'] },
        ].map(btn => (
          <button key={btn.path} onClick={() => navigate(btn.path)} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontFamily: '"Playfair Display", serif', fontSize: 15, fontWeight: 400,
            color: btn.color, letterSpacing: '0.04em',
            padding: '8px 16px', transition: 'opacity 0.2s',
          }}
            onMouseEnter={e => e.currentTarget.style.opacity = '0.6'}
            onMouseLeave={e => e.currentTarget.style.opacity = '1'}>
            {btn.label}
          </button>
        ))}
      </div>

      {/* ================================================ */}
      {/* GOLDEN PARTICLES — subtle floating light dots */}
      {/* ================================================ */}
      <style>{`
        @keyframes float-up {
          0% { transform: translateY(100vh) translateX(0); opacity: 0; }
          10% { opacity: 0.4; }
          90% { opacity: 0.1; }
          100% { transform: translateY(-10vh) translateX(20px); opacity: 0; }
        }
        .river-particle {
          position: fixed;
          width: 2px; height: 2px;
          background: #C4956A;
          border-radius: 50%;
          pointer-events: none;
          z-index: 0;
          animation: float-up 8s linear infinite;
        }
      `}</style>
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="river-particle" style={{
          left: `${44 + Math.random() * 12}%`,
          animationDelay: `${i * 1.3}s`,
          animationDuration: `${6 + Math.random() * 8}s`,
          opacity: 0.15,
        }} />
      ))}
    </div>
  );
}

export default GenealogyPage;
