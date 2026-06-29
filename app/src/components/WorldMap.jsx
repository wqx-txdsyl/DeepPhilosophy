/**
 * 世界哲学地图 —— 悬停显示简介卡片，点击跳转
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const REGIONS = [
  // 东亚
  { id: 'china', name: '中国', sub: '东方哲学', desc: '儒道墨法至当代，24流派。', x: 79, y: 24, r: 45, path: '/eastern-philosophies' },
  { id: 'japan', name: '日本', sub: '日本哲学', desc: '禅宗、京都学派、西田几多郎的无的哲学。', x: 92, y: 20, r: 22, path: '/school/日本哲学' },
  { id: 'korea', name: '韩国', sub: '韩国哲学', desc: '性理学、实学、东学、主体思想。', x: 87, y: 22, r: 18, path: '/school/韩国哲学' },
  // 南亚
  { id: 'india', name: '印度', sub: '印度哲学', desc: '吠陀、奥义书、佛教起源、六派哲学。', x: 65, y: 44, r: 32, path: '/school/印度哲学' },
  { id: 'tibet', name: '西藏', sub: '西藏哲学', desc: '藏传佛教中观应成派、宗喀巴、密宗。', x: 72, y: 35, r: 18, path: '/school/西藏哲学' },
  { id: 'seasia', name: '东南亚', sub: '东南亚哲学', desc: '上座部佛教与本土智慧的交融。', x: 80, y: 50, r: 24, path: '/school/东南亚哲学' },
  // 中亚/蒙古
  { id: 'mongol', name: '蒙古/中亚', sub: '蒙古中亚哲学', desc: '萨满传统、长生天、游牧智慧。', x: 70, y: 30, r: 24, path: '/school/蒙古中亚哲学' },
  // 欧洲
  { id: 'europe', name: '欧洲', sub: '西方哲学', desc: '从古希腊到后现代，43流派。', x: 40, y: 20, r: 50, path: '/western-philosophies' },
  { id: 'greece', name: '希腊', sub: '古希腊哲学', desc: '西方哲学总源——泰勒斯、柏拉图、亚里士多德。', x: 48, y: 26, r: 16, path: '/school/古希腊哲学' },
  { id: 'nordic', name: '北欧', sub: '北欧哲学', desc: '克尔凯郭尔的存在主义源头、易卜生。', x: 45, y: 10, r: 18, path: '/school/北欧哲学' },
  { id: 'slavic', name: '东欧', sub: '东欧斯拉夫哲学', desc: '舍斯托夫、索洛维约夫、俄罗斯宗教哲学。', x: 52, y: 15, r: 22, path: '/school/东欧斯拉夫哲学' },
  // 中东集群(精细化间距)
  { id: 'islam', name: '伊斯兰', sub: '伊斯兰哲学', desc: '百年翻译运动、阿维森纳、苏菲神秘主义。', x: 54, y: 38, r: 26, path: '/school/伊斯兰哲学' },
  { id: 'mesopotamia', name: '美索不达米亚', sub: '美索不达米亚哲学', desc: '人类最早的哲学追问——吉尔伽美什与智慧文学。', x: 52, y: 36, r: 14, path: '/school/美索不达米亚哲学' },
  { id: 'persia', name: '波斯', sub: '波斯哲学', desc: '琐罗亚斯德、苏菲诗歌、光明与黑暗。', x: 60, y: 34, r: 20, path: '/school/波斯哲学' },
  { id: 'arab', name: '阿拉伯', sub: '阿拉伯哲学', desc: '理性与信仰的调和。', x: 49, y: 40, r: 18, path: '/school/阿拉伯哲学' },
  { id: 'jewish', name: '犹太', sub: '犹太哲学', desc: '塔木德传统、迈蒙尼德、列维纳斯。', x: 48, y: 33, r: 16, path: '/school/犹太哲学' },
  // 非洲
  { id: 'africa', name: '非洲', sub: '非洲哲学', desc: '口头传统、社群伦理、后殖民批判。', x: 44, y: 55, r: 45, path: '/school/非洲哲学' },
  // 美洲
  { id: 'na', name: '北美', sub: '北美哲学', desc: '实用主义、超验主义、过程哲学。', x: 12, y: 24, r: 28, path: '/school/北美哲学' },
  { id: 'pragmatism', name: '美东', sub: '实用主义', desc: '皮尔士、詹姆斯、杜威——真理即有用。', x: 18, y: 28, r: 14, path: '/school/实用主义' },
  { id: 'latin', name: '拉丁美洲', sub: '拉丁美洲哲学', desc: '解放神学、混血意识、魔幻现实主义。', x: 17, y: 55, r: 36, path: '/school/拉丁美洲哲学' },
  { id: 'maya', name: '玛雅', sub: '玛雅哲学', desc: '波波尔·乌、时间循环、玉米人。', x: 15, y: 48, r: 16, path: '/school/玛雅哲学' },
  { id: 'aztec', name: '阿兹特克', sub: '阿兹特克哲学', desc: '宇宙论、献祭辩证法、第五太阳纪。', x: 14, y: 44, r: 16, path: '/school/阿兹特克哲学' },
  // 大洋洲
  { id: 'australia', name: '澳洲', sub: '澳洲原住民哲学', desc: 'Dreamtime、歌线、土地伦理。', x: 82, y: 62, r: 22, path: '/school/澳洲原住民哲学' },
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
