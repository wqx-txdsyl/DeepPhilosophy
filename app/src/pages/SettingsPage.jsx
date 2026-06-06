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
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
      if (config.apiKey) setApiKey(config.apiKey);
      if (config.model) setModel(config.model);
      if (config.apiUrl) setApiUrl(config.apiUrl);
    } catch {}
  }, []);

  const saveConfig = () => {
    const config = { apiKey, model, apiUrl };
    localStorage.setItem('dp_api_config', JSON.stringify(config));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
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
