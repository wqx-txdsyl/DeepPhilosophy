import { useEffect, useState } from 'react';
import { useAuth } from '../../auth';
import { setPref } from '../../data/localPrefs';
import useLocalPref from '../../utils/useLocalPref';

export default function ModelSettings({lang}) {
  const {token,accountReady,authFetch}=useAuth();
  const value=useLocalPref('modelProvider') || 'deepseek';
  const [models,setModels]=useState(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
  const zh=lang!=='en';
  useEffect(()=>{
    const controller=new AbortController();setModels(null);setError('');
    authFetch('/api/agent/models',{signal:controller.signal}).then(d=>{
      if(controller.signal.aborted)return;
      if(!Array.isArray(d.models))throw new Error('Unavailable');
      setModels(d.models);
    }).catch(()=>{if(!controller.signal.aborted)setError(zh?'模型列表暂未加载，请重试。':'Could not load model choices. Please retry.');});
    return()=>controller.abort();
  },[token,accountReady,retry]);
  const reason=id=>({login_required:zh?'登录后可用':'Sign in to use',not_configured:zh?'暂未配置':'Not configured',runtime_unsupported:zh?'当前模式不可用':'Unavailable in this runtime'}[id]||'');
  const selected=models?.find(m=>m.id===value);
  return <>
    <div className="cw-setting-row"><div className="cw-setting-copy"><div className="cw-settings-label">{zh?'对话模型':'Chat model'}</div><p className="cw-settings-sub">{zh?'从下一条消息开始使用。正在生成的回复继续使用发送时的模型。':'Applies to your next message. Replies already running keep their original model.'}</p></div>
      <div className="cw-setting-control"><select aria-label={zh?'对话模型':'Chat model'} value={value} disabled={!models} onChange={e=>{
        if(setPref('modelProvider',e.target.value))setError('');else setError(zh?'模型偏好未能保存，请检查浏览器存储。':'Could not save this preference. Check browser storage.');
      }}>{(models||[{id:'deepseek',label:'DeepSeek'},{id:'openai',label:'ChatGPT'}]).map(m=><option key={m.id} value={m.id} disabled={models&&!m.available}>{m.label}{m.id==='openai'?' · GPT-6.1 Terra':''}{m.reason?`（${reason(m.reason)}）`:''}</option>)}</select></div>
    </div>
    {selected&&<p className="cw-settings-desc">{zh?'当前模型':'Current model'}：{selected.model}{selected.reason?` · ${reason(selected.reason)}`:''}</p>}
    {!models&&!error&&<p className="cw-settings-desc" role="status">{zh?'正在读取可用模型…':'Loading available models…'}</p>}
    {error&&<div className="cw-settings-notice cw-settings-notice-error" role="alert">{error}<button className="cw-settings-button" onClick={()=>setRetry(n=>n+1)}>{zh?'重试':'Retry'}</button></div>}
    <p className="cw-settings-desc">{zh?'切换后可继续当前会话。每条回复会保留当时实际使用的模型。':'You can continue the same conversation after switching. Each reply keeps its actual model record.'}</p>
  </>;
}
