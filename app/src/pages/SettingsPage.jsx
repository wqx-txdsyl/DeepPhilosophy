/**
 * 设置页面 — API Key（加密存储）、模型配置
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { saveConfig, loadConfig } from '../data/crypto';

function SettingsPage() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('deepseek-chat');
  const [apiUrl, setApiUrl] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadConfig().then(config => {
      if (config.apiKey) setApiKey(config.apiKey);
      if (config.model) setModel(config.model);
      if (config.apiUrl) setApiUrl(config.apiUrl);
    });
  }, []);

  const handleSave = async () => {
    await saveConfig(apiKey, model, apiUrl);
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

        <button className="btn btn-primary btn-block" style={{ marginTop: 14 }}
          onClick={handleSave}>
          {saved ? '✅ 已保存' : '💾 保存配置'}
        </button>

        <div className="card" style={{ cursor: 'default', marginTop: 16 }}>
          <h3 style={{ fontSize: 15, marginBottom: 8 }}>📱 关于</h3>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6 }}>
            <strong>DeepPhilosophy</strong> v2.0.0<br />
            开发者: @txdsyl_<br />
            哲学爱好者知识平台<br />
            342 本哲学著作 · 353 位哲学家 · 84 个流派<br />
            答案之书 · PHTI 哲学人格测试 · AI 毒舌锐评
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
