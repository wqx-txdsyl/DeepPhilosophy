/**
 * 世界哲学地图 —— 悬停显示简介卡片，点击跳转
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const REGIONS = [
  { id: 'china', name: '中国', sub: '东方哲学', desc: '儒道墨法至当代，两千五百年不断的思想脉络。', x: 79, y: 28, r: 45, path: '/eastern-philosophies' },
  { id: 'japan', name: '日本', sub: '日本哲学', desc: '禅宗、京都学派、西田几多郎的无的哲学。', x: 91, y: 22, r: 25, path: '/school/日本哲学' },
  { id: 'india', name: '印度', sub: '印度哲学', desc: '吠陀、奥义书、佛教起源、六派哲学。', x: 65, y: 47, r: 35, path: '/school/印度哲学' },
  { id: 'europe', name: '欧洲', sub: '西方哲学', desc: '从古希腊到后现代，43流派的宏伟思想史。', x: 42, y: 23, r: 55, path: '/western-philosophies' },
  { id: 'islam', name: '中东', sub: '伊斯兰哲学', desc: '百年翻译运动、阿维森纳、苏菲神秘主义。', x: 55, y: 38, r: 30, path: '/school/伊斯兰哲学' },
  { id: 'africa', name: '非洲', sub: '非洲哲学', desc: '口头传统、社群伦理、后殖民批判思想。', x: 46, y: 59, r: 50, path: '/school/非洲哲学' },
  { id: 'latin', name: '拉丁美洲', sub: '拉丁美洲哲学', desc: '解放神学、混血意识、魔幻现实主义。', x: 17, y: 59, r: 40, path: '/school/拉丁美洲哲学' },
  { id: 'seasia', name: '东南亚', sub: '东南亚哲学', desc: '上座部佛教与本土智慧的交融。', x: 77, y: 53, r: 28, path: '/school/东南亚哲学' },
  { id: 'na', name: '北美', sub: '实用主义', desc: '皮尔士、詹姆斯、杜威——真理即有用。', x: 12, y: 27, r: 30, path: '/school/实用主义' },
  { id: 'jewish', name: '犹太', sub: '犹太哲学', desc: '塔木德传统、迈蒙尼德、列维纳斯。', x: 52, y: 31, r: 22, path: '/school/犹太哲学' },
  { id: 'persia', name: '波斯', sub: '波斯哲学', desc: '琐罗亚斯德、苏菲诗歌、光明与黑暗。', x: 58, y: 33, r: 25, path: '/school/波斯哲学' },
  { id: 'arab', name: '阿拉伯', sub: '阿拉伯哲学', desc: '理性与信仰的调和，百年翻译运动。', x: 50, y: 35, r: 22, path: '/school/阿拉伯哲学' },
];

function WorldMap() {
  const navigate = useNavigate();
  const [hover, setHover] = useState(null);

  return (
    <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%' }}>
      <img src="/schools/世界地图.png" alt="世界哲学地图"
        style={{ width: '100%', maxWidth: 1200, height: 'auto', borderRadius: 8, display: 'block' }} />

      {REGIONS.map(r => (
        <div key={r.id}
          onMouseEnter={() => setHover(r)}
          onMouseLeave={() => setHover(null)}
          onClick={() => navigate(r.path)}
          title=""
          style={{
            position: 'absolute',
            left: `${r.x}%`, top: `${r.y}%`,
            width: `${Math.max(r.r * 0.35, 8)}%`,
            height: `${Math.max(r.r * 0.5, 10)}%`,
            transform: 'translate(-50%, -50%)',
            cursor: 'pointer',
            borderRadius: '50%',
            zIndex: 1,
          }}
        />
      ))}

      {/* 悬浮卡片 — 磨砂玻璃 */}
      {hover && (
        <div style={{
          position: 'absolute',
          left: `${hover.x}%`, top: `${hover.y - hover.r * 0.06}%`,
          transform: 'translate(-50%, -100%)',
          background: 'rgba(244,240,235,0.75)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid rgba(196,149,106,0.3)',
          borderRadius: 8,
          padding: '12px 16px',
          minWidth: 160,
          maxWidth: 260,
          boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          zIndex: 10,
          pointerEvents: 'none',
        }}>
          <div style={{ fontSize: 11, color: 'var(--ochre)', fontWeight: 600, letterSpacing: '0.05em', marginBottom: 2 }}>
            {hover.sub}
          </div>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
            {hover.name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)', lineHeight: 1.5 }}>
            {hover.desc}
          </div>
        </div>
      )}
    </div>
  );
}

export default WorldMap;
