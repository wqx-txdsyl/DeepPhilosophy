import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useBlocker, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, FileText, BookOpen, MessageSquare, Footprints, ListChecks, ArrowUpRight, Download, Trash2 } from 'lucide-react';
import { useAuth } from '../auth';
import AuthModal from '../components/AuthModal';
import AreaNav from '../components/AreaNav';
import { renderMarkdown } from '../components/conversation/markdown';
import { projectApi, blankProject, objectId, downloadProject } from '../data/projectApi';
import '../project.css';

const labels = { queued:'等待研究', running:'正在研究', completed:'待采纳', adopted:'已采纳', failed:'未完成', canceled:'已停止', interrupted:'已中断', stale:'需重新研究' };
const isActive = r => ['queued','running'].includes(r.status);
const glyphs = {document:FileText,debate:MessageSquare,action:Footprints};

export default function ProjectPage() {
  const { token, profile, accountReady, authError, retryAccount } = useAuth();
  const [login,setLogin] = useState(false);
  const { pathname } = useLocation();
  const api = useMemo(()=>projectApi(token),[token]);
  const pieces = pathname.slice('/projects'.length).split('/').filter(Boolean);
  return <div className="pw-shell">
    <header className="pw-top"><Link className="pw-logo" to="/projects">PHIAGENT <span>PROJECT</span></Link><AreaNav /></header>
    {!accountReady ? <div className="pw-empty"><p>{authError ? '账号暂未连接。' : '正在连接账号…'}</p>{authError && <button onClick={retryAccount}>重试</button>}</div>
      : !token ? <div className="pw-empty"><div className="pw-eyebrow">PROJECT</div><h1>让一个问题，成为一项研究。</h1><p>为项目保存材料、文稿、争点与行动记录。</p><button className="pw-primary" onClick={()=>setLogin(true)}>登录并创建项目</button><p className="pw-caption">Chat 与 Project 分别保存，内容与记忆不互相带入。</p></div>
      : pieces[0] === 'new' ? <NewProject key={profile?.id} api={api} />
        : pieces[0] ? <Workspace key={`${profile?.id}:${pieces[0]}`} api={api} pid={pieces[0]} section={pieces[1] || 'brief'} oid={pieces[2]} />
          : <Projects key={profile?.id} api={api} />}
    {login && <AuthModal onClose={()=>setLogin(false)} />}
  </div>;
}

function Projects({api}) {
  const [items,setItems] = useState(null), [error,setError] = useState(''), [attempt,setAttempt] = useState(0);
  const input = useRef(null), navigate=useNavigate(), alive=useRef(true);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  useEffect(()=>{let live=true; api().then(d=>{if(live){setItems(d.projects);setError('');}}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[api,attempt]);
  async function importFile(event) {
    const file=event.target.files[0]; event.target.value=''; if(!file)return;
    try {
      if(file.size>2_000_000) throw new Error('项目文件超过 2MB。');
      const bundle=JSON.parse(await file.text());
      if(bundle.format!=='phiagent-project-v1' || !bundle.data) throw new Error('请选择 PhiAgent 导出的项目 JSON。');
      const {project}=await api('',{method:'POST',body:bundle.data});if(alive.current)navigate(`/projects/${project.id}/brief`);
    } catch(e){if(alive.current)setError(e.message);}
  }
  return <main className="pw-home">
    <div className="pw-home-heading"><div><div className="pw-eyebrow">你的研究空间</div><h1>项目</h1><p>问题可以持续追问，成果可以逐次修订。</p></div><Link className="pw-primary" to="/projects/new"><Plus size={16}/>新建项目</Link></div>
    <div className="pw-home-tools"><button onClick={()=>input.current.click()}><Download size={15}/>导入项目</button><input ref={input} type="file" accept="application/json,.json" hidden onChange={importFile}/><span>资料、任务与成果独立于 Chat。</span></div>
    {error && <div className="pw-error" role="alert">{error} <button onClick={()=>setAttempt(n=>n+1)}>重试</button></div>}
    {items===null&&!error ? <p>正在加载项目…</p> : items?.length ? <div className="pw-project-list">{items.map(p=><Link key={p.id} to={`/projects/${p.id}/brief`}><div><h2>{p.title}</h2><p>{p.question}</p><small>更新于 {new Date(p.updated_at).toLocaleString('zh-CN')}</small></div><ArrowUpRight size={20}/></Link>)}</div>
      : items&&<div className="pw-first"><BookOpen size={28} strokeWidth={1}/><h2>从一个真正想弄清的问题开始</h2><p>新建项目后，加入材料，开始写作或研究。</p><Link to="/projects/new">创建第一个项目 →</Link></div>}
  </main>;
}

function NewProject({api}) {
  const [title,setTitle]=useState(''),[question,setQuestion]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const navigate=useNavigate(), live=useRef(true);
  useEffect(()=>{live.current=true;return()=>{live.current=false;};},[]);
  async function create(e){e.preventDefault();if(busy)return;setBusy(true);try{const {project}=await api('',{method:'POST',body:blankProject(title,question)});if(live.current)navigate(`/projects/${project.id}/brief`);}catch(e){if(live.current)setError(e.message);}finally{if(live.current)setBusy(false);}}
  return <main className="pw-new"><Link className="pw-back" to="/projects"><ArrowLeft size={16}/>全部项目</Link><div className="pw-eyebrow">开始一项研究</div><h1>新建项目</h1><form onSubmit={create}>
    <label>项目名称<input autoFocus required maxLength={200} value={title} onChange={e=>setTitle(e.target.value)} placeholder="例如：儒家思想的当代价值"/></label>
    <label>你想弄清什么？<textarea required maxLength={3000} rows={5} value={question} onChange={e=>setQuestion(e.target.value)} placeholder="写下问题，暂时不必有结论。"/></label>
    <p className="pw-caption">创建独立的项目空间。之后可以添加资料、撰写文稿、整理异议和记录行动。</p>
    {error&&<p role="alert" className="pw-error">{error}</p>}<button className="pw-primary" disabled={busy||!title.trim()||!question.trim()}>{busy?'正在创建…':'创建项目'}</button>
  </form></main>;
}

function Workspace({api,pid,section,oid}) {
  const [record,setRecord]=useState(null),[data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[runs,setRuns]=useState([]),[instruction,setInstruction]=useState(''),[preview,setPreview]=useState(false),[attempt,setAttempt]=useState(0);
  const [source,setSource]=useState({title:'',url:'',locator:'',text:''});
  const alive=useRef(true), saving=useRef(false), navigate=useNavigate();
  const dirty=record&&data&&JSON.stringify(record.data)!==JSON.stringify(data);
  const blocker=useBlocker(({nextLocation})=>!!dirty&&!nextLocation.pathname.startsWith(`/projects/${pid}/`));
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  useEffect(()=>{let live=true;api(`/${pid}`).then(d=>{if(live){setRecord(d.project);setData(d.project.data);setError('');}}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[api,pid,attempt]);
  useEffect(()=>{
    let live=true,timer;
    const poll=async()=>{try{const d=await api(`/${pid}/runs`);if(live){setRuns(d.runs);timer=setTimeout(poll,d.runs.some(isActive)?1500:8000);}}catch(e){if(live){setError(e.message);timer=setTimeout(poll,8000);}}};
    poll();return()=>{live=false;clearTimeout(timer);};
  },[api,pid]);
  useEffect(()=>{const warn=e=>{if(dirty){e.preventDefault();e.returnValue='';}};window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn);},[dirty]);
  // Internal navigation retains this project's unsaved edits; leaving the project is explicit.
  useEffect(()=>{if(blocker.state==='blocked'){if(window.confirm('当前修改尚未保存，仍要离开？'))blocker.proceed();else blocker.reset();}},[blocker]);
  const obj=data?.objects.find(o=>o.id===oid);
  const {hash}=useLocation();
  useEffect(()=>{if(section==='sources'&&data&&hash){document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView({block:'center'});}},[section,hash,!!data]);
  async function refreshRuns(){const d=await api(`/${pid}/runs`);if(alive.current)setRuns(d.runs);}
  async function save(next=data){
    if(saving.current)return null;saving.current=true;setBusy(true);setError('');
    try{const d=await api(`/${pid}`,{method:'PUT',body:{data:next,expected_revision:record.revision}});if(alive.current){setRecord(d.project);setData(current=>JSON.stringify(current)===JSON.stringify(next)?d.project.data:current);}return d.project;}
    catch(e){if(alive.current)setError(e.message);return null;}finally{saving.current=false;if(alive.current)setBusy(false);}
  }
  const patch=values=>setData(d=>({...d,...values}));
  function editObject(content){patch({objects:data.objects.map(o=>o.id===oid?{...o,content}:o)});}
  async function start(e){
    e.preventDefault();if(busy||!instruction.trim()||!obj)return;
    let p=record;if(dirty){p=await save();if(!p)return;}
    setBusy(true);setError('');try{await api(`/${pid}/runs`,{method:'POST',body:{object_id:obj.id,instruction,expected_revision:p.revision}});if(alive.current){setInstruction('');await refreshRuns();}}catch(e){if(alive.current)setError(e.message);}finally{if(alive.current)setBusy(false);}
  }
  async function adopt(r){if(dirty){setError('请先保存修改。保存后若版本不同，需重新发起研究。');return;}setBusy(true);try{const d=await api(`/${pid}/runs/${r.id}/adopt`,{method:'POST',body:{expected_revision:record.revision}});if(alive.current){setRecord(d.project);setData(d.project.data);await refreshRuns();}}catch(e){if(alive.current)setError(e.message);}finally{if(alive.current)setBusy(false);}}
  async function stop(r){try{await api(`/${pid}/runs/${r.id}/stop`,{method:'POST'});await refreshRuns();}catch(e){setError(e.message);}}
  async function remove(){if(!window.confirm('删除这个项目及其资料和任务？此操作无法撤销。'))return;try{await api(`/${pid}`,{method:'DELETE'});navigate('/projects');}catch(e){setError(e.message);}}
  function exportBundle(){downloadProject({format:'phiagent-project-v1',data},`${data.title}.json`);}
  const nav=[['brief','项目简报',BookOpen],['sources','资料',BookOpen],...(data?.objects||[]).map(o=>[`objects/${o.id}`,o.title,glyphs[o.kind]]),['runs','任务记录',ListChecks]];
  const invalid=!['brief','sources','runs'].includes(section)&&!(section==='objects'&&obj);
  return <div className="pw-layout">
    <aside className="pw-sidebar"><Link className="pw-back" to="/projects"><ArrowLeft size={15}/>全部项目</Link><h2>{data?.title||'项目'}</h2><nav aria-label="项目导航">{nav.map(([path,title,Icon])=><Link key={path} className={`${section}${oid?`/${oid}`:''}`===path?'selected':''} to={`/projects/${pid}/${path}`}><Icon size={16}/>{title}</Link>)}</nav><div className="pw-sidebar-bottom"><button disabled={!data} onClick={exportBundle}><Download size={15}/>导出项目</button><button disabled={!data||busy} onClick={remove}><Trash2 size={15}/>删除项目</button></div></aside>
    <main className="pw-work">
      {error&&<div className="pw-error" role="alert">{error} <button onClick={()=>{if(!dirty||window.confirm('放弃尚未保存的修改并重新加载？'))setAttempt(a=>a+1);}}>重新加载</button></div>}
      {!data ? !error&&<p>正在加载项目…</p> : <>
        <div className="pw-work-top"><span>{data.title}</span><div><span aria-live="polite">{busy?'正在处理…':dirty?'有未保存修改':`已保存 · v${record.revision}`}</span><button className="pw-primary" disabled={!dirty||busy} onClick={()=>save()}>保存</button></div></div>
        {section==='brief'&&<article className="pw-page"><div className="pw-eyebrow">项目简报</div><h1>我们在研究什么</h1><label>项目名称<input disabled={busy} maxLength={200} value={data.title} onChange={e=>patch({title:e.target.value})}/></label><label>核心问题<textarea disabled={busy} rows={3} maxLength={3000} value={data.question} onChange={e=>patch({question:e.target.value})}/></label><label>范围、工作假设与下一步<textarea disabled={busy} rows={8} maxLength={10000} value={data.brief} onChange={e=>patch({brief:e.target.value})} placeholder="先界定问题，再选择材料。这里可以记录尚未确定的判断。"/></label><div className="pw-next"><Link to={`/projects/${pid}/sources`}>加入研究资料 →</Link><Link to={`/projects/${pid}/objects/${data.objects[0].id}`}>开始写作与研究 →</Link></div></article>}
        {section==='sources'&&<article className="pw-page"><div className="pw-eyebrow">研究材料 · {data.sources.length} 份</div><h1>让判断有出处</h1><p className="pw-caption">链接用于定位。研究任务只读取你填入的资料文本，不会自动打开链接或声称读过全文。</p><form className="pw-source-form" onSubmit={async e=>{e.preventDefault();const next={...data,sources:[...data.sources,{...source,id:`S-${objectId().slice(0,8)}`} ]};const p=await save(next);if(p){setData(p.data);setSource({title:'',url:'',locator:'',text:''});await refreshRuns();}}}>
          <label>资料标题<input required maxLength={500} disabled={busy} value={source.title} onChange={e=>setSource({...source,title:e.target.value})}/></label><div className="pw-two"><label>来源链接<input type="url" maxLength={2000} disabled={busy} value={source.url} onChange={e=>setSource({...source,url:e.target.value})} placeholder="https://…"/></label><label>篇章 / 页码<input disabled={busy} maxLength={1000} value={source.locator} onChange={e=>setSource({...source,locator:e.target.value})}/></label></div><label>原文摘录或研究笔记<textarea rows={4} maxLength={25000} disabled={busy} value={source.text} onChange={e=>setSource({...source,text:e.target.value})}/></label><button className="pw-primary" disabled={busy||!source.title.trim()||data.sources.length>=50}><Plus size={15}/>添加并保存资料</button></form>
          <div className="pw-sources">{data.sources.map(s=><section id={s.id} key={s.id}><small>{s.id} · {s.locator||'未标定位'}</small><h2>{s.title}</h2>{s.url&&<a href={s.url} target="_blank" rel="noreferrer">查看来源 ↗</a>}<p className="pw-source-text">{s.text||'尚未填写资料文本，研究任务无法据此引用原文。'}</p><details><summary>编辑资料</summary>{[['title','标题'],['url','来源链接'],['locator','篇章 / 页码'],['text','资料文本']].map(([key,label])=><label key={key}>{label}{key==='text'?<textarea disabled={busy} value={s[key]} maxLength={25000} onChange={e=>patch({sources:data.sources.map(v=>v.id===s.id?{...v,[key]:e.target.value}:v)})}/>:<input disabled={busy} value={s[key]} maxLength={key==='url'?2000:500} onChange={e=>patch({sources:data.sources.map(v=>v.id===s.id?{...v,[key]:e.target.value}:v)})}/>}</label>)}<p className="pw-caption">修改后点击顶部保存；旧研究建议会撤回。</p></details><button disabled={busy} onClick={async()=>{if(window.confirm('移除资料后，旧研究建议将撤回。继续？')){const p=await save({...data,sources:data.sources.filter(v=>v.id!==s.id)});if(p){setData(p.data);await refreshRuns();}}}}>移除资料</button></section>)}</div>
        </article>}
        {section==='objects'&&obj&&<article className="pw-page"><div className="pw-object-heading"><div><div className="pw-eyebrow">{obj.kind==='document'?'研究与写作':obj.kind==='debate'?'研讨':'实践'}</div><h1>{obj.title}</h1></div><button onClick={()=>setPreview(v=>!v)}>{preview?'编辑':'预览'}</button></div>
          {obj.kind==='action'&&<p className="pw-caption">方案、模拟预测与真实观察请分别记录；没有实际反馈时保留“尚未开展”。</p>}
          {preview?<div className="pw-prose">{renderMarkdown(obj.content||'尚未撰写。')}<ProjectReferences text={obj.content} sources={data.sources} pid={pid}/></div>:<textarea className="pw-editor" aria-label={obj.title} disabled={busy} maxLength={80000} value={obj.content} onChange={e=>editObject(e.target.value)} placeholder={obj.kind==='document'?'写下论证，或在下方给深哲一项具体研究任务。':obj.kind==='debate'?'记录主张、最强反驳、回应与仍未解决的分歧。':'写下行动目的、参与条件、步骤、检验方法，以及真实反馈。'}/>}
          <details className="pw-versions"><summary>历史版本（{obj.versions.length}）</summary>{obj.versions.map((v,i)=><div key={i}><small>{new Date(v.at).toLocaleString('zh-CN')}</small><pre>{v.content||'空白稿'}</pre><button disabled={busy} onClick={()=>editObject(v.content)}>恢复到编辑区</button></div>)}</details>
          <form className="pw-task-form" onSubmit={start}><label>请深哲处理这个工作对象<textarea rows={3} maxLength={3000} value={instruction} disabled={busy} onChange={e=>setInstruction(e.target.value)} placeholder="例如：依据现有资料写初稿，并指出证据不足和最强反驳。"/></label><div><span>{data.sources.length} 份项目资料 · 不读取 Chat 记忆</span><button className="pw-primary" disabled={busy||runs.some(isActive)||!instruction.trim()}>开始研究</button></div></form>
          <RunList runs={runs.filter(r=>r.object_id===oid)} data={data} record={record} dirty={dirty} busy={busy} adopt={adopt} stop={stop} pid={pid}/>
          <button onClick={()=>downloadProject(obj.content,`${obj.title}.md`,'text/markdown')}>导出当前文稿</button>
        </article>}
        {section==='runs'&&<article className="pw-page"><div className="pw-eyebrow">项目任务</div><h1>工作留下的痕迹</h1><p className="pw-caption">每项任务绑定发起时的项目版本和工作对象。研究结果须采纳后才写入文稿。</p><RunList runs={runs} data={data} record={record} dirty={dirty} busy={busy} adopt={adopt} stop={stop} pid={pid}/></article>}
        {invalid&&<div className="pw-empty"><h1>没有这个工作对象</h1><Link to={`/projects/${pid}/brief`}>返回项目简报</Link></div>}
      </>}
    </main>
  </div>;
}

function RunList({runs,data,record,dirty,busy,adopt,stop,pid}) {
  return <div className="pw-runs">{!runs.length?<p className="pw-caption">尚未发起研究任务。</p>:runs.map(r=><section className="pw-run" key={r.id}><div className="pw-run-head"><strong>{labels[r.status]||r.status}</strong><Link to={`/projects/${pid}/objects/${r.object_id}`}>{data.objects.find(o=>o.id===r.object_id)?.title||'原工作对象'}</Link><small>基于 v{r.base_revision}</small></div><p>{r.instruction}</p><small>{new Date(r.created_at).toLocaleString('zh-CN')}</small>{r.error&&<p role="status">{r.error}</p>}{isActive(r)&&<button onClick={()=>stop(r)}>停止研究</button>}
    {r.result&&<><details open={r.status==='completed'}><summary>查看研究成果</summary><div className="pw-prose">{renderMarkdown(r.result)}<ProjectReferences text={r.result} sources={data.sources} pid={pid}/></div></details>{r.status==='completed'&&<><button className="pw-primary" disabled={busy||dirty||r.base_revision!==record.revision} onClick={()=>adopt(r)}>采纳到工作对象</button>{r.base_revision!==record.revision&&<p className="pw-caption">项目版本已变化，请重新研究。此结果仍可查阅。</p>}</>}</>}
  </section>)}</div>;
}

function ProjectReferences({text,sources,pid}) {
  const used=sources.filter(s=>text.includes(`[${s.id}]`));
  const unknown=[...text.matchAll(/\[(S[\w-]*)\]/g)].map(m=>m[1]).filter(id=>!sources.some(s=>s.id===id));
  return <div className="pw-references">{used.length>0&&<><small>本稿关联资料（编号用于定位，不代表论证已核实）</small>{used.map(s=><Link key={s.id} to={`/projects/${pid}/sources#${encodeURIComponent(s.id)}`}>[{s.id}] {s.title} ↗</Link>)}</>}{unknown.length>0&&<p className="pw-caption">以下资料编号无法在本项目核对：{[...new Set(unknown)].join('、')}</p>}</div>;
}
