/**
 * 设置页面 — API Key 配置、服务器地址
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function SettingsPage() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('deepseek-chat');
  const [apiUrl, setApiUrl] = useState('');
  const [booksPath, setBooksPath] = useState('');
  const [saved, setSaved] = useState(false);

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
    setTimeout(() => setSaved(false), 2000);
    window.location.reload();
  };

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)}
        style={{ marginBottom: 16 }}>← 返回</button>

      <h2 className="section-title">⚙️ 设置</h2>

      <div className="settings-form">
        <div className="card" style={{ cursor: 'default' }}>
          <h3 style={{ fontSize: 15, marginBottom: 12 }}>🤖 云端 AI 配置</h3>
          <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 12 }}>
            输入你自己的 API Key 以使用云端大模型。支持 DeepSeek 及其兼容接口。
            如不填写，将使用本地知识库（无需API）。
          </p>

          <label>
            API 地址
            <input
              type="text"
              placeholder="https://api.deepseek.com"
              value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
            />
          </label>

          <label style={{ marginTop: 10 }}>
            API Key
            <input
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
            />
          </label>

          <label style={{ marginTop: 10 }}>
            模型名称
            <input
              type="text"
              placeholder="deepseek-chat"
              value={model}
              onChange={e => setModel(e.target.value)}
            />
          </label>

          <button
            className="btn btn-primary btn-block"
            style={{ marginTop: 14 }}
            onClick={saveConfig}
          >
            {saved ? '✅ 已保存' : '💾 保存配置'}
          </button>
        </div>

        <div className="card" style={{ cursor: 'default', marginTop: 16 }}>
          <h3 style={{ fontSize: 15, marginBottom: 12 }}>📂 本地书籍路径</h3>
          <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 12 }}>
            将 F:/philosophy 文件夹复制到手机存储，填入路径。留空则使用内置书单（无法阅读书籍内容）。
          </p>
          <label>
            书籍存储路径
            <input
              type="text"
              placeholder="/storage/emulated/0/DeepPhilosophy/books"
              value={booksPath}
              onChange={e => setBooksPath(e.target.value)}
            />
          </label>
          <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 6 }}>
            💡 手机连接电脑后，将 philosophy 文件夹复制到手机，路径通常为 /storage/emulated/0/philosophy
          </p>
        </div>

        <div className="card" style={{ cursor: 'default', marginTop: 16 }}>
          <h3 style={{ fontSize: 15, marginBottom: 8 }}>📱 关于</h3>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6 }}>
            <strong>DeepPhilosophy</strong> v1.0.0<br />
            开发者: @txdsyl_<br />
            一个面向哲学爱好者的知识库应用<br />
            支持东西方哲学典籍的浏览、检索与AI问答
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
