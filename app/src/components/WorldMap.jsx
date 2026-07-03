/**
 * 世界哲学地图 —— 悬停显示简介卡片，点击跳转
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const REGIONS = [
  // 东亚
  { id: 'china', name: '中国', sub: '东方哲学', desc: '儒道墨法至当代，24流派。', x: 78, y: 28, r: 42, path: '/eastern-philosophies' },
  { id: 'japan', name: '日本', sub: '日本哲学', desc: '禅宗、京都学派、西田几多郎的无的哲学。', x: 88, y: 26, r: 18, path: '/school/日本哲学' },
  { id: 'korea', name: '韩国', sub: '韩国哲学', desc: '性理学、实学、东学、主体思想。', x: 82, y: 30, r: 14, path: '/school/韩国哲学' },
  // 南亚
  { id: 'india', name: '印度', sub: '印度哲学', desc: '吠陀、奥义书、佛教起源、六派哲学。', x: 72, y: 45, r: 28, path: '/school/印度哲学' },
  { id: 'tibet', name: '西藏', sub: '西藏哲学', desc: '藏传佛教中观应成派、宗喀巴、密宗。', x: 68, y: 35, r: 14, path: '/school/西藏哲学' },
  { id: 'seasia', name: '东南亚', sub: '东南亚哲学', desc: '上座部佛教与本土智慧的交融。', x: 76, y: 55, r: 20, path: '/school/东南亚哲学' },
  // 中亚/蒙古
  { id: 'mongol', name: '蒙古/中亚', sub: '蒙古中亚哲学', desc: '萨满传统、长生天、游牧智慧。', x: 65, y: 25, r: 22, path: '/school/蒙古中亚哲学' },
  { id: 'shaman', name: '萨满', sub: '萨满哲学', desc: '万物有灵·三层宇宙·灵魂旅程。', x: 62, y: 10, r: 24, path: '/school/萨满哲学' },
  { id: 'caucasus-steppe', name: '高加索-草原', sub: '高加索-草原哲学', desc: '游牧伦理·马文化·口头史诗。', x: 54, y: 22, r: 18, path: '/school/高加索-草原哲学' },
  { id: 'caucasus', name: '高加索', sub: '高加索哲学', desc: '纳尔特史诗·山地文明·欧亚交汇。', x: 56, y: 32, r: 16, path: '/school/高加索哲学' },
  // 欧洲
  { id: 'europe', name: '欧洲', sub: '西方哲学', desc: '从古希腊到后现代，41流派。', x: 45, y: 25, r: 46, path: '/western-philosophies' },
  { id: 'world', name: '世界传统', sub: '世界哲学', desc: '37大世界哲学传统。', x: 36, y: 55, r: 36, path: '/world-philosophies' },
  { id: 'greece', name: '希腊', sub: '古希腊哲学', desc: '西方哲学总源——泰勒斯、柏拉图、亚里士多德。', x: 52, y: 32, r: 14, path: '/school/古希腊哲学' },
  { id: 'nordic', name: '北欧', sub: '北欧哲学', desc: '克尔凯郭尔的存在主义源头、易卜生。', x: 48, y: 12, r: 16, path: '/school/北欧哲学' },
  { id: 'celtic', name: '凯尔特', sub: '凯尔特哲学', desc: '德鲁伊传统、自然崇拜——森林中的哲学。', x: 38, y: 22, r: 14, path: '/school/凯尔特哲学' },
  { id: 'rome', name: '罗马', sub: '罗马哲学', desc: '西塞罗、塞内卡、奥勒留——斯多葛的帝国实践。', x: 48, y: 30, r: 14, path: '/school/罗马哲学' },
  { id: 'byzantine', name: '拜占庭', sub: '拜占庭哲学', desc: '东罗马帝国的神学哲学。', x: 55, y: 28, r: 11, path: '/school/拜占庭哲学' },
  { id: 'slavic', name: '东欧', sub: '东欧斯拉夫哲学', desc: '舍斯托夫、索洛维约夫、俄罗斯宗教哲学。', x: 58, y: 18, r: 20, path: '/school/东欧斯拉夫哲学' },
  // 中东集群
  { id: 'islam', name: '伊斯兰', sub: '伊斯兰哲学', desc: '百年翻译运动、阿维森纳、苏菲神秘主义。', x: 58, y: 44, r: 22, path: '/school/伊斯兰哲学' },
  { id: 'arab', name: '阿拉伯', sub: '阿拉伯哲学', desc: '铿迪、法拉比——理性与信仰的调和。', x: 62, y: 48, r: 14, path: '/school/阿拉伯哲学' },
  { id: 'egypt', name: '古埃及', sub: '古埃及哲学', desc: '玛阿特——宇宙秩序、真理与正义的永恒法则。', x: 50, y: 42, r: 14, path: '/school/古埃及哲学' },
  { id: 'inca', name: '印加', sub: '印加哲学', desc: '帕查、艾尼、帕查玛玛——安第斯的大地伦理。', x: 28, y: 68, r: 14, path: '/school/印加哲学' },
  { id: 'mesopotamia', name: '美索不达米亚', sub: '美索不达米亚哲学', desc: '人类最早的哲学追问。', x: 62, y: 36, r: 14, path: '/school/美索不达米亚哲学' },
  { id: 'persia', name: '波斯', sub: '波斯哲学', desc: '琐罗亚斯德、苏菲诗歌、光明与黑暗。', x: 66, y: 38, r: 18, path: '/school/波斯哲学' },
  { id: 'jewish', name: '犹太', sub: '犹太哲学', desc: '塔木德传统、迈蒙尼德、列维纳斯。', x: 56, y: 38, r: 14, path: '/school/犹太哲学' },
  { id: 'hebrew', name: '希伯来', sub: '古希伯来哲学', desc: '约伯、传道书——信仰、苦难与神圣正义的追问。', x: 54, y: 50, r: 12, path: '/school/古希伯来哲学' },
  // 非洲
  { id: 'africa', name: '非洲', sub: '非洲哲学', desc: '口头传统、社群伦理、后殖民批判。', x: 50, y: 60, r: 40, path: '/school/非洲哲学' },
  // 美洲
  { id: 'na', name: '北美', sub: '北美哲学', desc: '实用主义、超验主义、过程哲学。', x: 18, y: 25, r: 26, path: '/school/北美哲学' },
  { id: 'pragmatism', name: '美东', sub: '实用主义', desc: '皮尔士、詹姆斯、杜威——真理即有用。', x: 24, y: 30, r: 12, path: '/school/实用主义' },
  { id: 'latin', name: '拉丁美洲', sub: '拉丁美洲哲学', desc: '解放神学、混血意识、魔幻现实主义。', x: 25, y: 65, r: 32, path: '/school/拉丁美洲哲学' },
  { id: 'maya', name: '玛雅', sub: '玛雅哲学', desc: '波波尔·乌、时间循环、玉米人。', x: 22, y: 55, r: 14, path: '/school/玛雅哲学' },
  { id: 'aztec', name: '阿兹特克', sub: '阿兹特克哲学', desc: '宇宙论、献祭辩证法、第五太阳纪。', x: 18, y: 50, r: 14, path: '/school/阿兹特克哲学' },
  // 大洋洲
  { id: 'australia', name: '澳洲', sub: '澳洲原住民哲学', desc: 'Dreamtime、歌线、土地伦理。', x: 88, y: 75, r: 20, path: '/school/澳洲原住民哲学' },
  { id: 'austronesian', name: '南岛', sub: '南岛哲学', desc: '海洋迁徙·Mana与Tapu·关系性自我。', x: 84, y: 48, r: 16, path: '/school/南岛哲学' },
  { id: 'pacific', name: '太平洋', sub: '太平洋原住民哲学', desc: '礼物经济·土地人格·修复性正义。', x: 94, y: 62, r: 18, path: '/school/太平洋原住民哲学' },
  { id: 'arctic', name: '北极', sub: '北极原住民哲学', desc: '冰雪智慧·动物能动性·Sila伦理。', x: 30, y: 5, r: 20, path: '/school/北极原住民哲学' },
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
          role="button" tabIndex={0}
          aria-label={r.name + ' — ' + r.desc}
          onMouseEnter={() => setHover(r)}
          onMouseLeave={() => setHover(null)}
          onFocus={() => setHover(r)}
          onBlur={() => setHover(null)}
          onClick={() => navigate(r.path)}
          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(r.path); } }}
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
        >
          {/* Pulse dot — crimson + white hot center, high contrast on map */}
          <div style={{
            position: 'absolute', left: '50%', top: '50%',
            width: 10, height: 10, transform: 'translate(-50%, -50%)',
            background: 'radial-gradient(circle, #FFFFFF 0%, #E85050 30%, #8B1A1A 70%, transparent 100%)',
            borderRadius: '50%',
            boxShadow: '0 0 16px 6px rgba(232,80,80,0.8), 0 0 32px 12px rgba(200,30,30,0.4), 0 0 48px 16px rgba(180,20,20,0.2)',
            animation: 'pulse-dot 2.5s ease-in-out infinite',
          }} />
          {/* Outer glow ring */}
          <div style={{
            position: 'absolute', left: '50%', top: '50%',
            width: 18, height: 18, transform: 'translate(-50%, -50%)',
            border: '2px solid rgba(232,80,80,0.5)',
            borderRadius: '50%',
            animation: 'pulse-ring 2.5s ease-in-out infinite',
          }} />
        </div>
      ))}
      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 0.5; transform: translate(-50%,-50%) scale(0.8); }
          50% { opacity: 1; transform: translate(-50%,-50%) scale(1.4); }
        }
        @keyframes pulse-ring {
          0%, 100% { opacity: 0.3; transform: translate(-50%,-50%) scale(0.8); }
          50% { opacity: 0.7; transform: translate(-50%,-50%) scale(1.6); }
        }
      `}</style>

      {/* 悬浮卡片 — 磨砂玻璃 */}
      {hover && (
        <div style={{
          position: 'absolute',
          left: `${hover.x}%`, top: `${hover.y - hover.r * 0.06}%`,
          transform: 'translate(-50%, -100%)',
          background: 'color-mix(in srgb, var(--primary) 75%, transparent)',
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
