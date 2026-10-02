import { useEffect, useRef, useState } from 'react';
import { Loader2, Brain, Pencil, RefreshCw, Check, ChevronDown } from 'lucide-react';
import { useAuth } from '../../auth';
import { memorySections, memoryDirty } from '../../data/memoryProfile';

function MemoryProse({ text }) {
  return <div className="cw-memory-prose">{memorySections(text).map((s, i) => <section key={i}>
    {s.title && <h3>{s.title}</h3>}{s.paragraphs.map((p,j)=><p key={j}>{p}</p>)}
  </section>)}</div>;
}

export default function AccountMemory({ lang, onSignIn, draftState, onDraftChange }) {
  const { token, authFetch } = useAuth();
  const [profile, setProfile] = useState(null);
  const [items, setItems] = useState([]);
  const [draft, setDraft] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [editing, setEditing] = useState(false);
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
    if (profile) onDraftChange?.({text:draft,enabled,editing,revision:profile.revision,dirty:memoryDirty(profile,draft,enabled)});
  }, [draft,enabled,editing,profile]);
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
    <p className="cw-settings-desc">{L('根据你的历史对话整理，按主题了解你。可以更正整段文字；手动修改会优先保留。','A themed summary from your conversations. Edit the prose at any time; your corrections take priority.')}</p>
    {!token ? <div className="cw-settings-empty"><Brain size={26}/><h3>{L('记忆随账号保存','Memory follows your account')}</h3><p>{L('登录后可查看和修改记忆摘要。','Sign in to view and edit your memory summary.')}</p><button className="cw-settings-button cw-settings-primary" onClick={onSignIn}>{L('登录','Sign in')}</button></div> : !profile ? <div className="cw-settings-notice" role="status"><Loader2 size={15} className="cw-spinner"/>{notice || L('正在读取记忆…','Loading memory…')}{notice && <button className="cw-settings-button" onClick={()=>read()}>{L('重试','Retry')}</button>}</div> : <>
      <div className="cw-setting-row"><div className="cw-setting-copy"><div className="cw-settings-label">{L('启用长期记忆','Use memory')}</div><p className="cw-settings-sub">{L('自动整理历史，并在相关问题中参考摘要。关闭后保留内容，停止整理和引用。','Summarize history and use it when relevant. Turning this off keeps saved content but stops updates and recall.')}</p></div><button className="cw-toggle" role="switch" aria-label={L('启用长期记忆','Use memory')} aria-checked={enabled} disabled={busy||editing} onClick={()=>save(profile.text,!enabled)}><span className="cw-toggle-knob"/></button></div>
      <div className="cw-memory-document-head"><span><Brain size={17}/>{L('关于你','About you')}</span><div><button className="cw-settings-button" disabled={busy || editing || !enabled || profile.status==='updating'} onClick={refresh} title={L('重新整理历史对话','Refresh from conversations')}><RefreshCw size={14}/>{L('更新','Update')}</button><button className="cw-settings-button" disabled={busy} onClick={()=>{setEditing(!editing);setNotice('');}}><Pencil size={14}/>{editing ? L('预览','Preview') : L('编辑','Edit')}</button></div></div>
      {profile.status==='updating' && <p className="cw-settings-desc cw-memory-status" role="status"><Loader2 size={13} className="cw-spinner"/>{L('正在整理历史，不影响继续对话…','Updating from history. You can keep chatting…')}</p>}
      {profile.status==='error' && <div className="cw-settings-notice cw-settings-notice-error" role="alert">{L('自动整理暂未完成，已保存的记忆仍然保留。可点“更新”重试。','The update failed. Saved memory is kept; click Update to retry.')}</div>}
      {editing ? <form className="cw-settings-form" onSubmit={e=>{e.preventDefault();save();}}><label>{L('记忆正文','Memory text')}<textarea aria-label={L('记忆正文','Memory text')} className="cw-memory-editor" rows={13} value={draft} onChange={e=>setDraft(e.target.value)} placeholder={L('## 个人背景\n你希望深哲了解的背景。\n\n## 阅读与研究\n正在读的书、长期研究或项目。\n\n## 长期关注\n持续探索的问题。\n\n## 交流偏好\n对表达方式的偏好。','## Background\n\n## Reading and research\n\n## Ongoing interests\n\n## Communication preferences')} /><small>{L('小标题可自由修改。不想保留的段落可以删掉；偏好仍以当前问题为先。','Headings are optional. Remove any paragraph you do not want; the current question takes priority.')}</small></label><div className="cw-settings-form-footer"><button className="cw-settings-button cw-settings-primary" disabled={busy||conflict||!memoryDirty(profile,draft,enabled)}><Check size={14}/>{L('保存更正','Save corrections')}</button><button type="button" className="cw-settings-button" onClick={()=>{setDraft(profile.text);setEnabled(profile.enabled);setEditing(false);setConflict(false);setNotice('');}}>{L('取消','Cancel')}</button></div></form> : draft.trim() ? <MemoryProse text={draft}/> : <div className="cw-memory-empty"><p>{profile.manual ? L('记忆正文已清空','Memory text is cleared') : L('还没有形成摘要','No summary yet')}</p><span>{L('可以直接编辑，或等待历史对话整理。','Edit directly or wait for a summary from history.')}</span></div>}
      {notice && <div className="cw-settings-notice" role="status">{notice}{conflict && <button className="cw-settings-button" onClick={()=>reviewLatest().catch(()=>setNotice(L('最新版本暂未读取。','Could not load the latest version.')))}>{L('查看最新版本','Review latest')}</button>}</div>}
      {remote && editing && <details className="cw-memory-details" open><summary>{L('最新保存版本','Latest saved version')}</summary><MemoryProse text={remote.text}/></details>}
      {profile.proposal && profile.proposal!==profile.text && <details className="cw-memory-details"><summary><ChevronDown size={14}/>{L('新对话带来的更新','Updates from recent conversations')}</summary><MemoryProse text={profile.proposal}/><p className="cw-settings-desc">{L('你的更正未被覆盖。采用后可继续修改。','Your corrections are preserved. You can edit this update before saving.')}</p><button className="cw-settings-button" disabled={busy||editing} onClick={()=>{setDraft(profile.proposal);setEditing(true);}}>{L('在编辑器中查看','Review in editor')}</button></details>}
      {items.length>0 && <details className="cw-memory-details"><summary>{L('你明确要求记住的原话','Words you explicitly asked to remember')} · {items.length}</summary>{items.map(m=><div className="cw-memory-original" key={m.memory_id}><p>{m.text}</p><button className="cw-settings-button" disabled={busy} onClick={()=>forget(m.memory_id)}>{L('删除','Delete')}</button></div>)}</details>}
      <p className="cw-settings-desc cw-memory-footnote">{L('摘要是可更正的背景，不是你的固定立场。不会把一个问题当成你赞成的观点。回答规则仍在“个性化”中单独设置。','This summary is editable context, not a fixed position. Asking a question does not imply agreement. Response instructions are separate under Personalization.')}</p>
    </>}
  </section>;
}
