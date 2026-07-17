/**
 * 隐私政策页面
 */
import { useNavigate } from 'react-router-dom';

export default function PrivacyPage() {
  const navigate = useNavigate();
  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto', padding: '40px 24px', lineHeight: 1.9 }}>
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 24 }}>← 返回</button>
      <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: 28, marginBottom: 24 }}>隐私政策</h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: 16 }}>最后更新：2026年7月</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>1. 我们收集的信息</h2>
      <p>DeepPhilosophy 最小化收集用户数据：</p>
      <ul style={{ paddingLeft: 20 }}>
        <li><strong>账户信息</strong>：用户名和加密密码，仅用于登录认证。</li>
        <li><strong>阅读记录</strong>：您阅读的书籍和进度，用于跨设备同步。</li>
        <li><strong>聊天记录</strong>：AI 问答对话历史，存储于您的本地浏览器和云端（仅登录用户）。</li>
        <li><strong>API Key</strong>：您自行配置的 DeepSeek API Key，使用 AES-GCM 加密存储于本地浏览器，不上传至服务器。</li>
      </ul>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>2. 数据存储与安全</h2>
      <p>用户密码使用 bcrypt 哈希存储。聊天记录和阅读进度通过 HTTPS 加密传输。本地 API Key 使用 Web Crypto API (AES-GCM) 加密，仅可在您自己的设备上解密。</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>3. 第三方服务</h2>
      <p>本平台使用以下第三方服务：</p>
      <ul style={{ paddingLeft: 20 }}>
        <li><strong>DeepSeek API</strong>：AI 问答功能的后端模型。</li>
        <li><strong>百度 AI</strong>：语音识别服务（仅在您使用语音输入时）。</li>
        <li><strong>阿里云 OSS</strong>：书籍文件云端存储。</li>
        <li><strong>Google Fonts</strong>：网站字体加载。</li>
      </ul>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>4. 联系我们</h2>
      <p>如有隐私相关问题，请通过 GitHub Issues 联系开发者 @txdsyl_。</p>
    </div>
  );
}
