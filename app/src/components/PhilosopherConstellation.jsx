/**
 * 哲学家星丛 — AI 识别的真实思想关系可视化
 * 关系类型：师承 / 影响 / 论敌 / 友·合作
 */
import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from './Icon';

// 区域色
const REGION_COLORS = {
  '东方': { fill: 'rgba(59,90,150,0.12)', stroke: '#4a6fb5', text: '#3b5a96' },
  '西方': { fill: 'rgba(145,118,71,0.10)', stroke: '#b89447', text: '#8a6d3b' },
  '世界': { fill: 'rgba(90,138,90,0.10)', stroke: '#5a9a5a', text: '#4a7a4a' },
};

// 关系类型：颜色 + 图例 icon 名
const REL_STYLES = {
  '师承':   { stroke: '#c17d3b', dash: 'none', label: '师承', icon: 'icon-book-open' },
  '影响':   { stroke: '#7b9ec7', dash: 'none', label: '影响', icon: 'icon-candle' },
  '论敌':   { stroke: '#c75b5b', dash: '4 2', label: '论敌', icon: 'icon-drama' },
  '友/合作': { stroke: '#5b9a6b', dash: 'none', label: '友', icon: 'icon-handshake' },
};

function regionColor(region) {
  return REGION_COLORS[region] || REGION_COLORS['西方'];
}

function relStyle(type) {
  for (const [key, val] of Object.entries(REL_STYLES)) {
    if (type?.includes(key) || key.includes(type || '')) return val;
  }
  return { stroke: 'var(--text-dim)', dash: 'none', label: type || '?', icon: 'icon-question' };
}

export default function PhilosopherConstellation({ name, region }) {
  const [network, setNetwork] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/philosopher_network.json')
      .then(r => r.ok ? r.json() : {})
      .then(data => {
        setNetwork(data[name] || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [name]);

  // 计算节点布局
  const layout = useMemo(() => {
    if (!network?.connections?.length) return null;

    const connections = network.connections.slice(0, 15);
    const maxScore = Math.max(...connections.map(c => c.score), 1);

    const orbits = {};
    for (const c of connections) {
      let r;
      if (c.score >= 5) r = 0.27;
      else if (c.score >= 3) r = 0.45;
      else r = 0.63;
      if (!orbits[r]) orbits[r] = [];
      orbits[r].push(c);
    }

    const nodes = [];
    const seed = name.split('').reduce((s, c) => s + c.charCodeAt(0), 0);
    for (const [radius, items] of Object.entries(orbits)) {
      const r = parseFloat(radius);
      const startAngle = (seed * 0.37) % (Math.PI * 2);
      const count = items.length;
      for (let i = 0; i < count; i++) {
        const angle = startAngle + (i / count) * Math.PI * 2;
        const jitter = angle + Math.sin(i * 1.3 + seed * 0.01) * 0.06;
        const jitterR = r + Math.cos(i * 1.9 + seed * 0.01) * 0.025;
        nodes.push({
          ...items[i],
          x: 0.5 + Math.cos(jitter) * jitterR,
          y: 0.5 + Math.sin(jitter) * jitterR,
          orbit: r,
        });
      }
    }

    return { nodes, maxScore, isHot: network.is_hot, seed };
  }, [network, name]);

  if (loading) return <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: 12 }}><Icon name="icon-sparkles" size={14} /> 星丛加载中...</div>;
  if (!network || !network.connections?.length) {
    return (
      <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-dim)', fontSize: 13 }}>
        <p style={{ margin: '0 0 8px' }}><Icon name="icon-sparkles" size={32} /></p>
        <p style={{ margin: 0 }}>{network ? '暂无足够思想关系数据' : '星丛数据加载失败'}</p>
        <p style={{ fontSize: 11, margin: '4px 0 0', opacity: 0.6 }}>仅大哲学家之间可构建星丛</p>
      </div>
    );
  }

  const { nodes, maxScore } = layout;
  const mainColor = regionColor(region);

  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{
        fontFamily: 'var(--font-serif)', fontSize: 18, fontWeight: 400,
        color: 'var(--ink)', marginBottom: 4, letterSpacing: '0.03em',
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <Icon name="icon-sparkles" size={20} /> 思想星丛
      </h3>
      <p style={{ fontSize: 11, color: 'var(--text-dim)', margin: '0 0 16px' }}>
        基于 AI 识别的真实思想关系 · 越近关联越强 · 点击跳转
      </p>

      {/* 图例 */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 12, justifyContent: 'center' }}>
        {Object.entries(REL_STYLES).map(([type, style]) => (
          <span key={type} style={{ fontSize: 10, color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{
              display: 'inline-block', width: 14, height: 2,
              background: style.stroke,
            }} />
            <Icon name={style.icon} size={11} />
            <span>{style.label}</span>
          </span>
        ))}
      </div>

      <div style={{
        position: 'relative', width: '100%',
        aspectRatio: '1 / 1', maxWidth: 440, margin: '0 auto',
      }}>
        <svg viewBox="0 0 1 1"
          style={{ width: '100%', height: '100%', overflow: 'visible' }}>
          {/* 连接线 */}
          {nodes.map((n, i) => {
            const style = relStyle(n.type);
            return (
              <line key={`line-${i}`}
                x1={0.5} y1={0.5} x2={n.x} y2={n.y}
                stroke={style.stroke} strokeWidth="0.0035"
                opacity={0.25 + (n.score / maxScore) * 0.35}
                strokeDasharray={style.dash}
              />
            );
          })}

          {/* 淡色轨道 */}
          {[0.27, 0.45, 0.63].map((r, i) => (
            <circle key={`orb-${i}`} cx={0.5} cy={0.5} r={r}
              fill="none" stroke="var(--border)" strokeWidth="0.002"
              strokeDasharray="0.008 0.025" opacity={0.25} />
          ))}

          {/* 外围节点 */}
          {nodes.map((n, i) => {
            const color = regionColor(n.region);
            const relS = relStyle(n.type);
            const size = 0.018 + (n.score / maxScore) * 0.014;
            return (
              <g key={`node-${i}`}
                onClick={() => navigate(`/author/${encodeURIComponent(n.name)}`)}
                onMouseEnter={() => setTooltip(n)}
                onMouseLeave={() => setTooltip(null)}
                style={{ cursor: 'pointer' }}>
                {/* 光晕 */}
                <circle cx={n.x} cy={n.y} r={size + 0.009}
                  fill={color.fill} stroke={relS.stroke} strokeWidth="0.004"
                  opacity={0.5} />
                {/* 实体 */}
                <circle cx={n.x} cy={n.y} r={size}
                  fill={color.stroke} stroke="var(--bone)" strokeWidth="0.002"
                  opacity={0.9} />
                {/* 关系标记圆点 */}
                <circle cx={n.x} cy={n.y} r={size * 0.42}
                  fill={relS.stroke} opacity={0.9} />
                {/* 名字标签 */}
                <text x={n.x} y={n.y + size + 0.026}
                  textAnchor="middle"
                  fill="var(--text)"
                  fontSize={0.021}
                  fontFamily="var(--font-serif)"
                  style={{ pointerEvents: 'none' }}>
                  {n.name.length > 4 ? n.name.slice(0, 4) + '…' : n.name}
                </text>
              </g>
            );
          })}

          {/* 中心节点 */}
          <circle cx={0.5} cy={0.5} r={0.065}
            fill={mainColor.stroke} stroke="var(--bone)" strokeWidth="0.007"
            opacity={0.95}
            style={{ filter: 'drop-shadow(0 0 0.012px rgba(0,0,0,0.25))' }} />
          <text x={0.5} y={0.5 + 0.005}
            textAnchor="middle" dominantBaseline="middle"
            fill="#fff" fontSize={0.024} fontWeight={600}
            fontFamily="var(--font-serif)"
            style={{ pointerEvents: 'none' }}>
            {name.length > 6 ? name.slice(0, 5) + '…' : name}
          </text>
        </svg>

        {/* Tooltip */}
        {tooltip && (
          <div style={{
            position: 'absolute',
            top: `calc(${Math.max(0, tooltip.y - 0.06) * 100}% - 64px)`,
            left: `${Math.min(0.85, Math.max(0.05, tooltip.x)) * 100}%`,
            transform: 'translateX(-50%)',
            background: 'var(--card-bg)',
            border: '1px solid var(--border)',
            borderRadius: 8, padding: '8px 12px',
            fontSize: 11, color: 'var(--text)',
            zIndex: 20, pointerEvents: 'none',
            whiteSpace: 'nowrap',
            boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
            minWidth: 120, textAlign: 'center',
          }}>
            <div style={{ fontWeight: 600, marginBottom: 2, fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
              <Icon name={relStyle(tooltip.type).icon} size={13} />
              {tooltip.name}
            </div>
            <div style={{
              fontSize: 10, color: relStyle(tooltip.type).stroke,
              fontWeight: 500, marginBottom: 2,
            }}>
              {tooltip.type}{tooltip.role ? ` · ${tooltip.role}` : ''}
            </div>
            {tooltip.note && (
              <div style={{ fontSize: 10, color: 'var(--text-dim)', maxWidth: 180 }}>
                {tooltip.note}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
