/**
 * 谱系 —— 垂直时间轴，每行一个大流派卡片
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';

const WESTERN_TIMELINE = [
  { century: '公元前6世纪', schools: ['古希腊哲学'] },
  { century: '公元前3世纪', schools: ['斯多葛学派','怀疑论'] },
  { century: '4世纪', schools: ['教父哲学'] },
  { century: '11世纪', schools: ['经院哲学','唯名论'] },
  { century: '17世纪', schools: ['理性主义', '经验主义'] },
  { century: '18世纪', schools: ['启蒙运动', '实在论', '唯心主义', '自由主义', '浪漫主义'] },
  { century: '19世纪', schools: ['德国古典哲学', '功利主义', '超验主义', '实证主义', '马克思主义', '生命哲学', '社会学'] },
  { century: '20世纪初', schools: ['实用主义', '精神分析学', '现象学', '存在主义', '分析哲学', '过程哲学', '哲学人类学'] },
  { century: '20世纪中', schools: ['西方马克思主义', '法兰克福学派', '批判理论', '科学哲学', '荒诞哲学', '基督教哲学', '结构主义', '政治哲学', '哲学诠释学'] },
  { century: '20世纪末', schools: ['后结构主义', '后现代主义', '伦理学', '宗教哲学', '女性主义', '社群主义'] },
  { century: '21世纪', schools: ['技术哲学'] },
];

const SCHOOL_DESCRIPTIONS = {
  '古希腊哲学':'西方哲学的总源——以理性思辨取代神话解释，首次追问万物的本原、存在的本质与善的生活。',
  '教父哲学':'以希腊理性为基督教信仰奠基——教父们将耶路撒冷的信仰翻译为雅典的语言。',
  '经院哲学':'以亚里士多德的逻辑为基督教构建理性圣殿——信仰寻求理解，恩典成全自然。',
  '理性主义':'以数学公理为范本，以天赋观念为起点，从自明第一原理演绎出全部知识体系。',
  '经验主义':'一切知识起源于感觉经验——心灵如白纸，无经验则无观念。',
  '启蒙运动':'敢于运用你自己的理性——以理性之光驱散迷信与专制，相信进步、自由与人性尊严。',
  '实在论':'存在独立于心灵——无论是柏拉图的理念、亚里士多德的实体还是常识的物质世界。',
  '唯心主义':'实在的本质是精神或观念——存在即被感知，或世界是绝对精神的自我展开。',
  '自由主义':'个人自由是最高政治价值——限制权力、保护权利、宽容多元。',
  '浪漫主义':'以情感和想象反抗启蒙理性的冰冷——自然、天才、个体性与无限渴望。',
  '德国古典哲学':'从康德到黑格尔的哲学革命——以批判、体系和辩证法将理性推到历史的顶点。',
  '功利主义':'最大多数人的最大幸福——道德行为的对错以其产生的快乐或痛苦为唯一判准。',
  '超验主义':'美国的精神独立宣言——人人心中皆有与宇宙直接沟通的神性火花。',
  '实证主义':'以自然科学为一切知识的典范——拒斥形而上学，只问"如何"不问"为何"。',
  '马克思主义':'哲学家们只是解释了世界，问题在于改变世界——历史唯物主义与阶级斗争。',
  '生命哲学':'理性不能穷尽生命——以直觉、绵延与意志理解比理智更深层的生命冲动。',
  '社会学':'以科学方法追问社会何以可能——从分工、失范到官僚制的理性牢笼。',
  '实用主义':'真理即有用，意义在于效果——以行动后果检验观念的真值。',
  '精神分析学':'心灵深处有一个你不知道的你——无意识、欲望与压抑塑造了我们的全部。',
  '现象学':'回到事物本身——悬搁自然态度，描述意识给予经验的结构。',
  '存在主义':'存在先于本质——人被抛入自由之中，必须亲自赋予生命以意义。',
  '分析哲学':'全部哲学就是语言的批判——以逻辑分析澄清概念、消解假问题。',
  '过程哲学':'实在是生成而非存在——宇宙在创造性进展中不断向新质跃迁。',
  '哲学人类学':'人是什么——以哲学整合生物学、心理学与社会学对人的认识。',
  '西方马克思主义':'回到黑格尔的马克思——以文化批判和意识形态理论补充经济分析。',
  '法兰克福学派':'批判理论——工具理性已沦为新的统治形式，启蒙必须反思其自身的辩证法。',
  '批判理论':'传统的理论描述世界，批判的理论旨在解放——揭示权力、知识与意识形态的纠缠。',
  '科学哲学':'科学何以成为科学——从逻辑实证主义到范式革命与方法论的无政府主义。',
  '荒诞哲学':'世界没有意义，但人必须活下去——以反抗、自由与激情回应荒诞。',
  '基督教哲学':'信仰在理性中追问自身——从新托马斯主义到后自由主义神学的哲学反思。',
  '结构主义':'意义不在事物内部而在关系之中——语言、神话与无意识皆由深层结构支配。',
  '政治哲学':'追问正义、权力与自由的根基——从社会契约到分配正义与承认的政治。',
  '哲学诠释学':'理解不是方法而是存在方式——视域融合、效果历史与语言的对话本性。',
  '后结构主义':'解构逻各斯中心主义——差异、延异与权力微观物理学。',
  '后现代主义':'对宏大叙事的怀疑——真理、主体与历史都是语言的建构。',
  '伦理学':'追问人应该如何生活——从德性、义务到效用与关怀。',
  '宗教哲学':'以理性审视信仰——上帝存在的证明、恶的问题与宗教多元论。',
  '女性主义':'个人的即政治的——揭示性别作为权力结构的哲学根基。',
  '社群主义':'自我镶嵌于共同体之中——正义、善与归属不可分离。',
  '技术哲学':'技术不是中立的工具——它重塑了人的存在方式与世界的关系。',
  '斯多葛学派':'控制可控的，接受不可控的——困扰人的不是事物而是人对事物的看法。',
  '怀疑论':'悬搁判断以获得心灵的宁静——对一切教条保持彻底的审慎。',
  '唯名论':'共相只是名称不是实在——只有个别事物真实存在。',
};

const SCHOOL_COLORS = [
  '#C4956A','#C08C5E','#BC8452','#B87C46','#B4743A','#A97040','#9E6C46',
  '#94684C','#8A6452','#806058','#765C5E','#6C5864','#62546A',
  '#585070','#535876','#4E607C','#496882','#447088','#3F788E',
  '#3A8094','#35889A','#3090A0','#2B98A6','#26A0AC','#21A8B2',
  '#1CA8AE','#17A4AA','#12A0A6','#0D9CA2','#08989E','#03949A',
  '#049096','#058C92','#06888E','#07848A','#088086','#097C82',
  '#0A787E','#0B747A','#0C7076',
];

function GenealogyPage() {
  const navigate = useNavigate();
  const [schoolData, setSchoolData] = useState({});

  useEffect(() => {
    fetch(`${getApiBase()}/api/authors`, { signal: AbortSignal.timeout(10000) })
      .then(r => r.json())
      .then(d => {
        const map = {};
        (d.authors || []).forEach(a => {
          const raw = a.school || '';
          if (!raw) return;
          raw.replace('、','/').replace('，','/').replace(',','/').split('/').forEach(s => {
            s = s.trim();
            if (!s || s.length < 2) return;
            // Normalize to big schools
            const normMap = {
              '存在主义先驱':'存在主义','存在哲学':'存在主义','文学哲学':'存在主义',
              '柏拉图主义':'古希腊哲学','逍遥学派':'古希腊哲学','伊壁鸠鲁主义':'古希腊哲学',
              '米利都学派':'古希腊哲学','埃利亚派':'古希腊哲学','前苏格拉底':'古希腊哲学',
              '古代哲学':'古希腊哲学','犬儒学派':'古希腊哲学','自然哲学':'古希腊哲学',
              '新柏拉图主义':'古希腊哲学','折衷主义':'古希腊哲学','元素论':'古希腊哲学',
              '斯多葛派':'斯多葛学派','斯多葛主义':'斯多葛学派','晚期斯多亚':'斯多葛学派',
              '批判哲学':'德国古典哲学','德国唯心论':'德国古典哲学','唯意志论':'德国古典哲学','悲观主义哲学':'德国古典哲学',
              '交往理论':'法兰克福学派','文化批评':'法兰克福学派','法兰克福学派（批判理论）':'法兰克福学派',
              '结构马克思主义':'马克思主义','政治经济学':'政治哲学','宗教社会学':'社会学',
              '现实主义政治哲学':'政治哲学','文艺复兴人文主义':'启蒙运动','逻辑实证主义':'实证主义',
              '启蒙哲学':'启蒙运动','启蒙思想':'启蒙运动','苏格兰启蒙':'启蒙运动','人文主义':'启蒙运动',
              '精神分析':'精神分析学','分析心理学':'精神分析学','心理治疗':'精神分析学',
              '逻辑原子主义':'分析哲学','逻辑实用主义':'分析哲学','逻辑实证':'分析哲学',
              '日常语言':'分析哲学','语言哲学':'分析哲学',
              '形式社会学':'社会学','社会心理学':'社会学','群体心理学':'社会学','社会达尔文':'社会学',
              '激进平等':'政治哲学','责任伦理':'政治哲学','社会契约论':'政治哲学','古典经济学':'政治哲学',
              '德性伦理':'伦理学','批判理性主义':'科学哲学',
              '解释学':'现象学','身体哲学':'现象学','意向性':'现象学',
              '常识实在论':'实在论','人本唯物论':'实在论','机械唯物主义':'实在论',
              '结构语言学':'结构主义','进步教育':'实用主义','新实用主义':'实用主义',
              '荒诞文学':'荒诞哲学','浪漫主义先驱':'浪漫主义',
              '近代哲学之父':'近代哲学','有机体哲学':'过程哲学',
              '后现代哲学':'后现代主义','解构主义':'后现代主义',
              '绝对唯心主义':'唯心主义','历史唯物主义':'马克思主义',
              '文化霸权理论':'西方马克思主义',
            };
            const big = normMap[s] || s;
            if (!map[big]) map[big] = { authors: [], keywords: new Set(), books: [] };
            if (!map[big].authors.includes(a.name)) {
              map[big].authors.push(a.name);
              map[big].books.push(...(a.books || []));
            }
            if (a.era) map[big].keywords.add(a.era.split('-')[0].replace(/[^0-9]/g,'') + '年代');
            if (a.country) map[big].keywords.add(a.country.split('/')[0]);
          });
        });
        setSchoolData(map);
      }).catch(() => {});
  }, []);

  return (
    <div className="page-container" style={{ paddingBottom: 60 }}>
      <h2 className="section-title" style={{ marginBottom: 24, textAlign: 'center' }}>🧬 西方哲学谱系 · 43流派</h2>

      {/* Timeline */}
      <div style={{ maxWidth: 720, margin: '0 auto', position: 'relative', padding: '40px 0' }}>

        {/* Center axis */}
        <div style={{
          position: 'absolute', left: 180, top: 60, bottom: 60, width: 2,
          background: 'var(--border)',
        }} />

        {WESTERN_TIMELINE.map((era, eraIdx) => (
          <div key={eraIdx} style={{ display: 'flex', marginBottom: 48 }}>
            {/* Left: century + 东方 placeholder */}
            <div style={{ width: 160, textAlign: 'right', paddingRight: 24, paddingTop: 4, flexShrink: 0 }}>
              <div style={{
                fontSize: 14, fontWeight: 700, color: 'var(--accent)',
                marginBottom: 6,
              }}>
                {era.century}
              </div>
              <div style={{
                width: 12, height: 12, borderRadius: '50%',
                background: 'var(--accent)', border: '2px solid var(--primary)',
                position: 'absolute', left: 175, marginTop: -10,
              }} />
              {eraIdx === 0 && (
                <div style={{ fontSize: 11, color: 'var(--text-dim)', opacity: 0.3, marginTop: 12 }}>
                  ☯️ 东方
                </div>
              )}
            </div>

            {/* Right: school cards */}
            <div style={{ flex: 1, paddingLeft: 40 }}>
              {era.schools.map((school, si) => {
                const color = SCHOOL_COLORS[(eraIdx * 3 + si) % SCHOOL_COLORS.length];
                return (
                  <div key={school} style={{
                    background: 'var(--secondary)',
                    borderRadius: 12,
                    padding: '16px 22px',
                    marginBottom: 12,
                    border: '1px solid var(--border)',
                    borderLeft: `4px solid ${color}`,
                    cursor: 'pointer',
                  }}
                  onClick={() => navigate(`/school/${encodeURIComponent(school)}`)}
                  >
                    <h3 style={{ fontSize: 17, fontWeight: 700, color: color, margin: '0 0 6px' }}>
                      {school}
                    </h3>
                    {SCHOOL_DESCRIPTIONS[school] && (
                      <p style={{ fontSize: 13, color: 'var(--text-dim)', margin: 0, lineHeight: 1.7 }}>
                        {SCHOOL_DESCRIPTIONS[school]}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GenealogyPage;
