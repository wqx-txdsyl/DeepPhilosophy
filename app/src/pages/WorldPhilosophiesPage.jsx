/**
 * WorldPhilosophiesPage - 世界哲学传统概览
 * 展示印度、日本、伊斯兰、阿拉伯、非洲、犹太、波斯、拉丁美洲、东南亚哲学
 */
import { useNavigate } from 'react-router-dom';

const WORLD_PHILOSOPHIES = [
,
  { name: '古埃及哲学', color: '#C4A03A', desc: '人类最早的智慧传统之一——以玛阿特为核心，追问宇宙秩序、死后存在与王权的神圣基础，对希腊哲学产生深远影响。' },
,
  { name: '古希伯来哲学', color: '#C4A03A', desc: '约伯、传道书与智慧文学——信仰、苦难与神圣正义的追问，希伯来思想对一神教伦理的奠基。' },
,
  { name: '美索不达米亚哲学', color: '#C4A43A', desc: '人类最早的哲学追问。苏美尔智慧文学追问苦难与秩序，《吉尔伽美什》史诗探索死亡与不朽，巴比伦的天文学与占星术将宇宙秩序与人间命运相连。' },
,
  {
    name: '印度哲学',
    color: '#C4743A',
    desc: '以《吠陀》《奥义书》为源头，正统六派（吠檀多、数论、瑜伽、胜论、正理、弥曼差）与非正统的佛教、耆那教、顺世论共同构成了人类对意识、空性和自我最深刻的哲学追问。核心关切是"解脱"——如何从轮回中解放。',
  },
,
  {
    name: '犹太哲学',
    color: '#4A6BBF',
    desc: '以理性与信仰的永恒对话为核心。从斐洛的希腊化诠释到迈蒙尼德调和亚里士多德与犹太教，再到布伯"我与你"、列维纳斯"他者的面孔"，犹太哲学始终在雅典与耶路撒冷之间追问。',
  },
,
  {
    name: '波斯哲学',
    color: '#8B3A5C',
    desc: '超过两千五百年的连续传统。前伊斯兰时期以琐罗亚斯德教善恶二元论和自由意志问题为起点；伊斯兰时期贡献了阿维森纳和苏赫拉瓦迪的光照哲学——以光为宇宙本原，融合柏拉图理念论与琐罗亚斯德光明智慧。',
  },
,
  { name: '凯尔特哲学', color: '#3A8C6B', desc: '德鲁伊传统与凯尔特智慧——自然、灵魂转世与森林中的哲学，欧洲最古老的灵性传统之一。' },
{ name: '古希腊哲学', color: '#C4956A', desc: '西方哲学的总源——以理性思辨取代神话解释，首次追问万物的本原、存在的本质与善的生活。以柏拉图、亚里士多德、前苏格拉底诸学派为代表。' },
,
  { name: '罗马哲学', color: '#8B3A5C', desc: '西塞罗、塞内卡、马可·奥勒留——斯多葛与伊壁鸠鲁在帝国的实践，将哲学融入政治与日常生活。' },
,
  { name: '拜占庭哲学', color: '#6B3FA0', desc: '东罗马帝国的神学哲学传统——伪狄奥尼修斯与拜占庭智慧，融合希腊哲学与基督教神学。' },
,
  {
    name: '伊斯兰哲学',
    color: '#3A8C6B',
    desc: '以理性与启示的对话为核心。凯拉姆以思辨神学捍卫教义；苏非主义以内在修行直观体验神；伊斯兰伦理学和历史哲学从《古兰经》和圣训出发，追问真主、人和世界的关系。',
  },
,
  {
    name: '阿拉伯哲学',
    color: '#5B8E3A',
    desc: '中世纪保存和发展希腊哲学的关键桥梁。法尔萨法（铿迪、法拉比、阿维森纳、阿威罗伊）将亚里士多德与新柏拉图主义融入伊斯兰思想语境，深刻影响了欧洲经院哲学。伊本·赫勒敦创立了历史哲学和社会学方法论。',
  },
,
  { name: '西藏哲学', color: '#9B3A3A', desc: '以藏传佛教中观应成派为核心。宗喀巴的《菩提道次第广论》体系化整合了印度中观与密宗，以"空性"与"缘起"为根本，追问实相与解脱的终极关系。' },
,
  { name: '印加哲学', color: '#8B6E3A', desc: '安第斯文明的哲学结晶——帕查（宇宙时空）与艾尼（互惠平衡）为核心，大地母亲帕查玛玛的生态智慧为当代环境哲学提供古老资源。' },
,
  {
    name: '非洲哲学',
    color: '#C4882E',
    desc: '以口述传统和"乌班图"（我在因我们在）的共同体本体论为核心。政治哲学关注去殖民化和泛非主义；部族哲学从谚语和口传中挖掘智慧；智者哲学关注部落中长者的口述传统。',
  },
,
  {
    name: '拉丁美洲哲学',
    color: '#C44A3A',
    desc: '以解放为核心主题。从殖民时期拉斯·卡萨斯为印第安人权利辩护，到何塞·马蒂"我们的美洲"，再到杜塞尔解放哲学和弗莱雷被压迫者教育学，将哲学从书斋转向穷人和原住民的声音。',
  },
,
  { name: '玛雅哲学', color: '#8C5A3A', desc: '以《波波尔·乌》为圣书，追问时间、创造与人的位置。循环时间观、玉米人神话、二元互补的宇宙结构构成了中美洲最深邃的哲学体系。' },
,
  { name: '阿兹特克哲学', color: '#C44A2E', desc: '以"第五太阳纪"宇宙论为核心。献祭不是杀戮而是对宇宙秩序的维持，花与歌（诗歌）是对短暂生命的哲学回应。追问人在宇宙循环中的责任。' },
,
  {
    name: '东南亚哲学',
    color: '#3A7B8C',
    desc: '在印度教、佛教、伊斯兰教和本土万物有灵论交汇中形成独特的"和谐"智慧。印尼潘查希拉将多元统一上升为政治哲学；泰国适足经济哲学以中道为核心；菲律宾kapwa展示共同体式的自我理解。',
  },
,
  {
    name: '日本哲学',
    color: '#C44A6B',
    desc: '在神道、佛教（禅宗）和儒学的三重影响下形成了独特的"共感"传统。京都学派以西田几多郎"场所的逻辑"和"绝对无"为核心，将禅宗精神与西方哲学创造性融合，为世界哲学做出了原创性贡献。',
  },
,
  { name: '韩国哲学', color: '#6B3FA0', desc: '以性理学和实学为核心。从朝鲜时代的朱子学争辩（四端七情论）到实学的经世致用，再到东学思想与主体思想，韩国哲学在东亚儒学传统中开辟了独特道路。' },
,
  { name: '东欧斯拉夫哲学', color: '#4A6B8C', desc: '以俄罗斯宗教哲学为核心。索洛维约夫的"万物统一"、舍斯托夫的"雅典与耶路撒冷"对立、巴赫金的对话哲学，东欧哲学在东西方之间寻找第三条道路。' },
,
  { name: '北欧哲学', color: '#3A6B8C', desc: '以存在主义先驱克尔凯郭尔为标志。从丹麦的信仰跳跃到挪威的易卜生式个体觉醒，再到瑞典的价值哲学，北欧哲学在冰冷风景中燃烧着对个体生存最炽热的追问。' },
,
  { name: '北美哲学', color: '#3A8B8C', desc: '从殖民清教到实用主义与超验主义。爱默生的"自立"、梭罗的"公民不服从"、皮尔士的"真理即有用"——北美哲学将观念投入实践的熔炉中检验。' },
,
  { name: '黑人哲学', color: '#6B3A5C', desc: '从废奴运动到黑权运动，从杜波依斯双重意识到法农反殖民——全球黑人哲学追问种族、身份与自由的终极意义。' },
,
  { name: '解放哲学', color: '#C44A3A', desc: '从解放神学到巴西解放教育学——哲学为被压迫者发声，法农、弗莱雷、杜塞尔将哲学转向底层。' },
,
  { name: '原住民哲学', color: '#5A8B3A', desc: '全球原住民的生态智慧与土地伦理——从澳大利亚到亚马逊，追问人与自然的共生关系。' },
,
  { name: '后殖民哲学', color: '#8B5A3A', desc: '法农、萨义德、斯皮瓦克——殖民经验的哲学批判与去殖民化思想，揭示权力、知识与身份的关系。' },
,
  { name: '澳洲原住民哲学', color: '#5A7A3A', desc: '以"梦时代"（Dreamtime）为核心。土地不是财产而是祖先的化身，"歌线"穿越大陆将法律、地理、音乐与哲学编织为一体。人类最古老连续文明的生命智慧。' },
,
  { name: '环境哲学', color: '#3A8C6B', desc: '人类与自然的伦理关系——深层生态学、生态女性主义与环境正义，重新定义人与土地的连接。' },
,
  { name: '蒙古中亚哲学', color: '#7A6B3A', desc: '以萨满传统和长生天信仰为根基。游牧智慧追问人与自然的共生关系，口传史诗承载着草原民族的宇宙论与伦理观。' },
];

export default function WorldPhilosophiesPage() {
  const navigate = useNavigate();

  return (
    <div className="page-container" style={{ paddingBottom: 80 }}>

      {/* ══════════ HERO ══════════ */}
      <section style={{ minHeight: '40vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '72px 32px 48px', position: 'relative', overflow: 'hidden', backgroundImage: 'url(/schools/世界哲学传统.jpg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(244,240,235,0.88) 0%, rgba(244,240,235,0.5) 40%, rgba(244,240,235,0.2) 100%)' }} />
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
          position: 'relative', zIndex: 1, fontFamily: 'var(--font-sans)',
          fontSize: 'clamp(1rem, 1.5vw, 1.2rem)', fontWeight: 500,
          color: 'var(--ink)', lineHeight: 1.8, maxWidth: 520, margin: '0 auto',
          textShadow: '0 0 40px rgba(244,240,235,0.8)'
        }}>
          从古希腊到美索不达米亚，从印度到澳洲，<br />三十一大哲学传统覆盖了全球思想版图。
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
