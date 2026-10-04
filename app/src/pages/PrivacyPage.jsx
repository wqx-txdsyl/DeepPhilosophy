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
      <p style={{ color: 'var(--text-dim)', marginBottom: 16 }}>最后更新：2026年10月4日</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>1. 我们收集的信息</h2>
      <p>DeepPhilosophy 最小化收集用户数据：</p>
      <ul style={{ paddingLeft: 20 }}>
        <li><strong>账户信息</strong>：用户名和加密密码，仅用于登录认证。</li>
        <li><strong>阅读记录</strong>：您阅读的书籍和进度，用于跨设备同步。</li>
        <li><strong>阅读批注</strong>：您主动保存的读书笔记，存储于本地浏览器，并为登录用户提供云端同步。</li>
      </ul>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>2. 数据存储与安全</h2>
      <p>用户密码经哈希处理后保存。阅读进度、批注及账户数据通过 HTTPS 加密传输。</p>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>3. 第三方服务</h2>
      <p>本平台使用以下第三方服务：</p>
      <ul style={{ paddingLeft: 20 }}>
        <li><strong>Cloudflare</strong>：网站托管、账户认证与阅读数据同步服务。</li>
        <li><strong>阿里云 OSS</strong>：书籍文件云端存储。</li>
        <li><strong>jsDelivr</strong>：章节内容的备用分发服务。</li>
      </ul>

      <h2 style={{ fontSize: 18, marginTop: 24 }}>4. 联系我们</h2>
      <p>如有隐私相关问题，请通过 GitHub Issues 联系开发者 @txdsyl_。</p>
    </div>
  );
}
