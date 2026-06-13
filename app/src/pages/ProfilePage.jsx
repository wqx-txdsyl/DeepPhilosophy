/**
 * 个人中心 —— 阅读历史、聊天历史、数据导出导入
 * 所有数据本地存储，无需登录
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getReadingHistory, getChatHistory, clearChatHistory,
  exportToFile, importFromFile, getAllUserData,
  relativeTime,
} from '../data/userData';

function ProfilePage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('reading');
  const [readingHistory, setReadingHistory] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [importMsg, setImportMsg] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (tab === 'reading') setReadingHistory(getReadingHistory());
    else setChatHistory(getChatHistory());
  }, [tab]);

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const data = await importFromFile(file);
      setImportMsg(`导入成功：${data.readingHistory.length} 条阅读记录，${data.chatHistory.length} 条聊天记录`);
      setTimeout(() => setImportMsg(''), 5000);
    } catch (err) {
      setImportMsg('导入失败：' + err.message);
      setTimeout(() => setImportMsg(''), 5000);
    }
  };

  const handleClearChat = () => {
    if (confirm('确定清空所有聊天历史？')) {
      clearChatHistory();
      setChatHistory([]);
    }
  };

  const userData = getAllUserData();

  return (
    <div className="page-container">
      {/* 数据概览 */}
      <div className="card" style={{ cursor: 'default', textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 8 }}>👤</div>
        <h2 style={{ fontSize: 18, color: 'var(--accent)' }}>DeepPhilosophy</h2>
        <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 8 }}>
          📖 {userData.readingHistory.length} 条阅读 · 💬 {userData.chatHistory.length} 条对话
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
          自动保存 · {userData.updated ? userData.updated.slice(0, 16) : '从未'}
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 12 }}>
          <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
            onClick={exportToFile}>📤 导出</button>
          <button className="btn btn-secondary" style={{ padding: '6px 16px', fontSize: 13 }}
            onClick={() => fileInputRef.current?.click()}>📥 导入</button>
          <input type="file" ref={fileInputRef} style={{ display: 'none' }}
            accept=".phi,.json" onChange={handleImport} />
        </div>
        {importMsg && (
          <div style={{ fontSize: 12, marginTop: 8, color: importMsg.includes('成功') ? 'var(--success)' : 'var(--danger)' }}>
            {importMsg}
          </div>
        )}
      </div>

      {/* 标签切换 */}
      <div style={{ display: 'flex', gap: 8, margin: '16px 0' }}>
        <button className={`btn ${tab === 'reading' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, padding: '8px', fontSize: 13 }}
          onClick={() => setTab('reading')}>📖 阅读历史</button>
        <button className={`btn ${tab === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, padding: '8px', fontSize: 13 }}
          onClick={() => setTab('chat')}>💬 聊天历史</button>
      </div>

      {/* 阅读历史 */}
      {tab === 'reading' && (
        <div>
          {readingHistory.length > 0 && (
            <button className="btn btn-secondary" style={{ marginBottom: 8, padding: '4px 12px', fontSize: 12 }}
              onClick={() => { const ok = confirm('确定清空所有阅读记录？'); if (ok) { const d = JSON.parse(localStorage.getItem('dp_userdata') || '{}'); d.readingHistory = []; localStorage.setItem('dp_userdata', JSON.stringify(d)); setReadingHistory([]); } }}>
              清空阅读记录
            </button>
          )}
          {readingHistory.length === 0 ? (
            <div className="empty-state"><p>暂无阅读记录</p></div>
          ) : (
            readingHistory.map((item, i) => (
              <div key={i} className="card" style={{ cursor: 'pointer' }}
                onClick={() => navigate('/reader/' + item.bookId)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="card-title" style={{ fontSize: 14, flex: 1 }}>{item.bookTitle}</div>
                  {item.fileType && (
                    <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 8,
                      background: item.fileType === 'pdf' ? 'var(--accent)' : 'var(--secondary)',
                      color: item.fileType === 'pdf' ? '#fff' : 'var(--text-dim)',
                    }}>{item.fileType.toUpperCase()}</span>
                  )}
                </div>
                <div className="card-subtitle">
                  {item.bookAuthor} 进度: {Math.round((item.percent || 0) * 100)}%
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
                  {relativeTime(item.lastReadAt)}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 聊天历史 */}
      {tab === 'chat' && (
        <>
          {chatHistory.length > 0 && (
            <button className="btn btn-secondary" style={{ marginBottom: 8, padding: '4px 12px', fontSize: 12 }}
              onClick={handleClearChat}>🗑 清空聊天</button>
          )}
          {chatHistory.length === 0 ? (
            <div className="empty-state"><p>暂无聊天记录</p></div>
          ) : (
            chatHistory.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}
                style={{ maxWidth: '100%', marginBottom: 8, alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{msg.content}</div>
                {msg.sources?.length > 0 && (
                  <div className="chat-sources">📎 {msg.sources.join(', ')}</div>
                )}
              </div>
            ))
          )}
        </>
      )}

      {/* 跨设备说明 */}
      <div className="card" style={{ cursor: 'default', marginTop: 16 }}>
        <h3 style={{ fontSize: 14, marginBottom: 8 }}>💡 跨设备使用</h3>
        <p style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.6 }}>
          点击「导出」生成 userdata.phi 文件，传到新设备后点「导入」即可恢复所有阅读和聊天记录。
        </p>
      </div>
    </div>
  );
}

export default ProfilePage;
