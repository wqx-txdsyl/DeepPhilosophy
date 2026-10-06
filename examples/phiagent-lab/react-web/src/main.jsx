import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { readEvents } from '../../web/sse.mjs';
import '../../web/style.css';

function App() {
  const [question, setQuestion] = useState('自由与责任有什么关系？');
  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('React 基础客户端；刷新后新建会话。完整持久工作区是课程作业。');
  const conversation = useRef(crypto.randomUUID());
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);

  async function send(event) {
    event.preventDefault();
    if (request.current || !question.trim()) return;
    const id = crypto.randomUUID();
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setSources([]);
    setMessages(old => [...old, {id: crypto.randomUUID(), role: 'user', content: question},
      {id, role: 'assistant', content: ''}]);
    function change(update) {
      if (request.current !== controller) return;
      setMessages(old => old.map(m => m.id === id ? {...m, content: update(m.content)} : m));
    }
    let completed = false;
    try {
      const response = await fetch('/api/chat', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({conversation_id: conversation.current, message: question}),
        signal: controller.signal,
      });
      await readEvents(response, data => {
        if (request.current !== controller) return;
        if (data.type === 'token') change(text => text + data.text);
        if (data.type === 'status') setStatus(data.text);
        if (data.type === 'tool') setStatus(`调用：${data.name}`);
        if (data.type === 'source') setSources(old => [...old.filter(s => s.id !== data.source.id), data.source]);
        if (data.type === 'error') throw new Error(data.message);
        if (data.type === 'done') { completed = true; change(() => data.text); setStatus('已完成并保存'); }
      });
      if (!completed) throw new Error('没有收到完成事件');
    } catch (error) {
      change(() => '[本轮未确认完成]');
      setStatus(error.name === 'AbortError' ? '已停止' : error.message);
    } finally {
      if (request.current === controller) { request.current = null; setBusy(false); }
    }
  }

  return <main><header><p>第 09 章 · React 状态驱动</p><h1>PhiAgent Lab</h1></header>
    <button disabled={busy} onClick={() => {conversation.current = crypto.randomUUID(); setMessages([]); setSources([]);}}>新会话</button>
    <section aria-live="polite">{messages.map(m => <article key={m.id} data-role={m.role}>{m.content}</article>)}</section>
    <p role="status">{status}</p><form onSubmit={send}><label htmlFor="question">你的问题</label>
      <textarea id="question" value={question} maxLength={2000} onChange={e => setQuestion(e.target.value)} />
      <div><button disabled={busy || !question.trim()}>发送</button><button type="button" disabled={!busy} onClick={() => request.current?.abort()}>停止</button></div>
    </form><aside><h2>已读取材料</h2>{sources.map(s => <details key={s.id}><summary>{s.title} [{s.id}]</summary><p>{s.source}：{s.text}</p></details>)}</aside>
  </main>;
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>);
