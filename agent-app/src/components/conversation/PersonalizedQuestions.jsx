import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, RefreshCw } from 'lucide-react';
import { useAuth } from '../../auth';
import AuthModal from '../AuthModal';

export default function PersonalizedQuestions({ lang, onPick }) {
  const { token, profile, historyStatus } = useAuth();
  const [result, setResult] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const requestRef = useRef(0);
  const key = `${profile?.id || 'guest'}:${token || ''}:${lang}`;
  const en = lang === 'en';
  const waitingHistory = ['loading', 'saving'].includes(historyStatus);
  useEffect(() => {
    const controller = new AbortController();
    const request = ++requestRef.current;
    if (!token || !profile?.id || waitingHistory) { setResult(null); return () => controller.abort(); }
    setResult({ key, status: 'loading', suggestions: [] });
    fetch('/api/agent/home-questions', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ language: lang, refresh: refresh > 0 }), signal: controller.signal,
    }).then(async r => {
      if (!r.ok) throw new Error('home questions unavailable');
      const data = await r.json();
      if (request === requestRef.current && !controller.signal.aborted) setResult({ ...data, key });
    }).catch(() => {
      if (!controller.signal.aborted && request === requestRef.current) setResult({ key, status: 'unavailable', suggestions: [] });
    });
    return () => controller.abort();
  }, [key, refresh, waitingHistory]);
  const current = result?.key === key ? result : null;
  return <div className="cw-personal-home">
    {!token ? <p className="cw-home-hint">
      <button onClick={() => setLoginOpen(true)}>{en ? 'Sign in' : '登录'}</button>
      {en ? ' to explore questions drawn from your reading and conversations.' : '后，从你的阅读与对话中继续探索。'}
    </p> : <>
      {current?.status === 'ready' && <>
        <div className="cw-personal-heading"><span>{en ? 'From your recent explorations' : '接着你的思考'} </span>
          <button className="cw-icon-btn" onClick={() => setRefresh(n => n + 1)} title={en ? 'New questions' : '换一组问题'} aria-label={en ? 'New questions' : '换一组问题'}><RefreshCw size={14} /></button>
        </div>
        <div className="cw-personal-questions">{current.suggestions.map(item =>
          <button key={item.question} className="cw-personal-question" onClick={() => onPick(item.question)}>
            <span><span className="cw-question-basis">{item.basis}</span><span className="cw-question-text">{item.question}</span></span>
            <ArrowUpRight size={18} aria-hidden="true" />
          </button>)}</div>
      </>}
      {(!current || current.status === 'loading') && <p className="cw-home-hint" role="status">{en ? 'Connecting your recent explorations…' : '正在接续你的阅读与思考…'}</p>}
      {current?.status === 'empty' && <p className="cw-home-hint">{en ? 'Your reading, notes and conversations will shape the questions here.' : '你的阅读、笔记与对话，会成为这里下一次提问的起点。'}</p>}
      {current?.status === 'unavailable' && <p className="cw-home-hint">{en ? 'Questions are temporarily unavailable.' : '个性化提问暂时未能生成。'} <button onClick={() => setRefresh(n => n + 1)}>{en ? 'Retry' : '重试'}</button></p>}
    </>}
    {loginOpen && <AuthModal onClose={() => setLoginOpen(false)} />}
  </div>;
}
