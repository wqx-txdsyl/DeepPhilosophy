"""Generate the durable score matrix (JSON, Markdown, HTML and PNG).

Current suite dimensions and withdrawn historical sample ratings remain separate.
Run with a Python environment providing Pillow; no model or network calls.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import html
import json
import os
from pathlib import Path
import sys
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'))
import aggregate_benchmark_scores as aggregate
OUT=ROOT/'docs/evidence/benchmark_ledger'


def display(bounds, digits=1):
    if bounds is None:return '—'
    a,b=bounds
    return f'{float(a):.{digits}f}' if a==b else f'{float(a):.{digits}f}–{float(b):.{digits}f}'


def dimension(rows,key):
    per_case=defaultdict(list)
    for r in rows:
        if key not in r['ratings']:continue
        val=r['ratings'][key];maximum=1 if key.startswith('K') else 4
        per_case[r['case_id']].append((Fraction(0),Fraction(100)) if val=='U' else (Fraction(val*100,maximum),)*2)
    return aggregate.mean_bounds([aggregate.mean_bounds(v) for v in per_case.values()]),len(per_case)


def matrix():
    registry=json.loads(aggregate.REGISTRY.read_text());data=aggregate.build()
    if json.loads((OUT/'aggregate.json').read_text())!=data:
        raise ValueError('Run aggregate_benchmark_scores.py first; aggregate is stale')
    rules=json.loads((ROOT/registry['rubric']).read_text())
    legacy_path=ROOT/'docs/evidence/rubric_calibration_v1_1/SCORES.json'
    legacy_rules_path=legacy_path.with_name('RUBRIC_V1_1.json')
    legacy=json.loads(legacy_path.read_text());legacy_rules=json.loads(legacy_rules_path.read_text())
    current_cols=[{'name':'PhiAgent','sub':'v'+v,'own':True} for v in ['0.1.0','0.1.1','0.1.2']]+[{'name':v,'sub':'同题集未测','own':False} for v in ['DeepSeek','豆包','ChatGPT']]
    scored=[json.loads((ROOT/v['review']).read_text())['rows'] for v in registry['versions'] if v['review']]
    rows=[{'label':'综合指数','note':'共同64题 · 暂定 /100','values':[f"{data['runs'][v]['common_fully_scored_cases']['score']:.2f}" for v in ['0.1.0','0.1.1']]+['—']*4,'primary':True}]
    rows.append({'label':'共同复核指数','note':'同组10题 · /100','values':[f"{data['runs'][v]['common_independently_reviewed_cases']['score']:.2f}" for v in ['0.1.0','0.1.1']]+['—']*4,'primary':False})
    for group in ['C','R','K']:
        for key,spec in rules[group].items():
            title=spec['name'] if isinstance(spec,dict) else {'K1':'核验与证据一致','K2':'不超出检索范围','K3':'区分材料状态','K4':'不编造出处或执行'}[key]
            values=[];counts=[]
            for rs in scored:
                bounds,n=dimension(rs,key);values.append(display(bounds));counts.append(n)
            rows.append({'label':key+' '+title,'note':f'{counts[0]}道适用题 · /100','values':values+['—']*4,'primary':False})
    rows.append({'label':'完成题数','note':'固定70题 · 非百分分数','values':['65 / 70','65 / 70','未跑全套','未测','未测','未测'],'primary':False})
    titles={'L1':('DeepSeek','安慰题 · 旧答'),'L2':('豆包','安慰题 · 旧答'),'L3':('ChatGPT','安慰题 · 旧答'),'L4':('PhiAgent旧答','版本未核定'),'P1':('康德','第二类比选段'),'P2':('斯宾诺莎','伦理学 I·11'),'P3':('休谟','人性论选段')}
    selected=[next(r for r in legacy if r['id']==key) for key in titles]
    legacy_cols=[{'name':titles[r['id']][0],'sub':titles[r['id']][1],'own':r['id']=='L4'} for r in selected]
    old_rows=[{'label':'历史样本总分','note':'旧v1.1 · 不可与上表排名','values':[display((r['score_lower'],r['score_upper'])) for r in selected],'primary':True}]
    for i,(key,name,_) in enumerate(legacy_rules['dimensions']):
        vals=[]
        for r in selected:
            v=r['scores'][i];vals.append('—' if v is None else '未知' if v=='U' else f'{v*25:.1f}')
        old_rows.append({'label':key+' '+name,'note':'原0–4等级 ×25','values':vals,'primary':False})
    old_rows.append({'label':'样本数量','note':'非测试集均分','values':['1份答复']*4+['1段原典']*3,'primary':False})
    return {'scale':100,'product_version':'0.1.2','aggregate_source_sha256':aggregate.sha(OUT/'aggregate.json'),
            'historical_source_sha256':{str(p.relative_to(ROOT)):aggregate.sha(p) for p in [legacy_path,legacy_rules_path]},
            'current':{'title':'冻结 v1.2 · 当前测试集（开发暂定）','subtitle':'每题等权，多轮先在题内平均；多数为未校准自动初评，LLM 官方产品尚无同题集成绩。','columns':current_cols,'rows':rows},
            'historical':{'title':'历史样本档案 · 旧 v1.1 已撤回','subtitle':'LLM 原答与哲学原典均为单份样本；这里只展示旧记录，不重评原典作者。','columns':legacy_cols,'rows':old_rows},
            'notes':['— 表示未测或不适用，绝非0分；区间表示已有未知项。所有评分行均以100为满分。',
                     '上表分维度只统计适用题：C为60题，R为24题，K为5道纯核验题；不是未实测的K故障组。',
                     '综合指数为共同64题局部成绩；完整70题仍缺测。分维度均分不能再次平均来复算综合指数。',
                     '历史D维度与当前C/R/K维度定义不同，禁止混算或跨区排名。当前大部分得分仍为未经校准的自动初评。']}


def markdown(data):
    blocks=['# PhiAgent 多维百分制记录表','最新版本：v0.1.2。当前套题与历史样本分区展示，均不宣称已通过质量验收。']
    for name in ['current','historical']:
        t=data[name];blocks += ['## '+t['title'],t['subtitle']]
        table=['|维度|'+ '|'.join(c['name']+' '+c['sub'] for c in t['columns'])+'|','|---|'+'---|'*len(t['columns'])]
        table += ['|'+r['label']+'（'+r['note']+'）|'+'|'.join(r['values'])+'|' for r in t['rows']]
        blocks.append('\n'.join(table))
    blocks += ['\n'.join('- '+n for n in data['notes']),
               '来源：[版本台账](../../PHIAGENT_VERSION_BENCHMARK_LEDGER.md)、[机器数据](matrix.json)、[旧样本评分](../rubric_calibration_v1_1/SCORES.json)。']
    return '\n\n'.join(blocks)+'\n'


def html_page(data):
    esc=html.escape
    sections=[]
    for name in ['current','historical']:
        t=data[name]
        head='<tr><th>评分维度 <small>百分制</small></th>'+''.join(f'<th class="{"own" if c["own"] else ""}">{esc(c["name"])}<small>{esc(c["sub"])}</small></th>' for c in t['columns'])+'</tr>'
        body=''.join('<tr class="'+('primary' if r['primary'] else '')+'"><th>'+esc(r['label'])+'<small>'+esc(r['note'])+'</small></th>'+''.join('<td class="'+('muted' if v in ['—','未测','未跑全套'] else '')+'">'+esc(v)+'</td>' for v in r['values'])+'</tr>' for r in t['rows'])
        sections.append(f'<section id="{name}"><h2>{esc(t["title"])}</h2><p>{esc(t["subtitle"])}</p><p class="hint">横向滚动可查看全部对象。</p><div class="scroll"><table><thead>{head}</thead><tbody>{body}</tbody></table></div></section>')
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PhiAgent 多维评测记录</title><style>'+'''
*{box-sizing:border-box}body{margin:0;background:#f7f7f5;color:#252622;font:15px/1.5 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1500px;margin:auto;padding:48px 32px}h1{font-size:32px;margin:8px 0}header p,section>p{color:#70726c}header .eyebrow{letter-spacing:.16em;font-size:12px}nav{display:flex;gap:8px;margin:24px 0}button{border:1px solid #ddd;background:white;border-radius:6px;padding:10px 18px;color:#333;cursor:pointer}button.active{background:#292e29;color:white}section{background:white;border:1px solid #e6e7e2;border-radius:12px;padding:28px;margin:24px 0}h2{font-size:20px;margin:0}section>p{margin:6px 0 22px}.hint{display:none;font-size:12px;color:#8a9083}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:940px;table-layout:fixed}th,td{padding:12px 6px;text-align:center;border-bottom:1px solid #edeee9;font-variant-numeric:tabular-nums}thead th{border-bottom:2px solid #c6cbc3;font-size:17px}thead th:first-child,tbody th{width:240px;text-align:left;font-weight:500}small{display:block;color:#93968f;font-size:11px;font-weight:400;margin-top:3px}.own{background:#f0f3ee;border-top:3px solid #52674d}.primary{background:#f5f7f3;font-weight:600}.primary td{font-size:20px}td.muted{color:#babdb5}footer{color:#777c72;font-size:13px}footer li{margin:5px 0}a{color:#52674d}section[hidden]{display:none}@media(max-width:1100px){.hint{display:block}}@media(max-width:650px){main{padding:24px 12px}section{padding:16px}h1{font-size:26px}}@media print{body{background:white}main{padding:0}nav{display:none}section{break-inside:avoid}table{min-width:0}th,td{font-size:10px;padding:6px}small{font-size:8px}}
'''+ '</style><main><header><div class="eyebrow">PHIAGENT / EVALUATION RECORD</div><h1>多维评测记录</h1><p>v0.1.0 → v0.1.1 → v0.1.2 · 满分100 · 截至2026-10-02</p></header><nav><button class="active" data-view="all">全部记录</button><button data-view="current">当前测试集</button><button data-view="historical">历史样本</button></nav>'+''.join(sections)+'<footer><ul>'+''.join('<li>'+esc(n)+'</li>' for n in data['notes'])+'</ul><a href="../../PHIAGENT_VERSION_BENCHMARK_LEDGER.md">版本与评分长期台账</a> · <a href="matrix.json">可追溯数据</a></footer></main><script>document.querySelectorAll("button[data-view]").forEach(b=>b.onclick=()=>{document.querySelectorAll("button[data-view]").forEach(x=>x.classList.toggle("active",x===b));document.querySelectorAll("section").forEach(s=>s.hidden=b.dataset.view!=="all"&&s.id!==b.dataset.view)})</script></html>'


def png(data, target):
    from PIL import Image, ImageDraw, ImageFont
    font_path='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    if not Path(font_path).is_file():raise SystemExit('Set an available CJK font for PNG rendering')
    W=2160;H=2400
    im=Image.new('RGB',(W,H),'#ffffff');d=ImageDraw.Draw(im)
    fonts={size:ImageFont.truetype(font_path,size) for size in [18,20,22,24,26,28,32,40,46]}
    def text(x,y,s,size=24,color='#252722',align='left'):
        if align=='center':x-=d.textlength(s,font=fonts[size])/2
        d.text((x,y),s,font=fonts[size],fill=color)
    text(72,38,'PHIAGENT / EVALUATION RECORD',20,'#7e857a')
    text(72,75,'多维百分制评测记录',46)
    text(1200,95,'v0.1.0  →  v0.1.1  →  v0.1.2    ·    2026-10-02',22,'#7e857a')
    y=170
    for name in ['current','historical']:
        t=data[name];text(72,y,t['title'],32);y+=48;text(72,y,t['subtitle'],22,'#7e857a');y+=48
        left=72;labelw=455;right=W-72;cw=(right-left-labelw)/len(t['columns']);header_y=y
        for i,c in enumerate(t['columns']):
            x=left+labelw+i*cw
            if c['own']:
                d.rectangle((x+5,y,x+cw-5,y+83),fill='#f0f3ee');d.line((x+5,y,x+cw-5,y),fill='#52674d',width=4)
            text(x+cw/2,y+15,c['name'],28,align='center');text(x+cw/2,y+52,c['sub'],20,'#8a8f83',align='center')
        y+=90;d.line((left,y,right,y),fill='#bfc5b9',width=2)
        for r in t['rows']:
            row_h=50
            if r['primary']:d.rectangle((left,y,right,y+row_h),fill='#f5f7f3')
            text(left+4,y+5,r['label'],24);text(left+4,y+31,r['note'],18,'#90968a')
            for i,val in enumerate(r['values']):text(left+labelw+(i+.5)*cw,y+13,val,26,'#b7bcb1' if val in ['—','未测','未跑全套'] else '#252722',align='center')
            y+=row_h;d.line((left,y,right,y),fill='#edf0e8')
        y+=44
    for n in data['notes']:
        text(72,y,n,20,'#7c8376');y+=30
    im.crop((0,0,W,y+36)).save(target)


def main():
    p=argparse.ArgumentParser();p.add_argument('--png',type=Path);args=p.parse_args()
    data=matrix();(OUT/'matrix.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (OUT/'MATRIX.md').write_text(markdown(data));(OUT/'matrix.html').write_text(html_page(data))
    if args.png:args.png.parent.mkdir(parents=True,exist_ok=True);png(data,args.png)
    print('Matrix generated; source scores preserved, historical rubric separated.')


if __name__=='__main__':main()
