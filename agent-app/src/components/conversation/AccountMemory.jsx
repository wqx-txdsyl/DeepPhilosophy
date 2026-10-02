import { useEffect, useState } from 'react';
import { useAuth } from '../../auth';

export default function AccountMemory({ lang }) {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [text, setText] = useState('');
  const [status, setStatus] = useState('loading');
  const en = lang === 'en';
  async function request(path = '', options = {}) {
    const r = await fetch(`/api/agent/memory${path}`, { ...options, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` } });
    if (!r.ok) throw new Error('memory unavailable');
    return r.json();
  }
  useEffect(() => {
    let active = true;
    setItems([]);
    if (!token) { setStatus('guest'); return; }
    request().then(d => { if (active) { setItems(d.memories || []); setStatus('ready'); } })
      .catch(() => { if (active) setStatus('error'); });
    return () => { active = false; };
  }, [token]);
  async function add(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setStatus('saving');
    try {
      const d = await request('', { method: 'POST', body: JSON.stringify({ text: text.trim() }) });
      setItems(old => [...old.filter(m => m.memory_id !== d.memory.memory_id), d.memory]); setText(''); setStatus('ready');
    } catch { setStatus('error'); }
  }
  async function remove(id) {
    setStatus('saving');
    try { await request(`/${encodeURIComponent(id)}`, { method: 'DELETE' }); setItems(old => old.filter(m => m.memory_id !== id)); setStatus('ready'); }
    catch { setStatus('error'); }
  }
  return <div className="cw-settings-sec">
    <h3 className="cw-settings-h">{en ? 'Account memory' : '长期记忆'}</h3>
    <p className="cw-settings-desc">{en ? 'Explicit memories follow your account into new conversations. Past questions are context, not assumed beliefs.' : '明确保存的记忆会用于新的对话。历史提问只作背景，不会被当成你的立场。'}</p>
    {!token ? <p className="cw-settings-desc">{en ? 'Sign in to save memory.' : '登录后可保存和管理。'}</p> : <>
      <ul className="cw-memory-list">{items.map(m => <li key={m.memory_id}><span>{m.text}</span><button className="cw-danger-btn" disabled={status === 'saving'} onClick={() => remove(m.memory_id)}>{en ? 'Forget' : '忘记'}</button></li>)}</ul>
      {!items.length && status === 'ready' && <p className="cw-settings-desc">{en ? 'No explicit memories yet.' : '还没有明确保存的记忆。你也可以在对话中说“请记住……” 。'}</p>}
      <form onSubmit={add} className="cw-memory-form"><textarea value={text} onChange={e => setText(e.target.value)} placeholder={en ? 'What should I remember?' : '希望深哲记住什么？'} aria-label={en ? 'Memory content' : '记忆内容'} /><button className="cw-danger-btn" disabled={!text.trim() || status === 'saving'}>{en ? 'Save memory' : '保存记忆'}</button></form>
      {status === 'error' && <p role="alert" className="cw-settings-desc">{en ? 'Could not save or load memory. Please retry.' : '记忆读取或保存失败，请重试。'}</p>}
    </>}
  </div>;
}
