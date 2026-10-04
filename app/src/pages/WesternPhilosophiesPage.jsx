import { useNavigate } from 'react-router-dom';

const SCHOOLS = [
{ name: '教父哲学', color: '#C49A6E', desc: '以希腊理性为基督教信仰奠基——教父们将耶路撒冷的信仰翻译为雅典的语言。' },
  { name: '唯名论', color: '#A08050', desc: '共相只是名称不是实在——只有个别事物真实存在。' },
  { name: '经院哲学', color: '#B89060', desc: '以亚里士多德的逻辑为基督教构建理性圣殿——信仰寻求理解，恩典成全自然。' },
  { name: '托马斯主义', color: '#4A6B8B', desc: '从论战中成形、由通谕复兴的阿奎那解释传统' },
  { name: '理性主义', color: '#6B8FAE', desc: '以数学公理为范本，以天赋观念为起点，从自明第一原理演绎出全部知识体系。' },
  { name: '文艺复兴人文主义', color: '#8B4A5A', desc: '以古典语言、修辞与语文学重整学问与生活的欧洲思想—教育运动（14—16世纪）' },
  { name: '经验主义', color: '#7B9AB0', desc: '一切知识起源于感觉经验——心灵如白纸，无经验则无观念。' },
  { name: '启蒙运动', color: '#C4A060', desc: '敢于运用你自己的理性——以理性之光驱散迷信与专制，相信进步、自由与人性尊严。' },
  { name: '唯心主义', color: '#7B8BA0', desc: '实在的本质是精神或观念——存在即被感知，或世界是绝对精神的自我展开。' },
  { name: '实在论', color: '#8B7B6A', desc: '存在独立于心灵——无论是柏拉图的理念、亚里士多德的实体还是常识的物质世界。' },
  { name: '唯物主义', color: '#8B5A6B', desc: '从’万物皆原子与虚空’到’一切皆物理’：一场关于世界最终本性的持续争论' },
  { name: '浪漫主义', color: '#C48B8B', desc: '以情感和想象反抗启蒙理性的冰冷——自然、天才、个体性与无限渴望。' },
  { name: '自然主义', color: '#6B5A8B', desc: '从’无超自然’的否定式纲领到’哲学与科学连续’的方法论承诺' },
  { name: '自由主义', color: '#8B9EA0', desc: '个人自由是最高政治价值——限制权力、保护权利、宽容多元。' },
  { name: '一元论', color: '#7B8B5A', desc: '实体、性质与存在计数：“一”的三层立场' },
  { name: '贝叶斯主义', color: '#8B9BA5', desc: '以概率论为核心，将信念与决策纳入数学框架——从贝叶斯定理到主观概率与因果推理。' },
  { name: '数学哲学', color: '#6B7B8B', desc: '数学对象是否存在、数学知识何以确定、证明的界限何在' },
  { name: '二元论', color: '#8B7B4A', desc: '从笛卡尔式心身之别到当代属性二元论' },
  { name: '功利主义', color: '#9B8B5A', desc: '最大多数人的最大幸福——道德行为的对错以其产生的快乐或痛苦为唯一判准。' },
  { name: '自然哲学', color: '#6B7B8B', desc: '从米利都的本原到数学化的自然' },
  { name: '实证主义', color: '#6B8B7B', desc: '以自然科学为一切知识的典范——拒斥形而上学，只问如何不问为何。' },
  { name: '德国古典哲学', color: '#5A7A9B', desc: '从康德到黑格尔的哲学革命——以批判、体系和辩证法将理性推到历史的顶点。' },
  { name: '新康德主义', color: '#5A8B7B', desc: '「回到康德」口号下的马堡与西南两派' },
  { name: '生命哲学', color: '#8B9B6B', desc: '理性不能穷尽生命——以直觉、绵延与意志理解比理智更深层的生命冲动。' },
  { name: '社会学', color: '#7B8B6B', desc: '以科学方法追问社会何以可能——从分工、失范到官僚制的理性牢笼。' },
  { name: '历史哲学', color: '#8B4A5A', desc: '思辨的历史哲学与批判的历史哲学' },
  { name: '超验主义', color: '#7B9B8B', desc: '美国的精神独立宣言——人人心中皆有与宇宙直接沟通的神性火花。' },
  { name: '马克思主义', color: '#A05050', desc: '哲学家们只是解释了世界，问题在于改变世界——历史唯物主义与阶级斗争。' },
  { name: '分析哲学', color: '#5A7B8B', desc: '全部哲学就是语言的批判——以逻辑分析澄清概念、消解假问题。' },
  { name: '认识论', color: '#6B7B8B', desc: '关于知识与辩护的追问之学：从定义、怀疑到自然化与社会转向' },
  { name: '哲学人类学', color: '#8B7B7B', desc: '人是什么——以哲学整合生物学、心理学与社会学对人的认识。' },
  { name: '形而上学', color: '#8B6B5A', desc: '追问存在、实体、因果、模态与时空的第一哲学领域' },
  { name: '存在主义', color: '#8B6B6B', desc: '存在先于本质——人被抛入自由之中，必须亲自赋予生命以意义。' },
  { name: '逻辑与逻辑哲学', color: '#5A8B6B', desc: '从『必然得出』到模型、证明与多元之争' },
  { name: '实用主义', color: '#8B9B6B', desc: '真理即有用，意义在于效果——以行动后果检验观念的真值。' },
  { name: '教育哲学', color: '#5A8B7B', desc: '对教育的本质、目的与问题的哲学反思' },
  { name: '心灵哲学', color: '#8B5A6B', desc: '从身心问题到意识难问题：心智如何安放于自然世界' },
  { name: '现象学', color: '#7B8B8B', desc: '回到事物本身——悬搁自然态度，描述意识给予经验的结构。' },
  { name: '行动哲学', color: '#8B6B5A', desc: '什么使一个身体动作成为行动：意图、理由与因果之争' },
  { name: '语言哲学', color: '#6B5A8B', desc: '意义、指称与言语行为的问题域' },
  { name: '精神分析学', color: '#7B6B8B', desc: '心灵深处有一个你不知道的你——无意识、欲望与压抑塑造了我们的全部。' },
  { name: '逻辑经验主义', color: '#8B4A5A', desc: '维也纳学圈、柏林学派与可证实性纲领的兴衰' },
  { name: '过程哲学', color: '#7B9B9B', desc: '实在是生成而非存在——宇宙在创造性进展中不断向新质跃迁。' },
  { name: '日常语言哲学', color: '#5A8B7B', desc: '从语言游戏到言语行为：后期维特根斯坦、牛津学派与系统化转向' },
  { name: '伦理学', color: '#8B7B5A', desc: '追问人应该如何生活——从德性、义务到效用与关怀。' },
  { name: '美学', color: '#7B8B5A', desc: '关于美、艺术与审美经验之追问的学科及其跨传统前史' },
  { name: '哲学诠释学', color: '#6B8B9B', desc: '理解不是方法而是存在方式——视域融合、效果历史与语言的对话本性。' },
  { name: '德性伦理学', color: '#6B7B8B', desc: '以品格与德性为根基的规范伦理学立场' },
  { name: '基督教哲学', color: '#9B8B6E', desc: '信仰在理性中追问自身——从新托马斯主义到后自由主义神学的哲学反思。' },
  { name: '义务论伦理学', color: '#8B6B5A', desc: '正当优先于善：从康德定言令式到显见义务与权利约束' },
  { name: '批判理论', color: '#8B5A6B', desc: '传统的理论描述世界，批判的理论旨在解放——揭示权力、知识与意识形态的纠缠。' },
  { name: '关怀伦理学', color: '#5A8B6B', desc: '从『不同的声音』到关怀的政治：以关系与依赖为中心的道德立场' },
  { name: '政治哲学', color: '#7B6B5A', desc: '追问正义、权力与自由的根基——从社会契约到分配正义与承认的政治。' },
  { name: '法哲学', color: '#4A6B8B', desc: '法律的本性、效力与解释：自然法、法律实证主义与解释理论之争' },
  { name: '元伦理学', color: '#5A8B6B', desc: '道德语言、道德事实与道德动机的二阶追问：从开放问题论证到准实在论' },
  { name: '法兰克福学派', color: '#8B5A5A', desc: '批判理论——工具理性已沦为新的统治形式，启蒙必须反思其自身的辩证法。' },
  { name: '共和主义', color: '#8B5A6B', desc: '把政治自由理解为无支配的古今传统' },
  { name: '道德实在论', color: '#8B7B4A', desc: '道德判断有真值：从康奈尔实在论到非自然主义的本体之争' },
  { name: '社群主义', color: '#6B8B5A', desc: '自我镶嵌于共同体之中——正义、善与归属不可分离。' },
  { name: '保守主义', color: '#6B5A8B', desc: '对政治中抽象理性主义的哲学怀疑——从伯克的代际合伙到奥克肖特的反理性主义' },
  { name: '科学哲学', color: '#5A8B7B', desc: '科学何以成为科学——从逻辑实证主义到范式革命与方法论的无政府主义。' },
  { name: '无政府主义', color: '#7B8B5A', desc: '怀疑国家正当性、以自由联合取代统治的理论与社会运动' },
  { name: '结构主义', color: '#6B7B9B', desc: '意义不在事物内部而在关系之中——语言、神话与无意识皆由深层结构支配。' },
  { name: '荒诞哲学', color: '#9B7B6B', desc: '世界没有意义，但人必须活下去——以反抗、自由与激情回应荒诞。' },
  { name: '西方马克思主义', color: '#9B5A5A', desc: '回到黑格尔的马克思——以文化批判和意识形态理论补充经济分析。' },
  { name: '后现代主义', color: '#7B6B9B', desc: '对宏大叙事的怀疑——真理、主体与历史都是语言的建构。' },
  { name: '后结构主义', color: '#6B6B8B', desc: '解构逻各斯中心主义——差异、延异与权力微观物理学。' },
  { name: '女性主义', color: '#B87080', desc: '个人的即政治的——揭示性别作为权力结构的哲学根基。' },
  { name: '宗教哲学', color: '#8B7B6E', desc: '以理性审视信仰——上帝存在的证明、恶的问题与宗教多元论。' },
  { name: '解构主义', color: '#7B6B9B', desc: '德里达的解构——文字、意义与权力的边缘。' },
  { name: '技术哲学', color: '#5A7B9B', desc: '技术不是中立的工具——它重塑了人的存在方式与世界的关系。' },
  { name: '柏拉图主义', color: '#5A8B7B', desc: '型相论与它的学园谱系：从老学园、学园怀疑论到中期柏拉图主义' },
  { name: '亚里士多德学派（逍遥学派）', color: '#5A8B7B', desc: '从雅典吕克昂的步道讲学，到横跨希腊语、阿拉伯语与拉丁语的求知传统' },
];

export default function WesternPhilosophiesPage() {
  const navigate = useNavigate();
  return (
    <div className="page-container" style={{ paddingBottom: 80 }}>
      <section style={{ minHeight: '40vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '72px 32px 48px', position: 'relative', overflow: 'hidden', backgroundImage: 'url(https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/schools/西方哲学.webp?x-oss-process=image/resize,w_1280)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(244,240,235,0.88) 0%, rgba(244,240,235,0.5) 40%, rgba(244,240,235,0.2) 100%)' }} />
        <button onClick={() => navigate(-1)} style={{ position: 'relative', zIndex: 1, background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.04em', marginBottom: 32, padding: 0 }}>← 返回</button>
        <p style={{ position: 'relative', zIndex: 1, fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 500, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--ochre)', margin: '0 0 16px' }}>Western Philosophy</p>
        <h1 style={{ position: 'relative', zIndex: 1, fontFamily: '"Playfair Display","PingFang SC",serif', fontSize: 'clamp(2rem,5vw,3rem)', fontWeight: 400, color: 'var(--ink)', letterSpacing: '0.04em', lineHeight: 1.2, margin: '0 0 20px' }}>西方哲学</h1>
        <p style={{ position: 'relative', zIndex: 1, fontFamily: 'var(--font-sans)', fontSize: 'clamp(1rem, 1.5vw, 1.2rem)', fontWeight: 500, color: 'var(--ink)', lineHeight: 1.8, maxWidth: 520, margin: '0 auto', textShadow: '0 0 40px rgba(244,240,235,0.8)' }}>从古希腊到后现代，四十二个流派，<br />理性、存在与语言的跨越两千年的探索。</p>
        <div style={{ width: 40, height: 1, background: 'var(--ochre)', margin: '28px auto 0', opacity: 0.4 }} />
      </section>
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 32px 64px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24 }}>
          {SCHOOLS.map(s => (
            <div key={s.name} onClick={() => navigate('/school/' + encodeURIComponent(s.name))}
              style={{ padding: '24px 0', cursor: 'pointer', borderBottom: '1px solid var(--border)', transition: 'all 0.25s', background: 'transparent' }}
              onMouseEnter={e => { e.currentTarget.style.borderBottomColor = s.color; }}
              onMouseLeave={e => { e.currentTarget.style.borderBottomColor = 'var(--border)'; }}>
              <h3 style={{ fontFamily: '"Playfair Display","PingFang SC",serif', fontSize: 22, fontWeight: 400, color: 'var(--ink)', letterSpacing: '0.03em', margin: '0 0 8px' }}>{s.name}</h3>
              <p style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 300, color: 'var(--text-dim)', lineHeight: 1.8, margin: 0 }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
