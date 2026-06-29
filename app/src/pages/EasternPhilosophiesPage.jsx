import { useNavigate } from 'react-router-dom';

const SCHOOLS = [
  { name: '儒家', color: '#C46A6A', desc: '以仁为核心，以礼为规范——修身齐家治国平天下，两千年来塑造了东亚文明的精神底色。' },
  { name: '道家', color: '#6A8B6A', desc: '道法自然，无为而治——以柔克刚的智慧，在文明的对立面为心灵保留一片返璞归真的天地。' },
  { name: '墨家', color: '#6A6A8B', desc: '兼爱非攻，尚贤节用——以普遍之爱与逻辑理性，发出先秦最激进的平等主义呼声。' },
  { name: '法家', color: '#8B6A6A', desc: '以法治国，不别亲疏——制度先于道德，法律面前人人平等，为大一统帝国奠定制度哲学。' },
  { name: '名家', color: '#7B6A8B', desc: '白马非马，离坚白——中国最早的逻辑学与语言哲学，以概念辨析与悖论追问名与实的边界。' },
  { name: '阴阳家', color: '#6A7B8B', desc: '阴阳消长，五德终始——以宇宙论框架将自然、历史与政治纳入统一的运转法则。' },
  { name: '兵家', color: '#8B7B6A', desc: '知己知彼，不战屈人——将冲突升华为博弈的艺术，以最小代价达成最大目标的智慧。' },
  { name: '两汉经学', color: '#9B8B6A', desc: '通经致用，以经为法——今文以微言大义构建天人感应的政治神学，古文以训诂考据守护经典本义。' },
  { name: '魏晋玄学', color: '#6A8B7B', desc: '越名教而任自然——以老庄注解为表，以人格解放为里，在乱世中为个体心灵开辟自由的精神空间。' },
  { name: '隋唐佛学', color: '#8B6A7B', desc: '八宗竞秀，会通中印——天台之圆融、唯识之精密、华严之无尽、禅宗之顿悟，佛教在中国完成最深刻的本土化创造。' },
  { name: '宋明理学', color: '#6A6A9B', desc: '为天地立心，为生民立命——以天理为宇宙与道德的共同根基，在佛道冲击后重建儒家的形而上学体系。' },
  { name: '明清实学', color: '#7B6A6A', desc: '经世致用，实事求是——以批判空疏理学为旗帜，将学术重心从心性玄谈转向国计民生与实测之学。' },
  { name: '乾嘉朴学', color: '#6A7B6A', desc: '无征不信，孤证不立——以训诂考据校勘为方法，将语言学与历史学提升为严谨的实证科学。' },
  { name: '天演论', color: '#5A7B8B', desc: '物竞天择，适者生存——严复以《天演论》震醒甲午之后整整一代知识分子：不变则亡。' },
  { name: '维新派', color: '#8B6A5A', desc: '变则通，通则久——康梁借今文经改制传统为政治变革提供哲学合法性，探索中国政治转型的第一条道路。' },
  { name: '三民主义', color: '#5A6A8B', desc: '民族、民权、民生——孙中山以兼容中西的理论框架为现代中国提供第一个系统化的建国哲学方案。' },
  { name: '旧民主主义', color: '#7B6A8B', desc: '旧民主主义革命时期的政治哲学——以三民主义为核心，从兴中会到同盟会再到辛亥革命的理论演进。' },
  { name: '毛泽东思想', color: '#8B5A5A', desc: '实事求是，群众路线——从《实践论》《矛盾论》到农村包围城市，奠定了马克思主义中国化的理论基石。' },
  { name: '中国马克思主义哲学', color: '#9B6A5A', desc: '辩证唯物主义与历史唯物主义在中国的传播、研究与体系化——从革命指南发展为学科体系和教科书体系。' },
  { name: '新民主主义', color: '#8B5A6A', desc: '新民主主义革命理论——毛泽东系统阐述中国革命分两步走，各革命阶级联合专政，建设民族的科学的大众的新文化。' },
  { name: '现代新儒家', color: '#6A6A8B', desc: '返本开新，内圣外王——熊十力、牟宗三、唐君毅等以儒家心性之学为根基，与康德、黑格尔展开深度对话。' },
  { name: '中国实证哲学', color: '#5A6A7B', desc: '大胆假设，小心求证——胡适将杜威实验主义引入中国，以科学方法整理国故，开辟中国现代学术的新范式。' },
  { name: '马克思主义哲学的中国化与体系化', color: '#8B5A5A', desc: '从实践标准到特色社会主义理论体系的哲学基础——马克思主义哲学在中国制度实践与理论创新的双轮驱动下不断生成新的理论形态。' },
  { name: '习近平新时代中国特色社会主义思想', color: '#8B4A4A', desc: '以人民为中心的发展思想——将马克思主义基本原理与新时代中国具体实际相结合，系统回应重大时代课题。' },
];

export default function EasternPhilosophiesPage() {
  const navigate = useNavigate();
  return (
    <div className="page-container" style={{ paddingBottom: 80 }}>
      <section style={{ minHeight: '40vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '72px 32px 48px', position: 'relative', overflow: 'hidden', backgroundImage: 'url(/schools/东方哲学.png)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(244,240,235,0.88) 0%, rgba(244,240,235,0.5) 40%, rgba(244,240,235,0.2) 100%)' }} />
        <button onClick={() => navigate(-1)} style={{ position: 'relative', zIndex: 1, background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.04em', marginBottom: 32, padding: 0 }}>← 返回</button>
        <p style={{ position: 'relative', zIndex: 1, fontFamily: 'var(--font-sans)', fontSize: 11, fontWeight: 500, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--ochre)', margin: '0 0 16px' }}>Eastern Philosophy</p>
        <h1 style={{ position: 'relative', zIndex: 1, fontFamily: '"Playfair Display","PingFang SC",serif', fontSize: 'clamp(2rem,5vw,3rem)', fontWeight: 400, color: 'var(--ink)', letterSpacing: '0.04em', lineHeight: 1.2, margin: '0 0 20px' }}>东方哲学</h1>
        <p style={{ position: 'relative', zIndex: 1, fontFamily: 'var(--font-sans)', fontSize: 'clamp(1rem, 1.5vw, 1.2rem)', fontWeight: 500, color: 'var(--ink)', lineHeight: 1.8, maxWidth: 520, margin: '0 auto', textShadow: '0 0 40px rgba(244,240,235,0.8)' }}>从先秦诸子到当代，二十四个流派，<br />两千五百年不断的思想脉络。</p>
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
