/**
 * 问答分区 —— 直连 DeepSeek API，支持 Render RAG 作为优先源
 * 聊天历史本地自动保存
 */
import { useState, useRef, useEffect } from 'react';
import { getApiBase } from '../App';
import Icon from '../components/Icon';
import { useToast } from '../contexts/ToastContext';
import { saveChatMessage, getChatHistory, clearChatHistory } from '../data/userData';

const WELCOME_MSG = {
  role: 'assistant',
  content: <>你好！我是 DeepPhilosophy 哲学助手。你可以向我提问任何哲学问题，我会基于知识库中的文献为你解答，并附上参考文献。{'\n\n'}<Icon name="icon-tip" size={14} /> 提示：在设置页面可以配置你自己的 API Key。</>,
};

function QAPage() {
  const toast = useToast();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [thinkingPhase, setThinkingPhase] = useState('');
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [recording, setRecording] = useState(false);
  const [asrSupported, setAsrSupported] = useState(false);
  const chatRef = useRef(null);
  const thinkingTimer = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // 思考阶段动画
  const thinkingPhases = [
    <><Icon name="icon-search" size={14} /> 检索相关文献...</>,
    <><Icon name="icon-book-open" size={14} /> 分析文档内容...</>,
    <><Icon name="icon-thinking" size={14} /> 深度思考中...</>,
    <><Icon name="icon-writing" size={14} /> 组织回答...</>,
  ];

  const startThinking = () => {
    let i = 0;
    setThinkingPhase(thinkingPhases[0]);
    thinkingTimer.current = setInterval(() => {
      i = (i + 1) % thinkingPhases.length;
      setThinkingPhase(thinkingPhases[i]);
    }, 1200);
  };

  const stopThinking = () => {
    if (thinkingTimer.current) {
      clearInterval(thinkingTimer.current);
      thinkingTimer.current = null;
    }
    setThinkingPhase('');
  };

  // Load saved chat history on mount (behaves like all normal AI clients)
  useEffect(() => {
    const history = getChatHistory();
    if (history.length > 0) {
      const msgs = history.map(m => {
        let sources = m.sources || [];
        // 云端同步时 sources 可能是 JSON 字符串，需要转回数组
        if (typeof sources === 'string') {
          try { sources = JSON.parse(sources); } catch { sources = []; }
        }
        if (!Array.isArray(sources)) sources = [];
        return { role: m.role, content: m.content, sources };
      });
      setMessages(msgs);
    } else {
      setMessages([WELCOME_MSG]);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (thinkingTimer.current) clearInterval(thinkingTimer.current);
    };
  }, []);

  const [apiConfig, setApiConfig] = useState({});
  useEffect(() => {
    import('../data/crypto').then(({ loadConfig }) => loadConfig().then(setApiConfig));
  }, []);

  // 检测浏览器是否支持录音
  useEffect(() => {
    setAsrSupported(!!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder));
  }, []);

  // 开始录音（直接捕获 PCM 16kHz mono，省去 WebM→WAV 转换）
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = audioCtx.createMediaStreamSource(stream);

      // 使用 ScriptProcessorNode 捕获原始 PCM（兼容所有浏览器）
      const bufferSize = 4096;
      const processor = audioCtx.createScriptProcessor(bufferSize, 1, 1);
      const chunks = [];
      audioChunksRef.current = chunks;

      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0);
        // 复制 Float32Array 数据
        const copy = new Float32Array(input.length);
        copy.set(input);
        chunks.push(copy);
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);

      // 保存引用以便停止时清理
      mediaRecorderRef.current = {
        stop: () => {
          processor.disconnect();
          source.disconnect();
          audioCtx.close();
          stream.getTracks().forEach(t => t.stop());

          // 将所有 PCM 块合并编码为 WAV
          const totalLen = chunks.reduce((s, c) => s + c.length, 0);
          if (totalLen === 0) return;

          const pcmData = new Float32Array(totalLen);
          let offset = 0;
          for (const c of chunks) {
            pcmData.set(c, offset);
            offset += c.length;
          }
          audioChunksRef.current = pcmData;
        },
      };

      setRecording(true);
      console.log('[ASR] Recording started (PCM 16kHz)');
    } catch (e) {
      console.error('[ASR] Mic access denied:', e);
      toast.error('无法访问麦克风，请检查浏览器权限');
    }
  };

  // 停止录音 + 编码 WAV + 发送 ASR
  const stopRecording = () => {
    if (!mediaRecorderRef.current) return;

    const recorder = mediaRecorderRef.current;
    recorder.stop(); // cleanup audio context + merge PCM

    const pcmData = audioChunksRef.current;
    if (!pcmData || pcmData.length === 0) {
      setRecording(false);
      toast.warning('未检测到声音，请重试');
      return;
    }

    console.log('[ASR] Recording stopped, samples:', pcmData.length);
    try {
      const wavBlob = encodeWav(pcmData, 16000);
      console.log('[ASR] WAV encoded, size:', wavBlob.size);
      sendAudioToASR(wavBlob).then(text => {
        if (text) {
          console.log('[ASR] Recognized:', text);
          setInput(prev => prev + text);
          toast.success('识别成功');
        }
        setRecording(false);
      }).catch(e => {
        console.error('[ASR] Send error:', e);
        toast.error('语音识别失败: ' + (e.message || '网络错误'));
        setRecording(false);
      });
    } catch (e) {
      console.error('[ASR] WAV encode error:', e);
      toast.error('语音处理失败: ' + (e.message || '未知错误'));
      setRecording(false);
    }
  };

  // Float32 PCM → WAV Blob (16-bit PCM, 16kHz, mono)
  const encodeWav = (samples, sampleRate) => {
    const numSamples = samples.length;
    const buffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(buffer);
    const w = (off, str) => { for (let i = 0; i < str.length; i++) view.setUint8(off + i, str.charCodeAt(i)); };
    w(0, 'RIFF');
    view.setUint32(4, 36 + numSamples * 2, true);
    w(8, 'WAVE');
    w(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    w(36, 'data');
    view.setUint32(40, numSamples * 2, true);
    for (let i = 0; i < numSamples; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([buffer], { type: 'audio/wav' });
  };

  // 发送音频到后端 ASR（用相对路径，本地走 Vite 代理，线上同源）
  const sendAudioToASR = async (wavBlob) => {
    const url = `/api/asr`;
    console.log('[ASR] Sending to:', url, 'size:', wavBlob.size);
    try {
      const resp = await fetch(url, {
        method: 'POST',
        body: wavBlob,
        headers: { 'Content-Type': 'audio/wav' },
        signal: AbortSignal.timeout(15000),
      });
      console.log('[ASR] Response status:', resp.status);
      const data = await resp.json();
      console.log('[ASR] Response body:', data);
      if (resp.ok) {
        return data.text || '';
      } else if (resp.status === 503) {
        toast.info('语音识别服务未配置，请使用文字输入');
      } else if (resp.status === 404) {
        toast.error('后端未部署语音接口，请重新部署 Render');
      } else {
        toast.warning(`语音识别失败 (${resp.status}): ${data.error || data.detail || '未知错误'}`);
      }
    } catch (e) {
      console.error('[ASR] Request failed:', e);
      if (e.name === 'AbortError') {
        toast.warning('语音识别超时，请重试');
      } else {
        toast.warning('语音识别请求失败，请检查网络');
      }
    }
    return '';
  };

  // 自动滚动到底部（流式输出时逐字跟随）
  const bottomRef = useRef(null);
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');

    // 先构建 API 消息（用当前 messages state + 新问题），再更新 UI
    const historyMessages = messages
      .filter(m => !m._streaming && m.role !== 'system')
      .filter(m => typeof m.content === 'string' && m.content.trim().length > 0)
      .slice(-30);

    const apiMessages = [
      { role: 'system', content: '你是一个哲学知识助手，精通中西方哲学。请用中文回答，回答要准确、有深度。如果用户询问特定著作或哲学家，请详细阐述其核心思想。' },
      ...historyMessages.map(m => ({ role: m.role, content: m.content })),
      { role: 'user', content: question },
    ];

    // 更新 UI
    const userMsg = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [], _streaming: true }]);
    setLoading(true);
    startThinking();

    let answer = '';
    let sources = [];

    const baseUrl = (apiConfig.apiUrl || 'https://api.deepseek.com').replace(/\/+$/, '');

    const streamBody = {
      model: apiConfig.model || 'deepseek-chat',
      messages: apiMessages,
      temperature: 0.7, max_tokens: 1024,
      stream: true,
    };

    // 尝试 RAG 后端（非流式，快速获取检索来源）, then 直接流式 API
    try {
      const ragResp = await fetch(`${getApiBase()}/api/qa`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, api_key: apiConfig.apiKey || null }),
        signal: AbortSignal.timeout(10000),
      });
      if (ragResp.ok) {
        const d = await ragResp.json();
        if (d.sources?.length > 0) sources = d.sources;
      }
    } catch (e) { console.error('RAG backend unavailable:', e.message); }

    // 流式调用 DeepSeek API（有用户Key直连，无Key走服务器代理）
    try {
      const useProxy = !apiConfig.apiKey;
      const resp = useProxy
        ? await fetch(`${getApiBase()}/api/ai/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(streamBody),
            signal: AbortSignal.timeout(60000),
          })
        : await fetch(`${baseUrl}/v1/chat/completions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiConfig.apiKey}` },
            body: JSON.stringify(streamBody),
            signal: AbortSignal.timeout(60000),
          });

      if (resp.ok) {
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        const streamStart = Date.now();
        const STREAM_TIMEOUT = 90000; // 90s hard timeout

        while (true) {
          if (Date.now() - streamStart > STREAM_TIMEOUT) {
            if (!answer) answer = '回答生成超时，请重试。';
            break;
          }
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              if (data === '[DONE]') continue;
              try {
                const json = JSON.parse(data);
                const delta = json.choices?.[0]?.delta?.content || '';
                if (delta) {
                  answer += delta;
                  setMessages(prev => {
                    const updated = [...prev];
                    const last = { ...updated[updated.length - 1] };
                    last.content = answer;
                    last.sources = sources;
                    updated[updated.length - 1] = last;
                    return updated;
                  });
                }
              } catch {}
            }
          }
        }
      }
    } catch (e) { console.error('QA stream failed:', e); }

    if (!answer) {
      answer = '无法获取回答。\n\n请检查网络连接或在设置中配置 API Key。';
    }

    stopThinking();
    setLoading(false);
    // 最终更新，移除流式标记
    setMessages(prev => {
      const updated = [...prev];
      const last = { ...updated[updated.length - 1] };
      last.content = answer;
      last.sources = sources;
      delete last._streaming;
      updated[updated.length - 1] = last;
      return updated;
    });

    // Save history
    saveChatMessage('user', question);
    saveChatMessage('assistant', answer, sources);
  };

  const handleClearChat = () => {
    clearChatHistory();
    setMessages([WELCOME_MSG]);
    setShowConfirmClear(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 56px)', overflow: 'hidden' }}>
      {/* Top bar with clear button */}
      <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2px 12px', borderBottom: '1px solid var(--border)' }}>
        <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>
          {messages.length > 1 ? `${messages.length} 条消息` : '新对话'}
        </span>
        {messages.length > 1 && (
          showConfirmClear ? (
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>清空对话？</span>
              <button className="btn btn-primary" style={{ padding: '2px 10px', fontSize: 11 }}
                onClick={handleClearChat}>确认</button>
              <button className="btn btn-secondary" style={{ padding: '2px 10px', fontSize: 11 }}
                onClick={() => setShowConfirmClear(false)}>取消</button>
            </div>
          ) : (
            <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}
              onClick={() => setShowConfirmClear(true)}><Icon name="icon-trash" size={16} /> 新对话</button>
          )
        )}
      </div>

      <div className="chat-container" ref={chatRef} style={{ flex: 1, overflow: 'auto' }}>
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            {Array.isArray(msg.sources) && msg.sources.length > 0 && (
              <div style={{
                marginTop: 10, paddingTop: 10,
                borderTop: '1px solid var(--border)',
                fontSize: 11, color: 'var(--text-dim)',
              }}>
                <Icon name="icon-link" size={16} /> <strong>参考文献：</strong>
                {msg.sources.map((s, j) => (
                  <span key={j} style={{
                    display: 'inline-block',
                    background: 'var(--secondary)',
                    padding: '2px 8px', borderRadius: 4,
                    margin: '2px 4px', color: 'var(--accent)',
                  }}>《{s}》</span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: 'pulse 0.8s ease-in-out infinite',
                }} />
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: 'pulse 0.8s ease-in-out 0.2s infinite',
                }} />
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: 'pulse 0.8s ease-in-out 0.4s infinite',
                }} />
              </div>
              <span style={{
                color: 'var(--text-dim)', fontSize: 12,
                transition: 'opacity 0.3s',
              }}>
                {thinkingPhase}
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area" style={{ position: 'static', flexShrink: 0, padding: '6px 12px', paddingBottom: 12 }}>
        <input
          className="chat-input"
          placeholder={recording ? '正在聆听...' : '输入哲学问题...'}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || recording}
        />
        {asrSupported && (
          <button
            className={`chat-mic-btn${recording ? ' recording' : ''}`}
            onClick={recording ? stopRecording : startRecording}
            disabled={loading}
            aria-label={recording ? '停止录音' : '语音输入'}
            title={recording ? '点击停止' : '语音输入'}
          >
            {recording ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></svg>
            )}
          </button>
        )}
        <button className="chat-send-btn" onClick={sendMessage} disabled={loading} aria-label="发送">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
        </button>
      </div>
    </div>
  );
}

export default QAPage;
