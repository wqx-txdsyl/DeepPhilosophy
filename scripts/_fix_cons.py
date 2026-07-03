"""Fix constellation: focused node renders last (on top)."""
with open(r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\components\school\ConstellationMap.jsx", 'r', encoding='utf-8') as f:
    c = f.read()

# Find the start and end of the NODES section
start = c.find('{/* NODES')
end_marker = '{/* NODES — second pass: focused node ON TOP */}'
end = c.find(end_marker)

if end > start:
    # Remove the old second pass if it exists
    # Find the next section marker after nodes
    after_nodes = c.find('</svg>', end)
    if after_nodes > end and end > 0:
        # Already has two passes, just need to make sure focused renders last
        print("Two-pass already exists")
        # Check if the SVG closing is right after the second pass
        pass
    else:
        # Need to fix - focused node detail panel is still in first pass
        # The simplest fix: after all nodes, re-render the focused node's detail panel
        # Find the closing </svg>
        svg_end = c.find('</svg>', c.find('NODES'))
        before_svg = c[:svg_end]
        after_svg = c[svg_end:]

        # Add a top-layer for focused node detail panel after all nodes
        top_layer = """
          {/* Top layer — focused node detail panel, rendered last to avoid clipping */}
          {focusNode && thinkers.filter(t => t.name === focusNode).map(t => {
            const baseSize = getNodeSize(t);
            const color = SUB_COLORS[t.sub] || 'var(--ochre)';
            return (
              <g key="top-detail" style={{ pointerEvents: 'none' }}>
                <rect x={t._x - 80} y={t._y - baseSize - 78} width={160} height={66} rx={6}
                  fill="rgba(248,244,238,0.97)" stroke={color} strokeWidth="0.8" strokeOpacity="0.5"
                  filter="drop-shadow(0 2px 12px rgba(0,0,0,0.08))" />
                <text x={t._x} y={t._y - baseSize - 60} textAnchor="middle" fill="var(--ink)"
                  fontSize={12} fontFamily="var(--font-serif)" fontWeight={600}>{t.name}</text>
                <text x={t._x} y={t._y - baseSize - 44} textAnchor="middle" fill={color}
                  fontSize={9} fontFamily="var(--font-sans)" fontWeight={500}>{t.sub}</text>
                <text x={t._x} y={t._y - baseSize - 30} textAnchor="middle" fill="var(--text-dim)"
                  fontSize={9} fontFamily="var(--font-sans)">{t.era} · {t.key}</text>
                <text x={t._x} y={t._y - baseSize - 18} textAnchor="middle" fill="var(--fade)"
                  fontSize={8} fontFamily="var(--font-sans)">{Array.isArray(t.works) ? t.works.length + ' works' : ''}</text>
              </g>
            );
          })}
"""
        c = before_svg + top_layer + after_svg
        with open(r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\components\school\ConstellationMap.jsx", 'w', encoding='utf-8') as f:
            f.write(c)
        print("Added top-layer for focused node detail panel")
else:
    print("NODES section not found")
