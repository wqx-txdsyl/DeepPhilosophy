import { useEffect, useState } from 'react';
import { Loader2, Plus, Brain } from 'lucide-react';
import { useAuth } from '../../auth';

export default function AccountMemory({ lang, onSignIn }) {
  const { token, authFetch } = useAuth();
  const [items, setItems] = useState([]);
  const [text, setText] = useState('');
  const [status, setStatus] = useState('loading');
  const [forgetting, setForgetting] = useState(null);
  const en = lang === 'en';
  const request = (path = '', options = {}) => authFetch(`/api/agent/memory${path}`, options);
  useEffect(() => {
    const controller = new AbortController();
    setItems([]);
    if (!token) { setStatus('guest'); return; }
    request('', { signal: controller.signal }).then(data => {
      if (controller.signal.aborted) return;
      if (!Array.isArray(data.memories)) throw new Error('No memory response');
      setItems(data.memories); setStatus('ready');
    }).catch(() => { if (!controller.signal.aborted) setStatus('error'); });
    return () => controller.abort();
  }, [token]);
  async function reload() {
    setStatus('loading');
    try { const d = await request(); if (!Array.isArray(d.memories)) throw new Error('No memory response'); setItems(d.memories); setStatus('ready'); }
    catch { setStatus('error'); }
  }
  async function add(event) {
    event.preventDefault();
    if (!text.trim() || status === 'saving') return;
    setStatus('saving');
    try {
      const d = await request('', { method:'POST', body:JSON.stringify({text:text.trim()}) });
      if (!d.memory?.memory_id) throw new Error('No saved memory');
      setItems(old => [...old.filter(m=>m.memory_id!==d.memory.memory_id),d.memory]); setText(''); setStatus('ready');
    } catch { setStatus('error'); }
  }
  async function remove(id) {
    if (status === 'saving') return;
    setStatus('saving');
    try { const d = await request(`/${encodeURIComponent(id)}`,{method:'DELETE'}); if (!d.deleted) throw new Error('Not deleted'); setItems(old=>old.filter(m=>m.memory_id!==id)); setForgetting(null); setStatus('ready'); }
    catch { setStatus('error'); }
  }
  return <section className="cw-settings-memory">
    <p className="cw-settings-desc">{en ? 'Manage the facts you explicitly ask DeepPhilosophy to remember. Past questions remain context, not assumed beliefs.' : '管理你明确希望深哲记住的信息。历史提问只作背景，不会被当成你的立场。'}</p>
    {!token ? <div className="cw-settings-empty"><Brain size={26} aria-hidden="true" /><h3>{en ? 'Memory follows your account' : '记忆随账号保存'}</h3><p>{en ? 'Sign in to add and manage memory.' : '登录后可添加、查看和删除。'}</p>{onSignIn && <button className="cw-settings-button cw-settings-primary" onClick={onSignIn}>{en ? 'Sign in' : '登录'}</button>}</div> : <>
      {status === 'loading' && <p className="cw-settings-desc" role="status"><Loader2 size={14} className="cw-spinner" /> {en ? 'Loading memory…' : '正在读取记忆…'}</p>}
      {items.length > 0 && <ul className="cw-memory-list">{items.map(m => <li key={m.memory_id}><p>{m.text}</p>{forgetting === m.memory_id ? <div className="cw-memory-confirm"><span>{en ? 'Forget this memory?' : '删除这条记忆？'}</span><button className="cw-settings-button" onClick={()=>setForgetting(null)}>{en ? 'Cancel' : '取消'}</button><button className="cw-settings-button cw-settings-danger" disabled={status==='saving'} onClick={()=>remove(m.memory_id)}>{en ? 'Delete' : '删除'}</button></div> : <button className="cw-settings-button" disabled={status==='saving'} onClick={()=>setForgetting(m.memory_id)}>{en ? 'Forget' : '删除'}</button>}</li>)}</ul>}
      {!items.length && status === 'ready' && <div className="cw-memory-empty"><Brain size={22} aria-hidden="true" /><p>{en ? 'No saved memories yet' : '还没有保存的记忆'}</p><span>{en ? 'Add one below, or say “Please remember…” in a conversation.' : '在下方添加，或在对话中说“请记住……” 。'}</span></div>}
      <form onSubmit={add} className="cw-settings-form cw-memory-form"><label>{en ? 'Add a memory' : '添加记忆'}<textarea rows={3} value={text} onChange={e=>setText(e.target.value)} placeholder={en ? 'For example: I am reading Kant’s Critique of Pure Reason.' : '例如：我正在阅读康德的《纯粹理性批判》。'} aria-label={en ? 'Memory content' : '记忆内容'} /></label><button className="cw-settings-button cw-settings-primary" disabled={!text.trim() || ['loading','saving'].includes(status)}><Plus size={14} />{status==='saving' ? (en ? 'Saving…' : '保存中…') : (en ? 'Save memory' : '保存记忆')}</button></form>
      {status==='error' && <div className="cw-settings-notice cw-settings-notice-error" role="alert"><span>{en ? 'Could not load or save memory. Your draft is kept.' : '记忆读取或保存未完成，输入内容已保留。'}</span><button className="cw-settings-button" onClick={reload}>{en ? 'Retry' : '重试'}</button></div>}
    </>}
  </section>;
}
