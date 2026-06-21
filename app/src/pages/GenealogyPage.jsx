/**
 * 谱系 —— 垂直时间轴，每行一个大流派卡片
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';

const WESTERN_TIMELINE = [
  { century: '公元前6世纪', schools: ['古希腊哲学'] },


  { century: '4世纪', schools: ['教父哲学'] },
  { century: '11世纪', schools: ['经院哲学'] },
  { century: '14世纪', schools: ['唯名论'] },
  { century: '17世纪', schools: ['近代哲学', '理性主义', '经验主义'] },
  { century: '18世纪', schools: ['启蒙运动', '实在论', '唯心主义', '自由主义', '浪漫主义'] },
  { century: '19世纪', schools: ['德国古典哲学', '功利主义', '超验主义', '实证主义', '马克思主义', '生命哲学', '社会学'] },
  { century: '20世纪初', schools: ['实用主义', '精神分析学', '现象学', '存在主义', '分析哲学', '过程哲学', '哲学人类学'] },
  { century: '20世纪中', schools: ['西方马克思主义', '法兰克福学派', '批判理论', '科学哲学', '荒诞哲学', '基督教哲学', '结构主义', '政治哲学', '哲学诠释学'] },
  { century: '20世纪末', schools: ['后结构主义', '后现代主义', '伦理学', '宗教哲学', '女性主义', '社群主义'] },
  { century: '21世纪', schools: ['技术哲学'] },
];

const SCHOOL_COLORS = [
  '#d4a574','#c49a68','#b4905c','#a48650','#947c44','#847238','#74682c','#645e20',
  '#5c5820','#585c26','#54602c','#506432','#4c6838','#486c3e','#447044','#40744a',
  '#3c7850','#387c56','#34805c','#308462','#2c8868','#288c6e','#248074','#20847a',
  '#1c8880','#188c86','#14908c','#109492','#0c9898','#089c9e','#04a0a4','#00a4aa',
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
      <h2 className="section-title" style={{ marginBottom: 24, textAlign: 'center' }}>🧬 西方哲学谱系</h2>

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
                const data = schoolData[school] || {};
                const color = SCHOOL_COLORS[(eraIdx * 3 + si) % SCHOOL_COLORS.length];
                return (
                  <div key={school} style={{
                    background: 'var(--secondary)',
                    borderRadius: 12,
                    padding: '16px 22px',
                    marginBottom: 12,
                    borderLeft: `4px solid ${color}`,
                    cursor: 'pointer',
                  }}
                  onClick={() => navigate(`/school/${encodeURIComponent(school)}`)}
                  >
                    <h3 style={{ fontSize: 17, fontWeight: 700, color: color, margin: '0 0 6px' }}>
                      {school}
                    </h3>
                    {data.authors?.length > 0 && (
                      <p style={{ fontSize: 13, color: 'var(--text)', margin: '0 0 4px', lineHeight: 1.6 }}>
                        {data.authors.slice(0, 8).join('、')}
                        {data.authors.length > 8 && ` 等`}
                      </p>
                    )}
                    {data.books?.length > 0 && (
                      <p style={{ fontSize: 12, color: 'var(--text-dim)', margin: 0, lineHeight: 1.6 }}>
                        {[...new Set(data.books)].slice(0, 5).map((t, i) => (
                          <span key={i}>《{t}》 </span>
                        ))}
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
