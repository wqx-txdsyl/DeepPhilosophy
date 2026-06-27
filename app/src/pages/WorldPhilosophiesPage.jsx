/**
 * WorldPhilosophiesPage - 世界哲学传统概览
 * 展示印度、日本、伊斯兰、阿拉伯、非洲、犹太、波斯、拉丁美洲、东南亚哲学
 */
import { useNavigate } from 'react-router-dom';

const WORLD_PHILOSOPHIES = [
  {
    name: '印度哲学',
    color: '#C4743A',
    desc: '以《吠陀》《奥义书》为源头，正统六派（吠檀多、数论、瑜伽、胜论、正理、弥曼差）与非正统的佛教、耆那教、顺世论共同构成了人类对意识、空性和自我最深刻的哲学追问。核心关切是"解脱"——如何从轮回中解放。',
  },
  {
    name: '日本哲学',
    color: '#C44A6B',
    desc: '在神道、佛教（禅宗）和儒学的三重影响下形成了独特的"共感"传统。京都学派以西田几多郎"场所的逻辑"和"绝对无"为核心，将禅宗精神与西方哲学创造性融合，为世界哲学做出了原创性贡献。',
  },
  {
    name: '伊斯兰阿拉伯哲学',
    color: '#3A8C6B',
    desc: '中世纪保存和发展希腊哲学的关键桥梁。法尔萨法（铿迪、法拉比、阿维森纳、阿威罗伊）将亚里士多德与伊斯兰教义融合；凯拉姆以理性捍卫教义；苏非主义以内在修行直观体验神。深刻影响了欧洲经院哲学。',
  },
  {
    name: '非洲哲学',
    color: '#C4882E',
    desc: '以口述传统和"乌班图"（我在因我们在）的共同体本体论为核心。政治哲学关注去殖民化和泛非主义；部族哲学从谚语和口传中挖掘智慧；智者哲学关注部落中长者的口述传统。',
  },
  {
    name: '犹太哲学',
    color: '#4A6BBF',
    desc: '以理性与信仰的永恒对话为核心。从斐洛的希腊化诠释到迈蒙尼德调和亚里士多德与犹太教，再到布伯"我与你"、列维纳斯"他者的面孔"，犹太哲学始终在雅典与耶路撒冷之间追问。',
  },
  {
    name: '波斯哲学',
    color: '#8B3A5C',
    desc: '超过两千五百年的连续传统。前伊斯兰时期以琐罗亚斯德教善恶二元论和自由意志问题为起点；伊斯兰时期贡献了阿维森纳和苏赫拉瓦迪的光照哲学——以光为宇宙本原，融合柏拉图理念论与琐罗亚斯德光明智慧。',
  },
  {
    name: '拉丁美洲哲学',
    color: '#C44A3A',
    desc: '以解放为核心主题。从殖民时期拉斯·卡萨斯为印第安人权利辩护，到何塞·马蒂"我们的美洲"，再到杜塞尔解放哲学和弗莱雷被压迫者教育学，将哲学从书斋转向穷人和原住民的声音。',
  },
  {
    name: '东南亚哲学',
    color: '#3A7B8C',
    desc: '在印度教、佛教、伊斯兰教和本土万物有灵论交汇中形成独特的"和谐"智慧。印尼潘查希拉将多元统一上升为政治哲学；泰国适足经济哲学以中道为核心；菲律宾kapwa展示共同体式的自我理解。',
  },
];

export default function WorldPhilosophiesPage() {
  const navigate = useNavigate();

  return (
    <div className="page-container" style={{ paddingBottom: 80 }}>

      {/* ══════════ HERO ══════════ */}
      <section style={{ padding: '72px 32px 48px', textAlign: 'center', maxWidth: 720, margin: '0 auto' }}>
        <button onClick={() => navigate('/genealogy')} style={{
          background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13,
          color: 'var(--text-dim)', letterSpacing: '0.04em', marginBottom: 32, padding: 0
        }}>← 返回谱系</button>
        <p style={{
          fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 500,
          letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--ochre)', margin: '0 0 16px'
        }}>
          World Philosophies
        </p>
        <h1 style={{
          fontFamily: '"Playfair Display", "PingFang SC", serif',
          fontSize: 'clamp(2rem, 5vw, 3rem)', fontWeight: 400, color: 'var(--ink)',
          letterSpacing: '0.04em', lineHeight: 1.2, margin: '0 0 20px'
        }}>
          世界哲学传统
        </h1>
        <p style={{
          fontFamily: 'var(--font-sans)', fontSize: 15, fontWeight: 300,
          color: 'var(--text-dim)', lineHeight: 1.8, maxWidth: 500, margin: '0 auto'
        }}>
          除了东西方两大谱系，从南亚到非洲、从中东到拉美，<br />八大哲学传统覆盖了广阔的思想版图。
        </p>
        <div style={{ width: 40, height: 1, background: 'var(--ochre)', margin: '28px auto 0', opacity: 0.4 }} />
      </section>

      {/* ══════════ CARDS — editorial gallery ══════════ */}
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 32px 64px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 24,
        }}>
          {WORLD_PHILOSOPHIES.map((phil) => (
            <div
              key={phil.name}
              onClick={() => navigate('/school/' + encodeURIComponent(phil.name))}
              style={{
                padding: '24px 0', cursor: 'pointer',
                borderBottom: '1px solid var(--border)',
                transition: 'all 0.25s', background: 'transparent'
              }}
              onMouseEnter={e => { e.currentTarget.style.borderBottomColor = phil.color; }}
              onMouseLeave={e => { e.currentTarget.style.borderBottomColor = 'var(--border)'; }}
            >
              <h3 style={{
                fontFamily: '"Playfair Display", "PingFang SC", serif',
                fontSize: 22, fontWeight: 400, color: 'var(--ink)',
                letterSpacing: '0.03em', margin: '0 0 8px'
              }}>
                {phil.name}
              </h3>
              <p style={{
                fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 300,
                color: 'var(--text-dim)', lineHeight: 1.8, margin: 0
              }}>
                {phil.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════ FOOTER ══════════ */}
      <p style={{
        textAlign: 'center', color: 'var(--fade)', fontSize: 12, fontFamily: 'var(--font-sans)',
        fontWeight: 300, paddingBottom: 24
      }}>
        更多哲学传统持续收录中
      </p>
    </div>
  );
}
