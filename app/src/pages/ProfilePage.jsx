import { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getApiBase, getAuthBase } from '../utils/api';
import { loadBooks } from '../data';
import { getReadingHistory, relativeTime } from '../data/userData';
import { localNotes, switchReadingOwner, writeLocalNote, notePending, markNoteSynced, mergeCloudNotes, mergeReadingHistory, readingView } from '../data/readingRoom';
import { SiteFooter, RoomCover } from '../components/SitePageParts';
import AvatarUpload from '../components/AvatarUpload';
import { useSEO } from '../utils/seo';
import './SitePages.css';

async function request(path,{token,auth=false,body,method='GET'}={}){
  const response=await fetch(`${auth?getAuthBase():getApiBase()}${path}`,{method,headers:{...(token?{Authorization:`Bearer ${token}`}:{ }),...(body?{'Content-Type':'application/json'}:{})},...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(10000)});
  const data=await response.json().catch(()=>({}));if(!response.ok){const error=new Error(data.detail||data.error||'请求失败，请稍后重试');error.status=response.status;throw error;}return data;
}
export default function ProfilePage(){
  const [params,setParams]=useSearchParams();const tab=['reading','notes','account'].includes(params.get('tab'))?params.get('tab'):'reading';
  const [books,setBooks]=useState([]),[history,setHistory]=useState([]),[notes,setNotes]=useState({}),[session,setSession]=useState(null);
  const [checking,setChecking]=useState(true),[busy,setBusy]=useState(false),[syncing,setSyncing]=useState(false),[syncMessage,setSyncMessage]=useState('');
  const [username,setUsername]=useState(''),[password,setPassword]=useState(''),[authMode,setAuthMode]=useState('login'),[message,setMessage]=useState('');
  const [selected,setSelected]=useState(''),[noteQuery,setNoteQuery]=useState(''),[saving,setSaving]=useState(false),[avatar,setAvatar]=useState('');
  const generation=useRef(0);const syncingRef=useRef(false);
  useSEO('我的书房','继续阅读，整理批注，管理你的阅读记录与账户。');
  function refreshLocal(){setHistory(getReadingHistory());setNotes(localNotes());setAvatar(localStorage.getItem('dp_avatar')||'');}
  async function synchronize(token){
    if(syncingRef.current)return;syncingRef.current=true;setSyncing(true);setSyncMessage('正在同步…');const ticket=generation.current;
    try{
      const results=await Promise.allSettled([request('/api/history/reading',{token}),request('/api/notes',{token}),request('/api/user/avatar',{token})]);
      if(ticket!==generation.current||localStorage.getItem('dp_token')!==token)return;
      const [reading,annotations,picture]=results;
      if(reading.status==='fulfilled'){
        const merged=mergeReadingHistory(getReadingHistory(),reading.value.history||[]);const data=JSON.parse(localStorage.getItem('dp_userdata')||'{}');localStorage.setItem('dp_userdata',JSON.stringify({...data,readingHistory:merged}));setHistory(merged);
      }
      if(annotations.status==='fulfilled')setNotes(mergeCloudNotes(annotations.value.notes||{}));
      if(picture.status==='fulfilled'){const value=picture.value.avatar||'';if(value)localStorage.setItem('dp_avatar',value);else localStorage.removeItem('dp_avatar');setAvatar(value);}
      const failed=results.some(r=>r.status==='rejected');const pending=Object.keys(localNotes()).some(id=>notePending(id));setSyncMessage(failed?'部分同步失败，本地记录仍保留。':pending?'阅读记录已同步；有批注仅保存在本机。':'已读取云端记录');
    }catch{if(ticket===generation.current)setSyncMessage('同步失败，本地记录仍保留。');}finally{if(ticket===generation.current){syncingRef.current=false;setSyncing(false);}}
  }
  useEffect(()=>{
    let active=true;const requestGeneration=generation;const token=localStorage.getItem('dp_token'),name=localStorage.getItem('dp_username');
    loadBooks().then(data=>{if(active)setBooks(data);}).catch(()=>{});
    Promise.resolve().then(async()=>{
      if(!active)return;try{switchReadingOwner(name||'guest');refreshLocal();}catch{setMessage('本机存储空间不足，部分记录暂无法保存。');}
      if(!token||!name){setChecking(false);return;}
      try{const data=await request('/api/auth/profile',{token,auth:true});if(!active)return;setSession({token,name:data.username||name});setChecking(false);synchronize(token);}
      catch(error){if(!active)return;if(error.status===401||error.status===403||error.status===404){setMessage('登录已过期，请重新登录。');setUsername(name);}else{setSession({token,name});setSyncMessage('暂时离线，正在使用本机记录。');}setChecking(false);}
    });
    return()=>{active=false;requestGeneration.current++;};
  // This restoration runs once; user actions perform subsequent syncs explicitly.
  },[]);
  function chooseTab(value){setParams(previous=>{const next=new URLSearchParams(previous);next.set('tab',value);return next;},{replace:true,preventScrollReset:true});setMessage('');}
  async function authenticate(event){event.preventDefault();if(busy)return;setBusy(true);setMessage('');try{
    const result=await request(`/api/auth/${authMode}`,{auth:true,method:'POST',body:{username:username.trim(),password}});
    if(authMode==='register'){setMessage('注册成功，请登录。');setAuthMode('login');setPassword('');return;}
    generation.current++;switchReadingOwner(result.username||username.trim());localStorage.setItem('dp_token',result.token);localStorage.setItem('dp_username',result.username||username.trim());setSession({token:result.token,name:result.username||username.trim()});setPassword('');refreshLocal();setChecking(false);await synchronize(result.token);
  }catch(error){setMessage(error.message);}finally{setBusy(false);}}
  function logout(){try{generation.current++;syncingRef.current=false;switchReadingOwner('guest');localStorage.removeItem('dp_token');localStorage.removeItem('dp_username');setSession(null);setSyncMessage('');setSyncing(false);setSelected('');refreshLocal();setMessage('已退出登录。');}catch{setMessage('退出失败，请检查本机存储空间。');}}
  const lookup=id=>books.find(b=>b.id===id);
  const current=history[0];const currentBook=current&&(lookup(current.bookId)||{id:current.bookId,title:current.bookTitle,author:current.bookAuthor});
  const progress=current&&readingView(current,currentBook);
  const entries=Object.entries(notes).filter(([,text])=>text.trim()).map(([id,text])=>({id,text,book:lookup(id)||{id,title:history.find(h=>h.bookId===id)?.bookTitle||'未匹配的书籍',author:''}}));
  const selectedEntry=entries.find(n=>n.id===selected)||entries[0];const noteId=selected&&Object.hasOwn(notes,selected)?selected:selectedEntry?.id;
  const noteBook=noteId&&(lookup(noteId)||entries.find(n=>n.id===noteId)?.book||{title:'阅读批注'});
  const filteredNotes=entries.filter(n=>`${n.book.title} ${n.book.author}`.includes(noteQuery.trim()));
  async function saveNote(){if(!noteId||saving)return;const id=noteId,text=notes[id]||'',ticket=generation.current;setSaving(true);setMessage('');let savedLocally=false;try{
    writeLocalNote(id,text);savedLocally=true;if(session){await request('/api/notes/save',{token:session.token,method:'POST',body:{book_id:id,note_text:text}});if(ticket!==generation.current)return;markNoteSynced(id,text);setMessage('批注已保存并同步。');}else setMessage('批注已保存在本机。');
  }catch{setMessage(savedLocally?'批注已保存在本机，云端同步失败，可稍后重试。':'本机保存失败，请先复制你的批注后再重试。');}finally{setSaving(false);}}
  async function clearHistory(){if(!window.confirm('确定清空阅读记录？批注会保留。'))return;const ticket=generation.current;try{if(session)await request('/api/history/reading',{token:session.token,method:'DELETE'});if(ticket!==generation.current)return;const data=JSON.parse(localStorage.getItem('dp_userdata')||'{}');localStorage.setItem('dp_userdata',JSON.stringify({...data,readingHistory:[]}));setHistory([]);setMessage('阅读记录已清空。');}catch(error){setMessage(`未能清空：${error.message}`);}}
  const guestBooks=[books.find(b=>b.id==='c5013f33fe01'),books.find(b=>b.id==='84adfb4d0c0b')].filter(Boolean);
  return <div className="site-pages"><div className="s-shell"><header className="s-page-heading"><div><p className="s-kicker">Your reading room</p><h1 className="s-serif">我的书房</h1><p>从上次停下的地方，继续读。</p></div>{session?<div className="s-profile-identity">{avatar?<img className="room-avatar" src={avatar} alt="我的头像"/>:<span className="s-seal">{session.name.slice(0,1)}</span>}<div><strong>{session.name}</strong><p className="s-small" role="status">{syncing?'正在同步…':syncMessage}</p><button onClick={()=>chooseTab('account')}>账户设置 ↗</button></div></div>:<span className="s-small">{checking?'正在恢复登录…':'本机书房'}</span>}</header>
    {!session&&!checking&&<section className="s-guest"><div><p className="s-kicker">A place to return</p><h2>给你的阅读，<br/>留一个位置。</h2><p>登录后同步阅读记录与批注。<br/>浏览书库和在线阅读无需先登录。</p><form className="s-account-form" onSubmit={authenticate}><label className="s-field">用户名<input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" required/></label><label className="s-field">密码<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete={authMode==='register'?'new-password':'current-password'} minLength={authMode==='register'?8:undefined} required/></label><div className="s-current-actions"><button className="s-primary" disabled={busy||syncing}>{busy?'请稍候…':authMode==='register'?'注册':'登录'} ↗</button><button className="s-textlink" type="button" onClick={()=>{setAuthMode(authMode==='register'?'login':'register');setMessage('');}}>{authMode==='register'?'已有账户，去登录':'注册新账户'}</button></div>{authMode==='register'&&<p className="s-small">注册前请阅读 <Link to="/terms">用户协议</Link> 与 <Link to="/privacy">隐私政策</Link>。</p>}</form></div><div className="s-guest-books">{guestBooks.map(b=><RoomCover key={b.id} book={b} hero/>)}</div></section>}
    {message&&<p className="s-toast" role="status">{message}</p>}
    <nav className="s-profile-tabs" aria-label="我的书房">{[['reading','阅读记录'],['notes','我的批注'],['account','账户设置']].map(([id,title])=><button key={id} aria-pressed={tab===id} onClick={()=>chooseTab(id)}>{title}</button>)}<span>{history.length} 本读过 · {entries.length} 本有批注</span></nav>
    {tab==='reading'&&<>{current?<><section className="s-current-book"><div className="s-current-book-art"><RoomCover key={currentBook.id} book={currentBook} hero/></div><div><span className="s-kicker">接着上次读</span><h2>{currentBook.title}</h2><p className="s-small">{currentBook.author}</p><p className="s-current-chapter">已读至第 {progress.chapter+1} 章</p><div className="s-progress" role="progressbar" aria-label="阅读进度" aria-valuenow={progress.percent} aria-valuemin={0} aria-valuemax={100}><span style={{width:`${progress.percent}%`}}/></div><div className="s-progress-caption"><span>{progress.total?`${progress.chapter+1} / ${progress.total} 章`:relativeTime(current.lastReadAt)}</span><span>{progress.percent}%</span></div><div className="s-current-actions"><Link className="s-primary" to={progress.href}>继续阅读 ↗</Link><button className="s-textlink" onClick={()=>{if(!Object.hasOwn(notes,current.bookId))setNotes(n=>({...n,[current.bookId]:''}));setSelected(current.bookId);chooseTab('notes');}}>整理这本书的批注</button></div></div></section><div className="s-profile-columns"><section><h2>也在阅读</h2>{history.slice(1).map(item=>{const b=lookup(item.bookId)||{title:item.bookTitle,author:item.bookAuthor};return <div className="s-reading-row" key={item.bookId}><RoomCover book={b}/><div><h3>{b.title}</h3><p>{b.author}</p><small>{relativeTime(item.lastReadAt)}</small></div><Link to={readingView(item,b).href}>翻开 ↗</Link></div>;})}{history.length===1&&<p className="s-small">下一本书，等你从书库中发现。</p>}</section><section><h2>留在页边的话</h2>{entries[0]?<div className="s-notecard"><small>{entries[0].book.title} / 阅读批注</small><p className="room-note-excerpt">{entries[0].text}</p><button className="s-textlink" onClick={()=>{setSelected(entries[0].id);chooseTab('notes');}}>继续整理这条笔记 ↗</button></div>:<p className="s-small">阅读时打开批注，记下你的想法。</p>}</section></div></>:<div className="s-empty"><h2 className="s-serif">从第一本书开始</h2><p>读过的作品会出现在这里。</p><Link className="s-textlink" to="/books">去书库挑一本 ↗</Link></div>}</>}
    {tab==='notes'&&<><div className="s-note-toolbar"><label className="s-search"><span aria-hidden="true">⌕</span><input type="search" value={noteQuery} onChange={e=>setNoteQuery(e.target.value)} placeholder="按书名或作者查找批注" aria-label="查找批注" spellCheck={false}/></label><span className="s-small">{entries.length} 本书的批注</span></div><div className="s-notes-layout"><div className="s-note-list">{filteredNotes.map(n=><button key={n.id} aria-pressed={noteId===n.id} onClick={()=>setSelected(n.id)}><strong>{n.book.title}</strong><small>{notePending(n.id)?'仅保存在本机':'阅读批注'}</small></button>)}{!filteredNotes.length&&<p className="s-small">{noteQuery?'没有匹配的批注':'从阅读器中写下第一条批注。'}</p>}</div>{noteId?<section className="s-note-editor"><p className="s-kicker">Reading notes</p><h2>{noteBook.title}</h2><textarea value={notes[noteId]||''} aria-label="编辑批注" placeholder="在这里记下你的思考…" onChange={e=>{const text=e.target.value;setNotes(n=>({...n,[noteId]:text}));try{writeLocalNote(noteId,text);}catch{setMessage('本机存储失败，请先复制保存你的批注。');}}}/><div className="s-note-editor-footer"><span className="s-small">{session?'保存后同步到当前账户':'未登录，批注保存在本机'}</span><button className="s-textlink" disabled={saving} onClick={saveNote}>{saving?'保存中…':'保存批注'}</button></div><Link className="s-textlink" to={`/book/${encodeURIComponent(noteId)}`}>返回书籍详情 ↗</Link></section>:<div className="s-empty">选择一本书，整理页边的想法。</div>}</div></>}
    {tab==='account'&&<section className="s-account-form">{session?<><div className="room-account-avatar"><AvatarUpload key={`${session.name}:${avatar}`} size={64} avatar={avatar} onSave={async value=>{setAvatar(value);try{await request('/api/user/avatar',{token:session.token,method:'POST',body:{avatar:value}});setMessage('头像已同步。');}catch{setMessage('头像已保存在本机，云端同步失败。');}}}/><div><strong>{session.name}</strong><p className="s-small">更换头像，或管理账户资料。</p></div></div><div className="s-account-links"><Link to="/profile/edit">修改用户名与密码 ↗</Link><button disabled={syncing} onClick={()=>synchronize(session.token)}>{syncing?'同步中…':'重新同步记录'}</button></div><div className="s-account-links"><button onClick={logout}>退出登录</button>{history.length>0&&<button onClick={clearHistory}>清空阅读记录</button>}</div>{session.name==='txdsyl_'&&<Link className="s-textlink" to="/DEVELOPER_IS_TXDSYL">进入管理后台 ↗</Link>}</>:<p>登录后可管理账户并同步数据。本机阅读记录与批注仍可使用。</p>}<div className="s-account-links"><Link to="/settings">阅读与网站设置 ↗</Link><Link to="/about">关于本站 ↗</Link></div></section>}
    </div><SiteFooter/></div>;
}
