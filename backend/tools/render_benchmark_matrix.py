"""Generate the durable score matrix (JSON, Markdown, HTML and PNG).

Only the frozen v1.2 suite is shown; historical sample archives are not loaded.
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
    specs=[]
    for entry in registry['versions']:
        specs.append({'name':'PhiAgent','sub':'v'+entry['version'],'own':True,
                      'review':entry.get('review'),'summary':data['runs'][entry['version']]})
    for entry in registry['external_baselines']:
        summary=data.get('external_results',{}).get(entry.get('id'))
        specs.append({'name':entry.get('display_name',entry['name']),
                      'sub':('Work · '+entry['model_snapshot']+' · '+entry['mode']) if summary and entry.get('surface')=='Work' else (entry['model_snapshot']+' · '+entry['mode']) if summary else '尚无套题评分',
                      'own':False,'review':entry.get('review'),'summary':summary})
    current_cols=[{k:c[k] for k in ['name','sub','own']} for c in specs]
    scored=[json.loads((ROOT/c['review']).read_text())['rows'] if c['review'] else None for c in specs]
    rows=[]
    for label,note,key in [('综合指数','固定64题子集 · 暂定 /100','common_fully_scored_cases'),
                           ('已完成题集指数','65题宏平均 · 暂定 /100','completed_cases'),
                           ('固定10题指数','原PhiAgent复核题目子集 · /100','common_independently_reviewed_cases')]:
        vals=[]
        for c in specs:
            value=(c['summary'] or {}).get(key)
            vals.append(display((value['lower'],value['upper']),2) if value and value['lower'] is not None else '—')
        rows.append({'label':label,'note':note,'values':vals,'primary':key=='common_fully_scored_cases'})
    for group in ['C','R','K']:
        for key,spec in rules[group].items():
            title=spec['name'] if isinstance(spec,dict) else {'K1':'核验与证据一致','K2':'不超出检索范围','K3':'区分材料状态','K4':'不编造出处或执行'}[key]
            values=[];counts=[]
            for rs in scored:
                if rs is None:values.append('—');continue
                bounds,n=dimension(rs,key);values.append(display(bounds));counts.append(n)
            count_note=str(counts[0]) if len(set(counts))==1 else '/'.join(map(str,counts))
            rows.append({'label':key+' '+title,'note':f'{count_note}道适用题 · /100','values':values,'primary':False})
    values=[]
    for c in specs:
        summary=c['summary'] or {};coverage=summary.get('completed_cases')
        values.append(str(coverage['case_count'])+' / 70' if coverage else '未跑全套' if c['own'] else '未测')
    rows.append({'label':'答卷覆盖题数','note':'固定70题 · 非百分分数','values':values,'primary':False})
    rows.append({'label':'评审覆盖','note':'评审方法有差异 · 非分数','values':[
        (f"{c['summary']['reviewed_turns']}/{c['summary']['total_turns']}轮复核" if c['own'] and c['summary'].get('total_turns') else
         c['summary'].get('review_coverage_label') or (str(c['summary'].get('document_reviewed_turns',0))+'轮文本评审') if not c['own'] and c['summary'] else '未测')
        for c in specs],'primary':False})
    return {'scale':100,'product_version':'0.1.2','aggregate_source_sha256':aggregate.sha(OUT/'aggregate.json'),
            'current':{'title':'冻结 v1.2 · 当前测试集（开发暂定）','subtitle':'每题等权、题内各轮先平均。DeepSeek/豆包为官方网页采集；不同产品的工具条件与评审覆盖不同。','columns':current_cols,'rows':rows},
            'notes':['— 表示未测或不适用，绝非0分；区间表示已有未知项。所有评分行均以100为满分。',
                     '上表分维度只统计适用题：C为60题，R为24题，K为5道纯核验题；不是未实测的K故障组。',
                     '综合指数采用固定64题子集；完整70题仍缺测。各维度仅统计适用题，不能再平均复算总分。',
                     '固定10题来自PhiAgent两次都经过复核的题目，并不代表其他列也完成了同等复核。',
                     'DeepSeek：深度思考＋联网；豆包：快速默认档。各65题77轮，K故障组未运行；网页模型的具体版本未记录。',
                     '浏览器答卷由DeepSeek匿名模型初评、统一重评表达维度，再作Codex定向复核；同族评审偏差与证据缺口仍可能存在。',
                     'PhiAgent混合自动初评与部分复核；ChatGPT Work为Codex全文开发评审。评审者与条件不一致，本表不是统一盲评排行榜。',
                     'ChatGPT Work：桌面6.1 Sol high、声明使用本地书库；不是网页端逐题回执，K4执行事实有4项未知。']}


def markdown(data):
    blocks=['# PhiAgent 多维百分制记录表','最新版本：v0.1.2。只展示冻结 v1.2 测试集，不宣称已通过质量验收。']
    for name in ['current']:
        t=data[name];blocks += ['## '+t['title'],t['subtitle']]
        table=['|维度|'+ '|'.join(c['name']+' '+c['sub'] for c in t['columns'])+'|','|---|'+'---|'*len(t['columns'])]
        table += ['|'+r['label']+'（'+r['note']+'）|'+'|'.join(r['values'])+'|' for r in t['rows']]
        blocks.append('\n'.join(table))
    blocks += ['\n'.join('- '+n for n in data['notes']),
               '来源：[版本台账](../../PHIAGENT_VERSION_BENCHMARK_LEDGER.md)、[机器数据](matrix.json)。']
    return '\n\n'.join(blocks)+'\n'


def html_page(data):
    esc=html.escape
    sections=[]
    for name in ['current']:
        t=data[name]
        head='<tr><th>评分维度 <small>百分制</small></th>'+''.join(f'<th class="{"own" if c["own"] else ""}">{esc(c["name"])}<small>{esc(c["sub"])}</small></th>' for c in t['columns'])+'</tr>'
        body=''.join('<tr class="'+('primary' if r['primary'] else '')+'"><th>'+esc(r['label'])+'<small>'+esc(r['note'])+'</small></th>'+''.join('<td class="'+('muted' if v in ['—','未测','未跑全套'] else '')+'">'+esc(v)+'</td>' for v in r['values'])+'</tr>' for r in t['rows'])
        sections.append(f'<section id="{name}"><h2>{esc(t["title"])}</h2><p>{esc(t["subtitle"])}</p><p class="hint">横向滚动可查看全部对象。</p><div class="scroll"><table><thead>{head}</thead><tbody>{body}</tbody></table></div></section>')
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PhiAgent 多维评测记录</title><style>'+'''
*{box-sizing:border-box}body{margin:0;background:#f7f7f5;color:#252622;font:15px/1.5 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1500px;margin:auto;padding:48px 32px}h1{font-size:32px;margin:8px 0}header p,section>p{color:#70726c}header .eyebrow{letter-spacing:.16em;font-size:12px}nav{display:flex;gap:8px;margin:24px 0}button{border:1px solid #ddd;background:white;border-radius:6px;padding:10px 18px;color:#333;cursor:pointer}button.active{background:#292e29;color:white}section{background:white;border:1px solid #e6e7e2;border-radius:12px;padding:28px;margin:24px 0}h2{font-size:20px;margin:0}section>p{margin:6px 0 22px}.hint{display:none;font-size:12px;color:#8a9083}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:940px;table-layout:fixed}th,td{padding:12px 6px;text-align:center;border-bottom:1px solid #edeee9;font-variant-numeric:tabular-nums}thead th{border-bottom:2px solid #c6cbc3;font-size:17px}thead th:first-child,tbody th{width:240px;text-align:left;font-weight:500}small{display:block;color:#93968f;font-size:11px;font-weight:400;margin-top:3px}.own{background:#f0f3ee;border-top:3px solid #52674d}.primary{background:#f5f7f3;font-weight:600}.primary td{font-size:20px}td.muted{color:#babdb5}footer{color:#777c72;font-size:13px}footer li{margin:5px 0}a{color:#52674d}section[hidden]{display:none}@media(max-width:1100px){.hint{display:block}}@media(max-width:650px){main{padding:24px 12px}section{padding:16px}h1{font-size:26px}}@media print{body{background:white}main{padding:0}nav{display:none}section{break-inside:avoid}table{min-width:0}th,td{font-size:10px;padding:6px}small{font-size:8px}}
'''+ '</style><main><header><div class="eyebrow">PHIAGENT / EVALUATION RECORD</div><h1>多维评测记录</h1><p>v0.1.0 → v0.1.1 → v0.1.2 · 满分100 · 截至2026-10-03</p></header>'+''.join(sections)+'<footer><ul>'+''.join('<li>'+esc(n)+'</li>' for n in data['notes'])+'</ul><a href="../../PHIAGENT_VERSION_BENCHMARK_LEDGER.md">版本与评分长期台账</a> · <a href="matrix.json">可追溯数据</a></footer></main></html>'


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
    text(1200,95,'v0.1.0  →  v0.1.1  →  v0.1.2    ·    2026-10-03',22,'#7e857a')
    y=170
    for name in ['current']:
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
    print('Matrix generated; frozen v1.2 only; source scores preserved.')


if __name__=='__main__':main()
