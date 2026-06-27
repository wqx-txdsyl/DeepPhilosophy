/**
 * WorldPhilosophiesPage - 世界哲学传统概览
 * 展示印度、日本、伊斯兰、阿拉伯、非洲、犹太、波斯、拉丁美洲、东南亚哲学
 */
import { useNavigate } from 'react-router-dom';

const WORLD_PHILOSOPHIES = [
  {
    name: '印度哲学',
    color: '#C4743A',
    desc: '印度哲学是世界上最古老的哲学传统之一，以《吠陀》《奥义书》为源头，分化出正统六派（数论、瑜伽、正理、胜论、弥曼差、吠檀多）和非正统的佛教、耆那教哲学。核心关切是"解脱"（moksha）——如何从轮回中解放。商羯罗的不二论、龙树的中观、世亲的唯识，构成了人类对意识、空性和自我最深刻的哲学追问。',
  },
  {
    name: '日本哲学',
    color: '#C44A6B',
    desc: '日本哲学在神道、佛教（特别是禅宗）和儒学的三重影响下形成了独特的"共感"传统。西田几多郎以"纯粹经验"和"场所的逻辑"创立京都学派，将禅的"无"与西方哲学对话；和辻哲郎以"风土"和"间柄"将伦理学从个体转向"之间"；九鬼周造对"粹"的现象学分析呈现了日本美学的哲学深度。',
  },
  {
    name: '伊斯兰哲学',
    color: '#3A8C6B',
    desc: '伊斯兰哲学（falsafa）在8-12世纪达到了辉煌高峰，以肯迪、法拉比、伊本·西纳（阿维森纳）、伊本·鲁世德（阿威罗伊）为代表，将亚里士多德和新柏拉图主义与伊斯兰教义融合。伊本·西纳的"必然存在"论证、伊本·鲁世德的"双重真理"说深刻影响了托马斯·阿奎那和欧洲经院哲学，是东西方哲学之间的关键桥梁。',
  },
  {
    name: '阿拉伯哲学',
    color: '#5B8E3A',
    desc: '阿拉伯哲学在阿拔斯王朝的"翻译运动"中将希腊哲学遗产保存并发展。精诚兄弟会的百科全书式哲学、伊本·图斐利的《哈义·本·叶格赞》（独居孤岛的理性觉醒寓言）、伊本·赫勒敦的《历史绪论》（14世纪即创立了历史哲学和社会学方法论），展现了阿拉伯理性主义从形而上学到社会科学的广阔疆域。',
  },
  {
    name: '非洲哲学',
    color: '#C4882E',
    desc: '非洲哲学以"乌班图"（Ubuntu——"我在因为我们在"）为核心，强调共同体、关系和口传智慧。20世纪以降，以桑戈尔为代表的"黑人性"（Négritude）运动、以阿皮亚为代表的"认同哲学"、以维雷杜为代表的概念去殖民化研究，以及约鲁巴、阿肯等传统民族哲学中的"命运"（Ori）、"生命力"等概念，为世界哲学贡献了不同于西方个体主义的共同体本体论。',
  },
  {
    name: '犹太哲学',
    color: '#4A6BBF',
    desc: '犹太哲学以"对话"和"解释"为核心范式。从斐洛以希腊哲学诠释《托拉》开始，经萨阿迪亚·高恩的理性主义神学、迈蒙尼德的《迷途指津》调和亚里士多德与犹太教，到20世纪的布伯（"我与你"）、列维纳斯（"他者的面孔"），犹太哲学始终在"雅典与耶路撒冷"之间追问：启示与理性如何共存？对他者的无限责任如何成为第一哲学？',
  },
  {
    name: '波斯哲学',
    color: '#8B3A5C',
    desc: '波斯哲学在伊斯兰之前以琐罗亚斯德教的善恶二元宇宙论和"自由意志"问题为起点（《阿维斯塔》），在伊斯兰时代贡献了伊本·西纳（阿维森纳）和苏赫拉瓦迪的"光照哲学"（ishraq）。光照哲学以"光"为宇宙的本原，以"在场知识"超越推理知识，将柏拉图理念论与琐罗亚斯德的光明智慧融合为一种独特的"东方智慧"。',
  },
  {
    name: '拉丁美洲哲学',
    color: '#C44A3A',
    desc: '拉丁美洲哲学以"解放"为核心主题。殖民时期以巴托洛梅·德·拉斯·卡萨斯的"印第安人权利"辩护为开端；19世纪以独立和认同为主题；20世纪的"解放哲学"（杜塞尔）和"被压迫者的教育学"（弗莱雷）将哲学从书斋转向穷人、原住民和被殖民者的声音。"我们的美洲"（何塞·马蒂）是对欧洲中心主义的根本挑战。',
  },
  {
    name: '东南亚哲学',
    color: '#3A7B8C',
    desc: '东南亚哲学在印度教、佛教、伊斯兰教和本土万物有灵论的交汇中形成了独特的"和谐"与"包容"智慧。印尼的"潘查希拉"（建国五原则）将多元统一上升为政治哲学；泰国的"适足经济哲学"以中道和知足为核心；越南的儒学与佛教融合；菲律宾的"kapwa"（共享身份）概念展示了不同于西方个体主义的"共同自我"理解。',
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
          除了东西方两大哲学谱系，世界上还有丰富的哲学传统值得探索。以下九大哲学传统覆盖了从南亚到非洲、从中东到拉美的广阔思想版图。
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
              style={{
                background: 'var(--secondary)',
                borderRadius: 12,
                padding: '18px 20px',
                border: '1px solid var(--border)',
                borderLeft: '5px solid ' + phil.color,
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
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
