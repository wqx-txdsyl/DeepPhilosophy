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
    <div className="page-container" style={{ paddingBottom: 60 }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 16px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <button
            onClick={() => navigate('/genealogy')}
            style={{
              background: 'none', border: 'none', fontSize: 22, cursor: 'pointer',
              color: 'var(--text-dim)', padding: '4px 8px', lineHeight: 1,
            }}
            aria-label="返回"
          >
            ←
          </button>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>🌍 世界哲学传统</h2>
        </div>
        <p style={{ color: 'var(--text-dim)', fontSize: 13, margin: '0 0 28px', lineHeight: 1.7 }}>
          除了东西方两大哲学谱系，世界上还有丰富的哲学传统值得探索。以下八大哲学传统覆盖了从南亚到非洲、从中东到拉美的广阔思想版图。
        </p>

        {/* Cards Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: 16,
        }}>
          {WORLD_PHILOSOPHIES.map((phil) => (
            <div
              key={phil.name}
              onClick={() => navigate('/school/' + encodeURIComponent(phil.name))}
              style={{
                background: 'var(--secondary)',
                borderRadius: 12,
                padding: '18px 20px',
                border: '1px solid var(--border)',
                borderLeft: '5px solid ' + phil.color,
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                cursor: 'pointer',
              }}
            >
              <h3 style={{
                fontSize: 17,
                fontWeight: 700,
                color: phil.color,
                margin: 0,
              }}>
                {phil.name}
              </h3>
              <p style={{
                fontSize: 13,
                color: 'var(--text-dim)',
                margin: 0,
                lineHeight: 1.75,
              }}>
                {phil.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <p style={{
          textAlign: 'center',
          color: 'var(--text-dim)',
          fontSize: 12,
          marginTop: 32,
          opacity: 0.6,
        }}>
          更多哲学传统持续收录中 · 详情页即将上线
        </p>
      </div>
    </div>
  );
}
