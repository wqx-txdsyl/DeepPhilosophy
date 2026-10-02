import { useEffect, useRef, useState } from 'react';
import { Loader2, Brain, Pencil, RefreshCw, Check, ChevronDown, ArrowUpRight, Send, Sparkles } from 'lucide-react';
import { useAuth } from '../../auth';
import { memorySections, memoryDirty } from '../../data/memoryProfile';

function MemoryProse({ text, focus = '' }) {
  const sections = memorySections(text);
  const first = sections.findIndex(s=>s.title===focus);
  let last = sections.length;
  if (first>=0 && sections[first].level<3) {
    const next=sections.findIndex((s,i)=>i>first && s.level<3);
    if(next>=0)last=next;
  } else if(first>=0)last=first+1;
  const visible=focus && first>=0 ? sections.slice(first,last) : sections;
  return <div className="cw-memory-prose">{visible.map((s, i) => <section className={s.level===3?'cw-memory-subtopic':''} key={i}>
    {s.title && <h3>{s.title}</h3>}{s.paragraphs.map((p,j)=><p key={j}>{p}</p>)}
  </section>)}</div>;
}

export default function AccountMemory({ lang, onSignIn, draftState, onDraftChange, onExplore, conversationBusy = false }) {
  const { token, authFetch } = useAuth();
  const [profile, setProfile] = useState(null);
  const [items, setItems] = useState([]);
  const [draft, setDraft] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [editing, setEditing] = useState(false);
  const [focus, setFocus] = useState('');
  const [correction, setCorrection] = useState(draftState?.correction || '');
  const [question, setQuestion] = useState(draftState?.question || '');
  const [correcting, setCorrecting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [conflict, setConflict] = useState(false);
  const [remote, setRemote] = useState(null);
  const timer = useRef(null);
  const alive = useRef(true);
  const dirty = useRef(false);
  const currentProfile = useRef(null);
  const initialDraft = useRef(draftState);
  const restored = useRef(false);
  const en = lang === 'en';
  dirty.current = memoryDirty(profile, draft, enabled);
  const L = (zh, english) => en ? english : zh;
  const exploration = (profile?.metadata?.exploration || []).filter(item=>!focus || item.section===focus);
  const request = (path='',options={}) => authFetch('/api/agent/memory/profile'+path,options);
  const apply = (p, overwrite=true) => {
    if (!p || typeof p.text !== 'string') throw new Error('No memory profile');
    setProfile(p);
    currentProfile.current = p;
    if (overwrite) { setDraft(p.text); setEnabled(p.enabled); }
  };
  async function read(signal, preserve=false) {
    try {
      const d = await request('', signal ? {signal} : {});
      if (!alive.current || signal?.aborted) return;
      if (preserve && dirty.current && currentProfile.current?.revision !== d.profile.revision) {
        setRemote(d.profile); setConflict(true);
      } else {
        apply(d.profile, !preserve || !dirty.current);
        if (!restored.current && initialDraft.current?.dirty) {
          const previous = initialDraft.current;
          setDraft(previous.text);setEnabled(previous.enabled);setEditing(previous.editing);
          if(previous.revision!==d.profile.revision){setConflict(true);setRemote(d.profile);}
        }
        restored.current=true;
      }
      setItems(d.memories || []);
      if (d.profile.status === 'updating') {
        clearTimeout(timer.current); timer.current=setTimeout(()=>read(signal,true),2000);
      }
    } catch {
      if (alive.current && !signal?.aborted) setNotice(L('记忆暂未读取，草稿已保留。','Memory could not be loaded. Your draft is kept.'));
    }
  }
  useEffect(() => {
    alive.current=true;
    const controller = new AbortController();
    setProfile(null); currentProfile.current=null; setDraft(''); setItems([]); setNotice('');
    if (token) read(controller.signal);
    return () => { alive.current=false;controller.abort();clearTimeout(timer.current); };
  }, [token]);
  useEffect(() => {
    if (profile) onDraftChange?.({text:draft,enabled,editing,correction,question,revision:profile.revision,dirty:memoryDirty(profile,draft,enabled)});
  }, [draft,enabled,editing,correction,question,profile]);
  async function save(text=draft, active=enabled) {
    if (!profile || busy) return;
    setBusy(true); setNotice('');
    try {
      const d = await request('',{method:'PUT',body:JSON.stringify({text,enabled:active,expected_revision:profile.revision})});
      if (!alive.current) return;
      apply(d.profile);setEditing(false);setConflict(false);setRemote(null);
      setNotice(L('已保存','Saved'));
    } catch (error) {
      if (!alive.current) return;
      if (error.status===409) { setConflict(true); setNotice(L('记忆刚刚更新，你的草稿已保留。请查看最新版本再保存。','Memory has changed. Review the latest version before saving your draft.')); }
      else setNotice(L('保存未完成，你的草稿已保留。','Could not save. Your draft is kept.'));
    } finally { if(alive.current)setBusy(false); }
  }
  async function refresh() {
    setBusy(true); setNotice('');
    try {
      const d=await request('/refresh',{method:'POST'});
      if (!alive.current) return;
      apply(d.profile,false);
      clearTimeout(timer.current);timer.current=setTimeout(()=>read(undefined,true),2000);
    } catch { if(alive.current)setNotice(L('整理暂未启动，请稍后重试。','Could not start the update. Please retry.')); }
    finally { if(alive.current)setBusy(false); }
  }
  async function submitCorrection(event) {
    event.preventDefault();
    if (!correction.trim() || busy || !profile || conflict) return;
    setBusy(true);setCorrecting(true);setNotice('');
    try {
      const d=await request('/correct',{method:'POST',body:JSON.stringify({request:correction.trim(),expected_revision:profile.revision})});
      if(!alive.current)return;
      apply(d.profile);setCorrection('');setFocus('');setNotice(L('已按你的说明更正，后续整理会继续参考这次更正。','Corrected. Future updates will respect this correction.'));
    } catch(error) {
      if(!alive.current)return;
      if(error.status===409){setConflict(true);setNotice(L('摘要刚刚更新，更正内容已保留，请查看最新版本。','The summary changed. Your correction is kept; review the latest version.'));}
      else setNotice(L('更正未完成，原摘要和你的输入都已保留。','Could not apply the correction. The summary and your input are kept.'));
    } finally {if(alive.current){setBusy(false);setCorrecting(false);}}
  }
  function explore(text) {
    if(!text.trim() || conversationBusy || busy || !enabled)return;
    onExplore?.(text.trim());
  }
  async function reviewLatest() {
    const d=await request();
    if(!alive.current)return;
    setRemote(d.profile);setProfile(d.profile);currentProfile.current=d.profile;setConflict(false);
    setNotice(L('下方为最新保存版本。编辑框里的草稿仍然保留；保存将采用你的草稿。','Latest saved version below. Your draft is kept; saving will use your draft.'));
  }
  async function forget(id) {
    setBusy(true);
    try {
      await authFetch('/api/agent/memory/'+encodeURIComponent(id),{method:'DELETE'});
      if(alive.current){setItems(old=>old.filter(x=>x.memory_id!==id));await read(undefined,true);}
    } catch { if(alive.current)setNotice(L('删除未完成，请重试。','Could not delete. Please retry.')); }
    finally { if(alive.current)setBusy(false); }
  }
  return <section className="cw-settings-memory">
    <p className="cw-settings-desc">{L('记忆会随着对话更新，可以探索、询问或更正。','A personal summary that develops with your conversations. Explore a thread or tell DeepPhilosophy what to correct.')}</p>
    {!token ? <div className="cw-settings-empty"><Brain size={26}/><h3>{L('记忆随账号保存','Memory follows your account')}</h3><p>{L('登录后可查看和修改记忆摘要。','Sign in to view and edit your memory summary.')}</p><button className="cw-settings-button cw-settings-primary" onClick={onSignIn}>{L('登录','Sign in')}</button></div> : !profile ? <div className="cw-settings-notice" role="status"><Loader2 size={15} className="cw-spinner"/>{notice || L('正在读取记忆…','Loading memory…')}{notice && <button className="cw-settings-button" onClick={()=>read()}>{L('重试','Retry')}</button>}</div> : <>
      <div className="cw-setting-row"><div className="cw-setting-copy"><div className="cw-settings-label">{L('启用长期记忆','Use memory')}</div><p className="cw-settings-sub">{L('根据历史自动整理，在相关对话中参考。关闭后保留摘要。','Summarize history and use it when relevant. Turning this off keeps saved content but stops updates and recall.')}</p></div><button className="cw-toggle" role="switch" aria-label={L('启用长期记忆','Use memory')} aria-checked={enabled} disabled={busy||editing} onClick={()=>save(profile.text,!enabled)}><span className="cw-toggle-knob"/></button></div>
      <div className="cw-memory-document-head"><span><Brain size={17}/>{L('关于你','About you')}</span><div><button className="cw-settings-button" disabled={busy || editing || !enabled || profile.status==='updating'} onClick={refresh} title={L('重新整理历史对话','Refresh from conversations')}><RefreshCw size={14}/>{L('更新','Update')}</button><button className="cw-settings-button" disabled={busy} onClick={()=>{setEditing(!editing);setNotice('');}}><Pencil size={14}/>{editing ? L('预览','Preview') : L('编辑','Edit')}</button></div></div>
      {profile.status==='updating' && <p className="cw-settings-desc cw-memory-status" role="status"><Loader2 size={13} className="cw-spinner"/>{L('正在整理历史，不影响继续对话…','Updating from history. You can keep chatting…')}</p>}
      {profile.status==='error' && <div className="cw-settings-notice cw-settings-notice-error" role="alert">{L('自动整理暂未完成，已保存的记忆仍然保留。可点“更新”重试。','The update failed. Saved memory is kept; click Update to retry.')}</div>}
      {!editing && memorySections(draft).filter(s=>s.title).length>1 && <nav className="cw-memory-outline" aria-label={L('记忆主题','Memory topics')}><button className={!focus?'active':''} onClick={()=>setFocus('')}>{L('全部','All')}</button>{memorySections(draft).filter(s=>s.title).map(s=><button key={s.title} className={focus===s.title?'active':''} onClick={()=>setFocus(s.title)}>{s.title}</button>)}</nav>}
      {editing ? <form className="cw-settings-form" onSubmit={e=>{e.preventDefault();save();}}><label>{L('记忆正文','Memory text')}<textarea aria-label={L('记忆正文','Memory text')} className="cw-memory-editor" rows={13} value={draft} onChange={e=>setDraft(e.target.value)} placeholder={L('写下你希望深哲了解的背景、长期项目与关注的问题。小标题和段落可以自由安排。','Describe your background, ongoing projects and interests. Organize headings and paragraphs freely.')} /><small>{L('可以自由调整小标题和段落。不想保留的内容可以直接删除。','Headings are optional. Remove any paragraph you do not want; the current question takes priority.')}</small></label><div className="cw-settings-form-footer"><button className="cw-settings-button cw-settings-primary" disabled={busy||conflict||!memoryDirty(profile,draft,enabled)}><Check size={14}/>{L('保存更正','Save corrections')}</button><button type="button" className="cw-settings-button" onClick={()=>{setDraft(profile.text);setEnabled(profile.enabled);setEditing(false);setConflict(false);setNotice('');}}>{L('取消','Cancel')}</button></div></form> : draft.trim() ? <MemoryProse text={draft} focus={focus}/> : <div className="cw-memory-empty"><p>{profile.manual ? L('记忆正文已清空','Memory text is cleared') : L('还没有形成摘要','No summary yet')}</p><span>{L('可以直接编辑，或等待历史对话整理。','Edit directly or wait for a summary from history.')}</span></div>}
      {notice && <div className="cw-settings-notice" role="status">{notice}{conflict && <button className="cw-settings-button" onClick={()=>reviewLatest().catch(()=>setNotice(L('最新版本暂未读取。','Could not load the latest version.')))}>{L('查看最新版本','Review latest')}</button>}</div>}
      {remote && editing && <details className="cw-memory-details" open><summary>{L('最新保存版本','Latest saved version')}</summary><MemoryProse text={remote.text}/></details>}
      {profile.proposal && profile.proposal!==profile.text && <details className="cw-memory-details"><summary><ChevronDown size={14}/>{L('新对话带来的更新','Updates from recent conversations')}</summary><MemoryProse text={profile.proposal}/><p className="cw-settings-desc">{L('你的更正未被覆盖。采用后可继续修改。','Your corrections are preserved. You can edit this update before saving.')}</p><button className="cw-settings-button" disabled={busy||editing} onClick={()=>{setDraft(profile.proposal);setEditing(true);}}>{L('在编辑器中查看','Review in editor')}</button></details>}
      {!editing && draft.trim() && <>
        {exploration.length>0 && <section className="cw-memory-exploration"><h3><Sparkles size={15}/>{L('深入探索','Explore further')}</h3>{exploration.map(item=><button key={item.question} disabled={busy||conversationBusy||!enabled||!onExplore} onClick={()=>explore(item.question)}><ArrowUpRight size={16}/><span>{item.question}</span></button>)}</section>}
        {onExplore && <form className="cw-memory-ask" onSubmit={e=>{e.preventDefault();explore(question);}}><input aria-label={L('围绕记忆提问','Ask about your memory')} placeholder={L('围绕这些记忆继续提问…','Ask about a thread in your summary…')} value={question} onChange={e=>setQuestion(e.target.value)}/><button title={L('询问深哲','Ask DeepPhilosophy')} aria-label={L('询问深哲','Ask DeepPhilosophy')} disabled={busy||conversationBusy||!enabled||!question.trim()}><Send size={16}/></button></form>}
      </>}
      {!editing && <form className="cw-memory-correction cw-settings-form" onSubmit={submitCorrection}><label>{L('更正关于你的记忆','Correct your memory')}<textarea rows={3} aria-label={L('记忆更正请求','Memory correction request')} placeholder={L('哪些内容不准确、已经变化，或还没有体现？','What is inaccurate, has changed, or is missing?')} value={correction} onChange={e=>setCorrection(e.target.value)}/></label><button className="cw-settings-button cw-settings-primary" disabled={busy||conflict||!correction.trim()}>{correcting?<Loader2 size={14} className="cw-spinner"/>:<Check size={14}/>} {correcting?L('正在更正…','Correcting…'):L('提交更正','Apply correction')}</button></form>}
      {items.length>0 && <details className="cw-memory-details"><summary>{L('你明确要求记住的原话','Words you explicitly asked to remember')} · {items.length}</summary>{items.map(m=><div className="cw-memory-original" key={m.memory_id}><p>{m.text}</p><button className="cw-settings-button" disabled={busy} onClick={()=>forget(m.memory_id)}>{L('删除','Delete')}</button></div>)}</details>}
      <p className="cw-memory-update-meta">{enabled?L('自动整理已启用','Automatic updates enabled'):L('自动整理已关闭','Automatic updates off')}{profile.updated_at && <> · {L('更新于','Updated')} {new Date(profile.updated_at).toLocaleString(en?'en-US':'zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}</>}{profile.metadata?.conversation_count>0 && <> · {L(`来自 ${profile.metadata.conversation_count} 个对话`,`From ${profile.metadata.conversation_count} conversations`)}</>}</p>
    </>}
  </section>;
}
