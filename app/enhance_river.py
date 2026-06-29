"""Enhance GenealogyPage with century dividers, SVG connectors, richer cards"""
import re

with open('src/pages/GenealogyPage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace line connector with elegant SVG
old_line = """"<div style={{
                position: 'absolute',
                left: '50%', top: '50%',
                width: isLeft ? 'calc(50% - 5%)' : 'calc(50% - 5%)',
                height: 1,
                background: `linear-gradient(to ${'right' if isLeft else 'left'}, transparent, ${color}40)`,
                transform: 'translateY(-50%)',
                [isLeft ? 'right' : 'left']: '50%',
              }} />" """

new_line = """"<svg style={{
                position:'absolute', top:0, left:0, width:'100%', height:'100%',
                pointerEvents:'none', zIndex:0,
              }}>
                <path d={isLeft
                  ? `M 50% 50% C 45% 50%, 30% ${isWorld ? '60%' : '40%'}, 10% 50%`
                  : `M 50% 50% C 55% 50%, 70% ${isWorld ? '60%' : '40%'}, 90% 50%`}
                  stroke={color} strokeWidth={isWorld ? '0.8' : '0.5'}
                  fill='none' opacity='0.2' />
              </svg>" """

content = content.replace(old_line.strip(), new_line.strip())

# 2. Add century section headers
old_map_start = "{ALL_SCHOOLS.map((school, i) => {"
new_map_start = """{(() => {
          let lastCentury = '';
          return ALL_SCHOOLS.map((school, i) => {
            const showCentury = school.century !== lastCentury;
            lastCentury = school.century;"""
content = content.replace(old_map_start, new_map_start)

# 3. Add century header rendering before isLeft check
old_isleft = "const isLeft = i % 3 === 0 || i % 3 === 2;"
new_isleft = """const isLeft = i % 3 === 0 || i % 3 === 2;

            if (showCentury && i > 0) {
              return (
                <div key={'h-'+i} style={{
                  textAlign:'center', padding:'28px 0 8px', position:'relative', zIndex:1,
                }}>
                  <div style={{
                    display:'inline-block', background:'#F8F6F2', padding:'3px 18px',
                    borderRadius:3, border:'1px solid #E5DFD5',
                  }}>
                    <span style={{
                      fontSize:10, fontWeight:500, letterSpacing:'0.15em',
                      color:'#C4956A', fontFamily:'var(--font-sans)',
                    }}>{school.century}</span>
                  </div>
                </div>
              );
            }"""
content = content.replace(old_isleft, new_isleft)

# 4. Close IIFE
old_map_end = "})}"
new_map_end = """});
          })()}"""
content = content.replace(old_map_end, new_map_end)

with open('src/pages/GenealogyPage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Enhanced')
