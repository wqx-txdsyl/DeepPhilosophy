/**
 * 谱系 —— 东西方哲学流派时间轴
 */
import { useState } from 'react';

const WESTERN_TIMELINE = [
  { century: '公元前6世纪', schools: ['古希腊哲学'] },
  { century: '公元前4世纪', schools: ['怀疑论'] },
  { century: '公元前3世纪', schools: ['斯多葛学派'] },
  { century: '4世纪', schools: ['教父哲学'] },
  { century: '11世纪', schools: ['经院哲学'] },
  { century: '13世纪', schools: ['托马斯主义'] },
  { century: '14世纪', schools: ['唯名论'] },
  { century: '17世纪', schools: ['近代哲学', '理性主义', '经验主义'] },
  { century: '18世纪', schools: ['启蒙运动', '实在论', '唯心主义', '自由主义', '浪漫主义'] },
  { century: '19世纪', schools: ['德国古典哲学', '功利主义', '超验主义', '实证主义', '马克思主义', '生命哲学', '社会学'] },
  { century: '20世纪初', schools: ['实用主义', '精神分析学', '现象学', '存在主义', '分析哲学', '过程哲学', '哲学人类学'] },
  { century: '20世纪中', schools: ['西方马克思主义', '法兰克福学派', '批判理论', '科学哲学', '荒诞哲学', '基督教哲学', '结构主义', '政治哲学', '哲学诠释学'] },
  { century: '20世纪末', schools: ['后结构主义', '后现代主义', '伦理学', '宗教哲学', '女性主义', '社群主义'] },
  { century: '21世纪', schools: ['技术哲学'] },
];

const SCHOOL_COLORS = {
  '古希腊哲学': '#d4a574', '怀疑论': '#c9a96e', '斯多葛学派': '#bf9e68',
  '教父哲学': '#b89462', '经院哲学': '#b0895c', '托马斯主义': '#a87f56',
  '唯名论': '#a07550', '近代哲学': '#986b4a', '理性主义': '#906144',
  '经验主义': '#88573e', '启蒙运动': '#804d38', '实在论': '#784332',
  '唯心主义': '#70392c', '自由主义': '#682f26', '浪漫主义': '#602520',
  '德国古典哲学': '#581b1a', '功利主义': '#5c2020', '超验主义': '#602626',
  '实证主义': '#642c2c', '马克思主义': '#683232', '生命哲学': '#6c3838',
  '社会学': '#703e3e', '实用主义': '#744444', '精神分析学': '#784a4a',
  '现象学': '#7c5050', '存在主义': '#805656', '分析哲学': '#845c5c',
  '过程哲学': '#886262', '哲学人类学': '#8c6868', '西方马克思主义': '#906e6e',
  '法兰克福学派': '#947474', '批判理论': '#987a7a', '科学哲学': '#9c8080',
  '荒诞哲学': '#a08686', '基督教哲学': '#a48c8c', '结构主义': '#a89292',
  '政治哲学': '#ac9898', '哲学诠释学': '#b09e9e', '后结构主义': '#b4a4a4',
  '后现代主义': '#b8aaaa', '伦理学': '#bcb0b0', '宗教哲学': '#c0b6b6',
  '女性主义': '#c4bcbc', '社群主义': '#c8c2c2', '技术哲学': '#ccc8c8',
};

function GenealogyPage() {
  return (
    <div className="page-container" style={{ paddingBottom: 40 }}>
      <h2 className="section-title" style={{ marginBottom: 20 }}>🧬 哲学谱系</h2>

      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
          西方哲学流派沿时间轴排列 · 点击流派查看详情（即将开放）
        </span>
      </div>

      {/* Timeline */}
      <div style={{ position: 'relative', paddingLeft: 120, paddingRight: 40 }}>
        {/* Center line */}
        <div style={{
          position: 'absolute', left: 60, top: 0, bottom: 0, width: 2,
          background: 'linear-gradient(to bottom, var(--accent), var(--secondary))',
        }} />

        {WESTERN_TIMELINE.map((era, i) => (
          <div key={i} style={{ position: 'relative', marginBottom: 24 }}>
            {/* Century marker */}
            <div style={{
              position: 'absolute', left: -60, top: 8,
              width: 120, textAlign: 'right', paddingRight: 20,
              fontSize: 12, color: 'var(--accent)', fontWeight: 600,
            }}>
              {era.century}
            </div>

            {/* Dot on timeline */}
            <div style={{
              position: 'absolute', left: -68, top: 12,
              width: 10, height: 10, borderRadius: '50%',
              background: 'var(--accent)', border: '2px solid var(--primary)',
              zIndex: 1,
            }} />

            {/* School chips */}
            <div style={{
              display: 'flex', flexWrap: 'wrap', gap: 8,
              paddingLeft: 8,
            }}>
              {era.schools.map(school => (
                <span key={school}
                  style={{
                    display: 'inline-block',
                    padding: '8px 16px',
                    borderRadius: 20,
                    background: SCHOOL_COLORS[school] || 'var(--secondary)',
                    color: '#1a1a1a',
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'transform 0.15s',
                  }}
                  onMouseEnter={e => e.target.style.transform = 'scale(1.05)'}
                  onMouseLeave={e => e.target.style.transform = 'scale(1)'}
                >
                  {school}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GenealogyPage;
