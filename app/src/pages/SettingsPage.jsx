/**
 * 设置页面 — API Key、模型、书籍目录
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function SettingsPage() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('deepseek-chat');
  const [apiUrl, setApiUrl] = useState('');
  const [booksPath, setBooksPath] = useState('');
  const [saved, setSaved] = useState(false);
  const folderInputRef = useRef(null);

  useEffect(() => {
    try {
      const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
      if (config.apiKey) setApiKey(config.apiKey);
      if (config.model) setModel(config.model);
      if (config.apiUrl) setApiUrl(config.apiUrl);
      if (config.booksPath) setBooksPath(config.booksPath);
    } catch {}
  }, []);

  const saveConfig = () => {
    const config = { apiKey, model, apiUrl, booksPath };
    localStorage.setItem('dp_api_config', JSON.stringify(config));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleFolderPick = (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    // Extract directory path from first file
    const first = files[0];
    const relPath = first.webkitRelativePath || first.name;
    // The relative path looks like "philosophy/西方/尼采/book.pdf"
    // Find the root folder name
    const rootFolder = relPath.split('/')[0];
    // Common Android storage paths
    setBooksPath(`/storage/emulated/0/${rootFolder}`);
    // Auto-save
    const config = {
      apiKey, model, apiUrl,
      booksPath: `/storage/emulated/0/${rootFolder}`,
    };
    localStorage.setItem('dp_api_config', JSON.stringify(config));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)}
        style={{ marginBottom: 16 }}>← 返回</button>

      <h2 className="section-title">⚙️ 设置</h2>

      <div className="settings-form">
        <div className="card" style={{ cursor: 'default' }}>
          <h3 style={{ fontSize: 15, marginBottom: 12 }}>🤖 AI 配置</h3>
          <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 12 }}>
            填入你自己的 DeepSeek API Key 即可使用 AI 问答。不填则无法使用问答功能。
          </p>

          <label>
            API 地址
            <input type="text" placeholder="https://api.deepseek.com"
              value={apiUrl} onChange={e => setApiUrl(e.target.value)} />
          </label>

          <label style={{ marginTop: 10 }}>
            API Key
            <input type="password" placeholder="sk-..."
              value={apiKey} onChange={e => setApiKey(e.target.value)} />
          </label>

          <label style={{ marginTop: 10 }}>
            模型名称
            <input type="text" placeholder="deepseek-chat"
              value={model} onChange={e => setModel(e.target.value)} />
          </label>
        </div>

        <div className="card" style={{ cursor: 'default', marginTop: 16 }}>
          <h3 style={{ fontSize: 15, marginBottom: 12 }}>📂 书籍目录</h3>
          <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 12 }}>
            将 philosophy 文件夹复制到手机后，点击下方按钮选择该文件夹。
          </p>

          <button className="btn btn-primary" style={{ width: '100%', marginBottom: 10 }}
            onClick={() => folderInputRef.current?.click()}>
            📁 选择书籍文件夹
          </button>
          <input
            ref={folderInputRef}
            type="file"
            style={{ display: 'none' }}
            webkitdirectory=""
            directory=""
            onChange={handleFolderPick}
          />

          <label>
            或手动输入路径
            <input type="text"
              placeholder="/storage/emulated/0/philosophy"
              value={booksPath}
              onChange={e => setBooksPath(e.target.value)} />
          </label>
          <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 6 }}>
            💡 常见路径：/storage/emulated/0/philosophy 或 /sdcard/philosophy
          </p>
        </div>

        <button className="btn btn-primary btn-block" style={{ marginTop: 14 }}
          onClick={saveConfig}>
          {saved ? '✅ 已保存' : '💾 保存配置'}
        </button>

        <div className="card" style={{ cursor: 'default', marginTop: 16 }}>
          <h3 style={{ fontSize: 15, marginBottom: 8 }}>📱 关于</h3>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6 }}>
            <strong>DeepPhilosophy</strong> v1.0.0<br />
            开发者: @txdsyl_<br />
            哲学爱好者知识库应用<br />
            支持 EPUB/PDF 本地阅读与 AI 问答
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
