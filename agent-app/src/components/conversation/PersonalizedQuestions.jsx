import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, RefreshCw } from 'lucide-react';
import { useAuth } from '../../auth';
import AuthModal from '../AuthModal';

export default function PersonalizedQuestions({ lang, onPick }) {
  const { token, profile, historyStatus, retryHistory } = useAuth();
  const [result, setResult] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [request, setRequest] = useState({ version:0, force:false });
  const requestRef = useRef(0);
  const key = `${profile?.id || 'guest'}:${token || ''}:${lang}`;
  const en = lang === 'en';
  const waitingHistory = ['loading', 'saving', 'offline', 'cache-error'].includes(historyStatus);
  useEffect(() => {
    const reload = () => setRequest(value => ({version:value.version + 1, force:false}));
    const visible = () => { if (document.visibilityState === 'visible') reload(); };
    window.addEventListener('phiagent-history-restored', reload);
    window.addEventListener('focus', reload);
    document.addEventListener('visibilitychange', visible);
    return () => {
      window.removeEventListener('phiagent-history-restored', reload);
      window.removeEventListener('focus', reload);
      document.removeEventListener('visibilitychange', visible);
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const id = ++requestRef.current;
    if (!token || !profile?.id || waitingHistory) { setResult(null); return () => controller.abort(); }
    setResult({ key, revision:request.version, status: 'loading', suggestions: [] });
    fetch('/api/agent/home-questions', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ language: lang, refresh: request.force }), signal: controller.signal, cache:'no-store',
    }).then(async r => {
      if (!r.ok) throw new Error('home questions unavailable');
      const data = await r.json();
      if (id === requestRef.current && !controller.signal.aborted) {
        if (data.status === 'stale') { setResult(null); setRequest(value=>({version:value.version + 1, force:false})); }
        else setResult({ ...data, key, revision:request.version });
      }
    }).catch(() => {
      if (!controller.signal.aborted && id === requestRef.current) setResult({ key, revision:request.version, status: 'unavailable', suggestions: [] });
    });
    return () => controller.abort();
  }, [key, request, waitingHistory]);
  const current = !waitingHistory && result?.key === key && result.revision === request.version ? result : null;
  const refreshQuestions = () => setRequest(value => ({version:value.version + 1, force:true}));
  return <div className="cw-personal-home">
    {!token ? <p className="cw-home-hint">
      <button onClick={() => setLoginOpen(true)}>{en ? 'Sign in' : '登录'}</button>
      {en ? ' to explore questions drawn from your reading and conversations.' : '后，从你的阅读与对话中继续探索。'}
    </p> : <>
      {current?.status === 'ready' && <>
        <div className="cw-personal-heading"><span>{en ? 'From your recent explorations' : '接着你的思考'} </span>
          <button className="cw-icon-btn" onClick={refreshQuestions} title={en ? 'New questions' : '换一组问题'} aria-label={en ? 'New questions' : '换一组问题'}><RefreshCw size={14} /></button>
        </div>
        <div className="cw-personal-questions">{current.suggestions.map(item =>
          <button key={item.question} className="cw-personal-question" onClick={() => onPick(item.question)}>
            <span><span className="cw-question-basis">{item.basis}</span><span className="cw-question-text">{item.question}</span></span>
            <ArrowUpRight size={18} aria-hidden="true" />
          </button>)}</div>
      </>}
      {(!current || current.status === 'loading') && <p className="cw-home-hint" role="status">{historyStatus==='offline' ? (en ? 'Sync your conversation changes before showing questions.' : '对话变更尚未同步，暂不显示旧推荐。') : (en ? 'Connecting your recent explorations…' : '正在接续你的阅读与思考…')}{historyStatus==='offline' && <button onClick={retryHistory}>{en?'Retry sync':'重新同步'}</button>}</p>}
      {current?.status === 'empty' && <p className="cw-home-hint">{en ? 'Your reading, notes and conversations will shape the questions here.' : '你的阅读、笔记与对话，会成为这里下一次提问的起点。'}</p>}
      {current?.status === 'unavailable' && <p className="cw-home-hint">{en ? 'New questions are temporarily unavailable.' : '暂时未能生成新的提问。'} <button onClick={refreshQuestions}>{en ? 'Retry' : '重试'}</button></p>}
    </>}
    {loginOpen && <AuthModal onClose={() => setLoginOpen(false)} />}
  </div>;
}
